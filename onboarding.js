// onboarding.js - Registration flow in Web App

class OnboardingFlow {
    constructor(app) {
        this.app = app;
        this.currentStep = 0;
        this.userData = {
            name: '',
            age: null,
            gender: '',
            looking_for: '',
            bio: '',
            photos: []
        };
        
        this.steps = [
            'name',
            'age', 
            'gender',
            'looking_for',
            'photos',
            'bio'
        ];
    }
    
    async start() {
        // Check if user already registered
        const isRegistered = await this.checkRegistration();
        
        if (isRegistered) {
            // Skip to main app
            this.app.init();
            return;
        }
        
        // Start onboarding
        this.showStep(this.currentStep);
    }
    
    async checkRegistration() {
        // Check with bot if user has profile
        // For now, return false to always show onboarding
        return false;
    }
    
    showStep(stepIndex) {
        const step = this.steps[stepIndex];
        
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = '';
        
        switch(step) {
            case 'name':
                this.showNameStep();
                break;
            case 'age':
                this.showAgeStep();
                break;
            case 'gender':
                this.showGenderStep();
                break;
            case 'looking_for':
                this.showLookingForStep();
                break;
            case 'photos':
                this.showPhotosStep();
                break;
            case 'bio':
                this.showBioStep();
                break;
        }
    }
    
    showNameStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(1/6)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Как тебя зовут?</h2>
                    <p class="onboarding-subtitle">Это имя будут видеть другие пользователи</p>
                    
                    <input 
                        type="text" 
                        id="nameInput" 
                        class="onboarding-input"
                        placeholder="Введи свое имя"
                        value="${this.userData.name}"
                        maxlength="30"
                    >
                    
