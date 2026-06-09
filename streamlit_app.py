"""
King Arthur AI - Modern Dark Theme with Real Images
"""

import concurrent.futures
import json
import os
import streamlit as st
import streamlit.components.v1 as components
from langgraph_agent_v2 import KingArthurAgent
# from hf_agent import KingArthurAgent
import time
import base64
import re
import textwrap
from streamlit_image_select import image_select

st.set_page_config(
    page_title="King Arthur AI",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# LOAD CUSTOM ROBOT IMAGE
# ============================================================

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Update this path to your robot image
ROBOT_IMAGE_PATH = "F:/AI Chat Boat/king-arthur-scraper/image/bot.png"
robot_image_base64 = get_image_base64(ROBOT_IMAGE_PATH)

if robot_image_base64:
    ROBOT_AVATAR = f'<img src="data:image/png;base64,{robot_image_base64}" width="45" height="45" style="border-radius: 18px; object-fit: cover;">'
    HEADER_ROBOT = f'<img src="data:image/png;base64,{robot_image_base64}" width="60" height="60" style="border-radius: 28px; object-fit: cover;">'
else:
    ROBOT_AVATAR = '<div style="width: 45px; height: 45px; background: linear-gradient(135deg, #8b5cf6, #3b82f6); border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem;">🤖</div>'
    HEADER_ROBOT = '<div style="width: 80px; height: 80px; background: linear-gradient(135deg, #7c3aed, #4f46e5, #3b82f6); border-radius: 28px; display: flex; align-items: center; justify-content: center; font-size: 2.5rem;">🤖</div>'

# ============================================================
# SAMPLE PRODUCT DATA WITH REAL DESCRIPTIONS
# ============================================================

def get_sample_products():
    return [
        {
            "name": "Chocolate Indulgence Cake Mix",
            "price": "$16.95",
            "original_price": "$21.95",
            "save": "Save $5.00",
            "product_number": "#KA-CM-2847",
            "rating": "4.8",
            "reviews": 1247,
            "badge": "Bestseller",
            "description": "Rich, moist chocolate cake with deep cocoa flavor. Made with premium European cocoa powder.",
            "image_url": "https://placehold.co/1280x1280/7c3aed/white?text=Cake+Mix",
        },
        {
            "name": "Ultimate Chocolate Doughnut Mix",
            "price": "$8.95",
            "original_price": "$12.95",
            "save": "Save $4.00",
            "product_number": "#KA-DM-1852",
            "rating": "4.6",
            "reviews": 892,
            "badge": "Popular",
            "description": "Light to make, bake or fry.",
            "image_url": "https://placehold.co/1280x1280/8b5cf6/white?text=Doughnut+Mix",
        },
        {
            "name": "Outrageous Chocolate Chip Cookie Mix",
            "price": "$9.95",
            "original_price": "$14.95",
            "save": "Save $5.00",
            "product_number": "#KA-CM-3921",
            "rating": "4.9",
            "reviews": 2156,
            "badge": "Top Rated",
            "description": "Thick, chewy cookies loaded with premium dark chocolate chips.",
            "image_url": "https://placehold.co/1280x1280/a78bfa/white?text=Cookie+Mix",
        },
        {
            "name": "Premium Bread Flour",
            "price": "$7.95",
            "original_price": "$11.95",
            "save": "Save $4.00",
            "product_number": "#KA-BF-1105",
            "rating": "4.7",
            "reviews": 684,
            "badge": "Best Value",
            "description": "High-protein flour for artisan breads, pizza, and hearty loaves.",
            "image_url": "https://placehold.co/1280x1280/6d28d9/white?text=Bread+Flour",
        },
        {
            "name": "Baking Powder Duo Pack",
            "price": "$5.45",
            "original_price": "$7.95",
            "save": "Save $2.50",
            "product_number": "#KA-BP-2201",
            "rating": "4.4",
            "reviews": 512,
            "badge": "Kitchen Essential",
            "description": "Fast-acting baking powder for cakes, muffins, and quick breads.",
            "image_url": "https://placehold.co/1280x1280/8b5cf6/white?text=Baking+Powder",
        },
        {
            "name": "Pure Vanilla Extract",
            "price": "$13.45",
            "original_price": "$18.95",
            "save": "Save $5.50",
            "product_number": "#KA-VE-3310",
            "rating": "4.9",
            "reviews": 1340,
            "badge": "Premium",
            "description": "Rich vanilla extract for baking, frostings, and desserts.",
            "image_url": "https://placehold.co/1280x1280/f43f5e/white?text=Vanilla+Extract",
        },
        {
            "name": "Organic Brown Sugar",
            "price": "$6.50",
            "original_price": "$9.95",
            "save": "Save $3.45",
            "product_number": "#KA-BS-4412",
            "rating": "4.5",
            "reviews": 772,
            "badge": "Organic",
            "description": "Soft and moist brown sugar that adds richness to cookies and sauces.",
            "image_url": "https://placehold.co/1280x1280/ca8a04/white?text=Brown+Sugar",
        },
        {
            "name": "Sea Salt Flakes",
            "price": "$4.25",
            "original_price": "$5.95",
            "save": "Save $1.70",
            "product_number": "#KA-SS-5533",
            "rating": "4.6",
            "reviews": 412,
            "badge": "Staple",
            "description": "Delicate sea salt flakes perfect for balancing sweet baked goods.",
            "image_url": "https://placehold.co/1280x1280/0ea5e9/white?text=Sea+Salt",
        },
        {
            "name": "Classic Unsalted Butter",
            "price": "$5.95",
            "original_price": "$8.95",
            "save": "Save $3.00",
            "product_number": "#KA-UB-6604",
            "rating": "4.8",
            "reviews": 1049,
            "badge": "Favorite",
            "description": "Creamy unsalted butter for cookies, pastries, and pie crusts.",
            "image_url": "https://placehold.co/1280x1280/f97316/white?text=Butter",
        },
        {
            "name": "Large Farm Eggs",
            "price": "$4.85",
            "original_price": "$6.95",
            "save": "Save $2.10",
            "product_number": "#KA-EG-7707",
            "rating": "4.7",
            "reviews": 963,
            "badge": "Fresh",
            "description": "Grade A large eggs essential for baking structure and moisture.",
            "image_url": "https://placehold.co/1280x1280/f9a8d4/white?text=Eggs",
        },
        {
            "name": "Creamy Whole Milk",
            "price": "$3.95",
            "original_price": "$5.95",
            "save": "Save $2.00",
            "product_number": "#KA-MK-8818",
            "rating": "4.6",
            "reviews": 358,
            "badge": "Dairy",
            "description": "Whole milk for tender cakes, custards, and rich batters.",
            "image_url": "https://placehold.co/1280x1280/38bdf8/white?text=Milk",
        }
    ]

# ============================================================  
# TIMEOUT HELPERS
# ============================================================

def run_agent_with_timeout(agent, user_input, timeout_seconds=180):
    """Run the agent in a thread and allow more time for slow responses."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(agent.run, user_input)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(
                f"The assistant is taking too long to respond. "
                f"Please try again in a few seconds."
            )

# ============================================================
# CHECK IF USER IS JUST GREETING
# ============================================================

def is_greeting_only(message):
    greeting_patterns = [
        r'^(hi|hello|hey|greetings|sup|hola|yo|hi there|hello there)$',
        r'^(good morning|good afternoon|good evening)$',
        r'^(howdy|what\'s up|sup)$',
    ]
    msg_lower = message.lower().strip()
    for pattern in greeting_patterns:
        if re.match(pattern, msg_lower, re.IGNORECASE):
            return True
    return False


def get_product_value(product, *keys):
    metadata = {}
    if isinstance(product, dict):
        metadata = product.get("metadata", {}) or {}

    for key in keys:
        if isinstance(product, dict) and product.get(key):
            return product.get(key)
        if metadata.get(key):
            return metadata.get(key)
    return ""


def extract_sku_from_text(product):
    text = ""
    if isinstance(product, dict):
        text = product.get("text", "") or product.get("content", "")
    if not isinstance(text, str):
        return ""

    patterns = [
        r"SKU[:\s]*([A-Za-z0-9\-]+)",
        r"SKU\s*#[:\s]*([A-Za-z0-9\-]+)",
        r"Product\s*#[:\s]*([A-Za-z0-9\-]+)",
        r"Item\s*#[:\s]*([A-Za-z0-9\-]+)",
        r"#(\d{5,})\b"
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            return match.group(1).strip()
    return ""


def render_langgraph_flow():
    graph_path = os.path.join(os.path.dirname(__file__), "image", "graph.png")
    if os.path.exists(graph_path):
       st.image(graph_path, width=700, caption="LangGraph Flow")
    else:
        st.error(f"LangGraph image not found at: {graph_path}")

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

#MainMenu,
footer,
header,
.stDeployButton,
.stAppHeader {
    display:none !important;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html,
body,
[class*="css"]{
    font-family:'Inter',sans-serif;
}

.block-container{
    max-width:1400px !important;
    padding:1rem 2rem 2rem 2rem !important;
}

/* ================================================= */
/* BACKGROUND */
/* ================================================= */

.stApp{
    background:
        radial-gradient(circle at top left,
        rgba(139,92,246,.25),
        transparent 30%),

        radial-gradient(circle at top right,
        rgba(59,130,246,.18),
        transparent 25%),

        radial-gradient(circle at bottom center,
        rgba(99,102,241,.12),
        transparent 40%),

        #020617;
}

/* ================================================= */
/* SCROLLBAR */
/* ================================================= */

::-webkit-scrollbar{
    width:7px;
}

::-webkit-scrollbar-track{
    background:#0f172a;
}

::-webkit-scrollbar-thumb{
    background:#8b5cf6;
    border-radius:999px;
}

/* ================================================= */
/* INPUT */
/* ================================================= */

.stTextInput > div > div > input{
    position:sticky !important;
    background:rgba(15,23,42,.75) !important;

    backdrop-filter:blur(20px);

    border:1px solid rgba(255,255,255,.08) !important;

    border-radius:999px !important;

    color:white !important;

    height:60px !important;

    padding-left:24px !important;
    padding-bottom:25px !important;

    font-size:15px !important;

    transition:.3s;
}

.stTextInput > div > div > input:focus{
    border-color:#8b5cf6 !important;

    box-shadow:
        0 0 0 3px rgba(139,92,246,.15) !important;
}

/* ================================================= */
/* BUTTONS */
/* ================================================= */

.stButton button,
.stForm button,
button{

    background:
        linear-gradient(
            135deg,
            #8b5cf6,
            #6366f1
        ) !important;

    border:none !important;

    color:white !important;

    border-radius:18px !important;

    font-weight:700 !important;

    min-height:52px !important;

    box-shadow:
        0 15px 35px rgba(139,92,246,.35) !important;

    transition:.3s !important;
    
}

.stButton button:hover,
.stForm button:hover,
button:hover{

    transform:
        translateY(-3px)
        scale(1.02);

    box-shadow:
        0 22px 45px rgba(139,92,246,.45) !important;
}

/* ================================================= */
/* CHAT CARDS */
/* ================================================= */

.ai-message{

    background:rgba(15,23,42,.65);

    backdrop-filter:blur(18px);

    border:1px solid rgba(255,255,255,.06);

    border-radius:28px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.25);
}

/* ================================================= */
/* PRODUCT CARDS */
/* ================================================= */

.product-card-inner{

    background:
        rgba(15,23,42,.70) !important;

    backdrop-filter:
        blur(24px);

    border:
        1px solid rgba(255,255,255,.08);

    border-radius:
        30px !important;

    overflow:hidden;

    box-shadow:
        0 20px 60px rgba(0,0,0,.35);

    transition:.35s ease;
}

.product-card-inner:hover{

    transform:
        translateY(-6px);

    border-color:
        rgba(139,92,246,.4);

    box-shadow:
        0 30px 70px rgba(139,92,246,.15);
}

/* ================================================= */
/* PRODUCT IMAGE */
/* ================================================= */

.product-card-image{

    width:100%;

    height:280px !important;

    object-fit:cover;

    transition:.5s ease;
}

.product-card-inner:hover
.product-card-image{

    transform:scale(1.05);
}

/* ================================================= */
/* PRODUCT CONTENT */
/* ================================================= */

.product-card-body{

    padding:1.6rem !important;
}

.product-card-body h3{

    font-size:1.4rem;

    font-weight:800;

    color:white;
}

.product-description{

    color:#cbd5e1 !important;

    line-height:1.8 !important;

    opacity:.85;
}

/* ================================================= */
/* PRICE */
/* ================================================= */

.price-current{

    font-size:2rem !important;

    font-weight:900 !important;

    color:white !important;
}

.price-original{

    opacity:.5;

    font-size:.9rem;
}

.price-save{

    background:
        rgba(34,197,94,.15) !important;

    color:
        #4ade80 !important;

    border-radius:
        999px !important;

    padding:
        4px 10px !important;
}

/* ================================================= */
/* BADGE */
/* ================================================= */

.product-badge-inline{

    background:
        linear-gradient(
            135deg,
            #f59e0b,
            #ef4444
        ) !important;

    border-radius:
        999px !important;

    font-weight:
        700 !important;
}

/* ================================================= */
/* ANIMATION */
/* ================================================= */

@keyframes fadeUp{

    from{
        opacity:0;
        transform:translateY(15px);
    }

    to{
        opacity:1;
        transform:translateY(0);
    }
}

.product-card-inner,
.ai-message{

    animation:
        fadeUp .4s ease;
}

/* ================================================= */
/* PRODUCT DETAIL */
/* ================================================= */

.product-detail-card{

    background:
        rgba(15,23,42,.70);

    backdrop-filter:
        blur(30px);

    border:
        1px solid rgba(255,255,255,.08);

    border-radius:
        32px;

    box-shadow:
        0 25px 70px rgba(0,0,0,.35);
}

.product-detail-image{

    border-radius:
        30px;

    overflow:hidden;

    box-shadow:
        0 30px 80px rgba(0,0,0,.45);

    width: 100%;
    height: 420px;
    max-width: 520px;
}

.product-detail-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.product-detail-title{

    font-size:3rem;

    font-weight:900;

    line-height:1.1;
}

.product-detail-price{

    font-size:2.6rem;

    font-weight:900;

    color:white;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<script>
    // Auto-scroll to bottom when new messages arrive
    function scrollToBottom() {
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    // Scroll on load
    window.addEventListener('load', scrollToBottom);
    
    // Observe DOM changes and scroll
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)
# Add this CSS to your existing style section
st.markdown("""
<style>
/* Floating LangGraph button near chat input */
.langgraph-float-btn {
    position: fixed;
    bottom: 85px;
    right: 30px;
    z-index: 1000;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border-radius: 50%;
    width: 45px;
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
    transition: all 0.3s ease;
    font-size: 1.2rem;
}
.langgraph-float-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
}
</style>
""", unsafe_allow_html=True)
# ============================================================
# PRODUCT CARD COMPONENT - FIXED FOR BUGGY DATA
# ============================================================

def extract_product_images(product):
    metadata = {}
    if isinstance(product, dict):
        metadata = product.get("metadata", {}) or {}

    images = []
    if isinstance(product, dict):
        images = product.get("images", []) or []

    if not images and isinstance(product, dict):
        for key in ["image_url", "image", "img"]:
            value = product.get(key)
            if value:
                images = value
                break

    if not images and isinstance(metadata, dict):
        images = metadata.get("images", []) or metadata.get("image") or metadata.get("image_url") or []

    if isinstance(images, str):
        try:
            parsed = json.loads(images)
            if isinstance(parsed, list):
                images = parsed
            else:
                images = [parsed]
        except Exception:
            images = [images]

    if isinstance(images, dict):
        images = [images.get("url") or images.get("src") or images.get("image") or images.get("img")]

    if not isinstance(images, list):
        images = [images]

    cleaned_images = []
    for img in images:
        if not img:
            continue
        if isinstance(img, dict):
            img = img.get("url") or img.get("src") or img.get("image") or img.get("img")
        if isinstance(img, str) and img.strip():
            cleaned_images.append(img.strip())

    return cleaned_images


def render_product_card(product):
    """Render a product card in plain Markdown for Streamlit."""

    def clean_text(text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    rating_value = get_product_value(product, "rating", "rating_value") or 0
    if isinstance(rating_value, str):
        try:
            rating_value = float(rating_value)
        except:
            rating_value = 0

    full_stars = int(rating_value)
    half_star = (rating_value - full_stars) >= 0.5
    stars = "★" * full_stars
    if half_star:
        stars += "½"
    stars += "☆" * (5 - full_stars - (1 if half_star else 0))

    name = clean_text(get_product_value(product, "name", "title", "product_name") or "Product")
    price = clean_text(get_product_value(product, "price", "current_price", "price_text") or "N/A")
    product_number = clean_text(get_product_value(product, "product_number", "sku", "id") or extract_sku_from_text(product))
    reviews = get_product_value(product, "reviews", "review_count") or 0
    description = clean_text(get_product_value(product, "description", "short_description", "product_description", "details") or "")

    if description and ("Product information" in description or "Description Specs" in description or "Care & Storage" in description):
        description = clean_text(product.get("short_description", product.get("product_description", product.get("details", ""))))
        if not description:
            description = "Premium quality baking mix for delicious results."

    original_price = clean_text(product.get("original_price", product.get("compare_at_price", "")))
    save = clean_text(product.get("save", product.get("discount", "")))
    badge = clean_text(product.get("badge", product.get("tag", "")))
    link = product.get("link", product.get("url", ""))

    image_url = product.get("image_url") or product.get("image") or product.get("img")
    images = extract_product_images(product)
    if isinstance(images, list) and images:
        image_url = images[0]

    if not image_url:
        image_url = "https://placehold.co/1280x1280/7c3aed/white?text=Product"

    return {
        "name": name,
        "price": price,
        "product_number": product_number,
        "reviews": reviews,
        "stars": stars,
        "description": description,
        "original_price": original_price,
        "save": save,
        "badge": badge,
        "image_url": image_url,
        "link": link,
    }


# ============================================================
# DISPLAY PRODUCTS FUNCTION
# ============================================================

def display_products(products, base_key=""):
    """Display products using pure Streamlit grid layout."""
    if not products:
        st.info("No products found. Try a different search!")
        return

    products = products[:9]
    
    for i in range(0, len(products), 3):
        cols = st.columns(3)
        
        for j in range(3):
            idx = i + j
            if idx < len(products):
                product = products[idx]
                card = render_product_card(product)
                
                with cols[j]:
                    with st.container(border=True):
                        st.image(card['image_url'], use_container_width=True)
                        
                        if card['badge']:
                            st.markdown(f'<span style="background: linear-gradient(135deg, #f59e0b, #ef4444); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 600;">{card["badge"]}</span>', unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                        
                        st.markdown(f"**{card['name']}**")
                        st.markdown(f'<span style="color: #4ade80; font-size: 1.3rem; font-weight: 700;">{card["price"]}</span>', unsafe_allow_html=True)
                        
                        if card['original_price']:
                            st.caption(f"~~{card['original_price']}~~")
                        
                        st.markdown(f"{card['stars']} ({card['reviews']} reviews)")
                        st.caption(card['description'][:100] + "...")
                        
                        st.divider()
                        
                        if card['link']:
                            st.markdown(f"[🔗 View on King Arthur]({card['link']})", unsafe_allow_html=True)
                        
                        if st.button("✨ View Details", key=f"{base_key}_detail_{idx}", use_container_width=True):
                            st.session_state.selected_detail_index = idx
                            st.session_state.selected_product = product
                            st.session_state.selected_detail_image_index = 0
                            st.rerun()
# Helper function for the button click
def set_detail_view(index, product):
    """Set session state for product detail view"""
    st.session_state.selected_detail_index = index
    st.session_state.selected_product = product
    st.session_state.selected_detail_image_index = 0
# PRODUCT DETAIL VIEW
# ============================================================

# ============================================================
# PRODUCT DETAIL VIEW - MOVE THIS UP (before the call)
# ============================================================

def render_product_detail(product):
    def clean_text(text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    metadata = {}
    if isinstance(product, dict):
        metadata = product.get("metadata", {}) or {}

    def get_value(*keys):
        for key in keys:
            if isinstance(product, dict) and product.get(key):
                return product.get(key)
            if metadata.get(key):
                return metadata.get(key)
        return ""

    name = clean_text(get_value("name", "title", "product_name", "metadata.name") or "Product")
    price = clean_text(get_value("price", "current_price", "price_text", "metadata.price") or "N/A")
    link = get_value("link", "url", "metadata.link")
    sku = clean_text(get_value("sku", "product_number", "product_code", "item_code", "id") or extract_sku_from_text(product) or "N/A")
    rating = clean_text(get_value("rating", "rating_value") or "")
    reviews = clean_text(str(get_value("reviews", "review_count") or ""))
    description = clean_text(get_value("description", "short_description", "product_description", "details") or "")
    ingredients = clean_text(get_value("ingredients") or "")
    price_note = clean_text(get_value("price_note") or "")

    if description and ("Product information" in description or "Description Specs" in description or "Care & Storage" in description):
        description = clean_text(product.get("short_description", product.get("product_description", product.get("details", ""))))
        if not description:
            description = "Premium quality baking mix for delicious results."

    images = extract_product_images(product)
    if not images:
        images = ["https://placehold.co/1280x1280/7c3aed/white?text=Product"]

    # Deduplicate exact image URLs and keep only the first occurrence.
    seen_images = set()
    unique_images = []
    for img in images:
        if not img:
            continue
        if img not in seen_images:
            seen_images.add(img)
            unique_images.append(img)
    images = unique_images[:8]

    image_state_key = "selected_detail_image_index"
    if image_state_key not in st.session_state:
        st.session_state[image_state_key] = 0
    else:
        st.session_state[image_state_key] = min(st.session_state[image_state_key], len(images) - 1)

    selected_image = images[st.session_state.get(image_state_key, 0)]

    st.markdown(
        f"""
        <div class="product-detail-card">
            <div style="display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: flex-start; padding-left: 2rem; padding-right: 2rem; padding-top: 2rem; margin-bottom: 4rem;">
                <div style="flex: 1 1 380px; min-width: 280px;">
                    <div style="font-size: 2rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.5rem;">{name}</div>
                    <div style="font-size: 1.1rem; color: #a5b4fc; margin-bottom: 0.75rem;">{price}</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; color: #cbd5e1; font-size: 0.95rem; margin-bottom: 1rem;">
                        <div><strong>SKU:</strong> {sku}</div>
                        <div><strong>Rating:</strong> {rating}</div>
                        <div><strong>Reviews:</strong> {reviews}</div>
                    </div>
                    <div style="font-size: 0.95rem; color: #cbd5e1; margin-bottom: 1rem;">
                        <strong>Ingredients:</strong> {ingredients or 'No ingredients available.'}
                    </div>
                    <div style="font-size: 0.95rem; color: #c7d2fe; font-weight: 700; margin-bottom: 0.35rem;">Description:</div>
                    <div style="font-size: 0.95rem; color: #e2e8f0; line-height: 1.7; margin-bottom: 1rem;">{description or 'No description available.'}</div>
                    <div style="font-size: 0.95rem; color: #c7d2fe; margin-bottom: 1rem;">{(f'<a href="{link}" target="_blank" style="color: #a855f7;">Open product page</a>' if link else 'No product link available.')}</div>
                    <div style="font-size: 0.85rem; color: #94a3b8;">{price_note}</div>
                </div>
                <div style="flex: 1 1 420px; min-width: 280px; display: flex; flex-direction: column; gap: 1rem; align-items: center; justify-content: center;">
                    <div class="product-detail-image">
                        <img src="{selected_image}" style="width: 100%; height: 100%; object-fit: cover; display: block;" />
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            margin-top:20px;
            margin-bottom:15px;
            color:#c084fc;
            font-size:1rem;
            font-weight:600;
        ">
            Product Gallery
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_thumb = image_select(
        label="",
        images=images,
        captions=["" for _ in images],
        use_container_width=True,
    )

    if selected_thumb:
        st.session_state[image_state_key] = images.index(selected_thumb)


