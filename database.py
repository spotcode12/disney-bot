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
                "psycopg2 no está instalado. "
                "Agrega psycopg2-binary en requirements.txt"
            )

        database_url = os.environ.get("DATABASE_URL")

        conexion = psycopg2.connect(database_url)

        return conexion

    # Base de datos local
    conexion = sqlite3.connect("disney_bot.db")

    # Activar claves foráneas en SQLite
    conexion.execute("PRAGMA foreign_keys = ON")

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
# CREACIÓN Y ACTUALIZACIÓN DE TABLAS
# =========================================================

def crear_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    try:

        if es_postgresql():

            # -------------------------------------------------
            # TABLA CUENTAS
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cuentas (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    correo TEXT NOT NULL UNIQUE,
                    estado TEXT DEFAULT 'Activa',
                    contrasena TEXT DEFAULT '',
                    pais TEXT DEFAULT 'Perú',
                    activa INTEGER DEFAULT 1
                )
            """)

            # Agregar columnas faltantes en instalaciones antiguas
            cursor.execute("""
                ALTER TABLE cuentas
                ADD COLUMN IF NOT EXISTS nombre TEXT
            """)

            cursor.execute("""
                ALTER TABLE cuentas
                ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'Activa'
            """)

            cursor.execute("""
                ALTER TABLE cuentas
                ADD COLUMN IF NOT EXISTS contrasena TEXT DEFAULT ''
            """)

            cursor.execute("""
                ALTER TABLE cuentas
                ADD COLUMN IF NOT EXISTS pais TEXT DEFAULT 'Perú'
            """)

            cursor.execute("""
                ALTER TABLE cuentas
                ADD COLUMN IF NOT EXISTS activa INTEGER DEFAULT 1
            """)

            # -------------------------------------------------
            # TABLA PERFILES
            # -------------------------------------------------

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

            # -------------------------------------------------
            # TABLA DE SOLICITUDES DIARIAS
            # -------------------------------------------------

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

            # -------------------------------------------------
            # TABLA CUENTAS PARA SQLITE
            # -------------------------------------------------

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cuentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT,
                    correo TEXT NOT NULL UNIQUE,
                    estado TEXT DEFAULT 'Activa',
                    contrasena TEXT DEFAULT '',
                    pais TEXT DEFAULT 'Perú',
                    activa INTEGER DEFAULT 1
                )
            """)

            # -------------------------------------------------
            # TABLA PERFILES PARA SQLITE
            # -------------------------------------------------

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

            # -------------------------------------------------
            # TABLA DE SOLICITUDES DIARIAS
            # -------------------------------------------------

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

            # Migración sencilla para bases SQLite antiguas
            cursor.execute("""
                PRAGMA table_info(cuentas)
            """)

            columnas = [
                fila[1]
                for fila in cursor.fetchall()
            ]

            if "nombre" not in columnas:
                cursor.execute("""
                    ALTER TABLE cuentas
                    ADD COLUMN nombre TEXT
                """)

            if "estado" not in columnas:
                cursor.execute("""
                    ALTER TABLE cuentas
                    ADD COLUMN estado TEXT DEFAULT 'Activa'
                """)

            if "contrasena" not in columnas:
                cursor.execute("""
                    ALTER TABLE cuentas
                    ADD COLUMN contrasena TEXT DEFAULT ''
                """)

            if "pais" not in columnas:
                cursor.execute("""
                    ALTER TABLE cuentas
                    ADD COLUMN pais TEXT DEFAULT 'Perú'
                """)

            if "activa" not in columnas:
                cursor.execute("""
                    ALTER TABLE cuentas
                    ADD COLUMN activa INTEGER DEFAULT 1
                """)

        conexion.commit()

    except Exception as error:

        print("Error al crear o actualizar tablas:", error)

        conexion.rollback()

    finally:

        cursor.close()
        conexion.close()


# =========================================================
# CUENTAS
# =========================================================

def agregar_cuenta(
    nombre,
    correo,
    estado="Activa",
    contrasena="",
    pais="Perú"
):
    """
    Agrega una cuenta.

    Se mantiene el formato compatible con el panel:
    agregar_cuenta(nombre, correo, estado)
    """

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        INSERT INTO cuentas (
            nombre,
            correo,
            estado,
            contrasena,
            pais,
            activa
        )
        VALUES (?, ?, ?, ?, ?, 1)
    """)

    try:

        cursor.execute(
            consulta,
            (
                nombre,
                correo,
                estado,
                contrasena,
                pais
            )
        )

        conexion.commit()

        resultado = True

    except Exception as error:

        print("Error al agregar cuenta:", error)

        conexion.rollback()

        resultado = False

    finally:

        cursor.close()
        conexion.close()

    return resultado


def obtener_cuentas():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            correo,
            estado
        FROM cuentas
        ORDER BY id DESC
    """)

    cuentas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return cuentas


def obtener_cuenta(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT
            id,
            nombre,
            correo,
            estado
        FROM cuentas
        WHERE id = ?
    """)

    cursor.execute(
        consulta,
        (cuenta_id,)
    )

    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return cuenta


def obtener_datos_cuenta(cuenta_id):

    """
    Devuelve todos los datos internos de una cuenta.
    Esta función es independiente de obtener_cuenta(),
    que conserva el formato usado por el panel.
    """

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT
            id,
            nombre,
            correo,
            estado,
            contrasena,
            pais,
            activa
        FROM cuentas
        WHERE id = ?
    """)

    cursor.execute(
        consulta,
        (cuenta_id,)
    )

    cuenta = cursor.fetchone()

    cursor.close()
    conexion.close()

    return cuenta


