import sqlite3
import os
from datetime import datetime
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        size INTEGER NOT NULL,
        format TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def create_file_record(data):
    conn = get_db()
    cursor = conn.cursor()
    file_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO files (id, filename, original_name, stored_path, mime_type, size, format)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        file_id,
        data["filename"],
        data["original_name"],
        data["stored_path"],
        data["mime_type"],
        data["size"],
        data["format"]
    ))
    conn.commit()
    
    # Fetch and return the created record
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_file_by_id(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def list_files(skip=0, take=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files ORDER BY created_at DESC LIMIT ? OFFSET ?", (take, skip))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_file_name(file_id, new_filename):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE files SET original_name = ? WHERE id = ?", (new_filename, file_id))
    conn.commit()
    cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_file_record(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    return True
