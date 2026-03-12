import math
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import feedparser
import pandas as pd
import pytz
import requests
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="경제 대시보드(Economy Dash board)",
    page_icon="📊",
    layout="wide",
)

st_autorefresh(interval=60_000, key="economy-dashboard-refresh")  # 60s refresh


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
    .title-row {display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;}
    .time-chip {
        background:#111827; color:white; padding:12px 16px; border-radius:16px;
        font-size:15px; font-weight:600; border:1px solid #1f2937; display:inline-block;
    }
    .section-title {font-size:1.15rem; font-weight:800; margin-top:0.8rem; margin-bottom:0.6rem;}
    .metric-card {
        border:1px solid rgba(148,163,184,.25);
        border-radius:18px;
        padding:16px 16px 14px 16px;
        background:linear-gradient(180deg, rgba(17,24,39,.96) 0%, rgba(30,41,59,.94) 100%);
        color:white;
        min-height:138px;
        box-shadow:0 10px 30px rgba(2,6,23,.18);
    }
    .metric-label {font-size:14px; color:#cbd5e1; margin-bottom:7px; font-weight:700;}
    .metric-value {font-size:28px; line-height:1.15; font-weight:900; margin-bottom:8px;}
    .metric-sub {font-size:14px; color:#e2e8f0;}
    .pos {color:#22c55e; font-weight:800;}
    .neg {color:#ef4444; font-weight:800;}
    .neu {color:#f8fafc; font-weight:800;}
    .small-note {font-size:12px; color:#64748b;}
    .link-grid a {
        text-decoration:none; display:block; padding:12px 14px; border-radius:14px;
        border:1px solid #e5e7eb; margin-bottom:10px; color:inherit;
        background:white;
    }
    .footer-box {
        margin-top:24px; padding-top:14px; border-top:1px solid rgba(148,163,184,.25);
        text-align:center; color:#64748b; font-size:13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
}


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[^0-9.\-]", "", str(value))
        return float(cleaned) if cleaned not in {"", "-", "."} else None
    except Exception:
        return None



def fmt_number(n: Optional[float], digits: int = 2) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    return f"{n:,.{digits}f}"



def fmt_price_krw(n: Optional[float], digits: int = 0) -> str:
    if n is None:
        return "-"
    return f"₩{n:,.{digits}f}"



def fmt_percent(n: Optional[float], digits: int = 2) -> str:
    if n is None:
        return "-"
    return f"{n:+.{digits}f}%"



def delta_text(delta: Optional[float], pct: Optional[float], unit: str = "") -> Tuple[str, str]:
    if delta is None:
        return "정보 없음", "neu"
    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "■"
    cls = "pos" if delta > 0 else "neg" if delta < 0 else "neu"
    pct_part = f" ({pct:+.2f}%)" if pct is not None else ""
    unit_part = f" {unit}" if unit else ""
    return f"{arrow} {delta:+,.2f}{unit_part}{pct_part}", cls



def value_delta_card(label: str, value: str, delta: Optional[float], pct: Optional[float], sub_prefix: str = "전일 대비", unit: str = ""):
    text, cls = delta_text(delta, pct, unit=unit)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub_prefix} <span class="{cls}">{text}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=300)
def get_yf_snapshot(symbol: str, name: Optional[str] = None) -> Dict:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return {"name": name or symbol, "value": None, "delta": None, "pct": None}

        hist = hist.dropna(subset=["Close"])
        latest = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None
        delta = latest - prev if prev is not None else None
        pct = ((delta / prev) * 100) if prev not in (None, 0) else None
        return {
            "name": name or symbol,
            "value": latest,
            "prev": prev,
            "delta": delta,
            "pct": pct,
        }
    except Exception:
        return {"name": name or symbol, "value": None, "delta": None, "pct": None}


@st.cache_data(ttl=3600)
def get_bok_base_rate() -> Dict:
    url = "https://www.bok.or.kr/portal/singl/baseRate/list.do?menuNo=200643"
    try:
        html = requests.get(url, headers=HEADERS, timeout=20).text
        pairs = re.findall(r"(20\d{2})\s*(\d{2})월\s*(\d{2})일\s*([0-9.]+)", html)
        if len(pairs) >= 2:
            latest_dt = f"{pairs[0][0]}-{pairs[0][1]}-{pairs[0][2]}"
            latest = float(pairs[0][3])
            prev = float(pairs[1][3])
            delta = latest - prev
            pct = ((delta / prev) * 100) if prev else None
            return {"date": latest_dt, "value": latest, "delta": delta, "pct": pct}
    except Exception:
        pass
    return {"date": None, "value": None, "delta": None, "pct": None}


@st.cache_data(ttl=86400)
def get_ccsi_from_indexgo() -> Dict:
    url = "https://www.index.go.kr/unity/potal/main/EachDtlPageDetail.do?idx_cd=1058"
    try:
        html = requests.get(url, headers=HEADERS, timeout=20).text
        nums = re.findall(r"20\d{4}", html)
        # Frequently the page includes periods; keep unique ordered values.
        seen = []
        for n in nums:
            if n not in seen:
                seen.append(n)
        dates = seen

        # Look for likely numeric sequence around the page text. We focus on decimal values near the end.
        values = re.findall(r">\s*([0-9]{2,3}(?:\.[0-9])?)\s*<", html)
        numeric_vals = [safe_float(v) for v in values]
        numeric_vals = [v for v in numeric_vals if v is not None and 40 <= v <= 200]
        if len(numeric_vals) >= 2:
            latest = float(numeric_vals[-1])
            prev = float(numeric_vals[-2])
            delta = latest - prev
            pct = ((delta / prev) * 100) if prev else None
            latest_date = dates[-1] if dates else None
            return {"date": latest_date, "value": latest, "delta": delta, "pct": pct}
    except Exception:
        pass
    return {"date": None, "value": None, "delta": None, "pct": None}


@st.cache_data(ttl=900)
def get_gold_prices() -> Dict:
    candidates = [
        ("https://m.koreagoldx.co.kr/price/gold", "한국금거래소"),
        ("https://www.kgoldse.co.kr/", "한국금은거래소"),
        ("https://goldgold.co.kr/", "한국표준금거래소"),
    ]
    for url, source in candidates:
        try:
            text = requests.get(url, headers=HEADERS, timeout=20).text
            nums = [int(x.replace(",", "")) for x in re.findall(r"\b\d{3},\d{3}\b", text)]
            # Heuristic: pick 3.75g sell / buy and nearby diffs if present.
            if len(nums) >= 2:
                # choose largest as sell, next plausible as buy in typical gold page layout.
                sell = max(nums)
                remaining = [n for n in nums if n != sell]
                buy_candidates = [n for n in remaining if n < sell]
                buy = max(buy_candidates) if buy_candidates else (remaining[0] if remaining else None)
                diffs = [int(x.replace(",", "")) for x in re.findall(r"[▲△▼-]?\s*(\d{1,2},\d{3})", text)]
                sell_diff = diffs[0] if diffs else None
                buy_diff = diffs[1] if len(diffs) > 1 else None
                return {
                    "source": source,
                    "sell": sell,
                    "buy": buy,
                    "sell_delta": sell_diff,
                    "buy_delta": buy_diff,
                }
        except Exception:
            continue
    return {"source": None, "sell": None, "buy": None, "sell_delta": None, "buy_delta": None}


@st.cache_data(ttl=1800)
def get_opinet_avg_prices() -> Dict:
    api_key = st.secrets.get("OPINET_API_KEY", os.getenv("OPINET_API_KEY", ""))
    if not api_key:
        return {"gasoline": None, "diesel": None, "note": "OPINET_API_KEY 필요"}
    url = f"https://www.opinet.co.kr/api/avgAllPrice.do?out=json&code={api_key}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        data = res.json()
        rows = data.get("RESULT", {}).get("OIL", []) if isinstance(data, dict) else []
        mapping = {}
        for row in rows:
            prod = row.get("PRODCD")
            if prod in {"B027", "D047"}:
                mapping[prod] = {
                    "name": row.get("PRODNM"),
                    "price": safe_float(row.get("PRICE")),
                    "diff": safe_float(row.get("DIFF")),
                }
        return {
            "gasoline": mapping.get("B027"),
            "diesel": mapping.get("D047"),
            "note": None,
        }
    except Exception as e:
        return {"gasoline": None, "diesel": None, "note": f"오피넷 조회 실패: {e}"}


@st.cache_data(ttl=900)
def get_news() -> List[Dict]:
    queries = [
        "경제",
        "증시",
        "금리",
        "유가",
        "ETF",
        "AI 산업",
    ]
    allowed_domains = [
        "khan.co.kr",      # 경향신문
        "hani.co.kr",      # 한겨레
        "mk.co.kr",        # 매일경제
        "hankyung.com",    # 한국경제
        "sedaily.com",     # 서울경제
        "joongang.co.kr",  # 중앙일보
        "zdnet.co.kr",     # IT
        "etnews.com",      # IT
        "bloter.net",      # IT
    ]
    items: List[Dict] = []
    seen = set()
    for q in queries:
        feed_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q + ' when:1d')}+({'+OR+'.join([f'site:{d}' for d in allowed_domains])})&hl=ko&gl=KR&ceid=KR:ko"
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                link = entry.get("link", "")
                title = entry.get("title", "")
                published = entry.get("published", "")
                if not link or link in seen:
                    continue
                if not any(domain in link for domain in allowed_domains):
                    continue
                seen.add(link)
                items.append({"title": title, "link": link, "published": published})
        except Exception:
            continue
    items = items[:18]
    return items


@st.cache_data(ttl=1800)
def get_watchlist_table(tickers: Dict[str, str]) -> pd.DataFrame:
    rows = []
    for name, symbol in tickers.items():
        snap = get_yf_snapshot(symbol, name=name)
        rows.append(
            {
                "종목": name,
                "티커": symbol,
                "현재가": snap.get("value"),
                "전일대비": snap.get("delta"),
                "등락률(%)": snap.get("pct"),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["현재가"] = df["현재가"].apply(lambda x: round(x, 2) if pd.notna(x) else None)
        df["전일대비"] = df["전일대비"].apply(lambda x: round(x, 2) if pd.notna(x) else None)
        df["등락률(%)"] = df["등락률(%)"].apply(lambda x: round(x, 2) if pd.notna(x) else None)
    return df


# -----------------------------
# Configurable lists
# -----------------------------
KOSPI_TOP = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "NAVER": "035420.KS",
    "한화에어로스페이스": "012450.KS",
}

KOSDAQ_TOP = {
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "HLB": "028300.KQ",
    "알테오젠": "196170.KQ",
    "레인보우로보틱스": "277810.KQ",
    "리가켐바이오": "141080.KQ",
    "휴젤": "145020.KQ",
    "클래시스": "214150.KQ",
    "JYP Ent.": "035900.KQ",
    "파마리서치": "214450.KQ",
}

ETF_TOP = {
    "KODEX 200": "069500.KS",
    "TIGER 200": "102110.KS",
    "KODEX 코스닥150": "229200.KS",
    "TIGER 미국S&P500": "360750.KS",
    "KODEX 미국S&P500TR": "379800.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "KODEX 2차전지산업": "305720.KS",
    "KODEX 은행": "091170.KS",
    "KODEX 골드선물(H)": "132030.KS",
    "TIGER 리츠부동산인프라": "329200.KS",
}

LINKS = [
    ("한국은행 ECOS", "https://ecos.bok.or.kr/"),
    ("한국은행 기준금리", "https://www.bok.or.kr/portal/singl/baseRate/list.do?menuNo=200643"),
    ("KRX 정보데이터시스템", "https://data.krx.co.kr/"),
    ("오피넷", "https://www.opinet.co.kr/"),
    ("한국금거래소", "https://m.koreagoldx.co.kr/"),
    ("기획재정부", "https://www.moef.go.kr/"),
    ("통계청 국가통계포털(KOSIS)", "https://kosis.kr/"),
    ("국가지표체계", "https://www.index.go.kr/"),
    ("한국경제신문", "https://www.hankyung.com/"),
    ("매일경제", "https://www.mk.co.kr/"),
    ("서울경제", "https://www.sedaily.com/"),
    ("중앙일보 경제", "https://www.joongang.co.kr/money"),
]


# -----------------------------
# Header / clocks
# -----------------------------
kr_tz = pytz.timezone("Asia/Seoul")
ny_tz = pytz.timezone("America/New_York")
now_kr = datetime.now(kr_tz)
now_ny = datetime.now(ny_tz)
weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now_kr.weekday()]
weekday_ny = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now_ny.weekday()]

st.markdown('<div class="title-row">', unsafe_allow_html=True)
st.title("경제 대시보드(Economy Dash board)")
st.markdown(
    f"""
    <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <div class="time-chip">한국 시간 · {now_kr.strftime('%Y-%m-%d')} ({weekday_kr}) {now_kr.strftime('%H:%M:%S')}</div>
        <div class="time-chip">미국 동부 시간 · {now_ny.strftime('%Y-%m-%d')} ({weekday_ny}) {now_ny.strftime('%H:%M:%S')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)
st.caption("자동 새로고침: 60초")


# -----------------------------
# Core metrics
# -----------------------------
kospi = get_yf_snapshot("^KS11", "KOSPI")
kosdaq = get_yf_snapshot("^KQ11", "KOSDAQ")
crude = get_yf_snapshot("BZ=F", "브렌트유")
base_rate = get_bok_base_rate()
ccsi = get_ccsi_from_indexgo()
gold = get_gold_prices()
opinet = get_opinet_avg_prices()

st.markdown('<div class="section-title">오늘의 핵심 지표</div>', unsafe_allow_html=True)
row1 = st.columns(4)
with row1[0]:
    value_delta_card("오늘의 코스피", fmt_number(kospi.get("value"), 2), kospi.get("delta"), kospi.get("pct"))
with row1[1]:
    value_delta_card("오늘의 코스닥", fmt_number(kosdaq.get("value"), 2), kosdaq.get("delta"), kosdaq.get("pct"))
with row1[2]:
    sell = gold.get("sell")
    sell_diff = gold.get("sell_delta")
    pct = ((sell_diff / (sell - sell_diff)) * 100) if sell and sell_diff not in (None, 0) else None
    value_delta_card("한국 금시세 1돈 · 살때", fmt_price_krw(sell, 0), sell_diff, pct, sub_prefix="전일 대비", unit="원")
    st.caption(f"출처: {gold.get('source') or '-'}")
with row1[3]:
    buy = gold.get("buy")
    buy_diff = gold.get("buy_delta")
    pct = ((buy_diff / (buy - buy_diff)) * 100) if buy and buy_diff not in (None, 0) else None
    value_delta_card("한국 금시세 1돈 · 팔때", fmt_price_krw(buy, 0), buy_diff, pct, sub_prefix="전일 대비", unit="원")

row2 = st.columns(4)
with row2[0]:
    value_delta_card(
        "한국 기준금리",
        f"{fmt_number(base_rate.get('value'), 2)}%" if base_rate.get("value") is not None else "-",
        base_rate.get("delta"),
        base_rate.get("pct"),
        sub_prefix="직전 변경 대비",
        unit="%p",
    )
    st.caption(f"최근 변경일: {base_rate.get('date') or '-'}")
with row2[1]:
    value_delta_card(
        "소비심리지수(CCSI)",
        fmt_number(ccsi.get("value"), 1),
        ccsi.get("delta"),
        ccsi.get("pct"),
        sub_prefix="전월 대비",
        unit="p",
    )
    st.caption(f"기준월: {ccsi.get('date') or '-'}")
with row2[2]:
    value_delta_card(
        "국제유가 · 브렌트유",
        f"${fmt_number(crude.get('value'), 2)} / bbl" if crude.get("value") is not None else "-",
        crude.get("delta"),
        crude.get("pct"),
        sub_prefix="전일 대비",
        unit="달러",
    )
with row2[3]:
    if opinet.get("gasoline"):
        g = opinet["gasoline"]
        d = opinet["diesel"] or {}
        g_pct = ((g['diff'] / (g['price'] - g['diff'])) * 100) if g.get('price') and g.get('diff') not in (None, 0) else None
        d_pct = ((d.get('diff') / (d.get('price') - d.get('diff'))) * 100) if d.get('price') and d.get('diff') not in (None, 0) else None
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">한국 기준 유가</div>
                <div class="metric-value" style="font-size:20px;">휘발유 {fmt_price_krw(g.get('price'), 0)} / 경유 {fmt_price_krw(d.get('price'), 0)}</div>
                <div class="metric-sub">휘발유 <span class="{'pos' if (g.get('diff') or 0) > 0 else 'neg' if (g.get('diff') or 0) < 0 else 'neu'}">{delta_text(g.get('diff'), g_pct, '원')[0]}</span></div>
                <div class="metric-sub">경유 <span class="{'pos' if (d.get('diff') or 0) > 0 else 'neg' if (d.get('diff') or 0) < 0 else 'neu'}">{delta_text(d.get('diff'), d_pct, '원')[0]}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">한국 기준 유가</div>
                <div class="metric-value" style="font-size:22px;">API 키 설정 필요</div>
                <div class="metric-sub">{opinet.get('note') or '오피넷 데이터를 불러오지 못했습니다.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------
# Watch tables
# -----------------------------
left, right = st.columns(2)
with left:
    st.markdown('<div class="section-title">코스피 주요 10개 종목</div>', unsafe_allow_html=True)
    kospi_df = get_watchlist_table(KOSPI_TOP)
    st.dataframe(kospi_df, use_container_width=True, hide_index=True)
with right:
    st.markdown('<div class="section-title">코스닥 주요 10개 종목</div>', unsafe_allow_html=True)
    kosdaq_df = get_watchlist_table(KOSDAQ_TOP)
    st.dataframe(kosdaq_df, use_container_width=True, hide_index=True)

st.markdown('<div class="section-title">주요 ETF 10개 종목</div>', unsafe_allow_html=True)
etf_df = get_watchlist_table(ETF_TOP)
st.dataframe(etf_df, use_container_width=True, hide_index=True)


# -----------------------------
# News + quick links
# -----------------------------
news_col, link_col = st.columns([1.3, 0.7])
with news_col:
    st.markdown('<div class="section-title">주요 경제뉴스</div>', unsafe_allow_html=True)
    news_items = get_news()
    if not news_items:
        st.info("뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
    else:
        for item in news_items[:12]:
            st.markdown(f"- [{item['title']}]({item['link']})")
            if item.get("published"):
                st.caption(item["published"])

with link_col:
    st.markdown('<div class="section-title">주요 경제정보 확인 사이트</div>', unsafe_allow_html=True)
    st.markdown('<div class="link-grid">', unsafe_allow_html=True)
    for title, url in LINKS:
        st.markdown(f'<a href="{url}" target="_blank">{title}</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# Sidebar guidance
# -----------------------------
with st.sidebar:
    st.header("설정 안내")
    st.write("이 대시보드는 60초마다 자동 새로고침됩니다.")
    st.write("정확도를 높이려면 아래 키를 Streamlit Secrets에 넣어주세요.")
    st.code(
        """# .streamlit/secrets.toml
OPINET_API_KEY = "YOUR_OPINET_KEY"
""",
        language="toml",
    )
    st.caption("한국 기준금리와 소비심리지수는 공식 공개 페이지를 우선 활용합니다.")
    st.caption("주가/ETF/원유는 Yahoo Finance 데이터에 연결됩니다.")

st.markdown('<div class="footer-box">© miyawa 제작</div>', unsafe_allow_html=True)
