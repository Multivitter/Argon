# app.py — Argon MVP веб-інтерфейс (Streamlit)
import os
import re
import math
import statistics
from datetime import datetime, timedelta
import requests
import streamlit as st

# ============ КОНФІГ ============
st.set_page_config(page_title="Argon — Amazon Intelligence", page_icon="🔬", layout="centered")

API_KEY = os.getenv("SCRAPINGDOG_API_KEY") or st.secrets.get("SCRAPINGDOG_API_KEY", "")
PRODUCT_URL = "https://api.scrapingdog.com/amazon/product"
SEARCH_URL = "https://api.scrapingdog.com/amazon/search"


# ============ ДАНІ ============
def parse_number(value):
    if value is None:
        return 0.0
    m = re.search(r"\d[\d,]*\.?\d*", str(value).replace(",", ""))
    return float(m.group()) if m else 0.0


@st.cache_data(ttl=3600)
def get_product(asin):
    params = {"api_key": API_KEY, "domain": "com", "asin": asin, "country": "us"}
    r = requests.get(PRODUCT_URL, params=params, timeout=60)
    return r.json() if r.status_code == 200 else None


@st.cache_data(ttl=3600)
def get_search(asin):
    params = {"api_key": API_KEY, "query": asin, "domain": "com",
              "page": 1, "country": "us", "premium": "false"}
    r = requests.get(SEARCH_URL, params=params, timeout=60)
    if r.status_code == 200:
        results = r.json().get("results", [])
        for item in results:
            if item.get("asin") == asin:
                return item
        return results[0] if results else {}
    return {}


# ============ ДВИЖОК ============
class OpportunityEngine:
    def __init__(self, product, search=None):
        self.product = product
        self.search = search or {}
        info = product.get("product_information", {})
        self.price = self._get_price()
        self.old_price = self._get_old_price()
        self.rating = float(product.get("average_rating") or 0)
        self.reviews = int(parse_number(product.get("total_reviews")))
        self.availability = str(product.get("availability_status") or "")
        self.frequently_returned = bool(product.get("is_frequently_returned"))
        self.aplus_images = product.get("aplus_images") or []
        self.has_aplus = bool(product.get("aplus")) or len(self.aplus_images) > 0
        self.brand = str(product.get("brand") or "")
        self.sold_by = str(product.get("sold_by") or "")
        self.ships_from = str(product.get("ships_from") or "")
        self.category = str(product.get("product_category") or "")
        self.category_top = self.category.split("›")[0].strip() if self.category else ""
        self.bsr = self._get_bsr()
        self.bsr_category = self._get_bsr_category()
        self.bought_text = self._get_bought_text()
        self.monthly_bought = self._parse_bought()
        self.num_images = len(product.get("images", []))
        self.num_videos = int(product.get("number_of_videos") or 0)
        self.organic_pos = self.search.get("organic_position", 0)
        self.has_coupon = bool(product.get("is_coupon_exists"))
        self.coupon_text = self._get_coupon()
        self.variants = len(product.get("customization_options", {}).get("size", []))
        self.one_star_pct = self._get_one_star_pct()
        self.title = str(product.get("title", "N/A"))

    def _get_price(self):
        offer = self.product.get("purchase_options", {}).get("single_offer", {})
        if offer.get("extracted_price"):
            return round(float(offer["extracted_price"]), 2)
        if self.search.get("extracted_price"):
            return round(float(self.search["extracted_price"]), 2)
        for f in ["price", "list_price"]:
            p = parse_number(self.product.get(f))
            if p > 0:
                return round(p, 2)
        return 0.0

    def _get_old_price(self):
        p = parse_number(self.product.get("previous_price"))
        if p > 0:
            return round(p, 2)
        if self.search.get("extracted_old_price"):
            return round(float(self.search["extracted_old_price"]), 2)
        return 0.0

    def _get_bsr(self):
        info = self.product.get("product_information", {})
        txt = info.get("Best Sellers Rank") or self.product.get("Best Sellers Rank") or ""
        m = re.search(r"#([\d,]+)", str(txt).replace(",", ""))
        return int(m.group(1)) if m else 0

    def _get_bsr_category(self):
        info = self.product.get("product_information", {})
        txt = str(info.get("Best Sellers Rank") or "")
        m = re.search(r"#[\d,]+\s+in\s+([^(]+)", txt)
        return m.group(1).strip() if m else ""

    def _get_bought_text(self):
        return str(self.product.get("number_of_people_bought")
                   or self.search.get("number_of_people_bought") or "")

    def _parse_bought(self):
        m = re.search(r"([\d.]+)\s*([km]?)", self.bought_text.lower())
        if not m:
            return 0
        num = float(m.group(1))
        u = m.group(2)
        if u == "k": num *= 1000
        elif u == "m": num *= 1_000_000
        return int(num)

    def _get_coupon(self):
        c = self.product.get("coupons", [])
        return c[0].get("coupon_text", "") if c else ""

    def _get_one_star_pct(self):
        for d in self.product.get("ratings_distribution", []):
            if d.get("rating") == 1:
                return int(parse_number(d.get("distribution")))
        return 0

    def _monthly_bought_score(self):
        b = self.monthly_bought
        if b >= 5000: return 100
        if b >= 1000: return 85
        if b >= 500: return 70
        if b >= 100: return 50
        if b > 0: return 30
        return 0

    def _bsr_score(self):
        if self.bsr <= 0: return 0
        if self.bsr <= 100: return 100
        if self.bsr <= 1000: return 85
        if self.bsr <= 10000: return 60
        if self.bsr <= 100000: return 35
        return 15

    def demand_score(self):
        mb = self._monthly_bought_score()
        if mb > 0: return mb
        bsr = self._bsr_score()
        if bsr > 0: return bsr
        return round(min(self.reviews / 50, 60))

    def competition_score(self):
        if self.reviews <= 0: return 100
        return round(max(100 - (math.log10(self.reviews + 1) * 20), 0))

    def price_score(self):
        return round(min(self.price / 50 * 100, 100))

    def market_strength_score(self):
        mb = self._monthly_bought_score()
        bsr = self._bsr_score()
        rating = self.rating / 5 * 100
        return round(mb * 0.6 + bsr * 0.3 + rating * 0.1)

    def calculate(self):
        d = self.demand_score()
        c = self.competition_score()
        p = self.price_score()
        m = self.market_strength_score()
        opp = round(d * 0.4 + m * 0.3 + p * 0.2 + c * 0.1)
        if self.frequently_returned:
            opp = round(opp * 0.7)
        if self.one_star_pct >= 10:
            opp = round(opp * 0.85)
        return {"demand": d, "competition": c, "price": p, "market": m, "opportunity": opp}


