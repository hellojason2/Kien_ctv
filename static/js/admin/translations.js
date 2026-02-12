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
        administration: 'Quản Trị',
        ctv_management: 'Quản Lý CTV',
        ctv_list: 'Danh Sách CTV',
        ctv_registrations: 'Đơn Đăng Ký',
        registrations: 'Đăng Ký Mới',
        hierarchy: 'Cây Hệ Thống',
        menu: 'Menu',
        admin_brand: 'CTV Admin',
        financial: 'Tài Chính',
        commissions: 'Hoa Hồng',
        clients: 'Khách Hàng',
        configuration: 'Cấu Hình',
        settings: 'Cài Đặt',
        signup_terms: 'Điều Khoản',
        activity_logs: 'Nhật Ký',
        logout: 'Đăng Xuất',
        toggle_sidebar: 'Thu/Mở Thanh Bên',

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
        // Dashboard - System Status & Buttons
        check_duplicates: 'Quét Trùng Lặp',
        variables_ok: 'Biến: OK',
        checking_vars: 'Đang kiểm tra biến...',
        synced: 'Đã đồng bộ',
        syncing: 'Đang đồng bộ...',
        click_to_clear: 'Nhấn để xóa thông báo',
        tm_tooltip: 'Thẩm Mỹ (Beauty) - DB / Sheet',
        nk_tooltip: 'Nha Khoa (Dental) - DB / Sheet',
        gt_tooltip: 'Giới Thiệu (Referral) - DB / Sheet',

        // Date Filters
        today: 'Hôm Nay',
        three_days: '3 Ngày Qua',
        week: 'Tuần Này',
        this_month: 'Tháng Này',
        last_month: 'Tháng Trước',
        three_months: '3 Tháng Qua',
        this_year: 'Năm Nay',
        custom_range: 'Tùy Chỉnh',
        quick_filters: 'Lọc Nhanh',
        from_date: 'Từ:',
        to_date: 'Đến:',
        filter: 'Lọc',

        // Progress Modals & Cleanup
        cleanup_progress: 'Đang Dọn Dẹp',
        cleanup_subtitle: 'Đang quét dữ liệu trùng lặp dựa trên Ngày, Giờ, Tên & Dịch vụ...',
        starting: 'Đang khởi động...',
        cleanup_complete: 'Dọn Dẹp Hoàn Tất!',
        deleted_rows: 'Hàng đã xóa:',
        hard_reset_progress: 'Đang Đặt Lại Hệ Thống',
        hard_reset_subtitle: 'Vui lòng đợi trong khi chúng tôi đồng bộ lại dữ liệu...',
        step_read: 'Đang đọc cơ sở dữ liệu',
        step_clearing: 'Đang xóa dữ liệu cũ',
        step_beauty: 'Đang nhập dữ liệu Thẩm Mỹ',
        step_dental: 'Đang nhập dữ liệu Nha Khoa',
        step_referral: 'Đang nhập dữ liệu Giới Thiệu',
        step_commission: 'Đang tính toán hoa hồng',
        reset_complete: 'Đặt Lại Hoàn Tất!',
        sync_progress: 'Đang Đồng Bộ',
        sync_subtitle: 'Đang kéo dữ liệu mới từ Google Sheets...',
        close: 'Đóng',

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

        // CTV Registrations
        pending: 'Chờ Duyệt',
        approved: 'Đã Duyệt',
        rejected: 'Đã Từ Chối',
        all: 'Tất Cả',
        id: 'ID',
        phone_number: 'Số Điện Thoại',
        submitted_date: 'Ngày Gửi',
        approve: 'Duyệt',
        reject: 'Từ Chối',
        view: 'Xem',
        no_registrations: 'Không có đơn đăng ký',
        approve_registration: 'Duyệt Đơn Đăng Ký',
        reject_registration: 'Từ Chối Đơn Đăng Ký',
        registration_details: 'Chi Tiết Đơn Đăng Ký',
        ctv_code_hint: 'Nhập mã CTV duy nhất hoặc nhấn Tạo',
        ctv_code_auto_hint: 'Mã CTV sẽ được đặt thành số điện thoại tự động',
        generate: 'Tạo',
        rejection_reason: 'Lý Do Từ Chối',
        rejection_reason_placeholder: 'Nhập lý do từ chối (tùy chọn)',
        address: 'Địa Chỉ',
        dob: 'Ngày Sinh',
        id_number: 'Số CCCD/CMND',
        reviewed_date: 'Ngày Duyệt',
        reviewed_by: 'Người Duyệt',
        notes: 'Ghi Chú',
        close: 'Đóng',

        // Commission Settings
        commission_settings: 'Cài Đặt Hoa Hồng',
        commission_rates: 'Tỷ Lệ Hoa Hồng Theo Cấp',
        save_changes: 'Lưu Thay Đổi',
        settings_saved: 'Đã lưu cài đặt!',

        // Signup Terms
        signup_terms_title: 'Điều Khoản Đăng Ký',
        version_history: 'Lịch Sử Phiên Bản',
        save_terms: 'Lưu Điều Khoản',
        edit_terms: 'Chỉnh Sửa Điều Khoản',
        terms_title_label: 'Tiêu Đề Điều Khoản',
        terms_content_label: 'Nội Dung Điều Khoản (HTML)',
        preview_label: 'Xem Trước',
        version_history_title: 'Lịch Sử Phiên Bản Điều Khoản',
        close: 'Đóng',

        // Sync Steps & Logs
        log_read_db: 'Đang đọc số lượng trong cơ sở dữ liệu...',
        log_connect_sheet: 'Đang kết nối Google Sheets...',
        log_read_rows: 'Đang đọc tất cả hàng từ sheet...',
        log_check_dupes: 'Đang so sánh với DB (kiểm tra trùng lặp)...',
        tm_success: 'Thẩm Mỹ: +{inserted} mới, {skipped} bỏ qua',
        tm_fail: 'Thẩm Mỹ thất bại: {error}',
        log_sync_nk: 'Đang đồng bộ Nha Khoa (Dental)...',
        nk_success: 'Nha Khoa: +{inserted} mới, {skipped} bỏ qua',
        nk_fail: 'Nha Khoa thất bại: {error}',
        log_sync_gt: 'Đang đồng bộ Giới Thiệu (Referral)...',
        gt_success: 'Giới Thiệu: +{inserted} mới, {skipped} bỏ qua',
        gt_fail: 'Giới Thiệu thất bại: {error}',
        new: 'mới',
        skipped: 'bỏ qua',
        step_calc_comm: 'Đang tính toán hoa hồng',
        log_recalc_comm: 'Đang tính lại các mức hoa hồng...',
        comm_updated: 'Hoa hồng đã được cập nhật',
        step_no_records: 'Không có dữ liệu mới, bỏ qua',
        log_no_records: 'Không tìm thấy bản ghi mới - bỏ qua tính toán hoa hồng',

        // Hierarchy
        hierarchy_tree: 'Cây Cấp Bậc',
        select_root: 'Chọn CTV Gốc',
        select_ctv: 'Chọn CTV',
        select_ctv_view: 'Chọn CTV để xem cấp bậc',
        type_to_search: 'Gõ để tìm CTV...',
        no_ctv_found: 'Không tìm thấy CTV',
        total_members: 'Tổng Thành Viên',
        total_downline: 'Đội Nhóm',
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
        total_revenue_for_today: 'Doanh số cá nhân Hôm Nay',
        total_revenue_for_week: 'Doanh số cá nhân Tuần Này',
        total_revenue_for_month: 'Doanh số cá nhân Tháng Này',
        total_revenue_for_period: 'Doanh số cá nhân',
        total_revenue_for_custom: 'Doanh số cá nhân',
        apply: 'Áp Dụng',
        please_select_both_dates: 'Vui lòng chọn cả ngày bắt đầu và ngày kết thúc',
        date_from_must_be_before_date_to: 'Ngày bắt đầu phải trước ngày kết thúc',

        // Status
        da_coc: 'Đã cọc',
        chua_coc: 'Chưa cọc',
        cskh_potential: 'CSKH Tiềm Năng (360+ ngày)',
        all_statuses: 'Tất cả trạng thái',

        // Modal
        add_new_ctv: 'Thêm CTV Mới',
        edit_ctv: 'Chỉnh Sửa CTV',
        ctv_code: 'Mã CTV',
        ctv_code_placeholder: 'VD: CTV012',
        full_name: 'Họ tên đầy đủ',
        enter_name: 'Vui lòng nhập tên',
        referrer_label: 'Người Giới Thiệu',
        none_root: 'Không (CTV Gốc)',
        level_placeholder: 'Chọn hoặc nhập cấp bậc',
        cancel: 'Hủy',
        create_ctv: 'Tạo CTV',
        change_password: 'Đổi Mật Khẩu',
        new_password: 'Mật Khẩu Mới',
        save: 'Lưu',
        password_changed: 'Mật khẩu đã được thay đổi thành công',
        ctv_updated: 'CTV đã được cập nhật thành công',
        enter_password: 'Vui lòng nhập mật khẩu',

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
        unknown_service: 'Dịch vụ không xác định',
        vietnamese: 'Tiếng Việt',
        english: 'English'
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
        administration: 'Administration',
        ctv_management: 'CTV Management',
        ctv_list: 'CTV List',
        ctv_registrations: 'Registrations',
        registrations: 'New Registrations',
        hierarchy: 'System Tree',
        menu: 'Menu',
        admin_brand: 'CTV Admin',
        financial: 'Financial',
        commissions: 'Commissions',
        clients: 'Clients',
        configuration: 'Configuration',
        settings: 'Settings',
        activity_logs: 'Activity Logs',
        logout: 'Logout',
        toggle_sidebar: 'Toggle Sidebar',

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
        // Dashboard - System Status & Buttons
        check_duplicates: 'Check Duplicates',
        variables_ok: 'Variables: OK',
        checking_vars: 'Checking Vars...',
        synced: 'Synced',
        syncing: 'Syncing...',
        click_to_clear: 'Click to clear notifications',
        tm_tooltip: 'Thẩm Mỹ (Beauty) - DB / Sheet',
        nk_tooltip: 'Nha Khoa (Dental) - DB / Sheet',
        gt_tooltip: 'Giới Thiệu (Referral) - DB / Sheet',

        // Date Filters
        today: 'Today',
        three_days: '3 Days',
        week: 'This Week',
        this_month: 'This Month',
        last_month: 'Last Month',
        three_months: '3 Months',
        this_year: 'This Year',
        custom_range: 'Custom',
        quick_filters: 'Quick Filters',
        from_date: 'From:',
        to_date: 'To:',
        filter: 'Filter',

        // Progress Modals & Cleanup
        cleanup_progress: 'Cleanup In Progress',
        cleanup_subtitle: 'Scanning for duplicates based on Date, Time, Name & Service...',
        starting: 'Starting...',
        cleanup_complete: 'Cleanup Complete!',
        deleted_rows: 'Deleted Rows:',
        hard_reset_progress: 'Hard Reset In Progress',
        hard_reset_subtitle: 'Please wait while we sync your data...',
        step_read: 'Reading Database',
        step_clearing: 'Clearing Database',
        step_beauty: 'Importing Beauty Data',
        step_dental: 'Importing Dental Data',
        step_referral: 'Importing Referral Data',
        step_commission: 'Calculating Commissions',
        reset_complete: 'Reset Complete!',
        sync_progress: 'Sync In Progress',
        sync_subtitle: 'Pulling new records from Google Sheets...',
        close: 'Close',

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

        // CTV Registrations
        pending: 'Pending',
        approved: 'Approved',
        rejected: 'Rejected',
        all: 'All',
        id: 'ID',
        phone_number: 'Phone Number',
        submitted_date: 'Submitted',
        approve: 'Approve',
        reject: 'Reject',
        view: 'View',
        no_registrations: 'No registrations found',
        approve_registration: 'Approve Registration',
        reject_registration: 'Reject Registration',
        registration_details: 'Registration Details',
        ctv_code_hint: 'Enter a unique CTV code or click Generate',
        ctv_code_auto_hint: 'CTV code will be set to the phone number automatically',
        generate: 'Generate',
        rejection_reason: 'Rejection Reason',
        rejection_reason_placeholder: 'Enter reason for rejection (optional)',
        address: 'Address',
        dob: 'Date of Birth',
        id_number: 'ID Number',
        reviewed_date: 'Reviewed Date',
        reviewed_by: 'Reviewed By',
        notes: 'Notes',
        close: 'Close',

        // Commission Settings
        commission_settings: 'Commission Settings',
        commission_rates: 'Commission Rates by Level',
        save_changes: 'Save Changes',
        settings_saved: 'Settings saved!',

        // Signup Terms
        signup_terms: 'Terms of Service',
        signup_terms_title: 'Signup Agreement Terms',
        version_history: 'Version History',
        save_terms: 'Save Terms',
        edit_terms: 'Edit Agreement Terms',
        terms_title_label: 'Terms Title',
        terms_content_label: 'Terms Content (HTML)',
        preview_label: 'Live Preview',
        version_history_title: 'Terms Version History',
        close: 'Close',

        // Hierarchy
        hierarchy_tree: 'Hierarchy Tree',
        select_root: 'Select Root CTV',

        // Sync Steps & Logs
        log_read_db: 'Reading database counts...',
        log_connect_sheet: 'Connecting to Google Sheets...',
        log_read_rows: 'Reading all rows from sheet...',
        log_check_dupes: 'Comparing with DB (checking duplicates)...',
        tm_success: 'Beauty: +{inserted} new, {skipped} skipped',
        tm_fail: 'Beauty failed: {error}',
        log_sync_nk: 'Syncing Dental...',
        nk_success: 'Dental: +{inserted} new, {skipped} skipped',
        nk_fail: 'Dental failed: {error}',
        log_sync_gt: 'Syncing Referral...',
        gt_success: 'Referral: +{inserted} new, {skipped} skipped',
        gt_fail: 'Referral failed: {error}',
        new: 'new',
        skipped: 'skipped',
        step_calc_comm: 'Calculating commissions',
        log_recalc_comm: 'Recalculating commission levels...',
        comm_updated: 'Commissions updated',
        step_no_records: 'No new records, skipping',
        log_no_records: 'No new records found - skipping commission calculation',
        select_ctv: 'Select CTV',
        select_ctv_view: 'Select a CTV to view hierarchy',
        type_to_search: 'Type to search CTV...',
        no_ctv_found: 'No CTV found',
        total_members: 'Total Members',
        total_downline: 'Total Downline',
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
        total_revenue_for_today: 'Personal Sales for Today',
        total_revenue_for_week: 'Personal Sales for This Week',
        total_revenue_for_month: 'Personal Sales for This Month',
        total_revenue_for_period: 'Personal Sales',
        total_revenue_for_custom: 'Personal Sales',
        apply: 'Apply',
        please_select_both_dates: 'Please select both start and end dates',
        date_from_must_be_before_date_to: 'Start date must be before end date',

        // Modal
        add_new_ctv: 'Add New CTV',
        edit_ctv: 'Edit CTV',
        ctv_code: 'CTV Code',
        ctv_code_placeholder: 'e.g., CTV012',
        full_name: 'Full name',
        enter_name: 'Please enter a name',
        referrer_label: 'Referrer',
        none_root: 'None (Root CTV)',
        level_placeholder: 'Select or type level',
        cancel: 'Cancel',
        create_ctv: 'Create CTV',
        change_password: 'Change Password',
        new_password: 'New Password',
        save: 'Save',
        password_changed: 'Password changed successfully',
        ctv_updated: 'CTV updated successfully',
        enter_password: 'Please enter a password',

        // Language
        language: 'Language',
        choose_language: 'Choose Language',

        // Status
        da_coc: 'Deposited',
        chua_coc: 'Not Deposited',
        cskh_potential: 'CSKH Potential (360+ days)',
        all_statuses: 'All Statuses',

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
        unknown_service: 'Unknown Service',
        vietnamese: 'Vietnamese',
        english: 'English'
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
    const switcher = document.getElementById('adminLangSwitcher');
    if (switcher) {
        switcher.classList.toggle('active');
    }
}

