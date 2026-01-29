/**
 * CTV Portal - Translations Module
 * DOES: Manages i18n translations and language switching
 * OUTPUTS: translations object, setLanguage, t, applyTranslations
 * FLOW: Loaded first, used by all modules for text display
 */

window.translations = {
    vi: {
        // Login
        login_subtitle: 'Đăng nhập để xem hoa hồng và team',
        ctv_code: 'Tên đăng nhập',
        ctv_code_placeholder: 'Nhập số điện thoại',
        password: 'Mật khẩu',
        enter_password: 'Nhập mật khẩu',
        remember_me: 'Ghi nhớ đăng nhập',
        login: 'Đăng Nhập',
        back_home: 'Quay về trang chủ',
        login_success: 'Đăng nhập thành công!',
        login_redirecting: 'Đang chuyển hướng...',
        login_failed: 'Đăng nhập thất bại',
        logging_in: 'Đang đăng nhập...',

        // Branding
        ctv_portal: 'CTV Portal',

        // Dashboard
        overview: 'Tổng Quan',
        page_overview: 'Tổng Quan',
        earnings: 'Hoa Hồng',
        page_earnings: 'Hoa Hồng',
        network: 'Team',
        page_network: 'Team',
        customers: 'Khách Hàng',
        page_customers: 'Khách Hàng',
        search: 'Tìm Kiếm',
        search_placeholder: 'Tìm kiếm khách hàng...',
        settings: 'Cài Đặt',
        page_settings: 'Cài Đặt',
        logout: 'Đăng Xuất',
        language: 'Ngôn Ngữ',
        choose_language: 'Chọn Ngôn Ngữ',
        menu: 'Menu',

        // Stats
        total_earnings: 'Tổng Thu Nhập',
        this_month: 'Thu Nhập Tháng Này',
        network_size: 'Quy Mô Team',
        direct_referrals: 'Giới Thiệu Trực Tiếp',
        direct_level1: 'Trực Tiếp (Level 1)',
        services_this_month: 'Dịch Vụ Tháng Này',
        recent_commissions: 'Hoa Hồng Gần Đây',

        // Period Labels
        earnings_period_today: 'Thu Nhập Hôm Nay',
        earnings_period_3days: 'Thu Nhập 3 Ngày Qua',
        earnings_period_week: 'Thu Nhập Tuần Này',
        earnings_period_month: 'Thu Nhập Tháng Này',
        earnings_period_lastmonth: 'Thu Nhập Tháng Trước',
        earnings_period_3months: 'Thu Nhập 3 Tháng',
        earnings_period_year: 'Thu Nhập Năm Nay',
        earnings_period_custom: 'Thu Nhập Khoảng Thời Gian',

        // Total Revenue Period Labels
        total_revenue_today: 'Tổng Doanh Thu Hôm Nay',
        total_revenue_3days: 'Tổng Doanh Thu 3 Ngày Qua',
        total_revenue_week: 'Tổng Doanh Thu Tuần Này',
        total_revenue_month: 'Tổng Doanh Thu Tháng Này',
        total_revenue_lastmonth: 'Tổng Doanh Thu Tháng Trước',
        total_revenue_3months: 'Tổng Doanh Thu 3 Tháng',
        total_revenue_year: 'Tổng Doanh Thu Năm Nay',
        total_revenue_custom: 'Tổng Doanh Thu Khoảng Thời Gian',

        // Commission Period Labels
        commission_period_today: 'Hoa Hồng Hôm Nay',
        commission_period_3days: 'Hoa Hồng 3 Ngày Qua',
        commission_period_week: 'Hoa Hồng Tuần Này',
        commission_period_month: 'Hoa Hồng Tháng Này',
        commission_period_lastmonth: 'Hoa Hồng Tháng Trước',
        commission_period_3months: 'Hoa Hồng 3 Tháng',
        commission_period_year: 'Hoa Hồng Năm Nay',
        commission_period_custom: 'Hoa Hồng Khoảng Thời Gian',

        services_period_today: 'Dịch Vụ Hôm Nay',
        services_period_3days: 'Dịch Vụ 3 Ngày Qua',
        services_period_week: 'Dịch Vụ Tuần Này',
        services_period_month: 'Dịch Vụ Tháng Này',
        services_period_lastmonth: 'Dịch Vụ Tháng Trước',
        services_period_3months: 'Dịch Vụ 3 Tháng',
        services_period_year: 'Dịch Vụ Năm Nay',
        services_period_custom: 'Dịch Vụ Khoảng Thời Gian',

        // Filters
        from_date: 'Từ ngày:',
        to_date: 'Đến ngày:',
        filter: 'Lọc',
        all: 'Tất Cả',
        all_status: 'Tất cả trạng thái',
        all_levels: 'Tất cả cấp',
        custom_range: 'Tùy chỉnh',
        today: 'Hôm nay',
        three_days: '3 ngày qua',
        week: 'Tuần này',
        this_month: 'Tháng này',
        last_month: 'Tháng trước',
        three_months: '3 tháng',
        this_year: 'Năm nay',
        select_filter_hint: 'Chọn ngày và nhấn Lọc để xem hoa hồng',
        click_filter_hint: 'Nhấn Lọc để xem danh sách',

        // Commission
        no_commissions: 'Chưa có hoa hồng nào',
        no_commissions_period: 'Không có hoa hồng trong khoảng thời gian này',
        total_commission: 'Tổng Hoa Hồng',
        level: 'Cấp',
        level_0_self: 'Level 0 (Bản Thân)',
        rate: 'Tỷ Lệ',
        amount: 'Số Tiền',
        from_ctv: 'Từ CTV',
        customer: 'Khách Hàng',
        customers: 'Khách Hàng',
        service: 'Dịch Vụ',
        date: 'Ngày',
        transactions: 'Giao Dịch',
        revenue: 'Doanh Thu',

        // Network
        your_network: 'Team Của Bạn',
        direct_list: 'Danh Sách CTV Trực Tiếp',
        no_referrals: 'Bạn chưa giới thiệu ai',
        no_customers: 'Chưa có khách hàng nào',
        stats_by_level: 'Thống Kê Theo Cấp',
        count: 'Số Lượng',
        total_members: 'TỔNG THÀNH VIÊN',
        levels_deep: 'SỐ CẤP',
        direct_recruits: 'GIỚI THIỆU TRỰC TIẾP',
        expand_all: 'Mở Rộng',
        collapse_all: 'Thu Gọn',
        ctv_code_col: 'Mã CTV',
        name_col: 'Tên',
        email_col: 'Email',
        phone_col: 'SĐT',
        rank_col: 'Cấp Bậc',

        // Settings / Change Password
        change_password: 'Đổi Mật Khẩu',
        current_password: 'Mật khẩu hiện tại',
        current_password_placeholder: 'Nhập mật khẩu hiện tại',
        new_password: 'Mật khẩu mới',
        new_password_placeholder: 'Nhập mật khẩu mới (ít nhất 6 ký tự)',
        confirm_password: 'Xác nhận mật khẩu mới',
        confirm_password_placeholder: 'Nhập lại mật khẩu mới',
        change_password_btn: 'Đổi Mật Khẩu',
        password_changed: 'Đổi mật khẩu thành công!',
        password_mismatch: 'Mật khẩu mới không khớp',
        password_too_short: 'Mật khẩu mới phải có ít nhất 6 ký tự',

        // Booking Appointments
        booking_appointments: 'Giới thiệu khách',
        page_booking: 'Giới thiệu khách',
        book_appointment: 'Giới thiệu khách',
        introduce_customer: 'Giới thiệu khách',
        your_customers: 'Khách của bạn',

        // Catalogue
        catalogue: 'Catalog',
        pricing: 'Bảng Giá TMV',
        booking_form_title: 'Thông Tin Khách Hàng',
        booking_form_subtitle: 'Bạn vui lòng nhập thông tin khách hàng tại đây',
        customer_name: 'Tên khách hàng',
        customer_name_placeholder: 'Nhập tên khách hàng',
        customer_phone: 'Số điện thoại',
        customer_phone_placeholder: 'Nhập số điện thoại',
        service_interest: 'Dịch vụ Quan tâm',
        service_interest_placeholder: 'Nhập dịch vụ quan tâm',
        notes: 'Ghi chú',
        notes_placeholder: 'Nhập ghi chú (tùy chọn)',
        customer_region: 'Khu vực của khách hàng',
        select_region: '-- Chọn khu vực --',
        region_north: 'Miền Bắc',
        region_south: 'Miền Nam',
        region_central: 'Miền Trung',
        referrer_phone: 'SDT người giới thiệu',
        submit_booking: 'Gửi Thông Tin',
        submitting: 'Đang gửi...',
        booking_success: 'Thông tin khách hàng đã được gửi thành công!',
        booking_failed: 'Gửi thông tin thất bại',
        customer_name_required: 'Tên khách hàng là bắt buộc',
        customer_phone_required: 'Số điện thoại là bắt buộc',
        service_interest_required: 'Dịch vụ quan tâm là bắt buộc',

        // Phone Check
        phone_check_title: 'Kiểm Tra Trùng Lặp Số Điện Thoại',
        phone_check_placeholder: 'Nhập số điện thoại...',
        check: 'Kiểm Tra',
        checking: 'Đang kiểm tra...',
        duplicate: 'TRÙNG',
        not_duplicate: 'KHÔNG TRÙNG',
        phone_short: 'Số điện thoại quá ngắn',

        // Status
        completed: 'Đã đến làm',
        deposited: 'Đã cọc',
        cancelled: 'Hủy lịch',
        pending: 'Chờ xác nhận',
        da_coc: 'Đã cọc',
        chua_coc: 'Chưa cọc',

        // Loading
        loading: 'Đang tải...',
        no_data: 'Chưa có dữ liệu',

        // Service Card Labels
        tong_tien: 'Tổng tiền:',
        tien_coc: 'Tiền cọc:',
        phai_dong: 'Phải đóng:',
        ngay_nhap_don: 'Ngày nhập đơn:',
        ngay_hen_lam: 'Ngày hẹn làm:',

        // Client Card Labels
        co_so: 'Cơ sở',
        first_visit: 'Lần đầu',
        dich_vu: 'Dịch Vụ',
        services_title: 'Dịch Vụ',
        unknown_service: 'Dịch vụ không xác định',
        view_cards: 'Thẻ',
        view_table: 'Bảng',
        my_customers: 'Khách Hàng Của Bạn',
        vietnamese: 'Tiếng Việt',
        english: 'English',
        error_loading_data: 'Lỗi khi tải dữ liệu',

        // Table Headers
        ten_khach: 'Tên Khách Hàng',
        sdt: 'Số Điện Thoại',
        trang_thai_coc: 'Trạng Thái Cọc',
        status: 'Trạng Thái',
        service_count: 'Số Dịch Vụ',

        // Lifetime Statistics
        lifetime_statistics: 'Thống Kê Toàn Bộ',
        metric: 'Chỉ Số',
        value: 'Giá Trị',
        total_commissions_earned: 'Tổng Hoa Hồng Đã Nhận',
        total_transactions: 'Tổng Số Giao Dịch',
        total_network_members: 'Tổng Thành Viên Team',
        total_services_completed: 'Tổng Dịch Vụ Hoàn Thành',
        total_revenue_generated: 'Tổng Doanh Thu Tạo Ra',

        // Referral Link
        share_referral: 'Chia Sẻ Link',
        referral_link_copied: 'Đã sao chép link giới thiệu!',
        copy_link: 'Sao Chép Link',

        // Voice Input
        voice_input_title: 'Nhập bằng giọng nói',
        voice_input_short: 'Nhập giọng nói',
        press_to_speak: 'Bấm để nói',
        tap_to_stop: 'Nhấn để dừng',
        listening: 'Đang nghe...',
        processing: 'Đang xử lý...',
        detected_name: 'Tên:',
        detected_phone: 'SĐT:',
        detected_service: 'DV:',
        voice_hint: '💡 Nói: "Tên Nguyễn Văn A, số điện thoại 0983..., muốn làm nâng mũi"',
        mic_permission_denied: 'Không thể truy cập microphone. Vui lòng cấp quyền.',
        recording_too_short: 'Bản ghi quá ngắn. Vui lòng nói lâu hơn.',
        transcription_failed: 'Có lỗi xảy ra khi xử lý giọng nói'
    },
    en: {
        // Login
        login_subtitle: 'Login to view commissions and team',
        ctv_code: 'CTV Code',
        ctv_code_placeholder: 'Enter phone number',
        password: 'Password',
        enter_password: 'Enter password',
        remember_me: 'Remember me',
        login: 'Login',
        back_home: 'Back to Home',
        login_success: 'Login successful!',
        login_redirecting: 'Redirecting...',
        login_failed: 'Login failed',
        logging_in: 'Logging in...',

        // Branding
        ctv_portal: 'CTV Portal',

        // Dashboard
        overview: 'Overview',
        page_overview: 'Overview',
        earnings: 'Earnings',
        page_earnings: 'Earnings',
        network: 'Team',
        page_network: 'Team',
        customers: 'Customers',
        page_customers: 'Customers',
        search: 'Search',
        search_placeholder: 'Search customers...',
        settings: 'Settings',
        page_settings: 'Settings',
        logout: 'Logout',
        language: 'Language',
        choose_language: 'Choose Language',
        menu: 'Menu',

        // Stats
        total_earnings: 'Total Earnings',
        this_month: 'This Month',
        network_size: 'Team Size',
        direct_referrals: 'Direct Referrals',
        direct_level1: 'Direct (Level 1)',
        services_this_month: 'Services This Month',
        recent_commissions: 'Recent Commissions',

        // Period Labels
        earnings_period_today: 'Earnings Today',
        earnings_period_3days: 'Earnings Last 3 Days',
        earnings_period_week: 'Earnings This Week',
        earnings_period_month: 'Earnings This Month',
        earnings_period_lastmonth: 'Earnings Last Month',
        earnings_period_3months: 'Earnings Last 3 Months',
        earnings_period_year: 'Earnings This Year',
        earnings_period_custom: 'Earnings Period',

        // Total Revenue Period Labels
        total_revenue_today: 'Total Revenue Today',
        total_revenue_3days: 'Total Revenue Last 3 Days',
        total_revenue_week: 'Total Revenue This Week',
        total_revenue_month: 'Total Revenue This Month',
        total_revenue_lastmonth: 'Total Revenue Last Month',
        total_revenue_3months: 'Total Revenue Last 3 Months',
        total_revenue_year: 'Total Revenue This Year',
        total_revenue_custom: 'Total Revenue Period',

        // Commission Period Labels
        commission_period_today: 'Commission Today',
        commission_period_3days: 'Commission Last 3 Days',
        commission_period_week: 'Commission This Week',
        commission_period_month: 'Commission This Month',
        commission_period_lastmonth: 'Commission Last Month',
        commission_period_3months: 'Commission Last 3 Months',
        commission_period_year: 'Commission This Year',
        commission_period_custom: 'Commission Period',

        services_period_today: 'Services Today',
        services_period_3days: 'Services Last 3 Days',
        services_period_week: 'Services This Week',
        services_period_month: 'Services This Month',
        services_period_lastmonth: 'Services Last Month',
        services_period_3months: 'Services Last 3 Months',
        services_period_year: 'Services This Year',
        services_period_custom: 'Services Period',

        // Filters
        from_date: 'From:',
        to_date: 'To:',
        filter: 'Filter',
        all: 'All',
        all_status: 'All Status',
        all_levels: 'All Levels',
        custom_range: 'Custom',
        today: 'Today',
        three_days: '3 Days',
        week: 'This Week',
        this_month: 'This Month',
        last_month: 'Last Month',
        three_months: '3 Months',
        this_year: 'This Year',
        select_filter_hint: 'Select dates and click Filter to view commissions',
        click_filter_hint: 'Click Filter to view list',

        // Commission
        no_commissions: 'No commissions yet',
        no_commissions_period: 'No commissions in this period',
        total_commission: 'Total Commission',
        level: 'Level',
        level_0_self: 'Level 0 (Self)',
        rate: 'Rate',
        amount: 'Amount',
        from_ctv: 'From CTV',
        customer: 'Customer',
        customers: 'Customers',
        service: 'Service',
        date: 'Date',
        transactions: 'Transactions',
        revenue: 'Revenue',

        // Network
        your_network: 'Your Team',
        direct_list: 'Direct Referrals List',
        no_referrals: 'No referrals yet',
        no_customers: 'No customers yet',
        stats_by_level: 'Stats by Level',
        count: 'Count',
        total_members: 'TOTAL MEMBERS',
        levels_deep: 'LEVELS DEEP',
        direct_recruits: 'DIRECT RECRUITS',
        expand_all: 'Expand All',
        collapse_all: 'Collapse All',
        ctv_code_col: 'CTV Code',
        name_col: 'Name',
        email_col: 'Email',
        phone_col: 'Phone',
        rank_col: 'Rank',

        // Settings / Change Password
        change_password: 'Change Password',
        current_password: 'Current Password',
        current_password_placeholder: 'Enter current password',
        new_password: 'New Password',
        new_password_placeholder: 'Enter new password (at least 6 characters)',
        confirm_password: 'Confirm New Password',
        confirm_password_placeholder: 'Re-enter new password',
        change_password_btn: 'Change Password',
        password_changed: 'Password changed successfully!',
        password_mismatch: 'New passwords do not match',
        password_too_short: 'New password must be at least 6 characters',

        // Booking Appointments
        booking_appointments: 'Refer Customer',
        page_booking: 'Refer Customer',
        book_appointment: 'Refer Customer',
        introduce_customer: 'Refer Customer',
        your_customers: 'Your Customers',

        // Catalogue
        catalogue: 'Catalog',
        pricing: 'TMV Pricing',
        booking_form_title: 'Customer Information',
        booking_form_subtitle: 'Please enter customer information here',
        customer_name: 'Customer Name',
        customer_name_placeholder: 'Enter customer name',
        customer_phone: 'Phone Number',
        customer_phone_placeholder: 'Enter phone number',
        service_interest: 'Service of Interest',
        service_interest_placeholder: 'Enter service of interest',
        notes: 'Notes',
        notes_placeholder: 'Enter notes (optional)',
        customer_region: 'Customer Region',
        select_region: '-- Select region --',
        region_north: 'Northern Region',
        region_south: 'Southern Region',
        region_central: 'Central Region',
        referrer_phone: 'Referrer Phone Number',
        submit_booking: 'Submit Information',
        submitting: 'Submitting...',
        booking_success: 'Customer information submitted successfully!',
        booking_failed: 'Failed to submit information',
        customer_name_required: 'Customer name is required',
        customer_phone_required: 'Phone number is required',
        service_interest_required: 'Service of interest is required',

        // Phone Check
        phone_check_title: 'Phone Number Check',
        phone_check_placeholder: 'Enter phone number...',
        check: 'Check',
        checking: 'Checking...',
        duplicate: 'DUPLICATE',
        not_duplicate: 'NOT DUPLICATE',
        phone_short: 'Phone number too short',

        // Status
        completed: 'Completed',
        deposited: 'Deposited',
        cancelled: 'Cancelled',
        pending: 'Pending',
        da_coc: 'Deposited',
        chua_coc: 'Not Deposited',

        // Loading
        loading: 'Loading...',
        no_data: 'No data',

        // Service Card Labels
        tong_tien: 'Total:',
        tien_coc: 'Deposit:',
        phai_dong: 'Due:',
        ngay_nhap_don: 'Order Date:',
        ngay_hen_lam: 'Appointment Date:',

        // Client Card Labels
        co_so: 'Facility',
        first_visit: 'First Visit',
        dich_vu: 'Services',
        services_title: 'Services',
        unknown_service: 'Unknown Service',
        view_cards: 'Cards',
        view_table: 'Table',
        my_customers: 'My Customers',
        vietnamese: 'Vietnamese',
        english: 'English',
        error_loading_data: 'Error loading data',

        // Table Headers
        ten_khach: 'Customer Name',
        sdt: 'Phone Number',
        trang_thai_coc: 'Deposit Status',
        status: 'Status',
        service_count: 'Services',

        // Lifetime Statistics
        lifetime_statistics: 'Lifetime Statistics',
        metric: 'Metric',
        value: 'Value',
        total_commissions_earned: 'Total Commissions Earned',
        total_transactions: 'Total Transactions',
        total_network_members: 'Total Team Members',
        total_services_completed: 'Total Services Completed',
        total_revenue_generated: 'Total Revenue Generated',

        // Referral Link
        share_referral: 'Share Link',
        referral_link_copied: 'Referral link copied!',
        copy_link: 'Copy Link',

        // Voice Input
        voice_input_title: 'Voice Input',
        voice_input_short: 'Voice Input',
        press_to_speak: 'Press to Speak',
        tap_to_stop: 'Tap to Stop',
        listening: 'Listening...',
        processing: 'Processing...',
        detected_name: 'Name:',
        detected_phone: 'Phone:',
        detected_service: 'Service:',
        voice_hint: '💡 Say: \"Name John Smith, phone 0983..., want rhinoplasty\"',
        mic_permission_denied: 'Cannot access microphone. Please grant permission.',
        recording_too_short: 'Recording too short. Please speak longer.',
        transcription_failed: 'Error processing voice input'
    }
};

