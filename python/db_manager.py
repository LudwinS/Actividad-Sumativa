import sqlite3

DB_NAME = "gastos.db"

# -------------------- Conexión --------------------
def get_connection():
    return sqlite3.connect(DB_NAME)

# -------------------- Crear Tablas --------------------
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        ingreso REAL NOT NULL,
        ahorro_porcentaje REAL NOT NULL
    )
    """)

    # Tabla de gastos fijos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos_fijos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        monto REAL NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)

    # Tabla de gastos variables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos_variables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        monto REAL NOT NULL,
        fecha TEXT NOT NULL,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )
    """)

    conn.commit()
    conn.close()


# -------------------- CRUD USUARIOS --------------------
def insert_usuario(nombre, ingreso, ahorro_porcentaje):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO usuarios (nombre, ingreso, ahorro_porcentaje)
    VALUES (?, ?, ?)
    """, (nombre, ingreso, ahorro_porcentaje))
    conn.commit()
    conn.close()

# Nuevo: inserta y devuelve id
def insert_usuario_return_id(nombre, ingreso, ahorro_porcentaje):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO usuarios (nombre, ingreso, ahorro_porcentaje)
    VALUES (?, ?, ?)
    """, (nombre, ingreso, ahorro_porcentaje))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_usuario(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def get_usuario_por_nombre(nombre):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nombre = ?", (nombre,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def update_usuario(usuario_id, nombre, ingreso, ahorro_porcentaje):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE usuarios
    SET nombre = ?, ingreso = ?, ahorro_porcentaje = ?
    WHERE id = ?
    """, (nombre, ingreso, ahorro_porcentaje, usuario_id))
    conn.commit()
    conn.close()

def delete_usuario(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()


# -------------------- CRUD GASTOS FIJOS --------------------
def insert_gasto_fijo(usuario_id, categoria, monto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO gastos_fijos (usuario_id, categoria, monto)
    VALUES (?, ?, ?)
    """, (usuario_id, categoria, monto))
    conn.commit()
    conn.close()

def get_gastos_fijos(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gastos_fijos WHERE usuario_id = ?", (usuario_id,))
    gastos = cursor.fetchall()
    conn.close()
    return gastos

def total_gastos_fijos(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(monto),0) FROM gastos_fijos WHERE usuario_id = ?", (usuario_id,))
    s = cursor.fetchone()[0]
    conn.close()
    return s

def update_gasto_fijo(gasto_id, categoria, monto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE gastos_fijos
    SET categoria = ?, monto = ?
    WHERE id = ?
    """, (categoria, monto, gasto_id))
    conn.commit()
    conn.close()

def delete_gasto_fijo(gasto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos_fijos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()


# -------------------- CRUD GASTOS VARIABLES --------------------
def insert_gasto_variable(usuario_id, categoria, monto, fecha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO gastos_variables (usuario_id, categoria, monto, fecha)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, categoria, monto, fecha))
    conn.commit()
    conn.close()

def get_gastos_variables(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gastos_variables WHERE usuario_id = ?", (usuario_id,))
    gastos = cursor.fetchall()
    conn.close()
    return gastos

def total_gastos_variables(usuario_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(monto),0) FROM gastos_variables WHERE usuario_id = ?", (usuario_id,))
    s = cursor.fetchone()[0]
    conn.close()
    return s

def update_gasto_variable(gasto_id, categoria, monto, fecha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE gastos_variables
    SET categoria = ?, monto = ?, fecha = ?
    WHERE id = ?
    """, (categoria, monto, fecha, gasto_id))
    conn.commit()
    conn.close()

def delete_gasto_variable(gasto_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos_variables WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()


def get_all_usuarios():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Crear las tablas al importar el módulo y crear la conexión
get_connection()
create_tables()