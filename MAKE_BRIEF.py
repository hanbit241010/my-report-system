import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime, timedelta
import json

# ==========================================
# 1. 페이지 설정 및 스타일
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
    
    /* 모바일 여백 */
    @media (max-width: 600px) { .block-container { padding-bottom: 100px !important; } }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 수집 함수 (안정성 강화)
# ==========================================

# 2-1. 나스닥 100 데이터 (캐싱 적용, 스피너 제거)
@st.cache_data(ttl=600)
def get_nasdaq100_data():
    # 대표 50개 종목 (속도 최적화)
    tickers = ["NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "NFLX", "AMD", 
               "QCOM", "INTC", "PEP", "COST", "SBUX", "AMGN", "GILD", "TXN", "HON", "BKNG",
               "ADBE", "PYPL", "CSCO", "CMCSA", "TMUS", "INTU", "MDLZ", "ISRG", "LRCX", "MU",
               "ADI", "REGN", "VRTX", "PANW", "SNPS", "CDNS", "KLAC", "MAR", "ABNB", "ORLY"]
    
    themes = {
        "NVDA": "AI/반도체", "AAPL": "모바일/서비스", "MSFT": "클라우드/AI", "AMZN": "이커머스", "META": "SNS/메타",
        "GOOGL": "검색/AI", "TSLA": "전기차/로봇", "AVGO": "통신칩", "NFLX": "OTT", "AMD": "반도체",
        "ADBE": "SW", "CSCO": "네트워크", "PEP": "식음료", "COST": "유통", "SBUX": "식음료"
    }
    
    results = []
    try:
        # 배치 다운로드로 속도 향상
        data = yf.download(tickers, period="2d", progress=False)['Close']
        
        # 멀티컬럼 처리 (yfinance 버전에 따라 다름)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        for t in tickers:
            if t in data.columns:
                series = data[t].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct = ((curr - prev) / prev) * 100
                    results.append({
                        "ticker": t, 
                        "pct": pct, 
                        "theme": themes.get(t, "테크/기타")
                    })
    except Exception as e:
        pass # 에러 발생 시 빈 리스트 반환하여 앱 멈춤 방지

    # 등락률 순 정렬
    sorted_res = sorted(results, key=lambda x: x['pct'], reverse=True)
    return sorted_res[:10], sorted_res[-10:]

# 2-2. 7시 브리핑용 데이터
def get_briefing_data():
    # 주요 지수 + 국채 금리 + VIX
    tickers = ["^IXIC", "^GSPC", "^DJI", "^VIX", "^TNX"]
    data = {}
    try:
        df = yf.download(tickers, period="5d", progress=False)['Close']
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        for t in tickers:
            if t in df.columns:
                s = df[t].dropna()
                if len(s) >= 2:
                    data[t] = {
                        "price": s.iloc[-1],
                        "pct": ((s.iloc[-1] - s.iloc[-2]) / s.iloc[-2]) * 100,
                        "prev": s.iloc[-2]
                    }
    except: pass
    return data

# 2-3. 암호화폐 데이터 (뉴스 10개)
def get_crypto_bundle():
    kimp, dom = 0.0, 0.0
    news = []
    try:
        # 김프 계산
        usd = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        btc_usd = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        kor_res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW").json()
        btc_krw = float(kor_res['data']['closing_price'])
        kimp = ((btc_krw - (btc_usd * usd)) / (btc_usd * usd)) * 100
        
        # 도미넌스
        dom_res = requests.get("https://api.coinlore.net/api/global/").json()
        dom = float(dom_res[0]['btc_d'])
        
        # 뉴스 10개
        news = feedparser.parse("https://www.blockmedia.co.kr/archives/category/market/digital-asset/feed").entries[:10]
    except: pass
    return kimp, dom, news

