# app.py — Argon MVP (Streamlit) — 3 мови + дизайн + підказки
import os
import re
import math
import requests
import streamlit as st

st.set_page_config(page_title="Argon — Amazon Intelligence", page_icon="🔬", layout="centered")

API_KEY = os.getenv("SCRAPINGDOG_API_KEY") or st.secrets.get("SCRAPINGDOG_API_KEY", "")
PRODUCT_URL = "https://api.scrapingdog.com/amazon/product"
SEARCH_URL = "https://api.scrapingdog.com/amazon/search"

# ============ ПЕРЕКЛАДИ ============
T = {
    "UA": {
        "tagline": "Amazon Opportunity Intelligence — встав ASIN, отримай інсайт",
        "asin_label": "ASIN товару", "analyze": "🔍 Аналізувати",
        "price_sales": "💰 Ціна та продажі", "reputation": "⭐ Репутація",
        "listing": "🏷️ Лістинг", "opportunity": "Opportunity",
        "demand": "🔥 Попит", "competition": "⚔️ Конкуренція", "price": "💵 Ціна", "market": "🏪 Ринок",
        "coupon": "Купон", "bought_mo": "Покупок/міс", "bsr": "BSR",
        "rating": "Рейтинг", "reviews": "відгуків", "one_star": "1★ відгуків",
        "returned": "⚠️ Часто повертають товар",
        "brand": "Бренд", "seller": "Продавець", "photos": "Фото / Відео",
        "variants": "Варіантів", "aplus": "A+ контент", "organic": "Органіка",
        "yes": "✅ так", "no": "❌ ні", "na": "н/д", "err": "❌ Не вдалось. Перевір ASIN.",
        "spin": "Тягну дані з Amazon...", "enter": "Введи ASIN",
        "footer": "ℹ️ Argon показує калібровані сигнали. Точне число units не показуємо — низька точність. Bucket і тренд — висока.",
        "no_key": "⚠️ Не знайдено API ключ. Додай SCRAPINGDOG_API_KEY у Secrets.",
        "help_opp": "Підсумкова оцінка можливості зайти в товар/нішу (0-100). Враховує попит, ринок, ціну, конкуренцію.",
        "help_demand": "Чи є попит на товар. Рахується з реальних покупок/міс та BSR.",
        "help_comp": "Наскільки важко зайти. Більше відгуків у конкурента = важче (нижчий бал).",
        "help_price": "Цінова привабливість. Дорожчий товар = вища потенційна маржа.",
        "help_market": "Сила ринку в цілому — чи є тут гроші взагалі (продажі + BSR + рейтинг).",
        "view_amazon": "🔗 Відкрити на Amazon",
    },
    "RU": {
        "tagline": "Amazon Opportunity Intelligence — вставь ASIN, получи инсайт",
        "asin_label": "ASIN товара", "analyze": "🔍 Анализировать",
        "price_sales": "💰 Цена и продажи", "reputation": "⭐ Репутация",
        "listing": "🏷️ Листинг", "opportunity": "Opportunity",
        "demand": "🔥 Спрос", "competition": "⚔️ Конкуренция", "price": "💵 Цена", "market": "🏪 Рынок",
        "coupon": "Купон", "bought_mo": "Покупок/мес", "bsr": "BSR",
        "rating": "Рейтинг", "reviews": "отзывов", "one_star": "1★ отзывов",
        "returned": "⚠️ Часто возвращают товар",
        "brand": "Бренд", "seller": "Продавец", "photos": "Фото / Видео",
        "variants": "Вариантов", "aplus": "A+ контент", "organic": "Органика",
        "yes": "✅ да", "no": "❌ нет", "na": "н/д", "err": "❌ Не удалось. Проверь ASIN.",
        "spin": "Тяну данные с Amazon...", "enter": "Введи ASIN",
        "footer": "ℹ️ Argon показывает калиброванные сигналы. Точное число units не показываем — низкая точность. Bucket и тренд — высокая.",
        "no_key": "⚠️ Не найден API ключ. Добавь SCRAPINGDOG_API_KEY в Secrets.",
        "help_opp": "Итоговая оценка возможности зайти в товар/нишу (0-100). Учитывает спрос, рынок, цену, конкуренцию.",
        "help_demand": "Есть ли спрос на товар. Считается из реальных покупок/мес и BSR.",
        "help_comp": "Насколько сложно зайти. Больше отзывов у конкурента = сложнее (ниже балл).",
        "help_price": "Ценовая привлекательность. Дороже товар = выше потенциальная маржа.",
        "help_market": "Сила рынка в целом — есть ли тут деньги вообще (продажи + BSR + рейтинг).",
        "view_amazon": "🔗 Открыть на Amazon",
    },
    "EN": {
        "tagline": "Amazon Opportunity Intelligence — paste ASIN, get insight",
        "asin_label": "Product ASIN", "analyze": "🔍 Analyze",
        "price_sales": "💰 Price & Sales", "reputation": "⭐ Reputation",
        "listing": "🏷️ Listing", "opportunity": "Opportunity",
        "demand": "🔥 Demand", "competition": "⚔️ Competition", "price": "💵 Price", "market": "🏪 Market",
        "coupon": "Coupon", "bought_mo": "Bought/mo", "bsr": "BSR",
        "rating": "Rating", "reviews": "reviews", "one_star": "1★ reviews",
        "returned": "⚠️ Frequently returned",
        "brand": "Brand", "seller": "Seller", "photos": "Photos / Videos",
        "variants": "Variants", "aplus": "A+ content", "organic": "Organic rank",
        "yes": "✅ yes", "no": "❌ no", "na": "n/a", "err": "❌ Failed. Check ASIN.",
        "spin": "Fetching Amazon data...", "enter": "Enter ASIN",
        "footer": "ℹ️ Argon shows calibrated signals. Exact units not shown — low accuracy. Bucket & trend — high accuracy.",
        "no_key": "⚠️ API key not found. Add SCRAPINGDOG_API_KEY to Secrets.",
        "help_opp": "Final opportunity score to enter the product/niche (0-100). Combines demand, market, price, competition.",
        "help_demand": "Is there demand. Calculated from real monthly purchases and BSR.",
        "help_comp": "How hard to enter. More competitor reviews = harder (lower score).",
        "help_price": "Price attractiveness. Higher price = higher potential margin.",
        "help_market": "Overall market strength — is there money here at all (sales + BSR + rating).",
        "view_amazon": "🔗 View on Amazon",
    },
}

