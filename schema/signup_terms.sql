-- ══════════════════════════════════════════════════════════════════════════════
-- CTV Signup Terms Table
-- Stores editable signup agreement terms and conditions
-- Created: January 14, 2026
-- ══════════════════════════════════════════════════════════════════════════════

DROP TABLE IF EXISTS signup_terms CASCADE;

CREATE TABLE signup_terms (
    id SERIAL PRIMARY KEY,
    language VARCHAR(5) NOT NULL DEFAULT 'vi',  -- 'vi' or 'en'
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50),
    UNIQUE(language, version)
);

-- Index for active terms lookup
CREATE INDEX idx_signup_terms_active ON signup_terms(language, is_active);
CREATE INDEX idx_signup_terms_version ON signup_terms(language, version);

-- Insert default Vietnamese terms
INSERT INTO signup_terms (language, title, content, is_active, version, updated_by) VALUES 
('vi', 'Điều Khoản và Điều Kiện Cộng Tác Viên', 
'<h3>ĐIỀU KHOẢN VÀ ĐIỀU KIỆN CỘNG TÁC VIÊN</h3>

<h4>1. GIỚI THIỆU</h4>
<p>Chào mừng bạn đến với chương trình Cộng Tác Viên (CTV) của chúng tôi. Bằng cách đăng ký làm CTV, bạn đồng ý tuân thủ các điều khoản và điều kiện sau đây.</p>

<h4>2. ĐIỀU KIỆN THAM GIA</h4>
<p>- Phải từ 18 tuổi trở lên</p>
<p>- Cung cấp thông tin chính xác và đầy đủ</p>
<p>- Có năng lực hành vi dân sự đầy đủ theo quy định của pháp luật</p>
<p>- Chấp nhận các điều khoản và điều kiện của chương trình</p>

<h4>3. QUYỀN VÀ NGHĨA VỤ CỦA CTV</h4>
<p><strong>Quyền lợi:</strong></p>
<p>- Được hưởng hoa hồng theo chính sách của công ty</p>
<p>- Được đào tạo và hỗ trợ về sản phẩm/dịch vụ</p>
<p>- Được sử dụng các tài liệu marketing của công ty</p>
<p>- Được xây dựng mạng lưới đội nhóm và hưởng hoa hồng cấp dưới</p>

<p><strong>Nghĩa vụ:</strong></p>
<p>- Tuân thủ các quy định và chính sách của công ty</p>
<p>- Cung cấp thông tin chính xác về sản phẩm/dịch vụ cho khách hàng</p>
<p>- Không được phát tán thông tin sai lệch hoặc gây ảnh hưởng xấu đến uy tín công ty</p>
<p>- Bảo mật thông tin khách hàng và công ty</p>
<p>- Chịu trách nhiệm về các hoạt động kinh doanh của mình</p>

<h4>4. CHÍNH SÁCH HOA HỒNG</h4>
<p>- Hoa hồng được tính dựa trên doanh số thực tế của khách hàng do CTV giới thiệu</p>
<p>- Thời gian thanh toán hoa hồng theo quy định của công ty</p>
<p>- Công ty có quyền điều chỉnh tỷ lệ hoa hồng theo từng thời kỳ</p>
<p>- CTV sẽ được thông báo trước về mọi thay đổi liên quan đến chính sách hoa hồng</p>

<h4>5. CHẤM DỨT HỢP TÁC</h4>
<p>Hợp tác có thể chấm dứt trong các trường hợp sau:</p>
<p>- Vi phạm các điều khoản và điều kiện</p>
<p>- Cung cấp thông tin sai lệch</p>
<p>- Có hành vi gian lận hoặc không trung thực</p>
<p>- Gây ảnh hưởng xấu đến uy tín công ty</p>
<p>- Theo yêu cầu của một trong hai bên với thông báo trước</p>

<h4>6. BẢO MẬT THÔNG TIN</h4>
<p>- CTV cam kết bảo mật thông tin khách hàng và công ty</p>
<p>- Không được chia sẻ thông tin khách hàng cho bên thứ ba</p>
<p>- Không được sử dụng thông tin cho mục đích cá nhân ngoài hợp tác với công ty</p>

<h4>7. TRÁCH NHIỆM PHÁP LÝ</h4>
<p>- CTV chịu trách nhiệm cá nhân về các hoạt động kinh doanh của mình</p>
<p>- Công ty không chịu trách nhiệm về các tranh chấp phát sinh giữa CTV và khách hàng</p>
<p>- Mọi tranh chấp sẽ được giải quyết theo pháp luật Việt Nam</p>

<h4>8. ĐIỀU KHOẢN CHUNG</h4>
<p>- Các điều khoản này có thể được cập nhật theo thời gian</p>
<p>- CTV sẽ được thông báo về mọi thay đổi quan trọng</p>
<p>- Việc tiếp tục tham gia sau khi có thay đổi đồng nghĩa với việc chấp nhận các điều khoản mới</p>

<h4>9. LIÊN HỆ</h4>
<p>Nếu có bất kỳ thắc mắc nào về các điều khoản này, vui lòng liên hệ với chúng tôi qua các kênh hỗ trợ chính thức.</p>',
TRUE, 1, 'system');

