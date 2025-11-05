import streamlit as st
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from PIL import Image
import cv2
import traceback
import qrcode
import os
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import landscape, A6
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import io
import numpy as np
import time
import fitz  # PyMuPDF

# --- Carpetas y archivos ---
QR_FOLDER = "qrs"
VALID_FILE = os.path.join(QR_FOLDER, "codigos_validos.txt")
OUTPUT_FOLDER = "entradas"
USED_FILE = os.path.join(OUTPUT_FOLDER, "usados.txt")
REGISTRO_FILE = os.path.join(OUTPUT_FOLDER, "registro_escaneos.csv")
LOG_FILE = os.path.join(OUTPUT_FOLDER, "log_app.txt")

os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Log ---
def log(msg):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {msg}\n")
    print(f"{timestamp} - {msg}")

# --- Función para generar PDF tipo ticket ---
def generar_pdf_ticket(codigo, nombre, qr_path=None, template_path="template/template_ticket.pdf"):
    """
    Genera un ticket a partir del template PDF existente,
    reemplazando el QR de la esquina inferior izquierda
    y el código impreso en la esquina inferior derecha.
    """
    doc = fitz.open(template_path)
    page = doc[0]

    # --- Generar QR (si no se pasó uno existente) ---
    if qr_path is None or not os.path.exists(qr_path):
        qr_img = qrcode.make(codigo)
        qr_temp = "temp_qr.png"
        qr_img.save(qr_temp)
        qr_path = qr_temp

    page_width = page.rect.width
    page_height = page.rect.height

    # --- Reemplazar QR (inferior izquierda) ---
    qr_size = 180
    qr_margin_x = 60
    qr_margin_y = 130
    qr_rect = fitz.Rect(
        qr_margin_x,
        page_height - qr_margin_y - qr_size,
        qr_margin_x + qr_size,
        page_height - qr_margin_y
    )
    page.add_redact_annot(qr_rect, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_image(qr_rect, filename=qr_path)

    # --- Reemplazar código (inferior derecha) ---
    new_text = f"#{codigo}"
    text_margin_x = 250
    text_margin_y = 130
    page.insert_text(
        (page_width - text_margin_x, page_height - text_margin_y),
        new_text,
        fontsize=17,
        color=(1, 1, 1),
        fontname="helv"
    )

    # --- Guardar PDF final ---
    output_path = os.path.join("entradas", f"{codigo}.pdf")
    doc.save(output_path)
    doc.close()

    if qr_path == "temp_qr.png":
        os.remove(qr_path)

    return output_path

def reemplazar_qr_y_codigo_en_template(template_path, output_path, codigo):
    doc = fitz.open(template_path)
    page = doc[0]

    # --- Generar nuevo QR ---
    qr_img = qrcode.make(codigo)
    qr_temp = "temp_qr.png"
    qr_img.save(qr_temp)

    page_width = page.rect.width
    page_height = page.rect.height

    # --- 1️⃣ Reemplazar QR (esquina inferior izquierda) ---
    qr_size = 120  # ajustable si cambia el tamaño del QR
    qr_margin_x = 50
    qr_margin_y = 70  # margen inferior
    qr_rect = fitz.Rect(
        qr_margin_x,
        page_height - qr_margin_y - qr_size,
        qr_margin_x + qr_size,
        page_height - qr_margin_y
    )
    # cubrir el QR viejo con fondo
    page.add_redact_annot(qr_rect, fill=(1, 1, 1))
    page.apply_redactions()
    # insertar nuevo QR
    page.insert_image(qr_rect, filename=qr_temp)

    # --- 2️⃣ Reemplazar código (esquina inferior derecha) ---
    code_fontsize = 18
    text_margin_x = 80
    text_margin_y = 45  # distancia desde el borde inferior
    new_text = f"#{codigo}"
    text_x = page_width - text_margin_x - 200  # ajustable según alineación
    text_y = page_height - text_margin_y
    page.insert_text(
        (text_x, text_y),
        new_text,
        fontsize=code_fontsize,
        color=(1, 1, 1),
        fontname="helv"
    )

    # --- Guardar nuevo PDF ---
    doc.save(output_path)
    doc.close()
    os.remove(qr_temp)

    print(f"✅ Ticket actualizado: {output_path}")
    
# --- Cargar códigos válidos ---
if not os.path.exists(VALID_FILE):
    with open(VALID_FILE, "w") as f:
        pass

validos = {}
with open(VALID_FILE) as f:
    for line in f:
        line = line.strip()
        if line:
            if "|" in line:
                code, name = line.split("|", 1)
            else:
                code, name = line, ""
            validos[code] = {"name": name, "used": False}

# --- Cargar usados ---
if os.path.exists(USED_FILE):
    with open(USED_FILE) as f:
        for line in f:
            code = line.strip()
            if code in validos:
                validos[code]["used"] = True

# --- App UI ---
st.set_page_config(page_title="Gestor de Entradas QR", layout="centered")
st.title("🎫 Gestor de Entradas QR")

# --- Panel de Generación de QR ---
st.subheader("Generar QR para un invitado")
with st.form("generar_qr"):
    nombre = st.text_input("Nombre del invitado")
    identificador = st.text_input("Número identificativo / ID")
    submit_gen = st.form_submit_button("Generar QR")
    
    if submit_gen:
        if not nombre or not identificador:
            st.error("Debes ingresar nombre y número identificativo")
        else:
            code = f"{identificador}-{nombre.replace(' ','')}"
            qr_path = os.path.join(QR_FOLDER, f"{code}.png")
            
            if code in validos:
                st.warning(f"⚠️ Este código ya existe: {code}")
            else:
                qr = qrcode.QRCode(box_size=10, border=2)
                qr.add_data(code)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(qr_path)
                
                with open(VALID_FILE, "a") as f:
                    f.write(f"{code}|{nombre}\n")
                
                validos[code] = {"name": nombre, "used": False}
                st.success(f"✅ QR generado: {code}")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                st.image(buf, caption=f"QR de {nombre}", width=200)
                log(f"QR generado para {nombre} ({code})")

                pdf_path = generar_pdf_ticket(code, nombre, qr_path="qrs/" + f"{code}.png")
                st.success(f"🎟️ PDF tipo ticket generado: {pdf_path}")
                st.markdown(f"[Descargar PDF]({pdf_path})")

# --- Panel de Escaneo en tiempo real ---
# --- Panel de Escaneo en tiempo real ---
st.subheader("📷 Escanear QR en tiempo real (modo estable)")

from streamlit_webrtc import RTCConfiguration

# Configuración de STUN para conexión estable

rtc_config = RTCConfiguration({
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {
            "urls": [
                "turn:relay1.expressturn.com:3478",
                "turns:relay1.expressturn.com:5349"
            ],
            "username": "ef408b22e0",
            "credential": "oFOPc8ik2xkBdg4x"
        }
    ]
})



