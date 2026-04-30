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
    # i+2 because Dashboard and Favorites are 0 and 1
    with all_tabs[i+2]:
        st.header(f"{cat_name} Goals")
        
        # Pull fresh data for this specific category
        category_items = [item for item in get_items() if item['category_name'] == cat_name]
        active = [item for item in category_items if not item['is_completed']]

        if not active:
            st.info("No active goals here. Add one in the sidebar!")
        else:
            # HEADER ROW
            # We add a container to keep things grouped
            with st.container():
                h1, h2, h3, h4, h5 = st.columns([0.1, 0.5, 0.1, 0.15, 0.1])
                h1.caption("DONE")
                h2.caption("ADVENTURE")
                h3.caption("FAV")
                h4.caption("LINK")
                h5.caption("DEL")
                st.divider()

            # DATA ROWS
            for item in active:
                # A container with a border makes each "Card" distinct
                with st.container(border=True):
                    # 1. Title on its own line
                    st.markdown(f"### {item['task_name']}")
                    
                    # 2. Options Row (Small buttons, no stretching)
                    # We create 6 columns. The last one [0.4] acts as a "spacer" 
                    # to push the buttons to the left so they don't stretch on mobile.
                    btn_c1, btn_c2, btn_c3, btn_c4, btn_c5, spacer = st.columns([0.15, 0.15, 0.15, 0.15, 0.1, 0.4])
                    
                    with btn_c1: # Done
                        # collapsed label visibility keeps the checkbox tiny
                        if st.checkbox("Done", key=f"active_check_{item['id']}", label_visibility="visible"):
                            supabase.table("bucket_items").update({"is_completed": True}).eq("id", item['id']).execute()
                            st.rerun()
                    
                    with btn_c2: # Favorite
                        heart_label = "❤️" if item['is_favorite'] else "🤍"
                        if st.button(heart_label, key=f"fav_btn_{item['id']}"):
                            supabase.table("bucket_items").update({"is_favorite": not item['is_favorite']}).eq("id", item['id']).execute()
                            st.rerun()
                    
                    with btn_c3: # Link
                        if item.get('image_url'):
                            # use_container_width=False is the key to preventing full-width buttons
                            st.link_button("🌐", item['image_url'], use_container_width=False, help="Open Link")
                    
                    with btn_c4: # Delete
                        if st.button("🗑️", key=f"del_btn_{item['id']}"):
                            supabase.table("bucket_items").delete().eq("id", item['id']).execute()
                            st.rerun()
                
        # spacer column is left empty to "squeeze" the others to the left

        st.write("---") # Visual break before expander

        # --- COMPLETED ITEMS EXPANDER ---
        with st.expander("✅ See Completed Items"):
            done = [item for item in category_items if item['is_completed']]
            if done:
                for item in done:
                    d1, d2 = st.columns([0.1, 0.9])
                    # Unique key including 'done' prefix
                    is_unchecking = d1.checkbox(" ", value=True, key=f"done_check_{item['id']}")
                    if not is_unchecking:
                        supabase.table("bucket_items").update({"is_completed": False}).eq("id", item['id']).execute()
                        st.rerun()
                    d2.write(f"~~{item['task_name']}~~")
            else:
                st.write("Nothing finished yet.")
