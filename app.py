from flask import Flask, request, jsonify
import requests
import os
import random
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN    = "marsbotverify2026"
PHONE_NUMBER_ID = "1074786032384447"
WA_TOKEN        = os.environ.get("WA_TOKEN", "EAAV06dZAG84MBRUXgUGXok4WC0JpnEUwHLkiENthiYwFgKqJXZAtNK3dbh2XsTLCuaZBWrDppPwqCGVdSOKSY89UvgfpSA2nTTjNdeZAcGjez1BJ0LZBOPdxNLytGJHFmErfEBnSapP8ZAFnZB4Cg2NN7gx9EJDpDGiPOFVkv4y3ejDCXZCas5FH2T0sbbiQBVZA64fR6ImgMefczZA8koLZCjoniuR2PZALH0hKXOlbgzpUhUakWWYkh9hwkAZDZD")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_KEY", "")
SEND_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
HEADERS  = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}

sessions = {}

def get_session(phone):
    if phone not in sessions:
        sessions[phone] = {"collect_field": None, "pedido": {"cat": "", "nombre": "", "tel": "", "nota": ""}, "history": []}
    return sessions[phone]

STAFF = [
    {"nombre": "Robert Mata",   "cargo": "Gerente Administrativo"},
    {"nombre": "Yokairy Marte", "cargo": "Ejecutiva de Ventas"},
    {"nombre": "Lizbeth Félix", "cargo": "Ejecutiva de Ventas"},
]

INFO = {
    "direccion":      "Calle Señoritas Villa esq. José Horacio Rodríguez, La Vega, República Dominicana",
    "horario":        "Lun–Vie: 8:00 AM – 7:00 PM | Sábado: 8:00 AM – 6:00 PM | Domingo: Cerrado",
    "envios":         "Realizamos envíos a todo el territorio nacional de República Dominicana 🚚. El costo y tiempo de entrega se coordinan según tu provincia.",
    "financiamiento": "Ofrecemos financiamiento hasta *18 meses* en cuotas mensuales, sin prima en productos seleccionados. Solo necesitas cédula y comprobante de ingresos.",
}

CATEGORIAS = {
    "sala":             ["sala","sofá","sofa","sillón","sillon","seccional"],
    "aposento":         ["aposento","cama","cuarto","dormitorio","habitación","habitacion","dresser"],
    "nevera":           ["nevera","refrigerador","refrigeradora"],
    "lavadora":         ["lavadora","lavasecadora"],
    "estufa":           ["estufa","cocina","hornilla"],
    "aire":             ["aire","acondicionado","minisplit","mini split"],
    "televisor":        ["televisor","televisores","tv","smart tv","pantalla"],
    "electrodomestico": ["electrodoméstico","electrodomestico","electro"],
    "adorno":           ["adorno","cuadro","jarrón","jarron","lampara","lámpara","alfombra"],
    "cortina":          ["cortina","persiana","romana","blackout"],
    "decoracion":       ["decoración","decoracion","asesoría","asesoria","diseño","decorar"],
}

