import math
import re
from datetime import datetime

import pandas as pd
import pytz
import requests
import streamlit as st
import yfinance as yf
import feedparser

st.set_page_config(page_title="경제 대시보드", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

st.markdown("""
<style>
:root{
  --text:#f8fafc;
  --muted:#a8b4c7;
  --green:#3ee17b;
  --red:#ff6b6b;
  --btn-bg:#eef3fb;
  --btn-text:#0b1220;
  --btn-border:#c8d4e6;
}

html, body, [data-testid="stAppViewContainer"]{
  background: linear-gradient(180deg,#020817 0%, #071122 100%);
  color: var(--text);
}

.block-container{
  padding-top: 4rem !important;
  padding-bottom: 2.2rem;
  max-width: 1440px;
}

.main-title{
  font-size: 2rem;
  line-height: 1.16;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 0.85rem 0;
  word-break: keep-all;
}
.main-title .en{
  font-size: .72em;
  display: inline-block;
  opacity: .92;
  font-weight: 700;
}

.top-time{
  background: rgba(15,29,51,.72);
  border:1px solid rgba(80,110,150,.30);
  border-radius: 14px;
  padding: 11px 15px;
  margin: 8px 0 12px 0;
  color: #edf2f7;
  font-weight: 700;
  font-size: .98rem;
}

.section-title{
  font-size: 1.5rem;
  font-weight: 800;
  margin: 1.1rem 0 .8rem 0;
  color: #fff;
}

.card{
  background: linear-gradient(180deg, rgba(17,32,58,.96) 0%, rgba(28,40,64,.96) 100%);
  border: 1px solid rgba(89,115,156,.42);
  border-radius: 18px;
  padding: 16px 16px 13px 16px;
  min-height: 162px;
  box-shadow: 0 16px 32px rgba(0,0,0,.18);
  margin-bottom: 16px;
}
.card h4{
  margin: 0 0 .65rem 0;
  font-size: .98rem;
  line-height: 1.32;
  color: #ffffff;
  font-weight: 800;
}
.card .value{
  font-size: 1.12rem;
  line-height: 1.35;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: .5rem;
  word-break: keep-all;
}
.card .value.big{
  font-size: 1.55rem;
  line-height: 1.16;
  font-weight: 900;
}
.card .sub{
  font-size: .96rem;
  font-weight: 800;
  color: #e8edf5;
  line-height: 1.4;
}
.card .src{
  margin-top: .65rem;
  color: var(--muted);
  font-size: .84rem;
}
.card .note{
  margin-top: .45rem;
  color: #c7d2e3;
  font-size: .86rem;
  line-height: 1.4;
}
.up{ color: var(--green); }
.down{ color: var(--red); }
.flat{ color: #cbd5e1; }

div[data-testid="stHorizontalBlock"] > div{
  padding-right: 8px;
  padding-left: 8px;
}
[data-testid="column"]{
  padding-bottom: 8px;
}

.news-wrap{
  display:flex;
  flex-direction:column;
  gap:12px;
}
.news-item{
  display:block;
  background: rgba(20,38,64,.88);
  border:1px solid rgba(74,101,141,.34);
  border-radius:14px;
  padding:13px 14px;
  color:#f5f7fb !important;
  text-decoration:none;
  line-height:1.45;
}
.news-item:hover{
  background: rgba(26,46,76,.98);
}
.news-source{
  display:block;
  margin-top:4px;
  font-size:.84rem;
  color: var(--muted);
}
.link-list a{
  display:block;
  margin:0 0 12px 0;
  color:#7db4ff !important;
  text-decoration:none;
  line-height:1.5;
}

.market-mini{
  width:100%;
  border-collapse: collapse;
  margin-top: 8px;
  border-radius: 14px;
  overflow: hidden;
}
.market-mini th, .market-mini td{
  border-bottom: 1px solid rgba(90,110,139,.25);
  padding: 10px 10px;
  font-size: .94rem;
  text-align:left;
}
.market-mini th{
  color:#dbe7f7;
  background: rgba(18,31,52,.72);
}
.market-mini td{
  color:#eef4ff;
  background: rgba(10,22,40,.26);
}

.footer{
  margin-top: 26px;
  padding-top: 16px;
  border-top:1px solid rgba(90,110,139,.25);
  color:#8ea0ba;
  text-align:center;
}

.stButton > button{
  border-radius: 12px !important;
  font-weight: 800 !important;
  color: var(--btn-text) !important;
  background: var(--btn-bg) !important;
  border: 1px solid var(--btn-border) !important;
}
.stButton > button:hover{
  color: var(--btn-text) !important;
  background: #f7f9fd !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button div{
  color: var(--btn-text) !important;
  opacity: 1 !important;
}

/* 검색창 글씨/placeholder */
.stTextInput input{
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  background: rgba(14,26,46,.72) !important;
}
.stTextInput input::placeholder{
  color: #9fb0c8 !important;
  opacity: 1 !important;
}
.stTextInput label p{
  color: #dbe6f6 !important;
}
[data-testid="stTextInput"] p{
  color: #dbe6f6 !important;
}

[data-testid="stDataFrame"]{
  border-radius: 14px;
  overflow:hidden;
}

@media (max-width: 900px){
  .block-container{
    padding-top: 4.4rem !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
  }
  .main-title{
    font-size: 1.58rem;
    line-height: 1.18;
    margin-bottom: .65rem;
  }
  .main-title .en{
    display:block;
    font-size: .72em;
    margin-top: 2px;
  }
  .section-title{
    font-size: 1.28rem;
  }
  .card{
    min-height:auto;
    margin-bottom:18px !important;
    padding:15px 15px 13px 15px;
  }
  .card h4{ font-size:.94rem; }
  .card .value{ font-size:1.04rem; }
  .card .value.big{ font-size:1.38rem; }
  .card .sub{ font-size:.93rem; }
  .top-time{ font-size:.92rem; }
  div[data-testid="stHorizontalBlock"]{
    gap: 12px !important;
  }
  div[data-testid="stHorizontalBlock"] > div{
    padding-right:0px;
    padding-left:0px;
  }
}
</style>
""", unsafe_allow_html=True)


def fmt_num(v, digits=2):
    if v is None:
        return "-"
    try:
        if math.isnan(v) or math.isinf(v):
            return "-"
    except Exception:
        pass
    return f"{v:,.{digits}f}"


def fmt_int(v):
    if v is None:
        return "-"
    try:
        if math.isnan(v) or math.isinf(v):
            return "-"
    except Exception:
        pass
    return f"{int(round(v)):,}"


def delta_html(diff=None, pct=None, unit="", prefix="전일 대비"):
    if diff is None:
        return f'{prefix} <span class="flat">정보 없음</span>'
    cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    arrow = "▲" if diff > 0 else "▼" if diff < 0 else "■"
    if pct is None:
        body = f"{arrow} {diff:+,.2f}{unit}"
    else:
        body = f"{arrow} {diff:+,.2f}{unit} ({pct:+.2f}%)"
    return f'{prefix} <span class="{cls}">{body}</span>'


def render_card(title, value, sub_html, source=None, note=None, big=True):
    value_class = "value big" if big else "value"
    html = [
        f'<div class="card"><h4>{title}</h4>',
        f'<div class="{value_class}">{value}</div>',
        f'<div class="sub">{sub_html}</div>',
    ]
    if source:
        html.append(f'<div class="src">출처: {source}</div>')
    if note:
        html.append(f'<div class="note">{note}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


@st.cache_data(ttl=60)
def yf_last_two(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=False)
        hist = hist.dropna(subset=["Close"])
        if len(hist) < 2:
            return None
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        diff = price - prev
        pct = (diff / prev * 100) if prev else None
        return {"price": price, "prev": prev, "diff": diff, "pct": pct}
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_fx_card_data():
    mapping = {
        "달러": "KRW=X",
        "위안": "CNYKRW=X",
        "엔": "JPYKRW=X",
        "유로": "EURKRW=X",
    }
    out = {}
    for name, ticker in mapping.items():
        row = yf_last_two(ticker)
        if row:
            out[name] = row
    return out


@st.cache_data(ttl=300)
def get_brent():
    return yf_last_two("BZ=F")


@st.cache_data(ttl=180)
def get_index(ticker):
    return yf_last_two(ticker)


@st.cache_data(ttl=3600)
def get_base_rate():
    urls = [
        "https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643",
        "https://www.bok.or.kr/portal/main/main.do",
    ]

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if not r.ok:
                continue
            text = re.sub(r"\s+", " ", r.text)

            # 기준금리 추이 목록 페이지 우선
            m = re.search(r"202[0-9].*?([0-9]+\.[0-9]+)\s*</", text)
            if m:
                v = float(m.group(1))
                if 0.5 <= v <= 10:
                    return {"ok": True, "value": v, "message": "직전 변경 대비 정보는 별도 미연결"}

            # 메인 페이지 fallback
            patterns = [
                r"한국은행기준금리\s*([0-9]+\.[0-9]+)\s*%",
                r"기준금리\s*([0-9]+\.[0-9]+)\s*%",
            ]
            for p in patterns:
                m2 = re.search(p, text)
                if m2:
                    v = float(m2.group(1))
                    if 0.5 <= v <= 10:
                        return {"ok": True, "value": v, "message": "직전 변경 대비 정보는 별도 미연결"}
        except Exception:
            continue

    return {"ok": False, "message": "기준금리 파싱 실패"}


@st.cache_data(ttl=1800)
def get_gold_kr():
    # 1차: 한국금거래소 계열
    candidate_urls = [
        "https://koreagoldx.co.kr/",
        "https://jongro.koreagoldx.co.kr/",
        "https://cheongna.koreagoldx.co.kr/",
        "https://m.koreagoldx.co.kr/price/gold",
        # 2차: 대체 공개 금시세 페이지
        "https://www.kgoldse.co.kr/",
        "https://www.goldsilvershop.co.kr/",
        "https://www.kumsise.com/",
    ]

    buy = None
    sell = None
    note = None

    for url in candidate_urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if not r.ok:
                continue
            text = re.sub(r"\s+", " ", r.text)

            # 패턴 1: 순금 Gold24k-3.75g 1,025,000원 ... 879,000원 ...
            p1 = re.search(
                r"순금(?:시세)?\s*Gold24k[-,]3[.,]75g\s*([0-9,]{5,})원?.{0,40}?([0-9,]{5,})원",
                text,
                re.IGNORECASE,
            )
            if p1:
                b = int(p1.group(1).replace(",", ""))
                s = int(p1.group(2).replace(",", ""))
                if 200000 <= b <= 3000000 and b != 0:
                    buy = b
                if 200000 <= s <= 3000000 and s != 0:
                    sell = s

            # 패턴 2: 내가 살때 / 내가 팔때
            if buy is None:
                for patt in [
                    r"내가\s*살\s*때[^0-9]{0,40}([0-9,]{5,})",
                    r"판매가[^0-9]{0,40}([0-9,]{5,})",
                ]:
                    m = re.search(patt, text)
                    if m:
                        v = int(m.group(1).replace(",", ""))
                        if 200000 <= v <= 3000000 and v != 0:
                            buy = v
                            break

            if sell is None:
                for patt in [
                    r"내가\s*팔\s*때[^0-9]{0,40}([0-9,]{5,})",
                    r"매입가[^0-9]{0,40}([0-9,]{5,})",
                ]:
                    m = re.search(patt, text)
                    if m:
                        v = int(m.group(1).replace(",", ""))
                        if 200000 <= v <= 3000000 and v != 0:
                            sell = v
                            break

            if buy is not None or sell is not None:
                return {"ok": True, "buy": buy, "sell": sell, "message": note}
        except Exception:
            continue

    return {"ok": False, "message": "공개 금시세 페이지 구조상 파싱 실패"}


@st.cache_data(ttl=600)
def get_opinet():
    key = ""
    try:
        key = st.secrets.get("OPINET_API_KEY", "").strip()
    except Exception:
        key = ""

    if not key:
        return {"ok": False, "message": "API 키 설정 필요"}

    urls = [
        f"https://www.opinet.co.kr/api/avgAllPrice.do?out=json&code={key}",
        f"https://www.opinet.co.kr/api/avgAllPrice.do?out=json&certkey={key}",
        f"http://www.opinet.co.kr/api/avgAllPrice.do?out=json&code={key}",
        f"http://www.opinet.co.kr/api/avgAllPrice.do?out=json&certkey={key}",
    ]

    last_text = ""
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            last_text = r.text[:200]
            data = r.json()
            result = data.get("RESULT", {})
            oils = result.get("OIL", []) if isinstance(result, dict) else []
            if not oils:
                continue

            gas = next((x for x in oils if x.get("PRODCD") == "B027"), None)
            diesel = next((x for x in oils if x.get("PRODCD") == "D047"), None)

            def parse_num(v):
                try:
                    return float(str(v).replace(",", "").strip())
                except Exception:
                    return None

            return {
                "ok": True,
                "gas": parse_num(gas.get("PRICE")) if gas else None,
                "gas_diff": parse_num(gas.get("DIFF")) if gas else None,
                "diesel": parse_num(diesel.get("PRICE")) if diesel else None,
                "diesel_diff": parse_num(diesel.get("DIFF")) if diesel else None,
            }
        except Exception:
            continue

    return {"ok": False, "message": f"오피넷 응답에 유가 데이터가 없습니다. ({last_text[:120]})"}


@st.cache_data(ttl=600)
def get_market_overview(kospi_data, kosdaq_data):
    ks = yf.Ticker("^KS11").history(period="5d")
    kq = yf.Ticker("^KQ11").history(period="5d")

    def safe_last(df, col):
        try:
            return float(df[col].dropna().iloc[-1])
        except Exception:
            return None

    return {
        "종합주가지수": f"코스피 {fmt_num(kospi_data['price']) if kospi_data else '-'} / 코스닥 {fmt_num(kosdaq_data['price']) if kosdaq_data else '-'}",
        "거래량": f"코스피 {fmt_int(safe_last(ks, 'Volume')) if not ks.empty else '-'} / 코스닥 {fmt_int(safe_last(kq, 'Volume')) if not kq.empty else '-'}",
        "거래대금": "야후 데이터 기준 별도 미제공",
        "고객예탁금": "공개 API 미연결",
        "외국인 동향": "공개 API 미연결",
        "기관 동향": "공개 API 미연결",
    }


def make_stock_table(items):
    rows = []
    for name, ticker in items:
        row = yf_last_two(ticker)
        if row:
            rows.append({
                "종목": name,
                "티커": ticker,
                "현재가": fmt_int(row["price"]),
                "전일대비": f"{row['diff']:+,.0f}",
                "등락률(%)": f"{row['pct']:+.2f}",
            })
        else:
            rows.append({
                "종목": name,
                "티커": ticker,
                "현재가": "-",
                "전일대비": "-",
                "등락률(%)": "-",
            })
    return pd.DataFrame(rows)


@st.cache_data(ttl=900)
def get_news():
    feeds = [
        ("한국경제", "https://www.hankyung.com/feed/economy"),
        ("매일경제", "https://www.mk.co.kr/rss/30100041/"),
        ("서울경제", "https://www.sedaily.com/RSSFeed.xml"),
        ("한겨레", "https://www.hani.co.kr/rss/economy/"),
        ("경향신문", "https://www.khan.co.kr/rss/rssdata/economy_news.xml"),
    ]
    items = []

    for source, url in feeds:
        try:
            parsed = feedparser.parse(url)
            for ent in parsed.entries[:3]:
                title = getattr(ent, "title", "").strip()
                link = getattr(ent, "link", "").strip()
                if title and link:
                    items.append({"title": title, "link": link, "source": source})
        except Exception:
            continue

    out = []
    seen = set()
    for item in items:
        if item["title"] not in seen:
            seen.add(item["title"])
            out.append(item)
    return out[:10]


@st.cache_data(ttl=900)
def search_symbol(query):
    q = query.strip()
    if not q:
        return None
    candidates = []
    if q.isdigit():
        candidates += [f"{q}.KS", f"{q}.KQ"]
    if "." in q:
        candidates.append(q.upper())
    else:
        candidates += [q.upper(), f"{q.upper()}.KS", f"{q.upper()}.KQ"]

    for ticker in candidates:
        row = yf_last_two(ticker)
        if row:
            return ticker, row
    return None


kst = datetime.now(pytz.timezone("Asia/Seoul"))
est = datetime.now(pytz.timezone("US/Eastern"))

st.markdown('<div class="main-title">경제 대시보드 <span class="en">(Economy Dash board)</span></div>', unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1:
    st.markdown(f'<div class="top-time">한국 시간 · {kst.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)
with t2:
    st.markdown(f'<div class="top-time">미국 동부 시간 · {est.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)

st.caption("자동 새로고침: 60초")

kospi = get_index("^KS11")
kosdaq = get_index("^KQ11")
gold = get_gold_kr()
base_rate = get_base_rate()
brent = get_brent()
opinet = get_opinet()
fx = get_fx_card_data()

st.markdown('<div class="section-title">오늘의 핵심 지표</div>', unsafe_allow_html=True)

r1 = st.columns(4)
with r1[0]:
    render_card("오늘의 코스피",
                fmt_num(kospi["price"]) if kospi else "-",
                delta_html(kospi["diff"], kospi["pct"]) if kospi else "전일 대비 정보 없음",
                "Yahoo Finance")
with r1[1]:
    render_card("오늘의 코스닥",
                fmt_num(kosdaq["price"]) if kosdaq else "-",
                delta_html(kosdaq["diff"], kosdaq["pct"]) if kosdaq else "전일 대비 정보 없음",
                "Yahoo Finance")
with r1[2]:
    render_card("한국 금시세 1돈 · 살때",
                f"₩{fmt_int(gold.get('buy'))}" if gold.get("buy") else "-",
                "전일 대비 정보 없음",
                "공개 금시세 페이지" if gold.get("ok") else None,
                gold.get("message"),
                big=True)
with r1[3]:
    render_card("한국 금시세 1돈 · 팔때",
                f"₩{fmt_int(gold.get('sell'))}" if gold.get("sell") else "-",
                "전일 대비 정보 없음",
                "공개 금시세 페이지" if gold.get("ok") else None,
                gold.get("message"),
                big=True)

r2 = st.columns(4)
with r2[0]:
    if base_rate.get("ok"):
        render_card("한국 기준금리",
                    f"{base_rate['value']:.2f}%",
                    base_rate["message"],
                    "한국은행",
                    big=True)
    else:
        render_card("한국 기준금리",
                    "-",
                    base_rate.get("message", "직전 변경 대비 정보 없음"),
                    None,
                    None,
                    big=True)

with r2[1]:
    if fx:
        parts = []
        for nm in ["달러", "위안", "엔", "유로"]:
            if nm in fx:
                parts.append(f"{nm} {fmt_num(fx[nm]['price'])}원")
        first = fx.get("달러")
        render_card("원화환율",
                    "<br>".join(parts),
                    delta_html(first["diff"], first["pct"], unit="원", prefix="달러 기준") if first else "달러 기준 정보 없음",
                    "Yahoo Finance",
                    big=False)
    else:
        render_card("원화환율", "-", "환율 데이터 없음", big=False)

with r2[2]:
    render_card("국제유가 · 브렌트유",
                f"${fmt_num(brent['price'])} / bbl" if brent else "-",
                delta_html(brent["diff"], brent["pct"], unit=" 달러") if brent else "전일 대비 정보 없음",
                "Yahoo Finance")

with r2[3]:
    if opinet.get("ok"):
        notes = []
        if opinet.get("gas_diff") is not None:
            notes.append(f"휘발유 {opinet['gas_diff']:+,.0f}원")
        if opinet.get("diesel_diff") is not None:
            notes.append(f"경유 {opinet['diesel_diff']:+,.0f}원")
        render_card("한국 기준 유가",
                    f"휘발유 {fmt_num(opinet.get('gas'),0)}원<br>경유 {fmt_num(opinet.get('diesel'),0)}원",
                    "전일 대비 " + (" · ".join(notes) if notes else "정보 없음"),
                    "오피넷",
                    big=False)
    else:
        render_card("한국 기준 유가",
                    "API 키 확인 필요",
                    opinet.get("message", "오피넷 데이터 없음"),
                    "오피넷",
                    big=False)

st.markdown('<div class="section-title">오늘의 한국증시</div>', unsafe_allow_html=True)
overview = get_market_overview(kospi, kosdaq)

rows = ['<table class="market-mini"><thead><tr><th>항목</th><th>내용</th></tr></thead><tbody>']
for k, v in overview.items():
    rows.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
rows.append("</tbody></table>")
st.markdown("".join(rows), unsafe_allow_html=True)

KOSPI_50 = [
    ("삼성전자","005930.KS"),("SK하이닉스","000660.KS"),("LG에너지솔루션","373220.KS"),("삼성바이오로직스","207940.KS"),
    ("현대차","005380.KS"),("기아","000270.KS"),("셀트리온","068270.KS"),("KB금융","105560.KS"),
    ("NAVER","035420.KS"),("한화에어로스페이스","012450.KS"),("POSCO홀딩스","005490.KS"),("삼성SDI","006400.KS"),
    ("현대모비스","012330.KS"),("신한지주","055550.KS"),("메리츠금융지주","138040.KS"),("하나금융지주","086790.KS"),
    ("LG화학","051910.KS"),("삼성물산","028260.KS"),("HMM","011200.KS"),("카카오","035720.KS"),
    ("HD현대중공업","329180.KS"),("삼성생명","032830.KS"),("KT&G","033780.KS"),("두산에너빌리티","034020.KS"),
    ("한국전력","015760.KS"),("우리금융지주","316140.KS"),("대한항공","003490.KS"),("포스코퓨처엠","003670.KS"),
    ("크래프톤","259960.KS"),("삼성전기","009150.KS"),("기업은행","024110.KS"),("SK이노베이션","096770.KS"),
    ("HD한국조선해양","009540.KS"),("삼성화재","000810.KS"),("LG","003550.KS"),("아모레퍼시픽","090430.KS"),
    ("S-Oil","010950.KS"),("고려아연","010130.KS"),("오리온","271560.KS"),("유한양행","000100.KS"),
    ("롯데케미칼","011170.KS"),("한미반도체","042700.KS"),("삼성에스디에스","018260.KS"),("LS ELECTRIC","010120.KS"),
    ("SK텔레콤","017670.KS"),("CJ제일제당","097950.KS"),("LG전자","066570.KS"),("현대글로비스","086280.KS"),
    ("강원랜드","035250.KS"),("한진칼","180640.KS")
]

KOSDAQ_50 = [
    ("에코프로비엠","247540.KQ"),("에코프로","086520.KQ"),("HLB","028300.KQ"),("알테오젠","196170.KQ"),
    ("레인보우로보틱스","277810.KQ"),("리가켐바이오","141080.KQ"),("휴젤","145020.KQ"),("클래시스","214150.KQ"),
    ("JYP Ent.","035900.KQ"),("파마리서치","214450.KQ"),("펄어비스","263750.KQ"),("에스엠","041510.KQ"),
    ("셀트리온제약","068760.KQ"),("삼천당제약","000250.KQ"),("HPSP","403870.KQ"),("실리콘투","257720.KQ"),
    ("주성엔지니어링","036930.KQ"),("원익IPS","240810.KQ"),("이오테크닉스","039030.KQ"),("리노공업","058470.KQ"),
    ("SOOP","067160.KQ"),("ISC","095340.KQ"),("덕산네오룩스","213420.KQ"),("메디톡스","086900.KQ"),
    ("동진쎄미켐","005290.KQ"),("엔켐","348370.KQ"),("와이지엔터테인먼트","122870.KQ"),("카페24","042000.KQ"),
    ("에스티팜","237690.KQ"),("보로노이","310210.KQ"),("젬백스","082270.KQ"),("네이처셀","007390.KQ"),
    ("큐렉소","060280.KQ"),("코스메카코리아","241710.KQ"),("브이티","018290.KQ"),("차바이오텍","085660.KQ"),
    ("씨젠","096530.KQ"),("원텍","336570.KQ"),("대주전자재료","078600.KQ"),("티씨케이","064760.KQ"),
    ("에스앤에스텍","101490.KQ"),("파크시스템스","140860.KQ"),("천보","278280.KQ"),("컴투스","078340.KQ"),
    ("고영","098460.KQ"),("제이시스메디칼","287410.KQ"),("디어유","376300.KQ"),("오스템임플란트","048260.KQ"),
    ("루닛","328130.KQ"),("셀바스AI","108860.KQ")
]

ETF_10 = [
    ("KODEX 200","069500.KS"),("TIGER 200","102110.KS"),("KODEX 코스닥150","229200.KS"),("TIGER 미국S&P500","360750.KS"),
    ("KODEX 미국S&P500TR","379800.KS"),("TIGER 미국나스닥100","133690.KS"),("KODEX 2차전지산업","305720.KS"),
    ("KODEX 은행","091170.KS"),("KODEX 골드선물(H)","132030.KS"),("TIGER 리츠부동산인프라","329200.KS")
]

if "kospi_limit" not in st.session_state:
    st.session_state.kospi_limit = 10
if "kosdaq_limit" not in st.session_state:
    st.session_state.kosdaq_limit = 10

c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="section-title">코스피 주요 50개 종목</div>', unsafe_allow_html=True)
    st.dataframe(make_stock_table(KOSPI_50[:st.session_state.kospi_limit]), use_container_width=True, hide_index=True)
    if st.session_state.kospi_limit < 50 and st.button("코스피 더보기", use_container_width=True):
        st.session_state.kospi_limit = min(st.session_state.kospi_limit + 10, 50)
        st.rerun()

with c2:
    st.markdown('<div class="section-title">코스닥 주요 50개 종목</div>', unsafe_allow_html=True)
    st.dataframe(make_stock_table(KOSDAQ_50[:st.session_state.kosdaq_limit]), use_container_width=True, hide_index=True)
    if st.session_state.kosdaq_limit < 50 and st.button("코스닥 더보기", use_container_width=True):
        st.session_state.kosdaq_limit = min(st.session_state.kosdaq_limit + 10, 50)
        st.rerun()

st.markdown('<div class="section-title">주요 ETF 10개 종목</div>', unsafe_allow_html=True)
st.dataframe(make_stock_table(ETF_10), use_container_width=True, hide_index=True)

st.markdown('<div class="section-title">관심있는 종목 검색</div>', unsafe_allow_html=True)
search_q = st.text_input("종목코드 또는 티커를 입력해 주세요. 예: 005930 / 005930.KS / AAPL")
if search_q:
    found = search_symbol(search_q)
    if found:
        ticker, row = found
        render_card(f"검색 결과 · {ticker}",
                    fmt_num(row["price"]),
                    delta_html(row["diff"], row["pct"]),
                    "Yahoo Finance")
    else:
        st.info("검색 결과를 찾지 못했습니다. 종목코드 또는 티커 형식을 다시 확인해 주세요.")

left, right = st.columns([1.45, 1])
with left:
    st.markdown('<div class="section-title">주요 경제뉴스</div>', unsafe_allow_html=True)
    news_items = get_news()
    if news_items:
        st.markdown('<div class="news-wrap">', unsafe_allow_html=True)
        for item in news_items:
            st.markdown(
                f'<a class="news-item" href="{item["link"]}" target="_blank">{item["title"]}<span class="news-source">{item["source"]}</span></a>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")

with right:
    st.markdown('<div class="section-title">주요 경제정보 확인 사이트</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="link-list">
      <a href="https://ecos.bok.or.kr/" target="_blank">한국은행 ECOS</a>
      <a href="https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643" target="_blank">한국은행 기준금리 추이</a>
      <a href="https://data.krx.co.kr/" target="_blank">KRX 정보데이터시스템</a>
      <a href="https://www.opinet.co.kr/" target="_blank">오피넷</a>
      <a href="https://koreagoldx.co.kr/" target="_blank">한국금거래소</a>
      <a href="https://www.index.go.kr/" target="_blank">국가지표체계</a>
      <a href="https://www.hankyung.com/" target="_blank">한국경제신문</a>
      <a href="https://www.mk.co.kr/" target="_blank">매일경제</a>
      <a href="https://www.sedaily.com/" target="_blank">서울경제</a>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('<div class="footer">© miyawa 제작</div>', unsafe_allow_html=True)
