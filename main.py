import os
import json
import secrets
import string
import random
import time
import threading
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- PREVENIR SUSPENSIÓN EN ANDROID ---
try:
    import pydroid_wakelock
    pydroid_wakelock.acquire()
except Exception:
    pass

# --- CONFIGURACIÓN DE APIS ---
TELEGRAM_TOKEN = "8827683198:AAGHRQ5zgPpscnyIpM7rOhUkkPgBGNJi4Hk"
GEMINI_API_KEY = "AQ.Ab8RN6KsUkcoD82gau9CS49g9ZTIFnO9d3lkje0JXdDiULJpXg"

ai_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Probar modelos prioritarios requeridos por Google
        modelos_preferidos = [
            'gemini-3.6-flash',
            'gemini-2.5-flash',
            'models/gemini-3.6-flash',
            'models/gemini-2.5-flash'
        ]
        
        # Intentar conectar con los prioritarios primero
        for m_name in modelos_preferidos:
            try:
                ai_model = genai.GenerativeModel(m_name)
                print(f"✅ Conectado con éxito al modelo: {m_name}")
                break
            except Exception:
                continue

        # Si ninguno de los preferidos funcionó, buscar en la lista dinámica de la API
        if not ai_model:
            modelos_disponibles = [
                m.name for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            if modelos_disponibles:
                nombre_modelo = modelos_disponibles[0]
                ai_model = genai.GenerativeModel(nombre_modelo)
                print(f"✅ Conectado automáticamente al modelo disponible: {nombre_modelo}")
            else:
                print("❌ No se encontraron modelos activos para la clave de API.")
    except Exception as e:
        print(f"⚠️ Error en la configuración de Gemini: {e}")

# Lista de temas para aprendizaje en segundo plano
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
                    datos = json.load(f)
                    base = {"notas": [], "contactos": {}, "gastos": [], "ingresos": [], "tareas": [], "memoria": {}}
                    base.update(datos)
                    return base
            except Exception:
                pass
        return {"notas": [], "contactos": {}, "gastos": [], "ingresos": [], "tareas": [], "memoria": {}}

    def guardar_datos(self):
        temp = f"{self.archivo_datos}.tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)
        os.replace(temp, self.archivo_datos)

    def aprender_autonomamente(self):
        """Consulta a Gemini cada 3 minutos"""
        if not ai_model:
            print("❌ Gemini no está listo para el auto-aprendizaje.")
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

        # 1. REVISAR MEMORIA
        if t_low in self.datos["memoria"]:
            return f"🧠 (De mi memoria aprendida):\n{self.datos['memoria'][t_low]}"

        # 2. CONTROL DE FINANZAS
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

        # 3. NOTAS
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

        # 4. MEMORIA APRENDIDA
        elif t_low in ["ver memoria", "que aprendiste", "memoria"]:
            mem = self.datos["memoria"]
            cant = len(mem)
            if cant == 0:
                return "📂 Aún no tengo nada guardado en mi memoria."
            
            texto_memoria = f"🧠 Tengo guardados **{cant} conocimientos**.\n\n**Últimos aprendizajes:**\n"
            for clave, valor in list(mem.items())[-3:]:
                texto_memoria += f"• **{clave.capitalize()}**: {valor}\n\n"
            return texto_memoria

        # 5. GENERAR CONTRASEÑA
        elif "clave" in t_low or "contraseña" in t_low:
            chars = string.ascii_letters + string.digits + "!@#$%&*"
            clave = "".join(secrets.choice(chars) for _ in range(16))
            return f"🔑 Contraseña Segura:\n`{clave}`"

        # 6. CONSULTA DIRECTA A GEMINI
        if ai_model:
            try:
                res = ai_model.generate_content(texto)
                respuesta_ia = res.text
                
                self.datos["memoria"][t_low] = respuesta_ia
                self.guardar_datos()
                
                return respuesta_ia
            except Exception as e:
                return f"Error al consultar con Gemini: {str(e)}"

        return "No tengo conexión activa con Gemini."

yarvis = Yarvis()

def bucle_auto_aprendizaje():
    while True:
        time.sleep(180)  # Consulta cada 3 minutos
        yarvis.aprender_autonomamente()

hilo_aprendizaje = threading.Thread(target=bucle_auto_aprendizaje, daemon=True)
hilo_aprendizaje.start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Yarvis Online! Sistema de auto-aprendizaje iniciado correctamente.")

async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = yarvis.responder(update.message.text)
    await update.message.reply_text(res)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
    
    print("=== YARVIS ESCUCHANDO EN PYDROID 3 ===")
    app.run_polling()
