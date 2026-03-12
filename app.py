import math
import os
import re
from datetime import datetime
from html import unescape
from typing import Dict, List, Optional, Tuple

import feedparser
import pandas as pd
import pytz
import requests
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh


st.set_page_config(
    page_title="경제 대시보드(Economy Dash board)",
    page_icon="📊",
    layout="wide",
)

st_autorefresh(interval=60_000, key="economy-dashboard-refresh")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    )
}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.0rem; padding-bottom: 2rem; max-width: 1450px;}
    .time-chip {
        background:#0f172a; color:#f8fafc; padding:12px 16px; border-radius:16px;
        font-size:15px; font-weight:700; border:1px solid rgba(148,163,184,.18); display:inline-block;
        box-shadow:0 10px 30px rgba(2,6,23,.20);
    }
    .section-title {font-size:1.15rem; font-weight:900; margin-top:1.0rem; margin-bottom:0.7rem;}
    .metric-card {
        border:1px solid rgba(148,163,184,.25);
        border-radius:20px;
        padding:16px 16px 14px 16px;
        background:linear-gradient(180deg, rgba(15,23,42,.97) 0%, rgba(30,41,59,.95) 100%);
        color:#f8fafc;
        min-height:142px;
        box-shadow:0 14px 32px rgba(2,6,23,.22);
    }
    .metric-label {font-size:14px; color:#cbd5e1; margin-bottom:7px; font-weight:800;}
    .metric-value {font-size:28px; line-height:1.12; font-weight:900; margin-bottom:8px;}
    .metric-sub {font-size:14px; color:#e2e8f0;}
    .source-note {font-size:12px; color:#94a3b8; margin-top:8px;}
    .pos {color:#22c55e; font-weight:800;}
    .neg {color:#ef4444; font-weight:800;}
    .neu {color:#f8fafc; font-weight:800;}
    .footer-box {
        margin-top:28px; padding-top:14px; border-top:1px solid rgba(148,163,184,.25);
        text-align:center; color:#94a3b8; font-size:13px;
    }
    .news-card {
        border:1px solid rgba(148,163,184,.2);
        background:rgba(15,23,42,.62);
        border-radius:16px;
        padding:12px 14px;
        margin-bottom:10px;
    }
    .news-source {font-size:12px; color:#94a3b8; margin-top:4px;}
    .search-box-wrap {
        border:1px solid rgba(148,163,184,.22);
        background:linear-gradient(180deg, rgba(15,23,42,.96) 0%, rgba(30,41,59,.92) 100%);
        border-radius:20px;
        padding:16px;
        margin-top:8px;
        margin-bottom:8px;
    }
    .link-card a {
        text-decoration:none; display:block; padding:12px 14px; border-radius:14px;
        border:1px solid rgba(148,163,184,.22); margin-bottom:10px; color:#e5e7eb;
        background:rgba(15,23,42,.56);
    }
    .tiny {font-size:12px; color:#94a3b8;}
    .summary-caption {font-size:12px; color:#94a3b8; margin-top:4px; margin-bottom:8px;}
    div[data-testid="stDataFrame"] div[role="table"] {font-size:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 50개 리스트 (주요 대형주/대표주 중심)
KOSPI_TOP_50 = {
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
    "삼성전자우": "005935.KS",
    "HD현대중공업": "329180.KS",
    "신한지주": "055550.KS",
    "현대모비스": "012330.KS",
    "POSCO홀딩스": "005490.KS",
    "삼성물산": "028260.KS",
    "메리츠금융지주": "138040.KS",
    "하나금융지주": "086790.KS",
    "카카오": "035720.KS",
    "HMM": "011200.KS",
    "한국전력": "015760.KS",
    "LG화학": "051910.KS",
    "두산에너빌리티": "034020.KS",
    "크래프톤": "259960.KS",
    "SK이노베이션": "096770.KS",
    "SK스퀘어": "402340.KS",
    "대한항공": "003490.KS",
    "HD한국조선해양": "009540.KS",
    "삼성SDI": "006400.KS",
    "삼성생명": "032830.KS",
    "우리금융지주": "316140.KS",
    "KT&G": "033780.KS",
    "KT": "030200.KS",
    "포스코퓨처엠": "003670.KS",
    "기업은행": "024110.KS",
    "아모레퍼시픽": "090430.KS",
    "오리온": "271560.KS",
    "LG": "003550.KS",
    "한미반도체": "042700.KS",
    "S-Oil": "010950.KS",
    "현대글로비스": "086280.KS",
    "SK텔레콤": "017670.KS",
    "삼양식품": "003230.KS",
    "롯데케미칼": "011170.KS",
    "한화오션": "042660.KS",
    "CJ제일제당": "097950.KS",
    "LG전자": "066570.KS",
    "HD현대일렉트릭": "267260.KS",
    "LS ELECTRIC": "010120.KS",
    "미래에셋증권": "006800.KS",
}

KOSDAQ_TOP_50 = {
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
    "펩트론": "087010.KQ",
    "실리콘투": "257720.KQ",
    "에이비엘바이오": "298380.KQ",
    "코오롱티슈진": "950160.KQ",
    "삼천당제약": "000250.KQ",
    "펄어비스": "263750.KQ",
    "씨젠": "096530.KQ",
    "에스엠": "041510.KQ",
    "HPSP": "403870.KQ",
    "솔브레인": "357780.KQ",
    "원익IPS": "240810.KQ",
    "이오테크닉스": "039030.KQ",
    "동진쎄미켐": "005290.KQ",
    "ISC": "095340.KQ",
    "리노공업": "058470.KQ",
    "주성엔지니어링": "036930.KQ",
    "테크윙": "089030.KQ",
    "천보": "278280.KQ",
    "메디톡스": "086900.KQ",
    "셀트리온제약": "068760.KQ",
    "셀트리온헬스케어": "091990.KQ",
    "카카오게임즈": "293490.KQ",
    "HK이노엔": "195940.KQ",
    "네오위즈": "095660.KQ",
    "오스코텍": "039200.KQ",
    "브이티": "018290.KQ",
    "심텍": "222800.KQ",
    "제이앤티씨": "204270.KQ",
    "하나마이크론": "067310.KQ",
    "루닛": "328130.KQ",
    "보로노이": "310210.KQ",
    "덕산네오룩스": "213420.KQ",
    "원텍": "336570.KQ",
    "피에스케이홀딩스": "031980.KQ",
    "파두": "440110.KQ",
    "티씨케이": "064760.KQ",
    "제이시스메디칼": "287410.KQ",
    "유진테크": "084370.KQ",
    "엔켐": "348370.KQ",
    "케어젠": "214370.KQ",
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

QUICK_LINKS = [
    ("한국은행 ECOS", "https://ecos.bok.or.kr/"),
    ("한국은행 기준금리", "https://www.bok.or.kr/portal/singl/baseRate/list.do?menuNo=200643"),
    ("KRX 정보데이터시스템", "https://data.krx.co.kr/"),
    ("오피넷", "https://www.opinet.co.kr/"),
    ("한국금거래소", "https://www.exgold.co.kr/"),
    ("기획재정부", "https://www.moef.go.kr/"),
    ("통계청 국가통계포털(KOSIS)", "https://kosis.kr/"),
    ("국가지표체계", "https://www.index.go.kr/"),
    ("한국경제신문", "https://www.hankyung.com/"),
    ("매일경제", "https://www.mk.co.kr/"),
    ("서울경제", "https://www.sedaily.com/"),
    ("중앙일보 경제", "https://www.joongang.co.kr/money"),
]

NEWS_FEEDS = [
    ("경향신문", "https://www.khan.co.kr/rss/rssdata/economy_news.xml"),
    ("한겨레", "https://www.hani.co.kr/rss/economy/"),
    ("매일경제 경제", "https://www.mk.co.kr/rss/30100041/"),
    ("매일경제 증권", "https://www.mk.co.kr/rss/50200011/"),
    ("한국경제 경제", "https://www.hankyung.com/feed/economy"),
    ("한국경제 증권", "https://www.hankyung.com/feed/finance"),
    ("한국경제 IT", "https://www.hankyung.com/feed/it"),
    ("서울경제 경제", "https://www.sedaily.com/rss/economy"),
    ("서울경제 증권", "https://www.sedaily.com/rss/finance"),
    ("서울경제 IT", "https://www.sedaily.com/rss/it"),
    ("중앙일보 경제", "https://news.google.com/rss/search?q=site:joongang.co.kr+경제&hl=ko&gl=KR&ceid=KR:ko"),
    ("IT", "https://news.google.com/rss/search?q=site:zdnet.co.kr+OR+site:etnews.com+IT&hl=ko&gl=KR&ceid=KR:ko"),
]


def safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[^0-9.\-+]", "", str(value))
        return float(cleaned) if cleaned not in {"", "-", ".", "+"} else None
    except Exception:
        return None


def safe_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(float(re.sub(r"[^0-9.\-+]", "", str(value))))
    except Exception:
        return None


def fmt_number(n: Optional[float], digits: int = 2) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    return f"{n:,.{digits}f}"


def fmt_int(n: Optional[float]) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    return f"{int(round(n)):,}"


def fmt_price_krw(n: Optional[float], digits: int = 0) -> str:
    if n is None:
        return "-"
    return f"₩{n:,.{digits}f}"


def fmt_amount_kr(n: Optional[float], unit: str = "억원") -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    return f"{n:,.0f}{unit}"


def price_with_commas(n: Optional[float]) -> str:
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "-"
    if abs(n - round(n)) < 0.000001:
        return f"{int(round(n)):,}"
    return f"{n:,.2f}"


def delta_text(delta: Optional[float], pct: Optional[float], unit: str = "") -> Tuple[str, str]:
    if delta is None:
        return "정보 없음", "neu"
    arrow = "▲" if delta > 0 else "▼" if delta < 0 else "■"
    cls = "pos" if delta > 0 else "neg" if delta < 0 else "neu"
    delta_str = f"{delta:+,.2f}" if abs(delta - round(delta)) > 0.001 else f"{int(round(delta)):+,}"
    unit_part = f" {unit}" if unit else ""
    pct_part = f" ({pct:+.2f}%)" if pct is not None else ""
    return f"{arrow} {delta_str}{unit_part}{pct_part}", cls


def change_class(value: Optional[float]) -> str:
    if value is None:
        return "neu"
    if value > 0:
        return "pos"
    if value < 0:
        return "neg"
    return "neu"


def metric_card(label: str, value: str, delta: Optional[float], pct: Optional[float], sub_prefix: str = "전일 대비", unit: str = "", source: Optional[str] = None):
    text, cls = delta_text(delta, pct, unit=unit)
    source_html = f'<div class="source-note">출처: {source}</div>' if source else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub_prefix} <span class="{cls}">{text}</span></div>
            {source_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_market_symbol(code: str, market: str) -> str:
    code = code.zfill(6)
    return f"{code}.KS" if market == "KOSPI" else f"{code}.KQ"


def request_text(url: str, timeout: int = 15, encoding: Optional[str] = None) -> str:
    res = requests.get(url, headers=HEADERS, timeout=timeout)
    res.raise_for_status()
    if encoding:
        res.encoding = encoding
    elif not res.encoding:
        res.encoding = res.apparent_encoding or "utf-8"
    return res.text


@st.cache_data(ttl=300)
def get_yf_snapshot(symbol: str, name: Optional[str] = None) -> Dict:
    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return {"name": name or symbol, "value": None, "prev": None, "delta": None, "pct": None, "source": "Yahoo Finance"}
        hist = hist.dropna(subset=["Close"])
        latest = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None
        delta = latest - prev if prev is not None else None
        pct = ((delta / prev) * 100) if prev not in (None, 0) else None
        return {"name": name or symbol, "value": latest, "prev": prev, "delta": delta, "pct": pct, "source": "Yahoo Finance"}
    except Exception:
        return {"name": name or symbol, "value": None, "prev": None, "delta": None, "pct": None, "source": None}


@st.cache_data(ttl=300)
def get_naver_index_snapshot(code: str, label: str) -> Dict:
    url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
    try:
        html = request_text(url, encoding="euc-kr")
        soup = BeautifulSoup(html, "html.parser")
        now_value = soup.find("em", id="now_value") or soup.find("span", id="now_value")
        latest = safe_float(now_value.get_text(" ", strip=True) if now_value else None)

        change_block = soup.select_one("#change_value_and_rate")
        if change_block:
            spans = [s.get_text(" ", strip=True) for s in change_block.find_all(["span", "em"]) if s.get_text(" ", strip=True)]
            delta = None
            pct = None
            for t in spans:
                if pct is None and "%" in t:
                    pct = safe_float(t)
                elif delta is None:
                    delta = safe_float(t)
            block_text = change_block.get_text(" ", strip=True)
            classes = " ".join(change_block.get("class", []))
            is_down = "하락" in block_text or "down" in classes
            if is_down and delta is not None and delta > 0:
                delta = -delta
            if is_down and pct is not None and pct > 0:
                pct = -pct
        else:
            delta, pct = None, None

        if latest is not None:
            prev = latest - delta if delta is not None else None
            return {"name": label, "value": latest, "prev": prev, "delta": delta, "pct": pct, "source": "Naver Finance"}
    except Exception:
        pass
    return {"name": label, "value": None, "prev": None, "delta": None, "pct": None, "source": None}


@st.cache_data(ttl=300)
def get_index_snapshot(kind: str) -> Dict:
    if kind == "KOSPI":
        yf_data = get_yf_snapshot("^KS11", "KOSPI")
        if yf_data.get("value") is not None:
            return yf_data
        return get_naver_index_snapshot("KOSPI", "KOSPI")
    if kind == "KOSDAQ":
        yf_data = get_yf_snapshot("^KQ11", "KOSDAQ")
        if yf_data.get("value") is not None:
            return yf_data
        return get_naver_index_snapshot("KOSDAQ", "KOSDAQ")
    return {"name": kind, "value": None, "prev": None, "delta": None, "pct": None, "source": None}


@st.cache_data(ttl=300)
def get_naver_index_detail(code: str) -> Dict:
    url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
    out = {"volume": None, "amount": None, "high": None, "low": None, "open": None}
    try:
        html = request_text(url, encoding="euc-kr")
        tables = pd.read_html(html)
        for df in tables:
            flat = " ".join(map(str, df.columns)) + " " + " ".join(map(str, df.iloc[0].tolist()))
            if any(k in flat for k in ["거래량", "거래대금", "고가", "저가", "시가"]):
                # 구조가 가로일 수도 세로일 수도 있어서 텍스트 풀스캔
                text = re.sub(r"\s+", " ", flat)
                vol = re.search(r"거래량\s*([0-9,]+)", text)
                amt = re.search(r"거래대금\s*([0-9,]+)", text)
                hi = re.search(r"고가\s*([0-9,]+(?:\.\d+)?)", text)
                lo = re.search(r"저가\s*([0-9,]+(?:\.\d+)?)", text)
                op = re.search(r"시가\s*([0-9,]+(?:\.\d+)?)", text)
                if vol:
                    out["volume"] = safe_int(vol.group(1))
                if amt:
                    out["amount"] = safe_float(amt.group(1))
                if hi:
                    out["high"] = safe_float(hi.group(1))
                if lo:
                    out["low"] = safe_float(lo.group(1))
                if op:
                    out["open"] = safe_float(op.group(1))
                break
    except Exception:
        pass
    return out


@st.cache_data(ttl=3600)
def get_bok_base_rate() -> Dict:
    url = "https://www.bok.or.kr/portal/singl/baseRate/list.do?menuNo=200643"
    try:
        html = request_text(url)
        rows = re.findall(r"(20\d{2})\s*(\d{2})월\s*(\d{2})일\s*([0-9.]+)", html)
        if len(rows) >= 2:
            latest = float(rows[0][3])
            prev = float(rows[1][3])
            delta = latest - prev
            pct = ((delta / prev) * 100) if prev else None
            return {"date": f"{rows[0][0]}-{rows[0][1]}-{rows[0][2]}", "value": latest, "delta": delta, "pct": pct, "source": "한국은행"}
    except Exception:
        pass
    return {"date": None, "value": None, "delta": None, "pct": None, "source": None}


@st.cache_data(ttl=3600)
def get_ccsi_from_snapshot() -> Dict:
    urls = [
        "https://snapshot.bok.or.kr/dashboard/C8",
        "https://www.bok.or.kr/portal/bbs/B0000501/list.do?menuNo=201264",
    ]
    for url in urls:
        try:
            html = request_text(url)
            compact = re.sub(r"\s+", " ", html)
            m = re.search(r"CCSI[^0-9]{0,120}([0-9]{2,3}\.[0-9])[^0-9]{0,120}전월\s*대비\s*([+-]?[0-9]{1,2}\.[0-9])", compact)
            if m:
                value = float(m.group(1))
                delta = float(m.group(2))
                prev = value - delta
                pct = ((delta / prev) * 100) if prev else None
                date_match = re.search(r"(20\d{2})년\s*(\d{1,2})월", compact)
                date_txt = f"{date_match.group(1)}-{int(date_match.group(2)):02d}" if date_match else None
                return {"date": date_txt, "value": value, "delta": delta, "pct": pct, "source": "한국은행"}
        except Exception:
            continue
    return {"date": None, "value": None, "delta": None, "pct": None, "source": None}


@st.cache_data(ttl=900)
def get_gold_prices() -> Dict:
    # 1) 한국금거래소 사업자 페이지: 순금시세/변동/등락률이 비교적 잘 노출됨
    # 2) 한국금거래소 국내시세 페이지: 3.75g 기준값 보조
    results = {
        "source": None,
        "sell": None,
        "buy": None,
        "sell_delta": None,
        "buy_delta": None,
        "sell_pct": None,
        "buy_pct": None,
        "note": None,
    }

    candidates = [
        ("https://www.exgold.co.kr/", "한국금거래소 사업자전용"),
        ("https://www.exgold.co.kr/price/inquiry/domestic", "한국금거래소 국내시세"),
        ("https://m.koreagoldx.co.kr/price/gold", "한국금거래소 모바일"),
    ]

    page_texts = []
    for url, source in candidates:
        try:
            text = unescape(request_text(url, timeout=15))
            compact = re.sub(r"\s+", " ", text)
            page_texts.append((compact, source))

            # exgold 사업자 페이지 패턴: 순금시세, 897,000원, up 5,000, 0.56%
            m = re.search(
                r"순금시세\s*,?\s*([0-9,]{6,10})원\s*,?\s*(?:up|down)?\s*([+-]?[0-9,]{1,10})?\s*,?\s*([+-]?[0-9.]+)%",
                compact,
                re.IGNORECASE,
            )
            if m:
                buy = safe_int(m.group(1))
                buy_delta_abs = safe_int(m.group(2))
                buy_pct = safe_float(m.group(3))
                if "down" in m.group(0).lower() and buy_delta_abs is not None:
                    buy_delta = -abs(buy_delta_abs)
                    buy_pct = -abs(buy_pct) if buy_pct is not None else None
                else:
                    buy_delta = buy_delta_abs
                # 사업자 매입 시세는 일반적으로 팔때(내가 팔 때)에 가까움
                results.update({
                    "source": source,
                    "buy": buy,
                    "buy_delta": buy_delta,
                    "buy_pct": buy_pct,
                })

            # 모바일 패턴: 1,073,000 885,000 650,500 ... => 보통 살때/팔때/18K 순서
            nums = [safe_int(x) for x in re.findall(r"\b([0-9]{3},[0-9]{3}|[0-9]{1,3},[0-9]{3},[0-9]{3})\b", compact)]
            nums = [n for n in nums if n and 700_000 <= n <= 1_500_000]
            if nums:
                sell_like = max(nums)  # 일반적으로 살때가 더 큼
                buy_like = min(nums)
                if results["sell"] is None and sell_like > buy_like:
                    results["sell"] = sell_like
                    if results["source"] is None:
                        results["source"] = source
                if results["buy"] is None:
                    results["buy"] = buy_like
                    if results["source"] is None:
                        results["source"] = source
        except Exception:
            continue

    # 보조 추정: 살때 값이 없으면 buy 값 + 대략 스프레드(최근 공개 시세 범위 기반) 대신, 다른 페이지 숫자 활용
    if results["sell"] is None:
        for compact, source in page_texts:
            vals = [safe_int(x) for x in re.findall(r"\b([0-9]{3},[0-9]{3}|[0-9]{1,3},[0-9]{3},[0-9]{3})\b", compact)]
            vals = [n for n in vals if n and 900_000 <= n <= 1_500_000]
            if vals:
                results["sell"] = max(vals)
                results["source"] = results["source"] or source
                break

    if results["buy"] is None:
        for compact, source in page_texts:
            vals = [safe_int(x) for x in re.findall(r"\b([0-9]{3},[0-9]{3}|[0-9]{1,3},[0-9]{3},[0-9]{3})\b", compact)]
            vals = [n for n in vals if n and 700_000 <= n <= 1_000_000]
            if vals:
                results["buy"] = min(vals)
                results["source"] = results["source"] or source
                break

    if results["sell"] is None and results["buy"] is None:
        results["note"] = "금시세 페이지 구조 변경으로 파싱 실패"

    return results


@st.cache_data(ttl=1800)
def get_opinet_avg_prices() -> Dict:
    api_key = None
    try:
        api_key = st.secrets.get("OPINET_API_KEY") or os.getenv("OPINET_API_KEY", "")
    except Exception:
        api_key = os.getenv("OPINET_API_KEY", "")

    if not api_key:
        return {"gasoline": None, "diesel": None, "note": "OPINET_API_KEY 필요", "source": "오피넷"}

    api_key = str(api_key).strip().strip('"').strip("'")
    url = f"https://www.opinet.co.kr/api/avgAllPrice.do?out=json&certkey={api_key}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
        data = res.json()
        rows = []
        if isinstance(data, dict):
            if isinstance(data.get("RESULT"), list):
                rows = data.get("RESULT", [])
            else:
                result = data.get("RESULT", {})
                if isinstance(result, dict) and result.get("OIL"):
                    rows = result.get("OIL", [])
                elif isinstance(result, dict) and result.get("CODE") not in (None, "00"):
                    return {"gasoline": None, "diesel": None, "note": f"오피넷 오류 코드: {result.get('CODE')}", "source": "오피넷"}

        mapping = {}
        for row in rows:
            prod = row.get("PRODCD")
            if prod in {"B027", "D047"}:
                mapping[prod] = {
                    "name": row.get("PRODNM"),
                    "price": safe_float(row.get("PRICE")),
                    "diff": safe_float(row.get("DIFF")),
                    "date": row.get("TRADE_DT"),
                }

        if not mapping:
            return {
                "gasoline": None,
                "diesel": None,
                "note": f"오피넷 응답 파싱 실패: {str(data)[:180]}",
                "source": "오피넷",
            }

        return {"gasoline": mapping.get("B027"), "diesel": mapping.get("D047"), "note": None, "source": "오피넷"}
    except Exception as e:
        return {"gasoline": None, "diesel": None, "note": f"오피넷 조회 실패: {e}", "source": "오피넷"}


@st.cache_data(ttl=900)
def get_news() -> List[Dict]:
    items: List[Dict] = []
    seen = set()

    for source_name, feed_url in NEWS_FEEDS:
        try:
            xml_text = request_text(feed_url, timeout=12)
            feed = feedparser.parse(xml_text)
            for entry in feed.entries[:8]:
                title = unescape(entry.get("title", "")).strip()
                link = entry.get("link", "").strip()
                published = entry.get("published", "") or entry.get("updated", "")
                if not title or not link:
                    continue
                key = (title, link)
                if key in seen:
                    continue
                seen.add(key)
                items.append({
                    "source": source_name,
                    "title": re.sub(r"\s+-\s+Google 뉴스$", "", title),
                    "link": link,
                    "published": published,
                })
        except Exception:
            continue

    priority_order = {
        "경향신문": 0,
        "한겨레": 1,
        "매일경제 경제": 2,
        "매일경제 증권": 2,
        "한국경제 경제": 3,
        "한국경제 증권": 3,
        "서울경제 경제": 4,
        "서울경제 증권": 4,
        "중앙일보 경제": 5,
        "한국경제 IT": 6,
        "서울경제 IT": 6,
        "IT": 6,
    }
    items.sort(key=lambda x: (priority_order.get(x["source"], 99), x.get("published", "")))
    return items[:18]


@st.cache_data(ttl=1800)
def get_stock_master() -> pd.DataFrame:
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"
    try:
        html = requests.get(url, headers=HEADERS, timeout=25)
        html.encoding = "euc-kr"
        df = pd.read_html(html.text)[0]
        if "종목코드" in df.columns and "회사명" in df.columns:
            keep_cols = [c for c in ["회사명", "종목코드", "업종", "주요제품", "상장일"] if c in df.columns]
            out = df[keep_cols].copy()
            out["종목코드"] = out["종목코드"].astype(str).str.zfill(6)
            return out
    except Exception:
        pass

    rows = []
    for name, symbol in {**KOSPI_TOP_50, **KOSDAQ_TOP_50, **ETF_TOP}.items():
        code, suffix = symbol.split(".")
        rows.append({"회사명": name, "종목코드": code, "시장": "KOSPI" if suffix == "KS" else "KOSDAQ"})
    return pd.DataFrame(rows)


@st.cache_data(ttl=1800)
def enrich_market_info(master_df: pd.DataFrame) -> pd.DataFrame:
    df = master_df.copy()
    if "시장" not in df.columns:
        df["시장"] = ""
    kospi_codes = {v.split(".")[0] for v in KOSPI_TOP_50.values()} | {v.split(".")[0] for v in ETF_TOP.values()}
    kosdaq_codes = {v.split(".")[0] for v in KOSDAQ_TOP_50.values()}
    def infer_market(code: str) -> str:
        code = str(code).zfill(6)
        if code in kosdaq_codes:
            return "KOSDAQ"
        if code in kospi_codes:
            return "KOSPI"
        return "KOSPI"
    df["시장"] = df["시장"].replace("", pd.NA)
    df["시장"] = df["시장"].fillna(df["종목코드"].apply(infer_market))
    return df


@st.cache_data(ttl=1800)
def get_watchlist_table(tickers: Dict[str, str]) -> pd.DataFrame:
    rows = []
    for name, symbol in tickers.items():
        snap = get_yf_snapshot(symbol, name=name)
        if snap.get("value") is None and symbol.endswith(".KQ"):
            code = symbol.split(".")[0]
            # 검색 fallback: 네이버 종목 페이지 파싱
            try:
                html = request_text(f"https://finance.naver.com/item/main.naver?code={code}", encoding="euc-kr")
                soup = BeautifulSoup(html, "html.parser")
                no_today = soup.select_one("p.no_today span.blind")
                blind_spans = [s.get_text(strip=True) for s in soup.select("p.no_exday span.blind")]
                latest = safe_float(no_today.get_text(strip=True) if no_today else None)
                delta = safe_float(blind_spans[0]) if blind_spans else None
                pct = safe_float(blind_spans[1]) if len(blind_spans) > 1 else None
                exday_text = soup.select_one("p.no_exday")
                if exday_text and exday_text.get_text(" ", strip=True):
                    txt = exday_text.get_text(" ", strip=True)
                    if "하락" in txt and delta is not None and delta > 0:
                        delta = -delta
                    if "하락" in txt and pct is not None and pct > 0:
                        pct = -pct
                snap = {"value": latest, "delta": delta, "pct": pct}
            except Exception:
                pass
        rows.append({
            "종목": name,
            "티커": symbol,
            "현재가": snap.get("value"),
            "전일대비": snap.get("delta"),
            "등락률(%)": snap.get("pct"),
        })
    return pd.DataFrame(rows)


def format_watchlist_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out
    out["현재가"] = out["현재가"].apply(price_with_commas)
    out["전일대비"] = out["전일대비"].apply(lambda x: "-" if x is None or (isinstance(x, float) and math.isnan(x)) else (f"{int(round(x)):+,}" if abs(x - round(x)) < 0.00001 else f"{x:+,.2f}"))
    out["등락률(%)"] = out["등락률(%)"].apply(lambda x: "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}")
    return out


def render_search_result(symbol: str, label: str):
    snap = get_yf_snapshot(symbol, label)
    if snap.get("value") is None:
        code = symbol.split(".")[0]
        try:
            html = request_text(f"https://finance.naver.com/item/main.naver?code={code}", encoding="euc-kr")
            soup = BeautifulSoup(html, "html.parser")
            no_today = soup.select_one("p.no_today span.blind")
            blind_spans = [s.get_text(strip=True) for s in soup.select("p.no_exday span.blind")]
            latest = safe_float(no_today.get_text(strip=True) if no_today else None)
            delta = safe_float(blind_spans[0]) if blind_spans else None
            pct = safe_float(blind_spans[1]) if len(blind_spans) > 1 else None
            txt = soup.select_one("p.no_exday")
            text = txt.get_text(" ", strip=True) if txt else ""
            if "하락" in text and delta is not None and delta > 0:
                delta = -delta
            if "하락" in text and pct is not None and pct > 0:
                pct = -pct
            snap = {"value": latest, "delta": delta, "pct": pct, "source": "Naver Finance"}
        except Exception:
            pass
    delta_txt, cls = delta_text(snap.get("delta"), snap.get("pct"))
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">관심 종목 현재가</div>
            <div class="metric-value">{label} · {price_with_commas(snap.get('value'))}</div>
            <div class="metric-sub"><span class="{cls}">{delta_txt}</span></div>
            <div class="source-note">티커: {symbol} / 출처: {snap.get('source') or '-'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def get_deposit_info() -> Dict:
    url = "https://finance.naver.com/sise/sise_deposit.naver"
    try:
        html = request_text(url, encoding="euc-kr")
        compact = re.sub(r"\s+", " ", html)
        deposit = None
        margin = None
        m1 = re.search(r"고객예탁금\s*([0-9,]+)", compact)
        m2 = re.search(r"신용잔고\s*([0-9,]+)", compact)
        if m1:
            deposit = safe_float(m1.group(1))
        if m2:
            margin = safe_float(m2.group(1))
        return {"deposit": deposit, "margin": margin, "source": "Naver Finance"}
    except Exception:
        return {"deposit": None, "margin": None, "source": None}


@st.cache_data(ttl=1800)
def get_investor_trend(market: str = "KOSPI") -> Dict:
    sosok = "0" if market == "KOSPI" else "1"
    url = f"https://finance.naver.com/sise/investorDealTrendDay.naver?sosok={sosok}"
    try:
        html = request_text(url, encoding="euc-kr")
        tables = pd.read_html(html)
        for df in tables:
            cols = [str(c) for c in df.columns]
            joined = " ".join(cols)
            if "개인" in joined and "외국인" in joined and "기관계" in joined:
                work = df.copy()
                work.columns = [str(c).replace("Unnamed: 0", "일자") for c in work.columns]
                work = work.dropna(how="all")
                work = work[work.iloc[:, 0].astype(str).str.contains(r"\d{4}\.\d{2}\.\d{2}", regex=True, na=False)]
                if work.empty:
                    continue
                row = work.iloc[0]
                date_val = str(row.iloc[0])
                foreign_val = safe_float(row[[c for c in work.columns if "외국인" in c][0]])
                inst_val = safe_float(row[[c for c in work.columns if "기관계" in c][0]])
                person_val = safe_float(row[[c for c in work.columns if "개인" in c][0]])
                return {
                    "date": date_val,
                    "personal": person_val,
                    "foreign": foreign_val,
                    "institution": inst_val,
                    "source": "Naver Finance",
                }
    except Exception:
        pass
    return {"date": None, "personal": None, "foreign": None, "institution": None, "source": None}


def build_market_summary_df(kospi: Dict, kosdaq: Dict) -> pd.DataFrame:
    kospi_detail = get_naver_index_detail("KOSPI")
    kosdaq_detail = get_naver_index_detail("KOSDAQ")
    deposit = get_deposit_info()
    trend_kospi = get_investor_trend("KOSPI")
    trend_kosdaq = get_investor_trend("KOSDAQ")

    df = pd.DataFrame(
        {
            "구분": [
                "종합주가지수",
                "거래량",
                "거래대금",
                "고객예탁금",
                "신용잔고",
                "외국인 동향",
                "기관 동향",
                "개인 동향",
            ],
            "코스피": [
                fmt_number(kospi.get("value"), 2),
                fmt_int(kospi_detail.get("volume")),
                fmt_amount_kr(kospi_detail.get("amount")),
                fmt_amount_kr(deposit.get("deposit"), "억원"),
                fmt_amount_kr(deposit.get("margin"), "억원"),
                fmt_amount_kr(trend_kospi.get("foreign"), "백만원"),
                fmt_amount_kr(trend_kospi.get("institution"), "백만원"),
                fmt_amount_kr(trend_kospi.get("personal"), "백만원"),
            ],
            "코스닥": [
                fmt_number(kosdaq.get("value"), 2),
                fmt_int(kosdaq_detail.get("volume")),
                fmt_amount_kr(kosdaq_detail.get("amount")),
                "-",
                "-",
                fmt_amount_kr(trend_kosdaq.get("foreign"), "백만원"),
                fmt_amount_kr(trend_kosdaq.get("institution"), "백만원"),
                fmt_amount_kr(trend_kosdaq.get("personal"), "백만원"),
            ],
        }
    )
    return df


def init_more_state(key: str, default: int = 10):
    if key not in st.session_state:
        st.session_state[key] = default


def render_expandable_table(title: str, tickers: Dict[str, str], state_key: str):
    init_more_state(state_key, 10)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    items = list(tickers.items())
    visible = min(st.session_state[state_key], len(items))
    sub = dict(items[:visible])
    table = get_watchlist_table(sub)
    st.dataframe(format_watchlist_for_display(table), use_container_width=True, hide_index=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        if visible < len(items):
            if st.button("더보기", key=f"btn_more_{state_key}"):
                st.session_state[state_key] = min(st.session_state[state_key] + 10, len(items))
                st.rerun()
        elif visible > 10:
            if st.button("접기", key=f"btn_less_{state_key}"):
                st.session_state[state_key] = 10
                st.rerun()
    with c2:
        st.caption(f"현재 {visible}개 / 전체 {len(items)}개")


# Header
kr_tz = pytz.timezone("Asia/Seoul")
ny_tz = pytz.timezone("America/New_York")
now_kr = datetime.now(kr_tz)
now_ny = datetime.now(ny_tz)
weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now_kr.weekday()]
weekday_ny = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][now_ny.weekday()]

st.title("경제 대시보드(Economy Dash board)")
st.markdown(
    f"""
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
        <div class="time-chip">한국 시간 · {now_kr.strftime('%Y-%m-%d')} ({weekday_kr}) {now_kr.strftime('%H:%M:%S')}</div>
        <div class="time-chip">미국 동부 시간 · {now_ny.strftime('%Y-%m-%d')} ({weekday_ny}) {now_ny.strftime('%H:%M:%S')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("자동 새로고침: 60초")

# Core metrics
kospi = get_index_snapshot("KOSPI")
kosdaq = get_index_snapshot("KOSDAQ")
crude = get_yf_snapshot("BZ=F", "브렌트유")
base_rate = get_bok_base_rate()
ccsi = get_ccsi_from_snapshot()
gold = get_gold_prices()
opinet = get_opinet_avg_prices()

st.markdown('<div class="section-title">오늘의 핵심 지표</div>', unsafe_allow_html=True)
row1 = st.columns(4)
with row1[0]:
    metric_card("오늘의 코스피", fmt_number(kospi.get("value"), 2), kospi.get("delta"), kospi.get("pct"), source=kospi.get("source"))
with row1[1]:
    metric_card("오늘의 코스닥", fmt_number(kosdaq.get("value"), 2), kosdaq.get("delta"), kosdaq.get("pct"), source=kosdaq.get("source"))
with row1[2]:
    metric_card("한국 금시세 1돈 · 살때", fmt_price_krw(gold.get("sell"), 0), gold.get("sell_delta"), gold.get("sell_pct"), unit="원", source=gold.get("source"))
with row1[3]:
    metric_card("한국 금시세 1돈 · 팔때", fmt_price_krw(gold.get("buy"), 0), gold.get("buy_delta"), gold.get("buy_pct"), unit="원", source=gold.get("source"))

if gold.get("note"):
    st.caption(f"금시세 참고: {gold.get('note')}")

row2 = st.columns(4)
with row2[0]:
    metric_card(
        "한국 기준금리",
        f"{fmt_number(base_rate.get('value'), 2)}%" if base_rate.get("value") is not None else "-",
        base_rate.get("delta"),
        base_rate.get("pct"),
        sub_prefix="직전 변경 대비",
        unit="%p",
        source=base_rate.get("source"),
    )
    st.caption(f"최근 변경일: {base_rate.get('date') or '-'}")
with row2[1]:
    metric_card(
        "소비심리지수(CCSI)",
        fmt_number(ccsi.get("value"), 1),
        ccsi.get("delta"),
        ccsi.get("pct"),
        sub_prefix="전월 대비",
        unit="p",
        source=ccsi.get("source"),
    )
    st.caption(f"기준월: {ccsi.get('date') or '-'}")
with row2[2]:
    metric_card(
        "국제유가 · 브렌트유",
        f"${fmt_number(crude.get('value'), 2)} / bbl" if crude.get("value") is not None else "-",
        crude.get("delta"),
        crude.get("pct"),
        unit="달러",
        source=crude.get("source"),
    )
with row2[3]:
    g = opinet.get("gasoline")
    d = opinet.get("diesel")
    if g and d:
        g_prev = (g.get('price') - g.get('diff')) if g.get('price') is not None and g.get('diff') is not None else None
        d_prev = (d.get('price') - d.get('diff')) if d.get('price') is not None and d.get('diff') is not None else None
        g_pct = ((g['diff'] / g_prev) * 100) if g_prev not in (None, 0) else None
        d_pct = ((d['diff'] / d_prev) * 100) if d_prev not in (None, 0) else None
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">한국 기준 유가</div>
                <div class="metric-value" style="font-size:20px;">휘발유 {fmt_price_krw(g.get('price'), 0)} / 경유 {fmt_price_krw(d.get('price'), 0)}</div>
                <div class="metric-sub">휘발유 <span class="{change_class(g.get('diff'))}">{delta_text(g.get('diff'), g_pct, '원')[0]}</span></div>
                <div class="metric-sub">경유 <span class="{change_class(d.get('diff'))}">{delta_text(d.get('diff'), d_pct, '원')[0]}</span></div>
                <div class="source-note">출처: {opinet.get('source')} {('· 기준일 ' + str(g.get('date'))) if g.get('date') else ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">한국 기준 유가</div>
                <div class="metric-value" style="font-size:22px;">API 키 확인 필요</div>
                <div class="metric-sub">{opinet.get('note') or '오피넷 데이터를 불러오지 못했습니다.'}</div>
                <div class="source-note">출처: {opinet.get('source')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Market summary
st.markdown('<div class="section-title">오늘의 한국증시</div>', unsafe_allow_html=True)
st.markdown('<div class="summary-caption">거래대금은 지수 페이지, 고객예탁금·신용잔고·투자주체 동향은 네이버 금융 공개 페이지 기준으로 간략 요약합니다.</div>', unsafe_allow_html=True)
summary_df = build_market_summary_df(kospi, kosdaq)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# Watch tables
left, right = st.columns(2)
with left:
    render_expandable_table("코스피 주요 50개 종목", KOSPI_TOP_50, "kospi_visible")
with right:
    render_expandable_table("코스닥 주요 50개 종목", KOSDAQ_TOP_50, "kosdaq_visible")

st.markdown('<div class="section-title">주요 ETF 10개 종목</div>', unsafe_allow_html=True)
etf_df = get_watchlist_table(ETF_TOP)
st.dataframe(format_watchlist_for_display(etf_df), use_container_width=True, hide_index=True)

# Search area
st.markdown('<div class="section-title">관심있는 종목 주가 검색</div>', unsafe_allow_html=True)
st.markdown('<div class="search-box-wrap">', unsafe_allow_html=True)
st.caption("회사명 또는 6자리 종목코드를 입력하면 검색됩니다. 예: 삼성전자, 005930")
master_df = enrich_market_info(get_stock_master())
query = st.text_input("종목 검색", value="", placeholder="예: 삼성전자 / SK하이닉스 / 005930", label_visibility="collapsed")

if query.strip():
    q = query.strip().lower()
    work = master_df.copy()
    work["회사명_l"] = work["회사명"].astype(str).str.lower()
    work["종목코드_s"] = work["종목코드"].astype(str).str.zfill(6)
    mask = work["회사명_l"].str.contains(q, na=False) | work["종목코드_s"].str.contains(q, na=False)
    results = work.loc[mask, ["회사명", "종목코드", "시장"]].drop_duplicates().head(20)
    if results.empty:
        st.warning("검색 결과가 없습니다. 회사명 일부 또는 6자리 종목코드로 다시 검색해 주세요.")
    else:
        options = [f"{row['회사명']} ({row['종목코드']}, {row['시장']})" for _, row in results.iterrows()]
        selected = st.selectbox("검색 결과", options=options, index=0)
        selected_row = results.iloc[options.index(selected)]
        symbol = normalize_market_symbol(selected_row["종목코드"], selected_row["시장"])
        render_search_result(symbol, selected_row["회사명"])
else:
    st.info("원하는 종목명을 입력하면 현재가와 등락을 바로 확인할 수 있습니다.")
st.markdown('</div>', unsafe_allow_html=True)

# News + quick links
news_col, link_col = st.columns([1.4, 0.6])
with news_col:
    st.markdown('<div class="section-title">주요 경제뉴스</div>', unsafe_allow_html=True)
    news_items = get_news()
    if not news_items:
        st.warning("뉴스를 불러오지 못했습니다. RSS 차단 또는 일시 오류일 수 있습니다. 잠시 후 다시 시도해 주세요.")
    else:
        for item in news_items[:12]:
            st.markdown(
                f"""
                <div class="news-card">
                    <a href="{item['link']}" target="_blank">{item['title']}</a>
                    <div class="news-source">{item['source']} {('· ' + item['published']) if item.get('published') else ''}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
with link_col:
    st.markdown('<div class="section-title">주요 경제정보 확인 사이트</div>', unsafe_allow_html=True)
    st.markdown('<div class="link-card">', unsafe_allow_html=True)
    for title, url in QUICK_LINKS:
        st.markdown(f'<a href="{url}" target="_blank">{title}</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Sidebar guidance
with st.sidebar:
    st.header("설정 안내")
    st.write("이 대시보드는 60초마다 자동 새로고침됩니다.")
    st.write("오피넷 키는 Streamlit Secrets에 문자열로 넣어야 합니다.")
    st.code('OPINET_API_KEY = "발급받은인증키"', language="toml")
    st.caption("배포 위치: .streamlit/secrets.toml 또는 Streamlit Cloud Secrets")
    st.caption("키를 저장한 뒤에는 앱 재시작 또는 재배포를 한 번 해주세요.")
    st.caption("금시세는 공식 공개 페이지를 스크래핑하는 방식이라, 사이트 구조가 바뀌면 일시적으로 비어 보일 수 있습니다.")
    st.caption("뉴스는 언론사 RSS를 우선 사용하고 일부는 Google News RSS를 보조로 사용합니다.")
    st.caption("한국증시 요약 표의 투자주체 동향 단위는 백만원입니다.")

st.markdown('<div class="footer-box">© miyawa 제작</div>', unsafe_allow_html=True)