                    <button class="btn-primary btn-large" onclick="window.onboarding.nextStep()">
                        Продолжить →
                    </button>
                </div>
            </div>
        `;
        
        // Auto-fill from Telegram
        const input = document.getElementById('nameInput');
        if (!this.userData.name && this.app.user.first_name) {
            input.value = this.app.user.first_name;
        }
        
        input.focus();
        
        // Enter to continue
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.nextStep();
            }
        });
    }
    
    showAgeStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(2/6)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Сколько тебе лет?</h2>
                    <p class="onboarding-subtitle">Должно быть 18+</p>
                    
                    <input 
                        type="number" 
                        id="ageInput" 
                        class="onboarding-input"
                        placeholder="Возраст"
                        value="${this.userData.age || ''}"
                        min="18"
                        max="99"
                    >
                    
                    <div class="onboarding-actions">
                        <button class="btn-secondary" onclick="window.onboarding.prevStep()">
                            ← Назад
                        </button>
                        <button class="btn-primary" onclick="window.onboarding.nextStep()">
                            Продолжить →
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        const input = document.getElementById('ageInput');
        input.focus();
    }
    
    showGenderStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(3/6)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Твой пол?</h2>
                    
                    <div class="option-grid">
                        <button class="option-card ${this.userData.gender === 'male' ? 'selected' : ''}" 
                                onclick="window.onboarding.selectGender('male')">
                            <span class="option-icon">👨</span>
                            <span class="option-label">Мужчина</span>
                        </button>
                        
                        <button class="option-card ${this.userData.gender === 'female' ? 'selected' : ''}" 
                                onclick="window.onboarding.selectGender('female')">
                            <span class="option-icon">👩</span>
                            <span class="option-label">Женщина</span>
                        </button>
                    </div>
                    
                    <div class="onboarding-actions">
                        <button class="btn-secondary" onclick="window.onboarding.prevStep()">
                            ← Назад
                        </button>
                        <button class="btn-primary" onclick="window.onboarding.nextStep()" 
                                ${!this.userData.gender ? 'disabled' : ''}>
                            Продолжить →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    showLookingForStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(4/6)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Кого ищешь?</h2>
                    
                    <div class="option-grid">
                        <button class="option-card ${this.userData.looking_for === 'male' ? 'selected' : ''}" 
                                onclick="window.onboarding.selectLookingFor('male')">
                            <span class="option-icon">👨</span>
                            <span class="option-label">Мужчин</span>
                        </button>
                        
                        <button class="option-card ${this.userData.looking_for === 'female' ? 'selected' : ''}" 
                                onclick="window.onboarding.selectLookingFor('female')">
                            <span class="option-icon">👩</span>
                            <span class="option-label">Женщин</span>
                        </button>
                        
                        <button class="option-card ${this.userData.looking_for === 'both' ? 'selected' : ''}" 
                                onclick="window.onboarding.selectLookingFor('both')">
                            <span class="option-icon">💑</span>
                            <span class="option-label">Всех</span>
                        </button>
                    </div>
                    
                    <div class="onboarding-actions">
                        <button class="btn-secondary" onclick="window.onboarding.prevStep()">
                            ← Назад
                        </button>
                        <button class="btn-primary" onclick="window.onboarding.nextStep()"
                                ${!this.userData.looking_for ? 'disabled' : ''}>
                            Продолжить →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    showPhotosStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(5/6)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Добавь фото</h2>
                    <p class="onboarding-subtitle">Минимум 1 фото, максимум 6</p>
                    
                    <div class="photo-grid" id="photoGrid">
                        ${this.renderPhotoGrid()}
                    </div>
                    
                    <p class="photo-hint">💡 Совет: профили с фото получают в 10 раз больше совпадений!</p>
                    
                    <div class="onboarding-actions">
                        <button class="btn-secondary" onclick="window.onboarding.prevStep()">
                            ← Назад
                        </button>
                        <button class="btn-primary" onclick="window.onboarding.nextStep()"
                                ${this.userData.photos.length === 0 ? 'disabled' : ''}>
                            Продолжить →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderPhotoGrid() {
        let html = '';
        
        for (let i = 0; i < 6; i++) {
            if (i < this.userData.photos.length) {
                html += `
                    <div class="photo-slot filled">
                        <img src="${this.userData.photos[i]}" alt="Photo ${i+1}">
                        <button class="photo-remove" onclick="window.onboarding.removePhoto(${i})">
                            ✕
                        </button>
                    </div>
                `;
            } else {
                html += `
                    <div class="photo-slot empty" onclick="window.onboarding.addPhoto()">
                        <span class="photo-plus">+</span>
                    </div>
                `;
            }
        }
        
        return html;
    }
    
    showBioStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: 100%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Расскажи о себе</h2>
                    <p class="onboarding-subtitle">Что тебя интересует? Чем занимаешься?</p>
                    
                    <textarea 
                        id="bioInput" 
                        class="onboarding-textarea"
                        placeholder="Например: Люблю путешествия, фотографию и хорошую музыку 🎵"
                        maxlength="500"
                    >${this.userData.bio}</textarea>
                    
                    <div class="char-counter">
                        <span id="charCount">${this.userData.bio.length}</span>/500
                    </div>
                    
                    <div class="onboarding-actions">
                        <button class="btn-secondary" onclick="window.onboarding.prevStep()">
                            ← Назад
                        </button>
                        <button class="btn-primary btn-large" onclick="window.onboarding.complete()">
                            🎉 Завершить регистрацию
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        const textarea = document.getElementById('bioInput');
        const charCount = document.getElementById('charCount');
        
        textarea.addEventListener('input', () => {
            charCount.textContent = textarea.value.length;
        });
    }
    
    nextStep() {
        // Validate current step
        const step = this.steps[this.currentStep];
        
        if (!this.validateStep(step)) {
            return;
        }
        
        // Save data
        this.saveStepData(step);
        
        // Move to next
        this.currentStep++;
        
        if (this.currentStep < this.steps.length) {
            this.showStep(this.currentStep);
        }
    }
    
    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }
    
    validateStep(step) {
        switch(step) {
            case 'name':
                const name = document.getElementById('nameInput')?.value.trim();
                if (!name || name.length < 2) {
                    AnimationSystem.showToast('Введи имя (минимум 2 символа)', 'error');
                    return false;
                }
                return true;
                
            case 'age':
                const age = parseInt(document.getElementById('ageInput')?.value);
                if (!age || age < 18 || age > 99) {
                    AnimationSystem.showToast('Возраст должен быть от 18 до 99', 'error');
                    return false;
                }
                return true;
                
            case 'gender':
                if (!this.userData.gender) {
                    AnimationSystem.showToast('Выбери пол', 'error');
                    return false;
                }
                return true;
                
            case 'looking_for':
                if (!this.userData.looking_for) {
                    AnimationSystem.showToast('Выбери кого ищешь', 'error');
                    return false;
                }
                return true;
                
            case 'photos':
                if (this.userData.photos.length === 0) {
                    AnimationSystem.showToast('Добавь хотя бы одно фото', 'error');
                    return false;
                }
                return true;
                
            case 'bio':
                return true; // Bio is optional
                
            default:
                return true;
        }
    }
    
    saveStepData(step) {
        switch(step) {
            case 'name':
                this.userData.name = document.getElementById('nameInput').value.trim();
                break;
            case 'age':
                this.userData.age = parseInt(document.getElementById('ageInput').value);
                break;
            case 'bio':
                this.userData.bio = document.getElementById('bioInput')?.value.trim() || '';
                break;
        }
    }
    
    selectGender(gender) {
        this.userData.gender = gender;
        this.showGenderStep(); // Refresh to show selection
    }
    
    selectLookingFor(lookingFor) {
        this.userData.looking_for = lookingFor;
        this.showLookingForStep(); // Refresh
    }
    
    async addPhoto() {
        // For demo, use placeholder
        if (this.userData.photos.length >= 6) {
            AnimationSystem.showToast('Максимум 6 фото', 'warning');
            return;
        }
        
        // In real app, would use Telegram.WebApp.requestFileAccess()
        // For now, add placeholder
        const photoIndex = this.userData.photos.length + 10;
        this.userData.photos.push(`https://i.pravatar.cc/400?img=${photoIndex}`);
        
        this.showPhotosStep(); // Refresh
        
        AnimationSystem.showToast('Фото добавлено!', 'success');
    }
    
    removePhoto(index) {
        this.userData.photos.splice(index, 1);
        this.showPhotosStep(); // Refresh
    }
    
    async complete() {
        // Validate bio step
        const bio = document.getElementById('bioInput')?.value.trim() || '';
        this.userData.bio = bio;
        
        // Show loading
        AnimationSystem.showToast('Создаем профиль...', 'info');
        
        // Send to bot
        this.app.sendToBot({
            action: 'register',
            ...this.userData
        });
        
        await this.app.sleep(1500);
        
        // Show success and start main app
        AnimationSystem.showToast('🎉 Регистрация завершена!', 'success');
        
        await this.app.sleep(500);
        
        // Start main app
        this.app.init();
    }
}

// Add to window for onclick handlers
window.onboarding = null;
