import sqlite3

conexion = sqlite3.connect("usuarios.db")
cursor = conexion.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL UNIQUE,
        correo TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
""")

conexion.commit()
conexion.close()
print("Base de datos creada correctamente")
