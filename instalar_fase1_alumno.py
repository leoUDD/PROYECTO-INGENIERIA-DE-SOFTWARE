#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import re
import shutil
import sys

RAIZ = Path.cwd()
ORIGEN_TEMPLATES = RAIZ / "juego" / "templates"
ORIGEN_CSS = RAIZ / "juego" / "static" / "css"
DESTINO = RAIZ / "frontend" / "juego" / "fase1"

PAGINAS = {
    "bienvenida.html": (
        "bienvenida.html",
        "estilo_bienvenida.css",
        "bienvenida.js",
    ),
    "promptconocidos.html": (
        "modo-equipo.html",
        "estilo_promptconocidos.css",
        "modo-equipo.js",
    ),
    "conocidos.html": (
        "conocidos.html",
        "estilo_conocidos.css",
        "conocidos.js",
    ),
    "trabajoenequipo.html": (
        "trabajo-equipo.html",
        "estilo_trabajoenequipo.css",
        "trabajo-equipo.js",
    ),
}


def detener(mensaje: str) -> None:
    print(f"ERROR: {mensaje}", file=sys.stderr)
    raise SystemExit(1)


def convertir_static(contenido: str) -> str:
    patrones = {
        "css": "",
        "images": "../../compartido/recursos/imagenes/",
        "sounds": "../../compartido/recursos/sonidos/",
        "videos": "../../compartido/recursos/videos/",
    }

    for carpeta, prefijo in patrones.items():
        contenido = re.sub(
            rf"{{%\s*static\s+['\"]{carpeta}/([^'\"]+)['\"]\s*%}}",
            lambda coincidencia: prefijo + coincidencia.group(1),
            contenido,
        )

    contenido = re.sub(
        r"{%\s*static\s+['\"]([^'\"]+)['\"]\s*%}",
        lambda coincidencia:
            "../../compartido/recursos/" + coincidencia.group(1),
        contenido,
    )

    return contenido


def resolver_modo_rapido(contenido: str) -> str:
    patron = re.compile(
        r"{%\s*if\s+modo_rapido\s*%}(.*?)"
        r"{%\s*else\s*%}(.*?)"
        r"{%\s*endif\s*%}",
        flags=re.DOTALL,
    )

    return patron.sub(lambda coincidencia: coincidencia.group(2), contenido)


def limpiar_django(contenido: str) -> str:
    contenido = re.sub(
        r"{%\s*load\s+static\s*%}",
        "",
        contenido,
    )
    contenido = re.sub(
        r"{%\s*include\s+[^%]+%}",
        "",
        contenido,
    )
    contenido = resolver_modo_rapido(contenido)
    contenido = re.sub(
        r"{%\s*url\s+[^%]+%}",
        "#",
        contenido,
    )
    contenido = re.sub(
        r"{%[^%]*%}",
        "",
        contenido,
        flags=re.DOTALL,
    )
    contenido = re.sub(
        r"{{[^}]*}}",
        "",
        contenido,
    )

    return contenido


def transformar_html(
    origen: Path,
    destino: Path,
    script: str,
) -> None:
    contenido = origen.read_text(encoding="utf-8")
    contenido = convertir_static(contenido)

    # El botón de Trabajo en equipo estaba en un include de Django.
    # Se reemplaza antes de limpiar las etiquetas para conservar su posición
    # exacta dentro de la vista original.
    if destino.name == "trabajo-equipo.html":
        contenido = re.sub(
            r"{%\s*include\s+[\"']includes/boton_listo_fase\.html[\"'][^%]*%}",
            """<div class="serverless-inline-ready">
      <button id="btnListoPreSopa" class="serverless-ready-button" type="button">
        ¡ESTOY LISTO!
      </button>
      <p id="esperaPreSopa" class="serverless-waiting">
        Esperando a los demás equipos...
        <span id="progresoPreSopa" class="serverless-progress">0/0 grupos listos</span>
      </p>
    </div>""",
            contenido,
            flags=re.IGNORECASE,
        )

    # Se reemplaza el JavaScript Django por el controlador serverless.
    contenido = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        contenido,
        flags=re.DOTALL | re.IGNORECASE,
    )
    contenido = limpiar_django(contenido)
    contenido = contenido.replace(
        "CONTINUAR AL MAPA",
        "CONTINUAR",
    )
    contenido = re.sub(
        r'data-sesion-id="[^"]*"',
        "",
        contenido,
    )

    if "fase1-serverless.css" not in contenido:
        contenido = contenido.replace(
            "</head>",
            '  <link rel="stylesheet" href="fase1-serverless.css">\n</head>',
        )

    scripts = f'''
  <script src="../../compartido/js/api.js"></script>
  <script src="../compartido.js"></script>
  <script src="{script}"></script>
'''
    contenido = contenido.replace("</body>", scripts + "</body>")
    destino.write_text(contenido, encoding="utf-8")


def copiar_recursos() -> None:
    origen_static = RAIZ / "juego" / "static"
    destino_recursos = (
        RAIZ / "frontend" / "compartido" / "recursos"
    )
    equivalencias = {
        "images": "imagenes",
        "sounds": "sonidos",
        "videos": "videos",
    }

    for origen_nombre, destino_nombre in equivalencias.items():
        origen = origen_static / origen_nombre
        destino = destino_recursos / destino_nombre

        if origen.exists():
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                origen,
                destino,
                dirs_exist_ok=True,
            )


