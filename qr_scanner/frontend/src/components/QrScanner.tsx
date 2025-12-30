import { useEffect, useState } from "react";
import { Streamlit } from "streamlit-component-lib";

const MIN_HEIGHT = 380;

const QrScanner: React.FC = () => {
  const [height, setHeight] = useState<string>('300');
  useEffect(() => {
    console.log("[QR] useEffect iniciado");

    Streamlit.setComponentReady();
    Streamlit.setFrameHeight(500);
    console.log("[QR] componentReady + frameHeight inicial");

    const start = () => {
      const reader = document.getElementById("reader");

      if (!reader) {
        console.warn("[QR] reader no existe, reintentando...");
        setTimeout(start, 300);
        return;
      }

      const rect = reader.getBoundingClientRect();
      console.log("[QR] reader size:", rect.width, rect.height);

      if (rect.width === 0 || rect.height === 0) {
        console.warn("[QR] reader sin tamaño, reintentando...");
        setTimeout(start, 300);
        return;
      }

      Streamlit.setFrameHeight(rect.height + 200);
      setHeight(Math.max(rect.height, MIN_HEIGHT).toString());
      console.log("[QR] creando script html5-qrcode");

      const script = document.createElement("script");
      script.src = "https://unpkg.com/html5-qrcode";
      script.async = true;

      script.onload = () => {
        console.log("[QR] html5-qrcode cargado");

        // @ts-ignore
        Html5Qrcode.getCameras()
          .then((devices: any[]) => {
            console.log("[QR] Cámaras:", devices);

            if (!devices || devices.length === 0) {
              console.error("[QR] No hay cámaras");
              return;
            }

            const backCamera =
              devices.find(d =>
                d.label?.toLowerCase().includes("back") ||
                d.label?.toLowerCase().includes("rear")
              ) ||
              devices[1] ||
              devices[0];

            const qrBoxSize = Math.min(rect.width, rect.height) - 40;
            console.log("[QR] cámara seleccionada:", backCamera);

            // @ts-ignore
            const qr = new Html5Qrcode("reader");

            console.log("[QR] iniciando cámara");

            qr.start(
              backCamera.id,
              { fps: 10, qrbox: qrBoxSize },
              (decodedText: string) => {
                console.log("[QR] QR detectado:", decodedText);

                // ✅ AHORA Streamlit SÍ lo acepta
                Streamlit.setComponentValue(decodedText);
                console.log("[QR] valor enviado a Streamlit");

                qr.stop().then(() => {
                  console.log("[QR] cámara detenida");
                });
              }
            ).catch((err: any) => {
              console.error("[QR] error al iniciar cámara", err);
            });
          })
          .catch((err: any) => {
            console.error("[QR] error getCameras", err);
          });
      };

      document.body.appendChild(script);
    };

    start();
  }, []);

  return (
    <div
      id="reader"
      style={{
        width: "300px",
        height: height + 'px',
        margin: "auto",
        background: "#000",
      }}
    />
  );
};

export default QrScanner;
