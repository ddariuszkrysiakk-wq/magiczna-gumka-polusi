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

    stroke_w = 20
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.5)",
        stroke_width=stroke_w,
        stroke_color="#ff0000",
        background_image=raw_image,
        update_streamlit=True,
        height=raw_image.height,
        width=raw_image.width,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("Wyczaruj zmianę ✨", type="primary"):
        mask_binary = None

        # 1. Sprawdzanie danych JSON
        if (
            canvas_result.json_data is not None
            and "objects" in canvas_result.json_data
            and len(canvas_result.json_data["objects"]) > 0
        ):
            mask_binary = np.zeros((raw_image.height, raw_image.width), dtype=np.uint8)
            for obj in canvas_result.json_data["objects"]:
                if "path" in obj:
                    pts = []
                    for p in obj["path"]:
                        if p[0] in ["M", "L", "Q"] and len(p) >= 3:
                            pts.append([int(p[1]), int(p[2])])
                    if len(pts) > 1:
                        pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(
                            mask_binary,
                            [pts_arr],
                            isClosed=False,
                            color=255,
                            thickness=stroke_w,
                        )

        # 2. Rezerwa: próba z image_data
        if mask_binary is None or not np.any(mask_binary > 0):
            try:
                img_data = canvas_result.image_data
                if img_data is not None and np.any(img_data[:, :, 3] > 0):
                    mask = img_data[:, :, 3]
                    _, mask_binary = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
            except Exception:
                pass

        # Wyświetlanie wyniku
        if mask_binary is not None and np.any(mask_binary > 0):
            img_cv = cv2.cvtColor(np.array(raw_image), cv2.COLOR_RGB2BGR)
            result_cv = cv2.inpaint(img_cv, mask_binary, 3, cv2.INPAINT_TELEA)
            result_rgb = cv2.cvtColor(result_cv, cv2.COLOR_BGR2RGB)

            st.write("### Wynik:")
            st.image(result_rgb, use_container_width=True)
        else:
            st.warning("Najpierw zamaluj element do usunięcia!")