# ============ СТИЛІ ============
st.markdown("""
<style>
    .stApp { background: #0a0a0f; }
    .argon-title { font-size: 3rem; font-weight: 800; background: linear-gradient(90deg,#7b2ff7,#00d4ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:0; }
    .opp-card { background: linear-gradient(135deg,#1a1a2e,#16213e); border-radius:20px;
        padding:28px; text-align:center; border:1px solid #2a2a4a; margin:20px 0; }
    .opp-num { font-size:4rem; font-weight:900; line-height:1; }
    .info-card { background:#15151f; border-radius:14px; padding:20px; border:1px solid #252535; height:100%; }
    .info-card h4 { margin-top:0; color:#cdd; }
    .stButton>button { background:linear-gradient(90deg,#7b2ff7,#00d4ff); color:#fff; border:none;
        font-weight:700; border-radius:12px; padding:12px; }
</style>
""", unsafe_allow_html=True)


def parse_number(value):
    if value is None: return 0.0
    m = re.search(r"\d[\d,]*\.?\d*", str(value).replace(",", ""))
    return float(m.group()) if m else 0.0


@st.cache_data(ttl=3600)
def get_product(asin):
    r = requests.get(PRODUCT_URL, params={"api_key": API_KEY, "domain": "com", "asin": asin, "country": "us"}, timeout=60)
    return r.json() if r.status_code == 200 else None


@st.cache_data(ttl=3600)
def get_search(asin):
    r = requests.get(SEARCH_URL, params={"api_key": API_KEY, "query": asin, "domain": "com", "page": 1, "country": "us", "premium": "false"}, timeout=60)
    if r.status_code == 200:
        results = r.json().get("results", [])
        for item in results:
            if item.get("asin") == asin: return item
        return results[0] if results else {}
    return {}