/**
 * Select language from popup and close (Legacy/Generic)
 * @param {string} lang - Language code (vi/en)
 */
function selectLanguage(lang) {
    selectAdminLanguage(lang);
}

/**
 * Select language from popup and close (Admin Specific)
 * @param {string} lang - Language code (vi/en)
 */
function selectAdminLanguage(lang) {
    setLanguage(lang);

    // Close the desktop popup
    const switcher = document.getElementById('adminLangSwitcher');
    if (switcher) {
        switcher.classList.remove('active');
    }

    // Close the mobile popup (Toggle on Container)
    const mobileToggle = document.getElementById('adminMobileLangToggle');
    if (mobileToggle) {
        const mobileContainer = mobileToggle.closest('.mobile-menu-lang');
        if (mobileContainer) {
            mobileContainer.classList.remove('active');
        }
    }

    // Close the Header popup
    const headerSwitcher = document.getElementById('adminHeaderLangSwitcher');
    if (headerSwitcher) {
        headerSwitcher.classList.remove('active');
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

    // Update popup option states (both desktop and mobile)
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.lang === lang);
    });

    // Update current language label (Desktop)
    const langLabel = document.getElementById('adminCurrentLangLabel');
    if (langLabel) {
        langLabel.textContent = lang.toUpperCase();
    }

    // Update current language label (Mobile)
    const mobileLangLabel = document.getElementById('adminMobileCurrentLangLabel');
    if (mobileLangLabel) {
        mobileLangLabel.textContent = lang.toUpperCase();
    }

    // Update current language label (Header)
    const headerLangLabel = document.getElementById('headerCurrentLangLabel');
    if (headerLangLabel) {
        headerLangLabel.textContent = lang.toUpperCase();
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

    // Update tooltips (data-tooltip attribute)
    document.querySelectorAll('[data-i18n-tooltip]').forEach(el => {
        const key = el.getAttribute('data-i18n-tooltip');
        if (translations[currentLang][key]) {
            el.setAttribute('data-tooltip', translations[currentLang][key]);

            // Also update the child .sidebar-tooltip element if it exists
            const tooltipEl = el.querySelector('.sidebar-tooltip');
            if (tooltipEl) {
                tooltipEl.textContent = translations[currentLang][key];
            }
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

