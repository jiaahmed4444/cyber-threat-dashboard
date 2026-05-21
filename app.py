from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'threats.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS threats (id INTEGER PRIMARY KEY, threat_type TEXT, severity TEXT, source_ip TEXT, description TEXT, status TEXT DEFAULT "ACTIVE")')
        count = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
        if count == 0:
            threats = [('SQL Injection', 'HIGH', '192.168.1.100', 'SQL injection detected'), ('Brute Force', 'MEDIUM', '10.0.0.50', 'SSH brute force'), ('Malware', 'CRITICAL', '172.31.1.200', 'Ransomware detected')]
            for t in threats:
                conn.execute('INSERT INTO threats (threat_type, severity, source_ip, description) VALUES (?,?,?,?)', t)
            conn.commit()

@app.route('/')
def index():
    conn = get_db()
    threats = conn.execute('SELECT * FROM threats').fetchall()
    conn.close()
    return jsonify([dict(row) for row in threats])

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'database': 'connected'})

@app.route('/metrics')
def metrics():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
    conn.close()
    return f'cyber_threats_total {total}\n'

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