class OpportunityEngine:
    def __init__(self, product, search=None):
        self.product = product
        self.search = search or {}
        self.price = self._get_price()
        self.old_price = self._get_old_price()
        self.rating = float(product.get("average_rating") or 0)
        self.reviews = int(parse_number(product.get("total_reviews")))
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
        self.bought_text = str(product.get("number_of_people_bought") or self.search.get("number_of_people_bought") or "")
        self.monthly_bought = self._parse_bought()
        self.num_images = len(product.get("images", []))
        self.num_videos = int(product.get("number_of_videos") or 0)
        self.organic_pos = self.search.get("organic_position", 0)
        self.has_coupon = bool(product.get("is_coupon_exists"))
        self.coupon_text = (product.get("coupons") or [{}])[0].get("coupon_text", "")
        self.variants = len(product.get("customization_options", {}).get("size", []))
        self.one_star_pct = self._one_star()
        self.title = str(product.get("title", "N/A"))

    def _get_price(self):
        offer = self.product.get("purchase_options", {}).get("single_offer", {})
        if offer.get("extracted_price"): return round(float(offer["extracted_price"]), 2)
        if self.search.get("extracted_price"): return round(float(self.search["extracted_price"]), 2)
        for f in ["price", "list_price"]:
            p = parse_number(self.product.get(f))
            if p > 0: return round(p, 2)
        return 0.0

    def _get_old_price(self):
        p = parse_number(self.product.get("previous_price"))
        if p > 0: return round(p, 2)
        if self.search.get("extracted_old_price"): return round(float(self.search["extracted_old_price"]), 2)
        return 0.0

    def _get_bsr(self):
        txt = self.product.get("product_information", {}).get("Best Sellers Rank") or ""
        m = re.search(r"#([\d,]+)", str(txt).replace(",", ""))
        return int(m.group(1)) if m else 0

    def _get_bsr_category(self):
        txt = str(self.product.get("product_information", {}).get("Best Sellers Rank") or "")
        m = re.search(r"#[\d,]+\s+in\s+([^(]+)", txt)
        return m.group(1).strip() if m else ""

    def _parse_bought(self):
        m = re.search(r"([\d.]+)\s*([km]?)", self.bought_text.lower())
        if not m: return 0
        num = float(m.group(1)); u = m.group(2)
        if u == "k": num *= 1000
        elif u == "m": num *= 1_000_000
        return int(num)

    def _one_star(self):
        for d in self.product.get("ratings_distribution", []):
            if d.get("rating") == 1: return int(parse_number(d.get("distribution")))
        return 0

    def _mb_score(self):
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

    def calculate(self):
        mb = self._mb_score(); bsr = self._bsr_score()
        demand = mb if mb > 0 else (bsr if bsr > 0 else round(min(self.reviews / 50, 60)))
        competition = round(max(100 - (math.log10(self.reviews + 1) * 20), 0)) if self.reviews > 0 else 100
        price = round(min(self.price / 50 * 100, 100))
        market = round(mb * 0.6 + bsr * 0.3 + (self.rating / 5 * 100) * 0.1)
        opp = round(demand * 0.4 + market * 0.3 + price * 0.2 + competition * 0.1)
        if self.frequently_returned: opp = round(opp * 0.7)
        if self.one_star_pct >= 10: opp = round(opp * 0.85)
        return {"demand": demand, "competition": competition, "price": price, "market": market, "opportunity": opp}


# ============ UI ============
col_t, col_l = st.columns([3, 1])
with col_t:
    st.markdown('<p class="argon-title">🔬 Argon</p>', unsafe_allow_html=True)
with col_l:
    lang = st.selectbox("🌐", ["UA", "RU", "EN"], label_visibility="collapsed")

t = T[lang]
st.caption(t["tagline"])

asin = st.text_input(t["asin_label"], value="B07XGMHHT8", max_chars=10).strip().upper()
go = st.button(t["analyze"], use_container_width=True)

