import os
import sqlite3
from datetime import date

try:
    import psycopg2
except ImportError:
    psycopg2 = None


# =========================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =========================================================

def es_postgresql():
    """
    Render utiliza PostgreSQL mediante DATABASE_URL.
    En local, si no existe DATABASE_URL, se utiliza SQLite.
    """
    return bool(os.environ.get("DATABASE_URL"))


def conectar():
    """
    Crea una conexión a PostgreSQL o SQLite.
    """

    if es_postgresql():
        if psycopg2 is None:
            raise Exception(
                " psycopg2 no está instalado. "
                "Agrega psycopg2-binary en requirements.txt"
            )

        database_url = os.environ.get("DATABASE_URL")

        conexion = psycopg2.connect(database_url)
        return conexion

    # Base de datos local
    conexion = sqlite3.connect("disney_bot.db")
    return conexion


def adaptar_consulta(consulta):
    """
    PostgreSQL utiliza %s como marcador.
    SQLite utiliza ?.
    """

    if es_postgresql():
        return consulta.replace("?", "%s")

    return consulta


# =========================================================
# CREACIÓN DE TABLAS
# =========================================================

def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    if es_postgresql():

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                id SERIAL PRIMARY KEY,
                correo TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL,
                pais TEXT DEFAULT 'Perú',
                activa INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfiles (
                id SERIAL PRIMARY KEY,
                cuenta_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                pin TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (cuenta_id)
                    REFERENCES cuentas(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitudes_perfil (
                perfil_id INTEGER PRIMARY KEY,
                fecha TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (perfil_id)
                    REFERENCES perfiles(id)
                    ON DELETE CASCADE
            )
        """)

    else:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correo TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL,
                pais TEXT DEFAULT 'Perú',
                activa INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuenta_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                pin TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (cuenta_id)
                    REFERENCES cuentas(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitudes_perfil (
                perfil_id INTEGER PRIMARY KEY,
                fecha TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (perfil_id)
                    REFERENCES perfiles(id)
                    ON DELETE CASCADE
            )
        """)

    conexion.commit()
    conexion.close()


# =========================================================
# CUENTAS
# =========================================================

def agregar_cuenta(correo, contrasena, pais="Perú"):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        INSERT INTO cuentas (correo, contrasena, pais, activa)
        VALUES (?, ?, ?, 1)
    """)

    try:
        cursor.execute(
            consulta,
            (correo, contrasena, pais)
        )

        conexion.commit()

        resultado = True

    except Exception as error:
        print("Error al agregar cuenta:", error)
        conexion.rollback()
        resultado = False

    conexion.close()

    return resultado


def obtener_cuentas():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, correo, contrasena, pais, activa
        FROM cuentas
        ORDER BY id DESC
    """)

    cuentas = cursor.fetchall()

    conexion.close()

    return cuentas


def obtener_cuenta(cuenta_id):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT id, correo, contrasena, pais, activa
        FROM cuentas
        WHERE id = ?
    """)

    cursor.execute(consulta, (cuenta_id,))

    cuenta = cursor.fetchone()

    conexion.close()

    return cuenta


# =========================================================
# PERFILES
# =========================================================

def agregar_perfil(cuenta_id, nombre, pin):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        INSERT INTO perfiles (
            cuenta_id,
            nombre,
            pin,
            activo
        )
        VALUES (?, ?, ?, 1)
    """)

    try:
        cursor.execute(
            consulta,
            (cuenta_id, nombre, pin)
        )

        conexion.commit()

        resultado = True

    except Exception as error:
        print("Error al agregar perfil:", error)
        conexion.rollback()
        resultado = False

    conexion.close()

    return resultado


def obtener_perfiles(cuenta_id=None):
    conexion = conectar()
    cursor = conexion.cursor()

    if cuenta_id is not None:

        consulta = adaptar_consulta("""
            SELECT
                perfiles.id,
                perfiles.cuenta_id,
                perfiles.nombre,
                perfiles.pin,
                perfiles.activo,
                cuentas.correo
            FROM perfiles
            INNER JOIN cuentas
                ON perfiles.cuenta_id = cuentas.id
            WHERE perfiles.cuenta_id = ?
            ORDER BY perfiles.id DESC
        """)

        cursor.execute(consulta, (cuenta_id,))

    else:

        cursor.execute("""
            SELECT
                perfiles.id,
                perfiles.cuenta_id,
                perfiles.nombre,
                perfiles.pin,
                perfiles.activo,
                cuentas.correo
            FROM perfiles
            INNER JOIN cuentas
                ON perfiles.cuenta_id = cuentas.id
            ORDER BY perfiles.id DESC
        """)

    perfiles = cursor.fetchall()

    conexion.close()

    return perfiles


