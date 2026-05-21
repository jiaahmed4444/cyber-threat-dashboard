from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'threats.db'

@app.route('/')
def index():
    return jsonify({"message": "Cyber Threat Dashboard Running", "status": "active"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS threats (id INTEGER PRIMARY KEY, name TEXT)')
    app.run(host='0.0.0.0', port=5000)
