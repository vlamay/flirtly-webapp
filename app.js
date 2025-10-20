// app.js - Main application logic

class FlirtlyApp {
    constructor() {
        // Telegram WebApp
        this.tg = window.Telegram.WebApp;
        this.tg.expand();
        this.tg.enableClosingConfirmation();
        
        // User data
        this.user = this.tg.initDataUnsafe.user || {
            id: 123456,
            first_name: 'Demo',
            username: 'demo_user'
        };
        
        // App state
        this.currentProfiles = [];
        this.currentIndex = 0;
        this.history = [];
        this.stats = {
            likesRemaining: 10,
            superLikes: 1,
            matchCount: 0
        };
        
        // Elements
        this.elements = {
            loadingState: document.getElementById('loadingState'),
            cardStack: document.getElementById('cardStack'),
            emptyState: document.getElementById('emptyState'),
            actionBar: document.getElementById('actionBar'),
            matchModal: document.getElementById('matchModal'),
            toastContainer: document.getElementById('toastContainer')
        };
        
        // Onboarding
        this.onboarding = null;
        this.isRegistered = false;
        
        // Initialize
        this.init();
    }
    
    async init() {
        console.log('Initializing Flirtly App...', this.user);
        
        // Check if user is registered
        this.isRegistered = await this.checkRegistration();
        
        if (!this.isRegistered) {
            // Show onboarding
            this.onboarding = new OnboardingFlow(this);
            window.onboarding = this.onboarding;
            await this.onboarding.start();
            return;
        }
        
        // Continue with normal app flow
        this.updateStats();
        this.setupButtons();
        await this.loadProfiles();
        this.setupTheme();
    }
    
    async checkRegistration() {
        // Check if user has complete profile
        // In real app, this would check with backend
        // For now, check localStorage or always show onboarding
        const hasProfile = localStorage.getItem('flirtly_profile_complete');
        return hasProfile === 'true';
    }
    
    setupTheme() {
        // Adapt to Telegram theme
        if (this.tg.colorScheme === 'dark') {
            document.body.style.background = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)';
        }
        