window.currentLang = localStorage.getItem('ctv_language') || 'vi';

// Validate language
if (!window.translations[window.currentLang]) {
    console.warn(`Language '${window.currentLang}' not supported, falling back to 'vi'`);
    window.currentLang = 'vi';
    localStorage.setItem('ctv_language', 'vi');
}

// Translation function
window.t = function (key) {
    if (!window.translations[window.currentLang]) {
        return window.translations['vi'][key] || key;
    }
    return window.translations[window.currentLang][key] || window.translations['vi'][key] || key;
}

// Apply translations to DOM
window.applyTranslations = function () {
    // Safety check
    if (!window.translations[window.currentLang]) {
        window.currentLang = 'vi';
    }
    const currentDict = window.translations[window.currentLang];

    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (currentDict && currentDict[key]) {
            // Check if this is an active date filter button with a date range
            const isActiveFilterButton = el.classList.contains('btn-filter-preset') && el.classList.contains('active');
            const dateRange = el.getAttribute('data-date-range');

            // Preserve data-indicator span if it exists
            const indicator = el.querySelector('.data-indicator');
            if (indicator) {
                // Save the indicator element
                const indicatorClone = indicator.cloneNode(true);
                // Clear all content
                el.innerHTML = '';

                // Add translated text + date range if this is an active filter button
                let textContent = currentDict[key];
                if (isActiveFilterButton && dateRange) {
                    textContent = `${textContent} ${dateRange}`;
                }

                el.appendChild(document.createTextNode(textContent));
                // Restore the indicator
                el.appendChild(indicatorClone);
                // Update indicator with current config if function exists
                if (typeof updateIndicatorElement === 'function') {
                    updateIndicatorElement(indicatorClone);
                }
            } else {
                // For non-button elements or buttons without indicators
                let textContent = currentDict[key];
                if (isActiveFilterButton && dateRange) {
                    textContent = `${textContent} ${dateRange}`;
                }
                el.textContent = textContent;
            }
        }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (currentDict && currentDict[key]) {
            el.placeholder = currentDict[key];
        }
    });

    // Update tooltips (data-tooltip for custom CSS tooltips)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (currentDict && currentDict[key]) {
            el.setAttribute('data-tooltip', currentDict[key]);

            // Also update the child .sidebar-tooltip element if it exists
            const tooltipEl = el.querySelector('.sidebar-tooltip');
            if (tooltipEl) {
                tooltipEl.textContent = currentDict[key];
            }
        }
    });

    // Update page title
    document.title = window.currentLang === 'vi' ? 'CTV Portal' : 'CTV Portal';
}

