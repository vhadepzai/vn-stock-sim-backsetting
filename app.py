import streamlit as st
import pandas as pd
import numpy as np
from vnstock3 import Vnstock
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Cấu hình trang
st.set_page_config(layout="wide", page_title="VN Stock Backtest Simulator")

# 1. Danh sách ngân hàng vốn hóa lớn
BANKS = ['VCB', 'BID', 'CTG', 'TCB', 'MBB', 'VPB', 'ACB', 'HDB', 'VIB']

@st.cache_data
def get_stock_data(symbol):
    # Lấy dữ liệu lịch sử từ khi lên sàn
    df = stock_historical_data(symbol, "2010-01-01", str(datetime.now().date()), "daily")
    return df

# Khởi tạo session state để lưu trạng thái trò chơi
if 'game_state' not in st.session_state:
    st.session_state.game_state = 'START'
    st.session_state.history = []

def start_new_game():
    symbol = random.choice(BANKS)
    df = get_stock_data(symbol)
    
    # Chọn mốc thời gian A ngẫu nhiên (đảm bảo còn ít nhất 2 năm dữ liệu phía sau)
    max_idx = len(df) - 500 
    start_idx = random.randint(200, max_idx)
    
    st.session_state.symbol = symbol
    st.session_state.full_df = df
    st.session_state.start_idx = start_idx
    st.session_state.capital = 100000000 # 100 triệu mặc định
    st.session_state.game_state = 'PLAYING'

# GIAO DIỆN CHÍNH
st.title("🏦 VN Bank Stock Simulator (Gemini Style)")

if st.button("Bắt đầu ván mới 🎲") or st.session_state.game_state == 'START':
    start_new_game()

# Lấy dữ liệu tại mốc thời gian A
df = st.session_state.full_df
idx = st.session_state.start_idx
visible_df = df.iloc[:idx]
target_date = df.iloc[idx]['time']

col1, col2 = st.columns([7, 3])

with col1:
    st.subheader(f"Mã cổ phiếu: {st.session_state.symbol} - Ngày hiện tại (Mốc A): {target_date}")
    
    chart_type = st.radio("Loại đồ thị", ["Nến", "Đường"], horizontal=True)
    
    fig = go.Figure()
    if chart_type == "Nến":
        fig.add_trace(go.Candlestick(x=visible_df['time'], open=visible_df['open'], 
                                     high=visible_df['high'], low=visible_df['low'], close=visible_df['close']))
    else:
        fig.add_trace(go.Scatter(x=visible_df['time'], y=visible_df['close'], mode='lines'))
    
    fig.update_layout(height=600, dragmode='pan') # Cho phép kéo thả, zoom
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🤖 Trợ lý đầu tư")
    st.info(f"Vốn ban đầu: {st.session_state.capital:,.0f} VNĐ")
    
    prompt = st.text_area("Nhập kế hoạch đầu tư của bạn (ví dụ: Mua hết tại giá hiện tại, 1 năm sau bán):", height=200)
    
    duration = st.number_input("Khoảng thời gian M (tháng)", min_value=1, max_value=60, value=12)

    if st.button("Thực hiện kế hoạch 🚀"):
        # Logic xử lý AI mô phỏng (Ở đây tôi viết logic tính toán thực tế)
        future_df = df.iloc[idx : idx + (duration * 21)] # 21 ngày giao dịch/tháng
        entry_price = df.iloc[idx]['close']
        exit_price = future_df.iloc[-1]['close']
        
        profit_pct = (exit_price - entry_price) / entry_price * 100
        final_cash = st.session_state.capital * (1 + profit_pct/100)
        
        st.success(f"Kết quả sau {duration} tháng:")
        st.write(f"- Giá mua tại A: {entry_price:,.0f}")
        st.write(f"- Giá bán tại M: {exit_price:,.0f}")
        st.write(f"- Lợi nhuận: {profit_pct:.2f}%")
        st.write(f"- Tổng tài sản: {final_cash:,.0f} VNĐ")
        
        # Lưu snapshot
        st.session_state.history.append({
            "symbol": st.session_state.symbol,
            "date": target_date,
            "plan": prompt,
            "result": f"{profit_pct:.2f}%"
        })

if st.session_state.history:
    with st.expander("Xem lại lịch sử các lần thử (Snapshots)"):
        st.table(st.session_state.history)
