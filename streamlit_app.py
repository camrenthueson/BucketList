import streamlit as st
from supabase import create_client, Client
import random

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Family Bucket List", layout="wide")

# CSS for a tight button row
st.markdown("""
    <style>
    /* 1. Force the column container to never wrap */
    [data-testid="column"] {
        width: auto !important;
        flex-basis: auto !important;
        flex-grow: 0 !important;
        min-width: 0px !important;
    }

    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        gap: 10px !important;
    }

    /* 2. Shrink the buttons and checkboxes */
    div.stButton > button {
        width: 38px !important;
        height: 38px !important;
        padding: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stCheckbox {
        width: 30px !important;
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
    items = [i for i in get_items() if not i['is_completed']]
    if items:
        if st.button("🎰 SPIN!"):
            choice = random.choice(items)
            st.balloons()
            st.info(f"The winner is: **{choice['task_name']}**!")
            if choice['image_url']: st.image(choice['image_url'], use_container_width=True)
    else:
        st.write("Add some items in the sidebar first!")

# --- TAB 2: FAVORITES ---
with all_tabs[1]:
    fav_items = [i for i in get_items() if i['is_favorite']]
    for fav in fav_items:
        st.write(f"❤️ {fav['task_name']} ({fav['category_name']})")

# --- DYNAMIC CATEGORY TABS ---
for i, cat_name in enumerate(categories):
    with all_tabs[i+2]:
        st.header(f"{cat_name}")
        category_items = [item for item in get_items() if item['category_name'] == cat_name]
        active = [item for item in category_items if not item['is_completed']]

        if not active:
            st.info("No active goals here.")
        else:
            for item in active:
                with st.container(border=True):
                    st.markdown(f"**{item['task_name']}**")
                    
                    # We use 5 equal columns; the CSS above will shrink them to fit the icons
                    cols = st.columns([1, 1, 1, 1, 1])
                    
                    with cols[0]:
                        if st.checkbox("Done", key=f"active_check_{item['id']}", label_visibility="collapsed"):
                            supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                            st.rerun()
                    with cols[1]:
                        heart_label = "❤️" if item['is_favorite'] else "🤍"
                        if st.button(heart_label, key=f"fav_btn_{item['id']}"):
                            supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                            st.rerun()
                    with cols[2]:
                        if item.get('image_url') and item['image_url'].strip():
                            st.link_button("🌐", item['image_url'])
                        else:
                            st.button("➖", disabled=True, key=f"no_link_{item['id']}")
                    with cols[3]:
                        if st.button("🗑️", key=f"del_btn_{item['id']}"):
                            supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                            st.rerun()
                    # cols[4] remains empty as a small buffer
        
        st.divider()
        with st.expander("✅ Completed Items"):
            done = [item for item in category_items if item['is_completed']]
            if done:
                for item in done:
                    # Added a checkbox to allow "un-completing" an item
                    d1, d2 = st.columns([0.1, 0.9])
                    if d1.checkbox(" ", value=True, key=f"done_check_{item['id']}") == False:
                        supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                        st.rerun()
                    d2.markdown(f"~~{item['task_name']}~~")
            else:
                st.write("Nothing finished yet.")
