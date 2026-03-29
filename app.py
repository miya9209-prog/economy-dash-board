import json
import math
import re
from datetime import datetime

import feedparser
import pandas as pd
import pytz
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(
    page_title="경제 대시보드 | 한국 증시 현황, 코스피 코스닥, 환율, 유가, 금시세",
    layout="wide"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ---------------------------------
# SEO SETTINGS
# ---------------------------------
DEFAULT_SITE_URL = "https://economy-dash-board.streamlit.app"
DEFAULT_OG_IMAGE = "https://economy-dash-board.streamlit.app/"

SITE_URL = DEFAULT_SITE_URL
OG_IMAGE_URL = DEFAULT_OG_IMAGE

try:
    SITE_URL = st.secrets.get("SITE_URL", DEFAULT_SITE_URL)
except Exception:
    SITE_URL = DEFAULT_SITE_URL

try:
    OG_IMAGE_URL = st.secrets.get("OG_IMAGE_URL", DEFAULT_OG_IMAGE)
except Exception:
    OG_IMAGE_URL = DEFAULT_OG_IMAGE

SEO_TITLE = "경제 대시보드 | 한국 증시 현황, 코스피 코스닥, 환율, 유가, 금시세"
SEO_DESCRIPTION = (
    "경제 대시보드는 코스피, 코스닥, 한국 증시 현황, 원화환율, 국제유가, 국내 유가, "
    "금시세, 기준금리, ETF 시세, 경제뉴스를 한 화면에서 확인할 수 있는 실시간 경제 정보 페이지입니다."
)
SEO_KEYWORDS = (
    "경제 대시보드, 한국 증시 현황, 코스피, 코스닥, 코스피 코스닥 실시간, "
    "오늘의 환율, 오늘의 금시세, 국제유가, 한국 기준금리, ETF 시세, 경제뉴스"
)


def inject_seo_meta():
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "경제 대시보드",
        "url": SITE_URL,
        "description": SEO_DESCRIPTION,
        "inLanguage": "ko-KR",
        "publisher": {
            "@type": "Organization",
            "name": "MISHARP COMPANY by MIYAWA"
        }
    }

    webpage_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": SEO_TITLE,
        "url": SITE_URL,
        "description": SEO_DESCRIPTION,
        "inLanguage": "ko-KR",
        "about": [
            {"@type": "Thing", "name": "코스피"},
            {"@type": "Thing", "name": "코스닥"},
            {"@type": "Thing", "name": "환율"},
            {"@type": "Thing", "name": "국제유가"},
            {"@type": "Thing", "name": "금시세"},
            {"@type": "Thing", "name": "기준금리"}
        ]
    }

    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "경제 대시보드는 무엇을 보여주나요?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "경제 대시보드는 코스피, 코스닥, 원화환율, 국제유가, 국내 유가, 금시세, 기준금리, ETF 시세와 주요 경제뉴스를 한 화면에서 확인할 수 있도록 구성된 경제 정보 페이지입니다."
                }
            },
            {
                "@type": "Question",
                "name": "경제 대시보드는 어떻게 활용하면 좋나요?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "주식 투자자는 시장 흐름과 외국인 및 기관 수급, 거래대금, 환율, 유가를 함께 참고할 수 있고, 자영업자나 쇼핑몰 운영자는 환율과 유가, 금리 변화를 사업 전략과 원가 관리에 참고할 수 있습니다."
                }
            },
            {
                "@type": "Question",
                "name": "코스피와 코스닥의 차이는 무엇인가요?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "코스피는 한국 유가증권시장의 대표 지수로 대형주 중심의 흐름을 보여주고, 코스닥은 성장주, 기술주, 중소형주 중심의 시장 분위기를 보여주는 지수입니다."
                }
            }
        ]
    }

    seo_html = f"""
    <script>
    (function() {{
        const title = {json.dumps(SEO_TITLE)};
        const description = {json.dumps(SEO_DESCRIPTION)};
        const keywords = {json.dumps(SEO_KEYWORDS)};
        const canonicalUrl = {json.dumps(SITE_URL)};
        const ogImage = {json.dumps(OG_IMAGE_URL)};

        document.title = title;

        function setMeta(attr, key, value) {{
            let el = document.head.querySelector(`meta[${{attr}}="${{key}}"]`);
            if (!el) {{
                el = document.createElement('meta');
                el.setAttribute(attr, key);
                document.head.appendChild(el);
            }}
            el.setAttribute('content', value);
        }}

        function setLink(rel, href) {{
            let el = document.head.querySelector(`link[rel="${{rel}}"]`);
            if (!el) {{
                el = document.createElement('link');
                el.setAttribute('rel', rel);
                document.head.appendChild(el);
            }}
            el.setAttribute('href', href);
        }}

        setMeta('name', 'description', description);
        setMeta('name', 'keywords', keywords);
        setMeta('property', 'og:type', 'website');
        setMeta('property', 'og:title', title);
        setMeta('property', 'og:description', description);
        setMeta('property', 'og:url', canonicalUrl);
        setMeta('property', 'og:image', ogImage);
        setMeta('name', 'twitter:card', 'summary_large_image');
        setMeta('name', 'twitter:title', title);
        setMeta('name', 'twitter:description', description);
        setMeta('name', 'twitter:image', ogImage);
        setLink('canonical', canonicalUrl);

        function upsertJsonLd(id, payload) {{
            let el = document.head.querySelector(`#${{id}}`);
            if (!el) {{
                el = document.createElement('script');
                el.type = 'application/ld+json';
                el.id = id;
                document.head.appendChild(el);
            }}
            el.textContent = JSON.stringify(payload);
        }}

        upsertJsonLd('seo-web-site', {json.dumps(json_ld, ensure_ascii=False)});
        upsertJsonLd('seo-web-page', {json.dumps(webpage_ld, ensure_ascii=False)});
        upsertJsonLd('seo-faq-page', {json.dumps(faq_ld, ensure_ascii=False)});
    }})();
    </script>
    """
    components.html(seo_html, height=0, width=0)


