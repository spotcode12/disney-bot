from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import os

from database import (
    crear_tablas,
    verificar_perfil,
    obtener_cuentas,
    obtener_cuenta,
    obtener_perfiles,
    agregar_cuenta,
    agregar_perfil,
    editar_perfil,
    cambiar_estado_perfil,
    eliminar_perfil
)

from disney_mail import obtener_codigo_disney


app = Flask(__name__)

crear_tablas()

# SECURITY
app.secret_key = os.getenv("FLASK_SECRET_KEY", "CAMBIA-ESTA-CLAVE")


# =========================================================
# CONFIGURACIÓN
# =========================================================

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "CAMBIA-ESTA-CLAVE"
)


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
# DECORADOR DE SEGURIDAD
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
# PÁGINA DEL CLIENTE
# =========================================================

@app.route("/")
def inicio():

    return render_template(
        "index.html"
    )


# =========================================================
# VERIFICAR PERFIL DEL CLIENTE
# =========================================================

@app.route(
    "/verificar-perfil",
    methods=["POST"]
)
def verificar():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    pin = datos.get(
        "pin",
        ""
    ).strip()

    if not nombre or not pin:

        return jsonify({
            "ok": False,
            "mensaje": "Ingresa tu perfil y PIN."
        }), 400

    perfil = verificar_perfil(
        nombre,
        pin
    )

    if not perfil:

        return jsonify({
            "ok": False,
            "mensaje": "Perfil o PIN incorrecto."
        }), 401

    perfil_id = perfil[0]
    cuenta_id = perfil[1]
    nombre_perfil = perfil[2]
    correo_cuenta = perfil[3]

    print(
        f"✅ Perfil verificado: "
        f"{nombre_perfil} | "
        f"Cuenta: {correo_cuenta}"
    )

    return jsonify({
        "ok": True,
        "mensaje": "Perfil verificado correctamente.",
        "perfil": nombre_perfil,
        "cuenta_id": cuenta_id,
        "correo": correo_cuenta
    })


# =========================================================
# SOLICITAR CÓDIGO
# =========================================================

@app.route(
    "/solicitar-codigo",
    methods=["POST"]
)
def solicitar_codigo():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    pin = datos.get(
        "pin",
        ""
    ).strip()

    if not nombre or not pin:

        return jsonify({
            "ok": False,
            "mensaje": "Debes verificar tu perfil primero."
        }), 400

    perfil = verificar_perfil(
        nombre,
        pin
    )

    if not perfil:

        return jsonify({
            "ok": False,
            "mensaje": "Perfil o PIN incorrecto."
        }), 401

    cuenta_id = perfil[1]
    nombre_perfil = perfil[2]
    correo_cuenta = perfil[3]

    print(
        f"📩 Solicitud de código: "
        f"{nombre_perfil} | "
        f"Cuenta: {correo_cuenta}"
    )

    codigo = obtener_codigo_disney(
        correo_cuenta
    )

    if not codigo:

        print(
            f"❌ No se encontró código para "
            f"{correo_cuenta}"
        )

        return jsonify({
            "ok": False,
            "mensaje": "No se encontró un código."
        }), 404

    print(
        f"🔐 Código obtenido para "
        f"{correo_cuenta}: {codigo}"
    )

    return jsonify({
        "ok": True,
        "codigo": codigo
    })


