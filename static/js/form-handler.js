// Virtual Islamic University - Form Handler
// This script handles both Contact Form (index.html) and Admission Form (admission.html)

const API_BASE_URL = 'http://localhost:5000/api';

// Utility functions
function showLoading(element) {
    if (element) {
        element.style.display = 'block';
        element.textContent = 'لوڈ ہو رہا ہے...';
    }
}

function hideLoading(element) {
    if (element) {
        element.style.display = 'none';
    }
}

function showError(element, message) {
    if (element) {
        element.style.display = 'block';
        element.textContent = message;
    }
}

function showSuccess(element, message) {
    if (element) {
        element.style.display = 'block';
        element.style.color = '#28a745';
        element.innerHTML = message;
    }
}

// Error popup function for consistent error handling
function createAndShowErrorPopup(message) {
    // Remove any existing popup
    const existingPopup = document.querySelector('.error-popup, .success-popup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Create error popup element
    const popup = document.createElement('div');
    popup.className = 'error-popup';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-icon">⚠</div>
            <div class="popup-message">${message}</div>
            <button class="popup-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add error popup styles if not already present
    if (!document.querySelector('#error-popup-styles')) {
        const style = document.createElement('style');
        style.id = 'error-popup-styles';
        style.textContent = `
            .error-popup {
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 10000;
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(220, 53, 69, 0.3);
                animation: slideInUp 0.5s ease-out;
                max-width: 400px;
                min-width: 300px;
            }
            
            .error-popup .popup-content {
                display: flex;
                align-items: center;
                gap: 15px;
                position: relative;
            }
            
            .error-popup .popup-icon {
                font-size: 2rem;
                font-weight: bold;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.2);
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: shake 0.6s ease-in-out;
            }
            
            .error-popup .popup-message {
                flex: 1;
                font-size: 1.1rem;
                font-weight: 500;
                line-height: 1.4;
                font-family: 'Jameel Noori Nastaleeq', 'Noto Nastaliq Urdu', serif;
            }
            
            .error-popup .popup-close {
                position: absolute;
                top: -5px;
                right: -5px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                font-size: 1.2rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .error-popup .popup-close:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }
            
            @media (max-width: 768px) {
                .error-popup {
                    bottom: 20px;
                    right: 20px;
                    left: 20px;
                    min-width: auto;
                }
                
                .error-popup .popup-content {
                    gap: 12px;
                }
                
                .error-popup .popup-icon {
                    font-size: 1.5rem;
                    width: 35px;
                    height: 35px;
                }
                
                .error-popup .popup-message {
                    font-size: 1rem;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add popup to body
    document.body.appendChild(popup);
    
    // Auto close after 8 seconds
    setTimeout(() => {
        if (popup.parentElement) {
            popup.style.animation = 'slideInUp 0.3s ease-out reverse';
            setTimeout(() => {
                popup.remove();
            }, 300);
        }
    }, 8000);
}

// Fallback popup function if showSuccessPopup is not available
function createAndShowSuccessPopup(message) {
    // Remove any existing popup
    const existingPopup = document.querySelector('.success-popup, .error-popup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Create popup element
    const popup = document.createElement('div');
    popup.className = 'success-popup';
    popup.innerHTML = `
        <div class="popup-content">
            <div class="popup-icon">✓</div>
            <div class="popup-message">${message}</div>
            <button class="popup-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add styles if not already present
    if (!document.querySelector('#popup-styles')) {
        const style = document.createElement('style');
        style.id = 'popup-styles';
        style.textContent = `
            .success-popup {
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 10000;
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(40, 167, 69, 0.3);
                animation: slideInUp 0.5s ease-out;
                max-width: 400px;
                min-width: 300px;
            }
            
            .popup-content {
                display: flex;
                align-items: center;
                gap: 15px;
                position: relative;
            }
            
            .popup-icon {
                font-size: 2rem;
                font-weight: bold;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.2);
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: checkmark 0.6s ease-in-out;
            }
            
            .popup-message {
                flex: 1;
                font-size: 1.1rem;
                font-weight: 500;
                line-height: 1.4;
                font-family: 'Jameel Noori Nastaleeq', 'Noto Nastaliq Urdu', serif;
            }
            
            .popup-close {
                position: absolute;
                top: -5px;
                right: -5px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                font-size: 1.2rem;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .popup-close:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }
            
            @keyframes slideInUp {
                from {
                    transform: translateY(100px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            @keyframes checkmark {
                0% {
                    transform: scale(0) rotate(45deg);
                    opacity: 0;
                }
                50% {
                    transform: scale(1.2) rotate(45deg);
                    opacity: 0.8;
                }
                100% {
                    transform: scale(1) rotate(0deg);
                    opacity: 1;
                }
            }
            
            @media (max-width: 768px) {
                .success-popup {
                    bottom: 20px;
                    right: 20px;
                    left: 20px;
                    min-width: auto;
                }
                
                .popup-content {
                    gap: 12px;
                }
                
                .popup-icon {
                    font-size: 1.5rem;
                    width: 35px;
                    height: 35px;
                }
                
                .popup-message {
                    font-size: 1rem;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Add popup to body
    document.body.appendChild(popup);
    
    // Auto close after 8 seconds
    setTimeout(() => {
        if (popup.parentElement) {
            popup.style.animation = 'slideInUp 0.3s ease-out reverse';
            setTimeout(() => {
                popup.remove();
            }, 300);
        }
    }, 8000);
}

// Contact Form Handler (index.html)
function handleContactForm() {
    const contactForm = document.getElementById('contactForm') || document.querySelector('.contact-form');
    if (!contactForm) {
        console.error('Contact form not found!');
        return;
    }
    console.log('Contact form found:', contactForm);

    contactForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const loading = this.querySelector('.loading');
        const errorMessage = this.querySelector('.error-message');
        const sentMessage = this.querySelector('.sent-message');
        
        // Show loading
        showLoading(loading);
        hideLoading(errorMessage);
        hideLoading(sentMessage);
        
        // Get form data
        const formData = {
            name: this.querySelector('[name="name"]').value.trim(),
            email: this.querySelector('[name="email"]').value.trim(),
            subject: this.querySelector('[name="subject"]').value.trim(),
            message: this.querySelector('[name="message"]').value.trim()
        };
        
        try {
            // Use real Flask API
            const response = await fetch(`${API_BASE_URL}/submit-contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            hideLoading(loading);
            
            if (result.success) {
                showSuccess(sentMessage, result.message);
                contactForm.reset();
                // Clear form validation styles
                const inputs = contactForm.querySelectorAll('input, textarea');
                inputs.forEach(input => {
                    input.style.borderColor = '';
                    hideValidationMessage(input);
                });
            } else {
                showError(errorMessage, result.error || 'خرابی ہوئی، براہ کرم دوبارہ کوشش کریں');
            }
            
        } catch (error) {
            hideLoading(loading);
            showError(errorMessage, 'نیٹ ورک کی خرابی، براہ کرم اپنا انٹرنیٹ کنکشن چیک کریں');
            console.error('Contact form error:', error);
        }
    });
}

