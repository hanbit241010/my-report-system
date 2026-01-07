import streamlit as st
import streamlit.components.v1 as components
import FinanceDataReader as fdr
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
    /* 헤더/푸터 숨김 */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .stDeployButton { display: none !important; }
    
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

    /* 국제 증시 리스트 헤더 */
    .market-header {
        font-weight: bold; border-bottom: 2px solid #555; padding: 10px 5px; color: #333; font-size: 1rem;
    }

    /* 버튼 스타일 (리스트 아이템화) */
    div.stButton > button {
        width: 100%;
        border: none;
        background-color: transparent;
        color: #333;
        text-align: left;
        padding: 12px 2px;
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0;
        line-height: 1.2;
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div.stButton > button:hover {
        background-color: #f9f9f9;
        color: #d60000;
    }
    div.stButton > button:focus {
        box-shadow: none;
        color: #d60000;
    }

    /* 수치 데이터 셀 정렬용 */
    .data-cell {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        height: 48px;
        font-weight: bold;
        font-size: 1rem;
        white-space: nowrap;
    }
    
    /* [모바일 최적화] */
    @media (max-width: 600px) {
        .market-header { font-size: 0.85rem !important; padding: 10px 2px; }
        div.stButton > button { font-size: 0.9rem !important; padding: 12px 0; }
        .data-cell { font-size: 0.85rem !important; }
        .streamlit-expanderHeader p { font-size: 1.8rem !important; }
        .title-text { font-size: 2rem; }
    }
    
    /* 암호화폐 카드 스타일 */
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

# [수정] 날짜 및 주차 계산 (ISO 달력 기준)
now = datetime.now()
date_part = now.strftime("%Y. %m. %d")
week_num = now.isocalendar()[1] # ISO 기준 주차 사용 (1월 7일 -> Week 02)
today_str = f"{date_part} (Week {week_num:02d})"

date_html = f"""
<div style="display: flex; justify-content: center; margin-bottom: 20px;">
    <div style="background-color: #333; color: white; padding: 8px 25px; border-radius: 20px; font-weight: bold; font-size: 1rem; box-shadow: 0 3px 6px rgba(0,0,0,0.2);">
        {today_str}
    </div>
</div>
"""
st.markdown(date_html, unsafe_allow_html=True)

# 5. 상단 전광판
ticker_html = """
<div class="ticker-wrap">
    <div class="ticker-content">
        <span class="ticker-item">나스닥 14,500.50 <span class="down">(-0.16%)</span></span>
        <span class="ticker-item">원/달러 1,446.35 <span class="up">(+0.41%)</span></span>
        <span class="ticker-item">비트코인 134,826,448 <span class="down">(-0.72%)</span></span>
        <span class="ticker-item">코스피 4,525.48 <span class="up">(+1.52%)</span></span>
        <span class="ticker-item">코스닥 955.97 <span class="down">(-0.16%)</span></span>
    </div>
</div>
"""
st.markdown(ticker_html, unsafe_allow_html=True)

# --- 함수 모음 ---

def render_highchart_global(ticker, name, height=400):
    try:
        # [수정] 1Y 버튼 활성화를 위해 데이터 조회 기간을 2년(2y)으로 늘림
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df.reset_index()

        ohlc = []
        volume = []
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
        
        # [수정] 워터마크 위치 상단 40%로 조정 (height * 0.4)
        html_code = f"""
        <html>
        <head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;">
            <div id="chart_global" style="height: {height}px; width: 100%;"></div>
            <script>
                Highcharts.setOptions({{ lang: {{ thousandsSep: ',' }} }});
                Highcharts.stockChart('chart_global', {{
                    rangeSelector: {{
                        enabled: true,
                        selected: 1, inputEnabled: false,
                        buttons: [
                            {{ type: 'month', count: 1, text: '1M' }},
                            {{ type: 'month', count: 3, text: '3M' }},
                            {{ type: 'month', count: 6, text: '6M' }},
                            {{ type: 'ytd', text: 'YTD' }},
                            {{ type: 'year', count: 1, text: '1Y' }}
                        ]
                    }},
                    navigator: {{ enabled: true, height: 30 }},
                    scrollbar: {{ enabled: false }},
                    credits: {{ enabled: false }},
                    chart: {{ 
                        backgroundColor: '#ffffff',
                        events: {{
                            render: function() {{
                                var chart = this;
                                var width = chart.plotWidth;
                                var height = chart.plotHeight;
                                
                                var x = chart.plotLeft + width / 2;
                                var y = chart.plotTop + height * 0.4; // [수정] 상단 40% 지점
                                var fontSize = Math.min(width / 15, 50);
                                
                                if (!chart.watermark) {{
                                    chart.watermark = chart.renderer.text('AJIN PARTNERS', x, y)
                                        .css({{
                                            color: '#E0E0E0',
                                            fontWeight: '900',
                                            opacity: 0.6
                                        }})
                                        .attr({{
                                            align: 'center',
                                            zIndex: 0
                                        }})
                                        .add();
                                }}
                                chart.watermark.attr({{ x: x, y: y }}).css({{ fontSize: fontSize + 'px' }});
                            }}
                        }}
                    }},
                    yAxis: [{{
                        labels: {{ align: 'right', x: -3 }},
                        height: '75%', lineWidth: 2, resize: {{ enabled: true }}
                    }}, {{
                        labels: {{ align: 'right', x: -3 }},
                        top: '75%', height: '25%', offset: 0, lineWidth: 2
                    }}],
                    tooltip: {{ split: true }},
                    plotOptions: {{
                        candlestick: {{ color: '#0051c7', upColor: '#d60000', lineColor: '#0051c7', upLineColor: '#d60000' }}
                    }},
                    series: [{{
                        type: 'candlestick', name: '{name}', data: {ohlc_json}
                    }}, {{
                        type: 'column', name: 'Volume', data: {vol_json}, yAxis: 1, color: 'rgba(0,0,0,0.1)'
                    }}]
                }});
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=height+20)
    except:
        st.error("차트 오류")

def render_highchart_domestic(ticker, name, height=450):
    try:
        df = fdr.DataReader(ticker, '2024-01-01')
        df = df.reset_index()
        ohlc = []
        volume = []
        for idx, row in df.iterrows():
            ts = int(row['Date'].timestamp() * 1000)
            ohlc.append([ts, row['Open'], row['High'], row['Low'], row['Close']])
            vol = row['Volume'] if pd.notnull(row['Volume']) else 0
            volume.append([ts, vol])
        ohlc_json = json.dumps(ohlc)
        vol_json = json.dumps(volume)
        
        # [수정] 국내 증시 차트에도 워터마크 위치 40% 적용
        html_code = f"""
        <html>
        <head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;">
            <div id="chart_{ticker}" style="height: {height}px; width: 100%;"></div>
            <script>
                Highcharts.setOptions({{ lang: {{ thousandsSep: ',' }} }});
                Highcharts.stockChart('chart_{ticker}', {{
                    rangeSelector: {{
                        selected: 1, inputEnabled: false,
                        buttons: [{{ type: 'month', count: 1, text: '1M' }}, {{ type: 'month', count: 3, text: '3M' }}, {{ type: 'month', count: 6, text: '6M' }}, {{ type: 'ytd', text: 'YTD' }}, {{ type: 'year', count: 1, text: '1Y' }}]
                    }},
                    navigator: {{ enabled: true, height: 30 }},
                    scrollbar: {{ enabled: false }},
                    credits: {{ enabled: false }},
                    chart: {{ 
                        backgroundColor: '#ffffff',
                        events: {{
                            render: function() {{
                                var chart = this;
                                var width = chart.plotWidth;
                                var height = chart.plotHeight;
                                
                                var x = chart.plotLeft + width / 2;
                                var y = chart.plotTop + height * 0.4; // [수정] 상단 40% 지점
                                var fontSize = Math.min(width / 15, 50);
                                
                                if (!chart.watermark) {{
                                    chart.watermark = chart.renderer.text('AJIN PARTNERS', x, y)
                                        .css({{
                                            color: '#E0E0E0',
                                            fontWeight: '900',
                                            opacity: 0.6
                                        }})
                                        .attr({{
                                            align: 'center',
                                            zIndex: 0
                                        }})
                                        .add();
                                }}
                                chart.watermark.attr({{ x: x, y: y }}).css({{ fontSize: fontSize + 'px' }});
                            }}
                        }}
                    }},
                    yAxis: [{{
                        labels: {{ align: 'right', x: -3 }},
                        height: '75%', lineWidth: 2, resize: {{ enabled: true }}
                    }}, {{
                        labels: {{ align: 'right', x: -3 }},
                        top: '75%', height: '25%', offset: 0, lineWidth: 2
                    }}],
                    tooltip: {{ split: true }},
                    plotOptions: {{
                        candlestick: {{ color: '#0051c7', upColor: '#d60000', lineColor: '#0051c7', upLineColor: '#d60000' }}
                    }},
                    series: [{{
                        type: 'candlestick', name: '{name}', data: {ohlc_json}
                    }}, {{
                        type: 'column', name: 'Volume', data: {vol_json}, yAxis: 1, color: 'rgba(0,0,0,0.1)'
                    }}]
                }});
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=height+20)
    except Exception as e:
        st.error(f"차트 로딩 실패: {e}")

