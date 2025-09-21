/**
 * Form Handler for Virtual Islamic University
 * Handles contact form and admission form submissions
 */

// API Configuration - Smart URL detection
function getApiBaseUrl() {
    // If we're accessing through Flask server (port 8000), use relative URLs
    if (window.location.port === '8000') {
        return '/api';
    }
    // If we're on VS Code Live Server or other ports, use absolute URL to Flask server
    return 'http://127.0.0.1:8000/api';
}

const API_BASE_URL = getApiBaseUrl();
console.log('API Base URL:', API_BASE_URL);
console.log('Current page URL:', window.location.href);
console.log('Current port:', window.location.port);

// Initialize form handlers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeContactForm();
    initializeAdmissionForm();
});

/**
 * Initialize Contact Form Handler
 */
function initializeContactForm() {
    console.log('Initializing contact form handler...');
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        console.log('Contact form found, adding event listener');
        contactForm.addEventListener('submit', handleContactFormSubmission);
    } else {
        console.error('Contact form not found! Make sure there is an element with id="contactForm"');
    }
}

/**
 * Initialize Admission Form Handler (if exists)
 */
function initializeAdmissionForm() {
    const admissionForm = document.getElementById('admissionForm');
    if (admissionForm) {
        admissionForm.addEventListener('submit', handleAdmissionFormSubmission);
    }
}

/**
 * Handle Contact Form Submission
 */
