from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates')

# Data storage
presensi_data = []

@app.route('/')
def home():
    return render_template('index.html', data=presensi_data)

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    try:
        nama = request.form.get('nama', '').strip()
        if not nama:
            return redirect(url_for('home'))
        
        waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        presensi_data.append({
            'nama': nama,
            'waktu': waktu
        })
        return redirect(url_for('home'))
    except Exception as e:
        return redirect(url_for('home'))

@app.route('/clear')
def clear_data():
    global presensi_data
    presensi_data = []
    return redirect(url_for('home'))

# Vercel serverless handler
def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    app.run(debug=True)
