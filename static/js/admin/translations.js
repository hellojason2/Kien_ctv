/**
 * Admin Dashboard - Translations Module
 * i18n system with Vietnamese and English
 * 
 * Created: December 30, 2025
 */

const translations = {
    vi: {
        // Login
        admin_login: 'Dang Nhap Admin',
        ctv_system: 'He Thong Quan Ly CTV',
        username: 'Ten dang nhap',
        password: 'Mat khau',
        enter_username: 'Nhap ten dang nhap',
        enter_password: 'Nhap mat khau',
        login: 'Dang Nhap',
        back_home: '<- Quay ve trang chu',
        login_failed: 'Dang nhap that bai',
        
        // Navigation
        home_dashboard: '<- Trang Chu',
        overview: 'Tong Quan',
        ctv_management: 'Quan Ly CTV',
        hierarchy: 'Cap Bac',
        commissions: 'Hoa Hong',
        clients: 'Khach Hang',
        settings: 'Cai Dat',
        activity_logs: 'Nhat Ky',
        logout: 'Dang Xuat',
        
        // Activity Logs
        logins_today: 'Dang Nhap Hom Nay',
        failed_logins: 'Dang Nhap That Bai',
        unique_ips: 'IP Doc Nhat',
        total_logs: 'Tong So Log',
        event_type: 'Loai Su Kien',
        user_type: 'Loai Nguoi Dung',
        date_from: 'Tu Ngay',
        date_to: 'Den Ngay',
        search: 'Tim Kiem',
        apply_filters: 'Ap Dung',
        recent_activity: 'Hoat Dong Gan Day',
        timestamp: 'Thoi Gian',
        event: 'Su Kien',
        user: 'Nguoi Dung',
        ip_address: 'Dia Chi IP',
        endpoint: 'Diem Cuoi',
        status: 'Trang Thai',
        details: 'Chi Tiet',
        export_csv: 'Xuat CSV',
        export_excel: 'Xuat Excel',
        refresh: 'Lam Moi',
        showing: 'Hien thi',
        of: 'trong',
        logs: 'log',
        no_logs_found: 'Khong tim thay log nao',
        grouped_view: 'Xem nhom',
        groups: 'nhom',
        activities: 'hoat dong',
        click_to_load: 'Bam de tai chi tiet',
        suspicious_ips_detected: 'Phat hien IP dang nghi',
        multi_account_ip: 'Nhieu tai khoan',
        accounts: 'tai khoan',
        
        // Client Management
        client_management: 'Quan Ly Khach Hang',
        client_search_placeholder: 'Tim theo ten hoac so dien thoai...',
        
        // Dashboard
        dashboard_overview: 'Tong Quan Dashboard',
        total_ctv: 'Tong CTV',
        monthly_commission: 'Hoa Hong Thang',
        monthly_transactions: 'Giao Dich Thang',
        monthly_revenue: 'Doanh Thu Thang',
        top_earners: 'Top Thu Nhap Thang Nay',
        no_earnings: 'Chua co thu nhap thang nay',
        ctv_name: 'CTV',
        total_revenue: 'Doanh Thu',
        total_commission: 'Hoa Hong',
        
        // CTV Management
        add_ctv: '+ Them CTV',
        search_placeholder: 'Tim theo ten, email, dien thoai...',
        show_inactive: 'Hien CTV Ngung',
        code: 'Ma',
        name: 'Ten',
        email: 'Email',
        phone: 'Dien Thoai',
        referrer: 'Nguoi Gioi Thieu',
        level: 'Cap Bac',
        actions: 'Thao Tac',
        active: 'Hoat dong',
        inactive: 'Ngung hoat dong',
        
        // Commission Settings
        commission_settings: 'Cai Dat Hoa Hong',
        commission_rates: 'Ty Le Hoa Hong Theo Cap',
        save_changes: 'Luu Thay Doi',
        settings_saved: 'Da luu cai dat!',
        
        // Hierarchy
        hierarchy_tree: 'Cay Cap Bac',
        select_root: 'Chon CTV Goc',
        select_ctv: 'Chon CTV',
        select_ctv_view: 'Chon CTV de xem cap bac',
        type_to_search: 'Go de tim CTV...',
        no_ctv_found: 'Khong tim thay CTV',
        total_members: 'Tong Thanh Vien',
        levels_deep: 'Do Sau',
        direct_recruits: 'Truc Tiep',
        expand_all: 'Mo Rong',
        collapse_all: 'Thu Gon',
        
        // Commission Reports
        commission_reports: 'Bao Cao Hoa Hong',
        filter_ctv: 'Loc theo CTV',
        filter_month: 'Loc theo Thang',
        filter_level: 'Loc theo Cap',
        all_ctvs: 'Tat ca CTV',
        all_levels: 'Tat ca Cap',
        no_commissions: 'Khong co hoa hong',
        rate: 'Ty Le',
        transaction: 'Giao Dich',
        commission: 'Hoa Hong',
        date: 'Ngay',
        
        // Status
        da_coc: 'Da coc',
        chua_coc: 'Chua coc',
        
        // Modal
        add_new_ctv: 'Them CTV Moi',
        ctv_code: 'Ma CTV',
        ctv_code_placeholder: 'VD: CTV012',
        full_name: 'Ho ten day du',
        referrer_label: 'Nguoi Gioi Thieu',
        none_root: 'Khong (CTV Goc)',
        cancel: 'Huy',
        create_ctv: 'Tao CTV',
        
        // Language
        language: 'Ngon Ngu',
        choose_language: 'Chon Ngon Ngu',
        
        // Loading
        loading: 'Dang tai...',
        loading_hierarchy: 'Dang tai cay cap bac...',
        loading_please_wait: 'Vui long doi, co the mat mot luc cho cay lon',
        
        // Service Card Labels
        tong_tien: 'Tong tien:',
        tien_coc: 'Tien coc:',
        phai_dong: 'Phai dong:',
        ngay_hen: 'Ngay hen:',
        ngay_nhap_don: 'Ngay nhap don:',
        ngay_hen_lam: 'Ngay hen lam:',
        
        // Client Card Labels
        co_so: 'Co so',
        first_visit: 'Lan dau',
        nguoi_chot: 'Nguoi chot',
        service: 'Dich Vu',
        services: 'Dich Vu',
        services_title: 'Dich Vu',
        unknown_service: 'Dich vu khong xac dinh'
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
    document.title = currentLang === 'vi' ? 'Admin Dashboard - He Thong CTV' : 'Admin Dashboard - CTV System';
}

/**
 * Initialize language on page load
 */
function initLanguage() {
    setLanguage(currentLang);
}

