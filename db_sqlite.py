import sqlite3


class DBSqlite:

    def __init__(self, db):

        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        # Create table
        self.cur.execute("CREATE TABLE IF NOT EXISTS face_ids (id INTEGER PRIMARY KEY, user_id text, status text, current_time text, image_url text)")
        self.conn.commit()

    def fetch(self):
        self.cur.execute("SELECT * FROM face_ids")
        rows = self.cur.fetchall()
        return rows
    
    def insert(self, user_id, status, current_time, image):
        self.cur.execute("INSERT INTO face_ids VALUES (NULL, ?, ?, ?, ?)",
                         (user_id, status, current_time, image))
        self.conn.commit()

    def remove(self, id):
        self.cur.execute("DELETE FROM face_ids WHERE id=?", (id,))
        self.conn.commit()