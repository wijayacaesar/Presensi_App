from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from datetime import datetime, timedelta
import pytz
import hashlib
import secrets
import os
import math
from functools import wraps

app = Flask(__name__, template_folder='templates/', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

WIB = pytz.timezone('Asia/Jakarta')

ADMIN_CREDENTIALS = {
    'admin': hashlib.sha256('admin'.encode()).hexdigest()
}

EMPLOYEE_PINS = {
    'John Doe': '1234',
    'Jane Smith': '5678',
    'Ahmad Fauzi': '9999',
    'Siti Nurhaliza': '1111',
    'Budi Santoso': '2222',
    'Rina Wijaya': '3333'
}

OFFICE_LOCATION = {
    'latitude': -6.234055220571567,
    'longitude': 106.82199279535402,
    'radius_km': 2.0 
}

presensi_data = []
app_settings = {
    'title': 'Sistem Presensi Digital',
    'organization': 'PT. Wijaya Abadi',
    'version': '2.2.0',
    'theme': 'dark',
    'work_start_time': '08:00',
    'work_end_time': '17:00',
    'break_start_time': '12:00',
    'break_end_time': '13:00'
}

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Akses ditolak! Login sebagai admin terlebih dahulu.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_attendance_status(current_time, action_type='clock_in'):
    hour = current_time.hour
    minute = current_time.minute
    current_minutes = hour * 60 + minute
    
    if action_type == 'clock_in':
        work_start = 8 * 60
        late_threshold = 8 * 60 + 15
        
        if current_minutes < work_start:
            return 'Datang Awal', '🌅'
        elif current_minutes <= late_threshold:
            return 'Tepat Waktu', '✅'
        else:
            return 'Terlambat', '⏰'
    else:
        work_end = 17 * 60
        early_threshold = 17 * 60 - 30
        
        if current_minutes < early_threshold:
            return 'Pulang Awal', '🏃'
        elif current_minutes <= work_end:
            return 'Tepat Waktu', '✅'
        else:
            return 'Lembur', '🌙'

def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def is_location_valid(user_lat, user_lng):
    if not user_lat or not user_lng:
        return False
    
    distance = calculate_distance(
        float(user_lat), float(user_lng),
        OFFICE_LOCATION['latitude'], OFFICE_LOCATION['longitude']
    )
    
    return distance <= OFFICE_LOCATION['radius_km']

# ✅ ENHANCED: Improved work hours calculation
def calculate_work_hours(clock_in_time, clock_out_time):
    """
    Calculate work hours between clock in and clock out time
    Returns formatted string like "9:30" for 9 hours 30 minutes
    """
    if not clock_in_time or not clock_out_time:
        return "0:00"
    
    try:
        # Parse time strings to datetime objects
        clock_in = datetime.strptime(clock_in_time, '%H:%M:%S')
        clock_out = datetime.strptime(clock_out_time, '%H:%M:%S')
        
        # Handle case where clock out is next day
        if clock_out < clock_in:
            clock_out += timedelta(days=1)
        
        # Calculate work duration
        work_duration = clock_out - clock_in
        
        # Convert to hours and minutes
        total_seconds = work_duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        return f"{hours}:{minutes:02d}"
    
    except Exception as e:
        print(f"Error calculating work hours: {e}")
        return "0:00"

# ✅ ENHANCED: Better break time calculation
def calculate_effective_work_hours(clock_in_time, clock_out_time):
    """
    Calculate effective work hours excluding break time
    Assumes 1 hour break from 12:00-13:00
    """
    if not clock_in_time or not clock_out_time:
        return "0:00", "0:00"
    
    try:
        # Get total work hours
        total_hours = calculate_work_hours(clock_in_time, clock_out_time)
        
        # Parse times
        clock_in = datetime.strptime(clock_in_time, '%H:%M:%S')
        clock_out = datetime.strptime(clock_out_time, '%H:%M:%S')
        
        if clock_out < clock_in:
            clock_out += timedelta(days=1)
        
        # Break time boundaries
        break_start = datetime.strptime('12:00:00', '%H:%M:%S')
        break_end = datetime.strptime('13:00:00', '%H:%M:%S')
        
        # Check if work period overlaps with break time
        break_duration = 0
        if clock_in <= break_end and clock_out >= break_start:
            # Calculate overlap with break time
            overlap_start = max(clock_in, break_start)
            overlap_end = min(clock_out, break_end)
            if overlap_end > overlap_start:
                break_duration = (overlap_end - overlap_start).total_seconds() / 3600
        
        # Calculate effective hours
        total_seconds = (clock_out - clock_in).total_seconds()
        effective_seconds = total_seconds - (break_duration * 3600)
        
        effective_hours = int(effective_seconds // 3600)
        effective_minutes = int((effective_seconds % 3600) // 60)
        
        effective_time = f"{effective_hours}:{effective_minutes:02d}"
        
        return total_hours, effective_time
    
    except Exception as e:
        print(f"Error calculating effective work hours: {e}")
        return "0:00", "0:00"

@app.route('/')
def home():
    sorted_data = sorted(presensi_data, key=lambda x: x['timestamp'], reverse=True)
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
        'on_time': len([d for d in presensi_data if d.get('clock_in_status') == 'Tepat Waktu']),
        'late': len([d for d in presensi_data if d.get('clock_in_status') == 'Terlambat']),
        'early': len([d for d in presensi_data if d.get('clock_in_status') == 'Datang Awal']),
        'completed': len([d for d in presensi_data if d.get('clock_out') is not None])
    }
    
    return render_template('index.html',
                         data=sorted_data,
                         stats=stats,
                         settings=app_settings,
                         current_time=datetime.now(WIB),
                         is_admin=session.get('admin_logged_in', False),
                         employee_list=list(EMPLOYEE_PINS.keys()))

@app.route('/presensi', methods=['POST'])
def tambah_presensi():
    try:
        nama = request.form.get('nama', '').strip()
        pin = request.form.get('pin', '').strip()
        action = request.form.get('action', 'clock_in')
        keterangan = request.form.get('keterangan', '').strip()
        lokasi = request.form.get('lokasi', '').strip()
        user_lat = request.form.get('latitude', '')
        user_lng = request.form.get('longitude', '')
        
        # Validation
        if not nama or nama not in EMPLOYEE_PINS:
            flash('❌ Nama karyawan tidak terdaftar!', 'error')
            return redirect(url_for('home'))
        
        if not pin or EMPLOYEE_PINS[nama] != pin:
            flash('❌ PIN salah! Presensi ditolak.', 'error')
            return redirect(url_for('home'))
        
        if not is_location_valid(user_lat, user_lng):
            flash(f'❌ Anda tidak berada di area kantor! Distance: {calculate_distance(float(user_lat), float(user_lng), OFFICE_LOCATION["latitude"], OFFICE_LOCATION["longitude"]):.2f}km', 'error')
            return redirect(url_for('home'))
        
        now = datetime.now(WIB)
        today = now.date().strftime('%Y-%m-%d')
        
        # Find existing record
        existing_record = None
        for record in presensi_data:
            if record['nama'] == nama and record['date'] == today:
                existing_record = record
                break
        
        if action == 'clock_in':
            # ✅ CLOCK IN LOGIC
            if existing_record:
                flash(f'⚠️ {nama} sudah melakukan clock in hari ini pada {existing_record["clock_in"]}!', 'warning')
                return redirect(url_for('home'))
            
            status, icon = get_attendance_status(now, 'clock_in')
            needs_audit = bool(keterangan and keterangan.strip() != '')
            new_id = max([d['id'] for d in presensi_data], default=0) + 1
            
            presensi_data.append({
                'id': new_id,
                'nama': nama,
                'clock_in': now.strftime('%H:%M:%S'),
                'clock_out': None,
                'clock_in_status': status,
                'clock_out_status': None,
                'clock_in_icon': icon,
                'clock_out_icon': None,
                'date': today,
                'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': now.timestamp(),
                'keterangan': keterangan or '-',
                'lokasi': lokasi or 'Kantor',
                'latitude': float(user_lat) if user_lat else None,
                'longitude': float(user_lng) if user_lng else None,
                'day_name': now.strftime('%A'),
                'created_at': now.isoformat(),
                'pin_verified': True,
                'location_verified': True,
                'needs_audit': needs_audit,
                'audit_status': 'Pending' if needs_audit else 'Not Required',
                'work_hours': '0:00',
                'effective_work_hours': '0:00'
            })
            
            flash(f'✅ Clock In {nama} berhasil! Status: {status} {icon}', 'success')
            
        else:
            # ✅ ENHANCED CLOCK OUT LOGIC
            if not existing_record:
                flash(f'❌ {nama} belum melakukan clock in hari ini!', 'error')
                return redirect(url_for('home'))
            
            if existing_record.get('clock_out'):
                flash(f'⚠️ {nama} sudah melakukan clock out hari ini pada {existing_record["clock_out"]}!', 'warning')
                return redirect(url_for('home'))
            
            # Get clock out status
            status, icon = get_attendance_status(now, 'clock_out')
            
            # Update existing record with clock out data
            clock_out_time = now.strftime('%H:%M:%S')
            existing_record['clock_out'] = clock_out_time
            existing_record['clock_out_status'] = status
            existing_record['clock_out_icon'] = icon
            
            # ✅ CALCULATE WORK HOURS
            total_hours, effective_hours = calculate_effective_work_hours(
                existing_record['clock_in'], 
                clock_out_time
            )
            
            existing_record['work_hours'] = total_hours
            existing_record['effective_work_hours'] = effective_hours
            
            # Update other fields
            if keterangan:
                existing_record['keterangan'] = keterangan
                existing_record['needs_audit'] = True
                existing_record['audit_status'] = 'Pending'
            
            # Update location if different
            if lokasi:
                existing_record['lokasi'] = lokasi
            
            # Update last modified
            existing_record['clock_out_datetime'] = now.strftime('%Y-%m-%d %H:%M:%S')
            existing_record['last_updated'] = now.isoformat()
            
            flash(f'✅ Clock Out {nama} berhasil! Status: {status} {icon} | Total: {total_hours} | Efektif: {effective_hours}', 'success')
        
    except Exception as e:
        flash('❌ Terjadi kesalahan saat menyimpan presensi!', 'error')
        print(f"Error in tambah_presensi: {e}")
    
    return redirect(url_for('home'))

# ✅ ENHANCED: Debug route to test work hours calculation
@app.route('/test-work-hours')
def test_work_hours():
    test_cases = [
        ('08:00:00', '17:00:00'),  # Normal 9 hours
        ('08:30:00', '17:30:00'),  # 9 hours with 30 min late
        ('07:45:00', '18:15:00'),  # Early in, overtime
        ('09:00:00', '16:30:00'),  # Late in, early out
        ('10:00:00', '11:30:00'),  # Short day (no break)
    ]
    
    results = []
    for clock_in, clock_out in test_cases:
        total, effective = calculate_effective_work_hours(clock_in, clock_out)
        results.append({
            'clock_in': clock_in,
            'clock_out': clock_out,
            'total_hours': total,
            'effective_hours': effective
        })
    
    return jsonify({'test_results': results})

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
    today = datetime.now(WIB).date()
    
    daily_stats = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = len([d for d in presensi_data if d['date'] == date.strftime('%Y-%m-%d')])
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'count': count
        })
    
    status_stats = {
        'Tepat Waktu': len([d for d in presensi_data if d.get('clock_in_status') == 'Tepat Waktu']),
        'Terlambat': len([d for d in presensi_data if d.get('clock_in_status') == 'Terlambat']),
        'Datang Awal': len([d for d in presensi_data if d.get('clock_in_status') == 'Datang Awal']),
        'Completed': len([d for d in presensi_data if d.get('clock_out') is not None])
    }
    
    audit_data = [d for d in presensi_data if d.get('needs_audit', False)]
    
    return render_template('admin_dashboard.html',
                         data=presensi_data,
                         audit_data=audit_data,
                         daily_stats=daily_stats,
                         status_stats=status_stats,
                         settings=app_settings,
                         admin_username=session.get('admin_username'))