FAQ = [
    {"keys": ["garantía","garantia","defecto","daño"],"resp": "🛡️ *Garantía:*\n• Electrodomésticos: 1–2 años según marca\n• Muebles: 6 meses en estructura\n• Cortinas: 3 meses en instalación\n\nCoordinamos revisión o reposición en caso de defecto. 😊"},
    {"keys": ["devolu","cambio","devolver","arrepent"],"resp": "🔄 *Cambios y Devoluciones:*\nTienes hasta *7 días* desde la entrega. Producto debe estar en estado original. Artículos personalizados no aplican."},
    {"keys": ["tiempo","cuánto tarda","cuanto tarda","demora","llegará","cuando llega"],"resp": "⏱️ *Tiempos de entrega:*\n• La Vega: 1–2 días hábiles\n• Sto. Domingo/Santiago: 2–3 días\n• Resto del país: 3–5 días hábiles"},
    {"keys": ["marcas","marca","fabricante"],"resp": "🏷️ *Marcas:*\n• Neveras/Lavadoras: Samsung, LG, Mabe, Whirlpool\n• Televisores: Samsung, LG, TCL, Hisense\n• Aires: LG, Carrier, Midea"},
    {"keys": ["instala","instalación","instalacion","arman","montan"],"resp": "🔧 *Instalación:*\nInstalamos aires, televisores, cortinas y aposentos. Costo según artículo y zona."},
    {"keys": ["pago","efectivo","tarjeta","transferencia","formas de pago"],"resp": "💰 *Formas de pago:*\n• Efectivo\n• Tarjeta crédito/débito\n• Transferencia bancaria\n• Pagos móviles\n• Financiamiento hasta *18 meses*"},
    {"keys": ["usado","segunda","seminuevo"],"resp": "ℹ️ Solo manejamos *productos nuevos*, directamente del fabricante. ¡Calidad garantizada! 😊"},
    {"keys": ["regalo","obsequio","empaque"],"resp": "🎁 ¡Sí! Hacemos *empaque especial para regalo* en artículos seleccionados. Indícalo en tu pedido."},
]

def is_open():
    now = datetime.now()
    day = now.weekday()
    h   = now.hour + now.minute / 60
    if day == 6: return False
    if day <= 4: return 8 <= h < 19
    if day == 5: return 8 <= h < 18
    return False

def detect_category(t):
    for cat, keywords in CATEGORIAS.items():
        if any(k in t for k in keywords):
            return cat
    return None

def is_offer(t):
    return any(k in t for k in ["oferta","promoción","promo","promocion","descuento","rebaja","vi en","vi por","redes","instagram","facebook","anuncio","post"])

def match_faq(t):
    for f in FAQ:
        if any(k in t for k in f["keys"]):
            return f["resp"]
    return None

def pick_rep():
    reps = [s for s in STAFF if "Ejecutiva" in s["cargo"]]
    return random.choice(reps)

def rep_intro(rep, ctx=""):
    open_now = is_open()
    ctx_line = f"\n📋 _Consulta: {ctx}_" if ctx else ""
    off_line = "\n\n⚠️ Estamos fuera de horario (Lun–Vie 8AM–7PM · Sáb 8AM–6PM). Tu solicitud quedó registrada y te responderemos al abrir. 🙏" if not open_now else ""
    return f"¡Hola! 👋 Mi nombre es *{rep['nombre']}*, soy *{rep['cargo']}* de *Mars Electromuebles S.R.L.*{ctx_line}\n\nEs un placer atenderte. Estoy aquí para ayudarte. 😊{off_line}"

MENU = "¿En qué puedo ayudarte?\n\n1 Ver productos\n2️⃣ Envíos\n3️⃣ Contacto y horario\n4️⃣ Financiamiento\n5️⃣ Asesoría de decoración\n6️⃣ Hablar con un representante\n7️⃣ Hacer un pedido\n\n_Escribe el número o tu pregunta_ 😊"

PRODUCTS_MENU = "🏬 *Nuestros productos:*\n\n🛋️ Juegos de Sala\n🛏️ Juegos de Aposento\n📺 Electrodomésticos\n🪴 Adornos y Decoración\n🪟 Cortinas Personalizadas\n🎨 Asesoría de Decoración\n\n_Escríbenos qué artículo te interesa y un representante te atenderá._ 😊"

def send(to, text):
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(SEND_URL, headers=HEADERS, json=payload)

def ai_reply(history, user_msg):
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 400,
                  "system": "Eres el asistente virtual de Mars Electromuebles S.R.L., La Vega, República Dominicana. Vendemos muebles y electrodomésticos. NO des precios ni listas. Si preguntan por artículos diles que un representante les atenderá. Responde en español dominicano, amable, máximo 3 líneas.",
                  "messages": (history[-6:] if len(history) > 6 else history) + [{"role": "user", "content": user_msg}]}
        )
        return r.json()["content"][0]["text"]
    except:
        return "Disculpa, tuve un inconveniente. 😊 Escribe *menú* para ver las opciones."