if go and asin:
    if not API_KEY:
        st.error(t["no_key"]); st.stop()
    with st.spinner(t["spin"]):
        product = get_product(asin)
        if not product:
            st.error(t["err"]); st.stop()
        search = get_search(asin)
        e = OpportunityEngine(product, search)
        s = e.calculate()

    st.subheader(e.title[:90])
    st.markdown(f"[{t['view_amazon']}](https://www.amazon.com/dp/{asin})")
    if e.category_top:
        st.caption(f"📂 {e.category_top}")

    # Opportunity card + підказка
    color = "#22c55e" if s["opportunity"] >= 70 else "#eab308" if s["opportunity"] >= 50 else "#ef4444"
    st.markdown(f"""
    <div class="opp-card">
        <div style="color:#9a9ab0;font-size:1rem;">{t['opportunity'].upper()}</div>
        <div class="opp-num" style="color:{color};">{s['opportunity']}<span style="font-size:1.5rem;color:#666;">/100</span></div>
    </div>""", unsafe_allow_html=True)
    st.caption(f"ℹ️ {t['help_opp']}")

    # 4 scores з підказками (наведи на ℹ️)
    cols = st.columns(4)
    cols[0].metric(t["demand"], s["demand"], help=t["help_demand"])
    cols[1].metric(t["competition"], s["competition"], help=t["help_comp"])
    cols[2].metric(t["price"], s["price"], help=t["help_price"])
    cols[3].metric(t["market"], s["market"], help=t["help_market"])

    st.write("")

    # Price & Reputation
    ca, cb = st.columns(2)
    with ca:
        price_html = f"<h4>{t['price_sales']}</h4><div style='font-size:1.6rem;font-weight:800;color:#fff;'>${e.price}</div>"
        if e.old_price > 0:
            disc = round((1 - e.price / e.old_price) * 100)
            price_html += f"<div style='color:#9a9ab0;'><span style='text-decoration:line-through;'>${e.old_price}</span> <span style='color:#22c55e;'>-{disc}%</span></div>"
        if e.has_coupon:
            price_html += f"<div style='color:#f0a;margin-top:8px;'>🎟️ {t['coupon']}: {e.coupon_text}</div>"
        price_html += f"<div style='margin-top:8px;'>📦 {t['bought_mo']}: <b>{e.bought_text or t['na']}</b></div>"
        if e.bsr:
            price_html += f"<div>🏆 {t['bsr']}: <b>#{e.bsr}</b> · {e.bsr_category}</div>"
        st.markdown(f'<div class="info-card">{price_html}</div>', unsafe_allow_html=True)
    with cb:
        rep_html = f"<h4>{t['reputation']}</h4>"
        rep_html += f"<div style='font-size:1.6rem;font-weight:800;color:#fff;'>{e.rating}/5</div>"
        rep_html += f"<div style='color:#9a9ab0;'>{e.reviews:,} {t['reviews']}</div>"
        rep_html += f"<div style='margin-top:8px;'>{t['one_star']}: <b>{e.one_star_pct}%</b></div>"
        if e.frequently_returned:
            rep_html += f"<div style='color:#ef4444;margin-top:8px;'>{t['returned']}</div>"
        st.markdown(f'<div class="info-card">{rep_html}</div>', unsafe_allow_html=True)

    st.write("")

    # Listing
    list_html = f"<h4>{t['listing']}</h4><div style='display:flex;flex-wrap:wrap;gap:24px;'>"
    items = [
        (t["brand"], e.brand or t["na"]),
        (t["seller"], f"{e.sold_by or t['na']} ({e.ships_from})"),
        (t["photos"], f"{e.num_images} / {e.num_videos}"),
        (t["variants"], str(e.variants)),
        (t["aplus"], t["yes"] if e.has_aplus else t["no"]),
        (t["organic"], f"#{e.organic_pos or t['na']}"),
    ]
    for label, val in items:
        list_html += f"<div><div style='color:#9a9ab0;font-size:0.8rem;'>{label}</div><div style='color:#fff;font-weight:600;'>{val}</div></div>"
    list_html += "</div>"
    st.markdown(f'<div class="info-card">{list_html}</div>', unsafe_allow_html=True)

    st.write("")
    st.caption(t["footer"])

elif go and not asin:
    st.warning(t["enter"])
