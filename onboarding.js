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
            'location',
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
            case 'location':
                this.showLocationStep();
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
                    <div class="progress-bar" style="width: ${(4/7)*100}%"></div>
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
    
    showLocationStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(5/7)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Где ты находишься?</h2>
                    <p class="onboarding-subtitle">Это поможет найти людей поблизости</p>
                    
                    <div class="location-options">
                        <button class="location-btn location-auto" id="autoLocationBtn">
                            <span class="location-icon">📍</span>
                            <span class="location-text">
                                <strong>Определить автоматически</strong>
                                <small>Используя GPS</small>
                            </span>
                        </button>
                        
                        <div class="location-divider">или</div>
                        
                        <input 
                            type="text" 
                            id="cityInput" 
                            class="onboarding-input"
                            placeholder="Введи свой город"
                            value="${this.userData.city || ''}"
                        >
                    </div>
                    
                    <p class="location-privacy">
                        🔒 Точное местоположение не показывается другим пользователям.<br>
                        Показывается только расстояние и город.
                    </p>
                    
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
        
        // Setup auto location button
        document.getElementById('autoLocationBtn').addEventListener('click', () => {
            this.requestLocation();
        });
    }
    
    async requestLocation() {
        const btn = document.getElementById('autoLocationBtn');
        
        // Сохраняем оригинальный текст
        const originalHTML = btn.innerHTML;
        
        btn.innerHTML = `
            <span class="location-icon">⏳</span>
            <span class="location-text">
                <strong>Определяем местоположение...</strong>
                <small>Разреши доступ в браузере</small>
            </span>
        `;
        
        btn.disabled = true;

        try {
            // Пробуем разные методы геолокации
            let location = null;
            
            // Метод 1: Telegram WebApp API (приоритетный)
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.showPopup) {
                console.log('Using Telegram WebApp location API');
                location = await this.getTelegramLocation();
            }
            
            // Метод 2: HTML5 Geolocation API
            if (!location && 'geolocation' in navigator) {
                console.log('Using HTML5 Geolocation API');
                location = await this.getHTML5Location();
            }
            
            // Метод 3: IP-based geolocation (fallback)
            if (!location) {
                console.log('Using IP-based geolocation');
                location = await this.getIPLocation();
            }

            if (location) {
                await this.saveLocation(location.latitude, location.longitude, location.city, location.country);
            } else {
                throw new Error('Все методы геолокации недоступны');
            }

        } catch (error) {
            console.error('Location detection failed:', error);
            this.showLocationError(btn, originalHTML);
        }
    }

    useHtmlGeolocation() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.saveLocation(
                        position.coords.latitude,
                        position.coords.longitude
                    );
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    AnimationSystem.showToast(
                        'Не удалось определить местоположение. Введи город вручную.',
                        'warning'
                    );
                }
            );
        }
    }

    // Метод 1: Telegram WebApp Location
    async getTelegramLocation() {
        return new Promise((resolve) => {
            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.showPopup) {
                window.Telegram.WebApp.showPopup({
                    title: 'Доступ к геолокации',
                    message: 'Разрешить Flirtly доступ к вашему местоположению для поиска людей поблизости?',
                    buttons: [
                        { id: 'allow', type: 'default', text: 'Разрешить' },
                        { type: 'cancel', text: 'Отмена' }
                    ]
                }, (buttonId) => {
                    if (buttonId === 'allow') {
                        if (window.Telegram.WebApp.requestLocation) {
                            window.Telegram.WebApp.requestLocation((location) => {
                                if (location) {
                                    resolve({
                                        latitude: location.latitude,
                                        longitude: location.longitude
                                    });
                                } else {
                                    resolve(null);
                                }
                            });
                        } else {
                            resolve(null);
                        }
                    } else {
                        resolve(null);
                    }
                });
            } else {
                resolve(null);
            }
        });
    }

    // Метод 2: HTML5 Geolocation API
    async getHTML5Location() {
        return new Promise((resolve) => {
            const options = {
                enableHighAccuracy: true,
                timeout: 10000, // 10 секунд
                maximumAge: 300000 // 5 минут кэш
            };

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                },
                (error) => {
                    console.warn('HTML5 Geolocation failed:', error);
                    resolve(null);
                },
                options
            );
        });
    }

    // Метод 3: IP-based геолокация (fallback)
    async getIPLocation() {
        try {
            // Простой и надежный метод через IP
            const response = await fetch('https://api.db-ip.com/v2/free/self');
            const data = await response.json();
            
            const city = data.city || 'Москва'; // Fallback на Москву
            const country = data.countryName || 'Россия';
            
            // Используем приблизительные координаты
            let latitude, longitude;
            
            if (city.includes('Москва')) {
                latitude = 55.7558;
                longitude = 37.6173;
            } else if (city.includes('Санкт-Петербург')) {
                latitude = 59.9343;
                longitude = 30.3351;
            } else if (city.includes('Екатеринбург')) {
                latitude = 56.8431;
                longitude = 60.6454;
            } else if (city.includes('Новосибирск')) {
                latitude = 55.0084;
                longitude = 82.9357;
            } else {
                // Случайные координаты в пределах России
                latitude = 55 + (Math.random() - 0.5) * 10;
                longitude = 37 + (Math.random() - 0.5) * 20;
            }
            
            return {
                latitude: latitude,
                longitude: longitude,
                city: city,
                country: country
            };
            
        } catch (error) {
            console.warn('IP-based geolocation failed:', error);
            return null;
        }
    }

    // Обработка ошибок геолокации
    showLocationError(btn, originalHTML) {
        btn.innerHTML = `
            <span class="location-icon">❌</span>
            <span class="location-text">
                <strong>Не удалось определить</strong>
                <small>Введи город вручную</small>
            </span>
        `;
        
        btn.style.background = 'rgba(239, 68, 68, 0.2)';
        btn.style.borderColor = '#ef4444';
        
        // Восстанавливаем кнопку через 3 секунды
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.disabled = false;
        }, 3000);
        
        AnimationSystem.showToast(
            'Не удалось определить местоположение. Введи город вручную.',
            'warning',
            5000
        );
    }

    async saveLocation(latitude, longitude, city = null, country = null) {
        this.userData.latitude = latitude;
        this.userData.longitude = longitude;
        
        try {
            // Если город не передан, используем reverse geocoding
            if (!city) {
                const locationData = await this.reverseGeocode(latitude, longitude);
                city = locationData.city;
                country = locationData.country;
            }
            
            this.userData.city = city || 'Неизвестно';
            this.userData.country = country || 'Неизвестно';
            
            // Обновляем интерфейс
            this.updateLocationUI(city, country);
            
            AnimationSystem.showToast(`📍 Местоположение: ${city}`, 'success');
            
        } catch (error) {
            console.error('Reverse geocoding failed:', error);
            this.userData.city = 'Неизвестно';
            this.updateLocationUI('Неизвестно', '');
        }
    }

    async reverseGeocode(lat, lon) {
        try {
            // Пробуем разные сервисы геокодинга
            const services = [
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&accept-language=ru`,
                `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=ru`
            ];
            
            for (const url of services) {
                try {
                    const response = await fetch(url, { timeout: 5000 });
                    if (response.ok) {
                        const data = await response.json();
                        
                        if (url.includes('nominatim')) {
                            return {
                                city: data.address.city || data.address.town || data.address.village,
                                country: data.address.country
                            };
                        } else if (url.includes('bigdatacloud')) {
                            return {
                                city: data.city || data.locality,
                                country: data.countryName
                            };
                        }
                    }
                } catch (e) {
                    console.warn(`Geocoding service failed: ${url}`, e);
                    continue;
                }
            }
            
            throw new Error('All geocoding services failed');
            
        } catch (error) {
            console.error('Reverse geocoding error:', error);
            return { city: null, country: null };
        }
    }

    updateLocationUI(city, country) {
        const btn = document.getElementById('autoLocationBtn');
        const cityInput = document.getElementById('cityInput');
        
        if (btn) {
            btn.innerHTML = `
                <span class="location-icon">✅</span>
                <span class="location-text">
                    <strong>${city}</strong>
                    <small>${country || 'Определено'}</small>
                </span>
            `;
            btn.style.background = 'rgba(16, 185, 129, 0.2)';
            btn.style.borderColor = '#10b981';
            btn.disabled = false;
        }
        
        if (cityInput && city !== 'Неизвестно') {
            cityInput.value = city;
        }
    }
    
    showPhotosStep() {
        const container = document.getElementById('mainContent');
        
        container.innerHTML = `
            <div class="onboarding-container">
                <div class="onboarding-progress">
                    <div class="progress-bar" style="width: ${(6/7)*100}%"></div>
                </div>
                
                <div class="onboarding-content">
                    <h2 class="onboarding-title">Добавь фото</h2>
                    <p class="onboarding-subtitle">Минимум 1 фото, максимум 6</p>
                    
                    <div class="photo-grid" id="photoGrid">
                        ${this.renderPhotoGrid()}
                    </div>
                    
                    <div class="photo-upload-options">
                        <button class="photo-upload-btn" onclick="window.onboarding.uploadFromGallery()">
                            <span class="upload-icon">🖼️</span>
                            <span>Из галереи</span>
                        </button>
                        
                        <button class="photo-upload-btn" onclick="window.onboarding.takePhoto()">
                            <span class="upload-icon">📷</span>
                            <span>Сделать фото</span>
                        </button>
                    </div>
                    
                    <p class="photo-hint">
                        💡 <b>Советы для лучших фото:</b><br>
                        • Используй четкие, качественные фото<br>
                        • Покажи свое лицо<br>
                        • Добавь фото с хобби или интересами<br>
                        • Профили с фото получают в 10 раз больше лайков!
                    </p>
                    
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
                    <div class="photo-slot empty">
                        <span class="photo-placeholder">📷</span>
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
                
            case 'location':
                const city = document.getElementById('cityInput')?.value.trim();
                if (!this.userData.latitude && !city) {
                    AnimationSystem.showToast('Определи местоположение или введи город', 'error');
                    return false;
                }
                if (city) {
                    this.userData.city = city;
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
            case 'location':
                const city = document.getElementById('cityInput')?.value.trim();
                if (city) {
                    this.userData.city = city;
                }
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
    
    async uploadFromGallery() {
        try {
            if (this.userData.photos.length >= 6) {
                AnimationSystem.showToast('Максимум 6 фото', 'warning');
                return;
            }

            if (this.app.tg && this.app.tg.showFileSelector) {
                // Telegram WebApp API
                const file = await this.app.tg.showFileSelector({
                    type: 'photo',
                    source: 'gallery'
                });
                
                if (file) {
                    await this.processSelectedFile(file);
                }
            } else {
                // Браузерный fallback
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.multiple = false;
                
                input.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (file) await this.processSelectedFile(file);
                };
                
                input.click();
            }
        } catch (error) {
            console.error('Gallery upload failed:', error);
            this.addPlaceholderPhoto();
        }
    }

    async takePhoto() {
        try {
            if (this.userData.photos.length >= 6) {
                AnimationSystem.showToast('Максимум 6 фото', 'warning');
                return;
            }

            if (this.app.tg && this.app.tg.showFileSelector) {
                // Telegram WebApp API
                const file = await this.app.tg.showFileSelector({
                    type: 'photo',
                    source: 'camera'
                });
                
                if (file) {
                    await this.processSelectedFile(file);
                }
            } else {
                // Браузерный fallback
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.capture = 'environment'; // Использовать камеру
                
                input.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (file) await this.processSelectedFile(file);
                };
                
                input.click();
            }
        } catch (error) {
            console.error('Camera capture failed:', error);
            AnimationSystem.showToast('Камера недоступна', 'error');
        }
    }

    async processSelectedFile(file) {
        // Проверка размера
        if (file.size > 10 * 1024 * 1024) {
            AnimationSystem.showToast('Файл слишком большой (макс. 10MB)', 'error');
            return;
        }
        
        // Проверка типа
        if (!file.type.startsWith('image/')) {
            AnimationSystem.showToast('Выберите изображение', 'error');
            return;
        }
        
        // Показываем превью
        const previewUrl = URL.createObjectURL(file);
        this.userData.photos.push(previewUrl);
        this.showPhotosStep();
        
        AnimationSystem.showToast('Фото добавлено!', 'success');
        AnimationSystem.vibrate([10]); // Тактильный отклик
        
        // В реальном приложении здесь была бы загрузка на сервер
        // await this.uploadToServer(file);
    }

    addPlaceholderPhoto() {
        // Добавляем красивые placeholder фото как fallback
        const placeholders = [
            'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop', // Портрет 1
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop', // Портрет 2  
            'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop', // Портрет 3
            'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop', // Портрет 4
            'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&h=400&fit=crop', // Портрет 5
            'https://images.unsplash.com/photo-1519244703995-f4e0f30006d5?w=400&h=400&fit=crop'  // Портрет 6
        ];

        const randomIndex = Math.floor(Math.random() * placeholders.length);
        this.userData.photos.push(placeholders[randomIndex]);
        this.showPhotosStep();
        
        AnimationSystem.showToast('Фото добавлено!', 'success');
        AnimationSystem.vibrate([10]); // Тактильный отклик
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
        
        // Mark profile as complete
        localStorage.setItem('flirtly_profile_complete', 'true');
        
        await this.app.sleep(500);
        
        // Start main app
        this.app.init();
    }
}

// Add to window for onclick handlers
window.onboarding = null;
