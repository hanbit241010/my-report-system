import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime, timedelta
import json
import time

# 1. 페이지 설정
st.set_page_config(page_title="AJIN REPORT", layout="wide")

# 2. 세션 상태 초기화
if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = 'BTC-USD'
if 'selected_name' not in st.session_state:
    st.session_state['selected_name'] = '🪙 비트코인'

# 3. 스타일(CSS) 정의
st.markdown("""
    <style>
    /* -------------------------------------------------------------------
       [1] 강력 숨김 모드 & 커스텀 하단 배너
    ------------------------------------------------------------------- */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    
    [data-testid="stManageAppButton"] { opacity: 0 !important; pointer-events: none !important; height: 0 !important;}
    .stAppDeployButton { display: none !important; }
    div[class*="stViewerBadge"] { display: none !important; }

    /* 커스텀 하단 배너 */
    .custom-footer {
        position: fixed; bottom: 0; left: 0; width: 100%; height: 70px;
        background-color: #ffffff; border-top: 1px solid #e0e0e0;
        padding: 0 20px; z-index: 2147483647;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    .footer-content { display: flex; flex-direction: column; justify-content: center; }
    .footer-main { font-size: 1.1rem; font-weight: 900; color: #333; line-height: 1.2; }
    .footer-sub { font-size: 0.75rem; font-weight: 400; color: #888; margin-top: 2px; letter-spacing: 0.5px; }
    .footer-btn {
        background-color: #d60000; color: white !important; padding: 8px 16px;
        border-radius: 20px; font-size: 0.85rem; font-weight: bold; text-decoration: none;
        box-shadow: 0 3px 6px rgba(214, 0, 0, 0.3); transition: transform 0.1s;
    }
    .footer-btn:active { transform: scale(0.95); }
    
    /* -------------------------------------------------------------------
       [2] 카드 및 리포트 스타일
    ------------------------------------------------------------------- */
    .briefing-card {
        background-color: #ffffff; border: 1px solid #ddd; border-left: 5px solid #333;
        border-radius: 8px; padding: 20px; margin-top: 20px; margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); font-family: 'sans-serif';
    }
    .briefing-header {
        font-size: 1.2rem; font-weight: 900; color: #333; margin-bottom: 15px;
        border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .briefing-date { font-size: 0.8rem; color: #888; font-weight: normal; }
    .briefing-section { margin-bottom: 20px; }
    .briefing-title { font-size: 1rem; font-weight: 800; color: #d60000; margin-bottom: 8px; }
    .briefing-text { font-size: 0.95rem; line-height: 1.6; color: #444; }
    .briefing-highlight { background-color: #fff5f5; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: #d60000; }

    /* 히트맵 바 스타일 */
    .heat-bar-container { width: 100%; background-color: #f0f0f0; border-radius: 4px; height: 8px; margin-top: 5px; overflow: hidden; }
    .heat-bar-fill { height: 100%; border-radius: 4px; }
    .theme-tag { font-size: 0.75rem; color: #666; background-color: #f8f9fa; padding: 2px 6px; border-radius: 10px; border: 1px solid #eee; margin-left: 5px; }

    /* -------------------------------------------------------------------
       [3] 기본 UI
    ------------------------------------------------------------------- */
    div.row-widget.stRadio > div { flex-direction: row; align-items: center; flex-wrap: wrap !important; gap: 8px; padding-bottom: 5px; justify-content: flex-start; }
    div.row-widget.stRadio > div[role="radiogroup"] > label { background-color: #f0f2f6; padding: 8px 14px; border-radius: 20px; border: 1px solid #e0e0e0; cursor: pointer; transition: all 0.2s; margin-right: 0 !important; font-size: 0.9rem; color: #555; }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] { background-color: #d60000 !important; color: white !important; border-color: #d60000 !important; font-weight: bold; box-shadow: 0 2px 5px rgba(214,0,0,0.2); }
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child { display: none; }
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:last-child { margin-left: 0px; }

    .streamlit-expanderHeader p { font-size: 1.6rem !important; font-weight: 800 !important; color: #222 !important; }
    .title-text { text-align: center; font-size: 2.2rem; font-weight: 800; margin-bottom: 10px; color: #000; }
    
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #f8f9fa; padding: 10px 0; margin-bottom: 20px; border-radius: 8px; white-space: nowrap; }
    .ticker-content { display: inline-block; animation: scroll 40s linear infinite; }
    .ticker-item { display: inline-block; padding: 0 2rem; font-size: 1rem; font-weight: bold; color: #333; }
    @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .up { color: #d60000; } .down { color: #0051c7; } 

    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: 'sans-serif'; font-size: 0.9rem; }
    .custom-table th { border-bottom: 2px solid #333; padding: 10px 5px; text-align: right; color: #333; font-weight: bold; }
    .custom-table td { border-bottom: 1px solid #eee; padding: 12px 5px; text-align: right; color: #333; font-weight: 500; }
    .custom-table th:first-child, .custom-table td:first-child { text-align: left; }
    
    .selected-row { background-color: #fff5f5; }
    .selected-text { color: #d60000; font-weight: 900; border-left: 4px solid #d60000; padding-left: 8px; display: inline-block; }

    @media (max-width: 600px) {
        .title-text { font-size: 1.8rem; }
        .custom-table th, .custom-table td { font-size: 0.8rem; padding: 10px 2px; }
        .block-container { padding-bottom: 100px !important; }
    }
    
    .news-card { background-color: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 10px; height: 100%; transition: transform 0.2s; }
    .news-title { font-weight: bold; font-size: 0.95rem; margin-bottom: 8px; color: #333; text-decoration: none; display: block; line-height: 1.4; }
    .news-date { font-size: 0.8rem; color: #999; }
    </style>
    """, unsafe_allow_html=True)

