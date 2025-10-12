# Misión Emprende-App Web

Es una aplicación web gamificada desarrollada para que los alumnos de la **Universidad del Desarrollo (UDD)** aprendan sobre **emprendimiento e innovación** de manera interactiva, participando en equipos y resolviendo desafíos dentro de un entorno divertido y educativo.

## Arquitectura

- **Backend**: Django **(Python)** como framework.
- **Frontend**: HTML, CSS y Bootstrap.
- **BBDD**: MySQL

## Instalación y ejecución

Sigue estos pasos para ejecutar la app en tu entorno local:

```bash
# 1. Clonar el repositorio
git clone https://github.com/usuario/SparkApp-UDD.git
cd SparkApp-UDD

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate      # En Windows
# o
source venv/bin/activate   # En macOS / Linux

# 3. Instalar dependencias necesarias
pip install -r requirements.txt

# 4. Ejecutar el servidor de desarrollo
python manage.py runserver
```
Luego abre tu navegador y entra a:

http://127.0.0.1:8000/
