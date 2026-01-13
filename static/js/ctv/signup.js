/**
 * CTV Signup Page JavaScript
 * Handles form submission and validation
 */

// Simple translations
const translations = {
    vi: {
        signup_title: 'Đăng Ký CTV',
        signup_subtitle: 'Điền thông tin để đăng ký làm Cộng Tác Viên',
        last_name: 'Họ *',
        last_name_placeholder: 'Nhập họ',
        first_name: 'Tên *',
        first_name_placeholder: 'Nhập tên',
        phone_number: 'Số điện thoại *',
        phone_placeholder: 'Nhập số điện thoại',
        email: 'Email',
        email_placeholder: 'Nhập email (không bắt buộc)',
        address: 'Địa chỉ',
        address_placeholder: 'Nhập địa chỉ',
        dob: 'Ngày sinh',
        id_number: 'Số CCCD/CMND',
        id_placeholder: 'Nhập số CCCD/CMND',
        referrer_code: 'Mã CTV người giới thiệu',
        referrer_placeholder: 'Nhập mã CTV người giới thiệu (nếu có)',
        referrer_phone: '☎️ CTV Người giới thiệu (nếu có)',
        referrer_phone_placeholder: 'Nhập số điện thoại CTV người giới thiệu (nếu có)',
        checking: 'Đang kiểm tra...',
        referrer_found: 'Người giới thiệu',
        referrer_not_found: 'Không tìm thấy CTV với số này',
        password: 'Mật khẩu *',
        password_placeholder: 'Nhập mật khẩu',
        confirm_password: 'Xác nhận mật khẩu *',
        confirm_password_placeholder: 'Nhập lại mật khẩu',
        agree_terms: 'Tôi đồng ý với',
        terms_link: 'Điều khoản và Điều kiện',
        terms_title: 'Điều Khoản và Điều Kiện',
        signature_agreement: 'Bằng cách ký tên bên dưới, tôi xác nhận đã đọc, hiểu và đồng ý với tất cả các điều khoản và điều kiện trên.',
        signature_label: 'Chữ ký điện tử *',
        signature_placeholder: 'Vẽ chữ ký của bạn ở đây',
        clear_signature: 'Xóa chữ ký',
        signature_date: 'Ngày:',
        accept_sign: 'Chấp nhận và Ký',
        cancel: 'Hủy',
        signup_button: 'Đăng Ký',
        have_account: 'Đã có tài khoản? Đăng nhập',
        password_mismatch: 'Mật khẩu không khớp',
        password_too_short: 'Mật khẩu phải có ít nhất 6 ký tự',
        invalid_phone: 'Số điện thoại không hợp lệ',
        signup_success: 'Đăng ký thành công! Tài khoản của bạn đang chờ phê duyệt. Chúng tôi sẽ liên hệ với bạn sớm.',
        signup_error: 'Đăng ký thất bại. Vui lòng thử lại.',
        phone_exists: 'Số điện thoại này đã được đăng ký',
        submitting: 'Đang gửi...',
        terms_required: 'Vui lòng đồng ý với điều khoản và điều kiện',
        signature_required: 'Vui lòng nhập chữ ký của bạn'
    },
    en: {
        signup_title: 'CTV Sign Up',
        signup_subtitle: 'Fill in the information to register as a Collaborator',
        last_name: 'Last Name *',
        last_name_placeholder: 'Enter your last name',
        first_name: 'First Name *',
        first_name_placeholder: 'Enter your first name',
        phone_number: 'Phone Number *',
        phone_placeholder: 'Enter phone number',
        email: 'Email',
        email_placeholder: 'Enter email (optional)',
        address: 'Address',
        address_placeholder: 'Enter address',
        dob: 'Date of Birth',
        id_number: 'ID Number',
        id_placeholder: 'Enter ID number',
        referrer_code: 'Referrer Code',
        referrer_placeholder: 'Enter referrer CTV code (if any)',
        referrer_phone: '☎️ Referrer CTV (optional)',
        referrer_phone_placeholder: 'Enter referrer CTV phone number (if any)',
        checking: 'Checking...',
        referrer_found: 'Referrer',
        referrer_not_found: 'CTV not found with this phone',
        password: 'Password *',
        password_placeholder: 'Enter password',
        confirm_password: 'Confirm Password *',
        confirm_password_placeholder: 'Re-enter password',
        agree_terms: 'I agree to the',
        terms_link: 'Terms and Conditions',
        terms_title: 'Terms and Conditions',
        signature_agreement: 'By signing below, I confirm that I have read, understood, and agree to all the terms and conditions above.',
        signature_label: 'Digital Signature *',
        signature_placeholder: 'Draw your signature here',
        clear_signature: 'Clear Signature',
        signature_date: 'Date:',
        accept_sign: 'Accept and Sign',
        cancel: 'Cancel',
        signup_button: 'Sign Up',
        have_account: 'Already have an account? Login',
        password_mismatch: 'Passwords do not match',
        password_too_short: 'Password must be at least 6 characters',
        invalid_phone: 'Invalid phone number',
        signup_success: 'Sign up successful! Your account is pending approval. We will contact you soon.',
        signup_error: 'Sign up failed. Please try again.',
        phone_exists: 'This phone number is already registered',
        submitting: 'Submitting...',
        terms_required: 'Please agree to the terms and conditions',
        signature_required: 'Please enter your signature'
    }
};