async function handleContactFormSubmission(event) {
    console.log('Contact form submission started');
    event.preventDefault(); // Prevent default form submission
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    console.log('Submit button found:', submitButton);
    
    // Get form data
    const formData = new FormData(form);
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        subject: formData.get('subject'),
        message: formData.get('message')
    };
    console.log('Form data collected:', data);
    
    // Validate form data
    if (!validateContactForm(data)) {
        return;
    }
    
    // Disable submit button and show loading state
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> بھیجا جا رہا ہے...';
    submitButton.disabled = true;
    
    try {
        console.log('Sending request to:', `${API_BASE_URL}/submit-contact`);
        console.log('Sending data:', data);
        
        // Send data to backend
        const response = await fetch(`${API_BASE_URL}/submit-contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', [...response.headers.entries()]);
        
        const result = await response.json();
        console.log('Response data:', result);
        
        if (result.success) {
            // Show success message
            showSuccessPopup(result.message || 'آپ کا پیغام کامیابی سے بھیج دیا گیا');
            console.log('Form submitted successfully! Submission ID:', result.submission_id);
            
            // Reset form
            form.reset();
            
            // Focus first input
            const firstInput = form.querySelector('input[name="name"]');
            if (firstInput) {
                firstInput.focus();
            }
        } else {
            // Show error message
            console.error('Server returned error:', result.error);
            showErrorPopup(result.error || 'پیغام بھیجنے میں خرابی ہوئی');
        }
        
    } catch (error) {
        console.error('Contact form submission error:', error);
        let errorMessage = 'سرور سے رابطے میں خرابی، براہ کرم دوبارہ کوشش کریں';
        
        // More specific error messages
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = 'نیٹ ورک کنکشن کی خرابی۔ براہ کرم یقینی بنائیں کہ آپ http://localhost:8000/ استعمال کر رہے ہیں، فائل کو براہ راست نہ کھولیں۔';
        } else if (error.message.includes('CORS')) {
            errorMessage = 'CORS کی خرابی۔ براہ کرم Flask سرور دوبارہ شروع کریں۔';
        }
        
        showErrorPopup(errorMessage);
    } finally {
        // Restore submit button
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
    }
}

/**
 * Handle Admission Form Submission
 */
async function handleAdmissionFormSubmission(event) {
    event.preventDefault(); // Prevent default form submission
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Get form data
    const formData = new FormData(form);
    const data = {
        firstName: formData.get('firstName'),
        lastName: formData.get('lastName'),
        fatherName: formData.get('fatherName'),
        cnic: formData.get('cnic'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        dateOfBirth: formData.get('dateOfBirth'),
        gender: formData.get('gender'),
        address: formData.get('address'),
        education: formData.get('education'),
        course: formData.get('course')
    };
    
    // Validate form data
    if (!validateAdmissionForm(data)) {
        return;
    }
    
    // Disable submit button and show loading state
    const originalButtonText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> درخواست بھیجی جا رہی ہے...';
    submitButton.disabled = true;
    
    try {
        // Send data to backend
        const response = await fetch(`${API_BASE_URL}/submit-admission`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message with application number
            showSuccessPopup(`${result.message}<br><strong>Application Number: ${result.application_number}</strong>`);
            
            // Reset form
            form.reset();
            
            // Focus first input
            const firstInput = form.querySelector('input[name="firstName"]');
            if (firstInput) {
                firstInput.focus();
            }
        } else {
            // Show error message
            showErrorPopup(result.error || 'درخواست بھیجنے میں خرابی ہوئی');
        }
        
    } catch (error) {
        console.error('Admission form submission error:', error);
        showErrorPopup('سرور سے رابطے میں خرابی، براہ کرم دوبارہ کوشش کریں');
    } finally {
        // Restore submit button
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
    }
}

/**
 * Validate Contact Form Data
 */
function validateContactForm(data) {
    const errors = [];
    
    // Name validation
    if (!data.name || data.name.trim().length < 2) {
        errors.push('براہ کرم اپنا نام درج کریں (کم از کم 2 حروف)');
    }
    
    // Email validation
    if (!data.email || !isValidEmail(data.email)) {
        errors.push('براہ کرم صحیح ای میل ایڈریس درج کریں');
    }
    
    // Subject validation
    if (!data.subject || data.subject.trim().length < 3) {
        errors.push('براہ کرم موضوع درج کریں (کم از کم 3 حروف)');
    }
    
    // Message validation
    if (!data.message || data.message.trim().length < 10) {
        errors.push('براہ کرم پیغام درج کریں (کم از کم 10 حروف)');
    }
    
    // Show errors if any
    if (errors.length > 0) {
        showErrorPopup(errors.join('<br>'));
        return false;
    }
    
    return true;
}

/**
 * Validate Admission Form Data
 */
function validateAdmissionForm(data) {
    const errors = [];
    
    // Required field validation
    const requiredFields = [
        { field: 'firstName', name: 'پہلا نام' },
        { field: 'lastName', name: 'آخری نام' },
        { field: 'fatherName', name: 'والد کا نام' },
        { field: 'cnic', name: 'CNIC' },
        { field: 'email', name: 'ای میل' },
        { field: 'phone', name: 'فون نمبر' },
        { field: 'dateOfBirth', name: 'تاریخ پیدائش' },
        { field: 'gender', name: 'جنس' },
        { field: 'address', name: 'پتہ' },
        { field: 'education', name: 'تعلیمی قابلیت' },
        { field: 'course', name: 'کورس' }
    ];
    
    requiredFields.forEach(({ field, name }) => {
        if (!data[field] || data[field].trim() === '') {
            errors.push(`${name} لازمی ہے`);
        }
    });
    
    // Email validation
    if (data.email && !isValidEmail(data.email)) {
        errors.push('براہ کرم صحیح ای میل ایڈریس درج کریں');
    }
    
    // CNIC validation
    if (data.cnic && !isValidCNIC(data.cnic)) {
        errors.push('براہ کرم CNIC صحیح فارمیٹ میں درج کریں (12345-1234567-1)');
    }
    
    // Phone validation
    if (data.phone && !isValidPhone(data.phone)) {
        errors.push('براہ کرم فون نمبر صحیح فارمیٹ میں درج کریں (+923001234567)');
    }
    
    // Show errors if any
    if (errors.length > 0) {
        showErrorPopup(errors.join('<br>'));
        return false;
    }
    
    return true;
}

/**
 * Email validation helper
 */
function isValidEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
}

/**
 * CNIC validation helper
 */
function isValidCNIC(cnic) {
    const cnicRegex = /^\d{5}-\d{7}-\d{1}$/;
    return cnicRegex.test(cnic);
}

/**
 * Phone validation helper
 */
function isValidPhone(phone) {
    const phoneRegex = /^\+92[0-9]{10}$/;
    return phoneRegex.test(phone);
}

/**
 * Show Error Popup
 */
function showErrorPopup(message) {
    // Create popup element
    const popup = document.createElement('div');
    popup.className = 'error-popup';
    popup.innerHTML = `
        <div class="popup-content error-content">
            <div class="popup-icon">
                <i class="bi bi-exclamation-triangle-fill"></i>
            </div>
            <div class="popup-message">
                ${message}
            </div>
            <button class="popup-close" onclick="closeErrorPopup()">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `;
    
    // Add popup styles for error
    const style = document.createElement('style');
    style.textContent = `
        .error-popup {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 10000;
            opacity: 0;
            transform: translateY(100%) scale(0.8);
            animation: errorSlideUp 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
        }
        
        .error-content {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
            box-shadow: 
                0 20px 40px rgba(220, 53, 69, 0.3),
                0 8px 16px rgba(0, 0, 0, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
        }
        
        @keyframes errorSlideUp {
            0% {
                transform: translateY(100%) scale(0.8);
                opacity: 0;
            }
            60% {
                transform: translateY(-10px) scale(1.02);
                opacity: 0.9;
            }
            100% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
        }
        
        .error-popup.closing {
            animation: errorSlideDown 0.4s cubic-bezier(0.55, 0.055, 0.675, 0.19) forwards;
        }
        
        @keyframes errorSlideDown {
            0% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }
            100% {
                transform: translateY(100%) scale(0.8);
                opacity: 0;
            }
        }
    `;
    
    // Add styles to head
    document.head.appendChild(style);
    
    // Add popup to body
    document.body.appendChild(popup);
    
    // Auto close after 8 seconds
    setTimeout(() => {
        closeErrorPopup();
    }, 8000);
}

/**
 * Close Error Popup
 */
function closeErrorPopup() {
    const popup = document.querySelector('.error-popup');
    if (popup) {
        popup.classList.add('closing');
        setTimeout(() => {
            popup.remove();
        }, 400);
    }
}

// Note: showSuccessPopup function is already defined in index.html
// We'll use that existing function for consistency