// Admission Form Handler (admission.html)
function handleAdmissionForm() {
    const admissionForm = document.getElementById('admissionForm');
    if (!admissionForm) return;

    // Add validation helpers
    addFormValidation();
    
    admissionForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get all form data
        const formData = new FormData(this);
        const data = {};
        
        // Convert FormData to object
        for (let [key, value] of formData.entries()) {
            data[key] = value.trim();
        }
        
        // Frontend validation
        const validationError = validateAdmissionForm(data);
        if (validationError) {
            alert(validationError);
            return;
        }
        
        // Check terms acceptance
        if (!data.terms) {
            alert('براہ کرم شرائط و ضوابط سے اتفاق کریں۔');
            return;
        }
        
        // Show loading state
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'جمع کیا جا رہا ہے...';
        
        try {
            const response = await fetch(`${API_BASE_URL}/submit-admission`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message with application number using popup
                const successMessage = `آپ کی درخواست کامیابی سے جمع ہو گئی!\n\nApplication Number: ${result.application_number}\n\nہم جلد ہی آپ سے رابطہ کریں گے۔\nاپنا Application Number محفوظ رکھیں۔\n\nشکریہ!`;
                createAndShowSuccessPopup(successMessage);
                admissionForm.reset();
                // Clear form validation styles
                const inputs = admissionForm.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    input.style.borderColor = '';
                    hideValidationMessage(input);
                });
            } else {
                createAndShowErrorPopup(result.error || 'درخواست جمع کرنے میں خرابی ہوئی، براہ کرم دوبارہ کوشش کریں');
            }
            
        } catch (error) {
            createAndShowErrorPopup('نیٹ ورک کی خرابی، براہ کرم اپنا انٹرنیٹ کنکشن چیک کریں');
            console.error('Admission form error:', error);
        } finally {
            // Reset button state
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });
}

