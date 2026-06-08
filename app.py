import streamlit as st
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import pandas as pd
from datetime import datetime

# Cấu hình trang web
st.set_page_config(page_title="YChecker Replica - Live Email Checker", page_icon="✅", layout="wide")

# CSS để làm đẹp giao diện giống công cụ chuyên nghiệp
st.markdown("""
    <style>
    .status-live { color: #28a745; font-weight: bold; }
    .status-die { color: #dc3545; font-weight: bold; }
    .status-disposable { color: #fd7e14; font-weight: bold; }
    .status-invalid { color: #6c757d; font-weight: bold; }
    .main-container { border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def check_email_logic(email):
    email = email.strip().lower()
    try:
        # 1. Check cú pháp
        valid = validate_email(email, check_deliverability=False)
        domain = valid.domain
        
        # 2. Check Mail rác
        if any(dis in domain for dis in ['tempmail', '10minutemail', 'guerrilla', 'yopmail', 'mailinator']):
            return "Disposable", "Email tạm thời", "🟠"
            
        # 3. Check DNS MX (Kiểm tra sự tồn tại của máy chủ mail)
        try:
            dns.resolver.resolve(domain, 'MX')
            return "Live", "Máy chủ hoạt động", "🟢"
        except:
            return "Die", "Domain không tồn tại/Không có máy chủ Mail", "🔴"
                
    except EmailNotValidError:
        return "Invalid", "Sai định dạng email", "⚪"

# --- GIAO DIỆN WEB ---
st.title("🚀 YChecker Replica - Kiểm tra Email 24/7")
st.write("Dán danh sách email vào ô dưới đây để kiểm tra trạng thái thời gian thực.")

col_input, col_stats = st.columns([2, 1])

with col_input:
    emails_text = st.text_area("Nhập danh sách email (mỗi dòng 1 email):", height=250, placeholder="example@gmail.com\nanother@yahoo.com...")
    btn_check = st.button("Bắt đầu Quét (Check Now)", type="primary")

# Nơi lưu trữ kết quả tạm thời trong phiên làm việc
if "results" not in st.session_state:
    st.session_state.results = []

if btn_check:
    email_list = [e.strip() for e in emails_text.split("\n") if e.strip()]
    if not email_list:
        st.error("Vui lòng nhập email!")
    else:
        st.session_state.results = [] # Reset kết quả cũ
        progress_bar = st.progress(0)
        
        for i, email in enumerate(email_list):
            status, reason, icon = check_email_logic(email)
            st.session_state.results.append({
                "STT": i + 1,
                "Email": email,
                "Trạng thái": f"{icon} {status}",
                "Chi tiết": reason,
                "Thời gian": datetime.now().strftime("%H:%M:%S")
            })
            progress_bar.progress((i + 1) / len(email_list))

# Hiển thị Thống kê & Kết quả ngay tại web
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    
    # Hiển thị bảng thống kê nhanh ở cột bên phải
    with col_stats:
        st.subheader("📊 Thống kê")
        total = len(df)
        live_count = len(df[df['Trạng thái'].str.contains("Live")])
        die_count = len(df[df['Trạng thái'].str.contains("Die")])
        st.success(f"✅ Live: {live_count}")
        st.error(f"❌ Die: {die_count}")
        st.info(f"📝 Tổng: {total}")

    st.divider()
    st.subheader("📋 Kết quả chi tiết")
    
    # Hiển thị bảng kết quả đẹp mắt
    st.table(df) # Hoặc st.dataframe(df, use_container_width=True)

    # Nút bấm để xóa kết quả
    if st.button("Xóa kết quả (Clear)"):
        st.session_state.results = []
        st.rerun()