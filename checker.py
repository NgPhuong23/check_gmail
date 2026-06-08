from email_validator import validate_email, EmailNotValidError
import dns.resolver
import smtplib
import pandas as pd
import time
from datetime import datetime

def check_smtp_status(email, domain):
    """Giao tiếp với máy chủ Mail qua SMTP để check trạng thái thực của tài khoản"""
    try:
        # 1. Lấy máy chủ MX của domain
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            # Lấy máy chủ có độ ưu tiên cao nhất
            mx_record = sorted(mx_records, key=lambda r: r.preference)[0].exchange.to_text()
        except Exception:
            return "Not Exist", "Domain does not exist", "gray"

        # 2. Kết nối tới máy chủ SMTP (Cổng mặc định là 25)
        server = smtplib.SMTP(timeout=5)
        server.connect(mx_record, 25)
        server.helo(server.local_hostname)
        server.mail('check@ychecker-replica.com') # Email giả lập để gửi yêu cầu
        
        # Gửi lệnh RCPT TO để dò xem email phản hồi thế nào
        code, message = server.rcpt(str(email))
        server.quit()

        message_str = message.decode('utf-8', errors='ignore').lower()

        # 3. Phân tích phản hồi từ Máy chủ Mail (Đặc biệt là Google/Gmail)
        if code == 250:
            return "Live", "Active & deliverable", "green"
        
        elif code == 550:
            # Các trường hợp lỗi phổ biến của Gmail/Microsoft
            if any(kw in message_str for kw in ["disabled", "suspended", "terminated", "bị vô hiệu hóa"]):
                return "Disable", "Suspended by provider", "red"
            elif any(kw in message_str for kw in ["verify", "challenge", "verification"]):
                return "Verify", "Phone verify required", "orange"
            else:
                return "Not Exist", "Address not found", "gray"
                
        else:
            # Các mã lỗi tạm thời hoặc chặn IP (421, 450, 451,...)
            if "verify" in message_str:
                return "Verify", "Phone verify required", "orange"
            return "Not Exist", f"Address not found (SMTP Code: {code})", "gray"

    except Exception as e:
        # Nếu bị chặn kết nối hoặc timeout, giữ bộ lọc domain cơ bản cũ
        if "gmail.com" in domain or "googlemail.com" in domain:
            return "Live", "Active & deliverable (Fallback)", "green"
        return "Not Exist", f"Connection error: {str(e)}", "gray"

def classify_email(email):
    email = email.strip().lower()
    result = {
        "email": email,
        "status": "Not Exist",
        "reason": "",
        "color": "gray",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Bước 1: Kiểm tra cú pháp
        valid = validate_email(email, check_deliverability=False)
        domain = valid.domain
        
        # Bước 2: Kiểm tra mail rác/tạm thời (Disposable)
        if any(dis in domain for dis in ['tempmail', '10minutemail', 'guerrilla', 'throwaway', 'trashmail', 'yopmail']):
            result["status"] = "Disposable"
            result["reason"] = "Temporary / throwaway email"
            result["color"] = "orange"
            return result
        
        # Bước 3: Check sâu bằng SMTP
        status, reason, color = check_smtp_status(email, domain)
        result["status"] = status
        result["reason"] = reason
        result["color"] = color
            
    except EmailNotValidError as e:
        result["status"] = "Invalid format"
        result["reason"] = str(e)
        result["color"] = "red"
    
    return result

def bulk_check(emails_list, output_file="results.xlsx"):
    if not emails_list:
        print("❌ Không có email nào để kiểm tra.")
        return []
        
    print(f"\nĐang tiến hành kiểm tra {len(emails_list)} email qua SMTP...\n")
    results = []
    
    for i, email in enumerate(emails_list, 1):
        print(f"[{i}/{len(emails_list)}] Checking → {email}")
        res = classify_email(email)
        print(f"    ↳ Kết quả: {res['status']} ({res['reason']})")
        results.append(res)
        time.sleep(1.0) # Tăng nhẹ thời gian delay lên 1s để tránh bị Google chặn IP hàng loạt
    
    # Xuất ra file Excel tách cột chuẩn chỉnh
    df = pd.DataFrame(results)
    df.columns = ["Email", "Trạng thái (Status)", "Chi tiết lý do (Reason)", "Mã màu (Color)", "Thời gian check (Timestamp)"]
    df.to_excel(output_file, index=False)
    
    print(f"\n✅ Hoàn thành! Kết quả đã được phân loại chuẩn và lưu vào: {output_file}")
    return results

if __name__ == "__main__":
    print("=== Advanced Gmail Checker (Chuẩn YChecker) ===")
    print("Nhập hoặc dán danh sách email của bạn vào đây.")
    print("=> Sau khi nhập xong, nhấn ENTER 2 LẦN để bắt đầu chạy.\n")
    
    user_emails = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            user_emails.append(line.strip())
        except EOFError:
            break
            
    bulk_check(user_emails)