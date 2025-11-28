# import streamlit as st



# def display_preview(img, caption="", width=450):
#     """Display image at smaller width without modifying original image."""
#     st.image(img, caption=caption, width=width, use_container_width=False)

# def glass_card_start():
#     st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

# def glass_card_end():
#     st.markdown("</div>", unsafe_allow_html=True)

# def page_title(title, subtitle="", color=None, align="center", subtitle_color="#666"):
#     """Render a page title with optional subtitle.

#     Parameters:
#         title (str): Main heading text.
#         subtitle (str): Optional subtitle below the heading.
#         color (str|None): Text color for the title. If None, inherit theme default.
#         align (str): CSS text-align value (e.g. 'center', 'left').
#         subtitle_color (str): Color for subtitle text.
#     """
#     title_style = f"text-align:{align};" + (f"color:{color};" if color else "")
#     st.markdown(
#         f"<h1 style='{title_style}'>{title}</h1>",
#         unsafe_allow_html=True
#     )
#     if subtitle:
#         st.markdown(
#             f"<p style='text-align:{align};color:{subtitle_color};'>{subtitle}</p>",
#             unsafe_allow_html=True
#         )


import streamlit as st

PREVIEW_WIDTH = 450   # global width for all images

def display_preview(img, caption="", top_space=True):
    """Display image with 450px width and optional 150px top margin."""
    if top_space:
        st.markdown("<div style='height:150px;'></div>", unsafe_allow_html=True)

    st.image(
        img,
        caption=caption,
        use_container_width=False,
        width=PREVIEW_WIDTH
    )

def display_side_by_side(img_left, img_right, caption_left="", caption_right=""):
    """Side-by-side layout for input/output images."""
    col1, col2, col3 = st.columns([1, 2, 1])   # center-align the pair
    
    with col1:
        pass
    with col2:
        left_col, right_col = st.columns(2)
        with left_col:
            display_preview(img_left, caption_left, top_space=False)
        with right_col:
            display_preview(img_right, caption_right, top_space=False)
    with col3:
        pass

def page_title(title):
    st.markdown(
        f"<h1 style='text-align:center;margin-top:40px;'>{title}</h1>",
        unsafe_allow_html=True
    )