# =========================================================
# LOGIN DEL ADMIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    # Si ya inició sesión, no necesita volver al login
    if session.get("admin_logged_in"):

        return redirect(
            url_for("admin")
        )

    error = None

    if request.method == "POST":

        usuario = request.form.get(
            "usuario",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            usuario == ADMIN_USER
            and password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True
            session["admin_user"] = usuario

            print(
                f"🔐 Login admin correcto: {usuario}"
            )

            return redirect(
                url_for("admin")
            )

        error = "Usuario o contraseña incorrectos."

        print(
            "❌ Intento de login admin incorrecto"
        )

    return render_template(
        "admin_login.html",
        error=error
    )


# =========================================================
# CERRAR SESIÓN ADMIN
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    usuario = session.get(
        "admin_user",
        "admin"
    )

    session.clear()

    print(
        f"🔒 Sesión admin cerrada: {usuario}"
    )

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# ADMINISTRACIÓN
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    return render_template(
        "admin.html"
    )


# =========================================================
# LISTAR CUENTAS
# =========================================================

@app.route("/admin/cuentas")
@admin_required
def admin_cuentas():

    cuentas = obtener_cuentas()

    lista = []

    for cuenta in cuentas:

        lista.append({
            "id": cuenta[0],
            "nombre": cuenta[1],
            "correo": cuenta[2],
            "estado": cuenta[3]
        })

    return jsonify({
        "ok": True,
        "cuentas": lista
    })


# =========================================================
# AGREGAR CUENTA
# =========================================================

@app.route(
    "/admin/agregar-cuenta",
    methods=["POST"]
)
@admin_required
def admin_agregar_cuenta():

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    correo = datos.get(
        "correo",
        ""
    ).strip()

    if not nombre or not correo:

        return jsonify({
            "ok": False,
            "mensaje": "Completa todos los campos."
        }), 400

    agregar_cuenta(
        nombre,
        correo
    )

    print(
        f"✅ Cuenta agregada: "
        f"{nombre} | {correo}"
    )

    return jsonify({
        "ok": True,
        "mensaje": "Cuenta agregada correctamente."
    })


# =========================================================
# PÁGINA DE PERFILES
# =========================================================

@app.route(
    "/admin/cuenta/<int:cuenta_id>"
)
@admin_required
def admin_perfiles(cuenta_id):

    cuenta = obtener_cuenta(
        cuenta_id
    )

    if not cuenta:

        return "Cuenta no encontrada", 404

    return render_template(
        "perfiles.html",
        cuenta_id=cuenta_id
    )


# =========================================================
# DATOS DE LA CUENTA
# =========================================================

@app.route(
    "/admin/cuenta/<int:cuenta_id>/datos"
)
@admin_required
def admin_cuenta_datos(cuenta_id):

    cuenta = obtener_cuenta(
        cuenta_id
    )

    if not cuenta:

        return jsonify({
            "ok": False,
            "mensaje": "Cuenta no encontrada."
        }), 404

    return jsonify({
        "ok": True,
        "cuenta": {
            "id": cuenta[0],
            "nombre": cuenta[1],
            "correo": cuenta[2],
            "estado": cuenta[3]
        }
    })


# =========================================================
# LISTAR PERFILES
# =========================================================

@app.route(
    "/admin/cuenta/<int:cuenta_id>/perfiles"
)
@admin_required
def admin_lista_perfiles(cuenta_id):

    cuenta = obtener_cuenta(
        cuenta_id
    )

    if not cuenta:

        return jsonify({
            "ok": False,
            "mensaje": "Cuenta no encontrada."
        }), 404

    perfiles = obtener_perfiles(
        cuenta_id
    )

    lista = []

    for perfil in perfiles:

        lista.append({
            "id": perfil[0],
            "nombre": perfil[1],
            "activo": bool(perfil[3])
        })

    return jsonify({
        "ok": True,
        "perfiles": lista
    })


# =========================================================
# AGREGAR PERFIL
# =========================================================

@app.route(
    "/admin/cuenta/<int:cuenta_id>/agregar-perfil",
    methods=["POST"]
)
@admin_required
def admin_agregar_perfil(cuenta_id):

    cuenta = obtener_cuenta(
        cuenta_id
    )

    if not cuenta:

        return jsonify({
            "ok": False,
            "mensaje": "Cuenta no encontrada."
        }), 404

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    pin = datos.get(
        "pin",
        ""
    ).strip()

    if not nombre or not pin:

        return jsonify({
            "ok": False,
            "mensaje": "Completa nombre y PIN."
        }), 400

    agregar_perfil(
        cuenta_id,
        nombre,
        pin
    )

    print(
        f"👤 Perfil agregado: "
        f"{nombre} | "
        f"Cuenta: {cuenta[2]}"
    )

    return jsonify({
        "ok": True,
        "mensaje": "Perfil agregado correctamente."
    })


# =========================================================
# EDITAR PERFIL
# =========================================================

@app.route(
    "/admin/perfil/<int:perfil_id>/editar",
    methods=["POST"]
)
@admin_required
def admin_editar_perfil(perfil_id):

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    nombre = datos.get(
        "nombre",
        ""
    ).strip()

    pin = datos.get(
        "pin",
        ""
    ).strip()

    if not nombre or not pin:

        return jsonify({
            "ok": False,
            "mensaje": "Nombre y PIN son obligatorios."
        }), 400

    actualizado = editar_perfil(
        perfil_id,
        nombre,
        pin
    )

    if not actualizado:

        return jsonify({
            "ok": False,
            "mensaje": "Perfil no encontrado."
        }), 404

    return jsonify({
        "ok": True,
        "mensaje": "Perfil actualizado."
    })


# =========================================================
# ACTIVAR / DESACTIVAR PERFIL
# =========================================================

@app.route(
    "/admin/perfil/<int:perfil_id>/estado",
    methods=["POST"]
)
@admin_required
def admin_estado_perfil(perfil_id):

    datos = request.get_json()

    if not datos:

        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    activo = datos.get(
        "activo"
    )

    if activo not in [0, 1]:

        return jsonify({
            "ok": False,
            "mensaje": "Estado inválido."
        }), 400

    actualizado = cambiar_estado_perfil(
        perfil_id,
        activo
    )

    if not actualizado:

        return jsonify({
            "ok": False,
            "mensaje": "Perfil no encontrado."
        }), 404

    return jsonify({
        "ok": True,
        "mensaje": "Estado actualizado."
    })


# =========================================================
# ELIMINAR PERFIL
# =========================================================

@app.route(
    "/admin/perfil/<int:perfil_id>/eliminar",
    methods=["POST"]
)
@admin_required
def admin_eliminar_perfil(perfil_id):

    eliminado = eliminar_perfil(
        perfil_id
    )

    if not eliminado:

        return jsonify({
            "ok": False,
            "mensaje": "Perfil no encontrado."
        }), 404

    return jsonify({
        "ok": True,
        "mensaje": "Perfil eliminado."
    })


# =========================================================
# INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("🎬 DISNEY+ ADMIN")
    print("========================================")
    print("🌐 http://127.0.0.1:5000")
    print("🔐 Admin: http://127.0.0.1:5000/admin")
    print("========================================")
    print()

    app.run(
        debug=True
    )