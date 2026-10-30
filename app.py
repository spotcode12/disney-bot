from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for
)

from functools import wraps
import os

from database import (
    crear_tablas,
    verificar_perfil,
    obtener_cuentas,
    obtener_cuenta,
    obtener_perfiles,
    agregar_cuenta,
    editar_cuenta,
    eliminar_cuenta,
    agregar_perfil,
    editar_perfil,
    cambiar_estado_perfil,
    eliminar_perfil,
    obtener_estado_solicitudes,
    registrar_solicitud
)

from disney_mail import obtener_codigo_disney


app = Flask(__name__)


# =========================================================
# CONFIGURACIÓN
# =========================================================

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CAMBIA-ESTA-CLAVE"
)

crear_tablas()


# =========================================================
# CREDENCIALES DEL ADMIN
# =========================================================

ADMIN_USER = os.getenv(
    "ADMIN_USER",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "CAMBIA-ESTA-CONTRASEÑA"
)


# =========================================================
# DECORADOR DE SEGURIDAD DEL ADMIN
# =========================================================

def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):

            return redirect(
                url_for("admin_login")
            )

        return func(*args, **kwargs)

    return wrapper


# =========================================================
# OCULTAR DOMINIO DEL CORREO
#
# Ejemplo:
# tifycuen@streamservice2.space
# tifycuen@**************.space
# =========================================================

def ocultar_dominio(correo):

    if not correo or "@" not in correo:

        return correo
