document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    updateTime();
    setInterval(updateTime, 1000);
    setupFormValidation();
    setupDeleteConfirmations();
    autoHideFlashMessages();
    setupKeyboardShortcuts();
    setInterval(updateStats, 30000);
    addGlowEffects();
    setupScrollAnimations();
    console.log('🚀 Clock In/Out System Initialized');
}

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
    
    if (timeElement) {
        timeElement.textContent = timeString;
        if (now.getSeconds() % 2 === 0) {
            timeElement.style.textShadow = '0 0 20px var(--neon-blue)';
        } else {
            timeElement.style.textShadow = '0 0 10px var(--neon-blue)';
        }
    }
    
    if (dateElement) dateElement.textContent = dateString;
}

function setupFormValidation() {
    const form = document.getElementById('attendanceForm');
    const namaInput = document.getElementById('nama');
    const pinInput = document.getElementById('pin');
    const actionInput = document.getElementById('action');
    const submitBtn = document.getElementById('submitBtn');
    
    if (form && namaInput && pinInput && actionInput) {
        pinInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            
            if (this.value.length === 4) {
                this.style.borderColor = 'var(--neon-green)';
                this.style.boxShadow = '0 0 10px rgba(104, 211, 145, 0.3)';
            } else {
                this.style.borderColor = 'var(--accent-error)';
                this.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.3)';
            }
        });
        
        actionInput.addEventListener('change', function() {
            const action = this.value;
            const submitBtn = document.getElementById('submitBtn');
            
            if (action === 'clock_in') {
                submitBtn.innerHTML = '<span>🌅</span> Clock In';
                submitBtn.style.background = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)';
            } else {
                submitBtn.innerHTML = '<span>🌙</span> Clock Out';
                submitBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        });
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const nama = namaInput.value.trim();
            const pin = pinInput.value.trim();
            const action = actionInput.value;
            
            if (!nama) {
                showNotification('Pilih nama Anda!', 'error');
                namaInput.focus();
                return;
            }
            
            if (pin.length !== 4) {
                showNotification('PIN harus 4 digit!', 'error');
                pinInput.focus();
                return;
            }
            
            if (!action) {
                showNotification('Pilih aksi Clock In atau Clock Out!', 'error');
                actionInput.focus();
                return;
            }
            
            getLocationAndSubmit();
        });
    }
}

function getLocationAndSubmit() {
    const submitBtn = document.getElementById('submitBtn');
    const form = document.getElementById('attendanceForm');
    const action = document.getElementById('action').value;
    
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner"></span> Getting Location...';
    submitBtn.disabled = true;
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lng;
                
                if (action === 'clock_in') {
                    submitBtn.innerHTML = '<span class="spinner"></span> Processing Clock In...';
                } else {
                    submitBtn.innerHTML = '<span class="spinner"></span> Processing Clock Out...';
                }
                
                setTimeout(() => {
                    form.submit();
                }, 500);
            },
            function(error) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                
                let errorMsg = 'Gagal mendapatkan lokasi! ';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMsg += 'Izinkan akses lokasi untuk melanjutkan.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMsg += 'Informasi lokasi tidak tersedia.';
                        break;
                    case error.TIMEOUT:
                        errorMsg += 'Request timeout.';
                        break;
                    default:
                        errorMsg += 'Error tidak diketahui.';
                        break;
                }
                showNotification(errorMsg, 'error');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    } else {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        showNotification('Browser tidak mendukung geolocation!', 'error');
    }
}

function setupDeleteConfirmations() {
    document.querySelectorAll('a[href*="/delete/"]').forEach(button => {
        button.addEventListener('click', function(e) {
            const nama = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            if (!confirm(`🗑️ Hapus data presensi ${nama}?\n\nTindakan ini tidak dapat dibatalkan!`)) {
                e.preventDefault();
            }
        });
    });
    
    const clearButton = document.querySelector('a[href*="/clear"]');
    if (clearButton) {
        clearButton.addEventListener('click', function(e) {
            if (!confirm('⚠️ PERINGATAN!\n\nAnda akan menghapus SEMUA data presensi!\nTindakan ini tidak dapat dibatalkan!\n\nLanjutkan?')) {
                e.preventDefault();
            }
        });
    }
}

function autoHideFlashMessages() {
    const messages = document.querySelectorAll('.flash-message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            const form = document.getElementById('attendanceForm');
            if (form) {
                const submitEvent = new Event('submit');
                form.dispatchEvent(submitEvent);
            }
        }
        
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            refreshData();
        }
        
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            exportData();
        }
        
        if (e.ctrlKey && e.key === '1') {
            e.preventDefault();
            const actionSelect = document.getElementById('action');
            if (actionSelect) {
                actionSelect.value = 'clock_in';
                actionSelect.dispatchEvent(new Event('change'));
            }
        }
        
        if (e.ctrlKey && e.key === '2') {
            e.preventDefault();
            const actionSelect = document.getElementById('action');
            if (actionSelect) {
                actionSelect.value = 'clock_out';
                actionSelect.dispatchEvent(new Event('change'));
            }
        }
    });
}

function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatNumber('.stat-total .stat-number', data.total);
            updateStatNumber('.stat-today .stat-number', data.today);
            updateStatNumber('.stat-completed .stat-number', data.status_breakdown.completed);
            console.log('📊 Stats updated:', data);
        })
        .catch(error => console.log('Stats update failed:', error));
}

function updateStatNumber(selector, newValue) {
    const element = document.querySelector(selector);
    if (element) {
        const currentValue = parseInt(element.textContent);
        if (currentValue !== newValue) {
            element.style.transform = 'scale(1.2)';
            element.style.color = 'var(--neon-green)';
            element.textContent = newValue;
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.color = 'var(--neon-blue)';
            }, 300);
        }
    }
}

function addGlowEffects() {
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.filter = 'brightness(1.2)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.filter = 'brightness(1)';
        });
    });
    
    document.querySelectorAll('.stat-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 0 30px rgba(0, 212, 255, 0.4)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.boxShadow = 'var(--shadow-lg)';
        });
    });
}

function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.stat-card, .form-section, .data-section').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

function exportData() {
    const exportBtn = document.querySelector('button[onclick="exportData()"]');
    if (exportBtn) {
        exportBtn.innerHTML = '<span class="spinner"></span> Exporting...';
        exportBtn.disabled = true;
    }
    
    fetch('/export')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('📥 Data berhasil diexport!', 'success');
        })
        .catch(error => {
            showNotification('❌ Gagal export data!', 'error');
            console.error('Export error:', error);
        })
        .finally(() => {
            if (exportBtn) {
                exportBtn.innerHTML = '<span>📥</span> Export';
                exportBtn.disabled = false;
            }
        });
}

function refreshData() {
    showNotification('🔄 Refreshing data...', 'info');
    setTimeout(() => {
        location.reload();
    }, 1000);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: '📢'
    };
    
    notification.innerHTML = `
        <span>${icons[type] || '📢'}</span>
        <span>${message}</span>
    `;
    
    const container = document.querySelector('.flash-messages') || document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => notification.remove(), 500);
    }, 4000);
}

function initAdvancedFeatures() {
    const title = document.querySelector('.header h1');
    if (title) {
        const text = title.textContent;
        title.textContent = '';
        let i = 0;
        
        const typeWriter = () => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        setTimeout(typeWriter, 500);
    }
    
    createParticleEffect();
}

function createParticleEffect() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.3';
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    
    for (let i = 0; i < 50; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 2 + 1
        });
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(0, 212, 255, 0.5)';
        
        particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
        });
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

setTimeout(initAdvancedFeatures, 1000);
