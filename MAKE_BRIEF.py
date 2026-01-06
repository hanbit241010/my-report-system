import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# 1. 페이지 설정 (넓은 레이아웃)
st.set_page_config(page_title="Report System", layout="wide")

# 2. 스타일(CSS) 정의: 전광판 속도 조절 및 카드 디자인
st.markdown("""
    <style>
    /* 상단 전광판 스타일 */
    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background-color: #f8f9fa;
        padding: 10px 0;
        margin-bottom: 20px;
        border-radius: 5px;
        white-space: nowrap;
    }
    .ticker-content {
        display: inline-block;
        /* 속도 조절: 숫자가 클수록 느려짐 (40s = 40초 동안 이동) */
        animation: scroll 40s linear infinite; 
    }
    .ticker-item {
        display: inline-block;
        padding: 0 2rem;
        font-size: 1rem;
        font-weight: bold;
        color: #333;
    }
    @keyframes scroll {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    /* 상승/하락 색상 클래스 */
    .up { color: #e15241; }
    .down { color: #4e8df5; }

    /* 메트릭 카드 스타일 (이미지와 유사하게) */
    div[data-testid="stMetric"] {
        background-color: #fff0f0; /* 기본 붉은 배경 */
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* 두 번째 컬럼(코스닥)만 파란 배경으로 강제 변경하는 CSS 핵 (순서 의존) */
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] {
        background-color: #f0f6ff;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 헤더 영역 (로고 및 날짜)
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 📈 REPORT SYSTEM")
with col_h2:
    today_str = datetime.now().strftime("%Y. %m. %d (Week %W)")
    st.markdown(f"<div style='text-align:right; background:#333; color:white; padding:5px 15px; border-radius:15px;'>{today_str}</div>", unsafe_allow_html=True)

# 4. 상단 전광판 (Ticker) - 속도 조절됨
ticker_html = """
<div class="ticker-wrap">
    <div class="ticker-content">
        <span class="ticker-item">나스닥 14,500.50 <span class="down">(-0.16%)</span></span>
        <span class="ticker-item">원/달러 1,446.35 <span class="up">(+0.41%)</span></span>
        <span class="ticker-item">비트코인 134,826,448 <span class="down">(-0.72%)</span></span>
        <span class="ticker-item">코스피 4,525.48 <span class="up">(+1.52%)</span></span>
        <span class="ticker-item">코스닥 955.97 <span class="down">(-0.16%)</span></span>
        <span class="ticker-item">나스닥 14,500.50 <span class="down">(-0.16%)</span></span>
        <span class="ticker-item">원/달러 1,446.35 <span class="up">(+0.41%)</span></span>
        <span class="ticker-item">비트코인 134,826,448 <span class="down">(-0.72%)</span></span>
    </div>
</div>
"""
st.markdown(ticker_html, unsafe_allow_html=True)

# 5. 검색창 영역 -> 삭제됨

# 6. 주요 지수 카드 (Metrics)
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="코스피", value="4,525.48", delta="▲ 67.96 (+1.52%)")
with m2:
    st.metric(label="코스닥", value="955.97", delta="▼ 1.53 (-0.16%)", delta_color="inverse")
with m3:
    st.metric(label="원/달러", value="1,446.35", delta="▲ 5.87 (+0.41%)")

st.markdown("---")

# 7. 메인 컨텐츠 (차트 + 관심종목)
c_left, c_right = st.columns([2, 1])

# 왼쪽: 트레이딩뷰 차트 (수정됨)
with c_left:
    st.subheader("트레이딩뷰 차트 (KOSPI)")
    
    # 트레이딩뷰 위젯 코드
    tv_html = """
    <div class="tradingview-widget-container">
      <div id="tradingview_kospi"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {
      "width": "100%",
      "height": 500,
      "symbol": "KRX:KOSPI", 
      "interval": "D",
      "timezone": "Asia/Seoul",
      "theme": "light",
      "style": "1",
      "locale": "kr",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_kospi"
      }
      );
      </script>
    </div>
    """
    # 높이 500px 확보
    components.html(tv_html, height=510)

# 오른쪽: 관심종목 리스트 (Watch List)
with c_right:
    st.subheader("📑 Watch List")
    
    # 테이블 스타일링 및 데이터
    watchlist_html = """
    <style>
        table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
        th { text-align: left; color: #666; padding: 10px 0; border-bottom: 1px solid #eee; }
        td { padding: 12px 0; border-bottom: 1px solid #f0f0f0; }
        .price-up { color: #e15241; font-weight: bold; text-align: right;}
        .name { font-weight: bold; }
    </style>
    <table>
        <thead>
            <tr>
                <th>종목명</th>
                <th style="text-align:right;">현재가</th>
                <th style="text-align:right;">등락률</th>
            </tr>
        </thead>
        <tbody>
            <tr><td class="name">삼성전자</td><td style="text-align:right;">138,900</td><td class="price-up">+0.58%</td></tr>
            <tr><td class="name">SK하이닉스</td><td style="text-align:right;">726,000</td><td class="price-up">+4.31%</td></tr>
            <tr><td class="name">NAVER</td><td style="text-align:right;">260,000</td><td class="price-up">+4.21%</td></tr>
            <tr><td class="name">카카오</td><td style="text-align:right;">63,800</td><td class="price-up">+1.59%</td></tr>
            <tr><td class="name">현대차</td><td style="text-align:right;">308,000</td><td class="price-up">+1.15%</td></tr>
            <tr><td class="name">에코프로비엠</td><td style="text-align:right;">148,400</td><td class="price-up">+1.78%</td></tr>
        </tbody>
    </table>
    <br>
    <div style="background:#f9f9f9; padding:10px; border-radius:5px; font-size:0.8rem; color:#666;">
        ℹ️ <b>알림:</b><br>
        본 리포트는 실시간 데이터를 기반으로 자동 생성되었습니다.<br>
        차트는 마우스 휠로 확대/축소가 가능합니다.
    </div>
    """
    st.markdown(watchlist_html, unsafe_allow_html=True)

# 푸터
st.markdown("<div style='text-align:center; color:#ccc; margin-top:50px; font-size:0.8rem;'>Auto-Generated by Python Financial Bot | Created at " + datetime.now().strftime("%H:%M:%S") + "</div>", unsafe_allow_html=True)