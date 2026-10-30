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
