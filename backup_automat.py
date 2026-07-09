import os
import shutil
from datetime import datetime

# Căile către fișiere
DIRECTOR_CURENT = os.path.dirname(os.path.abspath(__file__))
FISIER_BAZA_DATE = os.path.join(DIRECTOR_CURENT, 'db.sqlite3')
DIRECTOR_BACKUP = os.path.join(DIRECTOR_CURENT, 'backups')

# Creăm folderul 'backups' dacă nu există deja
if not os.path.exists(DIRECTOR_BACKUP):
    os.makedirs(DIRECTOR_BACKUP)

# Generăm un nume unic pentru backup bazat pe data și ora exactă
timp_curent = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
nume_fisier_backup = f'db_backup_{timp_curent}.sqlite3'
cale_backup = os.path.join(DIRECTOR_BACKUP, nume_fisier_backup)

# Executăm copierea
try:
    shutil.copy2(FISIER_BAZA_DATE, cale_backup)
    print(f"✅ Backup creat cu succes: {nume_fisier_backup}")
    
    # (Opțional) Ștergem backup-urile mai vechi de 30 de zile pentru a nu umple hard disk-ul
    limita_zile = 30 * 86400 # 30 de zile în secunde
    timp_acum = datetime.now().timestamp()
    
    for fisier in os.listdir(DIRECTOR_BACKUP):
        cale_fisier = os.path.join(DIRECTOR_BACKUP, fisier)
        if os.path.isfile(cale_fisier):
            timp_creare = os.path.getmtime(cale_fisier)
            if timp_acum - timp_creare > limita_zile:
                os.remove(cale_fisier)
                print(f"🗑️ Backup vechi șters: {fisier}")

except FileNotFoundError:
    print("❌ Eroare: Nu am găsit fișierul db.sqlite3. Verifică dacă scriptul este în același folder cu el.")
except Exception as e:
    print(f"❌ A apărut o eroare la backup: {e}")