INSERT INTO ctv_registrations (full_name, phone, email, address, password_hash, status, created_at)
VALUES ('Test Nguyen', '0999888777', 'test@example.com', 'Test Address', '$2b$10$abcdefghijklmnopqrstuv', 'pending', NOW())
ON CONFLICT (phone, status) DO NOTHING;