// Set language
window.setLanguage = function (lang) {
    // Validate language
    if (!window.translations[lang]) {
        console.warn(`Language '${lang}' not supported, falling back to 'vi'`);
        lang = 'vi';
    }

    window.currentLang = lang;
    localStorage.setItem('ctv_language', lang);
    window.applyTranslations();

    // Update language options in popup (both desktop and mobile)
    document.querySelectorAll('.lang-option').forEach(opt => {
        const isActive = opt.dataset.lang === lang;
        if (isActive) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });

    // Update current language labels (sidebar, mobile menu, header, and login page)
    const langLabel = document.getElementById('currentLangLabel');
    if (langLabel) {
        langLabel.textContent = lang.toUpperCase();
    }
    const mobileLangLabel = document.getElementById('mobileCurrentLangLabel');
    if (mobileLangLabel) {
        mobileLangLabel.textContent = lang.toUpperCase();
    }
    const loginLangLabel = document.getElementById('loginLangLabel');
    if (loginLangLabel) {
        loginLangLabel.textContent = lang.toUpperCase();
    }
    // Update floating header language label
    const headerLangLabel = document.getElementById('headerLangLabel');
    if (headerLangLabel) {
        headerLangLabel.textContent = lang.toUpperCase();
    }

    // Close any open popups
    const loginToggle = document.getElementById('loginLangToggle');
    if (loginToggle) loginToggle.classList.remove('active');

    // Update header language label if function exists
    if (typeof updateHeaderLangLabel === 'function') {
        updateHeaderLangLabel();
    }

    // Update page title in header
    const activePage = document.querySelector('.page-section.active');
    if (activePage && typeof updatePageTitle === 'function') {
        const pageId = activePage.id.replace('page-', '');
        updatePageTitle(pageId);
    }

    // Re-render dynamic content based on active page
    // NOTE: Don't reload recent commissions on dashboard when language changes
    // It should only reload when date filter changes
    if (activePage) {
        const pageId = activePage.id;
        if (pageId === 'page-dashboard') {
            // Don't reload recent commissions - it's already loaded with date filter
            // Just update the title if needed
            if (typeof updateRecentCommissionsTitle === 'function') {
                updateRecentCommissionsTitle();
            }
        } else if (pageId === 'page-earnings' && typeof setEarningsDefaultDateFilter === 'function') {
            setEarningsDefaultDateFilter();
        } else if (pageId === 'page-network' && typeof loadNetwork === 'function') {
            loadNetwork();
        }
    }
}

// Toggle language popup (sidebar)
window.toggleLangPopup = function (e) {
    e.stopPropagation();
    const switcher = document.getElementById('langSwitcher');
    switcher.classList.toggle('active');
    // Close login page popup if open
    const loginToggle = document.getElementById('loginLangToggle');
    if (loginToggle) loginToggle.classList.remove('active');
}

// Toggle language popup (login page)
window.toggleLoginLangPopup = function (e) {
    e.stopPropagation();
    const toggle = document.getElementById('loginLangToggle');
    toggle.classList.toggle('active');
}

// Select language from popup
window.selectLanguage = function (lang) {
    window.setLanguage(lang);
    // Close the popup (desktop)
    const langSwitcher = document.getElementById('langSwitcher');
    if (langSwitcher) langSwitcher.classList.remove('active');
    // Close mobile language popup
    const mobileLangMenu = document.querySelector('.mobile-menu-lang');
    if (mobileLangMenu) mobileLangMenu.classList.remove('active');
}

// Get current language
window.getCurrentLang = function () {
    return window.currentLang;
}