# 2-4. 하이차트 렌더링 (안전장치 추가)
def render_chart(ticker, name):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty:
            st.warning(f"{name} 차트 데이터를 불러올 수 없습니다.")
            return

        # 멀티 인덱스 정리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.reset_index()
        
        # 데이터 포맷팅 (타임스탬프 변환 필수)
        ohlc_data = []
        for index, row in df.iterrows():
            # Date가 Timestamp 객체인지 확인
            ts = int(row['Date'].timestamp() * 1000)
            ohlc_data.append([
                ts, 
                float(row['Open']), float(row['High']), float(row['Low']), float(row['Close'])
            ])

        # JSON 문자열로 변환
        ohlc_json = json.dumps(ohlc_data)

        # HTML 생성
        html_code = f"""
        <html>
        <head><script src="https://code.highcharts.com/stock/highstock.js"></script></head>
        <body style="margin:0;">
            <div id="container" style="height:350px; width:100%"></div>
            <script>
                try {{
                    Highcharts.stockChart('container', {{
                        rangeSelector: {{ selected: 1 }},
                        navigator: {{ enabled: false }},
                        scrollbar: {{ enabled: false }},
                        credits: {{ enabled: false }},
                        series: [{{
                            type: 'candlestick',
                            name: '{name}',
                            data: {ohlc_json},
                            color: '#0051c7',
                            upColor: '#d60000',
                            lineColor: '#0051c7',
                            upLineColor: '#d60000'
                        }}]
                    }});
                }} catch (e) {{ console.log(e); }}
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=360)
    except Exception as e:
        st.error(f"차트 생성 중 오류: {e}")

# ==========================================
# 3. 메인 실행 로직
# ==========================================

now = datetime.now()
st.markdown(f"<div style='text-align:center; font-size:2.2rem; font-weight:900;'>📈 AJIN REPORT</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><span style='background:#333; color:white; padding:5px 20px; border-radius:20px; font-weight:bold;'>{now.strftime('%Y. %m. %d')} (Week {now.isocalendar()[1]:02d})</span></div>", unsafe_allow_html=True)

# 데이터 로딩 (스피너는 여기서만 사용)
with st.spinner("시장 데이터를 분석하고 있습니다..."):
    nas_top10, nas_bot10 = get_nasdaq100_data()
    brief_data = get_briefing_data()
    kimp, dom, crypto_news = get_crypto_bundle()

# ----------------------------------------------------------------
# 1. 국제 증시 (International) - 차트 및 리스트
# ----------------------------------------------------------------
with st.expander("🌏 국제 증시 (International Indices)", expanded=True):
    # 아이템 정의
    items = [
        ("🪙 비트코인", "BTC-USD"), ("💲 나스닥", "^IXIC"), ("📈 S&P 500", "^GSPC"),
        ("🏛️ 다우존스", "^DJI"), ("🟡 금", "GC=F"), ("⚪ 은", "SI=F"), ("⚫ 원유", "CL=F")
    ]
    
    # 칩 선택
    if 'selected_ticker' not in st.session_state: st.session_state['selected_ticker'] = items[0][1]
    if 'selected_name' not in st.session_state: st.session_state['selected_name'] = items[0][0]
    
    labels = [i[0] for i in items]
    choice = st.radio("차트 선택", labels, horizontal=True, label_visibility="collapsed", index=labels.index(st.session_state['selected_name']))
    
    # 선택 변경 감지
    if choice != st.session_state['selected_name']:
        st.session_state['selected_name'] = choice
        st.session_state['selected_ticker'] = [i[1] for i in items if i[0] == choice][0]
        st.rerun()

    # 차트 그리기
    render_chart(st.session_state['selected_ticker'], st.session_state['selected_name'])

    # 표 그리기 (API 최적화)
    table_html = ""
    for name, ticker in items:
        # brief_data에 있으면 그거 쓰고, 없으면 개별 호출 (안정성)
        if ticker in brief_data:
            price = brief_data[ticker]['price']
            pct = brief_data[ticker]['pct']
            diff = price - brief_data[ticker]['prev']
        else:
            try:
                hist = yf.Ticker(ticker).history(period="2d")
                price = hist['Close'].iloc[-1]
                diff = price - hist['Close'].iloc[-2]
                pct = (diff / hist['Close'].iloc[-2]) * 100
            except:
                price, diff, pct = 0, 0, 0

        color = "#d60000" if diff >= 0 else "#0051c7"
        sign = "+" if diff >= 0 else ""
        bg_class = "class='selected-row'" if ticker == st.session_state['selected_ticker'] else ""
        
        table_html += f"""
        <tr {bg_class}>
            <td style="text-align:left;">{name}</td>
            <td>{price:,.2f}</td>
            <td style="color:{color}">{sign}{pct:.2f}%</td>
            <td style="color:{color}">{sign}{diff:,.2f}</td>
        </tr>
        """
    
    st.markdown(f"""<table class="custom-table"><thead><tr><th style="text-align:left;">종목</th><th>현재가</th><th>등락률</th><th>등락폭</th></tr></thead><tbody>{table_html}</tbody></table>""", unsafe_allow_html=True)


# ----------------------------------------------------------------
# 2. 미국 증시 (US Market) - Top 10 히트맵
# ----------------------------------------------------------------
with st.expander("🗽 미국 증시 (US Market Analysis)", expanded=False):
    st.subheader("🔥 나스닥 100 주도주 & 소외주 (Top 10)")
    
    col1, col2 = st.columns(2)
    
    def make_heat_bar(p):
        color = "#d60000" if p >= 0 else "#0051c7"
        width = min(abs(p) * 15, 100) # 100% 꽉 차게 비율 조정
        return f"<div class='heat-container'><div class='heat-fill' style='width:{width}%; background-color:{color};'></div></div>"

    with col1:
        st.markdown("##### 🚀 급등 상위 10")
        for s in nas_top10:
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                    <span><b>{s['ticker']}</b> <span class="theme-tag">{s['theme']}</span></span>
                    <span style="color:#d60000; font-weight:bold;">+{s['pct']:.2f}%</span>
                </div>
                {make_heat_bar(s['pct'])}
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("##### 💧 급락 상위 10")
        for s in nas_bot10:
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                    <span><b>{s['ticker']}</b> <span class="theme-tag">{s['theme']}</span></span>
                    <span style="color:#0051c7; font-weight:bold;">{s['pct']:.2f}%</span>
                </div>
                {make_heat_bar(s['pct'])}
            </div>""", unsafe_allow_html=True)


