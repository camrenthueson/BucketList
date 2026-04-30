import streamlit as st
from supabase import create_client, Client
import random

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


# --- SIDEBAR: ADDING NEW ITEMS ---
st.sidebar.header("➕ Add New Adventure")
with st.sidebar.form("add_item_form", clear_on_submit=True):
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

# --- MAIN APP UI ---
st.title("🌟 Family Bucket List 2026")

# Create the Tabs
categories = get_categories()
tab_names = ["🏠 Dashboard", "❤️ Favorites"] + categories
all_tabs = st.tabs(tab_names)

# --- TAB 1: DASHBOARD ---
with all_tabs[0]:
    st.header("App Management")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Manage Categories")
        new_cat_name = st.text_input("New Category Name")
        if st.button("Create Category"):
            if new_cat_name:
                supabase.table("categories").insert({"name": new_cat_name}).execute()
                st.rerun()

        del_cat = st.selectbox("Delete a Category", options=["Select..."] + categories)
        if st.button("Delete Category 🗑️"):
            if del_cat != "Select...":
                supabase.table("categories").delete().eq("name", del_cat).execute()
                st.rerun()

    with col2:
        st.subheader("Adventure Roulette")
        items = [i for i in get_items() if not i['is_completed']]
        if items:
            if st.button("🎰 Spin for Adventure!"):
                choice = random.choice(items)
                st.info(f"The winner is: **{choice['task_name']}**!")
                if choice['image_url']:
                    st.image(choice['image_url'], width=300)
                st.button("Spin Again")
        else:
            st.write("Add some items first!")

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
        
        # Fetch items for this category
        category_items = [item for item in get_items() if item['category_name'] == cat_name]
        active = [item for item in category_items if not item['is_completed']]

        if not active:
            st.info("No active goals here. Add one in the sidebar!")
        else:
            # Table Header
            h1, h2, h3, h4, h5 = st.columns([0.1, 0.5, 0.1, 0.15, 0.1])
            h1.write("**Done**")
            h2.write("**Adventure**")
            h3.write("**Fav**")
            h4.write("**Link**")
            h5.write("**Del**")
            st.divider()

            # Table Rows
            for item in active:
                c1, c2, c3, c4, c5 = st.columns([0.1, 0.5, 0.1, 0.15, 0.1])
                
                # 1. Complete Checkbox
                if c1.checkbox(" ", key=f"check_{item['id']}"):
                    supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                    st.rerun()
                
                # 2. Task Name
                c2.write(item['task_name'])
                
                # 3. Favorite Heart
                heart_label = "❤️" if item['is_favorite'] else "🤍"
                if c3.button(heart_label, key=f"fav_{item['id']}"):
                    supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                    st.rerun()
                
                # 4. URL Button
                if item['image_url']:
                    # This creates a clickable link that looks like a button
                    c4.link_button("🌐 Open", item['image_url'], use_container_width=True)
                else:
                    c4.write("---")

                # 5. Delete Button
                if c5.button("🗑️", key=f"del_{item['id']}"):
                    supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                    st.rerun()

        # --- COMPLETED ITEMS EXPANDER ---
        with st.expander("✅ See Completed Items"):
            done = [item for item in category_items if item['is_completed']]
            if done:
                for item in done:
                    # Using a simple line for completed items to keep it compact
                    d1, d2 = st.columns([0.1, 0.9])
                    if d1.checkbox(" ", value=True, key=f"done_{item['id']}") == False:
                        supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                        st.rerun()
                    d2.write(f"~~{item['task_name']}~~")
            else:
                st.write("Nothing finished yet. Get out there!")
