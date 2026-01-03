/**
 * Admin Dashboard - Translations Module
 * i18n system with Vietnamese and English
 * 
 * Created: December 30, 2025
 */

const translations = {
    vi: {
        // Login
        admin_login: 'Đăng Nhập Admin',
        ctv_system: 'Hệ Thống Quản Lý CTV',
        username: 'Tên đăng nhập',
        password: 'Mật khẩu',
        enter_username: 'Nhập tên đăng nhập',
        enter_password: 'Nhập mật khẩu',
        login: 'Đăng Nhập',
        remember_me: 'Ghi nhớ đăng nhập',
        back_home: '<- Quay về trang chủ',
        login_failed: 'Đăng nhập thất bại',
        
        // Navigation
        home_dashboard: '<- Trang Chủ',
        overview: 'Tổng Quan',
        ctv_management: 'Quản Lý CTV',
        hierarchy: 'Cấp Bậc',
        commissions: 'Hoa Hồng',
        clients: 'Khách Hàng',
        settings: 'Cài Đặt',
        activity_logs: 'Nhật Ký',
        logout: 'Đăng Xuất',
        
        // Activity Logs
        logins_today: 'Đăng Nhập Hôm Nay',
        failed_logins: 'Đăng Nhập Thất Bại',
        unique_ips: 'IP Duy Nhất',
        total_logs: 'Tổng Số Log',
        event_type: 'Loại Sự Kiện',
        user_type: 'Loại Người Dùng',
        date_from: 'Từ Ngày',
        date_to: 'Đến Ngày',
        search: 'Tìm Kiếm',
        apply_filters: 'Áp Dụng',
        recent_activity: 'Hoạt Động Gần Đây',
        timestamp: 'Thời Gian',
        event: 'Sự Kiện',
        user: 'Người Dùng',
        ip_address: 'Địa Chỉ IP',
        endpoint: 'Điểm Cuối',
        status: 'Trạng Thái',
        details: 'Chi Tiết',
        export_csv: 'Xuất CSV',
        export_excel: 'Xuất Excel',
        refresh: 'Làm Mới',
        showing: 'Hiển thị',
        of: 'trong',
        logs: 'log',
        no_logs_found: 'Không tìm thấy log nào',
        grouped_view: 'Xem nhóm',
        groups: 'nhóm',
        activities: 'hoạt động',
        click_to_load: 'Bấm để tải chi tiết',
        suspicious_ips_detected: 'Phát hiện IP đáng nghi',
        multi_account_ip: 'Nhiều tài khoản',
        accounts: 'tài khoản',
        
        // Client Management
        client_management: 'Quản Lý Khách Hàng',
        client_search_placeholder: 'Tìm theo tên hoặc số điện thoại...',
        
        // Dashboard
        dashboard_overview: 'Tổng Quan Dashboard',
        total_ctv: 'Tổng CTV',
        monthly_commission: 'Hoa Hồng Tháng',
        monthly_transactions: 'Giao Dịch Tháng',
        monthly_revenue: 'Doanh Thu Tháng',
        top_earners: 'Top Thu Nhập Tháng Này',
        no_earnings: 'Chưa có thu nhập tháng này',
        no_ctv_found: 'Không tìm thấy CTV nào',
        ctv_name: 'CTV',
        total_revenue: 'Doanh Thu',
        total_commission: 'Hoa Hồng',
        filter_by_date: 'Lọc Theo Ngày',
        select_month: 'Chọn Tháng',
        select_day: 'Chọn Ngày (Tùy Chọn)',
        
        // CTV Management
        add_ctv: '+ Thêm CTV',
        search_placeholder: 'Tìm theo tên, email, điện thoại...',
        show_inactive: 'Hiện CTV Ngừng',
        code: 'Mã',
        name: 'Tên',
        email: 'Email',
        phone: 'Điện Thoại',
        referrer: 'Người Giới Thiệu',
        level: 'Cấp Bậc',
        actions: 'Thao Tác',
        active: 'Hoạt động',
        inactive: 'Ngừng hoạt động',
        no_clients: 'Không tìm thấy khách hàng nào',
        error_loading_clients: 'Lỗi khi tải danh sách khách hàng',
        clients: 'khách hàng',
        service: 'dịch vụ',
        services: 'dịch vụ',
        
        // Commission Settings
        commission_settings: 'Cài Đặt Hoa Hồng',
        commission_rates: 'Tỷ Lệ Hoa Hồng Theo Cấp',
        save_changes: 'Lưu Thay Đổi',
        settings_saved: 'Đã lưu cài đặt!',
        
        // Hierarchy
        hierarchy_tree: 'Cây Cấp Bậc',
        select_root: 'Chọn CTV Gốc',
        select_ctv: 'Chọn CTV',
        select_ctv_view: 'Chọn CTV để xem cấp bậc',
        type_to_search: 'Gõ để tìm CTV...',
        no_ctv_found: 'Không tìm thấy CTV',
        total_members: 'Tổng Thành Viên',
        levels_deep: 'Độ Sâu',
        direct_recruits: 'Trực Tiếp',
        expand_all: 'Mở Rộng',
        collapse_all: 'Thu Gọn',
        
        // Commission Reports
        commission_reports: 'Báo Cáo Hoa Hồng',
        filter_ctv: 'Lọc theo CTV',
        filter_month: 'Lọc theo Tháng',
        filter_level: 'Lọc theo Cấp',
        all_ctvs: 'Tất cả CTV',
        all_levels: 'Tất cả Cấp',
        no_commissions: 'Không có hoa hồng',
        rate: 'Tỷ Lệ',
        transaction: 'Giao Dịch',
        commission: 'Hoa Hồng',
        date: 'Ngày',
        quick_filters: 'Lọc Nhanh',
        custom_date_range: 'Khoảng Thời Gian Tùy Chỉnh',
        today: 'Hôm Nay',
        last_3_days: '3 Ngày Gần Đây',
        this_week: 'Tuần Này',
        this_month: 'Tháng Này',
        last_3_months: '3 Tháng Gần Đây',
        this_year: 'Năm Nay',
        total_revenue_for_today: 'Tổng Dịch Vụ Hôm Nay',
        total_revenue_for_week: 'Tổng Dịch Vụ Tuần Này',
        total_revenue_for_month: 'Tổng Dịch Vụ Tháng Này',
        total_revenue_for_period: 'Tổng Dịch Vụ',
        total_revenue_for_custom: 'Tổng Dịch Vụ',
        apply: 'Áp Dụng',
        please_select_both_dates: 'Vui lòng chọn cả ngày bắt đầu và ngày kết thúc',
        date_from_must_be_before_date_to: 'Ngày bắt đầu phải trước ngày kết thúc',
        
        // Status
        da_coc: 'Đã cọc',
        chua_coc: 'Chưa cọc',
        
        // Modal
        add_new_ctv: 'Thêm CTV Mới',
        ctv_code: 'Mã CTV',
        ctv_code_placeholder: 'VD: CTV012',
        full_name: 'Họ tên đầy đủ',
        referrer_label: 'Người Giới Thiệu',
        none_root: 'Không (CTV Gốc)',
        cancel: 'Hủy',
        create_ctv: 'Tạo CTV',
        
        // Language
        language: 'Ngôn Ngữ',
        choose_language: 'Chọn Ngôn Ngữ',
        
        // Loading
        loading: 'Đang tải...',
        loading_hierarchy: 'Đang tải cây cấp bậc...',
        loading_please_wait: 'Vui lòng đợi, có thể mất một lúc cho cây lớn',
        
        // Service Card Labels
        tong_tien: 'Tổng tiền:',
        tien_coc: 'Tiền cọc:',
        phai_dong: 'Phải đóng:',
        ngay_hen: 'Ngày hẹn:',
        ngay_nhap_don: 'Ngày nhập đơn:',
        ngay_hen_lam: 'Ngày hẹn làm:',
        
        // Client Card Labels
        co_so: 'Cơ sở',
        first_visit: 'Lần đầu',
        nguoi_chot: 'Người chốt',
        service: 'Dịch Vụ',
        services: 'Dịch Vụ',
        services_title: 'Dịch Vụ',
        unknown_service: 'Dịch vụ không xác định'
    },
    en: {
        // Login
        admin_login: 'Admin Login',
        ctv_system: 'CTV Management System',
        username: 'Username',
        password: 'Password',
        enter_username: 'Enter username',
        enter_password: 'Enter password',
        login: 'Login',
        remember_me: 'Remember Me',
        back_home: '<- Back to Home',
        login_failed: 'Login failed',
        
        // Navigation
        home_dashboard: '<- Home Dashboard',
        overview: 'Overview',
        ctv_management: 'CTV Management',
        hierarchy: 'Hierarchy',
        commissions: 'Commissions',
        clients: 'Clients',
        settings: 'Settings',
        activity_logs: 'Activity Logs',
        logout: 'Logout',
        
        // Activity Logs
        logins_today: 'Logins Today',
        failed_logins: 'Failed Logins',
        unique_ips: 'Unique IPs Today',
        total_logs: 'Total Logs',
        event_type: 'Event Type',
        user_type: 'User Type',
        date_from: 'Date From',
        date_to: 'Date To',
        search: 'Search',
        apply_filters: 'Apply Filters',
        recent_activity: 'Recent Activity',
        timestamp: 'Timestamp',
        event: 'Event',
        user: 'User',
        ip_address: 'IP Address',
        endpoint: 'Endpoint',
        status: 'Status',
        details: 'Details',
        export_csv: 'Export CSV',
        export_excel: 'Export Excel',
        refresh: 'Refresh',
        showing: 'Showing',
        of: 'of',
        logs: 'logs',
        no_logs_found: 'No logs found',
        grouped_view: 'Grouped View',
        groups: 'groups',
        activities: 'activities',
        click_to_load: 'Click to load details',
        suspicious_ips_detected: 'Suspicious IPs Detected',
        multi_account_ip: 'Multi-Account IP',
        accounts: 'accounts',
        
        // Client Management
        client_management: 'Client Management',
        client_search_placeholder: 'Search by name or phone...',
        
        // Dashboard
        dashboard_overview: 'Dashboard Overview',
        total_ctv: 'Total CTV',
        monthly_commission: 'Monthly Commission',
        monthly_transactions: 'Monthly Transactions',
        monthly_revenue: 'Monthly Revenue',
        top_earners: 'Top Earners This Month',
        no_earnings: 'No earnings this month',
        ctv_name: 'CTV',
        total_revenue: 'Total Revenue',
        total_commission: 'Total Commission',
        filter_by_date: 'Filter By Date',
        select_month: 'Select Month',
        select_day: 'Select Day (Optional)',
        
        // CTV Management
        add_ctv: '+ Add CTV',
        search_placeholder: 'Search by name, email, phone...',
        show_inactive: 'Show Inactive',
        code: 'Code',
        name: 'Name',
        email: 'Email',
        phone: 'Phone',
        referrer: 'Referrer',
        level: 'Level',
        status: 'Status',
        actions: 'Actions',
        active: 'Active',
        inactive: 'Inactive',
        
        // Commission Settings
        commission_settings: 'Commission Settings',
        commission_rates: 'Commission Rates by Level',
        save_changes: 'Save Changes',
        settings_saved: 'Settings saved!',
        
        // Hierarchy
        hierarchy_tree: 'Hierarchy Tree',
        select_root: 'Select Root CTV',
        select_ctv: 'Select CTV',
        select_ctv_view: 'Select a CTV to view hierarchy',
        type_to_search: 'Type to search CTV...',
        no_ctv_found: 'No CTV found',
        total_members: 'Total Members',
        levels_deep: 'Levels Deep',
        direct_recruits: 'Direct Recruits',
        expand_all: 'Expand All',
        collapse_all: 'Collapse All',
        
        // Commission Reports
        commission_reports: 'Commission Reports',
        filter_ctv: 'Filter by CTV',
        filter_month: 'Filter by Month',
        filter_level: 'Filter by Level',
        all_ctvs: 'All CTVs',
        all_levels: 'All Levels',
        no_commissions: 'No commissions found',
        rate: 'Rate',
        transaction: 'Transaction',
        commission: 'Commission',
        date: 'Date',
        quick_filters: 'Quick Filters',
        custom_date_range: 'Custom Date Range',
        today: 'Today',
        last_3_days: 'Last 3 Days',
        this_week: 'This Week',
        this_month: 'This Month',
        last_3_months: 'Last 3 Months',
        this_year: 'This Year',
        total_revenue_for_today: 'Total Revenue for Today',
        total_revenue_for_week: 'Total Revenue for This Week',
        total_revenue_for_month: 'Total Revenue for This Month',
        total_revenue_for_period: 'Total Revenue',
        total_revenue_for_custom: 'Total Revenue',
        apply: 'Apply',
        please_select_both_dates: 'Please select both start and end dates',
        date_from_must_be_before_date_to: 'Start date must be before end date',
        
        // Modal
        add_new_ctv: 'Add New CTV',
        ctv_code: 'CTV Code',
        ctv_code_placeholder: 'e.g., CTV012',
        full_name: 'Full name',
        referrer_label: 'Referrer',
        none_root: 'None (Root CTV)',
        cancel: 'Cancel',
        create_ctv: 'Create CTV',
        
        // Language
        language: 'Language',
        choose_language: 'Choose Language',
        
        // Status
        da_coc: 'Deposited',
        chua_coc: 'Not Deposited',
        
        // Loading
        loading: 'Loading...',
        loading_hierarchy: 'Loading hierarchy tree...',
        loading_please_wait: 'Please wait, this may take a moment for large trees',
        
        // Service Card Labels
        tong_tien: 'Total:',
        tien_coc: 'Deposit:',
        phai_dong: 'Due:',
        ngay_hen: 'Appointment:',
        ngay_nhap_don: 'Order Date:',
        ngay_hen_lam: 'Appointment Date:',
        
        // Client Card Labels
        co_so: 'Facility',
        first_visit: 'First Visit',
        nguoi_chot: 'Closer',
        service: 'Service',
        services: 'Services',
        services_title: 'Services',
        unknown_service: 'Unknown Service'
    }
};

