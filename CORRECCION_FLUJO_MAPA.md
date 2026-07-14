# Corrección del flujo entre Fase 1 y Fase 2

La versión anterior saltaba por error el mapa de habilidades.

Flujo correcto:

```text
Ranking Fase 1
→ Mapa de habilidades: Empatía
→ Transición Desafíos
→ Temáticas
→ Desafíos
→ Espera de equipos
→ Transición Empatía
→ Bubble Map
→ Ranking Fase 2
```

## Aplicar

Desde la raíz del repositorio:

```bash
unzip -o fase2-alumno-serverless-corregido-raiz.zip
python corregir_flujo_mapa.py
```

Luego:

```bash
cd backend-serverless
npm run verificar
rm -rf .aws-sam
export PATH="$PWD/node_modules/.bin:$PATH"
sam build
npm run local:api
```

No ejecutes `npm run local:preparar` si quieres conservar las sesiones locales.
