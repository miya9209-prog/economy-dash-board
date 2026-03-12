import math
import re
from datetime import datetime

import pandas as pd
import pytz
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="경제 대시보드", layout="wide")

st.markdown("""
<style>
:root{
  --text:#f8fafc;
  --muted:#a8b4c7;
  --green:#3ee17b;
  --red:#ff6b6b;

  --btn-bg:#e8eef9;
  --btn-text:#0b1220;
}

.block-container{
  padding-top:3rem;
  max-width:1440px;
}

.main-title{
  font-size:2rem;
  font-weight:800;
}

.card{
  background:linear-gradient(180deg,#11203a,#1c2840);
  border:1px solid rgba(89,115,156,.42);
  border-radius:16px;
  padding:16px;
  margin-bottom:16px;
}

.card h4{
  font-size:.95rem;
  margin-bottom:.6rem;
}

.card .value{
  font-size:1.45rem;
  font-weight:800;
}

.card .sub{
  font-size:.9rem;
}

.up{color:var(--green)}
.down{color:var(--red)}
.flat{color:#cbd5e1}

.stButton > button{
  color:var(--btn-text)!important;
  background:var(--btn-bg)!important;
  font-weight:800!important;
  border-radius:10px!important;
}

</style>
""",unsafe_allow_html=True)


# ------------------------
# 공통 포맷 함수
# ------------------------

def fmt_num(v,d=2):
    if v is None:
        return "-"
    return f"{v:,.{d}f}"

def fmt_int(v):
    if v is None:
        return "-"
    return f"{int(round(v)):,}"


def delta_html(diff,pct):
    if diff is None:
        return "전일 대비 정보 없음"

    cls="up" if diff>0 else "down"

    return f'<span class="{cls}">{diff:+.2f} ({pct:+.2f}%)</span>'


# ------------------------
# 시장 데이터
# ------------------------

@st.cache_data(ttl=60)
def get_index(ticker):
    try:
        df=yf.Ticker(ticker).history(period="5d")
        price=df["Close"].iloc[-1]
        prev=df["Close"].iloc[-2]
        diff=price-prev
        pct=diff/prev*100
        return price,diff,pct
    except:
        return None,None,None


@st.cache_data(ttl=300)
def get_fx():
    pairs={
        "달러":"KRW=X",
        "엔":"JPYKRW=X",
        "위안":"CNYKRW=X",
        "유로":"EURKRW=X"
    }

    out={}
    for k,v in pairs.items():
        p,d,pct=get_index(v)
        if p:
            out[k]=(p,d,pct)

    return out


@st.cache_data(ttl=300)
def get_brent():
    return get_index("BZ=F")


# ------------------------
# 기준금리
# ------------------------

@st.cache_data(ttl=3600)
def get_base_rate():

    try:

        r=requests.get("https://www.bok.or.kr",timeout=8)
        text=r.text

        m=re.search(r"([0-9]+\.[0-9]+)\s*%",text)

        if m:
            rate=float(m.group(1))

            if 1<=rate<=10:
                return rate

    except:
        pass

    return None


# ------------------------
# 금시세
# ------------------------

@st.cache_data(ttl=3600)
def get_gold():

    urls=[
        "https://m.koreagoldx.co.kr/",
        "https://www.koreagoldx.co.kr/",
        "https://www.exgold.co.kr/"
    ]

    buy=None
    sell=None

    for u in urls:

        try:

            r=requests.get(u,timeout=8)
            text=re.sub(r"\s+"," ",r.text)

            if buy is None:

                m=re.search(r"살\s*때[^0-9]{0,20}([0-9,]{5,})",text)

                if m:
                    buy=int(m.group(1).replace(",",""))

            if sell is None:

                m=re.search(r"팔\s*때[^0-9]{0,20}([0-9,]{5,})",text)

                if m:
                    sell=int(m.group(1).replace(",",""))

        except:
            pass

    return buy,sell


# ------------------------
# 카드 렌더
# ------------------------

def card(title,value,sub):

    st.markdown(f"""
<div class="card">
<h4>{title}</h4>
<div class="value">{value}</div>
<div class="sub">{sub}</div>
</div>
""",unsafe_allow_html=True)


# ------------------------
# 시간
# ------------------------

kst=datetime.now(pytz.timezone("Asia/Seoul"))
est=datetime.now(pytz.timezone("US/Eastern"))

st.markdown('<div class="main-title">경제 대시보드</div>',unsafe_allow_html=True)

c1,c2=st.columns(2)

with c1:
    st.write("한국시간",kst.strftime("%Y-%m-%d %H:%M:%S"))

with c2:
    st.write("미국시간",est.strftime("%Y-%m-%d %H:%M:%S"))


# ------------------------
# 데이터 로딩
# ------------------------

kospi=get_index("^KS11")
kosdaq=get_index("^KQ11")
fx=get_fx()
brent=get_brent()
rate=get_base_rate()
gold=get_gold()

# ------------------------
# 카드
# ------------------------

st.markdown("### 오늘의 핵심 지표")

r1=st.columns(4)

with r1[0]:
    p,d,pct=kospi
    card("오늘의 코스피",fmt_num(p),delta_html(d,pct))

with r1[1]:
    p,d,pct=kosdaq
    card("오늘의 코스닥",fmt_num(p),delta_html(d,pct))

with r1[2]:
    buy,sell=gold
    card("금시세 1돈 · 살때",fmt_int(buy),"전일 대비 정보 없음")

with r1[3]:
    buy,sell=gold
    card("금시세 1돈 · 팔때",fmt_int(sell),"전일 대비 정보 없음")


r2=st.columns(4)

with r2[0]:

    if rate:
        card("한국 기준금리",f"{rate} %","한국은행 기준")
    else:
        card("한국 기준금리","-","정보 없음")

with r2[1]:

    if fx:

        txt=""

        for k,v in fx.items():

            txt+=f"{k} {fmt_num(v[0])}원<br>"

        card("원화환율",txt,"")

with r2[2]:

    p,d,pct=brent

    card("브렌트유",f"${fmt_num(p)}",delta_html(d,pct))


with r2[3]:

    card("한국 기준 유가","오피넷 API 필요","")


# ------------------------
# 종목 리스트
# ------------------------

st.markdown("### 코스피 주요 종목")

stocks=[
("삼성전자","005930.KS"),
("SK하이닉스","000660.KS"),
("현대차","005380.KS"),
("기아","000270.KS"),
("NAVER","035420.KS"),
("카카오","035720.KS"),
]

rows=[]

for name,t in stocks:

    p,d,pct=get_index(t)

    rows.append({
        "종목":name,
        "현재가":fmt_int(p),
        "등락률":f"{pct:+.2f}%"
    })

st.dataframe(pd.DataFrame(rows),use_container_width=True)