-- Insert default English terms
INSERT INTO signup_terms (language, title, content, is_active, version, updated_by) VALUES 
('en', 'Collaborator Terms and Conditions',
'<h3>COLLABORATOR TERMS AND CONDITIONS</h3>

<h4>1. INTRODUCTION</h4>
<p>Welcome to our Collaborator (CTV) program. By registering as a CTV, you agree to comply with the following terms and conditions.</p>

<h4>2. ELIGIBILITY REQUIREMENTS</h4>
<p>- Must be 18 years or older</p>
<p>- Provide accurate and complete information</p>
<p>- Have full civil capacity as prescribed by law</p>
<p>- Accept the terms and conditions of the program</p>

<h4>3. RIGHTS AND OBLIGATIONS OF CTV</h4>
<p><strong>Benefits:</strong></p>
<p>- Receive commissions according to company policy</p>
<p>- Receive training and support on products/services</p>
<p>- Use company marketing materials</p>
<p>- Build team networks and earn commissions from downlines</p>

<p><strong>Obligations:</strong></p>
<p>- Comply with company regulations and policies</p>
<p>- Provide accurate information about products/services to customers</p>
<p>- Not disseminate false information or damage company reputation</p>
<p>- Maintain confidentiality of customer and company information</p>
<p>- Take responsibility for their business activities</p>

<h4>4. COMMISSION POLICY</h4>
<p>- Commissions are calculated based on actual sales from customers referred by CTV</p>
<p>- Commission payment schedule follows company regulations</p>
<p>- The company reserves the right to adjust commission rates periodically</p>
<p>- CTVs will be notified in advance of any changes to commission policy</p>

<h4>5. TERMINATION OF COOPERATION</h4>
<p>Cooperation may be terminated in the following cases:</p>
<p>- Violation of terms and conditions</p>
<p>- Providing false information</p>
<p>- Fraudulent or dishonest behavior</p>
<p>- Damaging company reputation</p>
<p>- Upon request by either party with prior notice</p>

<h4>6. INFORMATION CONFIDENTIALITY</h4>
<p>- CTV commits to maintaining confidentiality of customer and company information</p>
<p>- Not share customer information with third parties</p>
<p>- Not use information for personal purposes outside cooperation with company</p>

<h4>7. LEGAL LIABILITY</h4>
<p>- CTV takes personal responsibility for their business activities</p>
<p>- The company is not liable for disputes between CTV and customers</p>
<p>- All disputes will be resolved according to Vietnamese law</p>

<h4>8. GENERAL TERMS</h4>
<p>- These terms may be updated from time to time</p>
<p>- CTVs will be notified of any significant changes</p>
<p>- Continued participation after changes indicates acceptance of new terms</p>

<h4>9. CONTACT</h4>
<p>If you have any questions about these terms, please contact us through official support channels.</p>',
TRUE, 1, 'system');

-- Trigger to update updated_at
CREATE TRIGGER update_signup_terms_updated_at 
BEFORE UPDATE ON signup_terms
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
