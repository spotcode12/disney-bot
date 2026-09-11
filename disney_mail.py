import os
import re
import time
import imaplib
import email
from email.header import decode_header
from html import unescape
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = "imap.zoho.com"
IMAP_PORT = 993


# =========================================================
# DECODIFICAR TEXTO
# =========================================================

def decodificar(texto):

    if not texto:
        return ""

    resultado = ""

    for parte, encoding in decode_header(texto):

        if isinstance(parte, bytes):

            resultado += parte.decode(
                encoding or "utf-8",
                errors="replace"
            )

        else:

            resultado += parte

    return resultado


# =========================================================
# LIMPIAR HTML
# =========================================================

def html_a_texto(html):

    html = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    texto = re.sub(
        r"<[^>]+>",
        " ",
        html
    )

    texto = unescape(texto)

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    return texto


# =========================================================
# OBTENER CONTENIDO DEL CORREO
# =========================================================

def obtener_contenido(mensaje):

    texto_plano = ""
    texto_html = ""

    if mensaje.is_multipart():

        for parte in mensaje.walk():

            if parte.get_content_disposition() == "attachment":
                continue

            tipo = parte.get_content_type()

            contenido = parte.get_payload(
                decode=True
            )

            if not contenido:
                continue

            charset = (
                parte.get_content_charset()
                or "utf-8"
            )

            contenido = contenido.decode(
                charset,
                errors="replace"
            )

            if tipo == "text/plain":

                texto_plano += contenido

            elif tipo == "text/html":

                texto_html += contenido

    else:

        contenido = mensaje.get_payload(
            decode=True
        )

        if contenido:

            charset = (
                mensaje.get_content_charset()
                or "utf-8"
            )

            contenido = contenido.decode(
                charset,
                errors="replace"
            )

            if mensaje.get_content_type() == "text/html":

                texto_html = contenido

            else:

                texto_plano = contenido

    return texto_plano, texto_html


# =========================================================
# EXTRAER CÓDIGO
# =========================================================

def extraer_codigo(mensaje):

    texto_plano, texto_html = obtener_contenido(
        mensaje
    )

    texto_html_limpio = html_a_texto(
        texto_html
    )

    patrones = [

        # Español
        r"verifiques.*?código.*?\b(\d{6})\b",
        r"dirección de correo.*?código.*?\b(\d{6})\b",
        r"código.*?\b(\d{6})\b",

        # Inglés
        r"verify.*?(?:code|passcode).*?\b(\d{6})\b",
        r"(?:one-time|one time).*?(?:code|passcode).*?\b(\d{6})\b",
        r"(?:access|verification).*?code.*?\b(\d{6})\b",

        # Francés
        r"(?:code|vérification).*?\b(\d{6})\b",

        # Italiano
        r"(?:codice|accesso).*?\b(\d{6})\b",

        # Alemán
        r"(?:code|zugangscode|bestätigung).*?\b(\d{6})\b"
    ]

    # HTML
    for patron in patrones:

        resultado = re.search(
            patron,
            texto_html_limpio,
            re.IGNORECASE | re.DOTALL
        )

        if resultado:

            return resultado.group(1)

    # Texto plano
    for patron in patrones:

        resultado = re.search(
            patron,
            texto_plano,
            re.IGNORECASE | re.DOTALL
        )

        if resultado:

            return resultado.group(1)

    # Respaldo
    texto_completo = (
        texto_html_limpio
        + " "
        + texto_plano
    )

    codigos = re.findall(
        r"\b\d{6}\b",
        texto_completo
    )

    if codigos:

        return codigos[0]

    return None


# =========================================================
# NORMALIZAR CORREO
# =========================================================

def normalizar_correo(correo):

    if not correo:
        return ""

    correo = correo.strip().lower()

    # Si viene como:
    # Nombre <correo@dominio.com>
    resultado = re.search(
        r"<([^>]+)>",
        correo
    )

    if resultado:

        correo = resultado.group(1)

    return correo.strip()


# =========================================================
# VERIFICAR DESTINATARIO
# =========================================================

def correo_pertenece_a_cuenta(
    mensaje,
    correo_cuenta
):

    correo_cuenta = normalizar_correo(
        correo_cuenta
    )

    if not correo_cuenta:
        return False

    headers = [

        mensaje.get("To"),
        mensaje.get("Delivered-To"),
        mensaje.get("X-Original-To"),
        mensaje.get("Envelope-To"),
        mensaje.get("X-Envelope-To"),
        mensaje.get("Cc")
    ]

    for header in headers:

        if not header:
            continue

        header_decodificado = decodificar(
            header
        ).lower()

        if correo_cuenta in header_decodificado:

            return True

    return False


# =========================================================
# OBTENER IDS DE CÓDIGOS
# SOLO DE UNA CUENTA
# =========================================================

