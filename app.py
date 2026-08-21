import streamlit as st
import plotly.graph_objects as go
from agents.storage_agent import init_db, save_memo, load_memos, delete_memo, update_memo
from agents.stock_agent import init_stock_db, add_stock, load_stocks, delete_stock, update_stock_status, update_stock_tag
from agents.research_agent import get_stock_data, get_company_overview, get_chart_data, get_kr_stock_data, get_kr_dividend_info, search_ticker

# 스타일 설정
st.markdown("""
    <style>
    @import url("https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css");
    div[data-testid="InputInstructions"] { display: none !important; }
    @font-face {
        font-family: 'Cafe24AnemoneAir';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2202@1.0/Cafe24Ohsquareair.woff') format('woff');
        font-weight: normal;
        font-style: normal;
    }
    * { font-family: 'Cafe24AnemoneAir', sans-serif !important; }
    body, p, div, span, label, input, textarea { font-size: 21px !important; }
    [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
    [data-testid="stHorizontalBlock"] { align-items: stretch !important; }
    [data-testid="stColumn"] { display: flex !important; }
    [data-testid="stColumn"] > div { width: 100%; }
    [data-testid="stColumn"] [data-testid="stVerticalBlockBorderWrapper"] { height: 100%; }
    [data-testid="stColumn"] [data-testid="stVerticalBlock"] { height: 100%; }
    [data-testid="stColumn"] [data-testid="stCaptionContainer"] { margin-top: -1.0rem !important; }
    .main-title { font-size: 2.5rem; font-weight: 800; background: linear-gradient(90deg, #00c4ff, #0072ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    .sub-text { color: #888; font-size: 0.9rem; margin-bottom: 2rem; }
    .stButton > button { border-radius: 20px; font-weight: 600; transition: 0.2s; padding: 0.3rem 0.8rem; font-size: 0.85rem; width: auto !important; display: block !important; margin: 0 auto !important; border: none !important; background: none !important; color: #555 !important; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 1rem; }
    [data-testid="stElementContainer"]:has(.memo-card-marker) + div [data-testid="stMarkdownContainer"] p { margin: 0 !important; }
    .memo-card-marker + div [data-testid="stColumn"] { display: block !important; }
    .memo-card-marker + div [data-testid="stVerticalBlockBorderWrapper"] { height: auto !important; }
    .memo-card-marker + div [data-testid="stVerticalBlock"] { height: auto !important; }
    [data-testid="stElementContainer"]:has(.memo-card-marker) + div hr { margin: 0.3em 0px !important; }
    [data-testid="stButton"] { margin: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# DB 초기화
init_db()
init_stock_db()
from agents.stock_master_agent import auto_update_if_needed
auto_update_if_needed()

if not st.session_state.get("entered", False):
    st.markdown("""
    <div style="text-align:center; margin-top:15vh;">
        <h1 class="main-title">Byme</h1>
        <p class="sub-text">투자를 기록하고,<br>더 나은 판단을 남기다.</p>
    </div>
    """, unsafe_allow_html=True)

if "entered" not in st.session_state:
    st.session_state.entered = False
if "quote" not in st.session_state:
    st.session_state.quote = None
if "overview" not in st.session_state:
    st.session_state.overview = None
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

if not st.session_state.entered:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("[ 분석 시작하기 ]", use_container_width=True):
            st.session_state.entered = True
            st.rerun()
else:
    if st.button("Byme", key="logo_home_btn"):
        st.session_state.entered = False
        st.rerun()
    st.markdown('<p class="sub-text">투자 초보자를 위한 종목 분석 도우미</p>', unsafe_allow_html=True)

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["관심종목", "종목분석", "메모"])

    # ── Tab 1: 관심 종목 관리 ──
    with tab1:
        st.subheader("📋 관심 종목 추가")
        market_choice = st.radio("시장 선택", ["🇰🇷 국내", "🇺🇸 미국"], horizontal=True)
        keyword = st.text_input("종목명 검색", placeholder="예) 삼성전자 → Samsung, Apple, Tesla")

        if keyword:
            with st.spinner("검색 중..."):
                results = search_ticker(keyword)
            if market_choice == "🇰🇷 국내":
                results = [r for r in results if r["market"] == "국내"]
            else:
                results = [r for r in results if r["market"] == "미국"]

            if results:
                options = {f"{r['name']} ({r['ticker']}) - {r['region']}": r for r in results}
                selected_result = st.selectbox("종목 선택", list(options.keys()))
                if st.button("관심 종목 추가"):
                    r = options[selected_result]
                    add_stock(r["name"], r["ticker"], r["market"])
                    st.success(f"{r['name']} 추가됐어요!")
                    st.rerun()
            else:
                st.warning("검색 결과가 없어요. 영어로 검색해보세요!")

        st.divider()
        st.markdown("### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#FBEAF0;margin-right:6px;\"><i class=\"ti ti-pin\" style=\"font-size:14px;color:#993556;\"></i></span> 저장된 종목 목록", unsafe_allow_html=True)

        # 필터 버튼
        filter_options = ["전체", "관심", "관찰", "보류", "제외"]
        if "status_filter" not in st.session_state:
            st.session_state.status_filter = "전체"

        st.markdown("""
        <span class="filter-marker"></span>
        <style>
        .filter-marker + div[data-testid="stHorizontalBlock"] button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: #444 !important;
            font-size: 0.95rem !important;
            padding: 4px 10px !important;
        }
        .filter-marker + div[data-testid="stHorizontalBlock"] button:hover {
            color: #E74C3C !important;
            background: transparent !important;
        }
        </style>
        """, unsafe_allow_html=True)
        cols = st.columns(len(filter_options) + 3)
        for i, option in enumerate(filter_options):
            with cols[i]:
                is_selected = st.session_state.status_filter == option
                if is_selected:
                    st.markdown(f'<div style="color:#222;border-bottom:3px solid #E74C3C;padding:4px 10px 6px 10px;font-size:1.05rem;font-weight:700;text-align:center;margin-bottom:8px;">{option}</div>', unsafe_allow_html=True)
                else:
                    if st.button(option, key=f"filter_{option}"):
                        st.session_state.status_filter = option
                        st.rerun()

        # 필터 적용
        all_stocks = load_stocks()
        if st.session_state.status_filter == "전체":
            stocks = all_stocks
        else:
            stocks = [s for s in all_stocks if s[4] == st.session_state.status_filter]

        if stocks:
            kr_stocks = [s for s in stocks if s[3] == "국내"]
            us_stocks = [s for s in stocks if s[3] == "미국"]

            def show_stocks(stock_list):
                for stock in stock_list:
                    with st.container():
                        col1, col_market, col2, col3, col4 = st.columns([4, 1, 2, 3, 1])
                        with col1:
                            st.write(f"**{stock[1]}** ({stock[2]})")
                        with col_market:
                            st.markdown(f"<span style='white-space:nowrap'>{stock[3]}</span>", unsafe_allow_html=True)
                        with col2:
                            status = st.selectbox(
                                "상태",
                                ["관심", "관찰", "보류", "제외"],
                                index=["관심", "관찰", "보류", "제외"].index(stock[4]) if stock[4] in ["관심", "관찰", "보류", "제외"] else 0,
                                key=f"status_{stock[0]}"
                            )
                            if status != stock[4]:
                                update_stock_status(stock[0], status)
                                st.rerun()
                        with col3:
                            tag = st.text_input(
                                "태그",
                                value=stock[5] if stock[5] else "",
                                placeholder="예: AI, 반도체",
                                key=f"tag_{stock[0]}"
                            )
                            if tag != stock[5]:
                                update_stock_tag(stock[0], tag)
                        with col4:
                            if st.button("🗑️", key=f"del_{stock[0]}"):
                                delete_stock(stock[0])
                                st.rerun()
                        st.divider()

            if kr_stocks:
                st.markdown("### 🇰🇷 국내")
                show_stocks(kr_stocks)

            if us_stocks:
                st.markdown("### 🇺🇸 미국")
                show_stocks(us_stocks)

        else:
            st.info("아직 저장된 종목이 없어요.")

    # ── Tab 2: 종목 분석 ──
    with tab2:
        st.markdown("### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#EEEDFE;margin-right:6px;\"><i class=\"ti ti-search\" style=\"font-size:14px;color:#3C3489;\"></i></span> 종목 분석", unsafe_allow_html=True)

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

                st.markdown(f"### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#FAEEDA;margin-right:6px;\"><i class=\"ti ti-chart-bar\" style=\"font-size:14px;color:#854F0B;\"></i></span> {selected_stock[1]} 기본 정보", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    currency = "원" if selected_stock[3] == "국내" else "$"
                    raw_price = None
                    try:
                        raw_price = float(quote["price"])
                    except (TypeError, ValueError, KeyError):
                        raw_price = None
                    price = quote['price']
                    if price != "N/A":
                        price = f"{int(float(price)):,}"
                    price_display = f"${price}" if currency == "$" else f"{price}{currency}"
                    st.metric("현재 주가", price_display)
                with col2:
                    st.metric("등락률 (전일 대비)", quote['change_percent'])
                with col3:
                    volume = quote['volume']
                    if volume != "N/A":
                        volume = f"{int(float(volume)):,}"
                    st.metric("거래량", f"{volume} 주")

                st.divider()
                chart_col1, chart_col2 = st.columns([4, 1])
                with chart_col1:
                    st.markdown("### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#E1F5EE;margin-right:6px;\"><i class=\"ti ti-chart-line\" style=\"font-size:14px;color:#0F6E56;\"></i></span> 주가 차트", unsafe_allow_html=True)
                with chart_col2:
                    period_map = {"1주": "1wk", "1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y", "전체": "max"}
                    period_label = st.selectbox("기간", list(period_map.keys()), index=3, label_visibility="collapsed")
                dates, closes = get_chart_data(selected_stock[2], period=period_map[period_label])
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
                st.subheader("체크리스트")

                col1, col2 = st.columns(2)

                import yfinance as yf
                ticker_symbol = selected_stock[2]
                try:
                    info = yf.Ticker(ticker_symbol).info
                    debt_ratio = info.get("debtToEquity", None)
                    if debt_ratio is not None:
                        if debt_ratio < 50:
                            auto_debt = "낮음"
                        elif debt_ratio < 150:
                            auto_debt = "보통"
                        else:
                            auto_debt = "높음"
                        debt_label = f"부채비율 ({debt_ratio:.0f}%)"
                    else:
                        auto_debt = "보통"
                        debt_label = "부채비율 (데이터 없음)"

                    div_yield = info.get("dividendYield", None)
                    if div_yield and div_yield > 0:
                        auto_dividend = "있음"
                        div_rate = info.get("dividendRate", None)
                        div_label = f"배당 여부 (수익률: {div_yield:.2f}%)"
                    else:
                        auto_dividend = "없음"
                        div_rate = None
                        div_label = "배당 여부"
                except:
                    auto_debt = "보통"
                    debt_label = "부채비율 (데이터 없음)"
                    auto_dividend = "없음"
                    div_rate = None
                    div_label = "배당 여부"

                if selected_stock[3] == "국내":
                    kr_div = get_kr_dividend_info(selected_stock[2])
                    if kr_div and kr_div["annual_dividend_sum"] > 0:
                        auto_dividend = "있음"
                        div_rate = kr_div["annual_dividend_sum"]
                        if raw_price and raw_price > 0:
                            kr_div_yield = (kr_div["annual_dividend_sum"] / raw_price) * 100
                            div_label = f"배당 여부 (수익률: {kr_div_yield:.2f}%)"
                        else:
                            div_label = "배당 여부"
                        div_unit = "원"
                    else:
                        auto_dividend = "없음"
                        div_rate = None
                        div_label = "배당 여부"
                        div_unit = "원"
                else:
                    div_unit = "$"

                row1_c1, row1_c2 = st.columns(2)
                with row1_c1:
                    with st.container(border=True):
                        debt = st.radio(debt_label, ["낮음", "보통", "높음"],
                            index=["낮음", "보통", "높음"].index(auto_debt))
                with row1_c2:
                    with st.container(border=True):
                        news = st.radio("최근 뉴스", ["긍정", "중립", "부정"])

                row2_c1, row2_c2 = st.columns(2)
                with row2_c1:
                    with st.container(border=True):
                        dividend = st.radio(div_label, ["있음", "없음"],
                            index=["있음", "없음"].index(auto_dividend))
                        if dividend == "있음" and div_rate:
                            if div_unit == "원":
                                st.caption(f"주당 연배당: {div_rate:,}원")
                            else:
                                st.caption(f"주당 연배당: ${div_rate:.2f}")
                        if dividend == "없음":
                            st.caption("주당 연배당: -")
                with row2_c2:
                    with st.container(border=True):
                        period = st.radio("내 목표 투자기간", ["단기", "중기", "장기"])

                row3_c1, row3_c2 = st.columns(2)
                with row3_c1:
                    with st.container(border=True):
                        growth = st.radio("업종 성장성", ["낮음", "보통", "높음"])
                with row3_c2:
                    with st.container(border=True):
                        risk = st.radio("리스크 수준", ["낮음", "보통", "높음"])

                st.divider()
                st.markdown("### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#E6F1FB;margin-right:6px;\"><i class=\"ti ti-news\" style=\"font-size:14px;color:#185FA5;\"></i></span> 관련 뉴스", unsafe_allow_html=True)
                from agents.research_agent import get_stock_news
                news_list = get_stock_news(selected_stock[1], display=5)
                if news_list:
                    for n in news_list:
                        with st.expander(n["title"]):
                            st.write(n["description"])
                            st.markdown(f"[원문 보기]({n['link']})")
                else:
                    st.write("관련 뉴스를 찾을 수 없습니다.")



            st.markdown("""
        <style>
        input[aria-label="투자 금액 입력 (원)"] {
    text-align: right;
        }
        </style>
        """, unsafe_allow_html=True)

            if "amount_reset_count" not in st.session_state:
                st.session_state["amount_reset_count"] = 0

            amount_input = st.text_input(
                "투자 금액 입력 (원)",
                value="0",
                key=f"amount_input_{st.session_state['amount_reset_count']}"
            )
            amount_clean = amount_input.replace(",", "").strip()
            if amount_clean == "":
                amount = 0
            elif amount_clean.isdigit():
                amount = int(amount_clean)
            else:
                amount = 0
                st.warning("숫자만 입력해주세요")
            st.write(f"입력된 금액: {amount:,}원")
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

                st.markdown(f"### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#FAEEDA;margin-right:6px;\"><i class=\"ti ti-trophy\" style=\"font-size:14px;color:#854F0B;\"></i></span> 총점: {score} / 10", unsafe_allow_html=True)

                if score >= 8:
                    result = "✅ 긍정적인 종목이에요. 추가 검토 후 투자를 고려해보세요."
                elif score >= 5:
                    result = "⚠️ 보통 수준이에요. 신중하게 검토하세요."
                else:
                    result = "❌ 리스크가 높아 보여요. 충분한 조사가 필요해요."

                st.info(result)

                save_memo(
                    title=f"{selected_stock[1]} 분석",
                    content=f"총점: {score}/10 | 부채:{debt} | 배당:{dividend} | 성장:{growth} | 뉴스:{news} | 기간:{period} | 리스크:{risk}"
                )
                st.success("분석 결과가 메모에 저장됐어요!")

        else:
            st.info("먼저 관심 종목을 추가해주세요.")

    # ── Tab 3: 메모 관리 ──
    with tab3:
        st.markdown("### <span style=\"display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:#FBEAF0;margin-right:6px;\"><i class=\"ti ti-notes\" style=\"font-size:14px;color:#993556;\"></i></span> 저장된 분석 메모", unsafe_allow_html=True)

        memos = load_memos()
        if memos:
            titles = ["전체"] + list(set([m[1] for m in memos]))
            col_a, col_b = st.columns([3, 1])
            with col_a:
                selected_title = st.selectbox("종목", titles)
            with col_b:
                if selected_title == "전체":
                    sort_order = st.selectbox("정렬", ["최신순", "오래된순"])

            if selected_title != "전체":
                memos = [m for m in memos if m[1] == selected_title]
            else:
                if sort_order == "오래된순":
                    memos = list(reversed(memos))

            for memo in memos:
                st.markdown('<div class="memo-card-marker"></div>', unsafe_allow_html=True)
                with st.container(border=True):
                    col1, col2 = st.columns([8, 1], vertical_alignment="center")
                    with col1:
                        st.markdown(f"**{memo[1]}** — {memo[3]}")
                    with col2:
                        if st.button("🗑️", key=f"del_memo_{memo[0]}"):
                            delete_memo(memo[0])
                            st.rerun()
                    st.divider()
                    col_label, col_save = st.columns([8, 1], vertical_alignment="center")
                    with col_label:
                        st.markdown("**내용**")
                    with col_save:
                        save_clicked = st.button("💾", key=f"save_memo_{memo[0]}")
                    _wrapped_lines = sum(max(1, -(-len(p)//40)) for p in memo[2].split(chr(10))) if memo[2] else 1
                    new_content = st.text_area(
                        "내용",
                        value=memo[2],
                        key=f"memo_content_{memo[0]}",
                        height=min(500, max(120, _wrapped_lines*30 + 40)),
                        label_visibility="collapsed"
                    )
                    if save_clicked:
                        update_memo(memo[0], new_content)
                        st.rerun()
        else:
            st.info("저장된 메모가 없어요.")