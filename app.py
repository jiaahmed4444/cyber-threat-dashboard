from flask import Flask, jsonify, render_template_string, request
import os, datetime, random, sqlite3
from contextlib import contextmanager

app = Flask(__name__)
DB_PATH = '/data/threats.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS threats (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, threat_type TEXT, severity TEXT, source_ip TEXT, description TEXT, status TEXT DEFAULT "active")')
        conn.execute('CREATE TABLE IF NOT EXISTS metrics (key TEXT PRIMARY KEY, value INTEGER DEFAULT 0)')
        conn.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('threats_total', 0)")
        conn.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('scans_total', 0)")
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

DASHBOARD_TEMPLATE = '''<!DOCTYPE html><html><head><title>Cyber Threat Dashboard</title><style>body{font-family:"Courier New",monospace;background:linear-gradient(135deg,#0a0e27,#1a1f3a);color:#00ffcc;padding:20px;}.container{max-width:1200px;margin:0 auto;}h1{text-shadow:0 0 20px #00ffcc;}.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin:20px 0;}.stat-card{background:rgba(0,255,204,0.05);border:1px solid rgba(0,255,204,0.3);border-radius:15px;padding:20px;text-align:center;}.stat-value{font-size:2.5em;font-weight:bold;}.threat-card{background:rgba(0,0,0,0.4);border-radius:15px;padding:20px;margin-top:20px;}table{width:100%;border-collapse:collapse;}th,td{padding:10px;text-align:left;border-bottom:1px solid #333;}th{color:#00ffcc;}.badge{padding:2px 8px;border-radius:20px;font-size:0.7em;}.badge.HIGH{background:#ff4444;}.badge.MEDIUM{background:#ffaa44;color:#000;}.badge.LOW{background:#44ff44;color:#000;}</style></head><body><div class="container"><h1>🛡️ CYBER THREAT DASHBOARD</h1><div class="stats-grid"><div class="stat-card"><div class="stat-value">🟢 {{ status }}</div><div class="stat-label">Status</div></div><div class="stat-card"><div class="stat-value">{{ threats_total }}</div><div class="stat-label">Total Threats</div></div><div class="stat-card"><div class="stat-value">{{ scans_total }}</div><div class="stat-label">Scans</div></div><div class="stat-card"><div class="stat-value">{{ active_threats }}</div><div class="stat-label">Active</div></div></div><div class="threat-card"><h3>⚠️ Recent Threats</h3>\\n<table><tr><th>Time</th><th>Type</th><th>Severity</th><th>Source IP</th><th>Status</th></tr>{% for t in threats %}<tr><td>{{ t.timestamp[:19] }}</td><td>{{ t.threat_type }}</td><td><span class="badge {{ t.severity }}">{{ t.severity }}</span></td><td>{{ t.source_ip }}</td><td>{{ t.status }}</td></tr>{% endfor %}</table></div><div class="footer"><p>SQLite Database | Kubernetes | Jenkins CI/CD</p></div></div></body></html>'''

init_db()

@app.route('/')
def dashboard():
    with get_db() as conn:
        threats_total = conn.execute("SELECT value FROM metrics WHERE key='threats_total'").fetchone()[0]
        scans_total = conn.execute("SELECT value FROM metrics WHERE key='scans_total'").fetchone()[0]
        active_threats = conn.execute("SELECT COUNT(*) FROM threats WHERE status='active'").fetchone()[0]
        threats = conn.execute("SELECT * FROM threats ORDER BY id DESC LIMIT 10").fetchall()
    return render_template_string(DASHBOARD_TEMPLATE, status="ONLINE", threats_total=threats_total, scans_total=scans_total, active_threats=active_threats, threats=threats)

@app.route('/health')
def health():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "sqlite"})
    except Exception as e:
        return jsonify({"status": "unhealthy"}), 500

@app.route('/metrics')
def metrics():
    with get_db() as conn:
        return jsonify({
            "threats_total": conn.execute("SELECT value FROM metrics WHERE key='threats_total'").fetchone()[0],
            "scans_total": conn.execute("SELECT value FROM metrics WHERE key='scans_total'").fetchone()[0],
            "active_threats": conn.execute("SELECT COUNT(*) FROM threats WHERE status='active'").fetchone()[0]
        })

@app.route('/detect')
def detect():
    threat_detected = random.random() > 0.6
    with get_db() as conn:
        conn.execute("UPDATE metrics SET value = value + 1 WHERE key='scans_total'")
        if threat_detected:
            threat_type = random.choice(['DDoS', 'Malware', 'Phishing', 'Port Scan', 'Ransomware'])
            severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
            source_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            conn.execute("INSERT INTO threats (timestamp, threat_type, severity, source_ip) VALUES (?,?,?,?)", (datetime.datetime.now().isoformat(), threat_type, severity, source_ip))
            conn.execute("UPDATE metrics SET value = value + 1 WHERE key='threats_total'")
            conn.commit()
            return jsonify({"threat_detected": True, "threat_type": threat_type, "severity": severity, "source_ip": source_ip})
        conn.commit()
        return jsonify({"threat_detected": False})

# NEW: POST endpoint for adding threats manually
@app.route('/api/threats', methods=['POST'])
def add_threat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    threat_type = data.get('threat_type', 'Unknown')
    severity = data.get('severity', 'MEDIUM')
    source_ip = data.get('source_ip', '0.0.0.0')
    description = data.get('description', '')
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO threats (timestamp, threat_type, severity, source_ip, description, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        ''', (datetime.datetime.now().isoformat(), threat_type, severity, source_ip, description))
        
        conn.execute("UPDATE metrics SET value = value + 1 WHERE key='threats_total'")
        conn.commit()
        
        threat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    return jsonify({
        "success": True,
        "message": "Threat added to database",
        "threat_id": threat_id,
        "threat": data
    }), 201

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    init_db()
    app.run(host='0.0.0.0', port=port, debug=False)
