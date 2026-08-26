import os
import json
import secrets
import string
import random
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai

# --- CONFIGURACIÓN PRINCIPAL ---
GEMINI_API_KEY = "AQ.Ab8RN6JE7kWCm9xOraVGO8XlTG45fnZo8QUUcicrtQVu-SONkQ"

ai_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        modelos = ['gemini-1.5-flash', 'gemini-2.5-flash']
        for m_name in modelos:
            try:
                ai_model = genai.GenerativeModel(m_name)
                print(f"✅ Conectado con éxito al modelo: {m_name}")
                break
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Error al configurar Gemini: {e}")

TEMAS_INVESTIGACION = [
    "programacion en python", "inteligencia artificial", "astronomia y el universo",
    "historia universal", "trucos de productividad", "finanzas personales básicas",
    "ciberseguridad", "fisica cuantica explicada facil", "curiosidades del mundo",
    "salud y hábitos saludables", "tecnología del futuro"
]

class Yarvis:
    def __init__(self):
        self.archivo_datos = "yarvis_datos.json"
        self.datos = self.cargar_datos()

    def cargar_datos(self):
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, "r", encoding="utf-8") as f:
                    base = {"notas": [], "gastos": [], "ingresos": [], "memoria": {}}
                    base.update(json.load(f))
                    return base
            except Exception:
                pass
        return {"notas": [], "gastos": [], "ingresos": [], "memoria": {}}

    def guardar_datos(self):
        temp = f"{self.archivo_datos}.tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)
        os.replace(temp, self.archivo_datos)

    def aprender_autonomamente(self):
        if not ai_model:
            return

        tema = random.choice(TEMAS_INVESTIGACION)
        prompt = f"Dame un dato clave, útil o resumen conciso sobre: {tema}. Máximo 3 oraciones."

        try:
            res = ai_model.generate_content(prompt)
            conocimiento = res.text.strip()
            clave_memoria = f"dato sobre {tema}"

            self.datos["memoria"][clave_memoria] = conocimiento
            self.guardar_datos()
            print(f"🧠 [AUTO-APRENDIZAJE]: Yarvis aprendió algo nuevo sobre '{tema}'.")
        except Exception as e:
            print(f"Error en auto-aprendizaje: {e}")

    def responder(self, entrada):
        texto = entrada.strip()
        t_low = texto.lower()

        if not texto:
            return "Esperando tus órdenes..."

        if t_low in self.datos["memoria"]:
            return f"🧠 (De mi memoria aprendida):\n{self.datos['memoria'][t_low]}"

        if t_low.startswith("gasto "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                try:
                    monto = float(partes[1])
                    concepto = partes[2]
                    self.datos["gastos"].append({"monto": monto, "concepto": concepto, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    self.guardar_datos()
                    return f"💸 Gasto de ${monto:.2f} ('{concepto}') registrado."
                except ValueError:
                    return "Formato: `gasto 15.50 Comida`"

        elif t_low.startswith("ingreso "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                try:
                    monto = float(partes[1])
                    concepto = partes[2]
                    self.datos["ingresos"].append({"monto": monto, "concepto": concepto, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    self.guardar_datos()
                    return f"💵 Ingreso de ${monto:.2f} ('{concepto}') registrado."
                except ValueError:
                    return "Formato: `ingreso 100 Pago`"

        elif t_low in ["balance", "finanzas"]:
            tot_ing = sum(i["monto"] for i in self.datos["ingresos"])
            tot_gas = sum(g["monto"] for g in self.datos["gastos"])
            return f"📊 Saldo Actual: ${tot_ing - tot_gas:.2f} (Ingresos: ${tot_ing:.2f} | Gastos: ${tot_gas:.2f})"

        elif t_low.startswith("nota "):
            nota = texto[5:].strip()
            if nota:
                self.datos["notas"].append({"texto": nota, "fecha": datetime.now().strftime("%d/%m/%Y")})
                self.guardar_datos()
                return "📝 Nota guardada correctamente."

        elif t_low in ["ver notas", "notas"]:
            if not self.datos["notas"]: 
                return "📂 No tienes notas guardadas."
            return "📝 **Notas:**\n" + "\n".join([f"{i}. {n['texto']}" for i, n in enumerate(self.datos['notas'], 1)])

        elif t_low in ["ver memoria", "que aprendiste", "memoria"]:
            mem = self.datos["memoria"]
            cant = len(mem)
            if cant == 0:
                return "📂 Aún no tengo nada guardado en mi memoria."
            
            texto_memoria = f"🧠 Tengo guardados **{cant} conocimientos**.\n\n**Últimos aprendizajes:**\n"
            for clave, valor in list(mem.items())[-3:]:
                texto_memoria += f"• **{clave.capitalize()}**: {valor}\n\n"
            return texto_memoria

        elif "clave" in t_low or "contraseña" in t_low:
            chars = string.ascii_letters + string.digits + "!@#$%&*"
            clave = "".join(secrets.choice(chars) for _ in range(16))
            return f"🔑 Contraseña Segura:\n`{clave}`"

        if ai_model:
            try:
                res = ai_model.generate_content(texto)
                respuesta_ia = res.text
                self.datos["memoria"][t_low] = respuesta_ia
                self.guardar_datos()
                return respuesta_ia
            except Exception as e:
                return f"⚠️ Error al consultar con Gemini: {str(e)}"

        return "⚠️ La clave API de Gemini no está configurada o es inválida."

yarvis = Yarvis()

# --- SERVIDOR WEB FLASK CON MICRÓFONO Y RESPUESTA POR VOZ ---
app_web = Flask(__name__)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yarvis AI - Asistente Web</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #38bdf8; text-align: center; }
        .card { background-color: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .stat { font-size: 2em; font-weight: bold; color: #4ade80; }
        ul { list-style-type: none; padding: 0; }
        li { background: #334155; margin: 10px 0; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .text-content { max-width: 85%; }
        .btn-voice { background-color: #38bdf8; color: #0f172a; border: none; padding: 10px 16px; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background 0.2s; font-size: 1rem; }
        .btn-voice:hover { background-color: #7dd3fc; }
        .btn-mic { background-color: #ef4444; color: white; margin-left: 10px; }
        .btn-mic.listening { background-color: #22c55e; animation: pulse 1.5s infinite; }
        .btn-stop { background-color: #64748b; color: white; margin-left: 5px; }
        
        .chat-box { background: #0f172a; padding: 15px; border-radius: 8px; margin-top: 15px; min-height: 80px; border: 1px solid #334155; }
        .status-text { font-style: italic; color: #94a3b8; font-size: 0.9em; }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Yarvis AI - Asistente Web</h1>
        
        <!-- SECCIÓN DE INTERACCIÓN POR VOZ -->
        <div class="card">
            <h2>Hablar con Yarvis</h2>
            <p>Presiona el micrófono y habla. Yarvis procesará tu voz y te responderá en voz alta.</p>
            <div>
                <button id="btnMic" class="btn-voice btn-mic" onclick="alternarMicrofono()">🎙️ Iniciar Escucha</button>
                <button class="btn-voice btn-stop" onclick="detenerVoz()">⏹️ Detener Voz</button>
            </div>
            <p id="status" class="status-text">Micrófono inactivo.</p>
            
            <div class="chat-box">
                <p><strong>Tú dijiste:</strong> <span id="userQuery" style="color: #38bdf8;">-</span></p>
                <p><strong>Yarvis responde:</strong> <span id="yarvisReply" style="color: #4ade80;">-</span></p>
            </div>
        </div>

        <!-- DASHBOARD DE MEMORIA Y ESTADO -->
        <div class="card">
            <h2>Estado del Sistema</h2>
            <p>Servidor Web: <span style="color:#4ade80;">ACTIVO</span></p>
            <p>Conocimientos aprendidos en memoria:</p>
            <div class="stat">{{ memoria|length }}</div>
        </div>
        
        <div class="card">
            <h2>Conocimientos Aprendidos (Escuchar)</h2>
            <ul>
            {% for clave, valor in memoria.items() %}
                <li>
                    <div class="text-content">
                        <strong>{{ clave.capitalize() }}:</strong> {{ valor }}
                    </div>
                    <button class="btn-voice" onclick="hablar('{{ clave }}. {{ valor|replace('\'', '\\\'')|replace('\"', '\\\"')|replace('\n', ' ') }}')">🔊 Leer</button>
                </li>
            {% else %}
                <li>Aún no hay memorias registradas.</li>
            {% endfor %}
            </ul>
        </div>
    </div>

    <script>
        let meEstaEscuchando = false;
        let reconocimiento;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            reconocimiento = new SpeechRecognition();
            reconocimiento.lang = 'es-ES';
            reconocimiento.continuous = false;
            reconocimiento.interimResults = false;

            reconocimiento.onstart = function() {
                meEstaEscuchando = true;
                document.getElementById('status').innerText = "🔴 Escuchando... habla ahora.";
                const btn = document.getElementById('btnMic');
                btn.innerText = "🛑 Detener Escucha";
                btn.classList.add('listening');
            };

            reconocimiento.onresult = function(event) {
                const textoCapturado = event.results[0][0].transcript;
                document.getElementById('userQuery').innerText = textoCapturado;
                document.getElementById('status').innerText = "⏳ Yarvis está pensando...";
                enviarAYarvis(textoCapturado);
            };

            reconocimiento.onerror = function(event) {
                document.getElementById('status').innerText = "⚠️ Error en la escucha: " + event.error;
                detenerMicrofonoUI();
            };

            reconocimiento.onend = function() {
                detenerMicrofonoUI();
            };
        } else {
            document.getElementById('status').innerText = "❌ Tu navegador no admite el reconocimiento de voz por micrófono.";
        }

        function alternarMicrofono() {
            if (!reconocimiento) return;
            if (!meEstaEscuchando) {
                detenerVoz();
                reconocimiento.start();
            } else {
                reconocimiento.stop();
            }
        }

        function detenerMicrofonoUI() {
            meEstaEscuchando = false;
            document.getElementById('status').innerText = "Micrófono listo.";
            const btn = document.getElementById('btnMic');
            btn.innerText = "🎙️ Iniciar Escucha";
            btn.classList.remove('listening');
        }

        function enviarAYarvis(texto) {
            fetch('/api/preguntar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: texto })
            })
            .then(res => res.json())
            .then(data => {
                const respuesta = data.respuesta;
                document.getElementById('yarvisReply').innerText = respuesta;
                document.getElementById('status').innerText = "🔊 Yarvis está respondiendo por voz...";
                hablar(respuesta);
            })
            .catch(err => {
                document.getElementById('yarvisReply').innerText = "⚠️ Error al comunicarse con Yarvis.";
                document.getElementById('status').innerText = "Error en la conexión.";
            });
        }

        function hablar(texto) {
            window.speechSynthesis.cancel();
            if ('speechSynthesis' in window) {
                const mensaje = new SpeechSynthesisUtterance(texto);
                mensaje.lang = 'es-ES';
                mensaje.rate = 1.0;
                mensaje.pitch = 1.0;
                window.speechSynthesis.speak(mensaje);
            }
        }

        function detenerVoz() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
        }
    </script>
</body>
</html>
"""

@app_web.route('/')
def home():
    return render_template_string(HTML_DASHBOARD, memoria=yarvis.datos["memoria"])

@app_web.route('/api/preguntar', methods=['POST'])
def api_preguntar():
    datos = request.get_json()
    mensaje = datos.get("mensaje", "")
    respuesta = yarvis.responder(mensaje)
    return jsonify({"respuesta": respuesta})

def bucle_auto_aprendizaje():
    while True:
        time.sleep(900)
        yarvis.aprender_autonomamente()

if __name__ == "__main__":
    # Hilo para auto-aprendizaje en segundo plano
    threading.Thread(target=bucle_auto_aprendizaje, daemon=True).start()
    
    # Iniciar servidor Web
    port = int(os.environ.get("PORT", 10000))
    print(f"=== YARVIS WEB ONLINE EN EL PUERTO {port} ===")
    app_web.run(host="0.0.0.0", port=port)
