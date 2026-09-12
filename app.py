import io
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

    # 1. Suwaki do kontroli widoku i pędzla
col1, col2 = st.columns(2)
with col1:
        # Domyślnie zmniejszamy widok (0.5), aby zdjęcie zmieściło się na telefonie
        zoom_factor = st.slider("🔍 Powiększenie / Rozmiar zdjęcia", min_value=0.2, max_value=2.0, value=0.8, step=0.05)
with col2:
        stroke_w = st.slider("🖌️ Grubość pędzla", min_value=5, max_value=100, value=20, step=5)

    # Obliczamy wymiary wyświetlania na płótnie
canvas_w = int(raw_image.width * zoom_factor)
canvas_h = int(raw_image.height * zoom_factor)

st.write("Zamaluj pędzlem element, który ma zniknąć(przesuwaj ramkę palcem, by się przemieścić):")

    # 2. Rysowanie płótna canvas
   
st.markdown("<div style='width: 100%; max-height: 60vh; overflow: scroll !important; border: 2px solid #ff4b4b; border-radius: 8px; -webkit-overflow-scrolling: touch;'>" ,unsafe_allow_html=True)

drawing_mode = st.radio(
    "Wybierz tryb:",
    ("freedraw", "transform"),
    format_func=lambda x: "✏️ Malowanie" if x == "freedraw" else "🔍 Przesuwanie/Powiększanie",
    horizontal=True
    )
canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.5)",
        stroke_width=stroke_w, 
        stroke_color="#ff0000",
        background_image=raw_image,
        update_streamlit=True,
        height=canvas_h,
        width=canvas_w,
        drawing_mode="freedraw",
        key="canvas",
    )
st.markdown("</div>" , unsafe_allow_html=True)

if st.button("Wyczaruj zmianę ✨", type="primary"):
        mask_binary = np.zeros((raw_image.height, raw_image.width), dtype=np.uint8)

        # Sprawdzanie danych JSON i przeliczanie punktów ze skali canvas na pełne zdjęcie
        if (
            canvas_result.json_data is not None
            and "objects" in canvas_result.json_data
            and len(canvas_result.json_data["objects"]) > 0
        ):
            for obj in canvas_result.json_data["objects"]:
                if "path" in obj:
                    pts = []
                    for p in obj["path"]:
                        if p[0] in ["M", "L", "Q"] and len(p) >= 3:
                            # Przeliczamy współrzędne do oryginalnego rozmiaru zdjęcia
                            orig_x = int(p[1] / zoom_factor)
                            orig_y = int(p[2] / zoom_factor)
                            pts.append([orig_x, orig_y])
                    if len(pts) > 1:
                        pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(
                            mask_binary,
                            [pts_arr],
                            isClosed=False,
                            color=255,
                            thickness=stroke_w,
                        )

        # Rezerwa z image_data (przeskalowanie do oryginalnej rozdzielczości)
        if not np.any(mask_binary > 0):
            try:
                img_data = canvas_result.image_data
                if img_data is not None and np.any(img_data[:, :, 3] > 0):
                    mask = img_data[:, :, 3]
                    _, mask_resized = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
                    mask_binary = cv2.resize(
                        mask_resized, 
                        (raw_image.width, raw_image.height), 
                        interpolation=cv2.INTER_NEAREST
                    )
            except Exception:
                pass

        # Wynik i pobieranie
        if np.any(mask_binary > 0):
            img_cv = cv2.cvtColor(np.array(raw_image), cv2.COLOR_RGB2BGR)
            result_cv = cv2.inpaint(img_cv, mask_binary, 3, cv2.INPAINT_TELEA)
            result_rgb = cv2.cvtColor(result_cv, cv2.COLOR_BGR2RGB)

            st.write("### Wynik:")
            st.image(result_rgb, use_container_width=True)

            result_pil = Image.fromarray(result_rgb)
            buf = io.BytesIO()
            result_pil.save(buf, format="PNG")
            byte_im = buf.getvalue()

            st.download_button(
                label="📥 Pobierz wyczarowane zdjęcie",
                data=byte_im,
                file_name="magiczne_zdjecie_polusi.png",
                mime="image/png",
            )
        else:
            st.warning("Najpierw zamaluj element do usunięcia!")
