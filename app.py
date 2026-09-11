import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Magiczna Gumka Polusi", page_icon="❤️")

st.title("❤️ DLA CÓRUSI POLUSI ❤️")
st.subheader("❤️ OD TATY ❤️")

uploaded_file = st.file_uploader(
    "Wybierz zdjęcie z aparatu lub galerii", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file).convert("RGB")

    max_size = 1024
    w, h = raw_image.size
    if max(w, h) > max_size:
        scale = max_size / float(max(w, h))
        raw_image = raw_image.resize(
            (int(w * scale), int(h * scale)), Image.Resampling.LANCZOS
        )

    st.write("Zamaluj pędzlem element, który ma zniknąć:")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.5)",
        stroke_width=20,
        stroke_color="#ff0000",
        background_image=raw_image,
        update_streamlit=True,
        height=raw_image.height,
        width=raw_image.width,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("Wyczaruj zmianę ✨", type="primary"):
        img_data = None
        if canvas_result is not None:
            try:
                img_data = canvas_result.image_data
            except Exception:
                img_data = None

        if img_data is not None and np.any(img_data[:, :, 3] > 0):
            img_cv = cv2.cvtColor(np.array(raw_image), cv2.COLOR_RGB2BGR)
            mask = img_data[:, :, 3]
            _, mask_binary = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

            result_cv = cv2.inpaint(img_cv, mask_binary, 3, cv2.INPAINT_TELEA)
            result_rgb = cv2.cvtColor(result_cv, cv2.COLOR_BGR2RGB)

            st.write("### Wynik:")
            st.image(result_rgb, use_column_width=True)
        else:
            st.warning("Najpierw zamaluj element do usunięcia!")
