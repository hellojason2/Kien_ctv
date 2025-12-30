/**
 * CTV Portal - Translations Module
 * DOES: Manages i18n translations and language switching
 * OUTPUTS: translations object, setLanguage, t, applyTranslations
 * FLOW: Loaded first, used by all modules for text display
 */

const translations = {
    vi: {
        // Login
        login_subtitle: 'Dang nhap de xem hoa hong va mang luoi',
        ctv_code: 'Ten dang nhap',
        password: 'Mat khau',
        enter_password: 'Nhap mat khau',
        remember_me: 'Ghi nho dang nhap',
        login: 'Dang Nhap',
        back_home: 'Quay ve trang chu',
        login_success: 'Dang nhap thanh cong!',
        login_failed: 'Dang nhap that bai',
        logging_in: 'Dang dang nhap...',
        
        // Dashboard
        overview: 'Tong Quan',
        earnings: 'Hoa Hong',
        network: 'Mang Luoi',
        search: 'Tim Kiem',
        settings: 'Cai Dat',
        logout: 'Dang Xuat',
        language: 'Ngon Ngu',
        choose_language: 'Chon Ngon Ngu',
        
        // Stats
        total_earnings: 'Tong Thu Nhap',
        this_month: 'Thu Nhap Thang Nay',
        network_size: 'So Luong Mang Luoi',
        direct_referrals: 'Gioi Thieu Truc Tiep',
        direct_level1: 'Truc Tiep (Level 1)',
        services_this_month: 'Dich Vu Thang Nay',
        recent_commissions: 'Hoa Hong Gan Day',
        
        // Filters
        from_date: 'Tu ngay:',
        to_date: 'Den ngay:',
        filter: 'Loc',
        all: 'Tat Ca',
        all_status: 'Tat ca trang thai',
        all_levels: 'Tat ca cap',
        custom_range: 'Tuy chinh',
        today: 'Hom nay',
        three_months: '3 thang',
        this_year: 'Nam nay',
        select_filter_hint: 'Chon ngay va nhan Loc de xem hoa hong',
        click_filter_hint: 'Nhan Loc de xem danh sach',
        
        // Commission
        no_commissions: 'Chua co hoa hong nao',
        no_commissions_period: 'Khong co hoa hong trong khoang thoi gian nay',
        total_commission: 'Tong Hoa Hong',
        level: 'Cap',
        level_0_self: 'Level 0 (Ban Than)',
        rate: 'Ty Le',
        amount: 'So Tien',
        from_ctv: 'Tu CTV',
        customer: 'Khach Hang',
        service: 'Dich Vu',
        date: 'Ngay',
        transactions: 'Giao Dich',
        revenue: 'Doanh Thu',
        
        // Network
        your_network: 'Mang Luoi Cua Ban',
        direct_list: 'Danh Sach CTV Truc Tiep',
        no_referrals: 'Ban chua gioi thieu ai',
        no_customers: 'Chua co khach hang nao',
        stats_by_level: 'Thong Ke Theo Cap',
        count: 'So Luong',
        total_members: 'TONG THANH VIEN',
        levels_deep: 'SO CAP',
        direct_recruits: 'GIOI THIEU TRUC TIEP',
        expand_all: 'Mo Rong',
        collapse_all: 'Thu Gon',
        ctv_code_col: 'Ma CTV',
        name_col: 'Ten',
        email_col: 'Email',
        phone_col: 'SDT',
        rank_col: 'Cap Bac',
        
        // Settings / Change Password
        change_password: 'Doi Mat Khau',
        current_password: 'Mat khau hien tai',
        new_password: 'Mat khau moi',
        confirm_password: 'Xac nhan mat khau moi',
        change_password_btn: 'Doi Mat Khau',
        password_changed: 'Doi mat khau thanh cong!',
        password_mismatch: 'Mat khau moi khong khop',
        password_too_short: 'Mat khau moi phai co it nhat 6 ky tu',
        
        // Phone Check
        phone_check_title: 'Kiem Tra Trung Lap So Dien Thoai',
        phone_check_placeholder: 'Nhap so dien thoai...',
        check: 'Kiem Tra',
        checking: 'Dang kiem tra...',
        duplicate: 'TRUNG',
        not_duplicate: 'KHONG TRUNG',
        phone_short: 'So dien thoai qua ngan',
        
        // Status
        completed: 'Da den lam',
        deposited: 'Da coc',
        cancelled: 'Huy lich',
        pending: 'Cho xac nhan',
        da_coc: 'Da coc',
        chua_coc: 'Chua coc',
        
        // Loading
        loading: 'Dang tai...',
        no_data: 'Chua co du lieu',
        
        // Service Card Labels
        tong_tien: 'Tong tien:',
        tien_coc: 'Tien coc:',
        phai_dong: 'Phai dong:',
        ngay_nhap_don: 'Ngay nhap don:',
        ngay_hen_lam: 'Ngay hen lam:',
        
        // Client Card Labels
        co_so: 'Co so',
        first_visit: 'Lan dau',
        dich_vu: 'Dich Vu',
        services_title: 'Dich Vu',
        unknown_service: 'Dich vu khong xac dinh'
    },
    en: {
        // Login
        login_subtitle: 'Login to view commissions and network',
        ctv_code: 'CTV Code',
        password: 'Password',
        enter_password: 'Enter password',
        remember_me: 'Remember me',
        login: 'Login',
        back_home: 'Back to Home',
        login_success: 'Login successful!',
        login_failed: 'Login failed',
        logging_in: 'Logging in...',
        
        // Dashboard
        overview: 'Overview',
        earnings: 'Earnings',
        network: 'Network',
        settings: 'Settings',
        logout: 'Logout',
        language: 'Language',
        choose_language: 'Choose Language',
        
        // Stats
        total_earnings: 'Total Earnings',
        this_month: 'This Month',
        network_size: 'Network Size',
        direct_referrals: 'Direct Referrals',
        direct_level1: 'Direct (Level 1)',
        services_this_month: 'Services This Month',
        recent_commissions: 'Recent Commissions',
        
        // Filters
        from_date: 'From:',
        to_date: 'To:',
        filter: 'Filter',
        all: 'All',
        all_status: 'All Status',
        all_levels: 'All Levels',
        custom_range: 'Custom',
        today: 'Today',
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
        new_password: 'New Password',
        confirm_password: 'Confirm New Password',
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
        unknown_service: 'Unknown Service'
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
    
    // Update language options in popup
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.lang === lang);
    });
    
    // Update current language labels (sidebar and login page)
    const langLabel = document.getElementById('currentLangLabel');
    if (langLabel) {
        langLabel.textContent = lang.toUpperCase();
    }
    const loginLangLabel = document.getElementById('loginLangLabel');
    if (loginLangLabel) {
        loginLangLabel.textContent = lang.toUpperCase();
    }
    
    // Close any open popups
    const loginToggle = document.getElementById('loginLangToggle');
    if (loginToggle) loginToggle.classList.remove('active');
    
    // Re-render dynamic content based on active page
    const activePage = document.querySelector('.page-section.active');
    if (activePage) {
        const pageId = activePage.id;
        if (pageId === 'page-dashboard' && typeof loadRecentCommissions === 'function') {
            loadRecentCommissions();
        } else if (pageId === 'page-earnings' && typeof filterCommissions === 'function') {
            setEarningsDefaultDateFilter();
            filterCommissions();
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
    // Close the popup
    document.getElementById('langSwitcher').classList.remove('active');
}

// Get current language
function getCurrentLang() {
    return currentLang;
}