inject_seo_meta()

# -----------------------------
# STYLE
# -----------------------------
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
  margin: 1.15rem 0 .85rem 0;
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
.seo-box{
  margin-top: 28px;
  padding: 24px 22px;
  border: 1px solid rgba(89,115,156,.30);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(12,24,42,.92) 0%, rgba(18,30,49,.92) 100%);
}
.seo-box h2{
  font-size: 1.45rem;
  margin: 0 0 16px 0;
  color: #fff;
  font-weight: 800;
}
.seo-box h3{
  font-size: 1.08rem;
  margin: 22px 0 8px 0;
  color: #eef4ff;
  font-weight: 800;
}
.seo-box p{
  margin: 0 0 12px 0;
  color: #d7e2f1;
  line-height: 1.85;
  font-size: .98rem;
}
.footer{
  margin-top: 26px;
  padding-top: 16px;
  border-top:1px solid rgba(90,110,139,.25);
  color:#8ea0ba;
  text-align:center;
  line-height: 1.8;
}
.stButton > button{
  border-radius: 12px !important;
  font-weight: 800 !important;
  color: #0b1220 !important;
  background: #eef3fb !important;
  border: 1px solid #c8d4e6 !important;
}
.stButton > button:hover{
  color: #0b1220 !important;
  background: #f7f9fd !important;
  border: 1px solid #b8c8dc !important;
}
.stButton > button:focus{
  color: #0b1220 !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button div{
  color: #0b1220 !important;
  opacity: 1 !important;
  font-weight: 800 !important;
}
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
  .seo-box{
    padding: 18px 16px;
  }
  .seo-box h2{
    font-size: 1.25rem;
  }
  .seo-box h3{
    font-size: 1rem;
  }
  .seo-box p{
    font-size: .94rem;
    line-height: 1.8;
  }
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

# -----------------------------
# FORMATTERS
# -----------------------------
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


def fmt_billion_krw(v):
    if v is None:
        return "-"
    try:
        sign = "-" if v < 0 else ""
        return f"{sign}{abs(v):,.0f}억원"
    except Exception:
        return "-"


def fmt_hundred_million_from_million(v):
    if v is None:
        return "-"
    try:
        return f"{v/100:,.0f}억원"
    except Exception:
        return "-"


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

# -----------------------------
# DATA HELPERS
# -----------------------------
@st.cache_data(ttl=600)
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

# -----------------------------
# BASE RATE
# -----------------------------
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
            patterns = [
                r"기준금리[^0-9]{0,30}([0-9]+\.[0-9]+)",
                r"한국은행기준금리[^0-9]{0,30}([0-9]+\.[0-9]+)",
            ]
            for p in patterns:
                m = re.search(p, text)
                if m:
                    v = float(m.group(1))
                    if 0.5 <= v <= 10:
                        return {"ok": True, "value": v, "message": "직전 변경 대비 정보는 별도 미연결"}
        except Exception:
            continue
    return {"ok": False, "message": "기준금리 파싱 실패"}

