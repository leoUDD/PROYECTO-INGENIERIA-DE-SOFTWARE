# Registro serverless con el diseño original

Esta carpeta conserva el HTML, CSS, clases, marco SVG, partículas, logos,
animaciones y sonidos del registro original de Misión Emprende.

Los únicos cambios son:

- Se eliminaron las etiquetas de Django.
- El formulario usa `fetch` para comunicarse con API Gateway/Lambda.
- El token del grupo se guarda en `localStorage`.
- El nombre del escuadrón se guarda en DynamoDB.

## Instalación

Extrae el contenido de este paquete en la raíz del repositorio. Deben quedar:

```text
frontend/acceso/registro.html
frontend/acceso/registro.css
frontend/acceso/registro.js
frontend/compartido/js/api.js
backend-serverless/src/acceso/api.ts
backend-serverless/src/acceso/servicio.ts
backend-serverless/src/acceso/repositorio.ts
```

Luego copia la música original:

```bash
bash copiar-musica.sh
```

## URL local

`frontend/compartido/js/api.js` apunta por defecto a:

```js
const API_URL = "http://127.0.0.1:3000";
```

Cuando despliegues SAM, reemplázala por la URL de API Gateway.

## Probar el frontend

Desde la raíz del repositorio:

```bash
python -m http.server 5500 --directory frontend
```

Abre:

```text
http://127.0.0.1:5500/acceso/registro.html
```