def process_message(phone, text):
    sess = get_session(phone)
    t = text.lower().strip()
    replies = []
    def r(msg): replies.append(msg)

    num_map = {"1":"productos","2":"envio","3":"contacto","4":"financiamiento","5":"asesoria","6":"representante","7":"pedido"}
    if t in num_map: t = num_map[t]

    if sess["collect_field"]:
        f = sess["collect_field"]
        if f == "nombre":
            sess["pedido"]["nombre"] = text; sess["collect_field"] = "tel"
            r(f"Perfecto, *{text}*. 😊\n¿Cuál es tu número de teléfono o WhatsApp?"); return replies
        if f == "tel":
            sess["pedido"]["tel"] = text; sess["collect_field"] = "nota"
            r("¡Anotado! 📝\n¿Alguna nota adicional? (color, tamaño, modelo…)\nSi no, escribe *ninguna*."); return replies
        if f == "nota":
            nota = "" if t == "ninguna" else text
            sess["pedido"]["nota"] = nota; sess["collect_field"] = None
            p = sess["pedido"]
            r(f"✅ *¡Solicitud registrada!*\n\n👤 *Nombre:* {p['nombre']}\n📞 *Teléfono:* {p['tel']}\n🛒 *Interés:* {p['cat'] or 'Consulta general'}" + (f"\n📌 *Nota:* {nota}" if nota else "") + "\n\nUn representante te contactará en breve. 🤝")
            rep = pick_rep(); r(rep_intro(rep, p["cat"]))
            sess["pedido"] = {"cat": "", "nombre": "", "tel": "", "nota": ""}; return replies

    greetings = ["hola","hi","buenas","buenos","hey","buen día","buen dia","inicio","menú","menu","volver","start","opciones"]
    if any(t == w or t.startswith(w + " ") for w in greetings):
        open_now = is_open()
        status = "🟢 ¡Estamos *abiertos* ahora mismo!" if open_now else "🔴 Estamos *fuera de horario*, tu mensaje queda registrado. Te atendemos al abrir."
        r(f"¡Hola! 👋 Bienvenido/a a *Mars Electromuebles S.R.L.*\n\n{status}\n\n{MENU}"); return replies

    if is_offer(t):
        cat = detect_category(t)
        ctx = f"Oferta de {cat}" if cat else "Oferta de redes sociales"
        sess["pedido"]["cat"] = ctx
        r("🏷️ *¡Bienvenido/a a nuestra promoción!* 🎉\n\nGracias por tu interés. Para confirmarte el precio especial y disponibilidad, en breve un representante te atenderá personalmente. ⏳")
        r(rep_intro(pick_rep(), ctx)); return replies

    faq = match_faq(t)
    if faq: r(faq); return replies

    if any(k in t for k in ["ver producto","catálogo","catalogo","productos","qué venden","que venden"]):
        r(PRODUCTS_MENU); return replies

    cat = detect_category(t)
    if cat:
        nombres = {"sala":"Juegos de Sala","aposento":"Juegos de Aposento","nevera":"Neveras / Refrigeradores","lavadora":"Lavadoras","estufa":"Estufas / Cocinas","aire":"Aires Acondicionados","televisor":"Televisores Smart TV","electrodomestico":"Electrodomésticos","adorno":"Adornos y Decoración","cortina":"Cortinas Personalizadas","decoracion":"Asesoría de Decoración"}
        nombre_cat = nombres.get(cat, "ese artículo")
        sess["pedido"]["cat"] = nombre_cat
        r(f"¡Excelente elección! 😊\n\nTenemos disponibilidad en *{nombre_cat}*.\n\n⏳ *Un momento, por favor...* En breve uno de nuestros representantes te atenderá y te enviará imágenes de los artículos disponibles. 📸")
        r(rep_intro(pick_rep(), nombre_cat)); return replies

    if any(k in t for k in ["asesor","decorar","diseño","diseno","transformar"]):
        sess["pedido"]["cat"] = "Asesoría de Decoración"
        r("🎨 *Asesoría Personalizada de Decoración*\n\nNuestro equipo te ayuda a transformar tu espacio con visita al hogar, paleta de colores, selección de muebles y plan de distribución.\n\n✨ *Primera consulta sin costo* para clientes que compren en Mars Electromuebles.\n\n⏳ En breve un representante te contactará. 😊")
        r(rep_intro(pick_rep(), "Asesoría de Decoración")); return replies

    if any(k in t for k in ["representante","hablar con","hablar a","agente","vendedor","ejecutiva","persona"]):
        staff_list = "\n".join([f"• *{s['nombre']}* – {s['cargo']}" for s in STAFF])
        r(f"Con gusto te conecto:\n\n{staff_list}\n\nEscribe el nombre o *cualquiera* para asignarte uno disponible. 😊"); return replies

    for s in STAFF:
        if s["nombre"].lower().split()[0] in t or s["nombre"].lower() in t:
            r(f"⏳ Conectándote con *{s['nombre']}*..."); r(rep_intro(s, sess["pedido"].get("cat",""))); return replies
    if "cualquiera" in t:
        rep = pick_rep(); r(f"⏳ Conectándote con *{rep['nombre']}*..."); r(rep_intro(rep, sess["pedido"].get("cat",""))); return replies

    if any(k in t for k in ["envío","envio","entrega","despacho","enviar","domicilio","mandar","llevan"]):
        r(f"🚚 *Envíos a Todo el País*\n\n{INFO['envios']}\n\n📍 *Nuestra tienda:*\n{INFO['direccion']}"); return replies

    if any(k in t for k in ["financ","cuotas","crédito","credito","meses","mensual"]):
        r(f"💳 *Financiamiento hasta 18 Meses*\n\n{INFO['financiamiento']}\n\nEscribe *representante* para cotizar tu cuota. 😊"); return replies

    if any(k in t for k in ["contact","horario","dirección","direccion","dónde","donde","ubicación","abierto","abren","teléfono","telefono"]):
        open_now = is_open()
        status = "🟢 *¡Estamos abiertos ahora mismo!*" if open_now else "🔴 *Cerrados.* Te atendemos al reabrir. 😊"
        r(f"📍 *Mars Electromuebles S.R.L.*\n{INFO['direccion']}\n\n⏰ *Horario:*\n{INFO['horario']}\n\n{status}"); return replies

    if any(k in t for k in ["pedir","pedido","cotiz","reservar","comprar","agendar","solicitar","quiero","confirmar","aprovechar"]):
        sess["collect_field"] = "nombre"
        r("📋 *Registro de Solicitud*\n\n¡Excelente! 🙌 Voy a tomar tus datos para conectarte con un representante.\n\n¿Cuál es tu *nombre completo*?"); return replies

    if any(k in t for k in ["gracias","muchas gracias"]):
        r("¡Con mucho gusto! 😊 En *Mars Electromuebles* siempre es un placer atenderte. ¡Excelente día! ✨"); return replies

    if any(k in t for k in ["queja","problema","reclamo","molest","inconveniente"]):
        r("😔 Lamentamos tu experiencia. La satisfacción de nuestros clientes es nuestra prioridad.\n\nTe conecto de inmediato con un representante. 🤝")
        r(rep_intro(pick_rep(), "Queja / inconveniente")); return replies

    sess["history"].append({"role": "user", "content": text})
    reply = ai_reply(sess["history"], text)
    sess["history"].append({"role": "assistant", "content": reply})
    r(reply); return replies

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                for msg in messages:
                    if msg.get("type") == "text":
                        phone = msg["from"]
                        text  = msg["text"]["body"]
                        for reply in process_message(phone, text):
                            send(phone, reply)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def home():
    return "🛋️ Mars Electromuebles Bot – Activo ✅", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