# -----------------------------
# GOLD
# -----------------------------
@st.cache_data(ttl=1800)
def get_gold_kr():
    buy = None
    sell = None
    note = None

    try:
        r = requests.get("https://www.kumsise.com/main/index.php", headers=HEADERS, timeout=10)
        if r.ok:
            text = re.sub(r"\s+", " ", r.text)
            m = re.search(r"순금\s*([0-9,]{5,})원.*?([0-9,]{5,})원", text, re.IGNORECASE)
            if m:
                first = int(m.group(1).replace(",", ""))
                second = int(m.group(2).replace(",", ""))
                low_v, high_v = sorted([first, second])
                if 200000 <= low_v <= 3000000:
                    sell = low_v
                if 200000 <= high_v <= 3000000:
                    buy = high_v
                note = "금시세닷컴 기준"
    except Exception:
        pass

    if buy is None or sell is None:
        try:
            gold_row = yf_last_two("GC=F")
            usdkrw_row = yf_last_two("KRW=X")
            if gold_row and usdkrw_row:
                gold_usd_oz = gold_row["price"]
                usdkrw = usdkrw_row["price"]
                krw_per_3_75g = gold_usd_oz * usdkrw * (3.75 / 31.1034768)
                est_sell = int(round(krw_per_3_75g * 0.98))
                est_buy = int(round(krw_per_3_75g * 1.12))
                if sell is None:
                    sell = est_sell
                if buy is None:
                    buy = est_buy
                note = "국제 금 선물 + 원달러 환율 추정값"
        except Exception:
            pass

    if buy is not None or sell is not None:
        return {"ok": True, "buy": buy, "sell": sell, "message": note}

    return {"ok": False, "message": "공개 금시세 페이지 구조상 파싱 실패"}

# -----------------------------
# OPINET
# -----------------------------
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

# -----------------------------
# KOREA MARKET SUMMARY
# -----------------------------
@st.cache_data(ttl=900)
def get_korea_market_summary():
    def parse_page(url):
        out = {
            "date": None,
            "trading_value_억원": None,
            "foreign_억원": None,
            "inst_억원": None,
        }
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if not r.ok:
                return out
            text = re.sub(r"\s+", " ", r.text)

            date_patterns = [
                r"(20[0-9]{2}\.[0-9]{2}\.[0-9]{2})",
                r"(20[0-9]{2}-[0-9]{2}-[0-9]{2})",
            ]
            for p in date_patterns:
                m = re.search(p, text)
                if m:
                    out["date"] = m.group(1)
                    break

            tv_patterns = [
                r"거래대금\s*([0-9,]+)\s*억원",
                r"거래대금[^0-9]{0,20}([0-9,]+)",
            ]
            for p in tv_patterns:
                m = re.search(p, text)
                if m:
                    try:
                        out["trading_value_억원"] = int(m.group(1).replace(",", ""))
                        break
                    except Exception:
                        pass

            foreign_patterns = [
                r"외국인\s*(-?[0-9,]+)\s*억원",
                r"외국인[^-0-9]{0,20}(-?[0-9,]+)",
            ]
            for p in foreign_patterns:
                m = re.search(p, text)
                if m:
                    try:
                        out["foreign_억원"] = int(m.group(1).replace(",", ""))
                        break
                    except Exception:
                        pass

            inst_patterns = [
                r"기관\s*(-?[0-9,]+)\s*억원",
                r"기관[^-0-9]{0,20}(-?[0-9,]+)",
            ]
            for p in inst_patterns:
                m = re.search(p, text)
                if m:
                    try:
                        out["inst_억원"] = int(m.group(1).replace(",", ""))
                        break
                    except Exception:
                        pass
        except Exception:
            pass
        return out

    kospi = parse_page("https://finance.naver.com/sise/sise_index.naver?code=KOSPI")
    kosdaq = parse_page("https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ")

    if kospi["trading_value_억원"] is None:
        h_kospi = parse_page("https://markets.hankyung.com/indices/kospi")
        for k, v in h_kospi.items():
            if kospi.get(k) is None and v is not None:
                kospi[k] = v

    if kosdaq["trading_value_억원"] is None:
        h_kosdaq = parse_page("https://markets.hankyung.com/indices/kosdaq")
        for k, v in h_kosdaq.items():
            if kosdaq.get(k) is None and v is not None:
                kosdaq[k] = v

    deposit_million = None
    for url in ["https://freesis.kofia.or.kr/", "https://www.kofia.or.kr/"]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if not r.ok:
                continue
            text = re.sub(r"\s+", " ", r.text)
            m = re.search(r"투자자예탁금[^0-9]{0,50}([0-9,]{5,})", text)
            if m:
                deposit_million = int(m.group(1).replace(",", ""))
                break
        except Exception:
            continue

    return {
        "date": kospi.get("date") or kosdaq.get("date"),
        "trading_value_kospi_억원": kospi.get("trading_value_억원"),
        "trading_value_kosdaq_억원": kosdaq.get("trading_value_억원"),
        "foreign_net_kospi_억원": kospi.get("foreign_억원"),
        "foreign_net_kosdaq_억원": kosdaq.get("foreign_억원"),
        "inst_net_kospi_억원": kospi.get("inst_억원"),
        "inst_net_kosdaq_억원": kosdaq.get("inst_억원"),
        "deposit_million": deposit_million,
    }