def get_crypto_insight():
    kimp_rate, btc_dominance = 0.0, 0.0
    try:
        usd_krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        binance_btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", timeout=3).json()
        bithumb_btc = float(res['data']['closing_price'])
        global_price = binance_btc * usd_krw
        if global_price > 0:
            kimp_rate = ((bithumb_btc - global_price) / global_price) * 100
    except: pass
    try:
        cg_res = requests.get("https://api.coingecko.com/api/v3/global", timeout=3).json()
        btc_dominance = cg_res['data']['market_cap_percentage']['btc']
    except: pass
    return kimp_rate, btc_dominance

def get_crypto_news():
    try:
        feed = feedparser.parse("https://news.google.com/rss/search?q=블록체인+OR+비트코인+when:1d&hl=ko&gl=KR&ceid=KR:ko")
        return feed.entries[:6]
    except: return []

def render_custom_metric(label, value, delta, pct):
    if delta >= 0:
        bg_color = "#fff0f0"
        text_color = "#d60000"
        sign = "+"
        icon = "▲"
    else:
        bg_color = "#f0f6ff"
        text_color = "#0051c7"
        sign = ""
        icon = "▼"
    html = f"""
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <div style="color: #666; font-size: 0.9rem; margin-bottom: 5px;">{label}</div>
        <div style="color: #333; font-size: 1.8rem; font-weight: bold; margin-bottom: 5px;">{value}</div>
        <div style="color: {text_color}; font-size: 1rem; font-weight: bold;">
            {icon} {sign}{delta:,.2f} ({sign}{pct:.2f}%)
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- 메인 컨텐츠 ---

# 1. 국제 증시
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    st.info(f"📊 현재 차트: **{st.session_state['selected_name']}**")
    render_highchart_global(st.session_state['selected_ticker'], st.session_state['selected_name'])
    st.markdown("---")
    
    st.markdown("""
        <div style='text-align:right; margin-bottom:5px; font-size:0.85rem; color:#888;'>
            💡 종목명을 클릭하면 차트가 변경됩니다.
        </div>
    """, unsafe_allow_html=True)
    
    market_items = [
        {"name": "비트코인", "ticker": "BTC-USD"},
        {"name": "나스닥", "ticker": "^IXIC"},
        {"name": "S&P 500", "ticker": "^GSPC"},
        {"name": "다우존스", "ticker": "^DJI"},
        {"name": "이더리움", "ticker": "ETH-USD"},
    ]
    
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
        
        is_selected = (st.session_state['selected_ticker'] == item['ticker'])
        
        if is_selected:
            btn_label = f"▍ {item['name']}"
        else:
            btn_label = f"\u00A0\u00A0\u00A0{item['name']}"
        
        c1, c2, c3, c4 = st.columns([1.6, 0.8, 0.8, 0.8])
        
        with c1:
            if st.button(btn_label, key=f"btn_{item['ticker']}", use_container_width=True): 
                st.session_state['selected_ticker'] = item['ticker']
                st.session_state['selected_name'] = item['name']
                st.rerun()

        with c2:
            st.markdown(f"<div class='data-cell' style='color:#333;'>{price:,.2f}</div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='data-cell' style='color:{color};'>{sign}{rate:.2f}%</div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='data-cell' style='color:{color};'>{sign}{diff:,.2f}</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='border-bottom: 1px solid #f0f0f0; margin-top: 0px;'></div>", unsafe_allow_html=True)


# 2. 암호 화폐
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    with st.spinner("시장 데이터 조회 중..."):
        kimp, dom = get_crypto_insight()
        news_list = get_crypto_news()
    
    ic1, ic2 = st.columns(2)
    with ic1:
        color = "#d60000" if kimp >= 0 else "#0051c7"
        st.markdown(f"""
            <div class="insight-box">
                <div class="insight-label">글로벌 시세 차이 (Kimchi Premium)</div>
                <div class="insight-value" style="color: {color};">{kimp:.2f}%</div>
                <div class="insight-sub">한국 시세가 해외보다 <b>{'비쌉니다' if kimp>=0 else '저렴합니다'}</b></div>
            </div>
        """, unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""
            <div class="insight-box">
                <div class="insight-label">비트코인 점유율 (BTC Dominance)</div>
                <div class="insight-value" style="color: #f7931a;">{dom:.1f}%</div>
                <div class="insight-sub">전체 코인 시장 중 BTC 비중</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📰 주요 블록체인 뉴스")
    for i in range(0, len(news_list), 2):
        nc = st.columns(2)
        for j in range(2):
            if i + j < len(news_list):
                entry = news_list[i+j]
                try: dt = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d %H:%M')
                except: dt = ""
                with nc[j]:
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a>
                        <div class="news-date">{dt} | {entry.source.title if 'source' in entry else 'News'}</div>
                    </div>
                    """, unsafe_allow_html=True)