        // Listen for theme changes
        this.tg.onEvent('themeChanged', () => {
            if (this.tg.colorScheme === 'dark') {
                document.body.style.background = 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)';
            } else {
                document.body.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        });
    }
    
    setupButtons() {
        // Skip button
        document.getElementById('btnSkip')?.addEventListener('click', () => {
            this.handleAction('skip');
        });
        
        // Like button
        document.getElementById('btnLike')?.addEventListener('click', () => {
            this.handleAction('like');
        });
        
        // Superlike button
        document.getElementById('btnSuperlike')?.addEventListener('click', () => {
            this.handleAction('superlike');
        });
        
        // Undo button
        document.getElementById('btnUndo')?.addEventListener('click', () => {
            this.handleUndo();
        });
        
        // Info button
        document.getElementById('btnInfo')?.addEventListener('click', () => {
            this.showProfileInfo();
        });
        
        // Bottom nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                this.handleNavigation(e.currentTarget.dataset.page);
            });
        });
    }
    
    async loadProfiles() {
        this.showLoading(true);
        
        // Simulate API call
        await this.sleep(2000);
        
        // Demo profiles
        this.currentProfiles = this.generateDemoProfiles(10);
        this.currentIndex = 0;
        
        this.showLoading(false);
        
        if (this.currentProfiles.length > 0) {
            this.showCardStack();
            this.renderCards();
        } else {
            this.showEmptyState();
        }
    }
    
    generateDemoProfiles(count) {
        const names = [
            { name: 'Анна', age: 24, bio: 'Люблю путешествия и фотографию 📸', verified: true },
            { name: 'Мария', age: 26, bio: 'Дизайнер, обожаю кофе и книги ☕📚', verified: true },
            { name: 'Елена', age: 23, bio: 'Спорт, йога, здоровый образ жизни 🧘‍♀️', verified: false },
            { name: 'Ксения', age: 25, bio: 'Маркетолог днем, танцор ночью 💃', verified: true },
            { name: 'Дарья', age: 27, bio: 'Люблю животных и готовить 🐕👩‍🍳', verified: false },
            { name: 'София', age: 22, bio: 'Студентка, начинающий художник 🎨', verified: true },
            { name: 'Виктория', age: 28, bio: 'Предприниматель, всегда в движении 🚀', verified: true },
            { name: 'Алиса', age: 24, bio: 'Музыка - моя жизнь 🎵 Гитара и пение', verified: false },
            { name: 'Полина', age: 26, bio: 'HR-менеджер, люблю людей и психологию', verified: true },
            { name: 'Екатерина', age: 25, bio: 'Блогер о путешествиях ✈️ 15 стран', verified: true }
        ];
        
        const interests = [
            ['🎬 Кино', '🎵 Музыка', '📚 Книги'],
            ['☕ Кофе', '🍷 Вино', '🍕 Еда'],
            ['🏋️ Спорт', '🧘 Йога', '🏃 Бег'],
            ['✈️ Путешествия', '🏖️ Пляж', '⛰️ Горы'],
            ['🎨 Искусство', '📷 Фото', '🎭 Театр']
        ];
        
        return Array.from({ length: Math.min(count, names.length) }, (_, i) => ({
            id: i + 1,
            ...names[i],
            distance: Math.floor(Math.random() * 10) + 1,
            images: [
                `https://i.pravatar.cc/400?img=${i + 10}`,
                `https://i.pravatar.cc/400?img=${i + 20}`,
                `https://i.pravatar.cc/400?img=${i + 30}`
            ],
            tags: interests[Math.floor(Math.random() * interests.length)]
        }));
    }
    
    renderCards() {
        const stack = this.elements.cardStack;
        stack.innerHTML = '';
        
        // Render top 3 cards
        const cardsToRender = this.currentProfiles.slice(
            this.currentIndex, 
            this.currentIndex + 3
        );
        
        cardsToRender.forEach((profile, index) => {
            const card = this.createProfileCard(profile, index === 0);
            stack.appendChild(card);
        });
    }
    
    createProfileCard(profile, isTop) {
        const card = document.createElement('div');
        card.className = 'profile-card';
        card.dataset.profileId = profile.id;
        
        card.innerHTML = `
            <div class="card-images">
                ${profile.images.map((img, i) => `
                    <img src="${img}" 
                         alt="${profile.name}" 
                         class="card-image ${i === 0 ? 'active' : ''}"
                         loading="lazy">
                `).join('')}
                
                <div class="image-dots">
                    ${profile.images.map((_, i) => `
                        <div class="dot ${i === 0 ? 'active' : ''}"></div>
                    `).join('')}
                </div>
                
                <div class="swipe-indicator left">👎</div>
                <div class="swipe-indicator right">❤️</div>
            </div>
            
            <div class="card-info">
                <div class="card-name">
                    ${profile.name}, ${profile.age}
                    ${profile.verified ? '<span class="verified-badge">✓</span>' : ''}
                </div>
                
                <div class="card-details">
                    <div class="detail-item">
                        📍 ${profile.distance} км
                    </div>
                </div>
                
                <div class="card-bio">
                    ${profile.bio}
                </div>
                
                <div class="card-tags">
                    ${profile.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;
        
        // Setup swipe handler for top card
        if (isTop) {
            setTimeout(() => {
                new SwipeHandler(card, {
                    onSwipe: (direction) => {
                        const action = direction === 'right' ? 'like' : 'skip';
                        this.handleAction(action, false);
                    }
                });
                
                // Setup image carousel
                this.setupImageCarousel(card);
            }, 100);
        }
        
        return card;
    }
    
    setupImageCarousel(card) {
        const images = card.querySelectorAll('.card-image');
        const dots = card.querySelectorAll('.dot');
        let currentImage = 0;
        
        card.addEventListener('click', (e) => {
            const clickX = e.clientX;
            const cardWidth = card.offsetWidth;
            
            if (clickX > cardWidth / 2) {
                // Next image
                currentImage = (currentImage + 1) % images.length;
            } else {
                // Previous image
                currentImage = (currentImage - 1 + images.length) % images.length;
            }
            
            images.forEach((img, i) => {
                img.classList.toggle('active', i === currentImage);
            });
            
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i === currentImage);
            });
        });
    }
    
    async handleAction(action, animate = true) {
        if (this.currentIndex >= this.currentProfiles.length) {
            this.showEmptyState();
            return;
        }
        
        const profile = this.currentProfiles[this.currentIndex];
        const card = document.querySelector('.profile-card');
        
        // Check limits
        if (action === 'like' && this.stats.likesRemaining <= 0) {
            AnimationSystem.showToast('Лимит лайков исчерпан! 😔', 'warning');
            AnimationSystem.shake(card);
            this.showPremiumOffer();
            return;
        }
        
        if (action === 'superlike' && this.stats.superLikes <= 0) {
            AnimationSystem.showToast('Нет суперлайков! Получи Premium ⭐', 'warning');
            this.showPremiumOffer();
            return;
        }
        
        // Add to history for undo
        this.history.push({
            profile,
            action,
            index: this.currentIndex
        });
        
        // Update stats
        if (action === 'like') {
            this.stats.likesRemaining--;
        } else if (action === 'superlike') {
            this.stats.superLikes--;
        }
        
        this.updateStats();
        
        // Animate card out
        if (animate && card) {
            const swipeHandler = new SwipeHandler(card, {});
            swipeHandler.swipe(action === 'skip' ? 'left' : 'right');
        }
        
        // Send data to bot
        this.sendToBot({
            action,
            profile_id: profile.id
        });
        
        // Show feedback
        const messages = {
            skip: '👎 Пропущено',
            like: '❤️ Лайк отправлен!',
            superlike: '⭐ Суперлайк отправлен!'
        };
        
        AnimationSystem.showToast(messages[action], 'success', 2000);
        
        // Check for match (simulated)
        if (action !== 'skip' && Math.random() > 0.7) {
            setTimeout(() => this.showMatch(profile), 500);
        }
        
        // Move to next
        setTimeout(() => {
            this.currentIndex++;
            
            if (this.currentIndex >= this.currentProfiles.length) {
                this.showEmptyState();
            } else {
                this.renderCards();
            }
        }, animate ? 400 : 0);
    }
    
    handleUndo() {
        if (this.history.length === 0) {
            AnimationSystem.showToast('Нечего отменять', 'info');
            return;
        }
        
        const last = this.history.pop();
        
        // Restore stats
        if (last.action === 'like') {
            this.stats.likesRemaining++;
        } else if (last.action === 'superlike') {
            this.stats.superLikes++;
        }
        
        this.updateStats();
        
        // Go back
        this.currentIndex = last.index;
        this.renderCards();
        
        AnimationSystem.showToast('↩️ Действие отменено', 'info');
        AnimationSystem.vibrate([10]);
    }
    
    showMatch(profile) {
        this.stats.matchCount++;
        this.updateStats();
        
        const modal = this.elements.matchModal;
        modal.classList.add('active');
        
        // Setup match avatars
        document.getElementById('matchAvatar1').src = profile.images[0];
        document.getElementById('matchAvatar2').src = `https://i.pravatar.cc/100?img=99`;
        
        // Confetti!
        const confettiContainer = document.getElementById('matchConfetti');
        AnimationSystem.createConfetti(confettiContainer);
        
        // Vibrate
        AnimationSystem.vibrate([50, 100, 50]);
        
        // Play sound (if available)
        this.playSound('match');
    }
    
    showProfileInfo() {
        const profile = this.currentProfiles[this.currentIndex];
        if (!profile) return;
        
        const message = `
<b>${profile.name}, ${profile.age}</b>
${profile.verified ? '✓ Верифицирован' : ''}

📍 Расстояние: ${profile.distance} км

${profile.bio}

${profile.tags.join(' ')}
        `.trim();
        
        this.tg.showPopup({
            title: 'Информация о профиле',
            message: message,
            buttons: [{ type: 'close' }]
        });
    }
    
    showPremiumOffer() {
        this.tg.showPopup({
            title: '⭐ Premium подписка',
            message: 'Получи безлимитные лайки и суперлайки с Premium подпиской!',
            buttons: [
                { id: 'premium', type: 'default', text: 'Подробнее' },
                { type: 'cancel' }
            ]
        }, (buttonId) => {
            if (buttonId === 'premium') {
                this.handleNavigation('premium');
            }
        });
    }
    
    updateStats() {
        document.getElementById('likesRemaining').textContent = this.stats.likesRemaining;
        document.getElementById('superLikes').textContent = this.stats.superLikes;
        document.getElementById('matchCount').textContent = this.stats.matchCount;
    }
    
    showLoading(show) {
        this.elements.loadingState.style.display = show ? 'block' : 'none';
        this.elements.cardStack.style.display = show ? 'none' : 'block';
        this.elements.actionBar.style.display = show ? 'none' : 'flex';
    }
    
    showCardStack() {
        this.elements.loadingState.style.display = 'none';
        this.elements.cardStack.style.display = 'block';
        this.elements.emptyState.style.display = 'none';
        this.elements.actionBar.style.display = 'flex';
    }
    
    showEmptyState() {
        this.elements.loadingState.style.display = 'none';
        this.elements.cardStack.style.display = 'none';
        this.elements.emptyState.style.display = 'block';
        this.elements.actionBar.style.display = 'none';
    }
    
    handleNavigation(page) {
        console.log('Navigate to:', page);
        
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Handle navigation
        switch(page) {
            case 'discover':
                this.loadProfiles();
                break;
            case 'matches':
                AnimationSystem.showToast('💕 Раздел Матчи', 'info');
                break;
            case 'chats':
                AnimationSystem.showToast('💬 Раздел Чаты', 'info');
                break;
            case 'profile':
                AnimationSystem.showToast('👤 Раздел Профиль', 'info');
                break;
        }
    }
    
    sendToBot(data) {
        console.log('Sending to bot:', data);
        
        // Send data back to Telegram bot
        try {
            this.tg.sendData(JSON.stringify(data));
        } catch (e) {
            console.error('Failed to send data:', e);
        }
    }
    
    playSound(type) {
        // Placeholder for sound effects
        // You can add actual sound files and play them here
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global functions for HTML onclick handlers
window.closeMatchModal = function() {
    document.getElementById('matchModal').classList.remove('active');
};

window.openChat = function() {
    AnimationSystem.showToast('💬 Открываем чат...', 'success');
    closeMatchModal();
};

window.inviteFriends = function() {
    AnimationSystem.showToast('🎁 Открываем реферальную программу...', 'info');
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new FlirtlyApp();
    });
} else {
    window.app = new FlirtlyApp();
}
