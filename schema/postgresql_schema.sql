-- ══════════════════════════════════════════════════════════════════════════════
-- CTV System PostgreSQL Schema
-- Optimized for large-scale data management
-- Created: January 2, 2026
-- ══════════════════════════════════════════════════════════════════════════════

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS commissions CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS khach_hang CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS ctv CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS hoa_hong_config CASCADE;
DROP TABLE IF EXISTS commission_settings CASCADE;

-- ══════════════════════════════════════════════════════════════════════════════
-- 1. ADMINS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for login lookups
CREATE INDEX idx_admins_username ON admins(username);

-- Insert default admin account (password: admin123)
-- Hash format: salt:sha256hash
INSERT INTO admins (username, password_hash, name) VALUES 
('admin', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Administrator');

-- ══════════════════════════════════════════════════════════════════════════════
-- 2. CTV (Collaborator) TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE ctv (
    ma_ctv VARCHAR(20) PRIMARY KEY,
    ten VARCHAR(100) NOT NULL,
    sdt VARCHAR(15),
    email VARCHAR(100),
    nguoi_gioi_thieu VARCHAR(20),
    cap_bac VARCHAR(50) DEFAULT 'Bronze',
    password_hash VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nguoi_gioi_thieu) REFERENCES ctv(ma_ctv) ON DELETE SET NULL
);

-- Indexes for CTV table
CREATE INDEX idx_ctv_parent ON ctv(nguoi_gioi_thieu, ma_ctv);
CREATE INDEX idx_ctv_email ON ctv(email);
CREATE INDEX idx_ctv_sdt ON ctv(sdt);
CREATE INDEX idx_ctv_active ON ctv(is_active);
CREATE INDEX idx_ctv_created ON ctv(created_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- 3. SESSIONS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_type VARCHAR(10) NOT NULL CHECK (user_type IN ('admin', 'ctv')),
    user_id VARCHAR(50) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for session validation
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_sessions_user ON sessions(user_type, user_id);

-- ══════════════════════════════════════════════════════════════════════════════
-- 4. CUSTOMERS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_email ON customers(email);

-- ══════════════════════════════════════════════════════════════════════════════
-- 5. KHACH_HANG (Customer Transactions) TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE khach_hang (
    id SERIAL PRIMARY KEY,
    ngay_nhap_don DATE,
    ten_khach VARCHAR(100),
    sdt VARCHAR(15),
    co_so VARCHAR(100),
    ngay_hen_lam DATE,
    gio VARCHAR(20),
    dich_vu VARCHAR(500),
    tong_tien DECIMAL(15,0) DEFAULT 0,
    tien_coc DECIMAL(15,0) DEFAULT 0,
    phai_dong DECIMAL(15,0) DEFAULT 0,
    nguoi_chot VARCHAR(50),  -- Closer/Referrer - links to ctv.ma_ctv (used by all tabs)
    ghi_chu TEXT,
    trang_thai VARCHAR(50) DEFAULT 'Cho xac nhan',
    source VARCHAR(20),  -- Data source: 'tham_my', 'gioi_thieu', 'nha_khoa'
    khu_vuc VARCHAR(50),  -- Customer region (for Khách giới thiệu)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Composite indexes for khach_hang (optimized for common queries)
CREATE INDEX idx_khach_hang_sdt ON khach_hang(sdt);
CREATE INDEX idx_khach_hang_sdt_status ON khach_hang(sdt, trang_thai);
CREATE INDEX idx_khach_hang_date_status ON khach_hang(ngay_hen_lam, trang_thai);
CREATE INDEX idx_khach_hang_chot_date ON khach_hang(nguoi_chot, ngay_hen_lam);
CREATE INDEX idx_khach_hang_chot_status_date ON khach_hang(nguoi_chot, trang_thai, ngay_hen_lam);
CREATE INDEX idx_khach_hang_nhap_don ON khach_hang(ngay_nhap_don);

-- Partial index for active customers only (reduces index size)
CREATE INDEX idx_khach_hang_active ON khach_hang(sdt, trang_thai) 
WHERE trang_thai IN ('Da den lam', 'Da coc', 'Cho xac nhan', 'Đã đến làm', 'Đã cọc', 'Chờ xác nhận');

-- ══════════════════════════════════════════════════════════════════════════════
-- 6. SERVICES TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    service_name VARCHAR(200),
    date_entered DATE,
    date_scheduled DATE,
    amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Cho xu ly',
    ctv_code VARCHAR(20),
    nguoi_chot VARCHAR(20),
    tong_tien DECIMAL(15,0) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ctv_code) REFERENCES ctv(ma_ctv) ON DELETE SET NULL,
    FOREIGN KEY (nguoi_chot) REFERENCES ctv(ma_ctv) ON DELETE SET NULL
);

