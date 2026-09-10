import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    """
    En Render utiliza PostgreSQL.
    En la PC utiliza SQLite.
    """
    if DATABASE_URL:
        import psycopg2

        conexion = psycopg2.connect(DATABASE_URL)
        return conexion

    conexion = sqlite3.connect("disney.db")
    return conexion


def es_postgresql():
    return bool(DATABASE_URL)


def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()

    if es_postgresql():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                estado TEXT NOT NULL
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
            )
        """)

    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                estado TEXT NOT NULL
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
            )
        """)

    conexion.commit()
    conexion.close()


def ejecutar_consulta(consulta, parametros=(), fetchone=False, fetchall=False):
    """
    Ejecuta consultas utilizando el formato correcto
    para SQLite o PostgreSQL.
    """
    conexion = conectar()
    cursor = conexion.cursor()

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, parametros)

    resultado = None

    if fetchone:
        resultado = cursor.fetchone()
    elif fetchall:
        resultado = cursor.fetchall()

    conexion.commit()
    conexion.close()

    return resultado


def agregar_cuenta(nombre, correo):
    ejecutar_consulta("""
        INSERT INTO cuentas
        (nombre, correo, estado)
        VALUES (?, ?, ?)
    """, (nombre, correo, "activa"))


def editar_cuenta(cuenta_id, nombre, correo):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = """
        UPDATE cuentas
        SET nombre = ?, correo = ?
        WHERE id = ?
    """

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, (nombre, correo, cuenta_id))
    actualizado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return actualizado


def eliminar_cuenta(cuenta_id):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta_perfiles = """
        DELETE FROM perfiles
        WHERE cuenta_id = ?
    """

    consulta_cuenta = """
        DELETE FROM cuentas
        WHERE id = ?
    """

    if es_postgresql():
        consulta_perfiles = consulta_perfiles.replace("?", "%s")
        consulta_cuenta = consulta_cuenta.replace("?", "%s")

    cursor.execute(consulta_perfiles, (cuenta_id,))
    cursor.execute(consulta_cuenta, (cuenta_id,))

    eliminado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return eliminado


def agregar_perfil(cuenta_id, nombre, pin):
    ejecutar_consulta("""
        INSERT INTO perfiles
        (cuenta_id, nombre, pin, activo)
        VALUES (?, ?, ?, ?)
    """, (cuenta_id, nombre, pin, 1))


def obtener_cuentas():
    return ejecutar_consulta("""
        SELECT id, nombre, correo, estado
        FROM cuentas
        ORDER BY id
    """, fetchall=True)


def obtener_cuenta(cuenta_id):
    return ejecutar_consulta("""
        SELECT id, nombre, correo, estado
        FROM cuentas
        WHERE id = ?
    """, (cuenta_id,), fetchone=True)


def obtener_perfiles(cuenta_id):
    return ejecutar_consulta("""
        SELECT id, nombre, pin, activo
        FROM perfiles
        WHERE cuenta_id = ?
        ORDER BY id
    """, (cuenta_id,), fetchall=True)


def obtener_perfil(perfil_id):
    return ejecutar_consulta("""
        SELECT id, cuenta_id, nombre, pin, activo
        FROM perfiles
        WHERE id = ?
    """, (perfil_id,), fetchone=True)


def editar_perfil(perfil_id, nombre, pin):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = """
        UPDATE perfiles
        SET nombre = ?,
            pin = ?
        WHERE id = ?
    """

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, (nombre, pin, perfil_id))
    actualizado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return actualizado


def cambiar_estado_perfil(perfil_id, activo):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = """
        UPDATE perfiles
        SET activo = ?
        WHERE id = ?
    """

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, (activo, perfil_id))
    actualizado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return actualizado


def eliminar_perfil(perfil_id):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = """
        DELETE FROM perfiles
        WHERE id = ?
    """

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, (perfil_id,))
    eliminado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return eliminado


def verificar_perfil(nombre, pin):
    conexion = conectar()
    cursor = conexion.cursor()

    consulta = """
        SELECT
            perfiles.id,
            perfiles.cuenta_id,
            perfiles.nombre,
            cuentas.correo
        FROM perfiles
        INNER JOIN cuentas
            ON perfiles.cuenta_id = cuentas.id
        WHERE perfiles.nombre = ?
        AND perfiles.pin = ?
        AND perfiles.activo = 1
        AND cuentas.estado = 'activa'
    """

    if es_postgresql():
        consulta = consulta.replace("?", "%s")

    cursor.execute(consulta, (nombre, pin))
    perfil = cursor.fetchone()

    conexion.close()

    return perfil


if __name__ == "__main__":
    crear_tablas()
    print("✅ Tablas creadas correctamente.")

    print("\n📋 Cuentas actuales:")

    for cuenta in obtener_cuentas():
        print(cuenta)