def verificar_perfil(nombre, pin):
    """
    Verifica si existe un perfil activo con ese nombre y PIN.

    Devuelve:
    (
        perfil_id,
        cuenta_id,
        nombre,
        pin,
        activo,
        correo_cuenta
    )
    """

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT
            perfiles.id,
            perfiles.cuenta_id,
            perfiles.nombre,
            perfiles.pin,
            perfiles.activo,
            cuentas.correo
        FROM perfiles
        INNER JOIN cuentas
            ON perfiles.cuenta_id = cuentas.id
        WHERE LOWER(perfiles.nombre) = LOWER(?)
          AND perfiles.pin = ?
          AND perfiles.activo = 1
          AND cuentas.activa = 1
    """)

    cursor.execute(
        consulta,
        (nombre, pin)
    )

    perfil = cursor.fetchone()

    conexion.close()

    return perfil


def editar_perfil(perfil_id, nombre, pin):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        UPDATE perfiles
        SET nombre = ?, pin = ?
        WHERE id = ?
    """)

    try:
        cursor.execute(
            consulta,
            (nombre, pin, perfil_id)
        )

        conexion.commit()

        resultado = True

    except Exception as error:
        print("Error al editar perfil:", error)
        conexion.rollback()
        resultado = False

    conexion.close()

    return resultado


def cambiar_estado_perfil(perfil_id, activo):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        UPDATE perfiles
        SET activo = ?
        WHERE id = ?
    """)

    try:
        cursor.execute(
            consulta,
            (activo, perfil_id)
        )

        conexion.commit()

        resultado = True

    except Exception as error:
        print("Error al cambiar estado del perfil:", error)
        conexion.rollback()
        resultado = False

    conexion.close()

    return resultado


def eliminar_perfil(perfil_id):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        DELETE FROM perfiles
        WHERE id = ?
    """)

    try:
        cursor.execute(
            consulta,
            (perfil_id,)
        )

        conexion.commit()

        resultado = True

    except Exception as error:
        print("Error al eliminar perfil:", error)
        conexion.rollback()
        resultado = False

    conexion.close()

    return resultado


# =========================================================
# LÍMITE DIARIO DE SOLICITUDES POR PERFIL
# =========================================================

def obtener_estado_solicitudes(perfil_id, limite=3):
    """
    Obtiene cuántas solicitudes ha realizado un perfil
    durante el día actual.

    El contador se reinicia automáticamente cuando cambia
    la fecha.
    """

    hoy = date.today().isoformat()

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT fecha, cantidad
        FROM solicitudes_perfil
        WHERE perfil_id = ?
    """)

    cursor.execute(consulta, (perfil_id,))

    registro = cursor.fetchone()

    conexion.close()

    # El perfil todavía no tiene registros
    if registro is None:
        return {
            "permitido": True,
            "cantidad": 0,
            "restantes": limite
        }

    fecha_registro = registro[0]
    cantidad_registro = int(registro[1])

    # Si la fecha cambió, el contador comienza nuevamente
    if fecha_registro != hoy:
        cantidad_registro = 0

    restantes = max(0, limite - cantidad_registro)

    return {
        "permitido": cantidad_registro < limite,
        "cantidad": cantidad_registro,
        "restantes": restantes
    }


def registrar_solicitud(perfil_id, limite=3):
    """
    Registra una solicitud para un perfil.

    Retorna:
    {
        "permitido": True/False,
        "cantidad": cantidad_usada_hoy,
        "restantes": solicitudes_restantes
    }
    """

    hoy = date.today().isoformat()

    conexion = conectar()
    cursor = conexion.cursor()

    consulta_select = adaptar_consulta("""
        SELECT fecha, cantidad
        FROM solicitudes_perfil
        WHERE perfil_id = ?
    """)

    cursor.execute(
        consulta_select,
        (perfil_id,)
    )

    registro = cursor.fetchone()

    try:

        if registro is None:
            # Primera solicitud del perfil
            nueva_cantidad = 1

            consulta_insert = adaptar_consulta("""
                INSERT INTO solicitudes_perfil (
                    perfil_id,
                    fecha,
                    cantidad
                )
                VALUES (?, ?, ?)
            """)

            cursor.execute(
                consulta_insert,
                (
                    perfil_id,
                    hoy,
                    nueva_cantidad
                )
            )

        else:

            fecha_registro = registro[0]
            cantidad_registro = int(registro[1])

            # Si es un día nuevo, reiniciamos el contador
            if fecha_registro != hoy:
                cantidad_registro = 0

            # Ya alcanzó el límite
            if cantidad_registro >= limite:
                conexion.close()

                return {
                    "permitido": False,
                    "cantidad": cantidad_registro,
                    "restantes": 0
                }

            nueva_cantidad = cantidad_registro + 1

            consulta_update = adaptar_consulta("""
                UPDATE solicitudes_perfil
                SET fecha = ?, cantidad = ?
                WHERE perfil_id = ?
            """)

            cursor.execute(
                consulta_update,
                (
                    hoy,
                    nueva_cantidad,
                    perfil_id
                )
            )

        conexion.commit()
        conexion.close()

        return {
            "permitido": True,
            "cantidad": nueva_cantidad,
            "restantes": max(0, limite - nueva_cantidad)
        }

    except Exception as error:

        print("Error al registrar solicitud:", error)

        conexion.rollback()
        conexion.close()

        return {
            "permitido": False,
            "cantidad": 0,
            "restantes": 0,
            "error": str(error)
        }