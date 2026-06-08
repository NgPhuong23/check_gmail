import streamlit as st
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import pandas as pd
from datetime import datetime

# =========================
# CẤU HÌNH TRANG
# =========================

st.set_page_config(
    page_title="YChecker Replica - Live Email Checker",
    page_icon="✅",
    layout="wide"
)

# =========================
# CSS GIAO DIỆN
# =========================

st.markdown("""
<style>
.status-live {
    color: #28a745;
    font-weight: bold;
}
.status-die {
    color: #dc3545;
    font-weight: bold;
}
.status-disposable {
    color: #fd7e14;
    font-weight: bold;
}
.status-invalid {
    color: #6c757d;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HÀM KIỂM TRA EMAIL
# =========================

def check_email_logic(email):
    email = email.strip().lower()

    try:
        # Kiểm tra định dạng
        valid = validate_email(
            email,
            check_deliverability=False
        )

        domain = valid.domain

        # Kiểm tra email tạm thời
        disposable_domains = [
            "tempmail",
            "10minutemail",
            "guerrilla",
            "yopmail",
            "mailinator"
        ]

        if any(x in domain for x in disposable_domains):
            return (
                "Disposable",
                "Email tạm thời",
                "🟠"
            )

        # Kiểm tra MX Record
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3

            resolver.resolve(domain, "MX")

            return (
                "Live",
                "MX Record tồn tại",
                "🟢"
            )

        except Exception:
            return (
                "Die",
                "Domain không tồn tại hoặc không có MX Record",
                "🔴"
            )

    except EmailNotValidError:
        return (
            "Invalid",
            "Sai định dạng email",
            "⚪"
        )

# =========================
# GIAO DIỆN
# =========================

st.title("🚀 YChecker Replica")
st.write(
    "Kiểm tra định dạng email, MX Record và email tạm thời."
)

col_input, col_stats = st.columns([2, 1])

with col_input:

    emails_text = st.text_area(
        "Nhập danh sách email (mỗi dòng 1 email)",
        height=250,
        placeholder="""example@gmail.com
user@yahoo.com
test@outlook.com"""
    )

    btn_check = st.button(
        "Bắt đầu Quét",
        type="primary"
    )

# =========================
# SESSION STATE
# =========================

if "results" not in st.session_state:
    st.session_state.results = []

# =========================
# THỰC HIỆN CHECK
# =========================

if btn_check:

    email_list = [
        e.strip()
        for e in emails_text.splitlines()
        if e.strip()
    ]

    if not email_list:
        st.error("Vui lòng nhập email.")
    else:

        st.session_state.results = []

        progress_bar = st.progress(0)

        for i, email in enumerate(email_list):

            status, reason, icon = check_email_logic(email)

            st.session_state.results.append({
                "STT": i + 1,
                "Email": email,
                "Trạng thái": f"{icon} {status}",
                "Chi tiết": reason,
                "Thời gian": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            })

            progress_bar.progress(
                (i + 1) / len(email_list)
            )

# =========================
# HIỂN THỊ KẾT QUẢ
# =========================

if st.session_state.results:

    df = pd.DataFrame(
        st.session_state.results
    )

    with col_stats:

        st.subheader("📊 Thống kê")

        total = len(df)

        live_count = len(
            df[df["Trạng thái"].str.contains("Live")]
        )

        die_count = len(
            df[df["Trạng thái"].str.contains("Die")]
        )

        invalid_count = len(
            df[df["Trạng thái"].str.contains("Invalid")]
        )

        disposable_count = len(
            df[df["Trạng thái"].str.contains("Disposable")]
        )

        st.success(f"✅ Live: {live_count}")
        st.error(f"❌ Die: {die_count}")
        st.warning(f"🟠 Disposable: {disposable_count}")
        st.info(f"⚪ Invalid: {invalid_count}")
        st.info(f"📝 Tổng: {total}")

    st.divider()

    st.subheader("📋 Kết quả chi tiết")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Download CSV

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Tải kết quả CSV",
        data=csv,
        file_name="email_results.csv",
        mime="text/csv"
    )

    # Clear

    if st.button("🗑 Xóa kết quả"):
        st.session_state.results = []
        st.rerun()
