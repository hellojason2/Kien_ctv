/**
 * CTV Portal - Booking Module
 * DOES: Handles booking form submission and initialization
 * INPUTS: Booking form submit events
 * OUTPUTS: API calls to submit booking data
 */

// Initialize booking form handler
function initBooking() {
    const bookingForm = document.getElementById('bookingForm');
    if (!bookingForm) return;
    
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const customerName = document.getElementById('bookingCustomerName').value.trim();
        const customerPhone = document.getElementById('bookingCustomerPhone').value.trim();
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
}

// Update referrer phone field with current user's CTV code or phone
function updateBookingReferrerPhone() {
    const referrerPhoneInput = document.getElementById('bookingReferrerPhone');
    if (referrerPhoneInput && typeof currentUser !== 'undefined' && currentUser) {
        referrerPhoneInput.value = currentUser.ma_ctv || currentUser.sdt || '';
    }
}
