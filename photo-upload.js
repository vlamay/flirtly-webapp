// photo-upload.js - Fixed Photo Upload System for Telegram Web App

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
    // MAIN GALLERY ACCESS
    // ===================================

    async openGallery() {
        console.log('🟡 Открываем галерею...');
        
        try {
            // Создаем простой input для выбора файла
            return new Promise((resolve, reject) => {
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = 'image/*,image/jpeg,image/png,image/webp';
                fileInput.multiple = false;
                fileInput.style.display = 'none';
                
                fileInput.onchange = async (event) => {
                    console.log('📁 Файл выбран, обрабатываем...');
                    
                    const file = event.target.files[0];
                    if (!file) {
                        console.log('❌ Файл не выбран');
                        reject(new Error('Файл не выбран'));
                        return;
                    }
                    
                    console.log('📁 Файл:', file.name, file.size, file.type);
                    
                    try {
                        // Простая валидация
                        if (!this.allowedTypes.includes(file.type)) {
                            throw new Error('Неподдерживаемый формат файла');
                        }
                        
                        if (file.size > this.maxFileSize) {
                            throw new Error('Файл слишком большой');
                        }
                        
                        // Создаем URL для превью
                        const previewUrl = URL.createObjectURL(file);
                        
                        console.log('✅ Фото готово:', previewUrl);
                        
                        // Очищаем input
                        if (fileInput.parentElement) {
                            fileInput.parentElement.removeChild(fileInput);
                        }
                        
                        resolve({
                            file: file,
                            url: previewUrl,
                            size: file.size
                        });
                        
                    } catch (error) {
                        console.error('❌ Ошибка обработки фото:', error);
                        if (fileInput.parentElement) {
                            fileInput.parentElement.removeChild(fileInput);
                        }
                        reject(error);
                    }
                };
                
                // Добавляем в DOM и запускаем выбор
                document.body.appendChild(fileInput);
                fileInput.click();
            });
            
        } catch (error) {
            console.error('❌ Ошибка открытия галереи:', error);
            throw error;
        }
    }

    // ===================================
    // SIMPLE PHOTO PROCESSING
    // ===================================

    async processPhoto(file) {
        try {
            console.log('🔄 Обрабатываем фото...');
            
            // Простая обработка - создаем превью
            const previewUrl = URL.createObjectURL(file);
            
            return {
                file: file,
                url: previewUrl,
                size: file.size,
                name: file.name
            };
            
        } catch (error) {
            console.error('❌ Ошибка обработки фото:', error);
            throw error;
        }
    }

    // ===================================
    // ERROR HANDLING
    // ===================================

    showError(message) {
        console.error('❌ Photo Upload Error:', message);
        
        const userMessage = this.getUserFriendlyMessage(message);
        
        if (window.premiumUI) {
            window.premiumUI.error(userMessage);
        } else if (window.AnimationSystem) {
            window.AnimationSystem.showToast(userMessage, 'error');
        } else {
            alert(userMessage);
        }
    }

    getUserFriendlyMessage(error) {
        const messages = {
            'File not selected': 'Файл не выбран',
            'File too large': 'Файл слишком большой. Максимальный размер: 5MB',
            'Invalid file type': 'Неподдерживаемый формат файла. Используйте JPG, PNG или WebP',
            'Неподдерживаемый формат файла': 'Неподдерживаемый формат файла. Используйте JPG, PNG или WebP',
            'Файл слишком большой': 'Файл слишком большой. Максимальный размер: 5MB'
        };
        
        for (const [key, message] of Object.entries(messages)) {
            if (error.includes(key)) {
                return message;
            }
        }
        
        return 'Не удалось загрузить фото. Попробуйте еще раз.';
    }

    // ===================================
    // TESTING
    // ===================================

    async testPhotoUpload() {
        console.log('🧪 Тестируем загрузку фото...');
        
        try {
            const result = await this.openGallery();
            console.log('✅ Тест успешен:', result);
            return result;
        } catch (error) {
            console.error('❌ Тест провалился:', error);
            throw error;
        }
    }

    static async quickTest() {
        const uploader = new PhotoUploadSystem();
        return await uploader.testPhotoUpload();
    }
}

// CSS for photo upload
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
`;
document.head.appendChild(photoUploadStyles);

// Export for use in other modules
window.PhotoUploadSystem = PhotoUploadSystem;

// Global testing functions
window.testPhotoUpload = () => PhotoUploadSystem.quickTest();

window.debugPhotoUpload = async () => {
    console.log('🧪 Запускаем диагностику загрузки фото...');
    
    try {
        // Check Telegram WebApp
        if (window.Telegram?.WebApp) {
            console.log('✅ Telegram WebApp доступен');
        } else {
            console.log('⚠️ Telegram WebApp недоступен');
        }

        // Test upload
        const result = await window.testPhotoUpload();
        console.log('✅ Тест успешен:', result);
        return result;
        
    } catch (error) {
        console.error('❌ Тест провалился:', error);
        throw error;
    }
};