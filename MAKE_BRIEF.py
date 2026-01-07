import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime
import json

# 1. 페이지 설정
st.set_page_config(page_title="AJIN REPORT", layout="wide")

# 2. 세션 상태 초기화
if 'selected_ticker' not in st.session_state:
    st.session_state['selected_ticker'] = 'BTC-USD'
if 'selected_name' not in st.session_state:
    st.session_state['selected_name'] = '비트코인'

# 3. 스타일(CSS) 정의
st.markdown("""
    <style>
    /* [기본] 헤더/푸터/배포버튼 숨김 */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    .stAppDeployButton { display: none !important; } /* 왕관/로켓 버튼 숨김 */
    
    /* [폰트] 섹션 헤더(Expander Title) 대폭 확대 */
    .streamlit-expanderHeader p {
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        color: #000 !important;
    }
    
    /* 타이틀 */
    .title-text {
        text-align: center; font-size: 2.8rem; font-weight: 800;
        margin-bottom: 10px; color: #000;
    }
    
    /* 전광판 */
    .ticker-wrap {
        width: 100%; overflow: hidden; background-color: #f8f9fa;
        padding: 12px 0; margin-bottom: 20px; border-radius: 8px; white-space: nowrap;
    }
    .ticker-content { display: inline-block; animation: scroll 40s linear infinite; }
    .ticker-item { display: inline-block; padding: 0 2rem; font-size: 1.1rem; font-weight: bold; color: #333; }
    @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    
    .up { color: #d60000; } 
    .down { color: #0051c7; } 

    /* 리스트 헤더 */
    .market-header {
        font-weight: bold; border-bottom: 2px solid #555; padding: 10px 5px; color: #333; font-size: 1rem;
    }

    /* 버튼 스타일 (리스트 아이템화) */
    div.stButton > button {
        width: 100%; border: none; background-color: transparent;
        color: #333; text-align: left; padding: 12px 2px;
        font-size: 1.1rem; font-weight: 500; margin: 0;
        line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    div.stButton > button:hover { background-color: #f9f9f9; color: #d60000; }
    div.stButton > button:focus { box-shadow: none; color: #d60000; }

    /* 수치 데이터 셀 */
    .data-cell {
        display: flex; align-items: center; justify-content: flex-end;
        height: 48px; font-weight: bold; font-size: 1rem; white-space: nowrap;
    }
    
    /* [중요] 모바일 최적화 (표 형태 강제 유지) */
    @media (max-width: 600px) {
        /* 타이틀 크기 축소 */
        .title-text { font-size: 2rem; }
        
        /* 1. 가로 정렬 강제 (세로로 쌓이는 것 방지) */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
        }
        
        /* 2. 컬럼 너비 강제 조정 (최소 너비 해제) */
        [data-testid="column"] {
            min-width: 0 !important;
            width: auto !important;
            flex-shrink: 1 !important;
            padding: 0 1px !important;
        }
        
        /* 3. 폰트 및 여백 다이어트 (한 줄에 다 넣기 위해) */
        .market-header { 
            font-size: 0.7rem !important; 
            padding: 5px 0 !important; 
            text-align: center !important;
            white-space: nowrap;
        }
        
        div.stButton > button { 
            font-size: 0.75rem !important; 
            padding: 10px 0 !important; 
            margin: 0 !important;
        }
        
        .data-cell { 
            font-size: 0.75rem !important; 
            height: 40px !important; /* 높이 줄임 */
            justify-content: center !important; /* 모바일은 중앙 정렬이 깔끔 */
            padding-right: 0 !important;
        }
        
        /* 섹션 헤더 */
        .streamlit-expanderHeader p { font-size: 1.5rem !important; }
    }
    
    /* 암호화폐 카드 */
    .insight-box {
        background-color: #f8f9fa; border-radius: 10px; padding: 20px;
        text-align: center; border: 1px solid #eee;
    }
    .insight-label { font-size: 1rem; color: #666; margin-bottom: 5px; }
    .insight-value { font-size: 2rem; font-weight: bold; color: #333; }
    .insight-sub { font-size: 0.9rem; color: #888; }
    
    .news-card {
        background-color: white; padding: 15px; border-radius: 10px;
        border: 1px solid #eee; margin-bottom: 10px; height: 100%;
        transition: transform 0.2s;
    }
    .news-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .news-title { font-weight: bold; font-size: 1rem; margin-bottom: 5px; color: #333; text-decoration: none; display: block; }
    .news-date { font-size: 0.85rem; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# 4. 타이틀 및 날짜
st.markdown("<div class='title-text'>📈 AJIN REPORT</div>", unsafe_allow_html=True)

now = datetime.now()
date_part = now.strftime("%Y. %m. %d")
week_num = now.isocalendar()[1] 
today_str = f"{date_part} (Week {week_num:02d})"

date_html = f"""
<div style="display: flex; justify-content: center; margin-bottom: 20px;">
    <div style="background-color: #333; color: white; padding: 8px 25px; border-radius: 20px; font-weight: bold; font-size: 1rem; box-shadow: 0 3px 6px rgba(0,0,0,0.2);">
        {today_str}
    </div>
</div>
"""
st.markdown(date_html, unsafe_allow_html=True)

# 전광판 데이터 수집
def get_ticker_html_data():
    targets = {
        "나스닥": "^IXIC", "원/달러": "KRW=X", "비트코인": "BTC-KRW",
        "코스피": "^KS11", "코스닥": "^KQ11"
    }
    items_html = ""
    for name, ticker in targets.items():
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if len(data) >= 1:
                price = data['Close'].iloc[-1]
                if len(data) > 1:
                    prev = data['Close'].iloc[-2]
                    diff = price - prev
                    pct = (diff / prev) * 100
                else: diff, pct = 0, 0
                color_class = "up" if diff >= 0 else "down"
                sign = "+" if diff >= 0 else ""
                items_html += f'<span class="ticker-item">{name} {price:,.2f} <span class="{color_class}">({sign}{pct:.2f}%)</span></span>'
            else: items_html += f'<span class="ticker-item">{name} - </span>'
        except: items_html += f'<span class="ticker-item">{name} Error</span>'
    return items_html

with st.spinner("시장 데이터 동기화 중..."):
    live_ticker_items = get_ticker_html_data()

ticker_html = f"""
<div class="ticker-wrap"><div class="ticker-content">{live_ticker_items}</div></div>
"""
st.markdown(ticker_html, unsafe_allow_html=True)

# --- 함수 모음 ---
def render_highchart_global(ticker, name, height=400):
    try:
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        ohlc, volume = [], []
        if df.empty:
            st.warning("차트 데이터 로딩 실패")
            return
        for idx, row in df.iterrows():
            date_val = row.get('Date', row.name)
            if not isinstance(date_val, pd.Timestamp): continue
            ts = int(date_val.timestamp() * 1000)
            op = float(row['Open']) if pd.notnull(row['Open']) else 0
            hi = float(row['High']) if pd.notnull(row['High']) else 0
            lo = float(row['Low']) if pd.notnull(row['Low']) else 0
            cl = float(row['Close']) if pd.notnull(row['Close']) else 0
            vo = int(row['Volume']) if pd.notnull(row['Volume']) else 0
            ohlc.append([ts, op, hi, lo, cl])
            volume.append([ts, vo])
        ohlc_json = json.dumps(ohlc)
        vol_json = json.dumps(volume)
        html_code = f"""
        <html>
        <head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;">
            <div id="chart_global" style="height: {height}px; width: 100%;"></div>
            <script>
                Highcharts.setOptions({{ lang: {{ thousandsSep: ',' }} }});
                Highcharts.stockChart('chart_global', {{
                    rangeSelector: {{ enabled: true, selected: 1, inputEnabled: false, buttons: [{{ type: 'month', count: 1, text: '1M' }}, {{ type: 'month', count: 3, text: '3M' }}, {{ type: 'month', count: 6, text: '6M' }}, {{ type: 'ytd', text: 'YTD' }}, {{ type: 'year', count: 1, text: '1Y' }}] }},
                    navigator: {{ enabled: true, height: 30 }},
                    scrollbar: {{ enabled: false }},
                    credits: {{ enabled: false }},
                    chart: {{ backgroundColor: '#ffffff', events: {{ render: function() {{ var chart = this; var width = chart.plotWidth; var height = chart.plotHeight; var x = chart.plotLeft + width / 2; var y = chart.plotTop + height * 0.4; var fontSize = Math.min(width / 15, 50); if (!chart.watermark) {{ chart.watermark = chart.renderer.text('AJIN PARTNERS', x, y).css({{ color: '#E0E0E0', fontWeight: '900', opacity: 0.6 }}).attr({{ align: 'center', zIndex: 0 }}).add(); }} chart.watermark.attr({{ x: x, y: y }}).css({{ fontSize: fontSize + 'px' }}); }} }} }},
                    yAxis: [{{ labels: {{ align: 'right', x: -3 }}, height: '75%', lineWidth: 2, resize: {{ enabled: true }} }}, {{ labels: {{ align: 'right', x: -3 }}, top: '75%', height: '25%', offset: 0, lineWidth: 2 }}],
                    tooltip: {{ split: true }},
                    plotOptions: {{ candlestick: {{ color: '#0051c7', upColor: '#d60000', lineColor: '#0051c7', upLineColor: '#d60000' }} }},
                    series: [{{ type: 'candlestick', name: '{name}', data: {ohlc_json} }}, {{ type: 'column', name: 'Volume', data: {vol_json}, yAxis: 1, color: 'rgba(0,0,0,0.1)' }}]
                }});
            </script>
        </body></html>"""
        components.html(html_code, height=height+20)
    except: st.error("차트 오류")

def render_highchart_domestic(ticker, name, height=450):
    try:
        yf_ticker = "^KS11" if ticker == "KS11" else "^KQ11"
        if ticker == "USD/KRW": yf_ticker = "KRW=X"
        df = yf.download(yf_ticker, period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        ohlc, volume = [], []
        if df.empty:
            st.warning(f"{name} 데이터 수집 실패")
            return
        for idx, row in df.iterrows():
            ts = int(row['Date'].timestamp() * 1000)
            ohlc.append([ts, row['Open'], row['High'], row['Low'], row['Close']])
            volume.append([ts, row['Volume'] if pd.notnull(row['Volume']) else 0])
        ohlc_json = json.dumps(ohlc)
        vol_json = json.dumps(volume)
        html_code = f"""
        <html>
        <head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;">
            <div id="chart_{ticker}" style="height: {height}px; width: 100%;"></div>
            <script>
                Highcharts.setOptions({{ lang: {{ thousandsSep: ',' }} }});
                Highcharts.stockChart('chart_{ticker}', {{
                    rangeSelector: {{ enabled: true, selected: 1, inputEnabled: false, buttons: [{{ type: 'month', count: 1, text: '1M' }}, {{ type: 'month', count: 3, text: '3M' }}, {{ type: 'month', count: 6, text: '6M' }}, {{ type: 'ytd', text: 'YTD' }}, {{ type: 'year', count: 1, text: '1Y' }}] }},
                    navigator: {{ enabled: true, height: 30 }},
                    scrollbar: {{ enabled: false }},
                    credits: {{ enabled: false }},
                    chart: {{ backgroundColor: '#ffffff', events: {{ render: function() {{ var chart = this; var width = chart.plotWidth; var height = chart.plotHeight; var x = chart.plotLeft + width / 2; var y = chart.plotTop + height * 0.4; var fontSize = Math.min(width / 15, 50); if (!chart.watermark) {{ chart.watermark = chart.renderer.text('AJIN PARTNERS', x, y).css({{ color: '#E0E0E0', fontWeight: '900', opacity: 0.6 }}).attr({{ align: 'center', zIndex: 0 }}).add(); }} chart.watermark.attr({{ x: x, y: y }}).css({{ fontSize: fontSize + 'px' }}); }} }} }},
                    yAxis: [{{ labels: {{ align: 'right', x: -3 }}, height: '75%', lineWidth: 2, resize: {{ enabled: true }} }}, {{ labels: {{ align: 'right', x: -3 }}, top: '75%', height: '25%', offset: 0, lineWidth: 2 }}],
                    tooltip: {{ split: true }},
                    plotOptions: {{ candlestick: {{ color: '#0051c7', upColor: '#d60000', lineColor: '#0051c7', upLineColor: '#d60000' }} }},
                    series: [{{ type: 'candlestick', name: '{name}', data: {ohlc_json} }}, {{ type: 'column', name: 'Volume', data: {vol_json}, yAxis: 1, color: 'rgba(0,0,0,0.1)' }}]
                }});
            </script>
        </body></html>"""
        components.html(html_code, height=height+20)
    except: st.error("차트 오류")

def get_crypto_insight():
    kimp, dom = 0.0, 0.0
    try:
        usd = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", timeout=2).json()
        kor = float(res['data']['closing_price'])
        if btc * usd > 0: kimp = ((kor - (btc * usd)) / (btc * usd)) * 100
    except: pass
    try:
        dom = requests.get("https://api.coingecko.com/api/v3/global", timeout=2).json()['data']['market_cap_percentage']['btc']
    except: pass
    return kimp, dom

def get_crypto_news():
    try: return feedparser.parse("https://news.google.com/rss/search?q=블록체인+OR+비트코인+when:1d&hl=ko&gl=KR&ceid=KR:ko").entries[:6]
    except: return []

def render_custom_metric(label, value, delta, pct):
    color, icon, sign, bg = ("#d60000", "▲", "+", "#fff0f0") if delta >= 0 else ("#0051c7", "▼", "", "#f0f6ff")
    st.markdown(f"""
    <div style="background-color: {bg}; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">{label}</div>
        <div style="color: #333; font-size: 1.8rem; font-weight: bold; margin-bottom: 5px;">{value}</div>
        <div style="color: {color}; font-size: 1rem; font-weight: bold;">{icon} {sign}{delta:,.2f} ({sign}{pct:.2f}%)</div>
    </div>""", unsafe_allow_html=True)

# --- 메인 컨텐츠 ---

# 1. 국제 증시
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    st.info(f"📊 현재 차트: **{st.session_state['selected_name']}**")
    render_highchart_global(st.session_state['selected_ticker'], st.session_state['selected_name'])
    st.markdown("---")
    st.markdown("<div style='text-align:right; margin-bottom:5px; font-size:0.85rem; color:#888;'>💡 종목명을 클릭하면 차트가 변경됩니다.</div>", unsafe_allow_html=True)
    
    market_items = [
        {"name": "비트코인", "ticker": "BTC-USD"},
        {"name": "나스닥", "ticker": "^IXIC"},
        {"name": "S&P 500", "ticker": "^GSPC"},
        {"name": "다우존스", "ticker": "^DJI"},
        {"name": "이더리움", "ticker": "ETH-USD"},
    ]
    
    # [모바일] 4열 강제 배치
    h_c1, h_c2, h_c3, h_c4 = st.columns([1.6, 0.8, 0.8, 0.8])
    h_c1.markdown("<div class='market-header'>종목명</div>", unsafe_allow_html=True)
    h_c2.markdown("<div class='market-header' style='text-align:right'>현재가</div>", unsafe_allow_html=True)
    h_c3.markdown("<div class='market-header' style='text-align:right'>등락률</div>", unsafe_allow_html=True)
    h_c4.markdown("<div class='market-header' style='text-align:right'>등락폭</div>", unsafe_allow_html=True)

    for item in market_items:
        price, rate, diff = 0, 0, 0
        try:
            hist = yf.Ticker(item['ticker']).history(period="5d")
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                diff = price - prev
                rate = (diff / prev) * 100
        except: pass
        
        color = "#d60000" if diff >= 0 else "#0051c7"
        sign = "+" if diff >= 0 else ""
        btn_label = f"▍ {item['name']}" if st.session_state['selected_ticker'] == item['ticker'] else f"\u00A0\u00A0\u00A0{item['name']}"
        
        c1, c2, c3, c4 = st.columns([1.6, 0.8, 0.8, 0.8])
        with c1:
            if st.button(btn_label, key=f"btn_{item['ticker']}", use_container_width=True): 
                st.session_state['selected_ticker'] = item['ticker']
                st.session_state['selected_name'] = item['name']
                st.rerun()
        with c2: st.markdown(f"<div class='data-cell' style='color:#333;'>{price:,.2f}</div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='data-cell' style='color:{color};'>{sign}{rate:.2f}%</div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='data-cell' style='color:{color};'>{sign}{diff:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div style='border-bottom: 1px solid #f0f0f0; margin-top: 0px;'></div>", unsafe_allow_html=True)

# 2. 암호 화폐
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    with st.spinner("시장 데이터 조회 중..."):
        kimp, dom = get_crypto_insight()
        news_list = get_crypto_news()
    ic1, ic2 = st.columns(2)
    with ic1:
        color = "#d60000" if kimp >= 0 else "#0051c7"
        st.markdown(f"""<div class="insight-box"><div class="insight-label">글로벌 시세 차이 (Kimchi Premium)</div><div class="insight-value" style="color: {color};">{kimp:.2f}%</div><div class="insight-sub">한국 시세가 해외보다 <b>{'비쌉니다' if kimp>=0 else '저렴합니다'}</b></div></div>""", unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""<div class="insight-box"><div class="insight-label">비트코인 점유율 (BTC Dominance)</div><div class="insight-value" style="color: #f7931a;">{dom:.1f}%</div><div class="insight-sub">전체 코인 시장 중 BTC 비중</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("📰 주요 블록체인 뉴스")
    for i in range(0, len(news_list), 2):
        nc = st.columns(2)
        for j in range(2):
            if i + j < len(news_list):
                entry = news_list[i+j]
                try: dt = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d %H:%M')
                except: dt = ""
                with nc[j]: st.markdown(f"""<div class="news-card"><a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a><div class="news-date">{dt} | {entry.source.title if 'source' in entry else 'News'}</div></div>""", unsafe_allow_html=True)

# 3. 국내 증시
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    with st.spinner("잠시만 기다려주세요... 실시간 데이터를 불러오는 중입니다."):
        try:
            kp_df = yf.download('^KS11', period='5d', progress=False)
            kq_df = yf.download('^KQ11', period='5d', progress=False)
            ex_df = yf.download('KRW=X', period='5d', progress=False)
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

st.markdown("<div style='text-align:center; color:#ccc; margin-top:50px; font-size:0.8rem;'>AJIN REPORT | Generated by AJIN PARTNERS</div>", unsafe_allow_html=True)