# 3. 국내 증시
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    
    with st.spinner("잠시만 기다려주세요... 실시간 데이터를 불러오는 중입니다."):
        try:
            kp_df = fdr.DataReader('KS11', '2025-01-01')
            kq_df = fdr.DataReader('KQ11', '2025-01-01')
            ex_df = fdr.DataReader('USD/KRW', '2025-01-01')
            
            kp_now = kp_df.iloc[-1]['Close']
            kp_prev = kp_df.iloc[-2]['Close']
            kp_delta = kp_now - kp_prev
            kp_pct = (kp_delta / kp_prev) * 100
            
            kq_now = kq_df.iloc[-1]['Close']
            kq_prev = kq_df.iloc[-2]['Close']
            kq_delta = kq_now - kq_prev
            kq_pct = (kq_delta / kq_prev) * 100
            
            ex_now = ex_df.iloc[-1]['Close']
            ex_prev = ex_df.iloc[-2]['Close']
            ex_delta = ex_now - ex_prev
            ex_pct = (ex_delta / ex_prev) * 100
            
        except Exception as e:
            kp_now, kp_delta, kp_pct = 0.0, 0.0, 0.0
            kq_now, kq_delta, kq_pct = 0.0, 0.0, 0.0
            ex_now, ex_delta, ex_pct = 0.0, 0.0, 0.0

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

# 푸터
st.markdown("<div style='text-align:center; color:#ccc; margin-top:50px; font-size:0.8rem;'>AJIN REPORT | Generated by AJIN PARTNERS</div>", unsafe_allow_html=True)