# ----------------------------------------------------------------
# 3. 시장 흐름 (Flow) - 브리핑 & 캘린더
# ----------------------------------------------------------------
with st.expander("🌊 시장 흐름 (Market Flow)", expanded=True):
    # 데이터 추출
    nas_data = brief_data.get("^IXIC", {'pct': 0, 'price': 0})
    vix_data = brief_data.get("^VIX", {'price': 20})
    tnx_data = brief_data.get("^TNX", {'price': 4.0, 'pct': 0})
    
    # 문구 생성 로직
    nas_pct = nas_data['pct']
    mood = "강력한 매수세" if nas_pct > 1 else ("약세 흐름" if nas_pct < -0.5 else "혼조세")
    tnx_comment = "상승하며 기술주에 부담" if tnx_data['pct'] > 1 else "안정세를 보이며 지지"
    
    # HTML 공백 제거 (깨짐 방지)
    briefing_html = f"""
    <div class="briefing-card">
        <div class="briefing-header">
            ☕ 아침 7시 마켓 브리핑 <span style="font-size:0.8rem; color:#888; font-weight:normal;">{now.strftime('%m.%d')} 기준</span>
        </div>
        <div style="margin-bottom:15px;">
            <div class="briefing-title">1. 글로벌 매크로 (Overview)</div>
            <div class="briefing-text">
                간밤 뉴욕 증시는 <span class="highlight">{mood}</span>를 보였습니다. 
                나스닥 지수는 <b>{nas_pct:+.2f}%</b>를 기록했으며, 
                시장 금리(10년물 국채)는 {tnx_data['price']:.2f}%로 {tnx_comment}했습니다.
            </div>
        </div>
        <div>
            <div class="briefing-title">2. 전문가 종합 의견 (Strategy)</div>
            <div class="briefing-text">
                공포 지수(VIX)는 <b>{vix_data['price']:.2f}</b>를 기록 중입니다. 
                {'변동성이 확대되고 있으니 리스크 관리가 필요합니다.' if vix_data['price'] > 20 else '투자 심리가 비교적 안정적입니다.'}
                주요 경제 지표 발표를 앞두고 관망세가 짙어질 수 있습니다.
            </div>
        </div>
    </div>
    """
    st.markdown(briefing_html, unsafe_allow_html=True)

    st.markdown("##### 📅 이번 주 주요 경제 일정 (US)")
    st.link_button("🔗 실시간 경제 캘린더 확인하기 (Investing.com)", "https://kr.investing.com/economic-calendar/")


