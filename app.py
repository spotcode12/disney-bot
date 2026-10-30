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

    datos = request.get_json(
        silent=True
    )

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
