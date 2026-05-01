import streamlit as st
from supabase import create_client, Client
import random
from linkpreview import link_preview

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Family Bucket List", layout="wide")

# CSS for a tight button row
st.markdown("""
    <style>
    /* Make the expander header look more like a list item */
    .stExpander {
        border-radius: 10px !important;
        margin-bottom: 10px !important;
    }
    /* Simple button styling */
    div.stButton > button, div.stLinkButton > a {
        width: 100% !important; /* On mobile, full-width buttons inside expanders are very easy to tap */
        margin-bottom: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_categories():
    res = supabase.table("categories").select("name").execute()
    return [item['name'] for item in res.data]

def get_items():
    res = supabase.table("bucket_items").select("*").execute()
    return res.data

def get_preview_data(url):
    """
    Tries to grab the title and image from a URL.
    Returns (image_url, title) or (None, None) if it fails.
    """
    if not url or not url.startswith("http"):
        return None, None
        
    try:
        # The 'grabber' visits the site and pulls the metadata
        preview = link_preview(url)
        return preview.absolute_image, preview.title
    except Exception:
        # If the site is down or blocks scraping, we fail gracefully
        return None, None

def display_bucket_item(item, is_completed_view=False, context="cat"):
    """
    context: A string to make keys unique (e.g., 'cat', 'fav', 'spin')
    """
    label = f"❤️ {item['task_name']}" if item['is_favorite'] else item['task_name']
    if is_completed_view:
        label = f"✅ {label}"
    
    with st.expander(label):
        if item.get('image_url'):
            img, title = get_preview_data(item['image_url'])
            if img:
                st.image(img, use_container_width=True, caption=title)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if not is_completed_view:
                # Added {context} to the key
                if st.button("✅ Done ", key=f"{context}_done_{item['id']}"):
                    supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                    st.rerun()
            else:
                if st.button("🔄 Undo", key=f"{context}_undo_{item['id']}"):
                    supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                    st.rerun()

        with col2:
            heart_emoji = "💔" if item['is_favorite'] else "❤️"
            fav_label = "Unfav" if item['is_favorite'] else "Fav"
            if st.button(f"{heart_emoji} {fav_label}", key=f"{context}_fav_{item['id']}"):
                supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                st.rerun()

        with col3:
            if st.button("🗑️ Del  ", key=f"{context}_del_{item['id']}"):
                supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                st.rerun()

        if item.get('image_url') and item['image_url'].strip():
            st.link_button("🌐 Open Website", item['image_url'], use_container_width=True)
# --- SIDEBAR: MANAGEMENT ---
with st.sidebar:
    st.header("⚙️ Management")
    with st.expander("➕ Add New Adventure", expanded=True):
        with st.form("add_item_form", clear_on_submit=True):
            new_task = st.text_input("What is the goal?")
            all_cats = get_categories()
            selected_cat = st.selectbox("Which category?", options=all_cats if all_cats else ["None"])
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
        categories = get_categories()
        del_cat = st.selectbox("Delete a Category", options=["Select..."] + categories)
        if st.button("Delete Category 🗑️"):
            if del_cat != "Select...":
                supabase.table("categories").delete().eq("name", del_cat).execute()
                st.rerun()

# --- MAIN APP UI ---
st.title("🌟 Family Bucket List 2026")
tab_names = ["🎰 Adventure Roulette", "❤️ Favorites"] + categories
all_tabs = st.tabs(tab_names)

# --- TAB 1: ROULETTE ---
with all_tabs[0]:
    st.header("🎲 Adventure Roulette")
    st.write("Can't decide? Let the app choose your next family adventure!")

    # 1. Get fresh data
    all_items = get_items()
    # Filter for active items only (we don't want to spin for something already done!)
    roulette_pool = [i for i in all_items if not i['is_completed']]

    if roulette_pool:
        if st.button("🎰 SPIN THE WHEEL", use_container_width=True):
            import random
            import time
            
            # Simple "Loading" effect for suspense
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.01)
                progress_bar.progress(percent_complete + 1)
            
            winner = random.choice(roulette_pool)
            # Store the winner in session state so it stays on screen after the spin
            st.session_state.roulette_winner = winner
            st.balloons()

        # 2. Display the winner using our rich UI
        if 'roulette_winner' in st.session_state:
            st.success(f"### The Winner is: {st.session_state.roulette_winner['task_name']}!")
            
            # Use the function with a unique 'spin' context
            display_bucket_item(
                st.session_state.roulette_winner, 
                is_completed_view=False, 
                context="spin_tab"
            )
    else:
        st.info("Add some adventures to your categories to start spinning!")

# --- TAB 2: FAVORITES ---
with all_tabs[1]:
    st.header("❤️ Your Top Adventures")
    
    # 1. Grab the absolute latest data from the DB
    all_current_items = get_items()
    
    # 2. Filter for favorites
    fav_items = [i for i in all_current_items if i.get('is_favorite') == True]
    
    if fav_items:
        # 3. Sort them so the most recent favorites are at the top (optional)
        for fav in fav_items:
            display_bucket_item(fav, is_completed_view=fav['is_completed'], context="fav_tab")
    else:
        st.info("You haven't favorited any adventures yet. Click the ❤️ on any item to see it here!")

# --- DYNAMIC CATEGORY TABS ---
for i, cat_name in enumerate(categories):
    with all_tabs[i+2]:
        st.header(f"{cat_name}")
        category_items = [item for item in get_items() if item['category_name'] == cat_name]
        
        # ACTIVE SECTION
        active = [item for item in category_items if not item['is_completed']]
        if active:
            for item in active:
                display_bucket_item(item, is_completed_view=False, context="cat_act")
        else:
            st.info("All goals finished here! 🚀")

        st.divider()

        # COMPLETED SECTION
        with st.expander("✅ See Completed Items"):
            done = [item for item in category_items if item['is_completed']]
            if done:
                for item in done:
                    display_bucket_item(item, is_completed_view=True, context="cat_done")
            else:
                st.write("Nothing completed yet.")
