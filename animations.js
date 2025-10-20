// animations.js - Animations and visual effects

class AnimationSystem {
    
    // Confetti effect for matches
    static createConfetti(container) {
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];
        const confettiCount = 100;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'absolute';
            confetti.style.width = Math.random() * 10 + 5 + 'px';
            confetti.style.height = Math.random() * 10 + 5 + 'px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.opacity = '1';
            confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            
            container.appendChild(confetti);
            
            // Animate
            const duration = Math.random() * 3 + 2;
            const delay = Math.random() * 0.5;
            const rotation = Math.random() * 720 - 360;
            const drift = Math.random() * 100 - 50;
            
            confetti.animate([
                {
                    transform: `translate(0, 0) rotate(0deg)`,
                    opacity: 1
                },
                {
                    transform: `translate(${drift}px, ${window.innerHeight}px) rotate(${rotation}deg)`,
                    opacity: 0
                }
            ], {
                duration: duration * 1000,
                delay: delay * 1000,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
                fill: 'forwards'
            });
            
            // Remove after animation
            setTimeout(() => {
                confetti.remove();
            }, (duration + delay) * 1000);
        }
    }
    
    // Toast notification system
    static showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${message}</span>
        `;
        
        container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        return toast;
    }
    
    // Haptic feedback (if available)
    static vibrate(pattern = [10]) {
        if ('vibrate' in navigator) {
            navigator.vibrate(pattern);
        }
    }
    
    // Card flip animation
    static flipCard(element, onComplete) {
        element.animate([
            { transform: 'rotateY(0deg)' },
            { transform: 'rotateY(90deg)' },
            { transform: 'rotateY(0deg)' }
        ], {
            duration: 600,
            easing: 'ease-in-out'
        }).onfinish = onComplete;
    }
    
    // Shake animation for errors
    static shake(element) {
        element.animate([
            { transform: 'translateX(0)' },
            { transform: 'translateX(-10px)' },
            { transform: 'translateX(10px)' },
            { transform: 'translateX(-10px)' },
            { transform: 'translateX(10px)' },
            { transform: 'translateX(0)' }
        ], {
            duration: 400,
            easing: 'ease-in-out'
        });
        
        this.vibrate([10, 50, 10]);
    }
    
    // Pulse animation
    static pulse(element, scale = 1.1) {
        element.animate([
            { transform: 'scale(1)' },
            { transform: `scale(${scale})` },
            { transform: 'scale(1)' }
        ], {
            duration: 300,
            easing: 'ease-in-out'
        });
    }
    
    // Skeleton loader
    static createSkeletonLoader(container) {
        container.innerHTML = `
            <div class="skeleton-card">
                <div class="skeleton-image"></div>
                <div class="skeleton-content">
                    <div class="skeleton-line" style="width: 60%;"></div>
                    <div class="skeleton-line" style="width: 40%;"></div>
                    <div class="skeleton-line" style="width: 80%;"></div>
                </div>
            </div>
        `;
    }
    
    // Number counter animation
    static animateNumber(element, from, to, duration = 500) {
        const startTime = performance.now();
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(from + (to - from) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }
}

// Export for use in other files
window.AnimationSystem = AnimationSystem;

// Add skeleton loader CSS dynamically
const skeletonStyles = document.createElement('style');
skeletonStyles.textContent = `
    .skeleton-card {
        background: white;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    
    .skeleton-image {
        width: 100%;
        height: 400px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
    }
    
    .skeleton-content {
        padding: 20px;
    }
    
    .skeleton-line {
        height: 16px;
        margin-bottom: 12px;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 4px;
    }
    
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
`;
document.head.appendChild(skeletonStyles);