let currentLang = localStorage.getItem('ctv_language') || 'vi';

function t(key) {
    return translations[currentLang][key] || translations['vi'][key] || key;
}

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('ctv_language', lang);
    
    // Update language label
    document.getElementById('loginLangLabel').textContent = lang.toUpperCase();
    
    // Update all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });
    
    // Update active language option
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.lang === lang);
    });
}

function toggleLangPopup() {
    const toggle = document.getElementById('loginLangToggle');
    toggle.classList.toggle('active');
}

// Close language popup when clicking outside
document.addEventListener('click', (e) => {
    const toggle = document.getElementById('loginLangToggle');
    if (toggle && !toggle.contains(e.target)) {
        toggle.classList.remove('active');
    }
});

// Debounce function for real-time validation
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Real-time referrer phone validation
async function checkReferrerPhone(phone) {
    const referrerInput = document.getElementById('referrerCode');
    const formGroup = referrerInput.closest('.form-group');
    
    // Remove any existing validation message
    let validationMsg = formGroup.querySelector('.validation-msg');
    if (validationMsg) {
        validationMsg.remove();
    }
    
    // Clear any existing state classes
    referrerInput.classList.remove('input-valid', 'input-invalid', 'input-checking');
    
    if (!phone || phone.trim() === '') {
        return;
    }
    
    // Clean phone number
    const phoneDigits = phone.replace(/\D/g, '');
    
    if (phoneDigits.length < 8) {
        return; // Too short, don't validate yet
    }
    
    // Show checking state
    referrerInput.classList.add('input-checking');
    validationMsg = document.createElement('div');
    validationMsg.className = 'validation-msg checking';
    validationMsg.textContent = t('checking') || 'Checking...';
    formGroup.appendChild(validationMsg);
    
    try {
        const response = await fetch('/api/ctv/check-referrer-phone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone: phone
            })
        });
        
        const data = await response.json();
        
        // Remove checking state
        referrerInput.classList.remove('input-checking');
        if (validationMsg) {
            validationMsg.remove();
        }
        
        if (data.status === 'success') {
            if (data.exists) {
                // Valid referrer phone
                referrerInput.classList.add('input-valid');
                validationMsg = document.createElement('div');
                validationMsg.className = 'validation-msg valid';
                validationMsg.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg> ${t('referrer_found') || 'Referrer found'}: ${data.name} (${data.ma_ctv})`;
                formGroup.appendChild(validationMsg);
            } else {
                // Invalid referrer phone
                referrerInput.classList.add('input-invalid');
                validationMsg = document.createElement('div');
                validationMsg.className = 'validation-msg invalid';
                validationMsg.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> ${t('referrer_not_found') || 'CTV not found with this phone'}`;
                formGroup.appendChild(validationMsg);
            }
        }
    } catch (error) {
        console.error('Error checking referrer phone:', error);
        referrerInput.classList.remove('input-checking');
        if (validationMsg) {
            validationMsg.remove();
        }
    }
}

// Create debounced version
const debouncedCheckReferrer = debounce(checkReferrerPhone, 500);

// Terms and Conditions Modal
let termsAccepted = false;
let signatureData = null;

// Signature Pad Setup
let canvas, ctx, isDrawing = false;
let lastX = 0, lastY = 0;

function initSignaturePad() {
    canvas = document.getElementById('signatureCanvas');
    if (!canvas) {
        console.error('Signature canvas not found');
        return;
    }
    
    ctx = canvas.getContext('2d');
    
    // Set canvas size to match display size
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr; // Use device pixel ratio
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    // Set drawing styles
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Mouse events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Touch events (important for mobile)
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', stopDrawing);
    canvas.addEventListener('touchcancel', stopDrawing);
}

function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };
}

