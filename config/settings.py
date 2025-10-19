"""
Django settings for config project.
"""

from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Debug / Hosts (recomendado para Codespaces) ===
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.app.github.dev']
CSRF_TRUSTED_ORIGINS = ['https://*.app.github.dev']

# ⚠️ Mantén tu SECRET_KEY real aquí (no lo borres)
SECRET_KEY = 'django-insecure-z)ef_&ohvg#38ntgcy3#fcf@#p)72_sk7$eah&ukuba$x%!gyl'

# === Apps ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'juego',
    'evaluation',
]

# === Middleware ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# === Templates ===
# Usa carpeta global:  /templates/  (ej: templates/juego/market.html)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'juego' / 'templates',  # 👈 agrega esto
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# === Database ===
# Usa SOLO una base (SQLite es ideal en Codespaces)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# === I18N / TZ ===
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# === Static ===
STATIC_URL = 'static/'

# === Default PK ===
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# --- FIX duro para templates (dejar al final del settings) ---
from pathlib import Path as _Path  # por si acaso
if isinstance(TEMPLATES, list) and TEMPLATES:
    TEMPLATES[0]['DIRS'] = [BASE_DIR / 'juego' / 'templates']
# --- FIN FIX ---
# --- FIX ROBUSTO TEMPLATES (no mover archivos) ---
from pathlib import Path as _Path

# Asegura que exista un bloque TEMPLATES usable
_templates = TEMPLATES if isinstance(TEMPLATES, (list, tuple)) and TEMPLATES else [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# Carpetas que queremos sí o sí
_extra_dirs = [BASE_DIR / 'juego' / 'templates']
_global_dir = BASE_DIR / 'templates'
if _global_dir.exists():
    _extra_dirs.append(_global_dir)

# De-duplicar y fijar DIRS
_dirs = list(_templates[0].get('DIRS', []))
for d in _extra_dirs:
    if d not in _dirs:
        _dirs.append(d)
_templates[0]['DIRS'] = _dirs

# Sobrescribe TEMPLATES con nuestro bloque consolidado
TEMPLATES = list(_templates)

# Log de verificación en consola (solo en DEBUG)
if DEBUG:
    try:
        print("TEMPLATES.DIRS =", [str(p) for p in TEMPLATES[0]['DIRS']])
    except Exception:
        pass
# --- FIN FIX ROBUSTO ---

