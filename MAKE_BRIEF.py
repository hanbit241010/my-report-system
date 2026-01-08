import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime, timedelta
import json
import time

# ==========================================
# 1. 페이지 설정 및 스타일 (수정 없음, 디자인 유지)
# ==========================================
st.set_page_config(page_title="AJIN REPORT", layout="wide")

st.markdown("""
    <style>
    /* 기본 UI 숨김 */
    header[data-testid="stHeader"], footer { display: none !important; }
    [data-testid="stToolbar"], [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stManageAppButton"] { display: none !important; }

    /* 커스텀 하단 배너 */
    .custom-footer {
        position: fixed; bottom: 0; left: 0; width: 100%; height: 70px;
        background-color: #ffffff; border-top: 1px solid #e0e0e0;
        padding: 0 20px; z-index: 999999; display: flex; align-items: center; justify-content: space-between;
    }
    .footer-main { font-size: 1.1rem; font-weight: 900; color: #333; }
    .footer-btn {
        background-color: #d60000; color: white !important; padding: 8px 16px;
        border-radius: 20px; font-size: 0.85rem; font-weight: bold; text-decoration: none;
    }

    /* 브리핑 카드 */
    .briefing-card {
        background-color: #ffffff; border: 1px solid #ddd; border-left: 5px solid #000;
        border-radius: 4px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .briefing-header { font-size: 1.3rem; font-weight: 900; color: #000; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
    .briefing-text { font-size: 1rem; line-height: 1.7; color: #333; text-align: justify; }
    .highlight { background-color: #fff9c4; font-weight: bold; padding: 2px 4px; border-radius: 4px; }

    /* 히트맵 */
    .heat-container { width: 100%; background-color: #f0f0f0; border-radius: 4px; height: 10px; margin-top: 5px; overflow: hidden; }
    .heat-fill { height: 100%; border-radius: 4px; }
    .theme-tag { font-size: 0.75rem; background-color: #f1f3f5; color: #555; padding: 2px 6px; border-radius: 4px; margin-left: 5px; }

    /* 테이블 */
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
    .custom-table th { border-bottom: 2px solid #333; padding: 10px 5px; text-align: right; }
    .custom-table td { border-bottom: 1px solid #eee; padding: 12px 5px; text-align: right; }
    .selected-row { background-color: #fff5f5; font-weight: bold; color: #d60000; }
    
    /* 칩 버튼 */
    div.row-widget.stRadio > div { flex-direction: row; flex-wrap: wrap !important; gap: 8px; }
    div.row-widget.stRadio > div[role="radiogroup"] > label { background-color: #f0f2f6; padding: 6px 14px; border-radius: 20px; border: 1px solid #e0e0e0; }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] { background-color: #d60000 !important; color: white !important; border-color: #d60000 !important; }
    
    @media (max-width: 600px) { .block-container { padding-bottom: 100px !important; } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 안전한 데이터 수집 함수 (Sequential Safe Fetch)
# ==========================================

def safe_get_price(ticker):
    """
    단일 종목의 현재가와 등락률을 안전하게 가져오는 함수
    에러가 발생하면 0, 0을 반환하여 앱이 죽는 것을 방지함
    """
    try:
        t = yf.Ticker(ticker)
        # period='2d'로 최소한의 데이터만 요청
        hist = t.history(period="2d")
        if len(hist) >= 2:
            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            pct = ((price - prev) / prev) * 100
            change = price - prev
            return price, pct, change
        elif len(hist) == 1:
            return hist['Close'].iloc[-1], 0.0, 0.0
        return 0.0, 0.0, 0.0
    except:
        return 0.0, 0.0, 0.0

@st.cache_data(ttl=600)
def get_nasdaq_analysis():
    """
    나스닥 주요 종목을 하나씩 조회하여 안전하게 리스트를 만듦
    """
    # 주요 종목 리스트 (안정성을 위해 40여개 주요 종목으로 구성)
    target_tickers = [
        ("NVDA", "AI반도체"), ("AAPL", "모바일"), ("MSFT", "SW"), ("AMZN", "이커머스"), 
        ("META", "SNS"), ("GOOGL", "검색"), ("TSLA", "전기차"), ("AVGO", "통신"), 
        ("NFLX", "OTT"), ("AMD", "반도체"), ("QCOM", "통신"), ("INTC", "반도체"), 
        ("PEP", "식음료"), ("COST", "유통"), ("SBUX", "식음료"), ("AMGN", "바이오"), 
        ("GILD", "바이오"), ("TXN", "반도체"), ("ADBE", "SW"), ("PYPL", "결제"), 
        ("CSCO", "네트워크"), ("CMCSA", "미디어"), ("TMUS", "통신"), ("INTU", "핀테크"), 
        ("MDLZ", "식음료"), ("ISRG", "의료기기"), ("LRCX", "장비"), ("MU", "메모리"), 
        ("ADI", "반도체"), ("REGN", "바이오"), ("VRTX", "바이오"), ("PANW", "보안"), 
        ("SNPS", "SW"), ("CDNS", "SW"), ("KLAC", "장비"), ("MAR", "호텔"), 
        ("ABNB", "여행"), ("ORLY", "유통")
    ]
    
    results = []
    
    # 하나씩 순차적으로 가져옴 (속도는 느려도 가장 안전함)
    for ticker, theme in target_tickers:
        p, pct, chg = safe_get_price(ticker)
        if p != 0: # 데이터가 있는 경우만 추가
            results.append({"ticker": ticker, "pct": pct, "theme": theme})
    
    # 정렬
    sorted_data = sorted(results, key=lambda x: x['pct'], reverse=True)
    # 데이터가 부족할 경우를 대비해 슬라이싱 안전처리
    top_5 = sorted_data[:10] if len(sorted_data) >= 10 else sorted_data
    bot_5 = sorted_data[-10:] if len(sorted_data) >= 10 else []
    
    return top_5, bot_5

def get_briefing_metrics():
    """브리핑용 지표 수집"""
    # 역시 안전하게 하나씩
    nas_p, nas_pct, _ = safe_get_price("^IXIC")
    spx_p, spx_pct, _ = safe_get_price("^GSPC")
    dji_p, dji_pct, _ = safe_get_price("^DJI")
    vix_p, _, _ = safe_get_price("^VIX")
    tnx_p, tnx_pct, _ = safe_get_price("^TNX")
    
    return {
        "nas_pct": nas_pct,
        "spx_pct": spx_pct,
        "dji_pct": dji_pct,
        "vix": vix_p,
        "tnx": tnx_p,
        "tnx_pct": tnx_pct
    }

def get_crypto_safe():
    kimp, dom = 0.0, 0.0
    news_items = []
    try:
        # 김프
        btc_krw_res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", timeout=3).json()
        btc_krw = float(btc_krw_res['data']['closing_price'])
        
        p, _, _ = safe_get_price("BTC-USD")
        ex, _, _ = safe_get_price("KRW=X")
        
        if p > 0 and ex > 0:
            kimp = ((btc_krw - (p * ex)) / (p * ex)) * 100
    except: pass
    
    try:
        # 도미넌스
        res = requests.get("https://api.coinlore.net/api/global/", timeout=3).json()
        dom = float(res[0]['btc_d'])
    except: pass
    
    try:
        # 뉴스 10개 (블록미디어)
        rss_url = "https://www.blockmedia.co.kr/archives/category/market/digital-asset/feed"
        feed = feedparser.parse(rss_url)
        news_items = feed.entries[:10]
    except: pass
    
    return kimp, dom, news_items

def render_highchart_safe(ticker, name):
    """차트 렌더링 - 데이터 없으면 메시지 표시"""
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            st.warning(f"{name} 차트 데이터를 불러올 수 없습니다.")
            return

        # 멀티인덱스 컬럼 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.reset_index()
        
        # 타임스탬프 변환 (필수)
        ohlc = []
        for _, row in df.iterrows():
            ts = int(row['Date'].timestamp() * 1000)
            ohlc.append([ts, float(row['Open']), float(row['High']), float(row['Low']), float(row['Close'])])
            
        ohlc_json = json.dumps(ohlc)
        
        html = f"""
        <html><head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;"><div id="c" style="height:350px;"></div><script>
        Highcharts.stockChart('c', {{
            rangeSelector:{{selected:1}}, navigator:{{enabled:false}}, scrollbar:{{enabled:false}}, credits:{{enabled:false}},
            series:[{{type:'candlestick', name:'{name}', data:{ohlc_json}, color:'#0051c7', upColor:'#d60000', lineColor:'#0051c7', upLineColor:'#d60000'}}]
        }});
        </script></body></html>"""
        components.html(html, height=360)
    except:
        st.error(f"{name} 차트 로딩 실패")

# ==========================================
# 3. UI 구성 (Layout)
# ==========================================

now = datetime.now()
st.markdown(f"<div style='text-align:center; font-size:2.2rem; font-weight:900;'>📈 AJIN REPORT</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><span style='background:#333; color:white; padding:5px 20px; border-radius:20px; font-weight:bold;'>{now.strftime('%Y. %m. %d')} (Week {now.isocalendar()[1]:02d})</span></div>", unsafe_allow_html=True)

# 데이터 로딩 (여기서만 스피너 사용)
with st.spinner("데이터를 안전하게 불러오는 중입니다..."):
    nas_top, nas_bot = get_nasdaq_analysis()
    brief_metrics = get_briefing_metrics()
    kimp, dom, c_news = get_crypto_safe()

# ----------------------------------------------------------------
# [1] 국제 증시 (International)
# ----------------------------------------------------------------
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    # 아이템 정의
    intl_items = [
        ("🪙 비트코인", "BTC-USD"), ("💲 나스닥", "^IXIC"), ("📈 S&P 500", "^GSPC"),
        ("🏛️ 다우존스", "^DJI"), ("🟡 금", "GC=F"), ("⚪ 은", "SI=F"), ("⚫ 원유", "CL=F")
    ]
    
    # 세션 상태 관리
    if 'selected_ticker' not in st.session_state: st.session_state['selected_ticker'] = intl_items[0][1]
    if 'selected_name' not in st.session_state: st.session_state['selected_name'] = intl_items[0][0]
    
    # 칩 버튼
    labels = [i[0] for i in intl_items]
    current_idx = 0
    if st.session_state['selected_name'] in labels:
        current_idx = labels.index(st.session_state['selected_name'])
        
    choice = st.radio("차트 선택", labels, horizontal=True, label_visibility="collapsed", index=current_idx)
    
    # 선택 변경 처리
    if choice != st.session_state['selected_name']:
        st.session_state['selected_name'] = choice
        for name, ticker in intl_items:
            if name == choice:
                st.session_state['selected_ticker'] = ticker
        st.rerun()

    # 차트
    render_highchart_safe(st.session_state['selected_ticker'], st.session_state['selected_name'])

    # 리스트 (표) - 안전하게 하나씩
    table_html = ""
    for name, ticker in intl_items:
        p, pct, chg = safe_get_price(ticker)
        
        color = "#d60000" if chg >= 0 else "#0051c7"
        sign = "+" if chg >= 0 else ""
        bg_cls = "class='selected-row'" if ticker == st.session_state['selected_ticker'] else ""
        
        table_html += f"""
        <tr {bg_cls}>
            <td style="text-align:left;">{name}</td>
            <td>{p:,.2f}</td>
            <td style="color:{color}">{sign}{pct:.2f}%</td>
            <td style="color:{color}">{sign}{chg:,.2f}</td>
        </tr>
        """
    st.markdown(f"""<table class="custom-table"><thead><tr><th style="text-align:left;">종목</th><th>현재가</th><th>등락률</th><th>등락폭</th></tr></thead><tbody>{table_html}</tbody></table>""", unsafe_allow_html=True)


# ----------------------------------------------------------------
# [2] 미국 증시 (US Analysis)
# ----------------------------------------------------------------
with st.expander("🗽 미국 증시 (US Market Analysis)", expanded=False):
    st.subheader("🔥 나스닥 100 주도주 & 소외주 (Top 10)")
    
    def heat_bar(pct):
        color = "#d60000" if pct >= 0 else "#0051c7"
        w = min(abs(pct)*10, 100)
        return f"<div class='heat-container'><div class='heat-fill' style='width:{w}%; background:{color};'></div></div>"

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🚀 급등 Top 10")
        for s in nas_top:
            st.markdown(f"<div style='margin-bottom:8px; font-size:0.9rem;'><div style='display:flex; justify-content:space-between;'><span><b>{s['ticker']}</b> <span class='theme-tag'>{s['theme']}</span></span><span style='color:#d60000; font-weight:bold;'>+{s['pct']:.2f}%</span></div>{heat_bar(s['pct'])}</div>", unsafe_allow_html=True)
            
    with c2:
        st.markdown("##### 💧 급락 Top 10")
        for s in nas_bot:
            st.markdown(f"<div style='margin-bottom:8px; font-size:0.9rem;'><div style='display:flex; justify-content:space-between;'><span><b>{s['ticker']}</b> <span class='theme-tag'>{s['theme']}</span></span><span style='color:#0051c7; font-weight:bold;'>{s['pct']:.2f}%</span></div>{heat_bar(s['pct'])}</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------
# [3] 시장 흐름 (Flow) - 브리핑 & 캘린더
# ----------------------------------------------------------------
with st.expander("🌊 시장 흐름 (Market Flow)", expanded=True):
    # 브리핑 로직
    nas_pct = brief_metrics.get('nas_pct', 0)
    tnx_val = brief_metrics.get('tnx', 0)
    vix_val = brief_metrics.get('vix', 0)
    
    mood = "강력한 매수세" if nas_pct > 1 else ("약세 흐름" if nas_pct < -0.5 else "혼조세")
    
    # HTML 공백 제거 (깨짐 방지)
    briefing_html = f"""
    <div class="briefing-card">
        <div class="briefing-header">☕ 아침 7시 마켓 브리핑</div>
        <div style="margin-bottom:15px;">
            <div class="briefing-title">1. 글로벌 매크로 (Overview)</div>
            <div class="briefing-text">
                간밤 뉴욕 증시는 <span class="highlight">{mood}</span>를 보였습니다. 
                나스닥은 <b>{nas_pct:+.2f}%</b>를 기록했으며, 
                국채 10년물 금리는 {tnx_val:.2f}% 수준을 기록했습니다.
            </div>
        </div>
        <div>
            <div class="briefing-title">2. 전문가 종합 의견 (Strategy)</div>
            <div class="briefing-text">
                공포 지수(VIX)는 <b>{vix_val:.2f}</b>를 기록 중입니다. 
                {'시장 변동성에 주의가 필요합니다.' if vix_val > 20 else '투자 심리가 비교적 안정적입니다.'}
            </div>
        </div>
    </div>
    """
    st.markdown(briefing_html, unsafe_allow_html=True)
    
    st.markdown("##### 📅 이번 주 주요 경제 일정 (US)")
    st.link_button("🔗 실시간 경제 캘린더 확인하기 (Investing.com)", "https://kr.investing.com/economic-calendar/")


# ----------------------------------------------------------------
# [4] 암호 화폐 (Crypto)
# ----------------------------------------------------------------
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    c1, c2 = st.columns(2)
    c1.metric("김치 프리미엄", f"{kimp:.2f}%")
    c2.metric("BTC 점유율", f"{dom:.1f}%")
    
    st.markdown("---")
    st.subheader("📰 주요 뉴스 (BlockMedia)")
    
    for i in range(0, len(c_news), 2):
        cols = st.columns(2)
        for j in range(2):
            if i+j < len(c_news):
                e = c_news[i+j]
                try: 
                    dt = datetime(*e.published_parsed[:6]) + timedelta(hours=9)
                    dt_str = dt.strftime("%H:%M")
                except: dt_str = ""
                
                with cols[j]:
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:8px; border:1px solid #eee; height:100%; margin-bottom:10px;">
                        <a href="{e.link}" target="_blank" style="text-decoration:none; color:#333; font-weight:bold; font-size:0.95rem; display:block; margin-bottom:5px;">{e.title}</a>
                        <div style="font-size:0.8rem; color:#888;">{dt_str} | BlockMedia</div>
                    </div>""", unsafe_allow_html=True)


# ----------------------------------------------------------------
# [5] 국내 증시 (Domestic)
# ----------------------------------------------------------------
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    # 각각 안전하게 호출
    kp_p, kp_pct, kp_chg = safe_get_price("^KS11")
    kq_p, kq_pct, kq_chg = safe_get_price("^KQ11")
    krw_p, krw_pct, krw_chg = safe_get_price("KRW=X")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("코스피", f"{kp_p:,.2f}", f"{kp_chg:+.2f}")
    m2.metric("코스닥", f"{kq_p:,.2f}", f"{kq_chg:+.2f}")
    m3.metric("원/달러", f"{krw_p:,.2f}", f"{krw_chg:+.2f}")
    
    st.markdown("---")
    render_highchart_safe("^KS11", "KOSPI")
    st.markdown("<br>", unsafe_allow_html=True)
    render_highchart_safe("^KQ11", "KOSDAQ")


# 하단 배너
st.markdown("""
<div class="custom-footer">
    <div class="footer-content">
        <div class="footer-main">Financial Report</div>
        <div class="footer-sub">- by Ajin Partners</div>
    </div>
    <a href="tel:010-0000-0000" class="footer-btn">📞 문의하기</a>
</div>
""", unsafe_allow_html=True)