let currentLang = localStorage.getItem('admin_language') || 'en';

/**
 * Toggle language popup visibility
 * @param {Event} e - Click event
 */
function toggleLangPopup(e) {
    e.preventDefault();
    e.stopPropagation();
    const switcher = document.getElementById('langSwitcher');
    if (switcher) {
        switcher.classList.toggle('active');
    }
}

/**
 * Select language from popup and close
 * @param {string} lang - Language code (vi/en)
 */
function selectLanguage(lang) {
    setLanguage(lang);
    // Close the popup
    const switcher = document.getElementById('langSwitcher');
    if (switcher) {
        switcher.classList.remove('active');
    }
}

/**
 * Set language and apply translations
 * @param {string} lang - Language code (vi/en)
 */
function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('admin_language', lang);
    applyTranslations();
    
    // Update popup option states
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.lang === lang);
    });
    
    // Update current language label
    const langLabel = document.getElementById('currentLangLabel');
    if (langLabel) {
        langLabel.textContent = lang.toUpperCase();
    }
    
    // Re-populate dropdowns with translated options
    if (typeof allCTV !== 'undefined' && allCTV.length > 0) {
        populateCTVSelects();
    }
    
    // Re-render client cards if they're currently displayed
    const clientsPage = document.getElementById('clientsPage');
    if (clientsPage && clientsPage.style.display !== 'none') {
        loadClientsWithServices();
    }
}

/**
 * Get translation for a key
 * @param {string} key - Translation key
 * @returns {string} - Translated string
 */
function t(key) {
    return translations[currentLang][key] || translations['en'][key] || key;
}

/**
 * Apply translations to all elements with data-i18n attributes
 */
function applyTranslations() {
    // Update elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang][key]) {
            el.textContent = translations[currentLang][key];
        }
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[currentLang][key]) {
            el.placeholder = translations[currentLang][key];
        }
    });
    
    // Update tooltips
    document.querySelectorAll('[data-i18n-tooltip]').forEach(el => {
        const key = el.getAttribute('data-i18n-tooltip');
        if (translations[currentLang][key]) {
            el.setAttribute('data-tooltip', translations[currentLang][key]);
        }
    });
    
    // Update page title
    document.title = currentLang === 'vi' ? 'Admin Dashboard - Hệ Thống CTV' : 'Admin Dashboard - CTV System';
}

/**
 * Initialize language on page load
 */
function initLanguage() {
    setLanguage(currentLang);
}

