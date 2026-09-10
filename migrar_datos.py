import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception(
        "No se encontró DATABASE_URL. "
        "Agrega temporalmente la URL de PostgreSQL en el archivo .env"
    )

# Base local
sqlite_db = sqlite3.connect("disney.db")
sqlite_cursor = sqlite_db.cursor()

cuentas = sqlite_cursor.execute("""
    SELECT id, nombre, correo, estado
    FROM cuentas
    ORDER BY id
""").fetchall()

perfiles = sqlite_cursor.execute("""
    SELECT id, cuenta_id, nombre, pin, activo
    FROM perfiles
    ORDER BY id
""").fetchall()

print(f"Cuentas encontradas en SQLite: {len(cuentas)}")
print(f"Perfiles encontrados en SQLite: {len(perfiles)}")

# PostgreSQL
postgres = psycopg2.connect(DATABASE_URL)
cursor = postgres.cursor()

# Crear tablas si todavía no existen
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

# Evitar sobrescribir datos existentes
cursor.execute("SELECT COUNT(*) FROM cuentas")
cuentas_existentes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM perfiles")
perfiles_existentes = cursor.fetchone()[0]

if cuentas_existentes > 0 or perfiles_existentes > 0:
    postgres.rollback()
    postgres.close()
    sqlite_db.close()

    raise Exception(
        "La base PostgreSQL ya contiene datos. "
        "Migración cancelada para evitar duplicados."
    )

# Insertar cuentas conservando sus IDs originales
for cuenta in cuentas:
    cursor.execute("""
        INSERT INTO cuentas
        (id, nombre, correo, estado)
        VALUES (%s, %s, %s, %s)
    """, cuenta)

# Insertar perfiles conservando sus IDs originales
for perfil in perfiles:
    cursor.execute("""
        INSERT INTO perfiles
        (id, cuenta_id, nombre, pin, activo)
        VALUES (%s, %s, %s, %s, %s)
    """, perfil)

# Actualizar los contadores de IDs de PostgreSQL
if cuentas:
    cursor.execute("""
        SELECT setval(
            pg_get_serial_sequence('cuentas', 'id'),
            (SELECT MAX(id) FROM cuentas)
        )
    """)

if perfiles:
    cursor.execute("""
        SELECT setval(
            pg_get_serial_sequence('perfiles', 'id'),
            (SELECT MAX(id) FROM perfiles)
        )
    """)

postgres.commit()

cursor.close()
postgres.close()
sqlite_db.close()

print("✅ Migración completada correctamente.")
print(f"✅ Cuentas migradas: {len(cuentas)}")
print(f"✅ Perfiles migrados: {len(perfiles)}")