# Misión Emprende – App Web

**Misión Emprende** es una aplicación web gamificada desarrollada para que los alumnos de la  
**Universidad del Desarrollo (UDD)** aprendan sobre **emprendimiento e innovación** de manera interactiva.  
Los estudiantes trabajan en equipos, resuelven desafíos y avanzan en una narrativa estilo “misión”,  
mezclando contenidos académicos con dinámicas de juego.

---

## Arquitectura del Proyecto

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, Bootstrap
- **Base de datos:** MySQL
- **Lenguajes utilizados:** Python, JavaScript
- **Despliegue:** AWS EC2 (Ubuntu) + Docker
- **Control de versiones:** GitHub

---

## Requisitos Previos

Para ejecutar el proyecto en local necesitas:

- Python **3.11+**
- MySQL **8.x** instalado y con una base de datos creada
- (Opcional) Docker y Docker Compose
- Git

---

## Instalación y Ejecución en Entorno Local

### Clonar el repositorio

```bash
git clone https://github.com/leoUDD/PROYECTO-INGENIERIA-DE-SOFTWARE.git
cd PROYECTO-INGENIERIA-DE-SOFTWARE

Sigue estos pasos para ejecutar la app en tu entorno local:

```bash
# 1. Clonar el repositorio
git clone https://github.com/leoUDD/PROYECTO-INGENIERIA-DE-SOFTWARE.git
cd PROYECTO-INGENIERIA-DE-SOFTWARE

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate      # En Windows
# o
source venv/bin/activate   # En macOS / Linux

# 3. Instalar dependencias necesarias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Ejecutar el servidor de desarrollo
python manage.py runserver
```
Luego abre tu navegador y entra a:

http://127.0.0.1:8000/ => localhost

http://3.151.206.195:8000/ => Nube AWS
