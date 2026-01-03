/**
 * CTV Portal - Translations Module
 * DOES: Manages i18n translations and language switching
 * OUTPUTS: translations object, setLanguage, t, applyTranslations
 * FLOW: Loaded first, used by all modules for text display
 */

const translations = {
    vi: {
        // Login
        login_subtitle: 'Đăng nhập để xem hoa hồng và mạng lưới',
        ctv_code: 'Tên đăng nhập',
        ctv_code_placeholder: 'Nhập mã CTV',
        password: 'Mật khẩu',
        enter_password: 'Nhập mật khẩu',
        remember_me: 'Ghi nhớ đăng nhập',
        login: 'Đăng Nhập',
        back_home: 'Quay về trang chủ',
        login_success: 'Đăng nhập thành công!',
        login_redirecting: 'Đang chuyển hướng...',
        login_failed: 'Đăng nhập thất bại',
        logging_in: 'Đang đăng nhập...',
        
        // Dashboard
        overview: 'Tổng Quan',
        page_overview: 'Tổng Quan',
        earnings: 'Hoa Hồng',
        page_earnings: 'Hoa Hồng',
        network: 'Mạng Lưới',
        page_network: 'Mạng Lưới',
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
        network_size: 'Số Lượng Mạng Lưới',
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
        your_network: 'Mạng Lưới Của Bạn',
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
        error_loading_data: 'Lỗi khi tải dữ liệu',
        // Table Headers
        ten_khach: 'Tên Khách Hàng',
        sdt: 'Số Điện Thoại',
        trang_thai_coc: 'Trạng Thái Cọc',
        service_count: 'Số Dịch Vụ',
        
        // Lifetime Statistics
        lifetime_statistics: 'Thống Kê Toàn Bộ',
        metric: 'Chỉ Số',
        value: 'Giá Trị',
        total_commissions_earned: 'Tổng Hoa Hồng Đã Nhận',
        total_transactions: 'Tổng Số Giao Dịch',
        total_network_members: 'Tổng Thành Viên Mạng Lưới',
        total_services_completed: 'Tổng Dịch Vụ Hoàn Thành',
        total_revenue_generated: 'Tổng Doanh Thu Tạo Ra'
    },
    en: {
        // Login
        login_subtitle: 'Login to view commissions and network',
        ctv_code: 'CTV Code',
        ctv_code_placeholder: 'Enter CTV code',
        password: 'Password',
        enter_password: 'Enter password',
        remember_me: 'Remember me',
        login: 'Login',
        back_home: 'Back to Home',
        login_success: 'Login successful!',
        login_redirecting: 'Redirecting...',
        login_failed: 'Login failed',
        logging_in: 'Logging in...',
        
        // Dashboard
        overview: 'Overview',
        page_overview: 'Overview',
        earnings: 'Earnings',
        page_earnings: 'Earnings',
        network: 'Network',
        page_network: 'Network',
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
        network_size: 'Network Size',
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
        your_network: 'Your Network',
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
        error_loading_data: 'Error loading data',
        // Table Headers
        ten_khach: 'Customer Name',
        sdt: 'Phone Number',
        trang_thai_coc: 'Deposit Status',
        service_count: 'Services',
        
        // Lifetime Statistics
        lifetime_statistics: 'Lifetime Statistics',
        metric: 'Metric',
        value: 'Value',
        total_commissions_earned: 'Total Commissions Earned',
        total_transactions: 'Total Transactions',
        total_network_members: 'Total Network Members',
        total_services_completed: 'Total Services Completed',
        total_revenue_generated: 'Total Revenue Generated'
    }
};

let currentLang = localStorage.getItem('ctv_language') || 'vi';

// Translation function
function t(key) {
    return translations[currentLang][key] || translations['vi'][key] || key;
}

// Apply translations to DOM
function applyTranslations() {
    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang][key]) {
            // Preserve data-indicator span if it exists
            const indicator = el.querySelector('.data-indicator');
            if (indicator) {
                // Save the indicator element
                const indicatorClone = indicator.cloneNode(true);
                // Clear all content
                el.innerHTML = '';
                // Add translated text as text node
                el.appendChild(document.createTextNode(translations[currentLang][key]));
                // Restore the indicator
                el.appendChild(indicatorClone);
                // Update indicator with current config if function exists
                if (typeof updateIndicatorElement === 'function') {
                    updateIndicatorElement(indicatorClone);
                }
            } else {
                el.textContent = translations[currentLang][key];
            }
        }
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[currentLang][key]) {
            el.placeholder = translations[currentLang][key];
        }
    });
    
    // Update tooltips (data-tooltip for custom CSS tooltips)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (translations[currentLang][key]) {
            el.setAttribute('data-tooltip', translations[currentLang][key]);
        }
    });
    
    // Update page title
    document.title = currentLang === 'vi' ? 'CTV Portal' : 'CTV Portal';
}

// Set language
function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('ctv_language', lang);
    applyTranslations();
    
    // Update language options in popup (both desktop and mobile)
    document.querySelectorAll('.lang-option').forEach(opt => {
        const isActive = opt.dataset.lang === lang;
        if (isActive) {
            opt.classList.add('active');
        } else {
            opt.classList.remove('active');
        }
    });
    
    // Update current language labels (sidebar, mobile menu, and login page)
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
    
    // Close any open popups
    const loginToggle = document.getElementById('loginLangToggle');
    if (loginToggle) loginToggle.classList.remove('active');
    
    // Update page title in header
    const activePage = document.querySelector('.page-section.active');
    if (activePage && typeof updatePageTitle === 'function') {
        const pageId = activePage.id.replace('page-', '');
        updatePageTitle(pageId);
    }
    
    // Re-render dynamic content based on active page
    if (activePage) {
        const pageId = activePage.id;
        if (pageId === 'page-dashboard' && typeof loadRecentCommissions === 'function') {
            loadRecentCommissions();
        } else if (pageId === 'page-earnings' && typeof setEarningsDefaultDateFilter === 'function') {
            setEarningsDefaultDateFilter();
        } else if (pageId === 'page-network' && typeof loadNetwork === 'function') {
            loadNetwork();
        }
    }
}

// Toggle language popup (sidebar)
function toggleLangPopup(e) {
    e.stopPropagation();
    const switcher = document.getElementById('langSwitcher');
    switcher.classList.toggle('active');
    // Close login page popup if open
    const loginToggle = document.getElementById('loginLangToggle');
    if (loginToggle) loginToggle.classList.remove('active');
}

// Toggle language popup (login page)
function toggleLoginLangPopup(e) {
    e.stopPropagation();
    const toggle = document.getElementById('loginLangToggle');
    toggle.classList.toggle('active');
}

// Select language from popup
function selectLanguage(lang) {
    setLanguage(lang);
    // Close the popup (desktop)
    const langSwitcher = document.getElementById('langSwitcher');
    if (langSwitcher) langSwitcher.classList.remove('active');
    // Close mobile language popup
    const mobileLangMenu = document.querySelector('.mobile-menu-lang');
    if (mobileLangMenu) mobileLangMenu.classList.remove('active');
}

// Get current language
function getCurrentLang() {
    return currentLang;
}