# 4. 타이틀 및 날짜
st.markdown("<div class='title-text'>📈 AJIN REPORT</div>", unsafe_allow_html=True)

now = datetime.now()
date_part = now.strftime("%Y. %m. %d")
week_num = now.isocalendar()[1] 
today_str = f"{date_part} (Week {week_num:02d})"

st.markdown(f"""
<div style="display: flex; justify-content: center; margin-bottom: 20px;">
    <div style="background-color: #333; color: white; padding: 6px 20px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 3px 6px rgba(0,0,0,0.2);">
        {today_str}
    </div>
</div>
""", unsafe_allow_html=True)

# --- 데이터 수집 함수 ---
@st.cache_data(ttl=600) # 10분 캐시
def get_nasdaq100_movers():
    # 나스닥 100 주요 종목 (대표성 있는 50개)
    tickers = [
        "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "COST", "NFLX",
        "AMD", "QCOM", "PEP", "ADBE", "LIN", "TXN", "INTU", "AMGN", "INTC", "HON",
        "BKNG", "SBUX", "MDLZ", "GILD", "ADP", "ADI", "REGN", "VRTX", "LRCX", "KLAC",
        "PANW", "SNPS", "CDNS", "MU", "CSCO", "TMUS", "CMCSA", "PYPL", "MAR", "ABNB",
        "ORLY", "CTAS", "MNST", "ROST", "IDXX", "ODFL", "PCAR", "KDP", "EXC", "XEL"
    ]
    # 테마 매핑
    themes = {
        "NVDA": "AI반도체", "AAPL": "기기/서비스", "MSFT": "SW/클라우드", "AMZN": "커머스/클라우드",
        "META": "SNS/메타버스", "GOOGL": "검색/AI", "TSLA": "전기차/로봇", "AVGO": "통신칩",
        "NFLX": "콘텐츠", "AMD": "반도체", "QCOM": "통신칩", "INTC": "반도체", "MU": "메모리",
        "COST": "소비재", "PEP": "음료", "SBUX": "커피", "BKNG": "여행", "ABNB": "여행",
        "GILD": "바이오", "AMGN": "바이오", "VRTX": "바이오", "REGN": "바이오",
        "ADBE": "SW", "INTU": "핀테크", "PYPL": "결제", "CSCO": "네트워크",
        "PANW": "사이버보안", "CRWD": "보안", "SNPS": "EDA", "CDNS": "EDA"
    }
    
    data_list = []
    try:
        # 배치 다운로드
        data = yf.download(" ".join(tickers), period="2d", progress=False)['Close']
        
        # DataFrame 컬럼 레벨 정리 (멀티인덱스 대응)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1) # Ticker만 남김

        for t in tickers:
            try:
                # yfinance 최신 버전은 Ticker가 컬럼명이 됨
                # 데이터가 없는 경우를 대비해 get 사용 또는 try-except
                if t not in data.columns:
                    continue
                    
                series = data[t].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    theme = themes.get(t, "기타")
                    data_list.append({"ticker": t, "pct": pct, "price": curr, "theme": theme})
            except: continue
    except: pass
    
    # 정렬
    sorted_data = sorted(data_list, key=lambda x: x['pct'], reverse=True)
    return sorted_data[:5], sorted_data[-5:] # Top 5, Bottom 5

