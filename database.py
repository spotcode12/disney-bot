import sqlite3


DB_NAME = "disney.db"


def conectar():
    return sqlite3.connect(DB_NAME)


def crear_tablas():

    conexion = conectar()
    cursor = conexion.cursor()

    # Tabla de cuentas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    # Tabla de perfiles
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


def agregar_cuenta(nombre, correo):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO cuentas
        (nombre, correo, estado)
        VALUES (?, ?, ?)
    """, (nombre, correo, "activa"))

    conexion.commit()
    conexion.close()

def editar_cuenta(cuenta_id, nombre, correo):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE cuentas
        SET nombre = ?, correo = ?
        WHERE id = ?
    """, (nombre, correo, cuenta_id))

    actualizado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return actualizado


def eliminar_cuenta(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    # Primero eliminamos los perfiles de esa cuenta
    cursor.execute("""
        DELETE FROM perfiles
        WHERE cuenta_id = ?
    """, (cuenta_id,))

    # Luego eliminamos la cuenta
    cursor.execute("""
        DELETE FROM cuentas
        WHERE id = ?
    """, (cuenta_id,))

    eliminado = cursor.rowcount > 0

    conexion.commit()
    conexion.close()

    return eliminado


def agregar_perfil(cuenta_id, nombre, pin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO perfiles
        (cuenta_id, nombre, pin, activo)
        VALUES (?, ?, ?, ?)
    """, (cuenta_id, nombre, pin, 1))

    conexion.commit()
    conexion.close()


def obtener_cuentas():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, correo, estado
        FROM cuentas
        ORDER BY id
    """)

    cuentas = cursor.fetchall()

    conexion.close()

    return cuentas


def obtener_cuenta(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, correo, estado
        FROM cuentas
        WHERE id = ?
    """, (cuenta_id,))

    cuenta = cursor.fetchone()

    conexion.close()

    return cuenta


def obtener_perfiles(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            nombre,
            pin,
            activo
        FROM perfiles
        WHERE cuenta_id = ?
        ORDER BY id
    """, (cuenta_id,))

    perfiles = cursor.fetchall()

    conexion.close()

    return perfiles


def obtener_perfil(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            id,
            cuenta_id,
            nombre,
            pin,
            activo
        FROM perfiles
        WHERE id = ?
    """, (perfil_id,))

    perfil = cursor.fetchone()

    conexion.close()

    return perfil


def editar_perfil(perfil_id, nombre, pin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE perfiles
        SET nombre = ?,
            pin = ?
        WHERE id = ?
    """, (nombre, pin, perfil_id))

    conexion.commit()

    filas_modificadas = cursor.rowcount

    conexion.close()

    return filas_modificadas > 0


def cambiar_estado_perfil(perfil_id, activo):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE perfiles
        SET activo = ?
        WHERE id = ?
    """, (activo, perfil_id))

    conexion.commit()

    filas_modificadas = cursor.rowcount

    conexion.close()

    return filas_modificadas > 0


def eliminar_perfil(perfil_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM perfiles
        WHERE id = ?
    """, (perfil_id,))

    conexion.commit()

    filas_eliminadas = cursor.rowcount

    conexion.close()

    return filas_eliminadas > 0


def verificar_perfil(nombre, pin):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
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
    """, (nombre, pin))

    perfil = cursor.fetchone()

    conexion.close()

    return perfil

def obtener_cuenta(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, correo, estado
        FROM cuentas
        WHERE id = ?
    """, (cuenta_id,))

    cuenta = cursor.fetchone()

    conexion.close()

    return cuenta


def editar_cuenta(cuenta_id, nombre, correo):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE cuentas
        SET nombre = ?, correo = ?
        WHERE id = ?
    """, (nombre, correo, cuenta_id))

    filas = cursor.rowcount

    conexion.commit()
    conexion.close()

    return filas > 0


def eliminar_cuenta(cuenta_id):

    conexion = conectar()
    cursor = conexion.cursor()

    # Primero eliminamos los perfiles asociados
    cursor.execute("""
        DELETE FROM perfiles
        WHERE cuenta_id = ?
    """, (cuenta_id,))

    # Luego eliminamos la cuenta
    cursor.execute("""
        DELETE FROM cuentas
        WHERE id = ?
    """, (cuenta_id,))

    filas = cursor.rowcount

    conexion.commit()
    conexion.close()

    return filas > 0
if __name__ == "__main__":

    crear_tablas()

    print("✅ Tablas creadas correctamente.")

    print("\n📋 Cuentas actuales:")

    for cuenta in obtener_cuentas():
        print(cuenta)