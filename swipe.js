// swipe.js - Tinder-like swipe mechanics

class SwipeHandler {
    constructor(element, callbacks = {}) {
        this.element = element;
        this.callbacks = callbacks;
        
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.isDragging = false;
        
        this.threshold = 100; // Minimum distance for swipe
        this.rotation = 15; // Max rotation in degrees
        
        this.init();
    }
    
    init() {
        // Touch events
        this.element.addEventListener('touchstart', (e) => this.handleStart(e), { passive: false });
        this.element.addEventListener('touchmove', (e) => this.handleMove(e), { passive: false });
        this.element.addEventListener('touchend', (e) => this.handleEnd(e));
        
        // Mouse events (for desktop testing)
        this.element.addEventListener('mousedown', (e) => this.handleStart(e));
        this.element.addEventListener('mousemove', (e) => this.handleMove(e));
        this.element.addEventListener('mouseup', (e) => this.handleEnd(e));
        this.element.addEventListener('mouseleave', (e) => this.handleEnd(e));
    }
    
    handleStart(e) {
        e.preventDefault();
        this.isDragging = true;
        
        const point = e.touches ? e.touches[0] : e;
        this.startX = point.clientX;
        this.startY = point.clientY;
        
        this.element.classList.add('swiping');
        
        if (this.callbacks.onStart) {
            this.callbacks.onStart();
        }
    }
    
    handleMove(e) {
        if (!this.isDragging) return;
        e.preventDefault();
        
        const point = e.touches ? e.touches[0] : e;
        this.currentX = point.clientX - this.startX;
        this.currentY = point.clientY - this.startY;
        
        // Calculate rotation based on X position
        const rotate = (this.currentX / window.innerWidth) * this.rotation;
        
        // Apply transform
        this.element.style.transform = `
            translate(${this.currentX}px, ${this.currentY}px)
            rotate(${rotate}deg)
        `;
        
        // Calculate opacity for indicators
        const opacity = Math.abs(this.currentX) / this.threshold;
        
        // Show/hide swipe indicators
        if (this.currentX > 20) {
            this.showIndicator('right', Math.min(opacity, 1));
        } else if (this.currentX < -20) {
            this.showIndicator('left', Math.min(opacity, 1));
        } else {
            this.hideIndicators();
        }
        
        if (this.callbacks.onMove) {
            this.callbacks.onMove(this.currentX, this.currentY);
        }
    }
    
    handleEnd(e) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.element.classList.remove('swiping');
        
        const distance = Math.abs(this.currentX);
        
        if (distance > this.threshold) {
            // Swipe detected
            const direction = this.currentX > 0 ? 'right' : 'left';
            this.completeSwipe(direction);
        } else {
            // Return to center
            this.resetPosition();
        }
        
        this.hideIndicators();
    }
    
    completeSwipe(direction) {
        const targetX = direction === 'right' 
            ? window.innerWidth * 1.5 
            : -window.innerWidth * 1.5;
        
        const rotate = direction === 'right' ? this.rotation * 2 : -this.rotation * 2;
        
        this.element.classList.add('animating-out');
        this.element.style.transform = `
            translate(${targetX}px, ${this.currentY}px)
            rotate(${rotate}deg)
        `;
        
        // Vibrate
        if (window.AnimationSystem) {
            window.AnimationSystem.vibrate([10]);
        }
        
        setTimeout(() => {
            if (this.callbacks.onSwipe) {
                this.callbacks.onSwipe(direction);
            }
        }, 300);
    }
    
    resetPosition() {
        this.element.style.transform = '';
        this.currentX = 0;
        this.currentY = 0;
    }
    
    showIndicator(direction, opacity) {
        const indicator = this.element.querySelector(`.swipe-indicator.${direction}`);
        if (indicator) {
            indicator.style.opacity = opacity;
            indicator.classList.add('visible');
        }
    }
    
    hideIndicators() {
        const indicators = this.element.querySelectorAll('.swipe-indicator');
        indicators.forEach(ind => {
            ind.style.opacity = '0';
            ind.classList.remove('visible');
        });
    }
    
    // Programmatic swipe
    swipe(direction) {
        const targetX = direction === 'right' 
            ? window.innerWidth * 1.5 
            : -window.innerWidth * 1.5;
        
        const rotate = direction === 'right' ? this.rotation * 2 : -this.rotation * 2;
        
        this.element.classList.add('animating-out');
        this.element.style.transform = `
            translate(${targetX}px, 0)
            rotate(${rotate}deg)
        `;
        
        setTimeout(() => {
            if (this.callbacks.onSwipe) {
                this.callbacks.onSwipe(direction);
            }
        }, 400);
    }
    
    destroy() {
        // Clean up event listeners
        this.element.removeEventListener('touchstart', this.handleStart);
        this.element.removeEventListener('touchmove', this.handleMove);
        this.element.removeEventListener('touchend', this.handleEnd);
        this.element.removeEventListener('mousedown', this.handleStart);
        this.element.removeEventListener('mousemove', this.handleMove);
        this.element.removeEventListener('mouseup', this.handleEnd);
        this.element.removeEventListener('mouseleave', this.handleEnd);
    }
}

// Export for use in other files
window.SwipeHandler = SwipeHandler;