CREATE INDEX idx_services_customer ON services(customer_id);
CREATE INDEX idx_services_ctv ON services(ctv_code);
CREATE INDEX idx_services_nguoi_chot ON services(nguoi_chot);
CREATE INDEX idx_services_date ON services(date_entered);

-- ══════════════════════════════════════════════════════════════════════════════
-- 7. HOA_HONG_CONFIG (Commission Config) TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE hoa_hong_config (
    level INTEGER PRIMARY KEY,
    percent DECIMAL(5,3) NOT NULL,
    description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default commission rates
INSERT INTO hoa_hong_config (level, percent, description) VALUES 
(0, 25.0, 'Doanh so ban than (Level 0)'),
(1, 5.0, 'Doanh so Level 1 (truc tiep gioi thieu)'),
(2, 2.5, 'Doanh so Level 2'),
(3, 1.25, 'Doanh so Level 3'),
(4, 0.625, 'Doanh so Level 4 (cap cuoi)');

-- ══════════════════════════════════════════════════════════════════════════════
-- 8. COMMISSION_SETTINGS TABLE (Alternative config table)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE commission_settings (
    level INTEGER PRIMARY KEY,
    rate DECIMAL(5,4) NOT NULL,
    description VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50)
);

-- Insert default commission settings
INSERT INTO commission_settings (level, rate, description) VALUES 
(0, 0.25, 'Doanh so ban than (Level 0)'),
(1, 0.05, 'Doanh so Level 1'),
(2, 0.025, 'Doanh so Level 2'),
(3, 0.0125, 'Doanh so Level 3'),
(4, 0.00625, 'Doanh so Level 4');

-- ══════════════════════════════════════════════════════════════════════════════
-- 9. COMMISSIONS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE commissions (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER,
    ctv_code VARCHAR(20) NOT NULL,
    level INTEGER NOT NULL,
    commission_rate DECIMAL(5,4) NOT NULL,
    transaction_amount DECIMAL(15,2) NOT NULL,
    commission_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ctv_code) REFERENCES ctv(ma_ctv) ON DELETE CASCADE
);

-- Indexes for commission queries
CREATE INDEX idx_commissions_ctv ON commissions(ctv_code);
CREATE INDEX idx_commissions_ctv_date ON commissions(ctv_code, created_at);
CREATE INDEX idx_commissions_transaction ON commissions(transaction_id, level);
CREATE INDEX idx_commissions_created ON commissions(created_at);

-- ══════════════════════════════════════════════════════════════════════════════
-- 9.1 COMMISSION_CACHE TABLE (for tracking last processed IDs)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS commission_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(50) UNIQUE NOT NULL,
    last_kh_max_id INTEGER DEFAULT 0,
    last_svc_max_id INTEGER DEFAULT 0,
    total_kh_processed INTEGER DEFAULT 0,
    total_svc_processed INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default cache entry
INSERT INTO commission_cache (cache_key, last_kh_max_id, last_svc_max_id) 
VALUES ('global', 0, 0) 
ON CONFLICT (cache_key) DO NOTHING;

-- ══════════════════════════════════════════════════════════════════════════════
-- 10. ACTIVITY_LOGS TABLE
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_type VARCHAR(10),
    user_id VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for activity logs
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX idx_activity_logs_event ON activity_logs(event_type);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_type, user_id);
CREATE INDEX idx_activity_logs_ip ON activity_logs(ip_address);