def get_market_briefing_data():
    tickers = {
        "^IXIC": "나스닥", "^GSPC": "S&P 500", "^DJI": "다우존스",
        "BTC-USD": "비트코인", "GC=F": "금", "^VIX": "VIX"
    }
    data_storage = {}
    try:
        df = yf.download(" ".join(tickers.keys()), period="2d", progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        for t in tickers.keys():
            try:
                if t in df.columns:
                    series = df[t].dropna()
                    if len(series) >= 2:
                        curr = series.iloc[-1]
                        prev = series.iloc[-2]
                        pct = ((curr - prev) / prev) * 100
                        data_storage[t] = {'price': curr, 'pct': pct}
                    elif len(series) == 1: # 데이터가 하나뿐일 때
                        data_storage[t] = {'price': series.iloc[-1], 'pct': 0.0}
            except: pass
    except: pass
    return data_storage

# 전광판용
def get_ticker_html_data():
    targets = {"나스닥": "^IXIC", "원/달러": "KRW=X", "비트코인": "BTC-KRW", "코스피": "^KS11"}
    items = ""
    for name, ticker in targets.items():
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if len(data) >= 1:
                price = data['Close'].iloc[-1]
                prev = data['Close'].iloc[-2] if len(data) > 1 else price
                pct = ((price - prev) / prev) * 100
                color = "up" if pct >= 0 else "down"
                sign = "+" if pct >= 0 else ""
                items += f'<span class="ticker-item">{name} {price:,.0f} <span class="{color}">({sign}{pct:.2f}%)</span></span>'
        except: pass
    return items

with st.spinner("데이터 분석 중..."):
    nasdaq_top5, nasdaq_bot5 = get_nasdaq100_movers()
    market_brief_data = get_market_briefing_data()
    live_ticker = get_ticker_html_data()

st.markdown(f"""<div class="ticker-wrap"><div class="ticker-content">{live_ticker}</div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. 국제 증시 (International Indices)
# -----------------------------------------------------------------------------
market_items = [
    {"name": "🪙 비트코인", "ticker": "BTC-USD"},
    {"name": "💲 나스닥", "ticker": "^IXIC"},
    {"name": "📈 S&P 500", "ticker": "^GSPC"},
    {"name": "🏛️ 다우존스", "ticker": "^DJI"},
    {"name": "🟡 금", "ticker": "GC=F"},
    {"name": "⚪ 은", "ticker": "SI=F"},
    {"name": "⚫ 원유", "ticker": "CL=F"},
]

with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    options = [item["name"] for item in market_items]
    current_name = st.session_state['selected_name']
    if current_name not in options:
         current_name = options[0]
         st.session_state['selected_name'] = current_name
         st.session_state['selected_ticker'] = market_items[0]['ticker']

    selected_chip = st.radio("차트 선택", options, index=options.index(current_name), horizontal=True, label_visibility="collapsed")
    
    if selected_chip != st.session_state['selected_name']:
        st.session_state['selected_name'] = selected_chip
        for item in market_items:
            if item["name"] == selected_chip:
                st.session_state['selected_ticker'] = item['ticker']
                st.rerun()

    st.info(f"📊 현재 차트: **{st.session_state['selected_name']}**")
    
    # 차트 렌더링 함수
    try:
        df = yf.download(st.session_state['selected_ticker'], period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        ohlc = df[['Date', 'Open', 'High', 'Low', 'Close']].values.tolist()
        for i in range(len(ohlc)):
            ohlc[i][0] = int(pd.Timestamp(ohlc[i][0]).timestamp() * 1000)
        
        # Highcharts (간소화)
        ohlc_json = json.dumps(ohlc)
        html_code = f"""
        <html><head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;"><div id="chart" style="height:350px;"></div>
        <script>
            Highcharts.stockChart('chart', {{
                rangeSelector: {{ selected: 1 }}, navigator: {{ enabled: false }}, scrollbar: {{ enabled: false }}, credits: {{ enabled: false }},
                series: [{{ type: 'candlestick', name: '{st.session_state["selected_name"]}', data: {ohlc_json}, color: '#0051c7', upColor: '#d60000' }}]
            }});
        </script></body></html>"""
        components.html(html_code, height=370)
    except: st.error("차트 로딩 실패")

    # 리스트 출력
    html_rows = ""
    for item in market_items:
        try:
            # 실시간 데이터 호출
            hist = yf.Ticker(item['ticker']).history(period="5d")
            price, rate, diff = 0, 0, 0
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                diff = price - prev
                rate = (diff / prev) * 100
            
            color = "#d60000" if diff >= 0 else "#0051c7"
            sign = "+" if diff >= 0 else ""
            row_class = "selected-row" if st.session_state['selected_ticker'] == item['ticker'] else ""
            name_cell = f"<span class='selected-text'>{item['name']}</span>" if row_class else item['name']
            
            html_rows += f"<tr class='{row_class}'><td>{name_cell}</td><td>{price:,.2f}</td><td style='color:{color}'>{sign}{rate:.2f}%</td><td style='color:{color}'>{sign}{diff:,.2f}</td></tr>"
        except: pass

    st.markdown(f"""<table class="custom-table"><thead><tr><th>종목명</th><th>현재가</th><th>등락률</th><th>등락폭</th></tr></thead><tbody>{html_rows}</tbody></table>""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. 🗽 미국 증시 (US Market Analysis) [NEW]
# -----------------------------------------------------------------------------
with st.expander("🗽 미국 증시 (US Market Analysis)", expanded=False):
    st.subheader("🔥 나스닥 100 주도주 & 소외주")
    
    # 히트맵 바 생성 함수
    def make_heat_bar(pct):
        color = "#d60000" if pct >= 0 else "#0051c7"
        width = min(abs(pct) * 10, 100) # 최대 10%를 100% 길이로
        return f'<div class="heat-bar-container"><div class="heat-bar-fill" style="width:{width}%; background-color:{color};"></div></div>'

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### 🚀 급등 Top 5 (Gainers)")
        for stock in nasdaq_top5:
            st.markdown(f"""
            <div style="margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:bold;">{stock['ticker']} <span class="theme-tag">{stock['theme']}</span></span>
                    <span style="color:#d60000; font-weight:bold;">+{stock['pct']:.2f}%</span>
                </div>
                {make_heat_bar(stock['pct'])}
            </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown("##### 💧 급락 Top 5 (Losers)")
        for stock in nasdaq_bot5:
            st.markdown(f"""
            <div style="margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:bold;">{stock['ticker']} <span class="theme-tag">{stock['theme']}</span></span>
                    <span style="color:#0051c7; font-weight:bold;">{stock['pct']:.2f}%</span>
                </div>
                {make_heat_bar(stock['pct'])}
            </div>
            """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. 🌊 시장 흐름 (Market Flow) [NEW]
# -----------------------------------------------------------------------------
with st.expander("🌊 시장 흐름 (Market Flow)", expanded=True):
    # (1) 스마트 브리핑
    # HTML 들여쓰기 제거된 문자열
    nas_chg = market_brief_data.get('^IXIC', {}).get('pct', 0)
    avg_chg = nas_chg # 간단하게 나스닥 기준 (혹은 평균)
    mood = "강력한 상승세" if avg_chg > 1 else ("약세장" if avg_chg < -1 else "혼조세")
    
    briefing_html = f"""
<div class="briefing-card">
<div class="briefing-header">☕ 아침 7시 마켓 브리핑<span class="briefing-date">{today_str}</span></div>
<div class="briefing-section"><div class="briefing-title">1. 글로벌 시장 요약</div><div class="briefing-text">간밤 뉴욕 증시는 <span class="briefing-highlight">{mood}</span>를 보였습니다. 나스닥은 {nas_chg:+.2f}%를 기록하며 시장 흐름을 주도했습니다.</div></div>
<div class="briefing-section"><div class="briefing-title">2. 투자 포인트</div><div class="briefing-text">주요 기술주들의 실적과 금리 정책에 대한 기대감이 시장에 반영되고 있습니다. 변동성에 유의하며 분할 매수 관점이 유효합니다.</div></div>
</div>
"""
    st.markdown(briefing_html, unsafe_allow_html=True)

    # (2) 경제 캘린더 (이번 주)
    st.subheader("📅 이번 주 주요 경제 일정 (US)")
    
    # 주차 계산
    today = datetime.now()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    week_str = f"{start_week.strftime('%m.%d')} ~ {end_week.strftime('%m.%d')}"
    
    st.info(f"📆 **기간:** {week_str} (중요도 ★★★ 기준)")
    
    # 안전한 링크 버튼 제공 (크롤링 오류 방지)
    # Investing.com 필터링 된 URL (미국, 중요도 높음)
    cal_url = "https://kr.investing.com/economic-calendar/"
    
    st.markdown(f"""
    <a href="{cal_url}" target="_blank" style="text-decoration:none;">
        <div style="background-color:#f8f9fa; border:1px solid #ddd; border-radius:8px; padding:15px; text-align:center; color:#333; font-weight:bold; transition:0.3s;">
            🔗 이번 주 미국 경제지표 확인하기 (Investing.com)
        </div>
    </a>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. 🪙 암호 화폐 (Cryptocurrency)
# -----------------------------------------------------------------------------
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    # 블록미디어 뉴스 (디지털에셋 카테고리)
    try: 
        news_items = feedparser.parse("https://www.blockmedia.co.kr/archives/category/market/digital-asset/feed").entries[:8]
    except: news_items = []
    
    st.subheader("📰 주요 코인 뉴스 (BlockMedia)")
    for i in range(0, len(news_items), 2):
        nc = st.columns(2)
        for j in range(2):
            if i + j < len(news_items):
                entry = news_items[i+j]
                dt_str = ""
                try: 
                    dt_kst = datetime(*entry.published_parsed[:6]) + timedelta(hours=9)
                    dt_str = dt_kst.strftime('%Y-%m-%d %H:%M')
                except: pass
                
                with nc[j]:
                    st.markdown(f"""<div class="news-card"><a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a><div class="news-date">{dt_str}</div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 📈 국내 증시 (Domestic Market)
# -----------------------------------------------------------------------------
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    st.info("준비 중입니다...")

# [하단 커스텀 배너]
st.markdown("""
<div class="custom-footer">
    <div class="footer-content">
        <div class="footer-main">Financial Report</div>
        <div class="footer-sub">- by Ajin Partners</div>
    </div>
    <a href="tel:010-0000-0000" class="footer-btn">📞 문의하기</a>
</div>
""", unsafe_allow_html=True)