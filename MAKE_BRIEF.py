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
       [2] 브리핑 리포트 스타일
    ------------------------------------------------------------------- */
    .briefing-card {
        background-color: #ffffff; border: 1px solid #ddd; border-left: 5px solid #000;
        border-radius: 4px; padding: 25px; margin-top: 10px; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); font-family: 'sans-serif';
    }
    .briefing-header {
        font-size: 1.3rem; font-weight: 900; color: #000; margin-bottom: 20px;
        border-bottom: 2px solid #333; padding-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .briefing-date { font-size: 0.9rem; color: #666; font-weight: 500; }
    .briefing-section { margin-bottom: 20px; }
    .briefing-title { font-size: 1.1rem; font-weight: 800; color: #d60000; margin-bottom: 8px; letter-spacing: -0.5px; }
    .briefing-text { font-size: 1rem; line-height: 1.7; color: #333; text-align: justify; word-break: keep-all; }
    .briefing-highlight { background-color: #fff9c4; padding: 2px 4px; font-weight: bold; color: #333; }
    .briefing-tag { font-size: 0.8rem; background-color: #f1f3f5; color: #495057; padding: 2px 6px; border-radius: 4px; margin-right: 5px; }

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
        .briefing-card { padding: 15px; }
        .briefing-header { font-size: 1.1rem; flex-direction: column; align-items: flex-start; gap: 5px; }
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
@st.cache_data(ttl=600)
def get_nasdaq100_movers():
    tickers = [
        "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "COST", "NFLX",
        "AMD", "QCOM", "PEP", "ADBE", "LIN", "TXN", "INTU", "AMGN", "INTC", "HON",
        "BKNG", "SBUX", "MDLZ", "GILD", "ADP", "ADI", "REGN", "VRTX", "LRCX", "KLAC",
        "PANW", "SNPS", "CDNS", "MU", "CSCO", "TMUS", "CMCSA", "PYPL", "MAR", "ABNB",
        "ORLY", "CTAS", "MNST", "ROST", "IDXX", "ODFL", "PCAR", "KDP", "EXC", "XEL"
    ]
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
        data = yf.download(" ".join(tickers), period="2d", progress=False)['Close']
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
        for t in tickers:
            try:
                if t not in data.columns: continue
                series = data[t].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    theme = themes.get(t, "기타")
                    data_list.append({"ticker": t, "pct": pct, "price": curr, "theme": theme})
            except: continue
    except: pass
    sorted_data = sorted(data_list, key=lambda x: x['pct'], reverse=True)
    return sorted_data[:5], sorted_data[-5:]

def get_market_briefing_data():
    # ^TNX: 미국 10년물 국채 수익률 추가
    tickers = {
        "^IXIC": "나스닥", "^GSPC": "S&P 500", "^DJI": "다우존스",
        "BTC-USD": "비트코인", "GC=F": "금", "^VIX": "VIX", "^TNX": "국채금리"
    }
    data_storage = {}
    try:
        df = yf.download(" ".join(tickers.keys()), period="5d", progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        for t in tickers.keys():
            try:
                if t in df.columns:
                    series = df[t].dropna()
                    if len(series) >= 2:
                        curr = series.iloc[-1]
                        prev = series.iloc[-2]
                        pct = ((curr - prev) / prev) * 100
                        data_storage[t] = {'price': curr, 'pct': pct, 'prev': prev}
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
    
    # 차트
    try:
        df = yf.download(st.session_state['selected_ticker'], period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        ohlc = df[['Date', 'Open', 'High', 'Low', 'Close']].values.tolist()
        for i in range(len(ohlc)): ohlc[i][0] = int(pd.Timestamp(ohlc[i][0]).timestamp() * 1000)
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

    # 리스트
    html_rows = ""
    for item in market_items:
        try:
            t_data = market_brief_data.get(item['ticker'], None)
            if t_data:
                price = t_data['price']
                rate = t_data['pct']
                prev = t_data['prev']
                diff = price - prev
            else:
                hist = yf.Ticker(item['ticker']).history(period="5d")
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
# 2. 🗽 미국 증시 (US Market Analysis)
# -----------------------------------------------------------------------------
with st.expander("🗽 미국 증시 (US Market Analysis)", expanded=False):
    st.subheader("🔥 나스닥 100 주도주 & 소외주")
    
    def make_heat_bar(pct):
        color = "#d60000" if pct >= 0 else "#0051c7"
        width = min(abs(pct) * 10, 100)
        return f'<div class="heat-bar-container"><div class="heat-bar-fill" style="width:{width}%; background-color:{color};"></div></div>'

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🚀 급등 Top 5 (Gainers)")
        for stock in nasdaq_top5:
            st.markdown(f"""<div style="margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;"><div style="display:flex; justify-content:space-between;"><span style="font-weight:bold;">{stock['ticker']} <span class="theme-tag">{stock['theme']}</span></span><span style="color:#d60000; font-weight:bold;">+{stock['pct']:.2f}%</span></div>{make_heat_bar(stock['pct'])}</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("##### 💧 급락 Top 5 (Losers)")
        for stock in nasdaq_bot5:
            st.markdown(f"""<div style="margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;"><div style="display:flex; justify-content:space-between;"><span style="font-weight:bold;">{stock['ticker']} <span class="theme-tag">{stock['theme']}</span></span><span style="color:#0051c7; font-weight:bold;">{stock['pct']:.2f}%</span></div>{make_heat_bar(stock['pct'])}</div>""", unsafe_allow_html=True)

    # --- [풍성해진] 아침 7시 마켓 브리핑 ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 데이터 추출 및 분석 로직 강화
    nas = market_brief_data.get('^IXIC', {'pct':0, 'price':0})
    spx = market_brief_data.get('^GSPC', {'pct':0, 'price':0})
    dji = market_brief_data.get('^DJI', {'pct':0, 'price':0})
    vix = market_brief_data.get('^VIX', {'price':20})
    tnx = market_brief_data.get('^TNX', {'price':4.0, 'pct': 0}) # 국채 10년물
    
    avg_chg = (nas['pct'] + spx['pct'] + dji['pct']) / 3
    
    # 1. 시장 분위기 (Mood)
    if avg_chg > 1.5: mood_text = "폭발적인 매수세가 유입되며 강력한 상승 랠리(Bull Run)를 기록했습니다."
    elif avg_chg > 0.5: mood_text = "전반적인 투자 심리가 개선되며 견조한 상승 흐름을 보였습니다."
    elif avg_chg > -0.5: mood_text = "방향성을 탐색하며 보합권에서 등락을 거듭하는 혼조세(Mixed)를 보였습니다."
    elif avg_chg > -1.5: mood_text = "차익 실현 매물이 출회되며 약세 흐름을 보였습니다."
    else: mood_text = "투자 심리가 급격히 위축되며 강한 하락 압력(Sell-off)을 받았습니다."
    
    # 2. 금리 & 변동성 (Macro)
    macro_text = f"공포 지수인 VIX는 {vix['price']:.2f}를 기록했습니다."
    if vix['price'] < 15: macro_text += " 시장의 변동성은 매우 안정적인 구간(Low Volatility)에 진입했습니다."
    elif vix['price'] > 25: macro_text += " 시장 불확실성이 확대되며 투자자들의 경계감이 고조되고 있습니다."
    
    if tnx['pct'] > 1.0: macro_text += f" 한편, 미 10년물 국채 금리는 {tnx['price']:.2f}%로 상승하며 주식 시장 밸류에이션에 부담 요인으로 작용했습니다."
    elif tnx['pct'] < -1.0: macro_text += f" 미 10년물 국채 금리는 {tnx['price']:.2f}%로 하락 안정화되며 기술주 중심의 반등을 지지했습니다."
    
    # 3. 종합 의견 (Outlook)
    outlook = "현재 시장은 뚜렷한 주도 섹터가 부각되는 가운데,"
    if avg_chg > 0: outlook += " 조정 시 저가 매수세가 유입되는 강한 하방 경직성을 보여주고 있습니다."
    else: outlook += " 단기적인 기술적 저항에 직면하여 리스크 관리가 필요한 시점입니다."

    briefing_html = f"""
<div class="briefing-card">
<div class="briefing-header">☕ 아침 7시 마켓 브리핑<span class="briefing-date">{today_str} 기준</span></div>
<div class="briefing-section">
<div class="briefing-title">1. 글로벌 시장 및 매크로 (Overview)</div>
<div class="briefing-text">
간밤 뉴욕 증시는 <span class="briefing-highlight">{mood_text}</span> 
나스닥({nas['pct']:+.2f}%), S&P 500({spx['pct']:+.2f}%), 다우존스({dji['pct']:+.2f}%) 등 3대 지수는 엇갈린 흐름 속에 마감했습니다. 
{macro_text}
</div>
</div>
<div class="briefing-section">
<div class="briefing-title">2. 전문가 종합 의견 (Strategy)</div>
<div class="briefing-text">
{outlook} 특히 이번 주 예정된 주요 경제 지표 발표를 앞두고 관망세가 짙어질 수 있으므로, 
추격 매수보다는 <span class="briefing-highlight">실적 호전주 및 낙폭 과대 우량주 위주의 선별적 접근</span>이 유효해 보입니다.
</div>
</div>
</div>
"""
    st.markdown(briefing_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. 🌊 시장 흐름 (Market Flow)
# -----------------------------------------------------------------------------
with st.expander("🌊 시장 흐름 (Market Flow)", expanded=True):
    st.subheader("📅 이번 주 주요 경제 일정 (US)")
    
    # 주차 계산
    today = datetime.now()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    week_str = f"{start_week.strftime('%m.%d')} ~ {end_week.strftime('%m.%d')}"
    
    st.info(f"📆 **기간:** {week_str} (미국 중요도 ★★★ 지표 기준)")
    
    # 안전한 링크 버튼 (크롤링 오류 원천 차단)
    # investing.com 필터 적용 링크
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("실시간 경제 캘린더 확인하기 👉")
    with col2:
        st.link_button("🔗 Investing.com 경제 캘린더 (US)", "https://kr.investing.com/economic-calendar/")
    
    st.markdown("""
    <div style="font-size:0.8rem; color:#666; margin-top:10px;">
    * 데이터 제공사의 보안 정책으로 인해 실시간 일정은 위 버튼을 통해 확인하실 수 있습니다.<br>
    * 주요 체크 포인트: CPI(소비자물가지수), FOMC 의사록, 비농업 고용 지수 등
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. 🪙 암호 화폐 (Cryptocurrency)
# -----------------------------------------------------------------------------
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    with st.spinner("데이터 조회 중..."):
        kimp, dom = get_crypto_insight()
        news_list = get_crypto_news()
    ic1, ic2 = st.columns(2)
    with ic1:
        color = "#d60000" if kimp >= 0 else "#0051c7"
        st.markdown(f"""<div class="insight-box"><div class="insight-label">글로벌 시세 차이 (Kimchi Premium)</div><div class="insight-value" style="color: {color};">{kimp:.2f}%</div></div>""", unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""<div class="insight-box"><div class="insight-label">비트코인 점유율 (BTC Dominance)</div><div class="insight-value" style="color: #f7931a;">{dom:.1f}%</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📰 주요 코인 뉴스 (BlockMedia)")
    for i in range(0, len(news_list), 2):
        nc = st.columns(2)
        for j in range(2):
            if i + j < len(news_list):
                entry = news_list[i+j]
                dt_str = ""
                try: 
                    dt_kst = datetime(*entry.published_parsed[:6]) + timedelta(hours=9)
                    dt_str = dt_kst.strftime('%Y-%m-%d %H:%M')
                except: pass
                with nc[j]:
                    st.markdown(f"""<div class="news-card"><a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a><div class="news-date">{dt_str}</div></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 📈 국내 증시 (Domestic Market) [부활]
# -----------------------------------------------------------------------------
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    with st.spinner("국내 증시 데이터 수집 중..."):
        try:
            kp_df = yf.download('^KS11', period='5d', progress=False)
            kq_df = yf.download('^KQ11', period='5d', progress=False)
            ex_df = yf.download('KRW=X', period='5d', progress=False)
            
            # DataFrame 정리
            if isinstance(kp_df.columns, pd.MultiIndex): kp_df.columns = kp_df.columns.droplevel(1)
            if isinstance(kq_df.columns, pd.MultiIndex): kq_df.columns = kq_df.columns.droplevel(1)
            if isinstance(ex_df.columns, pd.MultiIndex): ex_df.columns = ex_df.columns.droplevel(1)

            def get_met(df):
                if df.empty: return 0, 0, 0
                now = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                return now, now - prev, ((now - prev) / prev) * 100
            
            kp_now, kp_delta, kp_pct = get_met(kp_df)
            kq_now, kq_delta, kq_pct = get_met(kq_df)
            ex_now, ex_delta, ex_pct = get_met(ex_df)
        except: kp_now, kp_delta, kp_pct, kq_now, kq_delta, kq_pct, ex_now, ex_delta, ex_pct = 0,0,0,0,0,0,0,0,0

    m1, m2, m3 = st.columns(3)
    with m1: render_custom_metric("코스피", f"{kp_now:,.2f}", kp_delta, kp_pct)
    with m2: render_custom_metric("코스닥", f"{kq_now:,.2f}", kq_delta, kq_pct)
    with m3: render_custom_metric("원/달러", f"{ex_now:,.2f}", ex_delta, ex_pct)

    st.markdown("---")
    st.subheader("KOSPI Market Trend")
    render_highchart_domestic('KS11', 'KOSPI', height=400)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("KOSDAQ Market Trend")
    render_highchart_domestic('KQ11', 'KOSDAQ', height=400)

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