#!/usr/bin/env python3
"""
Sistema de Gestión de Tareas con API y Base de Datos
PFO 2 - Programación sobre Redes
"""

import sqlite3
import hashlib
import secrets
from functools import wraps
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-para-el-tp'

DB_FILE = 'tareas.db'
tokens_sesion = {}  # {token: usuario}


# ============================================
# FUNCIONES AUXILIARES
# ============================================
def hash_contraseña(contraseña: str) -> str:
    return hashlib.sha256(contraseña.encode()).hexdigest()


def verificar_contraseña(contraseña: str, hash_almacenado: str) -> bool:
    return hash_contraseña(contraseña) == hash_almacenado


def generar_token() -> str:
    return secrets.token_hex(32)


def validar_token(token: str) -> str:
    return tokens_sesion.get(token)


def requiere_autenticacion(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token requerido'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        usuario = validar_token(token)
        if not usuario:
            return jsonify({'error': 'Token inválido'}), 401
        return f(usuario=usuario, *args, **kwargs)
    return decorador


# ============================================
# BASE DE DATOS
# ============================================
def inicializar_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                contraseña_hash TEXT NOT NULL,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                estado TEXT DEFAULT 'pendiente',
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    print(" Base de datos lista")


# ============================================
# ENDPOINTS
# ============================================
@app.route('/')
def home():
    return jsonify({'mensaje': 'API de Tareas funcionando'})


@app.route('/registro', methods=['POST'])
def registro():
    datos = request.get_json()
    usuario = datos.get('usuario')
    contraseña = datos.get('contraseña')

    if not usuario or not contraseña:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
    if len(usuario) < 3:
        return jsonify({'error': 'Usuario debe tener al menos 3 caracteres'}), 400
    if len(contraseña) < 4:
        return jsonify({'error': 'Contraseña debe tener al menos 4 caracteres'}), 400

    hash_pass = hash_contraseña(contraseña)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute('INSERT INTO usuarios (usuario, contraseña_hash) VALUES (?, ?)',
                         (usuario, hash_pass))
        return jsonify({'mensaje': 'Usuario registrado', 'usuario': usuario}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'El usuario ya existe'}), 400


@app.route('/login', methods=['POST'])
def login():
    datos = request.get_json()
    usuario = datos.get('usuario')
    contraseña = datos.get('contraseña')

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute('SELECT contraseña_hash FROM usuarios WHERE usuario = ?', (usuario,))
        resultado = cursor.fetchone()

    if not resultado or not verificar_contraseña(contraseña, resultado[0]):
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    token = generar_token()
    tokens_sesion[token] = usuario
    return jsonify({'mensaje': 'Login exitoso', 'usuario': usuario, 'token': token}), 200


@app.route('/tareas', methods=['GET'])
def obtener_tareas_html():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuario no especificado'}), 400

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        tareas = conn.execute(
            'SELECT id, titulo, descripcion, estado FROM tareas WHERE usuario = ? ORDER BY id DESC',
            (usuario,)
        ).fetchall()

    return render_template('tareas.html', usuario=usuario, tareas=tareas)


@app.route('/api/tareas', methods=['GET'])
def obtener_tareas_json():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuario no especificado'}), 400

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        tareas = conn.execute(
            'SELECT id, titulo, descripcion, estado FROM tareas WHERE usuario = ? ORDER BY id DESC',
            (usuario,)
        ).fetchall()

    return jsonify([dict(t) for t in tareas])


@app.route('/api/tareas', methods=['POST'])
def crear_tarea_json():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuario no especificado'}), 400

    datos = request.get_json()
    titulo = datos.get('titulo')
    descripcion = datos.get('descripcion', '')

    if not titulo:
        return jsonify({'error': 'Título requerido'}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            'INSERT INTO tareas (usuario, titulo, descripcion) VALUES (?, ?, ?)',
            (usuario, titulo, descripcion)
        )
        conn.commit()
        tarea_id = cursor.lastrowid

    return jsonify({'mensaje': 'Tarea creada', 'id': tarea_id}), 201


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
def eliminar_tarea_json(tarea_id):
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'error': 'Usuario no especificado'}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            'DELETE FROM tareas WHERE id = ? AND usuario = ?',
            (tarea_id, usuario)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Tarea no encontrada'}), 404
    return jsonify({'mensaje': 'Tarea eliminada'}), 200


@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    if token in tokens_sesion:
        del tokens_sesion[token]
    return jsonify({'mensaje': 'Sesión cerrada'}), 200


# ============================================
# INICIO
# ============================================
if __name__ == '__main__':
    inicializar_db()
    print("=" * 50)
    print(" Servidor corriendo en http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)