@app.route('/admin/audit/<int:record_id>/<action>')
@admin_required
def audit_record(record_id, action):
    try:
        record = next((d for d in presensi_data if d['id'] == record_id), None)
        if record and record.get('needs_audit', False):
            if action == 'approve':
                record['audit_status'] = 'Approved'
                record['audited_by'] = session.get('admin_username')
                record['audited_at'] = datetime.now(WIB).isoformat()
                flash(f'✅ Presensi {record["nama"]} telah disetujui!', 'success')
            elif action == 'reject':
                record['audit_status'] = 'Rejected'
                record['audited_by'] = session.get('admin_username')
                record['audited_at'] = datetime.now(WIB).isoformat()
                flash(f'❌ Presensi {record["nama"]} ditolak!', 'warning')
        else:
            flash('❌ Data tidak ditemukan atau tidak perlu audit!', 'error')
    except Exception as e:
        flash('❌ Gagal memproses audit!', 'error')
    
    return redirect(url_for('admin_dashboard'))

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
        export_data_obj = {
            'metadata': {
                'exported_at': datetime.now(WIB).isoformat(),
                'total_records': len(presensi_data),
                'app_version': app_settings['version'],
                'organization': app_settings['organization']
            },
            'settings': app_settings,
            'employee_pins': {name: '****' for name in EMPLOYEE_PINS.keys()},
            'office_location': OFFICE_LOCATION,
            'data': presensi_data
        }
        return jsonify(export_data_obj)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    today = datetime.now(WIB).date()
    return jsonify({
        'total': len(presensi_data),
        'today': len([d for d in presensi_data if d['date'] == today.strftime('%Y-%m-%d')]),
        'status_breakdown': {
            'on_time': len([d for d in presensi_data if d.get('clock_in_status') == 'Tepat Waktu']),
            'late': len([d for d in presensi_data if d.get('clock_in_status') == 'Terlambat']),
            'early': len([d for d in presensi_data if d.get('clock_in_status') == 'Datang Awal']),
            'completed': len([d for d in presensi_data if d.get('clock_out') is not None])
        },
        'audit_breakdown': {
            'pending': len([d for d in presensi_data if d.get('audit_status') == 'Pending']),
            'approved': len([d for d in presensi_data if d.get('audit_status') == 'Approved']),
            'rejected': len([d for d in presensi_data if d.get('audit_status') == 'Rejected'])
        },
        'last_updated': datetime.now(WIB).isoformat()
    })

application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