function getTouchPos(e) {
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    return {
        x: touch.clientX - rect.left,
        y: touch.clientY - rect.top
    };
}

function startDrawing(e) {
    isDrawing = true;
    const pos = getMousePos(e);
    lastX = pos.x;
    lastY = pos.y;
    hidePlaceholder();
}

function handleTouchStart(e) {
    e.preventDefault();
    isDrawing = true;
    const pos = getTouchPos(e);
    lastX = pos.x;
    lastY = pos.y;
    hidePlaceholder();
}

function draw(e) {
    if (!isDrawing) return;
    
    const pos = getMousePos(e);
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    
    lastX = pos.x;
    lastY = pos.y;
}

function handleTouchMove(e) {
    e.preventDefault();
    if (!isDrawing) return;
    
    const pos = getTouchPos(e);
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    
    lastX = pos.x;
    lastY = pos.y;
}

function stopDrawing() {
    isDrawing = false;
}

function clearSignature() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    showPlaceholder();
    signatureData = null;
}

function hidePlaceholder() {
    const placeholder = document.getElementById('signaturePlaceholder');
    if (placeholder) {
        placeholder.classList.add('hidden');
    }
}

function showPlaceholder() {
    const placeholder = document.getElementById('signaturePlaceholder');
    if (placeholder) {
        placeholder.classList.remove('hidden');
    }
}

function isCanvasBlank() {
    const pixelBuffer = new Uint32Array(
        ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
    );
    return !pixelBuffer.some(color => color !== 0);
}

// Make functions global for HTML onclick access
window.openTermsModal = function(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('Global openTermsModal called');

    const modal = document.getElementById('termsModal');
    const dateElement = document.getElementById('currentDate');
    
    if (!modal) {
        console.error('Terms modal not found');
        alert('Lỗi: Không tìm thấy khung điều khoản. Vui lòng tải lại trang.');
        return;
    }
    
    // Set current date
    const today = new Date();
    const dateString = today.toLocaleDateString(currentLang === 'vi' ? 'vi-VN' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    if (dateElement) {
        dateElement.textContent = dateString;
    }
    
    // FORCE SHOW MODAL - Direct Style Manipulation
    modal.classList.add('show');
    modal.style.cssText = 'display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999999 !important;';
    
    // Fix body
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.width = '100%';
    document.body.style.top = '0';
    
    // Initialize canvas with delay
    setTimeout(() => {
        initSignaturePad();
        // Force redraw of canvas
        if (canvas) {
            canvas.width = canvas.width; 
            initSignaturePad(); 
        }
    }, 200);
    
    return false;
};

// Also attach to the old name just in case
function openTermsModal() {
    return window.openTermsModal();
}

window.closeTermsModal = function() {
    const modal = document.getElementById('termsModal');
    if (!modal) return;
    
    modal.classList.remove('show');
    modal.style.display = 'none'; // Explicitly hide
    modal.style.cssText = ''; // Clear inline styles
    
    // Reset body styles for mobile
    document.body.style.overflow = '';
    document.body.style.position = '';
    document.body.style.width = '';
    document.body.style.top = '';
    
    // Clear signature if terms not accepted
    if (!termsAccepted && typeof clearSignature === 'function') {
        clearSignature();
    }
};

window.acceptTerms = function() {
    // Check if signature is drawn
    if (isCanvasBlank()) {
        alert(t('signature_required'));
        return;
    }
    
    // Save signature as data URL
    signatureData = canvas.toDataURL('image/png');
    
    // Mark terms as accepted
    termsAccepted = true;
    
    // Check the checkbox
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (termsCheckbox) {
        termsCheckbox.checked = true;
        
        // Trigger change event manually so the listener fires
        const event = new Event('change');
        termsCheckbox.dispatchEvent(event);
        
        // Also manually enable button just in case listener fails
        const signupBtn = document.getElementById('signupBtn');
        if (signupBtn) {
            signupBtn.disabled = false;
            signupBtn.style.opacity = '1';
            signupBtn.style.cursor = 'pointer';
        }
    }
    
    // Close modal
    window.closeTermsModal();
};

// Signup form submission
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorMsg = document.getElementById('signupError');
    const successMsg = document.getElementById('signupSuccess');
    const submitBtn = document.getElementById('signupBtn');
    
    // Hide messages
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    
    // Get form values
    const lastName = document.getElementById('lastName').value.trim();
    const firstName = document.getElementById('firstName').value.trim();
    const fullName = `${lastName} ${firstName}`.trim();
    const phoneNumber = document.getElementById('phoneNumber').value.trim();
    const email = document.getElementById('email').value.trim();
    const address = document.getElementById('address').value.trim();
    const dob = document.getElementById('dob').value;
    const idNumber = document.getElementById('idNumber').value.trim();
    const referrerCode = document.getElementById('referrerCode').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // Validation
    if (!lastName || !firstName || !phoneNumber || !password || !confirmPassword) {
        errorMsg.textContent = t('signup_error');
        errorMsg.style.display = 'block';
        return;
    }
    
    if (password.length < 6) {
        errorMsg.textContent = t('password_too_short');
        errorMsg.style.display = 'block';
        return;
    }
    
    if (password !== confirmPassword) {
        errorMsg.textContent = t('password_mismatch');
        errorMsg.style.display = 'block';
        return;
    }
    
    // Phone validation (basic)
    const phoneDigits = phoneNumber.replace(/\D/g, '');
    if (phoneDigits.length < 9 || phoneDigits.length > 11) {
        errorMsg.textContent = t('invalid_phone');
        errorMsg.style.display = 'block';
        return;
    }
    
    // Check if terms are accepted
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (!termsCheckbox.checked || !termsAccepted) {
        errorMsg.textContent = t('terms_required');
        errorMsg.style.display = 'block';
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = t('submitting');
    
    try {
        const response = await fetch('/api/ctv/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                phone: phoneNumber,
                email: email || null,
                address: address || null,
                dob: dob || null,
                id_number: idNumber || null,
                referrer_code: referrerCode || null,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Show success message
            successMsg.textContent = t('signup_success');
            successMsg.style.display = 'block';
            
            // Clear form
            document.getElementById('signupForm').reset();
            
            // Redirect to login after 3 seconds
            setTimeout(() => {
                window.location.href = '/ctv/portal';
            }, 3000);
        } else {
            // Show error message
            if (data.message && data.message.includes('phone')) {
                errorMsg.textContent = t('phone_exists');
            } else {
                errorMsg.textContent = data.message || t('signup_error');
            }
            errorMsg.style.display = 'block';
        }
    } catch (error) {
        console.error('Signup error:', error);
        errorMsg.textContent = t('signup_error');
        errorMsg.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = t('signup_button');
    }
});