def obtener_ids_codigos(
    mail,
    correo_cuenta
):

    estado, datos = mail.search(
        None,
        'FROM "disneyplus@trx.mail2.disneyplus.com"'
    )

    if estado != "OK":

        return set()

    ids = datos[0].split()

    ids_codigo = set()

    palabras_codigo = [

        "código",
        "codigo",
        "code",
        "passcode",
        "access code",
        "verification code",
        "one-time",
        "one time",
        "access",
        "verification",
        "codice",
        "code d'accès",
        "zugangscode",
        "bestätigung"
    ]

    for correo_id in ids:

        estado, datos = mail.fetch(
            correo_id,
            "(BODY.PEEK[HEADER.FIELDS "
            "(FROM TO CC SUBJECT DELIVERED-TO "
            "X-ORIGINAL-TO X-ENVELOPE-TO)])"
        )

        if estado != "OK":

            continue

        try:

            mensaje = email.message_from_bytes(
                datos[0][1]
            )

            # Comprobar destinatario
            if not correo_pertenece_a_cuenta(
                mensaje,
                correo_cuenta
            ):

                continue

            # Comprobar asunto
            asunto = decodificar(
                mensaje["Subject"]
            )

            asunto_lower = asunto.lower()

            if any(
                palabra in asunto_lower
                for palabra in palabras_codigo
            ):

                ids_codigo.add(
                    correo_id
                )

        except Exception as error:

            print(
                f"⚠️ Error leyendo correo {correo_id}: "
                f"{error}"
            )

            continue

    return ids_codigo


# =========================================================
# OBTENER ÚLTIMO CÓDIGO DE UNA CUENTA
# =========================================================

def obtener_codigo_disney(
    correo_cuenta,
    esperar_nuevo=True
):

    email_usuario = os.getenv(
        "EMAIL"
    )

    password = os.getenv(
        "PASSWORD"
    )

    if not email_usuario or not password:

        print(
            "❌ No existen las credenciales "
            "del buzón único."
        )

        print(
            "   Revisa EMAIL y PASSWORD "
            "en tu archivo .env."
        )

        return None

    print(
        f"📨 Buzón único: {email_usuario}"
    )

    print(
        f"🎯 Buscando código para: "
        f"{correo_cuenta}"
    )

    mail = None

    try:

        # -------------------------------------------------
        # CONEXIÓN IMAP CON TIEMPO MÁXIMO DE ESPERA
        # -------------------------------------------------

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT,
            timeout=20
        )

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        mail.login(
            email_usuario,
            password
        )

        mail.select("INBOX")

        # -------------------------------------------------
        # BUSCAR CÓDIGOS EXISTENTES
        # DE ESTA CUENTA
        # -------------------------------------------------

        ids_anteriores = obtener_ids_codigos(
            mail,
            correo_cuenta
        )

        print(
            f"📌 Códigos existentes de "
            f"{correo_cuenta}: "
            f"{len(ids_anteriores)}"
        )

        # =================================================
        # PRIMERO:
        # DEVOLVER EL ÚLTIMO CÓDIGO EXISTENTE
        # =================================================

        if ids_anteriores:

            ultimo_id = max(
                ids_anteriores,
                key=lambda x: int(x)
            )

            print(
                f"🔎 Revisando último correo "
                f"de la cuenta: {ultimo_id}"
            )

            estado, datos = mail.fetch(
                ultimo_id,
                "(RFC822)"
            )

            if estado == "OK":

                mensaje = email.message_from_bytes(
                    datos[0][1]
                )

                codigo = extraer_codigo(
                    mensaje
                )

                if codigo:

                    print(
                        f"✅ Último código de "
                        f"{correo_cuenta}: {codigo}"
                    )

                    return codigo

        # =================================================
        # SI NO HAY CÓDIGO:
        # ESPERAR UNO NUEVO
        # =================================================

        if not esperar_nuevo:

            print(
                "📭 No hay código disponible."
            )

            return None

        tiempo_maximo = 60
        intervalo = 1
        transcurrido = 0

        print(
            "⏳ Esperando nuevo código..."
        )

        while transcurrido < tiempo_maximo:

            print(
                f"⏳ {transcurrido}/"
                f"{tiempo_maximo}s"
            )

            mail.select("INBOX")

            ids_actuales = obtener_ids_codigos(
                mail,
                correo_cuenta
            )

            ids_nuevos = (
                ids_actuales
                - ids_anteriores
            )

            if ids_nuevos:

                ultimo_id = max(
                    ids_nuevos,
                    key=lambda x: int(x)
                )

                print(
                    f"📩 Nuevo correo encontrado: "
                    f"{ultimo_id}"
                )

                estado, datos = mail.fetch(
                    ultimo_id,
                    "(RFC822)"
                )

                if estado == "OK":

                    mensaje = email.message_from_bytes(
                        datos[0][1]
                    )

                    codigo = extraer_codigo(
                        mensaje
                    )

                    if codigo:

                        print(
                            f"🆕 Nuevo código de "
                            f"{correo_cuenta}: "
                            f"{codigo}"
                        )

                        return codigo

            time.sleep(
                intervalo
            )

            transcurrido += intervalo

        print(
            "⏰ Tiempo agotado."
        )

        return None

    except Exception as error:

        print(
            f"❌ Error IMAP: {error}"
        )

        return None

    finally:

        # -------------------------------------------------
        # CERRAR CORRECTAMENTE LA CONEXIÓN
        # -------------------------------------------------

        if mail is not None:

            try:

                mail.close()

            except Exception:

                pass

            try:

                mail.logout()

            except Exception:

                pass


# =========================================================
# PRUEBA DIRECTA
# =========================================================

if __name__ == "__main__":

    correo_prueba = input(
        "📧 Correo de la cuenta Disney+: "
    ).strip()

    if not correo_prueba:

        print(
            "❌ Debes ingresar un correo."
        )

    else:

        codigo = obtener_codigo_disney(
            correo_prueba
        )

        if codigo:

            print()
            print(
                "🔐 CÓDIGO:",
                codigo
            )

        else:

            print()
            print(
                "❌ No se encontró código."
            )