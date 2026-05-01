import streamlit as st
from supabase import create_client, Client
import random

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Family Bucket List", layout="wide")

# Force columns to stay horizontal on mobile
st.markdown("""
    <style>
    /* Create a tight row for buttons */
    .button-row {
        display: flex;
        flex-direction: row;
        justify-content: flex-start;
        gap: 10px; /* Adjust this to make buttons closer or further apart */
        align-items: center;
        margin-top: 10px;
    }
    
    /* Small fix to make sure Streamlit buttons don't have extra margin */
    div.stButton > button {
        width: auto !important;
        padding: 0px 10px !important;
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

# --- SIDEBAR: MANAGEMENT ---
with st.sidebar:
    st.header("⚙️ Management")
    
    # Section 1: Add New Item
    with st.expander("➕ Add New Adventure", expanded=True):
        with st.form("add_item_form", clear_on_submit=True):
            new_task = st.text_input("What is the goal?")
            all_cats = get_categories()
            selected_cat = st.selectbox("Which category?", options=all_cats if all_cats else ["None"])
            img_url = st.text_input("Image URL (optional)")

            if st.form_submit_button("Add to List"):
                if new_task and selected_cat != "None":
                    supabase.table("bucket_items").insert({
                        "task_name": new_task,
                        "category_name": selected_cat,
                        "image_url": img_url
                    }).execute()
                    st.rerun()

    # Section 2: Manage Categories
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

# Updated Tabs: Dashboard is now focused on the Roulette
tab_names = ["🎰 Adventure Roulette", "❤️ Favorites"] + categories
all_tabs = st.tabs(tab_names)

# --- TAB 1: ROULETTE ---
with all_tabs[0]:
    st.header("Spin for Adventure!")
    items = [i for i in get_items() if not i['is_completed']]
    if items:
        if st.button("🎰 SPIN!"):
            choice = random.choice(items)
            st.balloons()
            st.info(f"The winner is: **{choice['task_name']}**!")
            if choice['image_url'] and choice['image_url'].strip():
                st.image(choice['image_url'], use_container_width=True)
            st.button("Spin Again")
    else:
        st.write("Add some items in the sidebar first!")

# --- TAB 2: FAVORITES ---
with all_tabs[1]:
    st.header("Our Favorites")
    fav_items = [i for i in get_items() if i['is_favorite']]
    for fav in fav_items:
        st.write(f"❤️ {fav['task_name']} ({fav['category_name']})")

# --- DYNAMIC CATEGORY TABS ---
for i, cat_name in enumerate(categories):
    with all_tabs[i+2]:
        st.header(f"{cat_name} Goals")
        category_items = [item for item in get_items() if item['category_name'] == cat_name]
        active = [item for item in category_items if not item['is_completed']]

        if not active:
            st.info("No active goals here.")
        else:
            for item in active:
                with st.container(border=True):
                    st.markdown(f"### {item['task_name']}")
                    
                    # We create a container that "holds" our buttons horizontally
                    # Using a single row of columns with very small widths works better with the CSS
                    c1, c2, c3, c4, spacer = st.columns([0.1, 0.1, 0.1, 0.1, 0.6])
                    
                    with c1:
                        if st.checkbox("Done", key=f"active_check_{item['id']}", label_visibility="collapsed"):
                            supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                            st.rerun()
                    with c2:
                        heart_label = "❤️" if item['is_favorite'] else "🤍"
                        if st.button(heart_label, key=f"fav_btn_{item['id']}"):
                            supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                            st.rerun()
                    with c3:
                        if item.get('image_url') and item['image_url'].strip():
                            st.link_button("🌐", item['image_url'])
                    with c4:
                        if st.button("🗑️", key=f"del_btn_{item['id']}"):
                            supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                            st.rerun()
        st.divider()

        with st.expander("✅ See Completed Items"):
            done = [item for item in category_items if item['is_completed']]
            if done:
                for item in done:
                    d1, d2 = st.columns([0.1, 0.9])
                    if d1.checkbox(" ", value=True, key=f"done_check_{item['id']}") == False:
                        supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                        st.rerun()
                    d2.markdown(f"~~{item['task_name']}~~")