# -----------------------------
# TABLE / NEWS / SEARCH DATA
# -----------------------------
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

# -----------------------------
# STOCK UNIVERSE
# -----------------------------
KOSPI_50 = [
    ("삼성전자", "005930.KS"), ("SK하이닉스", "000660.KS"), ("LG에너지솔루션", "373220.KS"), ("삼성바이오로직스", "207940.KS"),
    ("현대차", "005380.KS"), ("기아", "000270.KS"), ("셀트리온", "068270.KS"), ("KB금융", "105560.KS"),
    ("NAVER", "035420.KS"), ("한화에어로스페이스", "012450.KS"), ("POSCO홀딩스", "005490.KS"), ("삼성SDI", "006400.KS"),
    ("현대모비스", "012330.KS"), ("신한지주", "055550.KS"), ("메리츠금융지주", "138040.KS"), ("하나금융지주", "086790.KS"),
    ("LG화학", "051910.KS"), ("삼성물산", "028260.KS"), ("HMM", "011200.KS"), ("카카오", "035720.KS"),
    ("HD현대중공업", "329180.KS"), ("삼성생명", "032830.KS"), ("KT&G", "033780.KS"), ("두산에너빌리티", "034020.KS"),
    ("한국전력", "015760.KS"), ("우리금융지주", "316140.KS"), ("대한항공", "003490.KS"), ("포스코퓨처엠", "003670.KS"),
    ("크래프톤", "259960.KS"), ("삼성전기", "009150.KS"), ("기업은행", "024110.KS"), ("SK이노베이션", "096770.KS"),
    ("HD한국조선해양", "009540.KS"), ("삼성화재", "000810.KS"), ("LG", "003550.KS"), ("아모레퍼시픽", "090430.KS"),
    ("S-Oil", "010950.KS"), ("고려아연", "010130.KS"), ("오리온", "271560.KS"), ("유한양행", "000100.KS"),
    ("롯데케미칼", "011170.KS"), ("한미반도체", "042700.KS"), ("삼성에스디에스", "018260.KS"), ("LS ELECTRIC", "010120.KS"),
    ("SK텔레콤", "017670.KS"), ("CJ제일제당", "097950.KS"), ("LG전자", "066570.KS"), ("현대글로비스", "086280.KS"),
    ("강원랜드", "035250.KS"), ("한진칼", "180640.KS")
]

KOSDAQ_50 = [
    ("에코프로비엠", "247540.KQ"), ("에코프로", "086520.KQ"), ("HLB", "028300.KQ"), ("알테오젠", "196170.KQ"),
    ("레인보우로보틱스", "277810.KQ"), ("리가켐바이오", "141080.KQ"), ("휴젤", "145020.KQ"), ("클래시스", "214150.KQ"),
    ("JYP Ent.", "035900.KQ"), ("파마리서치", "214450.KQ"), ("펄어비스", "263750.KQ"), ("에스엠", "041510.KQ"),
    ("셀트리온제약", "068760.KQ"), ("삼천당제약", "000250.KQ"), ("HPSP", "403870.KQ"), ("실리콘투", "257720.KQ"),
    ("주성엔지니어링", "036930.KQ"), ("원익IPS", "240810.KQ"), ("이오테크닉스", "039030.KQ"), ("리노공업", "058470.KQ"),
    ("SOOP", "067160.KQ"), ("ISC", "095340.KQ"), ("덕산네오룩스", "213420.KQ"), ("메디톡스", "086900.KQ"),
    ("동진쎄미켐", "005290.KQ"), ("엔켐", "348370.KQ"), ("와이지엔터테인먼트", "122870.KQ"), ("카페24", "042000.KQ"),
    ("에스티팜", "237690.KQ"), ("보로노이", "310210.KQ"), ("젬백스", "082270.KQ"), ("네이처셀", "007390.KQ"),
    ("큐렉소", "060280.KQ"), ("코스메카코리아", "241710.KQ"), ("브이티", "018290.KQ"), ("차바이오텍", "085660.KQ"),
    ("씨젠", "096530.KQ"), ("원텍", "336570.KQ"), ("대주전자재료", "078600.KQ"), ("티씨케이", "064760.KQ"),
    ("에스앤에스텍", "101490.KQ"), ("파크시스템스", "140860.KQ"), ("천보", "278280.KQ"), ("컴투스", "078340.KQ"),
    ("고영", "098460.KQ"), ("제이시스메디칼", "287410.KQ"), ("디어유", "376300.KQ"), ("오스템임플란트", "048260.KQ"),
    ("루닛", "328130.KQ"), ("셀바스AI", "108860.KQ")
]