# ============================================================
# Then your main app code continues here
# ============================================================

# Model selection
available_models = ["qwen2.5:3b"]
# ... rest of your code ...
# MODEL SELECTION
# ============================================================

available_models = [
    "qwen2.5:3b"
]

default_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
if "ollama_model" not in st.session_state:
    st.session_state.ollama_model = default_model

selected_model = st.sidebar.selectbox(
    "Ollama model",
    available_models,
    index=available_models.index(st.session_state.ollama_model) if st.session_state.ollama_model in available_models else 0,
    help="Choose the Ollama model to run locally. Use a lighter model if your machine is slow."
)

if selected_model != st.session_state.ollama_model:
    st.session_state.ollama_model = selected_model
    if "agent" in st.session_state:
        del st.session_state.agent
    st.session_state.agent_ready = False

if st.session_state.get("agent_ready", False) and hasattr(st.session_state.get("agent"), "model_name"):
    st.sidebar.markdown(f"**Active model:** `{st.session_state.agent.model_name}`")

# In sidebar, after model selection
with st.sidebar:
    # ... existing sidebar code ...
    
    st.markdown("---")
    with st.expander("🔧 System Workflow", expanded=False):
        st.markdown(
            "Use the floating LangGraph button at the bottom-right to open the workflow diagram on demand.",
            unsafe_allow_html=True,
        )
