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

    /* 커스텀 하단 배너 (B안) */
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
       [2] 브리핑 리포트 스타일 (종이 질감 카드)
    ------------------------------------------------------------------- */
    .briefing-card {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-left: 5px solid #333; /* 전문가 느낌의 포인트 라인 */
        border-radius: 8px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        font-family: 'sans-serif';
    }
    .briefing-header {
        font-size: 1.4rem; font-weight: 900; color: #333; margin-bottom: 10px;
        border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;
    }
    .briefing-date { font-size: 0.9rem; color: #666; font-weight: normal; float: right; margin-top: 5px;}
    .briefing-section { margin-bottom: 15px; }
    .briefing-title { font-size: 1.1rem; font-weight: 800; color: #d60000; margin-bottom: 5px; }
    .briefing-text { font-size: 1rem; line-height: 1.6; color: #444; text-align: justify; }
    .briefing-highlight { background-color: #fff5f5; padding: 2px 5px; border-radius: 4px; font-weight: bold; color: #d60000; }
    
    /* -------------------------------------------------------------------
       [3] 기본 UI 및 칩 스타일
    ------------------------------------------------------------------- */
    div.row-widget.stRadio > div { flex-direction: row; align-items: center; flex-wrap: wrap !important; gap: 8px; padding-bottom: 5px; justify-content: flex-start; }
    div.row-widget.stRadio > div[role="radiogroup"] > label { background-color: #f0f2f6; padding: 8px 14px; border-radius: 20px; border: 1px solid #e0e0e0; cursor: pointer; transition: all 0.2s; margin-right: 0 !important; font-size: 0.9rem; color: #555; }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] { background-color: #d60000 !important; color: white !important; border-color: #d60000 !important; font-weight: bold; box-shadow: 0 2px 5px rgba(214,0,0,0.2); }
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child { display: none; }
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:last-child { margin-left: 0px; }

    .streamlit-expanderHeader p { font-size: 1.8rem !important; font-weight: 800 !important; color: #222 !important; }
    .title-text { text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; color: #000; }
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #f8f9fa; padding: 12px 0; margin-bottom: 20px; border-radius: 8px; white-space: nowrap; }
    .ticker-content { display: inline-block; animation: scroll 40s linear infinite; }
    .ticker-item { display: inline-block; padding: 0 2rem; font-size: 1.1rem; font-weight: bold; color: #333; }
    @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .up { color: #d60000; } .down { color: #0051c7; } 

    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: 'sans-serif'; font-size: 0.9rem; }
    .custom-table th { border-bottom: 2px solid #333; padding: 10px 5px; text-align: right; color: #333; font-weight: bold; }
    .custom-table td { border-bottom: 1px solid #eee; padding: 14px 5px; text-align: right; color: #333; font-weight: 500; }
    .custom-table th:first-child, .custom-table td:first-child { text-align: left; }
    
    .selected-row { background-color: #fff5f5; }
    .selected-text { color: #d60000; font-weight: 900; border-left: 4px solid #d60000; padding-left: 8px; display: inline-block; }

    @media (max-width: 600px) {
        .title-text { font-size: 2rem; }
        .custom-table th, .custom-table td { font-size: 0.8rem; padding: 12px 2px; }
        .block-container { padding-bottom: 100px !important; }
        .briefing-card { padding: 15px; }
        .briefing-header { font-size: 1.2rem; }
    }

    .insight-box { background-color: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #eee; margin-bottom: 10px; }
    .insight-label { font-size: 0.95rem; color: #666; margin-bottom: 5px; font-weight: 600;}
    .insight-value { font-size: 1.8rem; font-weight: 800; color: #333; }
    .news-card { background-color: white; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 12px; height: 100%; transition: transform 0.2s; }
    .news-card:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .news-title { font-weight: bold; font-size: 1rem; margin-bottom: 8px; color: #333; text-decoration: none; display: block; line-height: 1.4; }
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
<div style="display: flex; justify-content: center; margin-bottom: 25px;">
    <div style="background-color: #333; color: white; padding: 8px 25px; border-radius: 20px; font-weight: bold; font-size: 1rem; box-shadow: 0 3px 6px rgba(0,0,0,0.2);">
        {today_str}
    </div>
</div>
""", unsafe_allow_html=True)

# --- 스마트 브리핑 생성 함수 (Expert Logic) ---
def generate_market_briefing(market_data):
    # 1. 시장 상태 판단
    nas_chg = market_data.get('^IXIC', {}).get('pct', 0)
    spx_chg = market_data.get('^GSPC', {}).get('pct', 0)
    dji_chg = market_data.get('^DJI', {}).get('pct', 0)
    vix_val = market_data.get('^VIX', {}).get('price', 20)
    
    avg_chg = (nas_chg + spx_chg + dji_chg) / 3
    
    # 키워드 생성
    market_mood = ""
    if avg_chg > 1.0: market_mood = "강력한 상승세(Bullish Rally)"
    elif avg_chg > 0.2: market_mood = "견조한 상승(Modest Gain)"
    elif avg_chg > -0.2: market_mood = "보합권 혼조세(Mixed/Flat)"
    elif avg_chg > -1.0: market_mood = "조정 및 차익실현(Correction)"
    else: market_mood = "약세장 및 하락 압력(Bearish)"

    vix_comment = ""
    if vix_val < 15: vix_comment = "투자 심리가 매우 안정적이며 위험 선호 현상이 뚜렷합니다."
    elif vix_val < 20: vix_comment = "시장의 변동성은 안정적인 수준을 유지하고 있습니다."
    elif vix_val < 30: vix_comment = "시장 불확실성이 다소 확대되며 변동성 관리가 필요해 보입니다."
    else: vix_comment = "극심한 공포 심리가 시장을 지배하며 변동성이 확대되었습니다."

    # 2. 자산군 분석
    btc_chg = market_data.get('BTC-USD', {}).get('pct', 0)
    gold_chg = market_data.get('GC=F', {}).get('pct', 0)
    
    asset_comment = ""
    if btc_chg > 1.0 and nas_chg > 0.5:
        asset_comment = "비트코인은 기술주(나스닥)와 강한 동조화(Coupling)를 보이며 위험 자산 선호 심리를 주도했습니다."
    elif btc_chg > 0 and nas_chg < 0:
        asset_comment = "비트코인은 증시 하락에도 불구하고 독자적인 상승세를 보이며 디커플링(Decoupling) 움직임을 나타냈습니다."
    elif gold_chg > 0.5 and avg_chg < 0:
        asset_comment = "증시 약세 속에 금(Gold)이 강세를 보이며 안전 자산으로의 자금 이동(Flight to Quality)이 관측되었습니다."
    else:
        asset_comment = f"비트코인은 전일 대비 {btc_chg:+.2f}% 변동하며 시장 흐름을 주시하고 있습니다."

    # 3. 브리핑 텍스트 조립
    briefing_html = f"""
    <div class="briefing-card">
        <div class="briefing-header">
            ☕ 아침 7시 마켓 브리핑
            <span class="briefing-date">{today_str} 기준</span>
        </div>
        
        <div class="briefing-section">
            <div class="briefing-title">1. 글로벌 시장 전반 (Overview)</div>
            <div class="briefing-text">
                간밤 뉴욕 증시는 <span class="briefing-highlight">{market_mood}</span>로 마감했습니다. 
                3대 지수의 평균 등락률은 약 {avg_chg:+.2f}%를 기록했습니다. 
                변동성 지수(VIX)는 {vix_val:.2f}를 기록하며, {vix_comment}
            </div>
        </div>

        <div class="briefing-section">
            <div class="briefing-title">2. 자산군별 흐름 (Asset Flow)</div>
            <div class="briefing-text">
                {asset_comment} 
                특히 기술주 중심의 나스닥은 {nas_chg:+.2f}%, 전통 산업 중심의 다우존스는 {dji_chg:+.2f}%의 등락을 보이며 섹터별 차별화 장세가 나타났습니다.
            </div>
        </div>

        <div class="briefing-section">
            <div class="briefing-title">3. 종합 전문가 의견 (Conclusion)</div>
            <div class="briefing-text">
                현재 시장은 {'모든 이평선 상단에 위치한 강세 국면' if avg_chg > 0 else '단기 저항선 돌파를 시도하는 국면'}으로 판단됩니다. 
                거시 경제 이슈와 뉴스 플로우에 따라 변동성이 발생할 수 있으므로, 추격 매수보다는 
                {'조정 시 분할 매수' if avg_chg > 0 else '보수적인 리스크 관리'} 관점의 대응이 유효해 보입니다.
            </div>
        </div>
    </div>
    """
    return briefing_html

# --- 데이터 수집 및 전처리 ---
def get_all_market_data():
    tickers = {
        "^IXIC": "나스닥", "^GSPC": "S&P 500", "^DJI": "다우존스",
        "BTC-USD": "비트코인", "GC=F": "금", "SI=F": "은", "CL=F": "원유", "^VIX": "VIX"
    }
    data_storage = {}
    
    # 한번에 다운로드하여 속도 향상
    ticker_str = " ".join(list(tickers.keys()))
    try:
        df = yf.download(ticker_str, period="2d", progress=False)['Close']
        # 멀티인덱스 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1) # Ticker만 남김 (이름이 아닌 심볼)
            
        for t in tickers.keys():
            try:
                # yfinance 다운로드 데이터 구조에 따라 컬럼 접근
                # 보통 df[ticker] 형태임. 최신버전 yfinance 확인 필요
                # 여기서는 안전하게 개별 처리 로직을 사용하지 않고 배치 처리된 df에서 추출
                series = df[t].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    data_storage[t] = {'price': curr, 'pct': pct}
                elif len(series) == 1:
                    data_storage[t] = {'price': series.iloc[-1], 'pct': 0.0}
                else:
                    data_storage[t] = {'price': 0.0, 'pct': 0.0}
            except:
                data_storage[t] = {'price': 0.0, 'pct': 0.0}
    except:
        pass
        
    return data_storage

# 전광판용 데이터 (HTML)
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

with st.spinner("시장 데이터 동기화 및 분석 중..."):
    # 1. 전체 데이터 수집 (브리핑용)
    market_data_all = get_all_market_data()
    # 2. 전광판 데이터 수집
    live_ticker_items = get_ticker_html_data()

st.markdown(f"""<div class="ticker-wrap"><div class="ticker-content">{live_ticker_items}</div></div>""", unsafe_allow_html=True)

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
            ts = int(row['Date'].timestamp() * 1000)
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
        res = requests.get("https://api.coinlore.net/api/global/", timeout=2).json()
        dom = float(res[0]['btc_d'])
    except: pass
    return kimp, dom

def get_crypto_news():
    try: return feedparser.parse("https://www.blockmedia.co.kr/archives/category/market/digital-asset/feed").entries[:8]
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

market_items = [
    {"name": "🪙 비트코인", "ticker": "BTC-USD"},
    {"name": "💲 나스닥", "ticker": "^IXIC"},
    {"name": "📈 S&P 500", "ticker": "^GSPC"},
    {"name": "🏛️ 다우존스", "ticker": "^DJI"},
    {"name": "🟡 금", "ticker": "GC=F"},
    {"name": "⚪ 은", "ticker": "SI=F"},
    {"name": "⚫ 원유", "ticker": "CL=F"},
]

# 1. 국제 증시
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    
    # [1] 상단 칩(Chip) UI
    options = [item["name"] for item in market_items]
    current_name = st.session_state['selected_name']
    
    if current_name not in options:
         current_name = options[0]
         st.session_state['selected_name'] = current_name
         st.session_state['selected_ticker'] = market_items[0]['ticker']

    selected_chip = st.radio(
        "차트 선택",
        options,
        index=options.index(current_name),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if selected_chip != st.session_state['selected_name']:
        st.session_state['selected_name'] = selected_chip
        for item in market_items:
            if item["name"] == selected_chip:
                st.session_state['selected_ticker'] = item['ticker']
                st.rerun()

    # [2] 차트 렌더링
    st.info(f"📊 현재 차트: **{st.session_state['selected_name']}**")
    render_highchart_global(st.session_state['selected_ticker'], st.session_state['selected_name'])
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # [NEW] 스마트 브리핑 리포트 출력 (차트 아래, 리스트 위)
    briefing_html = generate_market_briefing(market_data_all)
    st.markdown(briefing_html, unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:right; margin-bottom:10px; font-size:0.8rem; color:#666;'>💡 위 버튼을 누르면 차트가 변경됩니다.</div>", unsafe_allow_html=True)
    
    # [3] 시세 리스트
    html_rows = ""
    for item in market_items:
        # 미리 수집한 market_data_all 사용 (속도 향상)
        t_data = market_data_all.get(item['ticker'], {'price': 0, 'pct': 0})
        price = t_data['price']
        rate = t_data['pct']
        
        # 등락폭(Diff)은 따로 계산 필요 (여기서는 pct 역산 또는 0 처리, yfinance 호출 최소화 위해 pct만 사용해도 무방하나 정확도를 위해 개별호출 유지 혹은 로직 변경 가능)
        # 기존 로직 유지 (정확도 우선)
        diff = 0
        try:
             # 브리핑용 데이터와 별개로 리스트용 정확한 데이터 재호출 (안전성)
             # 속도가 느리다면 market_data_all에서 prev 계산 로직 추가 필요
             hist = yf.Ticker(item['ticker']).history(period="5d")
             if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
                diff = price - prev
                rate = (diff / prev) * 100
        except: pass
        
        color = "#d60000" if diff >= 0 else "#0051c7"
        sign = "+" if diff >= 0 else ""
        
        if st.session_state['selected_ticker'] == item['ticker']:
            row_class = "selected-row"
            name_cell = f"<span class='selected-text'>{item['name']}</span>"
        else:
            row_class = ""
            name_cell = item['name']
        
        html_rows += f"<tr class='{row_class}'><td>{name_cell}</td><td>{price:,.2f}</td><td style='color:{color}'>{sign}{rate:.2f}%</td><td style='color:{color}'>{sign}{diff:,.2f}</td></tr>"

    full_table_html = f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>종목명</th>
                <th>현재가</th>
                <th>등락률</th>
                <th>등락폭</th>
            </tr>
        </thead>
        <tbody>
            {html_rows}
        </tbody>
    </table>
    """
    st.markdown(full_table_html, unsafe_allow_html=True)


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
    st.subheader("📰 주요 코인 뉴스")
    for i in range(0, len(news_list), 2):
        nc = st.columns(2)
        for j in range(2):
            if i + j < len(news_list):
                entry = news_list[i+j]
                dt_str = ""
                try:
                    if hasattr(entry, 'published_parsed'):
                        dt_utc = datetime(*entry.published_parsed[:6])
                        dt_kst = dt_utc + timedelta(hours=9)
                        dt_str = dt_kst.strftime('%Y-%m-%d %H:%M')
                except: pass
                
                with nc[j]: 
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a>
                        <div class="news-date">{dt_str} | BlockMedia</div>
                    </div>""", unsafe_allow_html=True)

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

st.markdown("""
<div class="custom-footer">
    <div class="footer-content">
        <div class="footer-main">Financial Report</div>
        <div class="footer-sub">- by Ajin Partners</div>
    </div>
    <a href="tel:010-0000-0000" class="footer-btn">📞 문의하기</a>
</div>
""", unsafe_allow_html=True)