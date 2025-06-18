# Import library yang diperlukan
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Variabel global untuk menyimpan data presensi
# Dalam production, gunakan database seperti SQLite/PostgreSQL
presensi_data = []

# Route utama - halaman home
@app.route('/')
def home():
    """
    Function untuk menampilkan halaman utama
    Mengirim data presensi ke template HTML
    """
    return render_template('index.html', data=presensi_data)

# Route untuk menambah presensi - hanya menerima POST
@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    """
    Function untuk memproses form presensi
    Mengambil data dari form dan menyimpan ke list
    """
    nama = request.form['nama']  # Ambil input nama dari form
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp
    
    # Tambah data ke list sebagai dictionary
    presensi_data.append({
        'nama': nama,
        'waktu': waktu
    })
    
    # Redirect kembali ke halaman utama
    return redirect(url_for('home'))

# Route untuk menghapus semua data
@app.route('/clear')
def clear_data():
    """
    Function untuk menghapus semua data presensi
    """
    global presensi_data
    presensi_data = []  # Kosongkan list
    return redirect(url_for('home'))

# Kondisi untuk menjalankan aplikasi
if __name__ == '__main__':
    app.run(debug=True)  # Mode debug untuk development

# Konfigurasi untuk Vercel deployment
if __name__ != '__main__':
    app.debug = False  # Matikan debug mode di production
