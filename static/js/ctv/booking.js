/**
 * CTV Portal - Booking Module
 * DOES: Handles booking form submission and initialization
 * INPUTS: Booking form submit events
 * OUTPUTS: API calls to submit booking data
 */

// Check phone duplicate on booking page
// Note: .trim() only removes whitespace, trailing zeros in phone numbers are preserved
async function checkBookingPhone() {
    const input = document.getElementById('bookingCustomerPhone');
    const result = document.getElementById('bookingPhoneResult');
    const phone = input.value.trim(); // Preserves trailing zeros
    
    if (!phone || phone.length < 8) {
        result.textContent = t('phone_short') || 'Số điện thoại quá ngắn';
        result.className = 'phone-check-result warning';
        result.style.display = 'inline-block';
        return;
    }
    
    result.textContent = t('checking') || 'Đang kiểm tra...';
    result.className = 'phone-check-result checking';
    result.style.display = 'inline-block';
    
    try {
        const response = await api('/api/ctv/check-phone', {
            method: 'POST',
            body: JSON.stringify({ phone })
        });
        
        if (response.is_duplicate) {
            result.textContent = t('duplicate') || 'TRÙNG';
            result.className = 'phone-check-result trung';
        } else {
            result.textContent = t('not_duplicate') || 'KHÔNG TRÙNG';
            result.className = 'phone-check-result khong-trung';
        }
        result.style.display = 'inline-block';
    } catch (error) {
        result.textContent = 'Error';
        result.className = 'phone-check-result warning';
        result.style.display = 'inline-block';
    }
}

// Initialize booking form handler
function initBooking() {
    const bookingForm = document.getElementById('bookingForm');
    if (!bookingForm) return;
    
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Note: .trim() only removes whitespace, trailing zeros in phone numbers are preserved
        const customerName = document.getElementById('bookingCustomerName').value.trim();
        const customerPhone = document.getElementById('bookingCustomerPhone').value.trim(); // Preserves trailing zeros
        const serviceInterest = document.getElementById('bookingServiceInterest').value.trim();
        const notes = document.getElementById('bookingNotes').value.trim();
        const region = document.getElementById('bookingRegion').value;
        
        const submitBtn = document.getElementById('bookingSubmitBtn');
        const errorEl = document.getElementById('bookingError');
        const successEl = document.getElementById('bookingSuccess');
        
        // Clear previous messages
        errorEl.style.display = 'none';
        successEl.style.display = 'none';
        
        // Validate required fields
        if (!customerName) {
            errorEl.textContent = t('customer_name_required') || 'Tên khách hàng là bắt buộc';
            errorEl.style.display = 'block';
            return;
        }
        
        if (!customerPhone) {
            errorEl.textContent = t('customer_phone_required') || 'Số điện thoại là bắt buộc';
            errorEl.style.display = 'block';
            return;
        }
        
        if (!serviceInterest) {
            errorEl.textContent = t('service_interest_required') || 'Dịch vụ quan tâm là bắt buộc';
            errorEl.style.display = 'block';
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = t('submitting') || 'Đang gửi...';
        
        try {
            const result = await api('/api/ctv/booking', {
                method: 'POST',
                body: JSON.stringify({
                    customer_name: customerName,
                    customer_phone: customerPhone,
                    service_interest: serviceInterest,
                    notes: notes,
                    region: region
                })
            });
            
            if (result.status === 'success') {
                successEl.textContent = t('booking_success') || 'Thông tin khách hàng đã được gửi thành công!';
                successEl.style.display = 'block';
                // Clear form
                bookingForm.reset();
                // Re-populate referrer phone
                updateBookingReferrerPhone();
            } else {
                errorEl.textContent = result.message || t('booking_failed') || 'Gửi thông tin thất bại';
                errorEl.style.display = 'block';
            }
        } catch (error) {
            errorEl.textContent = t('booking_failed') || 'Gửi thông tin thất bại';
            errorEl.style.display = 'block';
        }
        
        submitBtn.disabled = false;
        submitBtn.textContent = t('submit_booking') || 'Gửi Thông Tin';
    });
    
    // Pre-fill referrer phone when page loads
    updateBookingReferrerPhone();
    
    // Add enter key listener for phone check
    const phoneInput = document.getElementById('bookingCustomerPhone');
    if (phoneInput) {
        phoneInput.addEventListener('keyup', (e) => {
            // Hide result when user types
            const result = document.getElementById('bookingPhoneResult');
            if (result) result.style.display = 'none';
        });
    }
}

// Update referrer phone field with current user's CTV code or phone
// Note: Trailing zeros in phone numbers are preserved when setting the value
function updateBookingReferrerPhone() {
    const referrerPhoneInput = document.getElementById('bookingReferrerPhone');
    if (referrerPhoneInput && typeof currentUser !== 'undefined' && currentUser) {
        // Preserve trailing zeros from database values
        referrerPhoneInput.value = currentUser.ma_ctv || currentUser.sdt || '';
    }
}
