import os
import json
import secrets
import string
import random
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- CONFIGURACIÓN PRINCIPAL ---
TELEGRAM_TOKEN = "8827683198:AAGHRQ5zgPpscnyIpM7rOhUkkPgBGNJi4Hk"

# Clave API de Gemini integrada directamente
GEMINI_API_KEY = "AQ.Ab8RN6IuwCzaokEDoln5GdJAra5BIh8D5UItnS3jS9N_xBGnVA"

ai_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Probamos modelos compatibles con la API
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

# --- SERVIDOR WEB FLASK PARA RENDER ---
app_web = Flask(__name__)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yarvis AI - Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #38bdf8; text-align: center; }
        .card { background-color: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .stat { font-size: 2em; font-weight: bold; color: #4ade80; }
        ul { list-style-type: none; padding: 0; }
        li { background: #334155; margin: 8px 0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Panel de Control de Yarvis</h1>
        <div class="card">
            <h2>Estado del Sistema</h2>
            <p>Servidor 24/7 en Render: <span style="color:#4ade80;">ACTIVO</span></p>
            <p>Conocimientos aprendidos en memoria:</p>
            <div class="stat">{{ memoria|length }}</div>
        </div>
        <div class="card">
            <h2>Últimos Aprendizajes</h2>
            <ul>
            {% for clave, valor in memoria.items() %}
                <li><strong>{{ clave.capitalize() }}:</strong> {{ valor }}</li>
            {% else %}
                <li>Aún no hay memorias registradas.</li>
            {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app_web.route('/')
def home():
    return render_template_string(HTML_DASHBOARD, memoria=yarvis.datos["memoria"])

def ejecutar_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

def bucle_auto_aprendizaje():
    while True:
        time.sleep(900)  # Revisa cada 15 minutos (900 segundos) para optimizar la cuota
        yarvis.aprender_autonomamente()

# Hilos para la Web y el Auto-aprendizaje en segundo plano
threading.Thread(target=ejecutar_web, daemon=True).start()
threading.Thread(target=bucle_auto_aprendizaje, daemon=True).start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Yarvis Online 24/7 en Render! Servidor web y bot activos.")

async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = yarvis.responder(update.message.text)
    await update.message.reply_text(res)

if __name__ == "__main__":
    app_telegram = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start_command))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
    
    print("=== YARVIS ONLINE EN RENDER (24/7) ===")
    app_telegram.run_polling()
