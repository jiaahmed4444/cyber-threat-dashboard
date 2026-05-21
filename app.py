from flask import Flask, jsonify, request, render_template_string
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'threats.db'

# HTML template as a string (no external file needed)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Cyber Threat Dashboard</title>
    <style>
        body { font-family: monospace; background: #0a0e27; color: #00ff9d; margin: 20px; }
        h1 { color: #00ff9d; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #00ff9d; padding: 10px; text-align: left; }
        .CRITICAL { color: #ff0000; font-weight: bold; }
        .HIGH { color: #ff6600; }
        .MEDIUM { color: #ffcc00; }
        .LOW { color: #00ff00; }
        button { background: #00ff9d; color: #0a0e27; padding: 10px; margin: 10px; cursor: pointer; }
        input, select { padding: 8px; margin: 5px; }
    </style>
</head>
<body>
    <h1>🛡️ Cyber Threat Intelligence Dashboard</h1>
    
    <div>
        <h3>Total Threats: {{ total }}</h3>
        <h3>Critical: {{ critical }}</h3>
    </div>
    
    <h2>Add New Threat</h2>
    <form method="POST">
        Type: <input name="threat_type" required>
        Severity: 
        <select name="severity">
            <option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option>
        </select>
        Source IP: <input name="source_ip">
        Description: <input name="description">
        <button type="submit">Add Threat</button>
    </form>
    
    <h2>Recent Threats</h2>
    <table>
        <tr><th>ID</th><th>Type</th><th>Severity</th><th>Source IP</th><th>Description</th><th>Status</th></tr>
        {% for t in threats %}
        <tr><td>{{ t[0] }}</td><td>{{ t[1] }}</td><td class="{{ t[2] }}">{{ t[2] }}</td><td>{{ t[3] }}</td><td>{{ t[4] }}</td><td>{{ t[5] }}</td></tr>
        {% endfor %}
    </table>
</body>
</html>
'''

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS threats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source_ip TEXT,
            description TEXT,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')
    # Insert sample data if empty
    count = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
    if count == 0:
        samples = [
            ('SQL Injection', 'HIGH', '192.168.1.100', 'SQL injection detected in login form'),
            ('Brute Force', 'MEDIUM', '10.0.0.50', 'Multiple failed SSH login attempts'),
            ('Ransomware', 'CRITICAL', '172.31.1.200', 'CryptoLocker ransomware detected'),
            ('Port Scan', 'LOW', '8.8.8.8', 'Suspicious port scanning activity')
        ]
        conn.executemany('INSERT INTO threats (threat_type, severity, source_ip, description) VALUES (?,?,?,?)', samples)
        conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect(DATABASE)
    if request.method == 'POST':
        conn.execute(
            'INSERT INTO threats (threat_type, severity, source_ip, description) VALUES (?,?,?,?)',
            (request.form['threat_type'], request.form['severity'], request.form['source_ip'], request.form['description'])
        )
        conn.commit()
    
    threats = conn.execute('SELECT * FROM threats ORDER BY id DESC LIMIT 20').fetchall()
    total = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
    critical = conn.execute('SELECT COUNT(*) FROM threats WHERE severity = "CRITICAL"').fetchone()[0]
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, threats=threats, total=total, critical=critical)

@app.route('/api/threats')
def api_threats():
    conn = sqlite3.connect(DATABASE)
    threats = conn.execute('SELECT * FROM threats').fetchall()
    conn.close()
    return jsonify([{'id': t[0], 'type': t[1], 'severity': t[2], 'ip': t[3], 'description': t[4], 'status': t[5]} for t in threats])

@app.route('/health')
def health():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.execute('SELECT 1')
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    conn = sqlite3.connect(DATABASE)
    total = conn.execute('SELECT COUNT(*) FROM threats').fetchone()[0]
    critical = conn.execute('SELECT COUNT(*) FROM threats WHERE severity = "CRITICAL"').fetchone()[0]
    conn.close()
    return f'cyber_threats_total {total}\ncyber_threats_critical {critical}\n'

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
