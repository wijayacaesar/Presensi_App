from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import os

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Set secret key untuk session security (opsional tapi recommended)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Data storage - dalam production gunakan database
presensi_data = []

@app.route('/')
def home():
    """
    Halaman utama aplikasi presensi
    Menampilkan form input dan data presensi yang ada
    """
    return render_template('index.html', data=presensi_data)

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    """
    Endpoint untuk menambahkan data presensi baru
    Menerima data dari form dan menyimpan ke storage
    """
    try:
        nama = request.form.get('nama', '').strip()
        
        # Validasi input
        if not nama:
            return redirect(url_for('home'))
        
        waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Tambah data ke storage
        presensi_data.append({
            'nama': nama,
            'waktu': waktu
        })
        
        return redirect(url_for('home'))
        
    except Exception as e:
        # Error handling untuk production
        print(f"Error in tambah_presensi: {e}")
        return redirect(url_for('home'))

@app.route('/clear')
def clear_data():
    """
    Endpoint untuk menghapus semua data presensi
    """
    try:
        global presensi_data
        presensi_data = []
        return redirect(url_for('home'))
        
    except Exception as e:
        print(f"Error in clear_data: {e}")
        return redirect(url_for('home'))

@app.route('/health')
def health_check():
    """
    Health check endpoint untuk monitoring
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'total_records': len(presensi_data)
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handler untuk 404 errors"""
    return render_template('index.html', data=presensi_data), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler untuk 500 errors"""
    return render_template('index.html', data=presensi_data), 500

# Vercel serverless function compatibility
def handler(request):
    """
    Handler function untuk Vercel serverless deployment
    """
    return app(request.environ, request.start_response)

# Local development
if __name__ == '__main__':
    # Mode development untuk testing lokal
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Production mode untuk Vercel
    app.debug = False