# ============ UI ============
st.title("🔬 Argon")
st.caption("Amazon Opportunity Intelligence — встав ASIN, отримай інсайт")

asin = st.text_input("ASIN товару", value="B07XGMHHT8", max_chars=10).strip().upper()
go = st.button("🔍 Аналізувати", type="primary", use_container_width=True)

if go and asin:
    if not API_KEY:
        st.error("⚠️ Не знайдено SCRAPINGDOG_API_KEY. Додай його в Streamlit Secrets.")
        st.stop()

    with st.spinner("Тягну дані з Amazon..."):
        product = get_product(asin)
        if not product:
            st.error("❌ Не вдалось отримати дані. Перевір ASIN.")
            st.stop()
        search = get_search(asin)
        e = OpportunityEngine(product, search)
        s = e.calculate()

    # Заголовок товару
    st.subheader(e.title[:90])
    if e.category_top:
        st.caption(f"📂 {e.category_top}")

    # Головна метрика — Opportunity
    color = "🟢" if s["opportunity"] >= 70 else "🟡" if s["opportunity"] >= 50 else "🔴"
    st.markdown(f"## {color} Opportunity: {s['opportunity']}/100")

    # 4 скори
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Demand", f"{s['demand']}")
    c2.metric("⚔️ Competition", f"{s['competition']}")
    c3.metric("💵 Price", f"{s['price']}")
    c4.metric("🏪 Market", f"{s['market']}")

    st.divider()

    # Ціна та продажі
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 💰 Ціна та продажі")
        price_line = f"**${e.price}**"
        if e.old_price > 0:
            disc = round((1 - e.price / e.old_price) * 100)
            price_line += f"  ~~${e.old_price}~~ **-{disc}%**"
        st.markdown(price_line)
        if e.has_coupon:
            st.markdown(f"🎟️ Купон: {e.coupon_text}")
        st.markdown(f"📦 Покупок/міс: **{e.bought_text or 'н/д'}**")
        if e.bsr:
            st.markdown(f"🏆 BSR: **#{e.bsr}** в {e.bsr_category}")

    with col_b:
        st.markdown("### ⭐ Репутація")
        st.markdown(f"Рейтинг: **{e.rating}/5** ({e.reviews:,} відгуків)")
        st.markdown(f"1★ відгуків: **{e.one_star_pct}%**")
        if e.frequently_returned:
            st.warning("⚠️ Часто повертають товар")

    st.divider()

    # Лістинг
    st.markdown("### 🏷️ Лістинг")
    l1, l2, l3 = st.columns(3)
    l1.markdown(f"**Бренд**\n\n{e.brand}")
    l1.markdown(f"**Продавець**\n\n{e.sold_by} ({e.ships_from})")
    l2.markdown(f"**Фото / Відео**\n\n{e.num_images} / {e.num_videos}")
    l2.markdown(f"**Варіантів**\n\n{e.variants}")
    l3.markdown(f"**A+ контент**\n\n{'✅ так' if e.has_aplus else '❌ ні'}")
    l3.markdown(f"**Органіка**\n\n#{e.organic_pos or 'н/д'}")

    st.divider()
    st.caption("ℹ️ Argon показує калібровані сигнали. Точне число units не показуємо — низька точність (60-75%). Bucket і тренд — висока точність.")

elif go and not asin:
    st.warning("Введи ASIN")
