# view_results.py
import sqlite3
conn = sqlite3.connect("potholes.db")
rows = conn.execute("SELECT * FROM potholes").fetchall()
for row in rows:
    print(row)
conn.close()