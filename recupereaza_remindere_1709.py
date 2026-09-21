from pathlib import Path
import sqlite3
import shutil
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
CURRENT_DB = ROOT / "db.sqlite3"

BACKUP_CANDIDATES = [
    ROOT / "db_backup_2026-09-17_23-00-05(1).sqlite3",
    ROOT / "db_backup_2026-09-17_23-00-05.sqlite3",
]

def find_backup():
    for p in BACKUP_CANDIDATES:
        if p.exists():
            return p

    matches = sorted(ROOT.glob("*2026-09-17*.sqlite3"))
    matches = [p for p in matches if p.name != "db.sqlite3" and "INAINTE_RECUPERARE" not in p.name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print("Am gasit mai multe backupuri din 17.09:")
        for i, p in enumerate(matches, 1):
            print(f"  {i}. {p.name}")
        try:
            idx = int(input("Alege numarul backupului: ").strip())
            return matches[idx - 1]
        except Exception:
            return None

    return None

def table_columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}

def normalize(value):
    return "" if value is None else str(value).strip()

if not CURRENT_DB.exists():
    print("EROARE: Nu gasesc db.sqlite3 langa acest script.")
    print("Pune scriptul in acelasi folder cu manage.py si db.sqlite3.")
    sys.exit(1)

backup_db = find_backup()
if not backup_db:
    print("EROARE: Nu gasesc backupul SQLite din 17.09.")
    print("Copiaza fisierul db_backup_2026-09-17_23-00-05(1).sqlite3 langa manage.py.")
    sys.exit(1)

print("=" * 70)
print("RECUPERARE REMINDERE")
print("=" * 70)
print(f"Baza actuala : {CURRENT_DB.name}")
print(f"Backup vechi : {backup_db.name}")
print()

current = sqlite3.connect(CURRENT_DB)
old = sqlite3.connect(backup_db)
current.row_factory = sqlite3.Row
old.row_factory = sqlite3.Row

try:
    for conn, label in [(current, "actuala"), (old, "backup")]:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if "core_reminder" not in tables:
            print(f"EROARE: tabela core_reminder lipseste din baza {label}.")
            sys.exit(1)
        if "core_user" not in tables:
            print(f"EROARE: tabela core_user lipseste din baza {label}.")
            sys.exit(1)

    current_cols = table_columns(current, "core_reminder")
    old_cols = table_columns(old, "core_reminder")

    needed = {"titlu", "detalii", "data_reminder", "creat_la", "user_id"}
    if not needed.issubset(current_cols) or not needed.issubset(old_cols):
        print("EROARE: schema tabelului core_reminder nu este compatibila.")
        sys.exit(1)

    old_users = {
        row["id"]: row["username"]
        for row in old.execute("SELECT id, username FROM core_user")
    }
    current_users = {
        row["username"]: row["id"]
        for row in current.execute("SELECT id, username FROM core_user")
    }

    old_reminders = list(old.execute("SELECT * FROM core_reminder ORDER BY id"))
    current_reminders = list(current.execute("SELECT * FROM core_reminder ORDER BY id"))

    def current_key(row):
        username = None
        uid = row["user_id"]
        for uname, cid in current_users.items():
            if cid == uid:
                username = uname
                break
        return (
            normalize(username),
            normalize(row["titlu"]),
            normalize(row["detalii"]),
            normalize(row["data_reminder"]),
        )

    existing_keys = {current_key(r) for r in current_reminders}

    missing = []
    skipped_user = []

    for r in old_reminders:
        old_username = old_users.get(r["user_id"])
        if not old_username or old_username not in current_users:
            skipped_user.append((r, old_username))
            continue

        key = (
            normalize(old_username),
            normalize(r["titlu"]),
            normalize(r["detalii"]),
            normalize(r["data_reminder"]),
        )

        if key not in existing_keys:
            missing.append((r, old_username))

    print(f"Remindere in backup : {len(old_reminders)}")
    print(f"Remindere in prezent: {len(current_reminders)}")
    print(f"Remindere lipsa      : {len(missing)}")
    print()

    if skipped_user:
        print("ATENTIE: unele remindere nu pot fi mapate deoarece utilizatorul nu mai exista:")
        for r, username in skipped_user:
            print(f"  - ID vechi {r['id']} | user={username} | {r['titlu']}")
        print()

    if not missing:
        print("Nu lipseste niciun reminder din backupul din 17.09.")
        print("Nu s-a modificat nimic.")
        input("\nApasa ENTER pentru inchidere...")
        sys.exit(0)

    print("URMATOARELE REMINDERE LIPSESC SI POT FI RECUPERATE:")
    print("-" * 70)
    for idx, (r, username) in enumerate(missing, 1):
        finalizat = r["finalizat"] if "finalizat" in old_cols else 0
        stare = "FINALIZAT" if finalizat else "ACTIV"
        print(f"{idx}. [{stare}] {r['titlu']}")
        print(f"   User: {username}")
        print(f"   Data reminder: {r['data_reminder']}")
        print(f"   Detalii: {normalize(r['detalii'])[:160]}")
        print()

    answer = input("Vrei sa recuperez TOATE reminderele de mai sus? [D/N]: ").strip().lower()
    if answer not in ("d", "da", "y", "yes"):
        print("Operatie anulata. Nu s-a modificat baza de date.")
        input("\nApasa ENTER pentru inchidere...")
        sys.exit(0)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety = ROOT / f"db_INAINTE_IMPORT_REMINDERE_{stamp}.sqlite3"
    shutil.copy2(CURRENT_DB, safety)
    print(f"\nBackup de siguranta creat: {safety.name}")

    has_finalizat = "finalizat" in current_cols
    has_data_finalizarii = "data_finalizarii" in current_cols

    inserted = 0
    with current:
        for r, username in missing:
            current_user_id = current_users[username]

            fields = ["titlu", "detalii", "data_reminder", "creat_la", "user_id"]
            values = [
                r["titlu"],
                r["detalii"],
                r["data_reminder"],
                r["creat_la"],
                current_user_id,
            ]

            if has_data_finalizarii:
                fields.append("data_finalizarii")
                values.append(r["data_finalizarii"] if "data_finalizarii" in old_cols else None)

            if has_finalizat:
                fields.append("finalizat")
                values.append(r["finalizat"] if "finalizat" in old_cols else 0)

            placeholders = ", ".join("?" for _ in fields)
            sql = f"INSERT INTO core_reminder ({', '.join(fields)}) VALUES ({placeholders})"
            current.execute(sql, values)
            inserted += 1

    print()
    print("=" * 70)
    print(f"GATA. Au fost recuperate {inserted} remindere.")
    print("ID-urile noi pot fi diferite de cele din backup, ceea ce este normal.")
    print("Taskurile, utilizatorii si celelalte date NU au fost modificate.")
    print("=" * 70)

finally:
    try:
        current.close()
    except Exception:
        pass
    try:
        old.close()
    except Exception:
        pass

input("\nApasa ENTER pentru inchidere...")
