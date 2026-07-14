# Fase 2 serverless — Desafíos y Empatía

Este paquete continúa el flujo después del ranking de Fase 1:

```text
Ranking Fase 1
→ Introducción a desafíos
→ Selección de temática
→ Selección de desafío
→ Espera de equipos
→ Introducción a empatía
→ Bubble Map
→ Ranking Fase 2
```

## Instalación

Desde la raíz del repositorio:

```bash
git add .
git commit -m "Respaldo antes de Fase 2"

unzip -o fase2-alumno-serverless-listo-raiz.zip
python instalar_fase2_alumno.py
```

Luego reconstruye:

```bash
cd backend-serverless
npm install
npm run verificar
rm -rf .aws-sam
sam build
npm run local:api
```

DynamoDB Local y el frontend deben seguir levantados como antes.

## Rutas nuevas

- `GET /api/fase2/estado`
- `POST /api/fase2/iniciar`
- `POST /api/fase2/listo`
- `POST /api/fase2/seleccion`
- `POST /api/fase2/asignar-azar`
- `POST /api/fase2/bubblemap/guardar`
- `POST /api/fase2/bubblemap/completar`
- `GET /api/fase2/ranking`

## Duraciones

En `backend-serverless/src/fase2/servicio.ts`:

```ts
const DURACION_ELECCION_SEGUNDOS = 120;
const DURACION_BUBBLE_SEGUNDOS = 180;
```

## Sincronización

Se mantiene polling cada 3 segundos. Cuando todos los grupos están listos, el backend cambia la fase en DynamoDB y cada navegador se redirige al detectar el cambio.

## Bubble Map

El puntaje máximo es 10 tokens:

- 6 dimensiones principales: hasta 6 puntos.
- Otros hallazgos: hasta 2 puntos.
- Relato breve: 1 punto.
- Link/noticia: 1 punto.

La recompensa se entrega una sola vez por grupo.
