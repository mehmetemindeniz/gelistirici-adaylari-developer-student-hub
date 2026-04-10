import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE message ADD COLUMN file_url VARCHAR(255)")
    cursor.execute("ALTER TABLE message ADD COLUMN file_type VARCHAR(50)")
    cursor.execute("ALTER TABLE message ADD COLUMN original_file_name VARCHAR(255)")
    conn.commit()
    print("Mesajlara dosya alanları eklendi.")
except sqlite3.OperationalError as e:
    print(f"Hata veya alanlar zaten mevcut: {e}")
finally:
    if conn:
        conn.close()
