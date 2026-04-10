import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE user ADD COLUMN cinsiyet VARCHAR(20) DEFAULT 'Erkek'")
    conn.commit()
    print("Sütun başarıyla eklendi.")
    
    # Mevcut admin kullanıcısını güncelle (opsiyonel ama iyi olur)
    cursor.execute("UPDATE user SET cinsiyet='Erkek' WHERE username='admin'")
    conn.commit()
    
except sqlite3.OperationalError as e:
    print(f"Hata veya zaten eklenmiş olabilir: {e}")
finally:
    if conn:
        conn.close()
