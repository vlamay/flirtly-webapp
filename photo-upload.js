// photo-upload.js - Advanced photo upload system for Telegram Mini App

class PhotoUploadSystem {
    constructor() {
        this.maxPhotos = 6;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        this.qualitySettings = {
            maxWidth: 1080,
            maxHeight: 1080,
            quality: 0.8,
            format: 'image/webp'
        };
    }

    // ===================================
    // PHOTO SOURCE SELECTION
    // ===================================

    async showSourceSelector() {
        return new Promise((resolve) => {
            const modal = this.createSourceModal();
            document.body.appendChild(modal);
            
            modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
                if (e.target === e.currentTarget) {
                    this.closeModal(modal);
                    resolve(null);
                }
            });

            // Telegram camera button
            modal.querySelector('.btn-camera').addEventListener('click', () => {
                this.closeModal(modal);
                this.openTelegramCamera().then(resolve);
            });

            // Gallery button
            modal.querySelector('.btn-gallery').addEventListener('click', () => {
                this.closeModal(modal);
                this.openGallery().then(resolve);
            });
        });
    }

    createSourceModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-premium active';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-premium-content animate-fade-in-scale">
                <h3 class="modal-title">Выберите источник фото</h3>
                <p class="modal-subtitle">Откуда хотите загрузить фото?</p>
                
                <div class="photo-source-options">
                    <button class="btn-camera btn-premium">
                        <span class="btn-icon">📷</span>
                        <span class="btn-text">Сделать фото</span>
                        <span class="btn-description">Использовать камеру</span>
                    </button>
                    
                    <button class="btn-gallery btn-premium">
                        <span class="btn-icon">🖼️</span>
                        <span class="btn-text">Выбрать из галереи</span>
                        <span class="btn-description">Загрузить существующее</span>
                    </button>
                </div>
                
                <div class="photo-tips">
                    <h4>💡 Советы для лучших фото:</h4>
                    <ul>
                        <li>Хорошее освещение</li>
                        <li>Четкое изображение лица</li>
                        <li>Один человек на фото</li>
                        <li>Улыбка всегда приветствуется!</li>
                    </ul>
                </div>
            </div>
        `;
        return modal;
    }

    // ===================================
    // TELEGRAM CAMERA INTEGRATION
    // ===================================

    async openTelegramCamera() {
        try {
            if (window.Telegram && window.Telegram.WebApp) {
                // Method 1: Modern Telegram WebApp API
                if (window.Telegram.WebApp.openCamera) {
                    return await this.useModernTelegramCamera();
                }
                
                // Method 2: Legacy API with popup
                if (window.Telegram.WebApp.showPopup) {
                    return await this.useLegacyTelegramCamera();
                }
            }
            
            // Fallback to HTML5 camera
            return await this.useHTML5Camera();
            
        } catch (error) {
            console.error('Camera access failed:', error);
            this.showError('Не удалось открыть камеру. Попробуйте выбрать фото из галереи.');
            return null;
        }
    }

    async useModernTelegramCamera() {
        return new Promise((resolve, reject) => {
            window.Telegram.WebApp.openCamera(
                "Сделайте фото для профиля",
                (result) => {
                    if (result && result.files && result.files.length > 0) {
                        const file = result.files[0];
                        this.processPhoto(file).then(resolve).catch(reject);
                    } else {
                        reject(new Error('Фото не было выбрано'));
                    }
                }
            );
        });
    }

    async useLegacyTelegramCamera() {
        return new Promise((resolve, reject) => {
            window.Telegram.WebApp.showPopup({
                title: 'Доступ к камере',
                message: 'Разрешить Flirtly доступ к камере для создания фото профиля?',
                buttons: [
                    { id: 'allow', type: 'default', text: '📷 Разрешить' },
                    { id: 'gallery', type: 'default', text: '🖼️ Галерея' },
                    { type: 'cancel', text: '❌ Отмена' }
                ]
            }, async (buttonId) => {
                if (buttonId === 'allow') {
                    try {
                        const result = await this.useHTML5Camera();
                        resolve(result);
                    } catch (error) {
                        reject(error);
                    }
                } else if (buttonId === 'gallery') {
                    try {
                        const result = await this.openGallery();
                        resolve(result);
                    } catch (error) {
                        reject(error);
                    }
                } else {
                    reject(new Error('User cancelled'));
                }
            });
        });
    }

    async useHTML5Camera() {
        return new Promise((resolve, reject) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.capture = 'camera';
            
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        const result = await this.processPhoto(file);
                        resolve(result);
                    } catch (error) {
                        reject(error);
                    }
                } else {
                    reject(new Error('No file selected'));
                }
            };
            
            input.click();
        });
    }

    // ===================================
    // GALLERY ACCESS
    // ===================================

    async openGallery() {
        return new Promise((resolve, reject) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.multiple = false;
            
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        const result = await this.processPhoto(file);
                        resolve(result);
                    } catch (error) {
                        reject(error);
                    }
                } else {
                    reject(new Error('No file selected'));
                }
            };
            
            input.click();
        });
    }

    // ===================================
    // PHOTO PROCESSING
    // ===================================

    async processPhoto(file) {
        // Show processing modal
        const processingModal = this.showProcessingModal();
        
        try {
            // Step 1: Validate file
            await this.validateFile(file);
            
            // Step 2: Show compression progress
            this.updateProcessingProgress(processingModal, 20, 'Проверяем фото...');
            
            // Step 3: Compress and optimize
            const compressed = await this.compressImage(file);
            this.updateProcessingProgress(processingModal, 60, 'Оптимизируем фото...');
            
            // Step 4: Detect and crop face
            const cropped = await this.cropToFace(compressed);
            this.updateProcessingProgress(processingModal, 80, 'Metric: Обрезаем фото...');
            
            // Step 5: Final validation
            await this.validateProcessedPhoto(cropped);
            this.updateProcessingProgress(processingModal, 100, 'Готово!');
            
            // Close modal after delay
            setTimeout(() => {
                this.closeModal(processingModal);
            }, 500);
            
            return {
                file: cropped,
                url: URL.createObjectURL(cropped),
                size: cropped.size,
                dimensions: await this.getImageDimensions(cropped)
            };
            
        } catch (error) {
            this.closeModal(processingModal);
            throw error;
        }
    }

    async validateFile(file) {
        // Check file type
        if (!this.allowedTypes.includes(file.type)) {
            throw new Error('Неподдерживаемый формат файла. Используйте JPG, PNG или WebP.');
        }
        
        // Check file size
        if (file.size > this.maxFileSize) {
            throw new Error('Файл слишком большой. Максимальный размер: 5MB.');
        }
        
        // Check if it's actually an image
        const isValidImage = await this.validateImageContent(file);
        if (!isValidImage) {
            throw new Error('Файл не является изображением или поврежден.');
        }
    }

    async validateImageContent(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = URL.createObjectURL(file);
        });
    }

    async compressImage(file) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            img.onload = () => {
                // Calculate new dimensions
                let { width, height } = img;
                const maxSize = Math.max(this.qualitySettings.maxWidth, this.qualitySettings.maxHeight);
                
                if (width > maxSize || height > maxSize) {
                    const ratio = Math.min(maxSize / width, maxSize / height);
                    width *= ratio;
                    height *= ratio;
                }
                
                // Set canvas dimensions
                canvas.width = width;
                canvas.height = height;
                
                // Draw and compress
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob(
                    (blob) => resolve(blob),
                    this.qualitySettings.format,
                    this.qualitySettings.quality
                );
            };
            
            img.src = URL.createObjectURL(file);
        });
    }

    async cropToFace(imageFile) {
        // For now, return the image as-is
        // In production, you would integrate with face detection API
        return imageFile;
    }

    async validateProcessedPhoto(file) {
        // Additional validation for processed photo
        if (file.size > 2 * 1024 * 1024) { // 2MB after compression
            throw new Error('Фото все еще слишком большое после сжатия.');
        }
    }

    async getImageDimensions(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                resolve({
                    width: img.width,
                    height: img.height
                });
            };
            img.src = URL.createObjectURL(file);
        });
    }

    // ===================================
    // UI HELPERS
    // ===================================

    showProcessingModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-premium active';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-premium-content animate-fade-in-scale">
                <div class="processing-content">
                    <div class="processing-spinner">
                        <div class="spinner"></div>
                    </div>
                    <h3 class="processing-title">Обрабатываем фото</h3>
                    <p class="processing-status">Начинаем обработку...</p>
                    <div class="processing-progress">
                        <div class="progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        return modal;
    }

    updateProcessingProgress(modal, progress, status) {
        const progressBar = modal.querySelector('.progress-bar');
        const statusText = modal.querySelector('.processing-status');
        
        progressBar.style.width = `${progress}%`;
        statusText.textContent = status;
    }

    showError(message) {
        if (window.premiumUI) {
            window.premiumUI.error(message);
        } else {
            alert(message);
        }
    }

    closeModal(modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            if (modal.parentElement) {
                modal.parentElement.removeChild(modal);
            }
        }, 300);
    }
}

// CSS for photo upload components
const photoUploadStyles = document.createElement('style');
photoUploadStyles.textContent = `
    .photo-source-options {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-4);
        margin: var(--spacing-6) 0;
    }
    
    .photo-source-options .btn-premium {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--spacing-2);
        padding: var(--spacing-6);
        text-align: center;
    }
    
    .btn-icon {
        font-size: 32px;
    }
    
    .btn-text {
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
    }
    
    .btn-description {
        font-size: var(--font-size-sm);
        opacity: 0.7;
    }
    
    .photo-tips {
        background: var(--bg-glass);
        border-radius: var(--radius-lg);
        padding: var(--spacing-4);
        margin-top: var(--spacing-6);
    }
    
    .photo-tips h4 {
        margin-bottom: var(--spacing-3);
        color: var(--text-primary);
    }
    
    .photo-tips ul {
        list-style: none;
        padding: 0;
    }
    
    .photo-tips li {
        padding: var(--spacing-1) 0;
        color: var(--text-secondary);
    }
    
    .photo-tips li::before {
        content: '✓ ';
        color: var(--success);
        font-weight: bold;
    }
    
    .processing-content {
        text-align: center;
        padding: var(--spacing-6);
    }
    
    .processing-spinner {
        margin-bottom: var(--spacing-4);
    }
    
    .processing-title {
        margin-bottom: var(--spacing-2);
        color: var(--text-primary);
    }
    
    .processing-status {
        margin-bottom: var(--spacing-4);
        color: var(--text-secondary);
        font-size: var(--font-size-sm);
    }
    
    .processing-progress {
        width: 100%;
        height: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-full);
        overflow: hidden;
    }
    
    .processing-progress .progress-bar {
        height: 100%;
        background: var(--gradient-primary);
        border-radius: var(--radius-full);
        transition: width 0.3s ease;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid rgba(255, 255, 255, 0.1);
        border-top: 3px solid var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(photoUploadStyles);

// Export for use in other modules
window.PhotoUploadSystem = PhotoUploadSystem;
