import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime, timedelta
import json

# ==========================================
# 1. 페이지 설정 및 전역 스타일
# ==========================================
st.set_page_config(page_title="AJIN REPORT", layout="wide")

st.markdown("""
    <style>
    header[data-testid="stHeader"], footer { display: none !important; }
    [data-testid="stToolbar"], [data-testid="stStatusWidget"] { display: none !important; }
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
    .footer-main { font-size: 1.1rem; font-weight: 900; color: #333; line-height: 1.2; }
    .footer-sub { font-size: 0.75rem; color: #888; margin-top: 2px; }
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
    .briefing-title { font-size: 1.1rem; font-weight: 800; color: #d60000; margin-bottom: 8px; }
    .briefing-text { font-size: 1rem; line-height: 1.7; color: #333; text-align: justify; }
    .highlight { background-color: #fff9c4; font-weight: bold; padding: 2px 4px; }

    /* 히트맵 바 */
    .heat-container { width: 100%; background-color: #f0f0f0; border-radius: 4px; height: 6px; margin-top: 4px; overflow: hidden; }
    .heat-fill { height: 100%; border-radius: 4px; }
    .theme-tag { font-size: 0.7rem; color: #777; background-color: #f1f3f5; padding: 1px 5px; border-radius: 8px; margin-left: 5px; }

    /* 테이블 */
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
    .custom-table th { border-bottom: 2px solid #333; padding: 10px 5px; text-align: right; }
    .custom-table td { border-bottom: 1px solid #eee; padding: 12px 5px; text-align: right; }
    .selected-row { background-color: #fff5f5; font-weight: bold; color: #d60000; }
    
    /* 칩 */
    div.row-widget.stRadio > div { flex-direction: row; flex-wrap: wrap !important; gap: 8px; }
    div.row-widget.stRadio > div[role="radiogroup"] > label { background-color: #f0f2f6; padding: 6px 14px; border-radius: 20px; border: 1px solid #e0e0e0; font-size: 0.9rem; }
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] { background-color: #d60000 !important; color: white !important; border-color: #d60000 !important; }
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child { display: none; }
    
    @media (max-width: 600px) { .block-container { padding-bottom: 100px !important; } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 수집 및 유틸리티 함수 (상단 배치)
# ==========================================

def get_nasdaq100_movers():
    # 주요 테마 매핑
    themes = {"NVDA": "AI반도체", "TSLA": "전기차", "AAPL": "기기", "MSFT": "SW", "AMZN": "커머스", "META": "SNS", "GOOGL": "AI", "AMD": "반도체", "NFLX": "OTT", "COST": "소비재"}
    tickers = list(themes.keys()) + ["AVGO", "QCOM", "TXN", "AMGN", "INTU", "ISRG", "AMAT", "BKNG", "MDLZ", "GILD"]
    try:
        data = yf.download(tickers, period="2d", progress=False)['Close']
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.droplevel(1)
        res = []
        for t in data.columns:
            s = data[t].dropna()
            if len(s) >= 2:
                pct = ((s.iloc[-1] - s.iloc[-2]) / s.iloc[-2]) * 100
                res.append({"ticker": t, "pct": pct, "theme": themes.get(t, "테크")})
        sorted_res = sorted(res, key=lambda x: x['pct'], reverse=True)
        return sorted_res[:10], sorted_res[-10:]
    except: return [], []

def get_market_brief_logic():
    t_list = ["^IXIC", "^GSPC", "^DJI", "^VIX", "^TNX"]
    try:
        df = yf.download(t_list, period="2d", progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        res = {t: {"price": df[t].iloc[-1], "pct": ((df[t].iloc[-1]-df[t].iloc[-2])/df[t].iloc[-2])*100} for t in t_list}
        return res
    except: return {}

def get_crypto_data():
    try:
        usd = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        btc_usd = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        kor = float(requests.get("https://api.bithumb.com/public/ticker/BTC_KRW").json()['data']['closing_price'])
        kimp = ((kor - (btc_usd * usd)) / (btc_usd * usd)) * 100
        dom = float(requests.get("https://api.coinlore.net/api/global/").json()[0]['btc_d'])
        news = feedparser.parse("https://www.blockmedia.co.kr/archives/category/market/digital-asset/feed").entries[:10]
        return kimp, dom, news
    except: return 0, 0, []

def render_chart(ticker, name):
    try:
        df = yf.download(ticker, period="2y", progress=False).reset_index()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        ohlc = [[int(row['Date'].timestamp()*1000), row['Open'], row['High'], row['Low'], row['Close']] for _, row in df.iterrows()]
        html = f"""
        <html><head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;"><div id="c" style="height:350px;"></div><script>
        Highcharts.stockChart('c', {{rangeSelector:{{selected:1}}, credits:{{enabled:false}}, series:[{{type:'candlestick', name:'{name}', data:{json.dumps(ohlc)}, color:'#0051c7', upColor:'#d60000'}}]}});
        </script></body></html>"""
        components.html(html, height=370)
    except: st.error("차트 로드 실패")

# ==========================================
# 3. 메인 리포트 구성
# ==========================================

now = datetime.now()
today_str = now.strftime("%Y. %m. %d")
st.markdown(f"<div class='title-text'>📈 AJIN REPORT</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><span style='background:#333; color:white; padding:5px 20px; border-radius:20px;'>{today_str} (Week {now.isocalendar()[1]:02d})</span></div>", unsafe_allow_html=True)

# 데이터 사전 로드
with st.spinner("시장 데이터 동기화 중..."):
    top10, bot10 = get_nasdaq100_movers()
    m_brief = get_market_brief_logic()
    kimp, dom, c_news = get_crypto_data()

# --- (1) 국제 증시 ---
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    m_items = [("🪙 비트코인", "BTC-USD"), ("💲 나스닥", "^IXIC"), ("📈 S&P 500", "^GSPC"), ("🏛️ 다우존스", "^DJI"), ("🟡 금", "GC=F"), ("⚪ 은", "SI=F"), ("⚫ 원유", "CL=F")]
    choice = st.radio("S", [i[0] for i in m_items], horizontal=True, label_visibility="collapsed")
    t_code = [i[1] for i in m_items if i[0] == choice][0]
    render_chart(t_code, choice)
    
    rows = ""
    for name, tick in m_items:
        h = yf.Ticker(tick).history(period="2d")
        curr, prev = h['Close'].iloc[-1], h['Close'].iloc[-2]
        diff, pct = curr-prev, ((curr-prev)/prev)*100
        clr = "#d60000" if diff >= 0 else "#0051c7"
        sel = "class='selected-row'" if choice == name else ""
        rows += f"<tr {sel}><td>{name}</td><td>{curr:,.2f}</td><td style='color:{clr}'>{pct:+.2f}%</td><td style='color:{clr}'>{diff:+.2f}</td></tr>"
    st.markdown(f"<table class='custom-table'><thead><tr><th>종목</th><th>현재가</th><th>등락률</th><th>등락폭</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

# --- (2) 미국 증시 ---
with st.expander("🗽 미국 증시 (US Market Analysis)", expanded=False):
    st.subheader("🔥 나스닥 100 주도주 & 소외주 (Top 10)")
    c1, c2 = st.columns(2)
    def hb(p):
        c = "#d60000" if p >= 0 else "#0051c7"
        w = min(abs(p)*10, 100)
        return f"<div class='heat-container'><div class='heat-fill' style='width:{w}%; background:{c};'></div></div>"
    with c1:
        for s in top10: st.markdown(f"**{s['ticker']}** <span class='theme-tag'>{s['theme']}</span> <span style='color:#d60000; float:right;'>+{s['pct']:.2f}%</span>{hb(s['pct'])}", unsafe_allow_html=True)
    with c2:
        for s in bot10: st.markdown(f"**{s['ticker']}** <span class='theme-tag'>{s['theme']}</span> <span style='color:#0051c7; float:right;'>{s['pct']:.2f}%</span>{hb(s['pct'])}", unsafe_allow_html=True)

# --- (3) 시장 흐름 ---
with st.expander("🌊 시장 흐름 (Market Flow)", expanded=True):
    n = m_brief.get("^IXIC", {"pct":0, "price":0})
    v = m_brief.get("^VIX", {"price":20})
    t = m_brief.get("^TNX", {"price":4.0})
    mood = "강세" if n['pct'] > 0 else "약세"
    st.markdown(f"""<div class="briefing-card"><div class="briefing-header">☕ 아침 7시 마켓 브리핑</div><div class="briefing-section"><div class="briefing-title">1. 글로벌 매크로 요약</div><div class="briefing-text">간밤 미 증시는 <span class="highlight">{mood} 흐름</span>을 보였습니다. 나스닥 지수는 {n['pct']:+.2f}%를 기록했으며, 국채 10년물 금리는 {t['price']:.2f}% 수준에서 등락을 거듭했습니다.</div></div><div class="briefing-section"><div class="briefing-title">2. 투자 전략 가이드</div><div class="briefing-text">변동성 지수(VIX)가 {v['price']:.2f}를 기록하며 시장의 경계감이 {'완화' if v['price']<20 else '고조'}되는 모습입니다. 주요 저항선 돌파 여부를 주시하며 선별적 접근이 필요합니다.</div></div></div>""", unsafe_allow_html=True)
    st.info(f"📅 **이번 주 경제 일정:** 미국 중요도 ★★★ 지표 기준")
    st.link_button("🔗 실시간 경제 캘린더 (Investing.com)", "https://kr.investing.com/economic-calendar/")

# --- (4) 암호 화폐 ---
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    col1, col2 = st.columns(2)
    col1.metric("김치 프리미엄", f"{kimp:.2f}%")
    col2.metric("BTC 점유율", f"{dom:.1f}%")
    st.markdown("---")
    for e in c_news:
        kst = datetime(*e.published_parsed[:6]) + timedelta(hours=9)
        st.markdown(f"**[{kst.strftime('%H:%M')}]** [{e.title}]({e.link})")

# --- (5) 국내 증시 ---
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    ks = yf.download("^KS11", period="2d", progress=False)['Close']
    kq = yf.download("^KQ11", period="2d", progress=False)['Close']
    ex = yf.download("KRW=X", period="2d", progress=False)['Close']
    c1, c2, c3 = st.columns(3)
    c1.metric("코스피", f"{ks.iloc[-1]:,.2f}", f"{ks.iloc[-1]-ks.iloc[-2]:+.2f}")
    c2.metric("코스닥", f"{kq.iloc[-1]:,.2f}", f"{kq.iloc[-1]-kq.iloc[-2]:+.2f}")
    c3.metric("원/달러", f"{ex.iloc[-1]:,.2f}", f"{ex.iloc[-1]-ex.iloc[-2]:+.2f}")
    render_chart("^KS11", "KOSPI")
    render_chart("^KQ11", "KOSDAQ")

# 하단 배너
st.markdown(f"""<div class="custom-footer"><div class="footer-content"><div class="footer-main">Financial Report</div><div class="footer-sub">- by Ajin Partners</div></div><a href="tel:010-0000-0000" class="footer-btn">📞 문의하기</a></div>""", unsafe_allow_html=True)