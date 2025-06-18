from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__, template_folder='templates/')

# In-memory storage
presensi_data = []

@app.route('/')
def home():
    return render_template('index.html', data=presensi_data)

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    try:
        nama = request.form.get('nama', '').strip()
        if nama:
            waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            presensi_data.append({'nama': nama, 'waktu': waktu})
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('home'))

@app.route('/clear')
def clear_data():
    try:
        presensi_data.clear()
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('home'))

# Export app untuk Vercel
application = app

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
