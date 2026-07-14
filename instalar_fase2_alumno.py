#!/usr/bin/env python3
from pathlib import Path
import json, re, shutil, sys

RAIZ = Path.cwd()
PAQUETE = Path(__file__).resolve().parent


def error(mensaje: str) -> None:
    print(f"ERROR: {mensaje}", file=sys.stderr)
    raise SystemExit(1)


def copiar_arbol(origen: Path, destino: Path) -> None:
    if origen.exists():
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copytree(origen, destino, dirs_exist_ok=True)


def copiar_backend_frontend() -> None:
    copiar_arbol(PAQUETE / "backend-serverless", RAIZ / "backend-serverless")
    copiar_arbol(PAQUETE / "frontend", RAIZ / "frontend")


def copiar_recursos_originales() -> None:
    origen = RAIZ / "juego" / "static"
    destino = RAIZ / "frontend" / "compartido" / "recursos"
    for original, nuevo in {"images":"imagenes", "sounds":"sonidos", "videos":"videos"}.items():
        if (origen / original).exists():
            copiar_arbol(origen / original, destino / nuevo)


def copiar_css_originales() -> None:
    origen = RAIZ / "juego" / "static" / "css"
    destino = RAIZ / "frontend" / "juego" / "fase2"
    archivos = [
        "estilo_transiciondesafio.css",
        "estilo_tematicas.css",
        "estilo_desafios.css",
        "estilo_transicionempatia.css",
        "estilo_bubblemap.css",
        "estilo_ranking.css",
    ]
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in archivos:
        ruta = origen / nombre
        if not ruta.exists():
            print(f"AVISO: no se encontró {ruta}")
            continue
        contenido = ruta.read_text(encoding="utf-8")
        contenido = contenido.replace("/static/images/", "../../compartido/recursos/imagenes/")
        contenido = contenido.replace("/static/sounds/", "../../compartido/recursos/sonidos/")
        contenido = contenido.replace("/static/videos/", "../../compartido/recursos/videos/")
        contenido = contenido.replace("../images/", "../../compartido/recursos/imagenes/")
        (destino / nombre).write_text(contenido, encoding="utf-8")


def parchear_template() -> None:
    ruta = RAIZ / "backend-serverless" / "template.yaml"
    if not ruta.exists(): error("No se encontró backend-serverless/template.yaml")
    contenido = ruta.read_text(encoding="utf-8")
    if "FuncionFase2:" in contenido:
        print("template.yaml ya contiene FuncionFase2")
        return
    bloque = '''
  FuncionFase2:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: src/fase2/api.manejador
      Policies: *PermisosDynamo
      Events:
        ObtenerEstadoFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/estado
            Method: GET

        IniciarFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/iniciar
            Method: POST

        MarcarListoFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/listo
            Method: POST

        SeleccionarDesafioFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/seleccion
            Method: POST

        AsignarDesafioAleatorioFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/asignar-azar
            Method: POST

        GuardarBubbleMapFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/bubblemap/guardar
            Method: POST

        CompletarBubbleMapFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/bubblemap/completar
            Method: POST

        ObtenerRankingFase2:
          Type: HttpApi
          Properties:
            ApiId: !Ref ApiBackend
            Path: /api/fase2/ranking
            Method: GET
    Metadata:
      BuildMethod: esbuild
      BuildProperties: *ConfiguracionEsbuild

'''
    if "Outputs:" not in contenido: error("No se encontró Outputs en template.yaml")
    contenido = contenido.replace("Outputs:\n", bloque + "Outputs:\n", 1)
    ruta.write_text(contenido, encoding="utf-8")