# ----------------------------------------------------------------
# 4. 암호 화폐 (Crypto) - 뉴스 10개
# ----------------------------------------------------------------
with st.expander("🪙 암호 화폐 (Cryptocurrency)", expanded=False):
    c1, c2 = st.columns(2)
    c1.metric("김치 프리미엄", f"{kimp:.2f}%")
    c2.metric("BTC 점유율 (Dominance)", f"{dom:.1f}%")
    
    st.markdown("---")
    st.subheader("📰 주요 뉴스 (BlockMedia)")
    
    for i in range(0, len(crypto_news), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(crypto_news):
                idx = i + j
                entry = crypto_news[idx]
                try:
                    dt = datetime(*entry.published_parsed[:6]) + timedelta(hours=9)
                    dt_str = dt.strftime("%H:%M")
                except: dt_str = ""
                
                with cols[j]:
                    st.markdown(f"""
                    <div style="background:white; padding:15px; border-radius:8px; border:1px solid #eee; height:100%; margin-bottom:10px;">
                        <a href="{entry.link}" target="_blank" style="text-decoration:none; color:#333; font-weight:bold; font-size:0.95rem; display:block; margin-bottom:5px;">
                            {entry.title}
                        </a>
                        <div style="font-size:0.8rem; color:#888;">{dt_str} | BlockMedia</div>
                    </div>
                    """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# 5. 국내 증시 (Domestic) - 복구 완료
# ----------------------------------------------------------------
with st.expander("📈 국내 증시 (Domestic Market)", expanded=False):
    # 데이터 수집 (에러 방지용 개별 호출)
    try:
        ks = yf.download("^KS11", period="5d", progress=False)['Close']
        kq = yf.download("^KQ11", period="5d", progress=False)['Close']
        krw = yf.download("KRW=X", period="5d", progress=False)['Close']
        
        # 멀티인덱스 처리
        if isinstance(ks.columns, pd.MultiIndex): ks.columns = ks.columns.droplevel(1)
        if isinstance(kq.columns, pd.MultiIndex): kq.columns = kq.columns.droplevel(1)
        if isinstance(krw.columns, pd.MultiIndex): krw.columns = krw.columns.droplevel(1)
        
        m1, m2, m3 = st.columns(3)
        
        def get_delta(series):
            if len(series) < 2: return 0, 0
            curr = series.iloc[-1]
            prev = series.iloc[-2]
            return curr, curr - prev
            
        v1, d1 = get_delta(ks)
        v2, d2 = get_delta(kq)
        v3, d3 = get_delta(krw)
        
        m1.metric("코스피 (KOSPI)", f"{v1:,.2f}", f"{d1:+.2f}")
        m2.metric("코스닥 (KOSDAQ)", f"{v2:,.2f}", f"{d2:+.2f}")
        m3.metric("원/달러 (USD/KRW)", f"{v3:,.2f}", f"{d3:+.2f}")
        
        st.markdown("---")
        render_chart("^KS11", "KOSPI")
        st.markdown("<br>", unsafe_allow_html=True)
        render_chart("^KQ11", "KOSDAQ")
        
    except Exception as e:
        st.error("국내 증시 데이터를 불러오는 중 오류가 발생했습니다.")


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