from flask import Flask, request, render_template
import os
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('devices.db')
    conn.execute('CREATE TABLE IF NOT EXISTS devices (id TEXT, ip TEXT, last_seen TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS files (device_id TEXT, filename TEXT, filepath TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS commands (device_id TEXT, action TEXT, status TEXT)')
    conn.commit()
    conn.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    device_id = request.form.get('device_id')
    file = request.files['file']
    filepath = os.path.join('Uploads', file.filename)
    file.save(filepath)
    conn = sqlite3.connect('devices.db')
    conn.execute('INSERT INTO files (device_id, filename, filepath) VALUES (?, ?, ?)', 
                 (device_id, file.filename, filepath))
    conn.commit()
    conn.close()
    return 'File uploaded'

@app.route('/register', methods=['POST'])
def register_device():
    device_id = request.form['device_id']
    device_ip = request.remote_addr
    last_seen = request.form.get('timestamp', 'unknown')
    conn = sqlite3.connect('devices.db')
    conn.execute('INSERT OR REPLACE INTO devices (id, ip, last_seen) VALUES (?, ?, ?)', 
                 (device_id, device_ip, last_seen))
    conn.commit()
    conn.close()
    return 'Device registered'

@app.route('/')
def control_panel():
    conn = sqlite3.connect('devices.db')
    devices = conn.execute('SELECT * FROM devices').fetchall()
    files = conn.execute('SELECT * FROM files').fetchall()
    conn.close()
    return render_template('index.html', devices=devices, files=files)

@app.route('/command/<device_id>/<action>')
def send_command(device_id, action):
    conn = sqlite3.connect('devices.db')
    conn.execute('INSERT INTO commands (device_id, action, status) VALUES (?, ?, ?)', 
                 (device_id, action, 'pending'))
    conn.commit()
    conn.close()
    return f'Command {action} sent to {device_id}'

@app.route('/command/<device_id>')
def get_command(device_id):
    conn = sqlite3.connect('devices.db')
    command = conn.execute('SELECT action FROM commands WHERE device_id = ? AND status = ?', 
                          (device_id, 'pending')).fetchone()
    if command:
        conn.execute('UPDATE commands SET status = ? WHERE device_id = ? AND action = ?', 
                     ('processed', device_id, command[0]))
        conn.commit()
        conn.close()
        return command[0]
    conn.close()
    return ''

if __name__ == '__main__':
    init_db()
    os.makedirs('Uploads', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
