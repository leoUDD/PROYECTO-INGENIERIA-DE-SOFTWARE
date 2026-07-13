# Integración del módulo Profesor

Este paquete agrega el flujo serverless de Profesor sin modificar
Administración ni las fases del juego.

## 1. Descomprimir en la raíz

Desde la raíz del repositorio:

```bash
unzip -o profesor-serverless-listo-raiz.zip
chmod +x copiar-recursos-profesor.sh
./copiar-recursos-profesor.sh
```

## 2. Integrar la pantalla Perfiles

En `frontend/acceso/perfiles.html`:

### Enlace Profesor

Debe apuntar a:

```html
<a
  href="../profesor/index.html"
  data-rol="profesor"
  aria-label="Ingresar como Profesor"
  class="restringido"
>
```

### Script de validación serverless

Justo antes de `</body>`, después del script original, agrega:

```html
<script src="../compartido/js/api.js"></script>
<script src="profesor-acceso.js"></script>
```

El script intercepta solamente el acceso Profesor. El acceso Admin
continúa con el comportamiento actual hasta que migremos Administración.

## 3. Variables locales

Si ya tienes `backend-serverless/env.local.json`, agrega dentro de
`Parameters`:

```json
"CLAVE_ACCESO_PROFESOR": "profe123"
```

También puedes reemplazar `env.local.json` copiando el ejemplo:

```bash
cd backend-serverless
cp env.local.example.json env.local.json
```

## 4. Construir y levantar

```bash
cd backend-serverless
npm install
npm run verificar
rm -rf .aws-sam
sam build
npm run local:api
```

DynamoDB Local debe continuar ejecutándose:

```bash
npm run local:base
npm run local:preparar
```

## 5. Probar

Abre Perfiles, selecciona Profesor y usa:

```text
profe123
```

Flujo esperado:

```text
Perfiles
→ Dashboard Profesor
→ Crear sesión
→ Subir Excel
→ Ver códigos de grupos
→ Ver sesiones
→ Panel de control
```

## Formato del Excel

Encabezados esperados:

- Correo
- RUT
- Nombre
- Apellido Paterno
- Apellido Materno
- Carrera

## Importante

El frontend analiza el Excel con SheetJS y envía estudiantes como JSON.
La Lambda no recibe ni guarda el archivo original.
