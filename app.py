import streamlit as st
import os
import qrcode
import io
import fitz  # PyMuPDF
from datetime import datetime
import pandas as pd
from qr_scanner.qr_scanner import qr_scanner  # tu componente React

# --- Carpetas y archivos ---
QR_FOLDER = "qrs"
OUTPUT_FOLDER = "entradas"
VALID_FILE = os.path.join(QR_FOLDER, "codigos_validos.txt")
USED_FILE = os.path.join(OUTPUT_FOLDER, "usados.txt")
REGISTRO_FILE = os.path.join(OUTPUT_FOLDER, "registro_escaneos.csv")

os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Logs ---
if "logs" not in st.session_state:
    st.session_state["logs"] = []

def log(msg):
    timestamp = datetime.now().isoformat()
    entry = f"{timestamp} - {msg}"
    st.session_state["logs"].append(entry)
    print(entry)


# --- Función para generar PDF tipo ticket ---
def generar_pdf_ticket(codigo, nombre, qr_path=None, template_path="template/template_ticket.pdf"):
    log(f"Iniciando generación de PDF para {codigo} - {nombre}")
    doc = fitz.open(template_path)
    page = doc[0]

    if qr_path is None or not os.path.exists(qr_path):
        qr_img = qrcode.make(codigo)
        qr_temp = "temp_qr.png"
        qr_img.save(qr_temp)
        qr_path = qr_temp
        log(f"QR temporal generado: {qr_temp}")

    page_width, page_height = page.rect.width, page.rect.height

    qr_size = 180
    qr_margin_x = 60
    qr_margin_y = 130
    qr_rect = fitz.Rect(qr_margin_x, page_height - qr_margin_y - qr_size,
                        qr_margin_x + qr_size, page_height - qr_margin_y)
    page.add_redact_annot(qr_rect, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_image(qr_rect, filename=qr_path)

    new_text = f"#{codigo}"
    text_margin_x = 250
    text_margin_y = 130
    page.insert_text((page_width - text_margin_x, page_height - text_margin_y),
                     new_text, fontsize=17, color=(1, 1, 1), fontname="helv")

    output_path = os.path.join(OUTPUT_FOLDER, f"{codigo}.pdf")
    doc.save(output_path)
    doc.close()

    if qr_path == "temp_qr.png":
        os.remove(qr_path)
        log("QR temporal eliminado")

    log(f"PDF generado: {output_path}")
    return output_path

# --- Cargar códigos válidos ---
validos = {}
if os.path.exists(VALID_FILE):
    with open(VALID_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                if "|" in line:
                    code, name = line.split("|", 1)
                else:
                    code, name = line, ""
                validos[code] = {"name": name, "used": False}
log(f"Códigos válidos cargados: {list(validos.keys())}")

# --- Cargar códigos usados ---
if os.path.exists(USED_FILE):
    with open(USED_FILE) as f:
        for line in f:
            code = line.strip()
            if code in validos:
                validos[code]["used"] = True
log("Códigos usados cargados")

# --- Inicializar session_state ---
if "ultimo_qr" not in st.session_state:
    st.session_state["ultimo_qr"] = None
if "qr_active" not in st.session_state:
    st.session_state["qr_active"] = True
if "qr_processed" not in st.session_state:
    st.session_state["qr_processed"] = False
if "qr_message" not in st.session_state:
    st.session_state["qr_message"] = None

if "qr_message_type" not in st.session_state:
    st.session_state["qr_message_type"] = None  # "success" | "error"


# # --- Generar QR ---
# st.subheader("Generar QR para un invitado")


# with st.form("generar_qr"):
#     nombre = st.text_input("Nombre del invitado")
#     identificador = st.text_input("Número identificativo / ID")
#     submit_gen = st.form_submit_button("Generar QR")

#     if submit_gen:
#         log("Formulario de generación enviado")
#         if not nombre or not identificador:
#             st.error("Debes ingresar nombre y número identificativo")
#             log("Error: Falta nombre o ID")
#         else:
#             code = f"{identificador}-{nombre.replace(' ','')}"
#             qr_path = os.path.join(QR_FOLDER, f"{code}.png")
#             log(f"Generando QR: {code}")

#             if code in validos:
#                 st.warning(f"⚠️ Este código ya existe: {code}")
#                 log(f"Advertencia: Código ya existe")
#             else:
#                 qr = qrcode.QRCode(box_size=10, border=2)
#                 qr.add_data(code)
#                 qr.make(fit=True)
#                 img = qr.make_image(fill_color="black", back_color="white")
#                 img.save(qr_path)
#                 log(f"QR guardado en {qr_path}")

#                 with open(VALID_FILE, "a") as f:
#                     f.write(f"{code}|{nombre}\n")

#                 validos[code] = {"name": nombre, "used": False}
#                 st.success(f"✅ QR generado: {code}")
#                 buf = io.BytesIO()
#                 img.save(buf, format="PNG")
#                 buf.seek(0)
#                 st.image(buf, caption=f"QR de {nombre}", width=200)
#                 log(f"QR generado y mostrado en UI")

#                 pdf_path = generar_pdf_ticket(code, nombre, qr_path=qr_path)
#                 st.success(f"🎟️ PDF tipo ticket generado: {pdf_path}")
#                 st.markdown(f"[Descargar PDF]({pdf_path})")


st.title("🎫 Gestor de Entradas QR")

if st.session_state["qr_message"]:
    if st.session_state["qr_message_type"] == "success":
        st.success(st.session_state["qr_message"])
    else:
        st.error(st.session_state["qr_message"])

# --- Escaneo QR ---
if st.session_state["qr_active"]:
    try:
        # log("ANTES de llamar a qr_scanner()")
        qr_code = qr_scanner(key="qr1")
        # log(f"DESPUÉS de llamar a qr_scanner() → valor={qr_code}")
    except Exception as e:
        log(f"ERROR llamando qr_scanner(): {e}")
        qr_code = None

    if qr_code:
        log(f"QR recibido desde componente: {qr_code}")
        st.session_state["ultimo_qr"] = qr_code
        st.session_state["qr_active"] = False
    else:
        log("QR vacío (None o '')")

log(f"Mensaje {st.session_state['qr_message']}")
# --- Procesar QR ---
if st.session_state["ultimo_qr"] and not st.session_state["qr_processed"] and st.session_state["qr_message"] == None:
    codigo = st.session_state["ultimo_qr"].strip()
    log(f"Procesando QR: {codigo}")

    st.session_state["qr_processed"] = True
    st.session_state["qr_active"] = False  # 🔒 apagar cámara

    if codigo in validos:
        nombre = validos[codigo]["name"]
        if validos[codigo]["used"]:
            st.session_state["qr_message"] = f"Código ya usado: {codigo} - {nombre}"
            st.session_state["qr_message_type"] = "error"
            log(f"Código ya usado: {codigo}")
        else:
            st.session_state["qr_message"] = f"Código válido: {codigo} - {nombre}"
            st.session_state["qr_message_type"] = "success"

            validos[codigo]["used"] = True
            with open(USED_FILE, "a") as f:
                f.write(f"{codigo}\n")
            with open(REGISTRO_FILE, "a") as f:
                f.write(f"{datetime.now().isoformat()},{codigo},{nombre}\n")

            log(f"Código marcado como usado y registrado: {codigo}")
    else:
        st.session_state["qr_message"] = f"Código inválido: {codigo}"
        st.session_state["qr_message_type"] = "error"
        log(f"Código inválido: {codigo}")

# --- Botón para escanear otro QR ---
if st.button("🔄 Escanear otro QR"):
    st.session_state["ultimo_qr"] = None
    st.session_state["qr_active"] = True
    st.session_state["qr_processed"] = False  # 🔓 permitir nuevo QR
    st.session_state["qr_message"] = None
    log("Reiniciando escaneo para otro QR")
    st.rerun()


# --- Mostrar logs ---
# st.subheader("📝 Logs en tiempo real")
# for entry in reversed(st.session_state["logs"][-10:]):
#     st.text(entry)

# --- Últimos escaneos ---
st.subheader("Últimos escaneos")
if os.path.exists(REGISTRO_FILE):
    try:
        df = pd.read_csv(REGISTRO_FILE, header=None, names=["fecha", "codigo", "nombre"])
        st.dataframe(df.sort_values("fecha", ascending=False).head(20))
    except Exception:
        st.write("No hay registros legibles todavía.")
else:
    st.write("Aún no hay escaneos registrados.")