-- Partial index for login events (commonly queried)
CREATE INDEX idx_activity_logs_logins ON activity_logs(timestamp, user_id) 
WHERE event_type IN ('login_success', 'login_failed');

-- ══════════════════════════════════════════════════════════════════════════════
-- UTILITY FUNCTIONS
-- ══════════════════════════════════════════════════════════════════════════════

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_ctv_updated_at BEFORE UPDATE ON ctv
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_khach_hang_updated_at BEFORE UPDATE ON khach_hang
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hoa_hong_config_updated_at BEFORE UPDATE ON hoa_hong_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ══════════════════════════════════════════════════════════════════════════════
-- RECURSIVE CTE FUNCTION FOR MLM HIERARCHY
-- ══════════════════════════════════════════════════════════════════════════════

-- Function to get all descendants of a CTV
CREATE OR REPLACE FUNCTION get_ctv_descendants(root_code VARCHAR(20), max_level INTEGER DEFAULT 4)
RETURNS TABLE(ma_ctv VARCHAR(20), ten VARCHAR(100), level INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE hierarchy AS (
        -- Base case: the root CTV
        SELECT c.ma_ctv, c.ten, 0 as level
        FROM ctv c
        WHERE c.ma_ctv = root_code
        
        UNION ALL
        
        -- Recursive case: children of current level
        SELECT c.ma_ctv, c.ten, h.level + 1
        FROM ctv c
        INNER JOIN hierarchy h ON c.nguoi_gioi_thieu = h.ma_ctv
        WHERE h.level < max_level
    )
    SELECT hierarchy.ma_ctv, hierarchy.ten, hierarchy.level
    FROM hierarchy
    ORDER BY hierarchy.level, hierarchy.ma_ctv;
END;
$$ LANGUAGE plpgsql;

-- Function to get ancestors of a CTV (upline)
CREATE OR REPLACE FUNCTION get_ctv_ancestors(child_code VARCHAR(20), max_level INTEGER DEFAULT 4)
RETURNS TABLE(ma_ctv VARCHAR(20), ten VARCHAR(100), level INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE ancestors AS (
        -- Base case: the child CTV
        SELECT c.ma_ctv, c.ten, c.nguoi_gioi_thieu, 0 as level
        FROM ctv c
        WHERE c.ma_ctv = child_code
        
        UNION ALL
        
        -- Recursive case: parent of current level
        SELECT c.ma_ctv, c.ten, c.nguoi_gioi_thieu, a.level + 1
        FROM ctv c
        INNER JOIN ancestors a ON c.ma_ctv = a.nguoi_gioi_thieu
        WHERE a.level < max_level AND a.nguoi_gioi_thieu IS NOT NULL
    )
    SELECT ancestors.ma_ctv, ancestors.ten, ancestors.level
    FROM ancestors
    ORDER BY ancestors.level;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate level between two CTVs
CREATE OR REPLACE FUNCTION calculate_ctv_level(descendant_code VARCHAR(20), ancestor_code VARCHAR(20))
RETURNS INTEGER AS $$
DECLARE
    result_level INTEGER;
BEGIN
    WITH RECURSIVE chain AS (
        SELECT ma_ctv, nguoi_gioi_thieu, 0 as level
        FROM ctv
        WHERE ma_ctv = descendant_code
        
        UNION ALL
        
        SELECT c.ma_ctv, c.nguoi_gioi_thieu, chain.level + 1
        FROM ctv c
        INNER JOIN chain ON c.ma_ctv = chain.nguoi_gioi_thieu
        WHERE chain.level < 10  -- Safety limit
    )
    SELECT level INTO result_level
    FROM chain
    WHERE ma_ctv = ancestor_code;
    
    RETURN result_level;
END;
$$ LANGUAGE plpgsql;

-- ══════════════════════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS (adjust as needed for your setup)
-- ══════════════════════════════════════════════════════════════════════════════
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_user;

-- ══════════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ══════════════════════════════════════════════════════════════════════════════
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';

