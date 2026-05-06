#!/usr/bin/env python3
"""
Cliente en consola para la API de Gestión de Tareas
PFO 2 - Programación sobre Redes
"""

import requests
import json
import webbrowser

API_URL = "http://localhost:5000"

class ClienteTareas:
    def __init__(self):
        self.token = None
        self.usuario = None

    def registrar(self):
        print("\n REGISTRO DE USUARIO")
        usuario = input("Usuario: ").strip()
        contraseña = input("Contraseña: ").strip()

        try:
            res = requests.post(f"{API_URL}/registro", json={"usuario": usuario, "contraseña": contraseña})
            if res.status_code == 201:
                print(f" {res.json()['mensaje']}")
            else:
                print(f" {res.json()['error']}")
        except Exception as e:
            print(f" Error: {e}")

    def login(self):
        print("\n INICIO DE SESIÓN")
        usuario = input("Usuario: ").strip()
        contraseña = input("Contraseña: ").strip()

        try:
            res = requests.post(f"{API_URL}/login", json={"usuario": usuario, "contraseña": contraseña})
            if res.status_code == 200:
                data = res.json()
                self.token = data['token']
                self.usuario = data['usuario']
                print(f" {data['mensaje']}")
                
                # 🚀 ABRIR EL NAVEGADOR AUTOMÁTICAMENTE
                url_html = f"{API_URL}/tareas?usuario={self.usuario}"
                print(f" Abriendo navegador con: {url_html}")
                webbrowser.open(url_html)
                
                return True
            else:
                print(f" {res.json()['error']}")
                return False
        except Exception as e:
            print(f" Error: {e}")
            return False

    def ver_tareas(self):
        print("\n MIS TAREAS")
        try:
            res = requests.get(f"{API_URL}/api/tareas?usuario={self.usuario}")  # 👈 Cambiado
            if res.status_code == 200:
                tareas = res.json()
                if not tareas:
                    print("   No hay tareas aún.")
                for t in tareas:
                    print(f"   [{t['id']}] {t['titulo']} - {t['descripcion'] or 'Sin descripción'} ({t['estado']})")
            else:
                error_msg = res.json().get('error', 'Error desconocido')
                print(f" Error: {error_msg}")
        except requests.exceptions.JSONDecodeError:
            print(f" Error: El servidor no respondió con JSON. Respuesta: {res.text[:100]}")
        except Exception as e:
            print(f" Error: {e}")

    def crear_tarea(self):
        print("\n CREAR TAREA")
        titulo = input("Título: ").strip()
        descripcion = input("Descripción: ").strip()

        try:
            res = requests.post(f"{API_URL}/api/tareas?usuario={self.usuario}", 
                            json={"titulo": titulo, "descripcion": descripcion})
            if res.status_code == 201:
                print(f" {res.json()['mensaje']} (ID: {res.json()['id']})")
            else:
                print(f" {res.json().get('error', 'Error desconocido')}")
        except Exception as e:
            print(f" Error: {e}")

    def eliminar_tarea(self):
        print("\n ELIMINAR TAREA")
        try:
            tarea_id = int(input("ID de la tarea: "))
        except ValueError:
            print(" ID inválido")
            return

        try:
            res = requests.delete(f"{API_URL}/api/tareas/{tarea_id}?usuario={self.usuario}")
            if res.status_code == 200:
                print(f" {res.json()['mensaje']}")
            else:
                print(f" {res.json().get('error', 'Error desconocido')}")
        except Exception as e:
            print(f" Error: {e}")

    def menu_principal(self):
        while True:
            print("\n" + "=" * 40)
            print(" SISTEMA DE TAREAS")
            print("=" * 40)
            print("1. Registrarse")
            print("2. Iniciar sesión")
            print("3. Salir")
            opcion = input("Seleccioná una opción: ")

            if opcion == "1":
                self.registrar()
            elif opcion == "2":
                if self.login():
                    self.menu_tareas()
            elif opcion == "3":
                print(" ¡Hasta luego!")
                break
            else:
                print(" Opción inválida")

    def menu_tareas(self):
        while True:
            print("\n" + "=" * 40)
            print(f" BIENVENIDO, {self.usuario.upper()}")
            print("=" * 40)
            print("1. Ver tareas")
            print("2. Crear tarea")
            print("3. Eliminar tarea")
            print("4. Cerrar sesión")
            opcion = input("Seleccioná una opción: ")

            if opcion == "1":
                self.ver_tareas()
            elif opcion == "2":
                self.crear_tarea()
            elif opcion == "3":
                self.eliminar_tarea()
            elif opcion == "4":
                self.token = None
                self.usuario = None
                print(" Sesión cerrada")
                break
            else:
                print(" Opción inválida")

if __name__ == "__main__":
    cliente = ClienteTareas()
    cliente.menu_principal()