/**
 * CTV Signup Page JavaScript
 * Handles form submission and validation
 */

/**
 * Load signup terms from database
 */
async function loadSignupTerms() {
    // Disabled to use hardcoded terms from template
    // try {
    //     const response = await fetch(`/api/admin/signup-terms/active?language=${currentLang}`);
    //     const result = await response.json();
    //     
    //     if (result.status === 'success' && result.term) {
    //         // Update terms title
    //         const termsTitle = document.querySelector('#termsModal h2[data-i18n="terms_title"]');
    //         if (termsTitle) {
    //             termsTitle.textContent = result.term.title;
    //         }
    //         
    //         // Update terms content
    //         const termsContent = document.querySelector('#termsModal .terms-content');
    //         if (termsContent) {
    //             termsContent.innerHTML = result.term.content;
    //         }
    //     } else {
    //         console.warn('No active terms found, using default terms');
    //     }
    // } catch (error) {
    //     console.error('Failed to load terms:', error);
    //     // Keep default terms if loading fails
    // }
}

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
        referrer_phone: '☎️ Người giới thiệu (nếu có)',
        referrer_phone_placeholder: 'Nhập số điện thoại người giới thiệu (nếu có)',
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
        close: 'Đóng',
        read_terms: 'Xem',
        cancel: 'Hủy',
        signup_button: 'Đăng Ký',
        have_account: 'Đã có tài khoản? Đăng nhập',
        password_mismatch: 'Mật khẩu không khớp',
        password_too_short: 'Mật khẩu phải có ít nhất 6 ký tự',
        invalid_phone: 'Số điện thoại không hợp lệ',
        signup_success: 'Đăng ký thành công! Bạn có thể đăng nhập ngay bằng số điện thoại.',
        signup_error: 'Đăng ký thất bại. Vui lòng thử lại.',
        phone_exists: 'Số điện thoại này đã được đăng ký',
        submitting: 'Đang gửi...',
        terms_required: 'Vui lòng đồng ý với điều khoản và điều kiện',
        signature_required: 'Vui lòng nhập chữ ký của bạn',
        pending_approval: 'Tài khoản của bạn đang chờ phê duyệt. Vui lòng đợi quản trị viên xác nhận.',
        account_already_exists: 'Số điện thoại này đã được đăng ký làm CTV. Vui lòng đăng nhập.'
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
        referrer_phone: '☎️ Referrer (optional)',
        referrer_phone_placeholder: 'Enter referrer phone number (if any)',
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
        close: 'Close',
        read_terms: 'Read',
        cancel: 'Cancel',
        signup_button: 'Sign Up',
        have_account: 'Already have an account? Login',
        password_mismatch: 'Passwords do not match',
        password_too_short: 'Password must be at least 6 characters',
        invalid_phone: 'Invalid phone number',
        signup_success: 'Sign up successful! You can now log in with your phone number.',
        signup_error: 'Sign up failed. Please try again.',
        phone_exists: 'This phone number is already registered',
        submitting: 'Submitting...',
        terms_required: 'Please agree to the terms and conditions',
        signature_required: 'Please enter your signature',
        pending_approval: 'Your account is pending approval. Please wait for admin confirmation.',
        account_already_exists: 'This phone number is already registered as a CTV. Please login.'
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

    // Reload terms in the selected language
    loadSignupTerms();
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
let termsShown = false; // Track if terms have been shown

// Make functions global for HTML onclick access
window.openTermsModal = function (event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    console.log('Global openTermsModal called');

    const modal = document.getElementById('termsModal');

    if (!modal) {
        console.error('Terms modal not found');
        alert('Lỗi: Không tìm thấy khung điều khoản. Vui lòng tải lại trang.');
        return;
    }

    // FORCE SHOW MODAL - Direct Style Manipulation
    modal.classList.add('show');
    modal.style.cssText = 'display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 999999 !important;';

    // Fix body
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.width = '100%';
    document.body.style.top = '0';

    return false;
};

// Also attach to the old name just in case
function openTermsModal() {
    return window.openTermsModal();
}

window.closeTermsModal = function () {
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
            // Show success message with CTV code if available
            let msg = t('signup_success');
            if (data.ctv_code) {
                msg = `${msg} Mã CTV: ${data.ctv_code}`;
            }
            successMsg.textContent = msg;
            successMsg.style.display = 'block';

            // Clear form
            document.getElementById('signupForm').reset();

            // Redirect to login after 2 seconds (account is already active)
            setTimeout(() => {
                window.location.href = '/ctv/portal';
            }, 2000);
        } else {
            // Show error message
            if (data.error_code === 'PENDING_APPROVAL') {
                alert(t('pending_approval'));
                errorMsg.textContent = t('pending_approval');
            } else if (data.error_code === 'ALREADY_REGISTERED') {
                alert(t('account_already_exists'));
                errorMsg.textContent = t('account_already_exists');
            } else if (data.message && data.message.includes('phone')) {
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
    loadSignupTerms(); // Load terms from database

    // Check for referral link parameter
    const urlParams = new URLSearchParams(window.location.search);
    const refPhone = urlParams.get('ref');

    const referrerInput = document.getElementById('referrerCode');
    if (refPhone && referrerInput) {
        // Pre-fill the referrer phone number from URL
        referrerInput.value = refPhone;
        referrerInput.readOnly = true; // Lock the field

        // Robust locking: prevent all mouse and touch interaction
        referrerInput.style.pointerEvents = 'none';
        referrerInput.style.cursor = 'not-allowed';
        referrerInput.style.userSelect = 'none';
        referrerInput.tabIndex = -1; // Prevent keyboard focus

        // Visual feedback for locked state
        referrerInput.style.backgroundColor = '#f9fafb';
        referrerInput.style.color = '#6b7280';
        referrerInput.style.borderColor = '#e5e7eb';
        referrerInput.style.fontWeight = '600';

        // Trigger validation to show referrer name
        debouncedCheckReferrer(refPhone);

        // Add a small badge or note if possible, but for now just the styling is enough
    }

    // Auto-show terms modal on first visit
    if (!termsShown) {
        termsShown = true;
        // Show modal after a brief delay to ensure page is loaded
        setTimeout(() => {
            window.openTermsModal();

            // Auto-close after 3 seconds
            setTimeout(() => {
                window.closeTermsModal();
            }, 3000);
        }, 500);
    }

    // Attach real-time validation to referrer code input
    if (referrerInput) {
        referrerInput.addEventListener('input', (e) => {
            // Revert changes if field is locked
            if (e.target.readOnly && refPhone) {
                e.target.value = refPhone;
                return;
            }
            debouncedCheckReferrer(e.target.value);
            // Reset styling if user manually changes
            if (!e.target.readOnly) {
                e.target.style.backgroundColor = '';
                e.target.style.borderColor = '';
            }
        });
    }

    // Terms modal event listeners
    const closeTermsModal_btn = document.getElementById('closeTermsModal');
    const closeTermsBtn = document.getElementById('closeTermsBtn');
    const termsModal = document.getElementById('termsModal');

    if (closeTermsModal_btn) {
        closeTermsModal_btn.addEventListener('click', window.closeTermsModal);
    }

    if (closeTermsBtn) {
        closeTermsBtn.addEventListener('click', window.closeTermsModal);
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
