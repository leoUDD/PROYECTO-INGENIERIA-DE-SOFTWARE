#!/usr/bin/env python3
from pathlib import Path
import re
import shutil
import sys

RAIZ = Path.cwd()
PAQUETE = Path(__file__).resolve().parent


def error(mensaje):
    print(f"ERROR: {mensaje}", file=sys.stderr)
    raise SystemExit(1)


def copiar(origen, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)


def copiar_backend_y_flujo():
    for relativo in [
        "backend-serverless/src/fase2/servicio.ts",
        "backend-serverless/src/fase2/repositorio.ts",
        "backend-serverless/pruebas/fase2.test.ts",
        "frontend/juego/mapa/mapa-flujo.js",
    ]:
        origen = PAQUETE / relativo
        destino = RAIZ / relativo
        copiar(origen, destino)


def parchear_fase1():
    ruta = RAIZ / "backend-serverless/src/fase1/servicio.ts"
    if not ruta.exists():
        error("No se encontró backend-serverless/src/fase1/servicio.ts")

    contenido = ruta.read_text(encoding="utf-8")

    contenido = contenido.replace(
        '  if (fase === "mapa_f2_empatia" || fase === "f2_transicion") {\n'
        '    return "../fase2/transicion-desafio.html";\n'
        '  }',
        '  if (fase === "mapa_f2_empatia") {\n'
        '    return "../mapa/habilidades.html";\n'
        '  }\n\n'
        '  if (fase === "f2_transicion") {\n'
        '    return "../fase2/transicion-desafio.html";\n'
        '  }',
    )

    if 'return "../mapa/habilidades.html";' not in contenido:
        marcador = (
            '  if (fase === "f1_ranking") {\n'
            '    return "ranking.html";\n'
            '  }\n'
        )
        agregado = marcador + (
            '\n  if (fase === "mapa_f2_empatia") {\n'
            '    return "../mapa/habilidades.html";\n'
            '  }\n\n'
            '  if (fase === "f2_transicion") {\n'
            '    return "../fase2/transicion-desafio.html";\n'
            '  }\n'
        )
        contenido = contenido.replace(marcador, agregado, 1)

    ruta.write_text(contenido, encoding="utf-8")


def generar_mapa():
    plantilla = RAIZ / "juego/templates/habilidades_intro.html"
    css_origen = RAIZ / "juego/static/css/estilo_habilidades_intro.css"
    js_origen = RAIZ / "juego/static/js/mapa_agente.js"
    destino = RAIZ / "frontend/juego/mapa"
    destino.mkdir(parents=True, exist_ok=True)

    if not plantilla.exists():
        error("No se encontró juego/templates/habilidades_intro.html")

    html = plantilla.read_text(encoding="utf-8")
    html = html.replace("{% load static %}", "")
    html = re.sub(
        r'{%\s*include\s+"includes/selector_idioma\.html"\s*%}',
        "",
        html,
    )

    def static(match):
        ruta = match.group(1)
        if ruta.startswith("css/"):
            return "mapa.css"
        if ruta.startswith("js/"):
            return "mapa-agente.js"
        if ruta.startswith("images/"):
            return "../../compartido/recursos/imagenes/" + ruta[7:]
        if ruta.startswith("sounds/"):
            return "../../compartido/recursos/sonidos/" + ruta[7:]
        if ruta.startswith("videos/"):
            return "../../compartido/recursos/videos/" + ruta[7:]
        return ruta

    html = re.sub(r"{%\s*static\s+'([^']+)'\s*%}", static, html)
    html = re.sub(r'{%\s*static\s+"([^"]+)"\s*%}', static, html)

    html = html.replace(
        '{{ estado_mapa.titulo_mapa|default:"HABILIDADES DE MISIÓN" }}',
        "HABILIDADES DE MISIÓN",
    )
    html = html.replace('{{ estado_mapa.ruta_continuar }}', "#")
    html = html.replace(
        '{{ estado_mapa.texto_boton|default:"CONTINUAR" }}',
        "CONTINUAR A DESAFÍOS",
    )

    config = (
        'window.MAPA_HABILIDADES_CONFIG = {\n'
        '  habilidadActiva: "Empatía",\n'
        '  habilidadesCompletadas: ["Trabajo en equipo"],\n'
        '  rutaContinuar: "#",\n'
        '  textoBoton: "CONTINUAR A DESAFÍOS"\n'
        '};'
    )
    html = re.sub(
        r"window\.MAPA_HABILIDADES_CONFIG\s*=\s*\{.*?\};",
        config,
        html,
        flags=re.S,
    )

    scripts = (
        '  <script src="../../compartido/js/api.js"></script>\n'
        '  <script src="../compartido.js"></script>\n'
        '  <script src="../fase2/fase2-comun.js"></script>\n'
        '  <script src="mapa-flujo.js"></script>\n'
    )
    html = html.replace("</body>", scripts + "</body>")

    html = re.sub(r"{{.*?}}", "", html, flags=re.S)
    html = re.sub(r"{%.*?%}", "", html, flags=re.S)

    (destino / "habilidades.html").write_text(
        html,
        encoding="utf-8",
    )

    if css_origen.exists():
        css = css_origen.read_text(encoding="utf-8")
        css = css.replace(
            "/static/images/",
            "../../compartido/recursos/imagenes/",
        )
        css = css.replace(
            "../images/",
            "../../compartido/recursos/imagenes/",
        )
        (destino / "mapa.css").write_text(css, encoding="utf-8")
    else:
        print(f"AVISO: no se encontró {css_origen}")

    if js_origen.exists():
        copiar(js_origen, destino / "mapa-agente.js")
    else:
        print(f"AVISO: no se encontró {js_origen}")


def parchear_profesor():
    ruta = RAIZ / "backend-serverless/src/profesor/servicio.ts"
    if not ruta.exists():
        return

    contenido = ruta.read_text(encoding="utf-8")
    contenido = contenido.replace(
        'if (faseActual === "mapa_f2_empatia" || faseActual === "f2_transicion") '
        'return Boolean(item.listoF2Transicion);',
        'if (faseActual === "mapa_f2_empatia") '
        'return Boolean(item.listoF2Mapa);\n'
        '        if (faseActual === "f2_transicion") '
        'return Boolean(item.listoF2Transicion);',
    )
    ruta.write_text(contenido, encoding="utf-8")


def main():
    if not (RAIZ / "backend-serverless").exists():
        error("Ejecuta el corrector desde la raíz del repositorio")

    copiar_backend_y_flujo()
    parchear_fase1()
    generar_mapa()
    parchear_profesor()

    print("Flujo corregido:")
    print("Ranking F1 -> Mapa Empatía -> Transición Desafíos -> Temáticas")
    print("Ahora reconstruye SAM.")


if __name__ == "__main__":
    main()
