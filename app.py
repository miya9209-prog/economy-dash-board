import json
import math
import re
from datetime import datetime
from html import escape, unescape
from urllib.parse import quote, urljoin

import feedparser
import pandas as pd
import pytz
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(
    page_title="MISHARP 투데이 경제정보 | 한국 증시, 코스피 코스닥, 환율, 유가, 금시세",
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

SEO_TITLE = "MISHARP 투데이 경제정보 | 한국 증시, 코스피 코스닥, 환율, 유가, 금시세"
SEO_DESCRIPTION = (
    "MISHARP 투데이 경제정보는 코스피, 코스닥, 한국 증시 현황, 원화환율, 국제유가, 국내 유가, "
    "금시세, 기준금리, ETF 시세, 경제뉴스를 한 화면에서 확인할 수 있는 실시간 경제 정보 페이지입니다. "
    "투자자, 자영업자, 온라인 셀러가 오늘 시장 흐름을 빠르게 파악할 수 있도록 구성했습니다."
)
SEO_KEYWORDS = (
    "MISHARP 투데이 경제정보, 경제 대시보드, 한국 증시 현황, 코스피, 코스닥, 코스피 코스닥 실시간, "
    "오늘의 환율, 오늘의 금시세, 국제유가, 한국 기준금리, ETF 시세, 경제뉴스, 실시간 경제 정보"
)


def inject_seo_meta():
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "MISHARP 투데이 경제정보",
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
                    "text": "MISHARP 투데이 경제정보는 코스피, 코스닥, 원화환율, 국제유가, 국내 유가, 금시세, 기준금리, ETF 시세와 주요 경제뉴스를 한 화면에서 확인할 수 있도록 구성된 경제 정보 페이지입니다."
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
  font-size: 2.6rem;
  line-height: 1.16;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 0.85rem 0;
  word-break: keep-all;
}
.main-title .en{
  font-size: .56em;
  display: inline-block;
  opacity: .92;
  font-weight: 700;
}
.title-sub{
  margin: 0 0 1.05rem 0;
  color:#d6e3f5;
  font-size:1rem;
  line-height:1.75;
  font-weight:600;
}
.title-divider{
  height:1px;
  margin: 0.3rem 0 1.2rem 0;
  background: linear-gradient(90deg, rgba(123,167,255,.55) 0%, rgba(80,110,150,.28) 45%, rgba(80,110,150,.08) 100%);
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
.card .src-row{
  margin-top:.65rem;
  display:flex;
  justify-content:space-between;
  align-items:flex-end;
  gap:10px;
}
.card .view-more, .section-view-more{
  color:#9ec5ff !important;
  text-decoration:none;
  font-size:.78rem;
  font-weight:800;
  white-space:nowrap;
}
.card .view-more:hover, .section-view-more:hover{
  text-decoration:underline;
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

.news-columns-box{
  display:flex;
  gap:22px;
  align-items:stretch;
}
.news-col{
  flex:1;
  min-width:0;
}
.news-divider{
  width:1px;
  background:linear-gradient(180deg, rgba(120,145,184,.12) 0%, rgba(120,145,184,.45) 20%, rgba(120,145,184,.45) 80%, rgba(120,145,184,.12) 100%);
}
.related-sites-box{
  margin-top: 18px;
  padding: 18px 18px 8px 18px;
  border:1px solid rgba(89,115,156,.30);
  border-radius:18px;
  background: linear-gradient(180deg, rgba(12,24,42,.82) 0%, rgba(16,30,50,.82) 100%);
}
.related-sites-grid{
  display:grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 8px 16px;
  margin-top: 8px;
}
.related-site-link{
  display:block;
  padding: 8px 0;
  color:#7db4ff !important;
  text-decoration:none;
  line-height:1.45;
  border-bottom:1px solid rgba(89,115,156,.16);
}
.related-site-link:hover{
  text-decoration:underline;
}
.footer-links{
  margin-top:4px;
  font-size:.84rem;
}
.footer-links a{
  color:#9ebeff !important;
  text-decoration:none;
}
.footer-links a:hover{
  text-decoration:underline;
}
.policy-box{
  margin-top: 12px;
  padding: 22px 20px;
  border:1px solid rgba(89,115,156,.30);
  border-radius:18px;
  background: linear-gradient(180deg, rgba(12,24,42,.92) 0%, rgba(18,30,49,.92) 100%);
}
.policy-box h1{
  font-size:1.7rem;
  margin:0 0 10px 0;
}
.policy-box h2{
  font-size:1.12rem;
  margin:18px 0 8px 0;
}
.policy-box p, .policy-box li{
  color:#d7e2f1;
  line-height:1.8;
  font-size:.96rem;
}
@media (max-width: 1100px){
  .related-sites-grid{ grid-template-columns: repeat(3, minmax(0,1fr)); }
}
@media (max-width: 900px){
  .title-sub{
    font-size:.92rem;
    line-height:1.7;
    margin-bottom:.9rem;
  }
  .title-divider{
    margin-bottom:1rem;
  }
  .block-container{
    padding-top: 4.4rem !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
  }
  .main-title{
    font-size: 2rem;
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
  .title-sub{
  margin: 0 0 1.05rem 0;
  color:#d6e3f5;
  font-size:1rem;
  line-height:1.75;
  font-weight:600;
}
.title-divider{
  height:1px;
  margin: 0.3rem 0 1.2rem 0;
  background: linear-gradient(90deg, rgba(123,167,255,.55) 0%, rgba(80,110,150,.28) 45%, rgba(80,110,150,.08) 100%);
}
.top-time{ font-size:.92rem; }
  .news-columns-box{display:block;}
  .news-divider{display:none;}
  .related-sites-grid{grid-template-columns: repeat(2, minmax(0,1fr));}
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


def render_card(title, value, sub_html, source=None, note=None, big=True, link=None):
    value_class = "value big" if big else "value"
    html = [
        f'<div class="card"><h4>{title}</h4>',
        f'<div class="{value_class}">{value}</div>',
        f'<div class="sub">{sub_html}</div>',
    ]
    if source or link:
        html.append('<div class="src-row">')
        if source:
            html.append(f'<div class="src">출처: {source}</div>')
        else:
            html.append('<div class="src"></div>')
        if link:
            html.append(f'<a class="view-more" href="{link}" target="_blank" rel="noopener noreferrer">&gt;&gt; VIEW MORE</a>')
        html.append('</div>')
    if note:
        html.append(f'<div class="note">{note}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_news_item(item):
    title = escape(item.get("title", ""))
    source = escape(item.get("source", ""))
    link = item.get("link", "#")
    return f'<a class="news-item" href="{link}" target="_blank" rel="noopener noreferrer">{title}<span class="news-source">{source}</span></a>'


def render_related_sites_box(title, links):
    html = [f'<div class="related-sites-box"><div class="section-title" style="margin-top:0;">{escape(title)}</div><div class="related-sites-grid">']
    for label, url in links:
        html.append(f'<a class="related-site-link" href="{url}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>')
    html.append('</div></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def strip_tags(value):
    if not value:
        return ""
    value = re.sub(r'<[^>]+>', ' ', str(value))
    value = unescape(value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def extract_html_articles(source, url, allowed_path_keywords=None, excluded_keywords=None, limit=20):
    allowed_path_keywords = allowed_path_keywords or []
    excluded_keywords = [kw.lower() for kw in (excluded_keywords or [])]
    items = []
    seen = set()
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return []
        html = res.text
        pattern = re.compile(r"<a[^>]+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", re.I | re.S)
        for href, inner in pattern.findall(html):
            full = urljoin(url, href.strip())
            low = full.lower()
            if not full.startswith('http'):
                continue
            if allowed_path_keywords and not any(k.lower() in low for k in allowed_path_keywords):
                continue
            if any(k in low for k in excluded_keywords):
                continue
            title = strip_tags(inner)
            if not title or len(title) < 8:
                continue
            if title in seen:
                continue
            seen.add(title)
            items.append({"title": title, "link": full, "source": source})
            if len(items) >= limit:
                break
    except Exception:
        return []
    return items


def normalize_news_title(title):
    title = strip_tags(title)
    title = re.sub(r'\[[^\]]+\]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def unique_news(items, limit=50):
    out = []
    seen = set()
    for item in items:
        title = normalize_news_title(item.get('title', ''))
        link = item.get('link', '').strip()
        if not title or not link:
            continue
        key = re.sub(r'[^0-9A-Za-z가-힣]+', '', title).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"title": title, "link": link, "source": item.get('source', '')})
        if len(out) >= limit:
            break
    return out


def compute_delta_text(curr, prev, suffix=""):
    if curr is None or prev is None:
        return '<span class="flat">전일 대비 정보 없음</span>'
    diff = curr - prev
    pct = safe_pct_change(curr, prev)
    cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    arrow = "▲" if diff > 0 else "▼" if diff < 0 else "■"
    if pct is None:
        return f'<span class="{cls}">{arrow} {diff:+,.0f}{suffix}</span>'
    return f'<span class="{cls}">{arrow} {diff:+,.0f}{suffix} ({pct:+.2f}%)</span>'


def parse_numeric(text_value):
    if text_value is None:
        return None
    m = re.search(r'-?[0-9][0-9,]*(?:\.[0-9]+)?', str(text_value))
    if not m:
        return None
    try:
        raw = m.group(0).replace(',', '')
        return float(raw) if '.' in raw else int(raw)
    except Exception:
        return None

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
    summary = {
        "date": None,
        "trading_value_kospi_억원": None,
        "trading_value_kosdaq_억원": None,
        "trading_value_kospi_prev_억원": None,
        "trading_value_kosdaq_prev_억원": None,
        "foreign_buy_kospi_억원": None,
        "foreign_sell_kospi_억원": None,
        "foreign_net_kospi_억원": None,
        "foreign_buy_kosdaq_억원": None,
        "foreign_sell_kosdaq_억원": None,
        "foreign_net_kosdaq_억원": None,
        "inst_buy_kospi_억원": None,
        "inst_sell_kospi_억원": None,
        "inst_net_kospi_억원": None,
        "inst_buy_kosdaq_억원": None,
        "inst_sell_kosdaq_억원": None,
        "inst_net_kosdaq_억원": None,
        "deposit_million": None,
        "deposit_prev_million": None,
        "sources_used": [],
    }

    def record_source(name):
        if name not in summary["sources_used"]:
            summary["sources_used"].append(name)

    def parse_date(text):
        for p in [r'(20[0-9]{2}[.-][0-9]{2}[.-][0-9]{2})', r'(20[0-9]{2}/[0-9]{2}/[0-9]{2})']:
            m = re.search(p, text)
            if m:
                return m.group(1).replace('-', '.').replace('/', '.')
        return None

    def parse_naver_index(url):
        out = {}
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if not r.ok:
                return out
            text = re.sub(r'\s+', ' ', r.text)
            out['date'] = parse_date(text)
            tv = re.search(r'거래대금[^0-9-]{0,20}([0-9,]+)', text)
            if tv:
                out['trading_value_억원'] = int(tv.group(1).replace(',', ''))
            fnet = re.search(r'외국인[^-0-9]{0,20}(-?[0-9,]+)', text)
            if fnet:
                out['foreign_net_억원'] = int(fnet.group(1).replace(',', ''))
            inet = re.search(r'기관[^-0-9]{0,20}(-?[0-9,]+)', text)
            if inet:
                out['inst_net_억원'] = int(inet.group(1).replace(',', ''))
        except Exception:
            return out
        return out

    def parse_krx_homepage():
        out = {}
        try:
            r = requests.get('https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd', headers=HEADERS, timeout=10)
            if not r.ok:
                return out
            text = re.sub(r'\s+', ' ', r.text)
            # KRX main page often exposes market summaries in 십억원 units.
            block = re.search(r'투자자별 매매동향(.*?)(시장별 매매동향|상장종목 현황)', text)
            src = block.group(1) if block else text
            for market in ['KOSPI', 'KOSDAQ']:
                # example pattern: KOSPI ... 기관(십억원), 2,773, 2,833, 61. 외국인(십억원), 5,827, 3,324, -2,503
                m = re.search(rf'{market}.*?기관\(십억원\)[^0-9-]*([0-9,.-]+)[^0-9-]+([0-9,.-]+)[^0-9-]+([0-9,.-]+).*?외국인\(십억원\)[^0-9-]*([0-9,.-]+)[^0-9-]+([0-9,.-]+)[^0-9-]+([0-9,.-]+)', src)
                if m:
                    out[f'inst_sell_{market.lower()}_억원'] = int(float(m.group(1).replace(',', '')) * 10)
                    out[f'inst_buy_{market.lower()}_억원'] = int(float(m.group(2).replace(',', '')) * 10)
                    out[f'inst_net_{market.lower()}_억원'] = int(float(m.group(3).replace(',', '')) * 10)
                    out[f'foreign_sell_{market.lower()}_억원'] = int(float(m.group(4).replace(',', '')) * 10)
                    out[f'foreign_buy_{market.lower()}_억원'] = int(float(m.group(5).replace(',', '')) * 10)
                    out[f'foreign_net_{market.lower()}_억원'] = int(float(m.group(6).replace(',', '')) * 10)
            m2 = re.search(r'시장별 매매동향.*?직전영업일[^0-9]{0,20}거래대금[^0-9]{0,20}KOSPI[^0-9]{0,20}([0-9,.-]+).*?KOSDAQ[^0-9]{0,20}([0-9,.-]+)', text)
            if m2:
                out['trading_value_kospi_억원'] = int(float(m2.group(1).replace(',', '')) * 10)
                out['trading_value_kosdaq_억원'] = int(float(m2.group(2).replace(',', '')) * 10)
            out['date'] = parse_date(text)
        except Exception:
            return out
        return out

    def parse_deposit_pages():
        out = {}
        urls = [
            'https://finance.naver.com/sise/sise_deposit.naver',
            'https://finance.naver.com/sise/sise_deposit.naver?menu=market_sum',
            'https://freesis.kofia.or.kr/',
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                if not r.ok:
                    continue
                text = re.sub(r'\s+', ' ', r.text)
                if out.get('date') is None:
                    out['date'] = parse_date(text)
                patterns = [
                    r'고객예탁금[^0-9-]{0,20}([0-9,]{4,})',
                    r'투자자예탁금[^0-9-]{0,20}([0-9,]{4,})',
                    r'고객예탁금[^0-9-]{0,40}전일대비[^-0-9]{0,20}(-?[0-9,]{1,})',
                ]
                if out.get('deposit_million') is None:
                    m = re.search(patterns[0], text) or re.search(patterns[1], text)
                    if m:
                        raw = int(m.group(1).replace(',', ''))
                        # usually displayed in 억원 or 백만원; normalize to million KRW conservatively.
                        out['deposit_million'] = raw * 100 if raw < 10_000_000 else raw
                if out.get('deposit_prev_million') is None:
                    m2 = re.search(r'(고객예탁금|투자자예탁금).*?전일대비[^-0-9]{0,20}(-?[0-9,]{1,})', text)
                    if m2 and out.get('deposit_million') is not None:
                        delta_raw = int(m2.group(2).replace(',', ''))
                        delta_million = delta_raw * 100 if abs(delta_raw) < 10_000_000 else delta_raw
                        out['deposit_prev_million'] = out['deposit_million'] - delta_million
                if out.get('deposit_million') is not None:
                    break
            except Exception:
                continue
        return out

    kospi = parse_naver_index('https://finance.naver.com/sise/sise_index.naver?code=KOSPI')
    kosdaq = parse_naver_index('https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ')
    if kospi:
        record_source('네이버 금융 코스피')
    if kosdaq:
        record_source('네이버 금융 코스닥')

    krx = parse_krx_homepage()
    if krx:
        record_source('한국거래소 KRX Data')

    dep = parse_deposit_pages()
    if dep:
        record_source('네이버 금융/FreeSIS')

    summary['date'] = kospi.get('date') or kosdaq.get('date') or krx.get('date') or dep.get('date')
    summary['trading_value_kospi_억원'] = kospi.get('trading_value_억원') or krx.get('trading_value_kospi_억원')
    summary['trading_value_kosdaq_억원'] = kosdaq.get('trading_value_억원') or krx.get('trading_value_kosdaq_억원')
    summary['foreign_net_kospi_억원'] = krx.get('foreign_net_kospi_억원') or kospi.get('foreign_net_억원')
    summary['foreign_net_kosdaq_억원'] = krx.get('foreign_net_kosdaq_억원') or kosdaq.get('foreign_net_억원')
    summary['inst_net_kospi_억원'] = krx.get('inst_net_kospi_억원') or kospi.get('inst_net_억원')
    summary['inst_net_kosdaq_억원'] = krx.get('inst_net_kosdaq_억원') or kosdaq.get('inst_net_억원')
    for key in [
        'foreign_buy_kospi_억원','foreign_sell_kospi_억원','foreign_buy_kosdaq_억원','foreign_sell_kosdaq_억원',
        'inst_buy_kospi_억원','inst_sell_kospi_억원','inst_buy_kosdaq_억원','inst_sell_kosdaq_억원'
    ]:
        summary[key] = krx.get(key)
    summary['deposit_million'] = dep.get('deposit_million')
    summary['deposit_prev_million'] = dep.get('deposit_prev_million')
    return summary

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
            for ent in parsed.entries[:18]:
                title = getattr(ent, "title", "").strip()
                link = getattr(ent, "link", "").strip()
                if title and link:
                    items.append({"title": title, "link": link, "source": source})
        except Exception:
            continue
    return unique_news(items, limit=50)


@st.cache_data(ttl=900)
def get_industry_news():
    keyword_groups = {
        '패션': ['패션', '의류', '섬유', '브랜드', '디자이너', '컬렉션'],
        '유통': ['유통', '리테일', '백화점', '편의점', '커머스', '쇼핑', '면세점', '마트'],
        'IT': ['IT', 'AI', '반도체', '플랫폼', '클라우드', 'SaaS', '테크', '디지털', '앱', '데이터'],
        '온라인마케팅': ['마케팅', '광고', '이커머스', '온라인', 'SNS', '검색광고', '퍼포먼스', '콘텐츠', '브랜딩'],
        '소비심리·트렌드': ['소비', '소비심리', '트렌드', '소비자', 'MZ', '매출', '구매', '수요', '라이프스타일'],
    }
    feeds = [
        ("전자신문", "https://www.etnews.com/rss/02000000000.xml"),
        ("블로터", "https://www.bloter.net/feed"),
        ("아이뉴스24", "https://www.inews24.com/rss/it.xml"),
        ("ZDNet Korea", "https://zdnet.co.kr/view/?no=feed"),
        ("한국섬유신문", "http://www.ktnews.com/rss/allArticle.xml"),
        ("한국경제", "https://www.hankyung.com/feed/all-news"),
        ("매일경제", "https://www.mk.co.kr/rss/30000001/"),
        ("서울경제", "https://www.sedaily.com/RSSFeed.xml"),
    ]
    html_sources = [
        ("한국패션뉴스", "https://www.kfashionnews.com/", ['/news/', '/article/'], ['login', 'javascript', '#']),
        ("패션엔", "https://www.fashionn.com/board/list_new.php?table=1006", ['article', 'news', 'board', 'list_new'], ['login', 'javascript', '#']),
        ("패션비즈", "https://fashionbiz.co.kr/", ['/article/', '/news/'], ['login', 'javascript', '#']),
        ("소비자경제", "https://www.consumernews.co.kr/news/articleList.html?sc_multi_code=S3&view_type=sm", ['/news/article', '/news/articleList'], ['javascript', '#']),
    ]
    items = []
    seen = set()
    keywords = [kw.lower() for kws in keyword_groups.values() for kw in kws]
    for source, url in feeds:
        try:
            parsed = feedparser.parse(url)
            for ent in parsed.entries[:20]:
                title = getattr(ent, "title", "").strip()
                link = getattr(ent, "link", "").strip()
                summary = (getattr(ent, "summary", "") or getattr(ent, "description", "")).strip()
                if not title or not link:
                    continue
                corpus = f"{title} {summary}".lower()
                if not any(kw in corpus for kw in keywords):
                    continue
                label = source
                for group, kws in keyword_groups.items():
                    if any(kw.lower() in corpus for kw in kws):
                        label = f"{source} · {group}"
                        break
                items.append({"title": title, "link": link, "source": label})
        except Exception:
            continue

    for source, url, allowed, excluded in html_sources:
        scraped = extract_html_articles(source, url, allowed_path_keywords=allowed, excluded_keywords=excluded, limit=18)
        for item in scraped:
            corpus = f"{item['title']} {item['source']}".lower()
            label = source
            for group, kws in keyword_groups.items():
                if any(kw.lower() in corpus for kw in kws):
                    label = f"{source} · {group}"
                    break
            if source == '소비자경제' and '소비심리·트렌드' not in label:
                label = f"{source} · 소비심리·트렌드"
            item['source'] = label
            items.append(item)

    return unique_news(items, limit=50)


RELATED_SITE_LINKS = [
    ("한국은행 ECOS", "https://ecos.bok.or.kr/"),
    ("한국은행 기준금리 추이", "https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643"),
    ("네이버 코스피", "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"),
    ("네이버 코스닥", "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ"),
    ("금융투자협회 FreeSIS", "https://freesis.kofia.or.kr/"),
    ("오피넷", "https://www.opinet.co.kr/"),
    ("금시세닷컴", "https://www.kumsise.com/main/index.php"),
    ("한국금거래소 금시세", "https://koreagoldx.co.kr/price/gold"),
    ("한국경제신문", "https://www.hankyung.com/"),
    ("매일경제", "https://www.mk.co.kr/"),
    ("서울경제", "https://www.sedaily.com/"),
    ("시동위키", "https://www.youtube.com/channel/UCdwlSE2aW2VCCQIS5aJwTsA"),
    ("삼프로TV", "https://www.youtube.com/@3protv"),
    ("김작가TV", "https://www.youtube.com/@lucky_tv"),
    ("월급쟁이부자들 TV", "https://www.youtube.com/@weolbu_official"),
    ("부읽남TV", "https://www.youtube.com/@buiknam_tv"),
    ("경향신문 경제", "https://www.khan.co.kr/economy"),
    ("한겨레 경제", "https://www.hani.co.kr/arti/economy/"),
    ("전자신문", "https://www.etnews.com/"),
    ("블로터", "https://www.bloter.net/"),
    ("한국패션뉴스", "https://www.kfashionnews.com/"),
    ("패션엔", "https://www.fashionn.com/"),
    ("패션비즈", "https://fashionbiz.co.kr/"),
    ("소비자경제", "https://www.consumernews.co.kr/news/articleList.html?sc_multi_code=S3&view_type=sm"),
    ("한국섬유신문", "http://www.ktnews.com/"),
    ("창조경제혁신센터", "https://ccei.creativekorea.or.kr/"),
    ("중소벤처기업부", "https://www.mss.go.kr/"),
]

# -----------------------------
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


CARD_LINKS = {
    "kospi": "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",
    "kosdaq": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",
    "gold_buy": "https://koreagoldx.co.kr/price/gold",
    "gold_sell": "https://www.kumsise.com/main/index.php",
    "base_rate": "https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643",
    "fx": "https://finance.naver.com/marketindex/",
    "brent": "https://finance.yahoo.com/quote/BZ=F",
    "domestic_oil": "https://www.opinet.co.kr/",
    "market_overview": "https://finance.naver.com/",
}

def safe_pct_change(curr, prev):
    try:
        if curr is None or prev in (None, 0):
            return None
        return (curr - prev) / prev * 100
    except Exception:
        return None

def billion_with_delta(curr, prev=None):
    base = fmt_billion_krw(curr)
    if curr is None:
        return "-"
    if prev is None:
        return f"{base} <span class='flat'>(전일 대비 정보 없음)</span>"
    diff = curr - prev
    pct = safe_pct_change(curr, prev)
    cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    return f"{base} <span class='{cls}'>({diff:+,.0f}억원 / {pct:+.2f}%)</span>"

def million_to_eok(v):
    try:
        if v is None:
            return None
        return v / 100
    except Exception:
        return None

def build_section_title(title, link=None):
    if link:
        return f'<div class="section-title">{title} <a class="section-view-more" href="{link}" target="_blank" rel="noopener noreferrer">&gt;&gt; VIEW MORE</a></div>'
    return f'<div class="section-title">{title}</div>'

def inject_auto_refresh(interval_seconds=3600):
    ms = int(interval_seconds * 1000)
    components.html(f"""
    <script>
      setTimeout(function() {{ window.location.reload(); }}, {ms});
    </script>
    """, height=0, width=0)

# -----------------------------
# SIMPLE PAGE ROUTER
# -----------------------------
page_mode = st.query_params.get("page", "main")

if page_mode == "policy":
    st.markdown('<div class="main-title">개인정보처리방침 · 서비스약관 <span class="en">(POLICY)</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="title-sub">MISHARP 투데이 경제정보 서비스 이용을 위한 기본 정책 안내 페이지입니다.</div>', unsafe_allow_html=True)
    st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="policy-box">
      <h1>개인정보처리방침 · 서비스약관</h1>
      <p>본 페이지는 MISHARP 투데이 경제정보의 기본 안내용 정책 페이지입니다. 현재 서비스는 공개 경제지표와 뉴스 링크를 제공하는 정보형 페이지이며, 별도의 회원가입 기능이나 결제 기능을 운영하지 않습니다.</p>

      <h2>1. 개인정보 처리방침</h2>
      <p>본 서비스는 이용자의 이름, 연락처, 결제정보와 같은 민감한 개인정보를 직접 수집하지 않습니다. 단, Streamlit 호스팅 환경 또는 웹서버의 기본 로그에는 접속 시간, 브라우저 정보, IP 등 최소한의 기술 정보가 일시적으로 기록될 수 있습니다.</p>
      <p>수집되는 기술 정보는 서비스 안정화, 오류 확인, 보안 점검 목적 범위 안에서만 활용되며, 별도 마케팅 목적으로 판매하거나 제공하지 않습니다.</p>

      <h2>2. 서비스 약관</h2>
      <p>본 서비스는 투자 판단을 돕기 위한 참고용 정보 페이지입니다. 제공되는 지표, 뉴스, 링크는 외부 공개 데이터를 바탕으로 표시되며 실시간 지연, 오차, 누락이 발생할 수 있습니다. 최종 투자 및 경영 판단은 이용자 본인 책임입니다.</p>
      <p>외부 링크를 통해 이동한 사이트의 콘텐츠, 서비스, 보안, 개인정보 처리 기준은 해당 사이트 정책을 따릅니다.</p>

      <h2>3. 문의 및 고지</h2>
      <p>정책 문구는 서비스 운영 상황에 따라 변경될 수 있으며, 변경 시 본 페이지에서 업데이트됩니다.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="footer">2026 MISHARP COMPANY by MIYAWA<div class="footer-links"><a href="?page=main">메인으로 돌아가기</a></div></div>', unsafe_allow_html=True)
    st.stop()

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
inject_auto_refresh(3600)
st.markdown('<div class="main-title">MISHARP 투데이 경제정보 <span class="en">(ECONOMY DASHBOARD)</span></div>', unsafe_allow_html=True)
st.markdown('<div class="title-sub">오늘 코스피, 코스닥, 환율, 금리, 금시세, 국제유가까지 한눈에 확인하는 실시간 경제 흐름 요약 페이지입니다. 투자자, 자영업자, 온라인 셀러를 위한 핵심 시장 정보만 빠르게 정리했습니다.</div>', unsafe_allow_html=True)
st.markdown('<div class="title-divider"></div>', unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1:
    st.markdown(f'<div class="top-time">한국 시간 · {kst.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)
with t2:
    st.markdown(f'<div class="top-time">미국 동부 시간 · {est.strftime("%Y-%m-%d (%a) %H:%M:%S")}</div>', unsafe_allow_html=True)

st.caption("자동 새로고침: 1시간")

# -----------------------------
# METRIC CARDS
# -----------------------------
st.markdown(build_section_title('오늘의 핵심 지표'), unsafe_allow_html=True)

r1 = st.columns(4)
with r1[0]:
    render_card(
        "오늘의 코스피",
        fmt_num(kospi["price"]) if kospi else "-",
        delta_html(kospi["diff"], kospi["pct"]) if kospi else "전일 대비 정보 없음",
        "Yahoo Finance",
        link=CARD_LINKS["kospi"]
    )
with r1[1]:
    render_card(
        "오늘의 코스닥",
        fmt_num(kosdaq["price"]) if kosdaq else "-",
        delta_html(kosdaq["diff"], kosdaq["pct"]) if kosdaq else "전일 대비 정보 없음",
        "Yahoo Finance",
        link=CARD_LINKS["kosdaq"]
    )
with r1[2]:
    render_card(
        "한국 금시세 1돈 · 살때",
        f"₩{fmt_int(gold.get('buy'))}" if gold.get("buy") else "-",
        "전일 대비 정보 없음",
        "공개 금시세 페이지 / fallback 계산" if gold.get("ok") else None,
        gold.get("message"),
        big=True,
        link=CARD_LINKS["gold_buy"]
    )
with r1[3]:
    render_card(
        "한국 금시세 1돈 · 팔때",
        f"₩{fmt_int(gold.get('sell'))}" if gold.get("sell") else "-",
        "전일 대비 정보 없음",
        "공개 금시세 페이지 / fallback 계산" if gold.get("ok") else None,
        gold.get("message"),
        big=True,
        link=CARD_LINKS["gold_sell"]
    )

r2 = st.columns(4)
with r2[0]:
    if base_rate.get("ok"):
        render_card(
            "한국 기준금리",
            f"{base_rate['value']:.2f}%",
            base_rate["message"],
            "한국은행",
            big=True,
            link=CARD_LINKS["base_rate"]
        )
    else:
        render_card(
            "한국 기준금리",
            "-",
            base_rate.get("message", "직전 변경 대비 정보 없음"),
            None,
            None,
            big=True,
            link=CARD_LINKS["base_rate"]
        )

with r2[1]:
    if fx:
        line1 = []
        line2 = []
        if "달러" in fx:
            line1.append(f"달러 {fmt_num(fx['달러']['price'])}원")
        if "엔" in fx:
            line1.append(f"엔 {fmt_num(fx['엔']['price'])}원")
        if "유로" in fx:
            line2.append(f"유로 {fmt_num(fx['유로']['price'])}원")
        if "위안" in fx:
            line2.append(f"위안 {fmt_num(fx['위안']['price'])}원")
        value_html = " / ".join(line1)
        if line2:
            value_html += f"<br>{' / '.join(line2)}"
        first = fx.get("달러")
        render_card(
            "원화환율",
            value_html,
            delta_html(first["diff"], first["pct"], unit="원", prefix="달러 기준") if first else "달러 기준 정보 없음",
            "Yahoo Finance",
            big=False,
            link=CARD_LINKS["fx"]
        )
    else:
        render_card("원화환율", "-", "환율 데이터 없음", big=False, link=CARD_LINKS["fx"])

with r2[2]:
    render_card(
        "국제유가 · 브렌트유",
        f"${fmt_num(brent['price'])} / bbl" if brent else "-",
        delta_html(brent["diff"], brent["pct"], unit=" 달러") if brent else "전일 대비 정보 없음",
        "Yahoo Finance",
        link=CARD_LINKS["brent"]
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
            big=False,
            link=CARD_LINKS["domestic_oil"]
        )
    else:
        render_card(
            "한국 기준 유가",
            "API 키 확인 필요",
            opinet.get("message", "오피넷 데이터 없음"),
            "오피넷",
            big=False,
            link=CARD_LINKS["domestic_oil"]
        )

# -----------------------------
# MARKET OVERVIEW
# -----------------------------
st.markdown(build_section_title('오늘의 한국증시', CARD_LINKS['market_overview']), unsafe_allow_html=True)

deposit_eok = million_to_eok(market_over.get('deposit_million'))
deposit_prev_eok = million_to_eok(market_over.get('deposit_prev_million'))
def flow_detail(prefix, market_code):
    buy = market_over.get(f"{prefix}_buy_{market_code}_억원")
    sell = market_over.get(f"{prefix}_sell_{market_code}_억원")
    net = market_over.get(f"{prefix}_net_{market_code}_억원")
    if buy is not None and sell is not None:
        net_txt = fmt_billion_krw(net) if net is not None else '-'
        return f"매수 {fmt_billion_krw(buy)} / 매도 {fmt_billion_krw(sell)} / 순매수 {net_txt}"
    if net is not None:
        return f"순매수 {fmt_billion_krw(net)}"
    return "-"

market_rows = {
    "종합주가지수": f"코스피 {fmt_num(kospi['price']) if kospi else '-'} / 코스닥 {fmt_num(kosdaq['price']) if kosdaq else '-'}",
    "기준일": market_over.get("date") or "-",
    "거래대금": f"코스피 {billion_with_delta(market_over.get('trading_value_kospi_억원'), market_over.get('trading_value_kospi_prev_억원'))} / 코스닥 {billion_with_delta(market_over.get('trading_value_kosdaq_억원'), market_over.get('trading_value_kosdaq_prev_억원'))}",
    "고객예탁금": billion_with_delta(deposit_eok, deposit_prev_eok),
    "외국인 동향": f"코스피 {flow_detail('foreign', 'kospi')} / 코스닥 {flow_detail('foreign', 'kosdaq')}",
    "기관 동향": f"코스피 {flow_detail('inst', 'kospi')} / 코스닥 {flow_detail('inst', 'kosdaq')}",
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
if "economy_news_limit" not in st.session_state:
    st.session_state.economy_news_limit = 10
if "industry_news_limit" not in st.session_state:
    st.session_state.industry_news_limit = 10

st.markdown('<div class="news-columns-box">', unsafe_allow_html=True)
news_left, news_divider, news_right = st.columns([1, 0.03, 1])
with news_left:
    st.markdown('<div class="section-title">오늘 꼭 확인할 주요 경제뉴스</div>', unsafe_allow_html=True)
    news_items = get_news()
    if news_items:
        st.markdown('<div class="news-wrap">', unsafe_allow_html=True)
        for item in news_items[:st.session_state.economy_news_limit]:
            st.markdown(render_news_item(item), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state.economy_news_limit < min(50, len(news_items)) and st.button("경제뉴스 더보기", key="economy_news_more", use_container_width=True):
            st.session_state.economy_news_limit = min(st.session_state.economy_news_limit + 10, min(50, len(news_items)))
            st.rerun()
    else:
        st.info('뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
with news_divider:
    st.markdown('<div class="news-divider"></div>', unsafe_allow_html=True)
with news_right:
    st.markdown('<div class="section-title">오늘의 패션 · 유통 · IT · 온라인마케팅 뉴스</div>', unsafe_allow_html=True)
    industry_news = get_industry_news()
    if industry_news:
        st.markdown('<div class="news-wrap">', unsafe_allow_html=True)
        for item in industry_news[:st.session_state.industry_news_limit]:
            st.markdown(render_news_item(item), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state.industry_news_limit < min(50, len(industry_news)) and st.button("패션·유통·IT·마케팅 뉴스 더보기", key="industry_news_more", use_container_width=True):
            st.session_state.industry_news_limit = min(st.session_state.industry_news_limit + 10, min(50, len(industry_news)))
            st.rerun()
    else:
        st.info('관련 업계 뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')

render_related_sites_box('관련정보 사이트', RELATED_SITE_LINKS)

# -----------------------------
# SEO CONTENT
# -----------------------------
st.markdown("""
<div class="seo-box">
  <h2>MISHARP 투데이 경제정보 안내</h2>

  <h3>1. 오늘 경제 흐름을 빠르게 확인하는 방법</h3>
  <p>
    MISHARP 투데이 경제정보는 오늘 코스피와 코스닥, 환율, 금리, 금시세, 국제유가, 국내 유가, ETF 흐름, 주요 경제뉴스를 한 번에 확인할 수 있도록 구성한 실시간 경제 정보 페이지입니다.
    한국 증시 현황과 오늘의 핵심 경제지표를 함께 보고 싶은 투자자, 자영업자, 온라인 쇼핑몰 운영자, 마케터에게 실무적으로 도움이 되도록 정리했습니다.
  </p>
  <p>
    검색엔진에서 경제 대시보드, 한국 증시 현황, 코스피 코스닥 실시간, 오늘의 환율, 오늘의 금시세, 오늘 국제유가 같은 키워드를 찾는 사용자가 바로 필요한 정보를 확인할 수 있도록 섹션별 구성을 분명하게 잡았습니다.
  </p>

  <h3>2. 이 페이지를 보는 순서</h3>
  <p>
    먼저 오늘의 핵심 지표에서 시장 온도를 확인하고, 이어서 오늘의 한국증시 영역에서 거래대금과 고객예탁금, 외국인과 기관의 수급 방향을 확인해 보세요. 이후 코스피 주요 종목, 코스닥 주요 종목, ETF 흐름, 주요 경제뉴스까지 함께 보면 시장 움직임을 더 입체적으로 이해할 수 있습니다.
  </p>
  <p>
    온라인 셀러와 자영업자는 환율, 유가, 금리 흐름을 함께 체크하면 원가 부담, 소비 심리, 광고 예산, 재고 전략, 가격 정책을 점검하는 데 활용할 수 있습니다.
  </p>

  <h3>3. 각 지표를 함께 봐야 하는 이유</h3>
  <p>
    코스피는 대형주 중심의 한국 대표 지수이고, 코스닥은 성장주와 기술주, 바이오주, 중소형주 흐름을 보여주는 지수입니다. 원화환율은 달러, 엔, 유로, 위안 대비 원화 가치의 변화를 보여주며 수입 원가와 해외 결제 비용에 영향을 줄 수 있습니다. 국제유가와 국내 유가는 물류비와 생활 물가에 영향을 주고, 기준금리는 소비와 투자, 부동산과 금융시장 전반에 연결됩니다.
  </p>
  <p>
    그래서 한 가지 지표만 보기보다 코스피와 코스닥, 환율, 유가, 금리, 수급 흐름을 함께 확인해야 오늘 시장 분위기를 더 정확하게 해석할 수 있습니다.
  </p>

  <h3>4. 투자와 실무에 참고할 포인트</h3>
  <p>
    단기 투자자는 전일 대비 변화폭과 거래대금, 외국인과 기관의 수급 방향을 같이 확인하는 것이 좋고, 장기 투자자는 하루 숫자보다 추세 변화와 뉴스 흐름을 꾸준히 보는 것이 중요합니다.
  </p>
  <p>
    쇼핑몰 운영자와 브랜드 실무자는 환율과 유가, 금리 변화가 마케팅 효율과 수입 원가, 소비 심리에 어떤 영향을 주는지 함께 체크하면 실제 운영 판단에 도움이 됩니다.
  </p>

  <h3>자주 묻는 질문</h3>
  <p><strong>Q. MISHARP 투데이 경제정보는 어떤 페이지인가요?</strong><br>
  A. 코스피, 코스닥, 환율, 금리, 금시세, 국제유가, ETF, 주요 경제뉴스를 한 화면에서 확인할 수 있는 실시간 경제 대시보드입니다.</p>

  <p><strong>Q. 초보자도 활용할 수 있나요?</strong><br>
  A. 네. 오늘의 핵심 지표와 오늘의 한국증시만 확인해도 시장 방향을 빠르게 파악할 수 있도록 구성했습니다.</p>

  <p><strong>Q. 이 페이지는 어떤 사람에게 특히 유용한가요?</strong><br>
  A. 투자자뿐 아니라 자영업자, 온라인 셀러, 마케터처럼 시장 변화와 소비 흐름을 함께 봐야 하는 사용자에게 유용합니다.</p>

  <p><strong>Q. 외국인 동향과 기관 동향은 무엇을 뜻하나요?</strong><br>
  A. 현재 연결된 공개 데이터 기준으로 순매수 흐름을 중심으로 표시하며, 시장 참여자별 자금 방향성을 빠르게 확인하는 참고 지표로 활용할 수 있습니다.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="footer">2026 MISHARP COMPANY by MIYAWA<br>무단 게재, 복재, 전제를 금합니다.<div class="footer-links"><a href="?page=policy">개인정보처리방침 · 서비스약관</a></div></div>',
    unsafe_allow_html=True
)
