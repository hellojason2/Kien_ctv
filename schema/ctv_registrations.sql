-- CTV Registrations Table
-- Stores pending CTV registration requests for admin approval

CREATE TABLE IF NOT EXISTS ctv_registrations (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    dob DATE,
    id_number VARCHAR(50),
    referrer_code VARCHAR(50),
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(50),
    UNIQUE(phone, status) -- Prevent duplicate pending registrations
);

CREATE INDEX IF NOT EXISTS idx_ctv_registrations_status ON ctv_registrations(status);
CREATE INDEX IF NOT EXISTS idx_ctv_registrations_phone ON ctv_registrations(phone);
CREATE INDEX IF NOT EXISTS idx_ctv_registrations_created_at ON ctv_registrations(created_at DESC);

COMMENT ON TABLE ctv_registrations IS 'Stores CTV signup requests awaiting admin approval';
COMMENT ON COLUMN ctv_registrations.status IS 'Registration status: pending (awaiting review), approved (accepted), rejected (denied)';
COMMENT ON COLUMN ctv_registrations.referrer_code IS 'CTV code of the person who referred this applicant';
