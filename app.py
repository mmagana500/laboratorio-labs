import re
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB = "usuarios.db"
LOG_EVENTOS = "eventos.log"


# ---------- Registro de eventos de seguridad ----------
def registrar_evento(evento, usuario):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_EVENTOS, "a", encoding="utf-8") as archivo:
        archivo.write(f"{fecha},{evento},{usuario}\n")


# ---------- Reglas de validación ----------
def validar_usuario(usuario):
    if len(usuario) < 4 or len(usuario) > 20:
        return False
    return re.fullmatch(r"[A-Za-z0-9_]+", usuario) is not None


def validar_correo(correo):
    patron = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return re.fullmatch(patron, correo) is not None


def validar_password(password):
    return len(password) >= 8


# ---------- Rutas ----------
@app.route("/")
def inicio():
    return "Laboratorio de Ciberseguridad"


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        # Normalización: solo se recortan extremos (la contraseña conserva sus espacios internos)
        usuario = request.form["usuario"].strip()
        correo = request.form["correo"].strip()
        password = request.form["password"].strip()

        if not validar_usuario(usuario):
            return "Usuario inválido: 4 a 20 caracteres, solo letras, números y guion bajo"

        if not validar_correo(correo):
            return "Correo electrónico inválido"

        if not validar_password(password):
            return "Contraseña inválida: mínimo 8 caracteres"

        password_hash = generate_password_hash(password)

        conexion = sqlite3.connect(DB)
        cursor = conexion.cursor()

        # Verificar duplicados (consulta parametrizada)
        cursor.execute(
            "SELECT id FROM usuarios WHERE usuario = ? OR correo = ?",
            (usuario, correo),
        )
        if cursor.fetchone():
            conexion.close()
            return "El usuario o el correo ya está registrado"

        cursor.execute(
            "INSERT INTO usuarios (usuario, correo, password) VALUES (?, ?, ?)",
            (usuario, correo, password_hash),
        )
        conexion.commit()
        conexion.close()
        return "Usuario registrado"

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        password = request.form["password"].strip()

        conexion = sqlite3.connect(DB)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT password FROM usuarios WHERE usuario = ?",
            (usuario,),
        )
        resultado = cursor.fetchone()
        conexion.close()

        if resultado and check_password_hash(resultado[0], password):
            registrar_evento("LOGIN_CORRECTO", usuario)
            return "Inicio de sesión correcto"

        registrar_evento("LOGIN_FALLIDO", usuario)
        return "Credenciales incorrectas"

    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