// Initialize language
document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
    
    // Disable signup button initially
    const signupBtn = document.getElementById('signupBtn');
    const termsCheckbox = document.getElementById('termsCheckbox');
    
    if (signupBtn && termsCheckbox) {
        signupBtn.disabled = true;
        signupBtn.style.opacity = '0.5';
        signupBtn.style.cursor = 'not-allowed';
        
        // Enable/disable signup button based on checkbox
        termsCheckbox.addEventListener('change', (e) => {
            if (e.target.checked && termsAccepted) {
                signupBtn.disabled = false;
                signupBtn.style.opacity = '1';
                signupBtn.style.cursor = 'pointer';
            } else {
                signupBtn.disabled = true;
                signupBtn.style.opacity = '0.5';
                signupBtn.style.cursor = 'not-allowed';
                
                // If unchecked, reset terms acceptance
                if (!e.target.checked) {
                    termsAccepted = false;
                    signatureData = null;
                }
            }
        });
    }
    
    // Attach real-time validation to referrer code input
    const referrerInput = document.getElementById('referrerCode');
    if (referrerInput) {
        referrerInput.addEventListener('input', (e) => {
            debouncedCheckReferrer(e.target.value);
        });
    }
    
    // Terms modal event listeners
    const viewTermsLink = document.getElementById('viewTermsLink');
    const closeTermsModal_btn = document.getElementById('closeTermsModal');
    const cancelTermsBtn = document.getElementById('cancelTermsBtn');
    const acceptTermsBtn = document.getElementById('acceptTermsBtn');
    const clearSignatureBtn = document.getElementById('clearSignatureBtn');
    const termsModal = document.getElementById('termsModal');
    
    // Note: viewTermsLink now uses inline onclick="openTermsModal(event)"
    
    if (closeTermsModal_btn) {
        closeTermsModal_btn.addEventListener('click', window.closeTermsModal);
    }
    
    if (cancelTermsBtn) {
        cancelTermsBtn.addEventListener('click', window.closeTermsModal);
    }
    
    if (acceptTermsBtn) {
        acceptTermsBtn.addEventListener('click', window.acceptTerms);
    }
    
    if (clearSignatureBtn) {
        clearSignatureBtn.addEventListener('click', clearSignature);
    }
    
    // Close modal when clicking outside
    if (termsModal) {
        termsModal.addEventListener('click', (e) => {
            if (e.target === termsModal) {
                window.closeTermsModal();
            }
        });
    }
});
