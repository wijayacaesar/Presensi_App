from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from datetime import datetime, timedelta
import pytz
import hashlib
import secrets
import os
from functools import wraps

app = Flask(__name__, template_folder='templates/', static_folder='../static/')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Timezone Indonesia
WIB = pytz.timezone('Asia/Jakarta')

# Admin credentials (dalam production gunakan database)
ADMIN_CREDENTIALS = {
    'admin': hashlib.sha256('admin123'.encode()).hexdigest(),
    'supervisor': hashlib.sha256('super456'.encode()).hexdigest()
}

# Data storage dengan struktur lengkap
presensi_data = []
app_settings = {
    'title': 'Sistem Presensi Digital',
    'organization': 'PT. Wijaya Abadi',
    'version': '2.0.0',
    'theme': 'dark',
    'max_daily_entries': 1,
    'work_start_time': '08:00',
    'work_end_time': '17:00',
    'break_start_time': '12:00',
    'break_end_time': '13:00'
}

def admin_required(f):
    """Decorator untuk route yang memerlukan admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Akses ditolak! Login sebagai admin terlebih dahulu.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_attendance_status(current_time):
    """Menentukan status kehadiran berdasarkan waktu"""
    hour = current_time.hour
    minute = current_time.minute
    
    # Convert work times to minutes for easier comparison
    work_start = 8 * 60  # 08:00 in minutes
    late_threshold = 8 * 60 + 15  # 08:15 in minutes
    current_minutes = hour * 60 + minute
    
    if current_minutes < work_start:
        return 'Datang Awal', '🌅'
    elif current_minutes <= late_threshold:
        return 'Tepat Waktu', '✅'
    else:
        return 'Terlambat', '⏰'

@app.route('/')
def home():
    # Sort data berdasarkan waktu terbaru
    sorted_data = sorted(presensi_data, key=lambda x: x['timestamp'], reverse=True)
    
    # Statistik lengkap
    today = datetime.now(WIB).date()
    this_week_start = today - timedelta(days=today.weekday())
    this_month_start = today.replace(day=1)
    
    stats = {
        'total': len(presensi_data),
        'today': len([d for d in presensi_data if d['date'] == today.strftime('%Y-%m-%d')]),
        'this_week': len([d for d in presensi_data if 
                         datetime.strptime(d['date'], '%Y-%m-%d').date() >= this_week_start]),
        'this_month': len([d for d in presensi_data if 
                          datetime.strptime(d['date'], '%Y-%m-%d').date() >= this_month_start]),
        'on_time': len([d for d in presensi_data if d['status'] == 'Tepat Waktu']),
        'late': len([d for d in presensi_data if d['status'] == 'Terlambat']),
        'early': len([d for d in presensi_data if d['status'] == 'Datang Awal'])
    }
    
    return render_template('index.html', 
                         data=sorted_data, 
                         stats=stats, 
                         settings=app_settings,
                         current_time=datetime.now(WIB),
                         is_admin=session.get('admin_logged_in', False))

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    try:
        nama = request.form.get('nama', '').strip().title()
        keterangan = request.form.get('keterangan', '').strip()
        lokasi = request.form.get('lokasi', '').strip()
        
        if not nama or len(nama) < 2:
            flash('Nama harus diisi minimal 2 karakter!', 'error')
            return redirect(url_for('home'))
        
        # Cek duplikasi nama hari ini
        today = datetime.now(WIB).date().strftime('%Y-%m-%d')
        existing = [d for d in presensi_data if d['nama'].lower() == nama.lower() and d['date'] == today]
        
        if existing and app_settings['max_daily_entries'] == 1:
            flash(f'{nama} sudah melakukan presensi hari ini pada {existing[0]["waktu"]}!', 'warning')
            return redirect(url_for('home'))
        
        # Waktu Indonesia yang akurat
        now = datetime.now(WIB)
        status, icon = get_attendance_status(now)
        
        # Generate unique ID
        new_id = max([d['id'] for d in presensi_data], default=0) + 1
        
        presensi_data.append({
            'id': new_id,
            'nama': nama,
            'waktu': now.strftime('%H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': now.timestamp(),
            'status': status,
            'status_icon': icon,
            'keterangan': keterangan or '-',
            'lokasi': lokasi or 'Kantor',
            'day_name': now.strftime('%A'),
            'created_at': now.isoformat()
        })
        
        flash(f'✅ Presensi {nama} berhasil dicatat! Status: {status} {icon}', 'success')
        
    except Exception as e:
        flash('❌ Terjadi kesalahan saat menyimpan presensi!', 'error')
        print(f"Error: {e}")
    
    return redirect(url_for('home'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username in ADMIN_CREDENTIALS:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if ADMIN_CREDENTIALS[username] == hashed_password:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                flash(f'🎉 Selamat datang, {username.title()}!', 'success')
                return redirect(url_for('admin_dashboard'))
        
        flash('❌ Username atau password salah!', 'error')
    
    return render_template('admin_login.html', settings=app_settings)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('👋 Anda telah logout dari panel admin.', 'info')
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Advanced statistics
    today = datetime.now(WIB).date()
    
    # Daily statistics for the last 7 days
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = len([d for d in presensi_data if d['date'] == date.strftime('%Y-%m-%d')])
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'count': count
        })
    
    # Hourly distribution
    hourly_stats = {}
    for hour in range(24):
        hourly_stats[f"{hour:02d}:00"] = len([
            d for d in presensi_data 
            if int(d['waktu'].split(':')[0]) == hour
        ])
    
    # Status distribution
    status_stats = {
        'Tepat Waktu': len([d for d in presensi_data if d['status'] == 'Tepat Waktu']),
        'Terlambat': len([d for d in presensi_data if d['status'] == 'Terlambat']),
        'Datang Awal': len([d for d in presensi_data if d['status'] == 'Datang Awal'])
    }
    
    return render_template('admin_dashboard.html',
                         data=presensi_data,
                         daily_stats=daily_stats,
                         hourly_stats=hourly_stats,
                         status_stats=status_stats,
                         settings=app_settings,
                         admin_username=session.get('admin_username'))

@app.route('/admin/delete/<int:record_id>')
@admin_required
def delete_record(record_id):
    try:
        global presensi_data
        deleted_record = next((d for d in presensi_data if d['id'] == record_id), None)
        if deleted_record:
            presensi_data = [d for d in presensi_data if d['id'] != record_id]
            flash(f'🗑️ Data presensi {deleted_record["nama"]} berhasil dihapus!', 'success')
        else:
            flash('❌ Data tidak ditemukan!', 'error')
    except Exception as e:
        flash('❌ Gagal menghapus data!', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/clear')
@admin_required
def clear_all_data():
    try:
        count = len(presensi_data)
        presensi_data.clear()
        flash(f'🗑️ Berhasil menghapus {count} data presensi!', 'success')
    except Exception as e:
        flash('❌ Gagal menghapus data!', 'error')
    
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/export')
def export_data():
    try:
        export_data = {
            'metadata': {
                'exported_at': datetime.now(WIB).isoformat(),
                'total_records': len(presensi_data),
                'app_version': app_settings['version'],
                'organization': app_settings['organization']
            },
            'settings': app_settings,
            'data': presensi_data
        }
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    today = datetime.now(WIB).date()
    return jsonify({
        'total': len(presensi_data),
        'today': len([d for d in presensi_data if d['date'] == today.strftime('%Y-%m-%d')]),
        'status_breakdown': {
            'on_time': len([d for d in presensi_data if d['status'] == 'Tepat Waktu']),
            'late': len([d for d in presensi_data if d['status'] == 'Terlambat']),
            'early': len([d for d in presensi_data if d['status'] == 'Datang Awal'])
        },
        'last_updated': datetime.now(WIB).isoformat()
    })

# Export app untuk Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