// Form validation for admission form
function validateAdmissionForm(data) {
    // Check required fields
    const requiredFields = {
        'firstName': 'پہلا نام',
        'lastName': 'آخری نام',
        'fatherName': 'والد کا نام',
        'cnic': 'شناختی کارڈ نمبر',
        'email': 'ای میل',
        'phone': 'فون نمبر',
        'dateOfBirth': 'تاریخ پیدائش',
        'gender': 'جنس',
        'address': 'پتہ',
        'education': 'تعلیمی قابلیت',
        'course': 'کورس'
    };
    
    for (let [field, label] of Object.entries(requiredFields)) {
        if (!data[field] || data[field].trim() === '') {
            return `براہ کرم ${label} درج کریں`;
        }
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        return 'براہ کرم صحیح ای میل ایڈریس درج کریں';
    }
    
    // CNIC validation
    const cnicRegex = /^\d{5}-\d{7}-\d{1}$/;
    if (!cnicRegex.test(data.cnic)) {
        return 'براہ کرم CNIC صحیح فارمیٹ میں درج کریں (12345-1234567-1)';
    }
    
    // Phone validation
    const phoneRegex = /^\+92-3\d{2}-\d{7}$/;
    if (!phoneRegex.test(data.phone)) {
        return 'براہ کرم فون نمبر صحیح فارمیٹ میں درج کریں (+92-300-1234567)';
    }
    
    // Age validation (minimum 16 years)
    const birthDate = new Date(data.dateOfBirth);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    if (age < 16) {
        return 'داخلے کے لیے کم از کم 16 سال کی عمر ضروری ہے';
    }
    
    return null; // No validation errors
}

// Add form validation helpers
function addFormValidation() {
    // CNIC formatting
    const cnicInput = document.getElementById('cnic');
    if (cnicInput) {
        cnicInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 5) {
                value = value.slice(0, 5) + '-' + value.slice(5);
            }
            if (value.length >= 13) {
                value = value.slice(0, 13) + '-' + value.slice(13);
            }
            if (value.length > 15) {
                value = value.slice(0, 15);
            }
            e.target.value = value;
        });
    }
    
    // Phone formatting
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.startsWith('92')) {
                value = '+' + value;
            } else if (value.startsWith('0')) {
                value = '+92' + value.slice(1);
            } else if (!value.startsWith('+92')) {
                value = '+92' + value;
            }
            
            // Format: +92-3XX-XXXXXXX
            if (value.length > 3) {
                value = value.slice(0, 3) + '-' + value.slice(3);
            }
            if (value.length > 7) {
                value = value.slice(0, 7) + '-' + value.slice(7);
            }
            if (value.length > 15) {
                value = value.slice(0, 15);
            }
            
            e.target.value = value;
        });
    }
    
    // Real-time validation feedback
    addRealTimeValidation();
}

// Add real-time validation feedback
function addRealTimeValidation() {
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (email && !emailRegex.test(email)) {
                this.style.borderColor = '#dc3545';
                showValidationMessage(this, 'صحیح ای میل ایڈریس درج کریں');
            } else {
                this.style.borderColor = '#28a745';
                hideValidationMessage(this);
            }
        });
    }
    
    const cnicInput = document.getElementById('cnic');
    if (cnicInput) {
        cnicInput.addEventListener('blur', function() {
            const cnic = this.value.trim();
            const cnicRegex = /^\d{5}-\d{7}-\d{1}$/;
            if (cnic && !cnicRegex.test(cnic)) {
                this.style.borderColor = '#dc3545';
                showValidationMessage(this, 'CNIC فارمیٹ: 12345-1234567-1');
            } else {
                this.style.borderColor = '#28a745';
                hideValidationMessage(this);
            }
        });
    }
}

function showValidationMessage(input, message) {
    hideValidationMessage(input); // Remove existing message
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function hideValidationMessage(input) {
    const existingError = input.parentNode.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        handleContactForm();
        handleAdmissionForm();
        
        console.log('Virtual Islamic University Form Handler Initialized');
        console.log('API Base URL:', API_BASE_URL);
    });
} else {
    handleContactForm();
    handleAdmissionForm();
    
    console.log('Virtual Islamic University Form Handler Initialized');
    console.log('API Base URL:', API_BASE_URL);
}
