// premium-ui.js - Premium UI/UX enhancements for Telegram Mini App

class PremiumUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.setupAnimations();
        this.setupMicroInteractions();
        this.setupHapticFeedback();
        this.setupPremiumComponents();
    }

    // ===================================
    // THEME SYSTEM
    // ===================================

    setupThemeToggle() {
        // Auto-detect system theme
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('flirtly_theme');
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            this.setTheme(prefersDark ? 'dark' : 'light');
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('flirtly_theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('flirtly_theme', theme);
        
        // Update Telegram WebApp theme
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.setHeaderColor(theme === 'dark' ? '#1e1b4b' : '#6366f1');
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
        
        // Animate theme transition
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    // ===================================
    // ANIMATION SYSTEM
    // ===================================

    setupAnimations() {
        // Intersection Observer for scroll animations
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-slide-in-up');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observe all cards and components
        document.querySelectorAll('.card, .profile-card, .btn, .onboarding-content').forEach(el => {
            this.observer.observe(el);
        });
    }

    // Stagger animation for multiple elements
    staggerAnimation(elements, animationClass = 'animate-slide-in-up', delay = 100) {
        elements.forEach((el, index) => {
            setTimeout(() => {
                el.classList.add(animationClass);
            }, index * delay);
        });
    }

    // ===================================
    // MICRO INTERACTIONS
    // ===================================

    setupMicroInteractions() {
        // Button ripple effect
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn, .btn-primary, .btn-secondary, .btn-premium')) {
                this.createRipple(e);
            }
        });

        // Card hover effects
        document.querySelectorAll('.card, .profile-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });

        // Input focus effects
        document.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
            });
        });
    }

    createRipple(event) {
        const button = event.target;
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
            z-index: 1;
        `;

        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    // ===================================
    // HAPTIC FEEDBACK
    // ===================================

    setupHapticFeedback() {
        // Light haptic feedback for button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn, .btn-primary, .btn-secondary')) {
                this.hapticFeedback('light');
            }
        });

        // Medium haptic for important actions
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-danger, .btn-premium')) {
                this.hapticFeedback('medium');
            }
        });

        // Heavy haptic for matches and important events
        this.hapticFeedback = (type = 'light') => {
            if (window.Telegram && window.Telegram.WebApp) {
                switch (type) {
                    case 'light':
                        window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
                        break;
                    case 'medium':
                        window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
                        break;
                    case 'heavy':
                        window.Telegram.WebApp.HapticFeedback.impactOccurred('heavy');
                        break;
                    case 'success':
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                        break;
                    case 'error':
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
                        break;
                    case 'warning':
                        window.Telegram.WebApp.HapticFeedback.notificationOccurred('warning');
                        break;
                }
            }
        };
    }

    // ===================================
    // PREMIUM COMPONENTS
    // ===================================

    setupPremiumComponents() {
        this.setupProgressBars();
        this.setupToggles();
        this.setupTooltips();
        this.setupModals();
        this.setupSkeletons();
    }

    setupProgressBars() {
        document.querySelectorAll('.progress-premium').forEach(progress => {
            const progressValue = progress.getAttribute('data-progress');
            if (progressValue) {
                progress.setAttribute('data-progress', progressValue);
            }
        });
    }

    setupToggles() {
        document.querySelectorAll('.toggle-premium').forEach(toggle => {
            toggle.addEventListener('click', () => {
                toggle.classList.toggle('active');
                this.hapticFeedback('light');
            });
        });
    }

    setupTooltips() {
        document.querySelectorAll('.tooltip-premium').forEach(tooltip => {
            tooltip.addEventListener('mouseenter', () => {
                tooltip.classList.add('tooltip-active');
            });
            
            tooltip.addEventListener('mouseleave', () => {
                tooltip.classList.remove('tooltip-active');
            });
        });
    }

    setupModals() {
        // Modal open/close functionality
        window.openModal = (modalId) => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
                this.hapticFeedback('light');
            }
        };

        window.closeModal = (modalId) => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        };

        // Close modal on backdrop click
        document.querySelectorAll('.modal-premium').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        });
    }

    setupSkeletons() {
        // Replace skeletons with actual content when loaded
        document.querySelectorAll('.skeleton-premium').forEach(skeleton => {
            // Simulate loading
            setTimeout(() => {
                skeleton.classList.remove('skeleton-premium');
                skeleton.classList.add('animate-fade-in-scale');
            }, 1500);
        });
    }

    // ===================================
    // PREMIUM TOAST NOTIFICATIONS
    // ===================================

    showPremiumToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast-premium toast-${type} animate-slide-in-down`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;

        // Add toast styles if not already added
        if (!document.getElementById('toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'toast-styles';
            styles.textContent = `
                .toast-premium {
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: var(--bg-card);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: var(--radius-xl);
                    padding: var(--spacing-4) var(--spacing-6);
                    box-shadow: var(--shadow-xl);
                    z-index: var(--z-toast);
                    max-width: 400px;
                    width: 90%;
                }
                
                .toast-content {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-3);
                }
                
                .toast-icon {
                    font-size: 20px;
                }
                
                .toast-message {
                    color: var(--text-primary);
                    font-weight: var(--font-weight-medium);
                }
                
                .toast-close {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    margin-left: auto;
                }
                
                .toast-success { border-left: 4px solid var(--success); }
                .toast-error { border-left: 4px solid var(--danger); }
                .toast-warning { border-left: 4px solid var(--warning); }
                .toast-info { border-left: 4px solid var(--info); }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slide-in-down 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);

        this.hapticFeedback(type === 'error' ? 'error' : 'light');
    }

    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    // ===================================
    // PREMIUM LOADING STATES
    // ===================================

    showPremiumLoader(container, message = 'Загрузка...') {
        const loader = document.createElement('div');
        loader.className = 'premium-loader';
        loader.innerHTML = `
            <div class="loader-content">
                <div class="loader-spinner"></div>
                <p class="loader-message">${message}</p>
            </div>
        `;

        // Add loader styles if not already added
        if (!document.getElementById('loader-styles')) {
            const styles = document.createElement('style');
            styles.id = 'loader-styles';
            styles.textContent = `
                .premium-loader {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: var(--bg-overlay);
                    backdrop-filter: blur(8px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: var(--z-modal);
                }
                
                .loader-content {
                    text-align: center;
                    color: var(--text-primary);
                }
                
                .loader-spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid rgba(255, 255, 255, 0.1);
                    border-top: 3px solid var(--primary);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto var(--spacing-4);
                }
                
                .loader-message {
                    font-weight: var(--font-weight-medium);
                    opacity: 0.8;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(styles);
        }

        container.style.position = 'relative';
        container.appendChild(loader);
        
        return loader;
    }

    hidePremiumLoader(container) {
        const loader = container.querySelector('.premium-loader');
        if (loader) {
            loader.remove();
        }
    }

    // ===================================
    // PREMIUM CONFETTI EFFECT
    // ===================================

    showConfetti() {
        // Create confetti particles
        for (let i = 0; i < 50; i++) {
            this.createConfettiParticle();
        }
        
        this.hapticFeedback('success');
    }

    createConfettiParticle() {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: ${this.getRandomColor()};
            top: -10px;
            left: ${Math.random() * 100}%;
            z-index: var(--z-toast);
            animation: confetti-fall ${2 + Math.random() * 3}s linear forwards;
            pointer-events: none;
        `;

        // Add confetti animation if not already added
        if (!document.getElementById('confetti-styles')) {
            const styles = document.createElement('style');
            styles.id = 'confetti-styles';
            styles.textContent = `
                @keyframes confetti-fall {
                    0% {
                        transform: translateY(-100vh) rotate(0deg);
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(100vh) rotate(720deg);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(particle);

        setTimeout(() => {
            particle.remove();
        }, 5000);
    }

    getRandomColor() {
        const colors = ['#6366f1', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    // ===================================
    // PREMIUM SCROLL EFFECTS
    // ===================================

    setupScrollEffects() {
        let ticking = false;

        const updateScrollEffects = () => {
            const scrollY = window.scrollY;
            const header = document.querySelector('.header');
            
            if (header) {
                if (scrollY > 50) {
                    header.classList.add('header-scrolled');
                } else {
                    header.classList.remove('header-scrolled');
                }
            }
            
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollEffects);
                ticking = true;
            }
        });
    }

    // ===================================
    // PUBLIC API
    // ===================================

    // Method to trigger premium animations
    animateElement(element, animationClass = 'animate-slide-in-up') {
        element.classList.add(animationClass);
    }

    // Method to show premium notification
    notify(message, type = 'info') {
        this.showPremiumToast(message, type);
    }

    // Method to show success with confetti
    celebrate(message = '🎉 Успешно!') {
        this.showPremiumToast(message, 'success');
        setTimeout(() => this.showConfetti(), 500);
    }

    // Method to show error
    error(message) {
        this.showPremiumToast(message, 'error');
        this.hapticFeedback('error');
    }
}

// Initialize Premium UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.premiumUI = new PremiumUI();
});

// Add ripple animation styles
const rippleStyles = document.createElement('style');
rippleStyles.textContent = `
    @keyframes ripple {
        0% {
            transform: scale(0);
            opacity: 1;
        }
        100% {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyles);