# ============================================================
# INITIALIZATION
# ============================================================

if "agent" not in st.session_state:
    try:
        os.environ["OLLAMA_MODEL"] = st.session_state.ollama_model
        st.session_state.agent = KingArthurAgent()
        st.session_state.agent_ready = True
    except Exception as e:
        st.session_state.agent_ready = False
        st.session_state.agent_error = str(e)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_products" not in st.session_state:
    st.session_state.current_products = []

if "selected_detail_index" not in st.session_state:
    st.session_state.selected_detail_index = None

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

if not st.session_state.get("agent_ready", False):
    st.error("⚠️ Ollama is offline")
    model_name = st.session_state.get("ollama_model", os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    st.markdown(f"**Selected model:** `{model_name}`")
    if st.session_state.get("agent_error"):
        st.markdown(f"**Startup error:** `{st.session_state.agent_error}`")
    st.code(f"""
    # Start Ollama first:
    ollama serve
    ollama run {model_name}
    """)
    st.stop()

selected_product = None

if st.session_state.selected_detail_index is not None:
    selected_product = st.session_state.get("selected_product")
    if selected_product is None:
        products = st.session_state.get("current_products", [])
        if 0 <= st.session_state.selected_detail_index < len(products):
            selected_product = products[st.session_state.selected_detail_index]

if selected_product:
    st.markdown("""
    <div style="margin: 1rem 0;">
        <div style="font-size: 1.4rem; font-weight: 700; color: #c084fc; margin-bottom: 0.75rem;">Product Detail</div>
    </div>
    """, unsafe_allow_html=True)
    render_product_detail(selected_product)
    left_col, mid_col, right_col = st.columns([0.15, 1, 0.15])
    with mid_col:
        if st.button("◀ Back to Results", use_container_width=True, key="back_to_results"):
            st.session_state.selected_detail_index = None
            st.session_state.selected_product = None
            st.rerun()
    st.stop()

st.markdown(f"""
<div style="text-align: center; padding: 1.5rem 1rem 2rem 1rem;">
    <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #7c3aed, #4f46e5, #3b82f6); border-radius: 28px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; box-shadow: 0 15px 35px rgba(124, 58, 237, 0.3);">
        {HEADER_ROBOT}
    </div>
    <div style="font-size: 3.5rem; font-weight: 900;letter-spacing: -1px; background: linear-gradient(135deg, #c084fc, #818cf8, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        King Arthur AI
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# LANGGRAPH FLOATING BUTTON WITH MODAL
# ============================================================

# Initialize session state for modal
# ============================================================
# SIMPLEST WORKING VERSION - PURE STREAMLIT
# ============================================================

if "show_graph" not in st.session_state:
    st.session_state.show_graph = False

# Floating button
st.markdown("""
<style>
.floating-btn {
    position: fixed;
    bottom: 100px;
    right: 25px;
    z-index: 9999;
}
.floating-btn button {
    background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
    border-radius: 50% !important;
    width: 55px !important;
    height: 55px !important;
    padding: 0 !important;
    font-size: 1.6rem !important;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    cols = st.columns([0.85, 0.05, 0.1])
    with cols[2]:
        if st.button("🧠", key="float_btn"):
            st.session_state.show_graph = True
            st.rerun()

# Show full screen when activated
if st.session_state.show_graph:
    # Use expander as a modal-like container
    st.markdown("---")
    st.markdown("# 🧠 LangGraph Workflow Diagram")
    
    graph_path = os.path.join(os.path.dirname(__file__), "image", "graph.png")
    if os.path.exists(graph_path):
        st.image(graph_path, use_container_width=True)
        
        # Close button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("❌ Close", use_container_width=True, type="primary"):
                st.session_state.show_graph = False
                st.rerun()
    else:
        st.error("Image not found")
    
    st.markdown("---")
# CHAT DISPLAY - FULL WIDTH
# ===========================================================

for msg_idx, msg in enumerate(st.session_state.chat_history):
    if msg["role"] == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
            <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 0.9rem 1.4rem; border-radius: 24px 24px 8px 24px; max-width: 70%;">
                <span style="color: white;">{msg["content"]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(20, 25, 50, 0.8); backdrop-filter: blur(10px); border-radius: 24px; padding: 1.3rem; margin: 1rem 0; border: 1px solid rgba(124, 58, 237, 0.2);">
            <div style="display: flex; gap: 12px; margin-bottom: 0.8rem;">
                {ROBOT_AVATAR}
                <div>
                    <div style="font-weight: 700; color: #c084fc;">King Arthur AI</div>
                    <div style="color: #94a3b8; font-size: 0.7rem;">Baking Assistant</div>
                </div>
            </div>
            <div style="color: #f1f5f9; line-height: 1.7;">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if msg.get("products") and len(msg["products"]) > 0 and not msg.get("is_greeting", False):
            st.markdown("""
            <div style="margin: 1.5rem 0 1rem 0;">
                <div style="font-size: 1.2rem; font-weight: 600; color: #c084fc;">Recommended Products</div>
            </div>
            """, unsafe_allow_html=True)
            display_products(msg["products"], base_key=f"msg{msg_idx}")

if len(st.session_state.chat_history) == 0:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(79, 70, 229, 0.1)); border-radius: 28px; padding: 2rem; margin: 1rem 0; border: 1px solid rgba(124, 58, 237, 0.2);">
        <div style="display: flex; gap: 12px; margin-bottom: 1rem;">
            {ROBOT_AVATAR}
            <div>
                <div style="font-weight: 700; color: #c084fc;">King Arthur AI</div>
                <div style="color: #94a3b8; font-size: 0.7rem;">Baking Assistant</div>
            </div>
        </div>
        <div style="color: #f1f5f9; line-height: 1.7;">
            Hello! It's nice to meet you. How can I assist you today?
        </div>
    </div>
    """, unsafe_allow_html=True)
# ============================================================
# CHAT INPUT WITH THINKING SPINNER
# ============================================================

# Modern chat input
user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Show thinking animation
    with st.spinner("🍞 King Arthur is thinking..."):
        try:
            # Check if greeting
            is_greeting = is_greeting_only(user_input)
            
            if is_greeting:
                response_text = "Hello! 👋 It's nice to meet you. How can I help you with your baking today?"
                products = []
                st.session_state.current_products = []
            else:
                # Run agent
                result = run_agent_with_timeout(
                    st.session_state.agent,
                    user_input,
                    timeout_seconds=120
                ) or {}
                
                if not isinstance(result, dict):
                    result = {}
                
                response_text = result.get("response") or "I'm here to help!"
                if not isinstance(response_text, str):
                    response_text = str(response_text)
                response_text = response_text.strip() or "I'm here to help!"

                products = result.get("products", [])
                if not isinstance(products, list):
                    products = []

                st.session_state.current_products = products
            
            # Add assistant response
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response_text,
                "products": products,
                "is_greeting": is_greeting
            })
            
        except TimeoutError:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "⏱️ The assistant is taking too long to respond. Please try again.",
                "products": [],
                "is_greeting": False
            })
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)}",
                "products": [],
                "is_greeting": False
            })
    
    # Refresh the page
    st.rerun()



# FOOTER
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.75rem; padding: 0.5rem;">
    @Made In copyright 2026. For demo purposes only.
</div>
""", unsafe_allow_html=True)
        