detector = cv2.QRCodeDetector()

# Estado inicial
if "ultimo_qr" not in st.session_state:
    st.session_state["ultimo_qr"] = None

webrtc_ctx = webrtc_streamer(
    key="scanner_estable",
    rtc_configuration=rtc_config,
    async_processing=True,
    media_stream_constraints={
        "video": {"width": {"ideal": 320}, "height": {"ideal": 240}},
        "audio": False
    },
)

# --- Mostrar estado detallado del componente ---
log(f"🎛 State={webrtc_ctx.state}")
time.sleep(2)
log(f"📡 Receiver={hasattr(webrtc_ctx, 'video_receiver')}, Value={webrtc_ctx.video_receiver}")


# ✅ Log más claro (solo muestra si la cámara está activa o no)
if webrtc_ctx.state.playing:
    log("📹 Cámara activa y reproduciendo correctamente")
else:
    log("🛑 Cámara detenida o inicializando")

# --- Interfaz de cámara ---
if webrtc_ctx.state.playing:
    st.info("📸 Cámara activa. Apunta el QR y presiona el botón para capturarlo.")
    time.sleep(0.8)  # Pequeña espera para asegurar que el receptor esté listo

    # 🔄 Solo mostrar el botón si el receptor de video está activo
    if hasattr(webrtc_ctx, "video_receiver") and webrtc_ctx.video_receiver:
        if st.button("📸 Capturar QR ahora"):
            try:
                frame = webrtc_ctx.video_receiver.last_frame
                if frame is None:
                    st.error("❌ No se pudo capturar el frame desde la cámara.")
                else:
                    pil_img = frame.to_image()
                    np_img = np.array(pil_img.convert("RGB"))
                    np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)

                    # Intentar decodificar QR
                    data, _, _ = detector.detectAndDecode(np_img)
                    if data:
                        codigo = data.strip()
                        st.session_state["ultimo_qr"] = codigo
                        log(f"✅ QR detectado: {codigo}")

                        # Validar código
                        if codigo in validos:
                            nombre = validos[codigo]["name"]
                            if validos[codigo]["used"]:
                                st.warning(f"⚠️ Código ya usado: {codigo} - {nombre}")
                                log(f"QR usado detectado: {codigo} - {nombre}")
                            else:
                                st.success(f"✅ Código válido: {codigo} - {nombre}")
                                validos[codigo]["used"] = True

                                with open(USED_FILE, "a") as f:
                                    f.write(f"{codigo}\n")
                                with open(REGISTRO_FILE, "a") as f:
                                    f.write(f"{datetime.now().isoformat()},{codigo},{nombre}\n")

                                log(f"QR válido usado: {codigo} - {nombre}")
                        else:
                            st.error(f"❌ Código inválido: {codigo}")
                            log(f"Código inválido detectado: {codigo}")
                    else:
                        st.warning("⚠️ No se detectó ningún QR. Intentá enfocar mejor.")
            except Exception as e:
                st.error(f"Error procesando el frame: {e}")
                log(f"Error procesando frame: {repr(e)}")
    else:
        st.info("⏳ Inicializando cámara... Espera unos segundos.")
else:
    st.warning("🎥 Esperando que actives la cámara (botón ▶️ arriba).")

# --- Mostrar último QR detectado ---
if st.session_state["ultimo_qr"]:
    st.markdown(f"**Último código detectado:** `{st.session_state['ultimo_qr']}`")

# --- Panel de subida de foto ---
st.subheader("O subir foto del QR")
uploaded_file = st.file_uploader("Sube imagen del QR", type=["png","jpg","jpeg"])
if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img, _, mensaje = procesar_qr_img(img)
    if mensaje.startswith("✅"):
        st.success(mensaje)
    elif mensaje.startswith("⚠️"):
        st.warning(mensaje)
    else:
        st.error(mensaje)
    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

# --- Panel de últimos escaneos ---
st.subheader("Últimos escaneos")
if os.path.exists(REGISTRO_FILE):
    try:
        df = pd.read_csv(REGISTRO_FILE, header=None, names=["fecha","codigo","nombre"])
        st.dataframe(df.sort_values("fecha", ascending=False).head(20))
    except Exception:
        st.write("No hay registros legibles todavía.")
else:
    st.write("Aún no hay escaneos registrados.")
