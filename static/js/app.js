// Modern JavaScript untuk interaktivitas
document.addEventListener('DOMContentLoaded', function() {
    // Update waktu real-time
    updateTime();
    setInterval(updateTime, 1000);
    
    // Auto-hide flash messages
    setTimeout(hideFlashMessages, 5000);
    
    // Form validation
    setupFormValidation();
    
    // Konfirmasi hapus data
    setupDeleteConfirmation();
    
    // Auto-refresh stats
    setInterval(updateStats, 30000);
});

function updateTime() {
    const now = new Date();
    const options = {
        timeZone: 'Asia/Jakarta',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    
    const timeString = now.toLocaleTimeString('id-ID', options);
    const dateString = now.toLocaleDateString('id-ID', {
        timeZone: 'Asia/Jakarta',
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const timeElement = document.querySelector('.time-display');
    const dateElement = document.querySelector('.date-display');
    
    if (timeElement) timeElement.textContent = timeString;
    if (dateElement) dateElement.textContent = dateString;
}

function hideFlashMessages() {
    const messages = document.querySelectorAll('.flash-message');
    messages.forEach(message => {
        message.style.transition = 'opacity 0.5s ease';
        message.style.opacity = '0';
        setTimeout(() => message.remove(), 500);
    });
}

function setupFormValidation() {
    const form = document.querySelector('form');
    const namaInput = document.querySelector('input[name="nama"]');
    
    if (form && namaInput) {
        form.addEventListener('submit', function(e) {
            const nama = namaInput.value.trim();
            if (nama.length < 2) {
                e.preventDefault();
                showNotification('Nama harus minimal 2 karakter!', 'error');
                namaInput.focus();
            }
        });
        
        namaInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-Z\s]/g, '');
        });
    }
}

function setupDeleteConfirmation() {
    const deleteButtons = document.querySelectorAll('a[href*="/delete/"]');
    const clearButton = document.querySelector('a[href*="/clear"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Yakin ingin menghapus data ini?')) {
                e.preventDefault();
            }
        });
    });
    
    if (clearButton) {
        clearButton.addEventListener('click', function(e) {
            if (!confirm('Yakin ingin menghapus SEMUA data presensi?')) {
                e.preventDefault();
            }
        });
    }
}

function updateStats() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            document.querySelector('.stat-total .stat-number').textContent = data.total;
            document.querySelector('.stat-today .stat-number').textContent = data.today;
        })
        .catch(error => console.log('Stats update failed:', error));
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.innerHTML = `
        <span>📢</span>
        <span>${message}</span>
    `;
    
    const container = document.querySelector('.flash-messages') || document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Export data functionality
function exportData() {
    fetch('/export')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `presensi-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('Data berhasil diexport!', 'success');
        })
        .catch(error => {
            showNotification('Gagal export data!', 'error');
        });
}
