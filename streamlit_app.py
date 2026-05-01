import streamlit as st
from supabase import create_client, Client
import random
from linkpreview import link_preview

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Family Bucket List", layout="wide")

# --- FUNCTIONS ---
def get_categories():
    res = supabase.table("categories").select("name").execute()
    return [item['name'] for item in res.data]

def get_items():
    res = supabase.table("bucket_items").select("*").execute()
    return res.data

@st.cache_data(ttl=3600) # Caches the image for 1 hour so the app stays fast!
def get_preview_data(url):
    if not url or not url.startswith("http"):
        return None, None
    try:
        preview = link_preview(url)
        return preview.absolute_image, preview.title
    except Exception:
        return None, None

def display_bucket_item(item, is_completed_view=False, context="cat"):
    label = f"❤️ {item['task_name']}" if item['is_favorite'] else item['task_name']
    if is_completed_view:
        label = f"✅ {label}"
    
    with st.expander(label):
        if item.get('image_url'):
            img, title = get_preview_data(item['image_url'])
            if img:
                st.image(img, use_container_width=True, caption=title)
        
        # Now using 4 columns for 4 square buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if not is_completed_view:
                if st.button("✅", key=f"{context}_done_{item['id']}", help="Complete"):
                    supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                    st.rerun()
            else:
                if st.button("🔄", key=f"{context}_undo_{item['id']}", help="Restore"):
                    supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                    st.rerun()

        with col2:
            heart_emoji = "💔" if item['is_favorite'] else "❤️"
            if st.button(heart_emoji, key=f"{context}_fav_{item['id']}", help="Favorite"):
                supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()

        with col3:
            # The link is now a square button in its own column
            if item.get('image_url') and item['image_url'].startswith("http"):
                # We use st.link_button but the CSS will make it a square because it's in a column
                st.link_button("🌐", item['image_url'], help="Open Link")
            else:
                st.button("🚫", key=f"{context}_nolink_{item['id']}", disabled=True, help="No link")

        with col4:
            if st.button("🗑️", key=f"{context}_del_{item['id']}", help="Delete"):
                supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                st.rerun()

# Pre-fetch categories for the sidebar and the tabs
categories = get_categories()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Management")
    with st.expander("➕ Add New Adventure", expanded=True):
        with st.form("add_item_form", clear_on_submit=True):
            new_task = st.text_input("What is the goal?")
            selected_cat = st.selectbox("Which category?", options=categories if categories else ["None"])
            img_url = st.text_input("Image URL (optional)")
            if st.form_submit_button("Add to List"):
                if new_task and selected_cat != "None":
                    supabase.table("bucket_items").insert({"task_name": new_task, "category_name": selected_cat, "image_url": img_url}).execute()
                    st.rerun()

    with st.expander("📂 Manage Categories"):
        new_cat_name = st.text_input("New Category Name")
        if st.button("Create Category"):
            if new_cat_name:
                supabase.table("categories").insert({"name": new_cat_name}).execute()
                st.rerun()
        st.divider()
        del_cat = st.selectbox("Delete a Category", options=["Select..."] + categories)
        if st.button("Delete Category 🗑️"):
            if del_cat != "Select...":
                supabase.table("categories").delete().eq("name", del_cat).execute()
                st.rerun()

    with st.expander("🎨 Custom Theme"):
        # Color pickers for full customization
        bg_color = st.color_picker("Background Color", "#0E1117")
        text_color = st.color_picker("Text Color", "#FFFFFF")
        btn_color = st.color_picker("Button/Icon Color", "#FF4B4B")

    st.markdown(f"""
    <style>
    /* Target the root app containers */
    .stApp, [data-testid="stHeader"], [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    /* Force all headers and labels to use the chosen text color */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: {text_color} !important;
    }}

     /* Sidebar - Solid contrast */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.8) !important;
    }}

    /* Force Sidebar text to stay white so it's always readable */
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}

    /* Fix for Tab text color */
    button[data-baseweb="tab"] p {{
        color: {text_color} !important;
    }}

    /* Make expanders slightly visible against the new background */
    .stExpander {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }}

    /* Square Buttons with Custom Color */
    [data-testid="column"] div.stButton > button, 
    [data-testid="column"] div.stLinkButton > a {{
        width: 45px !important;
        height: 45px !important;
        background-color: {btn_color} !important;
        color: white !important; /* Icons usually look best in white */
        border: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        font-size: 22px !important;
        border-radius: 8px !important;
    }}

    /* Keep the BIG buttons (Spin, Add, Create) normal size */
    div.stButton > button {{
        border-radius: 8px !important;
    }}

    /* Hover effect for buttons */
    [data-testid="column"] div.stButton > button:hover {{
        opacity: 0.8 !important;
        color: white !important;
    }}

    /* Center the icons in the columns */
    [data-testid="column"] {{
        display: flex;
        justify-content: center;
        align-items: center;
    }}

    /* Tab text fix */
    button[data-baseweb="tab"] p {{
        color: {text_color} !important;
    }}
    
    </style>
""", unsafe_allow_html=True)

# --- MAIN APP UI ---
st.title("🌟 Family Bucket List 2026")
# Grab ALL items once per rerun to keep things fast
all_items = get_items()

tab_names = ["🎲 Roulette", "❤️ Favorites"] + categories
all_tabs = st.tabs(tab_names)

# --- TAB 1: ROULETTE ---
with all_tabs[0]:
    roulette_pool = [i for i in all_items if not i['is_completed']]
    if roulette_pool:
        if st.button("🎰 SPIN THE WHEEL", use_container_width=True):
            import time
            progress_bar = st.progress(0)
            for p in range(100):
                time.sleep(0.005)
                progress_bar.progress(p + 1)
            st.session_state.roulette_winner = random.choice(roulette_pool)
            st.balloons()
        
        if 'roulette_winner' in st.session_state:
            st.success(f"### The Winner is: {st.session_state.roulette_winner['task_name']}!")
            display_bucket_item(st.session_state.roulette_winner, False, "spin")
    else:
        st.info("Add some adventures to start spinning!")

# --- TAB 2: FAVORITES ---
with all_tabs[1]:
    st.header("❤️ Your Top Adventures")
    fav_items = [i for i in all_items if i.get('is_favorite')]
    if fav_items:
        for fav in fav_items:
            display_bucket_item(fav, fav['is_completed'], "fav_tab")
    else:
        st.info("No favorites yet!")

# --- DYNAMIC CATEGORY TABS ---
for i, cat_name in enumerate(categories):
    with all_tabs[i+2]:
        st.header(f"{cat_name}")
        cat_data = [item for item in all_items if item['category_name'] == cat_name]
        
        active = [item for item in cat_data if not item['is_completed']]
        for item in active:
            display_bucket_item(item, False, f"cat_act_{i}")
        
        if not active: st.info("All done here!")
        
        st.divider()
        with st.expander("✅ See Completed Items"):
            done = [item for item in cat_data if item['is_completed']]
            for item in done:
                display_bucket_item(item, True, f"cat_done_{i}")