def parchear_package_json() -> None:
    ruta = RAIZ / "backend-serverless" / "package.json"
    if not ruta.exists(): return
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    scripts = datos.setdefault("scripts", {})
    comando = scripts.get("empaquetar:verificar", "")
    if comando and "src/fase2/api.ts" not in comando:
        referencia = "src/fase1/api.ts"
        if referencia in comando:
            comando = comando.replace(referencia, referencia + " src/fase2/api.ts")
        else:
            comando += " src/fase2/api.ts"
        scripts["empaquetar:verificar"] = comando
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parchear_rutas_fase1() -> None:
    ruta = RAIZ / "backend-serverless" / "src" / "fase1" / "servicio.ts"
    if not ruta.exists(): return
    contenido = ruta.read_text(encoding="utf-8")
    if 'fase === "f2_tematicas"' in contenido: return
    marcador = '''  if (fase === "f1_ranking") {
    return "ranking.html";
  }
'''
    agregado = marcador + '''
  if (fase === "mapa_f2_empatia" || fase === "f2_transicion") {
    return "../fase2/transicion-desafio.html";
  }

  if (fase === "f2_tematicas") {
    return "../fase2/tematicas.html";
  }

  if (fase === "f2_transicion_empatia") {
    return "../fase2/transicion-empatia.html";
  }

  if (fase === "f2_bubblemap") {
    return "../fase2/bubblemap.html";
  }

  if (fase === "f2_ranking") {
    return "../fase2/ranking.html";
  }
'''
    if marcador in contenido:
        contenido = contenido.replace(marcador, agregado, 1)
        ruta.write_text(contenido, encoding="utf-8")
    else:
        print("AVISO: no fue posible ampliar rutaSugerida de Fase 1")


def parchear_ranking_fase1() -> None:
    ruta = RAIZ / "frontend" / "juego" / "fase1" / "ranking.html"
    if not ruta.exists():
        print("AVISO: no se encontró el ranking de Fase 1")
        return
    contenido = ruta.read_text(encoding="utf-8")
    if "btnContinuarFase2" in contenido: return
    panel = '''
    <section class="serverless-f2-ready" style="margin-top:22px">
      <button id="btnContinuarFase2" class="serverless-f2-button" type="button">
        CONTINUAR A EMPATÍA
      </button>
      <div id="progresoInicioFase2" class="serverless-f2-progress">0/0 grupos listos</div>
    </section>
'''
    contenido = contenido.replace('<footer class="ranking-footer">', panel + '\n    <footer class="ranking-footer">', 1)
    scripts = '''
  <script src="../fase2/fase2-comun.js"></script>
  <script src="../fase2/iniciar-desde-ranking.js"></script>
'''
    contenido = contenido.replace("</body>", scripts + "</body>")
    if "../fase2/fase2-serverless.css" not in contenido:
        contenido = contenido.replace("</head>", '  <link rel="stylesheet" href="../fase2/fase2-serverless.css">\n</head>')
    ruta.write_text(contenido, encoding="utf-8")


def parchear_profesor() -> None:
    ruta = RAIZ / "backend-serverless" / "src" / "profesor" / "servicio.ts"
    if not ruta.exists(): return
    contenido = ruta.read_text(encoding="utf-8")
    # Solo amplía el bloque antiguo si aún existe; no pisa correcciones manuales.
    viejo = '''      listo: Boolean(
        item.listoF1 ||
          item.listoF2 ||
          item.listoF3 ||
          item.listoF4 ||
          item.listoF5 ||
          item.listoF6,
      ),'''
    nuevo = '''      listo: (() => {
        const faseActual = String(sesion.fase || "");

        if (faseActual === "f1_conocidos") return Boolean(item.listoConocidos);
        if (faseActual === "f1_pre_sopa") return Boolean(item.listoF1);
        if (faseActual === "f1_sopa" || faseActual === "f1_ranking") return Boolean(item.sopaCompletada);
        if (faseActual === "mapa_f2_empatia" || faseActual === "f2_transicion") return Boolean(item.listoF2Transicion);
        if (faseActual === "f2_tematicas") return Boolean(item.listoF2Desafio);
        if (faseActual === "f2_transicion_empatia") return Boolean(item.listoF2Empatia);
        if (faseActual === "f2_bubblemap" || faseActual === "f2_ranking") return Boolean(item.bubbleCompletado);

        return false;
      })(),'''
    if viejo in contenido:
        contenido = contenido.replace(viejo, nuevo, 1)
        ruta.write_text(contenido, encoding="utf-8")


def main() -> None:
    if not (RAIZ / "backend-serverless").exists(): error("Ejecuta este instalador desde la raíz del repositorio")
    copiar_recursos_originales()
    copiar_css_originales()
    parchear_template()
    parchear_package_json()
    parchear_rutas_fase1()
    parchear_ranking_fase1()
    parchear_profesor()
    print("\nFase 2 instalada correctamente.")
    print("Siguiente paso: cd backend-serverless && npm run verificar && rm -rf .aws-sam && sam build")


if __name__ == "__main__":
    main()
