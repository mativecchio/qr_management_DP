import os
from pathlib import Path
import streamlit.components.v1 as components
import sys

_RELEASE = True

if _RELEASE:
    build_path = str(Path(__file__).parent / "frontend/dist/qr_scanner_component")
    qr_scanner_component = components.declare_component("qr_scanner", path=build_path)

else:
    qr_scanner_component = components.declare_component(
        "qr_scanner", url="http://localhost:5173"
    )

def qr_scanner(key=None):
    print(f">>> qr_scanner() llamado con key={key}", file=sys.stderr)
    value = qr_scanner_component(key=key)
    print(f">>> qr_scanner() devolvió {value!r}", file=sys.stderr)
    return value