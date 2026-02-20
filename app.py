import streamlit as st
import plotly.graph_objects as go
from agents.storage_agent import init_db, save_memo, load_memos
from agents.stock_agent import init_stock_db, add_stock, load_stocks, delete_stock
from agents.research_agent import get_stock_data, get_company_overview, get_chart_data, get_kr_stock_data, search_ticker
# 스타일 설정
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00c4ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-text {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2e2e3e;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)
# DB 초기화
init_db()
init_stock_db()

st.markdown('<p class="main-title">📈 투자 판단 보조 도구</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">투자 초보자를 위한 종목 분석 도우미</p>', unsafe_allow_html=True)

# session_state 초기화
if "quote" not in st.session_state:
    st.session_state.quote = None
if "overview" not in st.session_state:
    st.session_state.overview = None
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

# 탭 구성
tab1, tab2, tab3 = st.tabs(["관심 종목 관리", "종목 분석", "메모 관리"])

# ── Tab 1: 관심 종목 관리 ──
with tab1:
    st.subheader("📋 관심 종목 추가")
    
    keyword = st.text_input("종목명 검색", placeholder="예) 삼성전자, Apple, Tesla")
    
    if keyword:
        with st.spinner("검색 중..."):
            results = search_ticker(keyword)
        
        if results:
            options = {f"{r['name']} ({r['ticker']}) - {r['region']}": r for r in results}
            selected_result = st.selectbox("종목 선택", list(options.keys()))
            
            if st.button("관심 종목 추가"):
                r = options[selected_result]
                ticker = r["ticker"]
                name = r["name"]
                market = "국내" if ticker.isdigit() else "미국"
                add_stock(name, ticker, market)
                st.success(f"{name} 추가됐어요!")
                st.rerun()
        else:
            st.warning("검색 결과가 없어요.")
    
    st.divider()
    st.subheader("📌 저장된 종목 목록")
    stocks = load_stocks()
    
    if stocks:
        for stock in stocks:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{stock[1]}**")
            with col2:
                st.write(stock[2])
            with col3:
                st.write(stock[3])
            with col4:
                if st.button("삭제", key=f"del_{stock[0]}"):
                    delete_stock(stock[0])
                    st.rerun()
    else:
        st.info("아직 저장된 종목이 없어요.")

# ── Tab 2: 종목 분석 ──
with tab2:
    st.subheader("🔍 종목 분석")
    
    stocks = load_stocks()
    
    if stocks:
        stock_options = {f"{s[1]} ({s[2]}) - {s[3]}": s for s in stocks}
        selected = st.selectbox("분석할 종목 선택", list(stock_options.keys()))
        
        if st.button("데이터 조회"):
            with st.spinner("데이터 가져오는 중..."):
                selected_stock = stock_options[selected]
                ticker = selected_stock[2]
                market = selected_stock[3]
                
                if market == "미국":
                    st.session_state.quote = get_stock_data(ticker)
                    st.session_state.overview = get_company_overview(ticker)
                else:
                    kr_data = get_kr_stock_data(ticker)
                    if kr_data:
                        st.session_state.quote = {
                            "ticker": ticker,
                            "price": kr_data["price"],
                            "change_percent": kr_data["change_percent"],
                            "volume": kr_data["volume"]
                        }
                        st.session_state.overview = {
                            "market_cap": kr_data["market_cap"],
                            "52_week_high": "N/A",
                            "52_week_low": "N/A",
                            "dividend": "N/A",
                            "debt_to_equity": "N/A"
                        }
                    else:
                        st.error("국내 주식 데이터를 불러올 수 없어요.")
                
                st.session_state.selected_stock = selected_stock

        if st.session_state.quote:
            quote = st.session_state.quote
            selected_stock = st.session_state.selected_stock

            st.subheader(f"📊 {selected_stock[1]} 기본 정보")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("현재 주가", f"${quote['price']}")
            with col2:
                st.metric("등락률", quote['change_percent'])
            with col3:
                st.metric("거래량", quote['volume'])
           # 차트
            st.divider()
            st.subheader("📈 주가 차트 (최근 100일)")
            dates, closes = get_chart_data(selected_stock[2])
            if dates and closes:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=closes,
                    mode='lines',
                    name=selected_stock[1],
                    line=dict(color='#00c4ff', width=2)
                ))
                fig.update_layout(
                    xaxis_title="날짜",
                    yaxis_title="주가",
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("차트 데이터를 불러올 수 없어요.") 
            st.divider()
            st.subheader("📋 체크리스트")
            
            col1, col2 = st.columns(2)
            with col1:
                debt = st.radio("부채비율", ["낮음", "보통", "높음"])
                dividend = st.radio("배당 여부", ["있음", "없음"])
                growth = st.radio("업종 성장성", ["낮음", "보통", "높음"])
            with col2:
                news = st.radio("최근 뉴스", ["긍정", "중립", "부정"])
                period = st.radio("투자 기간", ["단기", "중기", "장기"])
                risk = st.radio("리스크 수준", ["낮음", "보통", "높음"])
            
            st.divider()
            
            user_type = st.radio("나는?", ["A타입 - 금액 입력해서 배분 참고", "B타입 - 정보만 보고 선택"])
            
            if "A타입" in user_type:
                amount = st.number_input("투자 금액 입력 (원)", min_value=0, step=10000)
            
            if st.button("판단 보조 결과 보기"):
                score = 0
                if debt == "낮음": score += 2
                elif debt == "보통": score += 1
                if dividend == "있음": score += 1
                if growth == "높음": score += 2
                elif growth == "보통": score += 1
                if news == "긍정": score += 2
                elif news == "중립": score += 1
                if period == "장기": score += 1
                if risk == "낮음": score += 1
                
                st.subheader(f"📊 총점: {score} / 10")
                
                if score >= 8:
                    result = "✅ 긍정적인 종목이에요. 추가 검토 후 투자를 고려해보세요."
                elif score >= 5:
                    result = "⚠️ 보통 수준이에요. 신중하게 검토하세요."
                else:
                    result = "❌ 리스크가 높아 보여요. 충분한 조사가 필요해요."
                
                st.info(result)
                
                if "A타입" in user_type and amount > 0:
                    st.subheader("💰 금액 배분 참고")
                    if score >= 8:
                        ratio = 0.3
                    elif score >= 5:
                        ratio = 0.2
                    else:
                        ratio = 0.1
                    st.write(f"총 투자금액: {amount:,}원")
                    st.write(f"권장 배분 비율: {int(ratio*100)}%")
                    st.write(f"권장 투자금액: {int(amount * ratio):,}원")
                
                save_memo(
                    title=f"{selected_stock[1]} 분석",
                    content=f"총점: {score}/10 | 부채:{debt} | 배당:{dividend} | 성장:{growth} | 뉴스:{news} | 기간:{period} | 리스크:{risk}"
                )
                st.success("분석 결과가 메모에 저장됐어요!")
    else:
        st.info("먼저 관심 종목을 추가해주세요.")

# ── Tab 3: 메모 관리 ──
with tab3:
    st.subheader("📝 저장된 분석 메모")
    memos = load_memos()
    if memos:
        for memo in memos:
            st.markdown(f"**{memo[1]}** — {memo[3]}")
            st.write(memo[2])
            st.divider()
    else:
        st.info("저장된 메모가 없어요.")