from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
import pytz
import json
import os

app = Flask(__name__, template_folder='templates/', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-for-flash-messages')

# Timezone Indonesia
WIB = pytz.timezone('Asia/Jakarta')

# In-memory storage dengan struktur yang lebih lengkap
presensi_data = []
admin_settings = {
    'title': 'Sistem Presensi Digital',
    'organization': 'PT. Teknologi Maju',
    'auto_clear_hours': 24,
    'require_keterangan': False
}

@app.route('/')
def home():
    # Sort data berdasarkan waktu terbaru
    sorted_data = sorted(presensi_data, key=lambda x: x['timestamp'], reverse=True)
    
    # Statistik
    today = datetime.now(WIB).date()
    today_count = len([d for d in presensi_data if d['date'] == today.strftime('%Y-%m-%d')])
    
    stats = {
        'total': len(presensi_data),
        'today': today_count,
        'this_week': len([d for d in presensi_data if 
                         datetime.strptime(d['date'], '%Y-%m-%d').date() >= 
                         (today - timedelta(days=today.weekday()))])
    }
    
    return render_template('index.html', 
                         data=sorted_data, 
                         stats=stats, 
                         settings=admin_settings,
                         current_time=datetime.now(WIB))

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    try:
        nama = request.form.get('nama', '').strip()
        keterangan = request.form.get('keterangan', '').strip()
        
        if not nama:
            flash('Nama tidak boleh kosong!', 'error')
            return redirect(url_for('home'))
        
        # Cek duplikasi nama hari ini
        today = datetime.now(WIB).date().strftime('%Y-%m-%d')
        existing = [d for d in presensi_data if d['nama'].lower() == nama.lower() and d['date'] == today]
        
        if existing:
            flash(f'{nama} sudah melakukan presensi hari ini!', 'warning')
            return redirect(url_for('home'))
        
        # Waktu Indonesia yang akurat
        now = datetime.now(WIB)
        
        # Tentukan status berdasarkan waktu
        status = 'Tepat Waktu'
        if now.hour < 8:
            status = 'Datang Awal'
        elif now.hour >= 9:
            status = 'Terlambat'
        
        presensi_data.append({
            'id': len(presensi_data) + 1,
            'nama': nama,
            'waktu': now.strftime('%H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': now.timestamp(),
            'status': status,
            'keterangan': keterangan,
            'day_name': now.strftime('%A')
        })
        
        flash(f'Presensi {nama} berhasil dicatat! Status: {status}', 'success')
        
    except Exception as e:
        flash('Terjadi kesalahan saat menyimpan presensi!', 'error')
        print(f"Error: {e}")
    
    return redirect(url_for('home'))

@app.route('/clear')
def clear_data():
    try:
        presensi_data.clear()
        flash('Semua data presensi berhasil dihapus!', 'success')
    except Exception as e:
        flash('Gagal menghapus data!', 'error')
    return redirect(url_for('home'))

@app.route('/export')
def export_data():
    """Export data ke format JSON untuk download"""
    try:
        return jsonify({
            'data': presensi_data,
            'exported_at': datetime.now(WIB).isoformat(),
            'total_records': len(presensi_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    """API endpoint untuk statistik real-time"""
    today = datetime.now(WIB).date()
    
    # Statistik per hari dalam seminggu terakhir
    daily_stats = {}
    for i in range(7):
        date = today - timedelta(days=i)
        count = len([d for d in presensi_data if d['date'] == date.strftime('%Y-%m-%d')])
        daily_stats[date.strftime('%Y-%m-%d')] = count
    
    return jsonify({
        'total': len(presensi_data),
        'today': len([d for d in presensi_data if d['date'] == today.strftime('%Y-%m-%d')]),
        'daily_stats': daily_stats,
        'status_breakdown': {
            'tepat_waktu': len([d for d in presensi_data if d['status'] == 'Tepat Waktu']),
            'terlambat': len([d for d in presensi_data if d['status'] == 'Terlambat']),
            'datang_awal': len([d for d in presensi_data if d['status'] == 'Datang Awal'])
        }
    })

@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    """Hapus record individual"""
    try:
        global presensi_data
        presensi_data = [d for d in presensi_data if d['id'] != record_id]
        flash('Data berhasil dihapus!', 'success')
    except Exception as e:
        flash('Gagal menghapus data!', 'error')
    return redirect(url_for('home'))

# Export app untuk Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
