import io
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# 1. Konfiguracja strony
st.set_page_config(page_title="Magiczna Gumka Polusi", page_icon="❤️")

st.title("❤️ DLA CÓRUSI POLUSI ❤️")
st.subheader("❤️ OD TATY ❤️")

uploaded_file = st.file_uploader(
    "Wybierz zdjęcie z aparatu lub galerii", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file).convert("RGB")

    # Suwaki do kontroli widoku i pędzla
    col1, col2 = st.columns(2)
    with col1:
        zoom_factor = st.slider("🔍 Powiększenie", min_value=0.5, max_value=2.5, value=1.0, step=0.1)
    with col2:
        stroke_w = st.slider("🖌️ Grubość pędzla", min_value=5, max_value=100, value=20, step=5)

    # Obliczamy bazowe wymiary kadru
    base_w = int(raw_image.width * zoom_factor)
    base_h = int(raw_image.height * zoom_factor)

    # Okno podglądu dopasowane do ekranu telefonu
    view_w = min(base_w, 350)
    view_h = min(base_h, 450)

    # Suwaki przesuwania kadru
    col_x, col_y = st.columns(2)
    with col_x:
        shift_x = st.slider("⬅️➡️ Przesuń poziom", min_value=0, max_value=max(0, base_w - view_w), value=0)
    with col_y:
        shift_y = st.slider("⬆️⬇️ Przesuń pion", min_value=0, max_value=max(0, base_h - view_h), value=0)

    # Przycinamy obraz tła do wybranego kadru
    img_zoomed = raw_image.resize((base_w, base_h))
    img_cropped = img_zoomed.crop((shift_x, shift_y, shift_x + view_w, shift_y + view_h))

    # 2. Wywołanie płótna canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.5)",
        stroke_width=stroke_w,
        stroke_color="#ff0000",
        background_image=img_cropped,
        update_streamlit=True,
        height=view_h,
        width=view_w,
        drawing_mode="freedraw",
        key="canvas",
    )

    # 3. Akcja przetwarzania zdjęcia
    if st.button("Wyczaruj zmianę ✨", type="primary"):
        mask_binary = np.zeros((raw_image.height, raw_image.width), dtype=np.uint8)

        # 1. Główna metoda: Odczyt punktów rysowania (JSON)
        if canvas_result is not None and canvas_result.json_data is not None and "objects" in canvas_result.json_data:
            for obj in canvas_result.json_data["objects"]:
                if obj.get("type") == "path" and "path" in obj:
                    pts = []
                    for p in obj["path"]:
                        if p[0] in ["M", "L", "Q"] and len(p) >= 3:
                            # Uwzględniamy powiększenie oraz przesunięcie kadru
                            orig_x = int((p[1] + shift_x) / zoom_factor)
                            orig_y = int((p[2] + shift_y) / zoom_factor)
                            pts.append([orig_x, orig_y])

                    if len(pts) > 1:
                        pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                        scaled_stroke = max(5, int(stroke_w / zoom_factor))
                        cv2.polylines(
                            mask_binary,
                            [pts_arr],
                            isClosed=False,
                            color=255,
                            thickness=scaled_stroke,
                        )

        # 2. Metoda awaryjna: Bezpieczny odczyt z pikseli (Alpha Channel)
        if not np.any(mask_binary > 0) and canvas_result is not None:
            try:
                img_data = canvas_result.image_data
                if img_data is not None and np.any(img_data[:, :, 3] > 0):
                    alpha_mask = (img_data[:, :, 3] > 0).astype(np.uint8) * 255
                    
                    full_canvas_mask = np.zeros((base_h, base_w), dtype=np.uint8)
                    h_crop, w_crop = alpha_mask.shape[:2]
                    full_canvas_mask[shift_y:shift_y + h_crop, shift_x:shift_x + w_crop] = alpha_mask
                    
                    mask_binary = cv2.resize(
                        full_canvas_mask,
                        (raw_image.width, raw_image.height),
                        interpolation=cv2.INTER_NEAREST,
                    )
            except Exception:
                pass

        # Generowanie wyniku
        if np.any(mask_binary > 0):
            kernel = np.ones((5, 5), np.uint8)
            mask_binary = cv2.dilate(mask_binary, kernel, iterations=1)

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
            st.warning("Nie wykryto zamalowanego obszaru. Spróbuj zamalować element ponownie!")