def convertir_css(origen: Path, destino: Path) -> None:
    contenido = origen.read_text(encoding="utf-8")
    reemplazos = {
        "/static/images/":
            "../../compartido/recursos/imagenes/",
        "/static/sounds/":
            "../../compartido/recursos/sonidos/",
        "/static/videos/":
            "../../compartido/recursos/videos/",
        "../images/":
            "../../compartido/recursos/imagenes/",
    }

    for anterior, nuevo in reemplazos.items():
        contenido = contenido.replace(anterior, nuevo)

    destino.write_text(contenido, encoding="utf-8")


def parchear_registro() -> None:
    ruta = RAIZ / "frontend" / "acceso" / "registro.js"

    if not ruta.exists():
        print("AVISO: no se encontró frontend/acceso/registro.js")
        return

    contenido = ruta.read_text(encoding="utf-8")
    contenido = contenido.replace(
        'window.location.href = "bienvenida.html";',
        'window.location.href = "../juego/fase1/bienvenida.html";',
    )
    contenido = contenido.replace(
        "window.location.href = 'bienvenida.html';",
        "window.location.href = '../juego/fase1/bienvenida.html';",
    )
    contenido = contenido.replace(
        'window.location.replace("bienvenida.html");',
        'window.location.replace("../juego/fase1/bienvenida.html");',
    )
    ruta.write_text(contenido, encoding="utf-8")


def parchear_template_sam() -> None:
    ruta = RAIZ / "backend-serverless" / "template.yaml"

    if not ruta.exists():
        detener("No se encontró backend-serverless/template.yaml")

    contenido = ruta.read_text(encoding="utf-8")

    if "/api/fase1/iniciar" in contenido:
        print("template.yaml ya contiene las rutas nuevas de Fase 1")
        return

    marcador = "        ObtenerEstado:\n"

    if marcador not in contenido:
        detener(
            "No se encontró el bloque ObtenerEstado dentro de FuncionFase1"
        )

    eventos = '''        IniciarFase1:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase1/iniciar
            Method: POST

        SeleccionarModoEquipo:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase1/modo-equipo
            Method: POST

        MarcarGrupoListo:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase1/listo
            Method: POST

        FinalizarActividadConocidos:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase1/finalizar-conocidos
            Method: POST

        ObtenerRankingFase1:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase1/ranking
            Method: GET

'''
    contenido = contenido.replace(
        marcador,
        eventos + marcador,
        1,
    )
    ruta.write_text(contenido, encoding="utf-8")


def acelerar_sam_local() -> None:
    ruta = RAIZ / "backend-serverless" / "package.json"

    if not ruta.exists():
        return

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    scripts = datos.setdefault("scripts", {})
    comando = scripts.get("local:api", "")

    if comando and "--warm-containers" not in comando:
        scripts["local:api"] = (
            comando + " --warm-containers EAGER"
        )

    ruta.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parchear_control_profesor() -> None:
    ruta = (
        RAIZ
        / "backend-serverless"
        / "src"
        / "profesor"
        / "servicio.ts"
    )

    if not ruta.exists():
        return

    contenido = ruta.read_text(encoding="utf-8")
    anterior = '''      listo: Boolean(
        item.listoF1 ||
          item.listoF2 ||
          item.listoF3 ||
          item.listoF4 ||
          item.listoF5 ||
          item.listoF6,
      ),'''
    nuevo = '''      listo: (() => {
        const faseActual = String(sesion.fase || "");

        if (faseActual === "f1_conocidos") {
          return Boolean(item.listoConocidos);
        }

        if (faseActual === "f1_pre_sopa") {
          return Boolean(item.listoF1);
        }

        if (
          faseActual === "f1_sopa" ||
          faseActual === "f1_ranking"
        ) {
          return Boolean(item.sopaCompletada);
        }

        return Boolean(
          item.listoF2 ||
            item.listoF3 ||
            item.listoF4 ||
            item.listoF5 ||
            item.listoF6,
        );
      })(),'''

    if anterior in contenido:
        ruta.write_text(
            contenido.replace(anterior, nuevo),
            encoding="utf-8",
        )


def main() -> None:
    if not ORIGEN_TEMPLATES.exists():
        detener(
            "Ejecuta este instalador desde la raíz del repositorio; falta juego/templates"
        )

    DESTINO.mkdir(parents=True, exist_ok=True)

    for origen_nombre, (
        destino_nombre,
        css_nombre,
        script,
    ) in PAGINAS.items():
        origen_html = ORIGEN_TEMPLATES / origen_nombre
        origen_css = ORIGEN_CSS / css_nombre

        if not origen_html.exists():
            detener(f"No se encontró {origen_html}")

        if not origen_css.exists():
            detener(f"No se encontró {origen_css}")

        transformar_html(
            origen_html,
            DESTINO / destino_nombre,
            script,
        )
        convertir_css(
            origen_css,
            DESTINO / css_nombre,
        )

    # CSS originales utilizados por las dos páginas estáticas nuevas.
    for css_nombre in (
        "estilo_sopadeletras.css",
        "estilo_ranking.css",
    ):
        origen = ORIGEN_CSS / css_nombre
        if origen.exists():
            convertir_css(origen, DESTINO / css_nombre)

    copiar_recursos()
    parchear_registro()
    parchear_template_sam()
    acelerar_sam_local()
    parchear_control_profesor()

    print("\nInstalación de Fase 1 completada.")
    print("Vistas creadas en frontend/juego/fase1")
    print("Rutas SAM agregadas a backend-serverless/template.yaml")
    print("Registro conectado a juego/fase1/bienvenida.html")


if __name__ == "__main__":
    main()