def cambiar_estado_cuenta(cuenta_id, estado, activa=1):

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        UPDATE cuentas
        SET estado = ?, activa = ?
        WHERE id = ?
    """)

    try:

        cursor.execute(
            consulta,
            (
                estado,
                activa,
                cuenta_id
            )
        )

        conexion.commit()

        resultado = True

    except Exception as error:

        print("Error al cambiar estado de cuenta:", error)

        conexion.rollback()

        resultado = False

    finally:

        cursor.close()
        conexion.close()

    return resultado


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
            (
                cuenta_id,
                nombre,
                pin
            )
        )

        conexion.commit()

        resultado = True

    except Exception as error:

        print("Error al agregar perfil:", error)

        conexion.rollback()

        resultado = False

    finally:

        cursor.close()
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

        cursor.execute(
            consulta,
            (cuenta_id,)
        )

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

    cursor.close()
    conexion.close()

    return perfiles


def obtener_perfil(perfil_id):

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
        WHERE perfiles.id = ?
    """)

    cursor.execute(
        consulta,
        (perfil_id,)
    )

    perfil = cursor.fetchone()

    cursor.close()
    conexion.close()

    return perfil


def verificar_perfil(nombre, pin):
    """
    Verifica si existe un perfil activo con ese nombre y PIN.

    Devuelve exactamente este orden:

    perfil[0] = ID del perfil
    perfil[1] = ID de la cuenta
    perfil[2] = Nombre del perfil
    perfil[3] = PIN
    perfil[4] = Estado del perfil
    perfil[5] = Correo de la cuenta
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
        (
            nombre,
            pin
        )
    )

    perfil = cursor.fetchone()

    cursor.close()
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
            (
                nombre,
                pin,
                perfil_id
            )
        )

        conexion.commit()

        resultado = True

    except Exception as error:

        print("Error al editar perfil:", error)

        conexion.rollback()

        resultado = False

    finally:

        cursor.close()
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
            (
                activo,
                perfil_id
            )
        )

        conexion.commit()

        resultado = True

    except Exception as error:

        print("Error al cambiar estado del perfil:", error)

        conexion.rollback()

        resultado = False

    finally:

        cursor.close()
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

    finally:

        cursor.close()
        conexion.close()

    return resultado


# =========================================================
# LÍMITE DIARIO DE SOLICITUDES POR PERFIL
# =========================================================

def obtener_estado_solicitudes(perfil_id, limite=3):
    """
    Obtiene cuántas solicitudes ha realizado un perfil
    durante el día actual.

    El contador se reinicia automáticamente al cambiar
    la fecha.
    """

    hoy = date.today().isoformat()

    conexion = conectar()
    cursor = conexion.cursor()

    consulta = adaptar_consulta("""
        SELECT
            fecha,
            cantidad
        FROM solicitudes_perfil
        WHERE perfil_id = ?
    """)

    cursor.execute(
        consulta,
        (perfil_id,)
    )

    registro = cursor.fetchone()

    cursor.close()
    conexion.close()

    # El perfil todavía no tiene registros
    if registro is None:

        return {
            "permitido": True,
            "cantidad": 0,
            "restantes": limite,
            "limite": limite
        }

    fecha_registro = str(registro[0])
    cantidad_registro = int(registro[1])

    # Si cambió el día, el contador se reinicia
    if fecha_registro != hoy:
        cantidad_registro = 0

    restantes = max(
        0,
        limite - cantidad_registro
    )

    return {
        "permitido": cantidad_registro < limite,
        "cantidad": cantidad_registro,
        "restantes": restantes,
        "limite": limite
    }


def registrar_solicitud(perfil_id, limite=3):
    """
    Registra una solicitud exitosa para un perfil.

    Retorna:

    {
        "permitido": True/False,
        "cantidad": cantidad_usada_hoy,
        "restantes": solicitudes_restantes,
        "limite": limite
    }
    """

    hoy = date.today().isoformat()

    conexion = conectar()
    cursor = conexion.cursor()

    consulta_select = adaptar_consulta("""
        SELECT
            fecha,
            cantidad
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

            fecha_registro = str(registro[0])
            cantidad_registro = int(registro[1])

            # Si es un nuevo día, reiniciar contador
            if fecha_registro != hoy:
                cantidad_registro = 0

            # Ya alcanzó el límite
            if cantidad_registro >= limite:

                conexion.rollback()

                return {
                    "permitido": False,
                    "cantidad": cantidad_registro,
                    "restantes": 0,
                    "limite": limite
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

        return {
            "permitido": True,
            "cantidad": nueva_cantidad,
            "restantes": max(
                0,
                limite - nueva_cantidad
            ),
            "limite": limite
        }

    except Exception as error:

        print("Error al registrar solicitud:", error)

        conexion.rollback()

        return {
            "permitido": False,
            "cantidad": 0,
            "restantes": 0,
            "limite": limite,
            "error": str(error)
        }

    finally:

        cursor.close()
        conexion.close()