ETF_10 = [
    ("KODEX 200", "069500.KS"), ("TIGER 200", "102110.KS"), ("KODEX 코스닥150", "229200.KS"), ("TIGER 미국S&P500", "360750.KS"),
    ("KODEX 미국S&P500TR", "379800.KS"), ("TIGER 미국나스닥100", "133690.KS"), ("KODEX 2차전지산업", "305720.KS"),
    ("KODEX 은행", "091170.KS"), ("KODEX 골드선물(H)", "132030.KS"), ("TIGER 리츠부동산인프라", "329200.KS")
]

# -----------------------------
# SEARCH MAP
# -----------------------------
ALL_SEARCH_ITEMS = KOSPI_50 + KOSDAQ_50 + ETF_10

NAME_TO_TICKER = {}
for name, ticker in ALL_SEARCH_ITEMS:
    key1 = name.strip().lower()
    key2 = name.replace(" ", "").strip().lower()
    NAME_TO_TICKER[key1] = ticker
    NAME_TO_TICKER[key2] = ticker

EXTRA_NAME_MAP = {
    "한화시스템": "272210.KS",
    "한화에어로스페이스": "012450.KS",
    "삼성전자": "005930.KS",
    "sk하이닉스": "000660.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "hlb": "028300.KQ",
    "jyp": "035900.KQ",
    "jypent": "035900.KQ",
    "jypent.": "035900.KQ",
    "naver": "035420.KS",
    "카카오": "035720.KS",
}
for k, v in EXTRA_NAME_MAP.items():
    NAME_TO_TICKER[k.lower()] = v
    NAME_TO_TICKER[k.replace(" ", "").lower()] = v


def find_partial_matches(query: str, limit: int = 10):
    q = query.strip().lower().replace(" ", "")
    if not q:
        return []

    matches = []
    seen = set()

    for name, ticker in ALL_SEARCH_ITEMS:
        key = name.lower().replace(" ", "")
        if q in key and (name, ticker) not in seen:
            matches.append((name, ticker))
            seen.add((name, ticker))

    for alias, ticker in EXTRA_NAME_MAP.items():
        alias_key = alias.lower().replace(" ", "")
        if q in alias_key:
            pair = (alias, ticker)
            if pair not in seen:
                matches.append(pair)
                seen.add(pair)

    return matches[:limit]


@st.cache_data(ttl=900)
def search_symbol(query):
    q = query.strip()
    if not q:
        return None

    q_lower = q.lower().strip()
    q_compact = q.replace(" ", "").lower().strip()

    # 1. 한글/영문 종목명 완전일치
    if q_lower in NAME_TO_TICKER:
        ticker = NAME_TO_TICKER[q_lower]
        row = yf_last_two(ticker)
        if row:
            return {"mode": "exact", "display_name": q, "ticker": ticker, "row": row}

    if q_compact in NAME_TO_TICKER:
        ticker = NAME_TO_TICKER[q_compact]
        row = yf_last_two(ticker)
        if row:
            return {"mode": "exact", "display_name": q, "ticker": ticker, "row": row}

    # 2. 숫자 코드 검색
    candidates = []
    if q.isdigit():
        if len(q) == 6:
            candidates += [f"{q}.KS", f"{q}.KQ"]
        else:
            candidates += [q]

    # 3. 티커 직접 입력
    if "." in q:
        candidates.append(q.upper())
    else:
        candidates += [q.upper(), f"{q.upper()}.KS", f"{q.upper()}.KQ"]

    seen = set()
    uniq_candidates = []
    for c in candidates:
        if c not in seen:
            uniq_candidates.append(c)
            seen.add(c)

    for ticker in uniq_candidates:
        row = yf_last_two(ticker)
        if row:
            return {"mode": "exact", "display_name": q, "ticker": ticker, "row": row}

    # 4. 부분일치
    partials = find_partial_matches(q)
    if len(partials) == 1:
        name, ticker = partials[0]
        row = yf_last_two(ticker)
        if row:
            return {"mode": "exact", "display_name": name, "ticker": ticker, "row": row}

    if len(partials) > 1:
        return {"mode": "partial", "matches": partials}

    return None

# -----------------------------
# DATA LOAD
# -----------------------------
kst = datetime.now(pytz.timezone("Asia/Seoul"))
est = datetime.now(pytz.timezone("US/Eastern"))

