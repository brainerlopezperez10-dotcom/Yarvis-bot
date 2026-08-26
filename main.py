import os
import json
import secrets
import string
import random
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

# --- CONFIGURACIÓN DE GEMINI ---
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
    "ciberseguridad", "fisica cuantica explicada facil", "curiosidades del mundo"
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
        prompt = f"Dame un dato clave o curioso muy conciso sobre: {tema}. Máximo 2 oraciones."
        try:
            res = ai_model.generate_content(prompt)
            conocimiento = res.text.strip()
            self.datos["memoria"][f"dato sobre {tema}"] = conocimiento
            self.guardar_datos()
            print(f"🧠 [AUTO-APRENDIZAJE]: Aprendido sobre '{tema}'.")
        except Exception as e:
            print(f"Error en auto-aprendizaje: {e}")

    def responder(self, entrada):
        texto = entrada.strip()
        t_low = texto.lower()

        if not texto:
            return "Esperando tus órdenes..."

        if t_low in self.datos["memoria"]:
            return f"🧠 (De mi memoria):\n{self.datos['memoria'][t_low]}"

        if t_low.startswith("gasto "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                try:
                    monto = float(partes[1])
                    concepto = partes[2]
                    self.datos["gastos"].append({"monto": monto, "concepto": concepto, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    self.guardar_datos()
                    return f"💸 Gasto registrado: ${monto:.2f} en '{concepto}'."
                except ValueError:
                    return "Formato incorrecto. Usa: gasto 15.50 Comida"

        elif t_low.startswith("ingreso "):
            partes = texto.split(" ", 2)
            if len(partes) >= 3:
                try:
                    monto = float(partes[1])
                    concepto = partes[2]
                    self.datos["ingresos"].append({"monto": monto, "concepto": concepto, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    self.guardar_datos()
                    return f"💵 Ingreso registrado: ${monto:.2f} por '{concepto}'."
                except ValueError:
                    return "Formato incorrecto. Usa: ingreso 100 Pago"

        elif t_low in ["balance", "finanzas"]:
            tot_ing = sum(i.get("monto", 0) for i in self.datos.get("ingresos", []))
            tot_gas = sum(g.get("monto", 0) for g in self.datos.get("gastos", []))
            return f"📊 Saldo Actual: ${tot_ing - tot_gas:.2f} (Ingresos: ${tot_ing:.2f} | Gastos: ${tot_gas:.2f})"

        elif t_low.startswith("nota "):
            nota = texto[5:].strip()
            if nota:
                self.datos["notas"].append({"texto": nota, "fecha": datetime.now().strftime("%d/%m/%Y")})
                self.guardar_datos()
                return "📝 Nota guardada correctamente."

        elif t_low in ["ver notas", "notas"]:
            if not self.datos.get("notas"): 
                return "📂 No tienes notas guardadas."
            return "📝 Notas:\n" + "\n".join([f"{i}. {n['texto']}" for i, n in enumerate(self.datos['notas'], 1)])

        elif "clave" in t_low or "contraseña" in t_low:
            chars = string.ascii_letters + string.digits + "!@#$%&*"
            clave = "".join(secrets.choice(chars) for _ in range(16))
            return f"🔑 Contraseña generada: {clave}"

        if ai_model:
            try:
                res = ai_model.generate_content(texto)
                respuesta_ia = res.text
                self.datos["memoria"][t_low] = respuesta_ia
                self.guardar_datos()
                return respuesta_ia
            except Exception as e:
                return f"⚠️ Error al consultar con Gemini: {str(e)}"

        return "⚠️ Servidor no disponible temporalmente."

yarvis = Yarvis()
app = Flask(__name__)

# --- RUTA PRINCIPAL CON PROTECCIÓN ANTI PANTALLA EN BLANCO ---
@app.route('/')
def home():
    try:
        ingresos = yarvis.datos.get("ingresos", [])
        gastos = yarvis.datos.get("gastos", [])
        memoria = yarvis.datos.get("memoria", {})
        notas = yarvis.datos.get("notas", [])

        tot_ing = sum(i.get("monto", 0) for i in ingresos)
        tot_gas = sum(g.get("monto", 0) for g in gastos)
        balance = tot_ing - tot_gas

        return render_template(
            'index.html', 
            memoria=memoria, 
            notas=notas,
            balance=balance
        )
    except Exception as e:
        return f"<h2>Error al cargar la interfaz web: {str(e)}</h2>"

@app.route('/api/preguntar', methods=['POST'])
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
    threading.Thread(target=bucle_auto_aprendizaje, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"=== YARVIS WEB ONLINE EN PUERTO {port} ===")
    app.run(host="0.0.0.0", port=port)
