# Alumno + Fase 1 serverless

Este paquete completa el primer flujo jugable:

```text
Perfiles
→ Alumno
→ Registro con código generado por Profesor
→ Bienvenida
→ Selección del modo de equipo
→ Actividad para conocerse
→ Trabajo en equipo
→ Sopa de letras sincronizada
→ Ranking parcial
```

## 1. Respaldo

Desde la raíz del repositorio:

```bash
git add .
git commit -m "Respaldo antes de migrar Fase 1 alumno"
```

## 2. Descomprimir e instalar

Sube el ZIP a la raíz y ejecuta:

```bash
unzip -o fase1-alumno-serverless-listo-raiz.zip
python instalar_fase1_alumno.py
```

El instalador reutiliza las plantillas y CSS originales que ya están en
`juego/templates` y `juego/static/css`, cambia únicamente Django por JavaScript
y conecta las pantallas a las Lambdas.

## 3. Verificar backend

```bash
cd backend-serverless
npm install
npm run verificar
rm -rf .aws-sam
sam build
```

Debe terminar con:

```text
Build Succeeded
```

Después:

```bash
npm run local:api
```

DynamoDB Local debe permanecer levantado:

```bash
npm run local:base
```

## 4. Frontend

Desde la raíz, en otra terminal:

```bash
python -m http.server 5500 --directory frontend
```

Los puertos 3000 y 5500 deben estar públicos en Codespaces.

## 5. Prueba recomendada

Crea una sesión con dos grupos desde Profesor y abre dos ventanas privadas:

1. Ingresa cada grupo con un código distinto.
2. Ambos deben llegar a Bienvenida.
3. Elijan el modo de equipo.
4. Marquen “Listo para comenzar” en Conocerse.
5. Cuando todos estén listos se activa simultáneamente la actividad de 10 segundos.
6. Al terminar, pasan a Trabajo en equipo.
7. Al marcar ambos “Estoy listo”, comienza la sopa y el timer de 60 segundos.
8. Cada palabra nueva suma un token.
9. El primer grupo que termina recibe 5 tokens; los demás reciben 3.
10. Cuando todos terminan se muestra el ranking parcial.

## Rutas agregadas

```text
POST /api/fase1/iniciar
POST /api/fase1/modo-equipo
POST /api/fase1/listo
POST /api/fase1/finalizar-conocidos
GET  /api/fase1/estado
POST /api/fase1/palabras
POST /api/fase1/completar
GET  /api/fase1/ranking
```

## Nota de rendimiento local

El instalador agrega `--warm-containers EAGER` al script `local:api` para que
SAM mantenga las Lambdas locales activas y las llamadas posteriores sean más
rápidas.