kospi = get_index("^KS11")
kosdaq = get_index("^KQ11")
gold = get_gold_kr()
base_rate = get_base_rate()
brent = get_brent()
opinet = get_opinet()
fx = get_fx_card_data()
market_over = get_korea_market_summary()

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="main-title">경제 대시보드 <span class="en">(Economy Dash board)</span></div>', unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1:
    st.markdown(f'<div class="top-time">한국 시간 · {kst.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)
with t2:
    st.markdown(f'<div class="top-time">미국 동부 시간 · {est.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)

st.caption("자동 새로고침: 60초")

# -----------------------------
# METRIC CARDS
# -----------------------------
st.markdown('<div class="section-title">오늘의 핵심 지표</div>', unsafe_allow_html=True)

r1 = st.columns(4)
with r1[0]:
    render_card(
        "오늘의 코스피",
        fmt_num(kospi["price"]) if kospi else "-",
        delta_html(kospi["diff"], kospi["pct"]) if kospi else "전일 대비 정보 없음",
        "Yahoo Finance"
    )
with r1[1]:
    render_card(
        "오늘의 코스닥",
        fmt_num(kosdaq["price"]) if kosdaq else "-",
        delta_html(kosdaq["diff"], kosdaq["pct"]) if kosdaq else "전일 대비 정보 없음",
        "Yahoo Finance"
    )
with r1[2]:
    render_card(
        "한국 금시세 1돈 · 살때",
        f"₩{fmt_int(gold.get('buy'))}" if gold.get("buy") else "-",
        "전일 대비 정보 없음",
        "공개 금시세 페이지 / fallback 계산" if gold.get("ok") else None,
        gold.get("message"),
        big=True
    )
with r1[3]:
    render_card(
        "한국 금시세 1돈 · 팔때",
        f"₩{fmt_int(gold.get('sell'))}" if gold.get("sell") else "-",
        "전일 대비 정보 없음",
        "공개 금시세 페이지 / fallback 계산" if gold.get("ok") else None,
        gold.get("message"),
        big=True
    )

r2 = st.columns(4)
with r2[0]:
    if base_rate.get("ok"):
        render_card(
            "한국 기준금리",
            f"{base_rate['value']:.2f}%",
            base_rate["message"],
            "한국은행",
            big=True
        )
    else:
        render_card(
            "한국 기준금리",
            "-",
            base_rate.get("message", "직전 변경 대비 정보 없음"),
            None,
            None,
            big=True
        )

with r2[1]:
    if fx:
        parts = []
        for nm in ["달러", "위안", "엔", "유로"]:
            if nm in fx:
                parts.append(f"{nm} {fmt_num(fx[nm]['price'])}원")
        first = fx.get("달러")
        render_card(
            "원화환율",
            "<br>".join(parts),
            delta_html(first["diff"], first["pct"], unit="원", prefix="달러 기준") if first else "달러 기준 정보 없음",
            "Yahoo Finance",
            big=False
        )
    else:
        render_card("원화환율", "-", "환율 데이터 없음", big=False)

with r2[2]:
    render_card(
        "국제유가 · 브렌트유",
        f"${fmt_num(brent['price'])} / bbl" if brent else "-",
        delta_html(brent["diff"], brent["pct"], unit=" 달러") if brent else "전일 대비 정보 없음",
        "Yahoo Finance"
    )

with r2[3]:
    if opinet.get("ok"):
        notes = []
        if opinet.get("gas_diff") is not None:
            notes.append(f"휘발유 {opinet['gas_diff']:+,.0f}원")
        if opinet.get("diesel_diff") is not None:
            notes.append(f"경유 {opinet['diesel_diff']:+,.0f}원")
        render_card(
            "한국 기준 유가",
            f"휘발유 {fmt_num(opinet.get('gas'),0)}원<br>경유 {fmt_num(opinet.get('diesel'),0)}원",
            "전일 대비 " + (" · ".join(notes) if notes else "정보 없음"),
            "오피넷",
            big=False
        )
    else:
        render_card(
            "한국 기준 유가",
            "API 키 확인 필요",
            opinet.get("message", "오피넷 데이터 없음"),
            "오피넷",
            big=False
        )

# -----------------------------
# MARKET OVERVIEW
# -----------------------------
st.markdown('<div class="section-title">오늘의 한국증시</div>', unsafe_allow_html=True)

market_rows = {
    "종합주가지수": f"코스피 {fmt_num(kospi['price']) if kospi else '-'} / 코스닥 {fmt_num(kosdaq['price']) if kosdaq else '-'}",
    "기준일": market_over.get("date") or "-",
    "거래대금": f"코스피 {fmt_billion_krw(market_over.get('trading_value_kospi_억원'))} / 코스닥 {fmt_billion_krw(market_over.get('trading_value_kosdaq_억원'))}",
    "고객예탁금": fmt_hundred_million_from_million(market_over.get('deposit_million')),
    "외국인 동향": f"코스피 {fmt_billion_krw(market_over.get('foreign_net_kospi_억원'))} / 코스닥 {fmt_billion_krw(market_over.get('foreign_net_kosdaq_억원'))}",
    "기관 동향": f"코스피 {fmt_billion_krw(market_over.get('inst_net_kospi_억원'))} / 코스닥 {fmt_billion_krw(market_over.get('inst_net_kosdaq_억원'))}",
}

rows = ['<table class="market-mini"><thead><tr><th>항목</th><th>내용</th></tr></thead><tbody>']
for k, v in market_rows.items():
    rows.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
rows.append("</tbody></table>")
st.markdown("".join(rows), unsafe_allow_html=True)

# -----------------------------
# STOCK TABLES
# -----------------------------
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

# -----------------------------
# SEARCH
# -----------------------------
st.markdown('<div class="section-title">관심있는 종목 검색</div>', unsafe_allow_html=True)

search_q = st.text_input(
    "종목코드, 티커, 한글 종목명을 입력해 주세요. 예: 005930 / 005930.KS / AAPL / 한화시스템 / 한화",
    key="stock_search_input"
)

search_clicked = st.button("종목 조회", key="stock_search_btn")

def render_search_result(display_name, ticker, row):
    render_card(
        f"검색 결과 · {display_name} ({ticker})",
        fmt_int(row["price"]),
        delta_html(row["diff"], row["pct"]),
        "Yahoo Finance"
    )

if search_clicked and search_q:
    found = search_symbol(search_q)

    if found and found["mode"] == "exact":
        render_search_result(found["display_name"], found["ticker"], found["row"])

    elif found and found["mode"] == "partial":
        st.warning("정확한 종목명이 아니어서 아래 후보를 찾았습니다.")
        st.markdown("##### 후보 종목 선택")

        for idx, (name, ticker) in enumerate(found["matches"]):
            if st.button(f"{name} ({ticker})", key=f"candidate_{idx}_{ticker}"):
                exact = search_symbol(name)
                if exact and exact["mode"] == "exact":
                    render_search_result(exact["display_name"], exact["ticker"], exact["row"])

    else:
        st.info("검색 결과를 찾지 못했습니다. 종목명, 종목코드, 티커를 다시 확인해 주세요.")

# -----------------------------
# NEWS + LINKS
# -----------------------------
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
      <a href="https://finance.naver.com/sise/sise_index.naver?code=KOSPI" target="_blank">네이버 코스피</a>
      <a href="https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ" target="_blank">네이버 코스닥</a>
      <a href="https://freesis.kofia.or.kr/" target="_blank">금융투자협회 FreeSIS</a>
      <a href="https://www.opinet.co.kr/" target="_blank">오피넷</a>
      <a href="https://www.kumsise.com/main/index.php" target="_blank">금시세닷컴</a>
      <a href="https://koreagoldx.co.kr/price/gold" target="_blank">한국금거래소 금시세</a>
      <a href="https://www.hankyung.com/" target="_blank">한국경제신문</a>
      <a href="https://www.mk.co.kr/" target="_blank">매일경제</a>
      <a href="https://www.sedaily.com/" target="_blank">서울경제</a>
    </div>
    ''', unsafe_allow_html=True)

# -----------------------------
# SEO CONTENT
# -----------------------------
st.markdown("""
<div class="seo-box">
  <h2>경제 대시보드 활용 가이드</h2>

  <h3>1. 경제 대시보드 활용방법</h3>
  <p>
    경제 대시보드는 코스피, 코스닥, 한국 증시 현황, 원화환율, 국제유가, 금시세, 기준금리,
    ETF 시세와 주요 경제뉴스를 한 화면에서 확인할 수 있도록 구성한 실시간 경제 정보 페이지입니다.
    투자자, 자영업자, 온라인 쇼핑몰 운영자, 마케팅 담당자, 소상공인처럼
    경제 흐름을 빠르게 파악해야 하는 사용자에게 특히 유용합니다.
  </p>
  <p>
    하루 시장 분위기를 파악할 때는 코스피와 코스닥 지수만 보기보다
    환율, 국제유가, 국내 유가, 금시세, 기준금리를 함께 보아야
    시장 심리와 자금 흐름, 물가 부담, 소비 여건 변화를 입체적으로 이해할 수 있습니다.
  </p>

  <h3>2. 사용법</h3>
  <p>
    화면 상단 오늘의 핵심 지표에서는 코스피, 코스닥, 금시세, 한국 기준금리, 원화환율,
    국제유가와 국내 유가를 빠르게 확인할 수 있습니다. 각 카드에는 현재 수치와 전일 대비 증감 정보가 함께 표시되어
    하루 흐름을 즉시 파악할 수 있습니다. 오늘의 한국증시 표에서는 시장 전체 분위기와 거래대금,
    고객예탁금, 외국인 동향, 기관 동향 등을 요약해서 볼 수 있습니다.
  </p>
  <p>
    중간 영역에서는 코스피 주요 50개 종목과 코스닥 주요 50개 종목을 10개씩 확인할 수 있고,
    더보기 버튼으로 확장할 수 있습니다. ETF 주요 10개 종목 영역은 대표 지수형 ETF와
    미국 지수형 ETF, 금 ETF, 리츠 ETF 흐름을 참고하는 데 적합합니다.
    관심있는 종목 검색 기능을 이용하면 종목코드, 티커, 한글 종목명으로 원하는 종목의 현재가와 등락률을 빠르게 확인할 수 있습니다.
  </p>

  <h3>3. 각 지수별 의미</h3>
  <p>
    코스피는 한국 유가증권시장 전체 흐름을 보여주는 대표 지수로,
    삼성전자, SK하이닉스, 현대차 등 대형주의 영향을 크게 받습니다.
    코스닥은 성장주와 기술주, 바이오주, 중소형주 중심의 시장 흐름을 보여주는 지수로
    위험자산 선호 심리를 파악하는 데 유용합니다.
  </p>
  <p>
    원화환율은 달러, 위안, 엔, 유로 대비 원화 가치의 변화를 보여주며,
    수입 원가와 해외 결제 비용, 여행 소비, 해외 투자 심리에 영향을 줄 수 있습니다.
    브렌트유는 글로벌 에너지 가격 흐름을 대표하는 지표이며,
    국내 휘발유와 경유 가격에도 영향을 주는 핵심 변수입니다.
    금시세는 안전자산 선호 흐름을 이해하는 데 참고할 수 있고,
    기준금리는 대출금리와 예금금리, 소비와 투자, 부동산과 주식 시장에 큰 영향을 주는 지표입니다.
  </p>

  <h3>4. 투자 참고 포인트</h3>
  <p>
    투자 판단은 단일 지표보다 여러 지표를 함께 보는 것이 중요합니다.
    예를 들어 코스피가 상승하더라도 외국인과 기관이 동시에 순매도 중인지,
    거래대금이 충분히 동반되고 있는지, 환율이 급등하고 있지는 않은지 함께 체크해야 합니다.
  </p>
  <p>
    원달러 환율 상승은 수입물가 부담과 외국인 수급 변화 가능성을 시사할 수 있고,
    국제유가 상승은 운송비와 생산비 상승으로 이어질 수 있습니다.
    기준금리 변화는 소비와 투자, 부채 부담에 직접적인 영향을 줄 수 있으므로
    자산배분 관점에서도 중요한 체크 포인트가 됩니다.
  </p>
  <p>
    장기 투자자는 하루 수치보다 추세를 보는 것이 중요하고,
    단기 투자자는 전일 대비 변화폭과 거래대금, 외국인·기관 수급의 방향성을 함께 보는 것이 좋습니다.
    자영업자나 쇼핑몰 운영자라면 환율과 유가, 금리, 소비 관련 지표를 함께 확인해
    마케팅 예산, 수입 원가, 재고 전략, 가격 정책을 점검하는 데 활용할 수 있습니다.
  </p>

  <h3>자주 묻는 질문</h3>
  <p>
    경제 대시보드는 무엇을 보여주나요? 이 페이지는 코스피, 코스닥, 환율, 금시세, 국제유가,
    국내 유가, 기준금리, ETF 시세, 경제뉴스를 한 번에 보여주는 경제 정보 페이지입니다.
  </p>
  <p>
    코스피와 코스닥의 차이는 무엇인가요? 코스피는 대형주 중심의 대표 지수이고,
    코스닥은 성장주와 기술주 중심의 시장 흐름을 보여주는 지수입니다.
  </p>
  <p>
    이 페이지는 구글, 네이버, 다음 등 검색엔진에서 경제 대시보드, 한국 증시 현황,
    코스피 코스닥 실시간, 오늘의 환율, 오늘의 금시세, 투자 참고 지표 등의 검색 의도에 맞는
    정보를 제공하기 위해 구성되었습니다.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">2026 MISHARP COMPANY by MIYAWA<br>무단 게재, 복재, 전제를 금합니다.</div>',
    unsafe_allow_html=True
)
