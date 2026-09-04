import streamlit as st
import pandas as pd
import numpy as np
from vnstock3 import Vnstock
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- CẤU HÌNH TRANG ---
st.set_page_config(layout="wide", page_title="VN Bank Stock Simulator", page_icon="🏦")

# Tùy chỉnh giao diện giống Gemini (Darkmode nhẹ)
st.markdown("""
    <style>
    .main { background-color: #131314; color: #e3e3e3; }
    .stTextArea textarea { background-color: #1e1f20; color: white; border: 1px solid #444746; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #004a77; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Vnstock
@st.cache_resource
def init_stock():
    return Vnstock()

stock = init_stock()

# Danh sách ngân hàng vốn hóa lớn (>25% tỉ trọng thường là nhóm Big4 + Bank lớn)
BANKS = ['VCB', 'BID', 'CTG', 'TCB', 'MBB', 'VPB', 'ACB', 'LPB', 'HDB']

@st.cache_data
def get_data(symbol):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = "2012-01-01" # Lấy dữ liệu từ 2012
    try:
        df = stock.stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution='1D', type='stock')
        df['time'] = pd.to_datetime(df['time'])
        return df
    except:
        return pd.DataFrame()

# --- KHỞI TẠO GAME STATE ---
if 'game_id' not in st.session_state:
    st.session_state.game_id = 0
    st.session_state.history = []
    st.session_state.playing = False

def start_new_game():
    symbol = random.choice(BANKS)
    df = get_data(symbol)
    if not df.empty and len(df) > 500:
        # Chọn mốc A ngẫu nhiên, chừa ít nhất 3 năm (750 phiên) để test
        max_idx = len(df) - 750
        start_idx = random.randint(200, max_idx)
        
        st.session_state.symbol = symbol
        st.session_state.full_df = df
        st.session_state.start_idx = start_idx
        st.session_state.capital = 100000000 # 100 Triệu
        st.session_state.playing = True
        st.session_state.result_shown = False
    else:
        start_new_game()

# --- GIAO DIỆN CHÍNH ---
st.title("🚀 VN Stock Strategy Simulator")

if not st.session_state.playing:
    st.info("Chào mừng bạn! Nhấn nút bên dưới để bắt đầu mô phỏng một mã ngân hàng ngẫu nhiên trong quá khứ.")
    if st.button("Bắt đầu thử thách mới 🎲"):
        start_new_game()
        st.rerun()
else:
    df = st.session_state.full_df
    idx = st.session_state.start_idx
    visible_df = df.iloc[:idx]
    current_price = df.iloc[idx]['close']
    current_date = df.iloc[idx]['time'].strftime('%d/%m/%Y')

    # Chia cột: Trái là Biểu đồ, Phải là Chat/Kế hoạch
    col_chart, col_chat = st.columns([7, 3])

    with col_chart:
        st.subheader(f"Biểu đồ mã: {st.session_state.symbol}")
        mode = st.radio("Chế độ hiển thị", ["Nến Nhật", "Đồ thị đường"], horizontal=True)
        
        fig = go.Figure()
        if mode == "Nến Nhật":
            fig.add_trace(go.Candlestick(
                x=visible_df['time'], open=visible_df['open'],
                high=visible_df['high'], low=visible_df['low'], close=visible_df['close'],
                name="Candlestick"
            ))
        else:
            fig.add_trace(go.Scatter(x=visible_df['time'], y=visible_df['close'], mode='lines', line=dict(color='#00d1ff')))

        fig.update_layout(
            height=600,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            dragmode='zoom', # Cho phép scale, zoom thoải mái
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Mẹo: Dùng chuột bôi đen vùng trên đồ thị để phóng to (Zoom), nhấn đúp để quay lại.")

    with col_chat:
        st.markdown(f"### 💬 Gemini Analyst")
        st.write(f"📅 **Ngày hiện tại:** {current_date}")
        st.write(f"💰 **Vốn ban đầu:** {st.session_state.capital:,.0f} VNĐ")
        st.write(f"💵 **Giá hiện tại:** {current_price:,.0f} VNĐ")
        
        st.divider()
        
        plan = st.text_area("Mô tả kế hoạch đầu tư của bạn:", 
                            placeholder="Ví dụ: Tôi sẽ mua 50% vốn ở đây, nếu giá giảm 10% tôi mua hết phần còn lại. Tôi sẽ chốt lời sau 2 năm.",
                            height=150)
        
        m_months = st.number_input("Thời gian nắm giữ (M tháng):", min_value=1, max_value=60, value=12)

        if st.button("Thực thi kế hoạch & Xem kết quả 📈"):
            # Giả lập AI xử lý (Lấy giá tại thời điểm M)
            end_idx = idx + (m_months * 21) # 21 ngày giao dịch/tháng
            if end_idx >= len(df): end_idx = len(df) - 1
            
            sell_price = df.iloc[end_idx]['close']
            sell_date = df.iloc[end_idx]['time'].strftime('%d/%m/%Y')
            profit_pct = (sell_price - current_price) / current_price * 100
            final_money = st.session_state.capital * (1 + profit_pct/100)

            st.session_state.result_data = {
                "profit": profit_pct,
                "final": final_money,
                "sell_price": sell_price,
                "sell_date": sell_date
            }
            st.session_state.result_shown = True
            
            # Snapshot lại lịch sử
            st.session_state.history.append({
                "Mã": st.session_state.symbol,
                "Ngày bắt đầu": current_date,
                "Kế hoạch": plan,
                "Thời gian": f"{m_months} th",
                "Kết quả": f"{profit_pct:.2f}%"
            })

        if st.session_state.get('result_shown'):
            res = st.session_state.result_data
            st.divider()
            color = "#00ff00" if res['profit'] > 0 else "#ff4b4b"
            st.markdown(f"#### Kết quả tại ngày {res['sell_date']}:")
            st.markdown(f"<h2 style='color:{color}'>{res['profit']:+.2f}%</h2>", unsafe_allow_html=True)
            st.write(f"Tổng tài sản: **{res['final']:,.0f} VNĐ**")
            
            if st.button("Chơi ván mới 🔄"):
                st.session_state.playing = False
                st.rerun()

# --- PHẦN BACKEND: SNAPSHOT REVIEW ---
if st.session_state.history:
    with st.expander("📂 Xem lại các chiến lược đã thực hiện (Snapshots)"):
        hist_df = pd.DataFrame(st.session_state.history)
        st.table(hist_df)
