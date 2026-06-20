import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from juego.models import Grupo, Sesion, BubbleMapRespuesta
from juego.backend.core_global.services import (
    acceso_permitido,
    obtener_grupo_desde_session,
    )


def transiciondesafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transiciondesafio"):
        return redirect("pantalla_espera")
    return render(request, "fase2/transiciondesafio.html", {"grupo": grupo})

@never_cache
def tematicas(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "tematicas"):
        return redirect("pantalla_espera")

    if (grupo.tema_elegido or "").strip():
        return redirect("desafios")

    tematicas_bd = Tematica.objects.filter(activa=True).order_by("orden", "title")

    return render(request, "fase2/tematicas.html", {
        "grupo": grupo,
        "tema_actual": (grupo.tema_elegido or "").strip().lower(),
        "tematicas": tematicas_bd,
    })

@require_POST
def guardar_tematica(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de temáticas."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
        slug = str(payload.get("tema") or "").strip().lower()
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    if not slug:
        return JsonResponse({"ok": False, "error": "Debes seleccionar una temática."}, status=400)

    tematica = Tematica.objects.filter(slug=slug, activa=True).first()

    if not tematica:
        return JsonResponse({"ok": False, "error": "Temática no válida."}, status=404)

    grupo.tema_elegido = tematica.slug

    grupo.save(update_fields=["tema_elegido"])

    return JsonResponse({
        "ok": True,
        "tema": tematica.slug,
        "redirect_url": reverse("desafios"),
    })

@never_cache
def desafios(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "desafios"):
        return redirect("pantalla_espera")

    slug = (grupo.tema_elegido or "").strip().lower()
    if not slug:
        return redirect("tematicas")

    tematica = Tematica.objects.filter(slug=slug, activa=True).first()
    if not tematica:
        return redirect("tematicas")

    desafios_bd = Desafio.objects.filter(
        tematica=tematica,
        activo=True
    ).order_by("orden", "nombredesafio")

    return render(request, "fase2/desafios.html", {
        "grupo": grupo,
        "tematica": tematica,
        "desafios": desafios_bd,
        "slug": slug,
        "desafio_confirmado": bool(grupo.listo_f2_desafio),
        "desafio_id_actual": str(grupo.desafio_id_externo or ""),
        "desafio_nombre_actual": grupo.desafio_nombre or "",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "",
    })
@require_POST
def guardar_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "La sesión no está en la etapa de desafíos."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
        desafio_id = str(payload.get("desafio_id") or "").strip()
    except Exception:
        return JsonResponse({"ok": False, "error": "Solicitud inválida."}, status=400)

    if not desafio_id:
        return JsonResponse({"ok": False, "error": "Debes seleccionar un desafío."}, status=400)

    tema = (grupo.tema_elegido or "").strip().lower()

    desafio = Desafio.objects.filter(
        iddesafio=desafio_id,
        tematica__slug=tema,
        activo=True
    ).first()

    if not desafio:
        return JsonResponse({"ok": False, "error": "Desafío no válido."}, status=404)

    grupo.desafio_elegido = desafio
    grupo.desafio_id_externo = str(desafio.iddesafio)
    grupo.desafio_nombre = desafio.nombredesafio or ""
    grupo.desafio_descripcion = desafio.descripciondesafio or ""
    grupo.listo_f2_desafio = True

    grupo.save(update_fields=[
        "desafio_elegido",
        "desafio_id_externo",
        "desafio_nombre",
        "desafio_descripcion",
        "listo_f2_desafio",
    ])

    return JsonResponse({
        "ok": True,
        "desafio_id": grupo.desafio_id_externo,
        "desafio_nombre": grupo.desafio_nombre,
        "desafio_descripcion": grupo.desafio_descripcion,
        "bloqueado": True,
    })

@require_POST
def desbloquear_desafio(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_tematicas":
        return JsonResponse({"ok": False, "error": "No puedes cambiar el desafío en esta etapa."}, status=400)

    grupo.listo_f2_desafio = False
    grupo.save(update_fields=["listo_f2_desafio"])

    return JsonResponse({"ok": True})

def transicionempatia(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")
    if not acceso_permitido(grupo, "transicionempatia"):
        return redirect("pantalla_espera")
    return render(request, "fase2/transicionempatia.html", {"grupo": grupo})

@never_cache
def bubblemap(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return redirect("registro")

    if not acceso_permitido(grupo, "bubblemap"):
        return redirect("pantalla_espera")

    grupo.refresh_from_db()
    sesion = grupo.sesion

    segundos = 180
    if sesion and sesion.segundos_restantes is not None:
        segundos = sesion.segundos_restantes

    return render(request, "fase2/bubblemap.html", {
        "grupo": grupo,
        "sesion": sesion,
        "desafio_nombre_actual": grupo.desafio_nombre or "Desafío no seleccionado",
        "desafio_descripcion_actual": grupo.desafio_descripcion or "Aún no hay descripción disponible para este desafío.",
        "desafio_foto_actual": (
            grupo.desafio_elegido.imagen_desafio.url
            if grupo.desafio_elegido and grupo.desafio_elegido.imagen_desafio
            else ""
        ),
        "segundos_restantes": segundos,
    })


@require_POST
def otorgar_tokens_bubblemap(request):
    grupo = obtener_grupo_desde_session(request)
    if not grupo:
        return JsonResponse({"ok": False, "error": "Grupo no encontrado."}, status=403)

    if grupo.sesion.fase_actual != "f2_bubblemap":
        return JsonResponse({"ok": False, "error": "La sesión no está en Bubble Map."}, status=400)

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    burbujas = payload.get("burbujas", [])
    relato = (payload.get("relato") or "").strip()
    link = (payload.get("link") or "").strip()

    def texto_valido(texto):
        return len((texto or "").strip()) >= 5

    def cantidad_palabras(texto):
        return len((texto or "").strip().split())

    respuestas_validas = []
    principales_validas = []
    respuestas_largas = []

    for item in burbujas:
        if isinstance(item, dict):
            texto = (item.get("texto") or "").strip()
            tipo = item.get("tipo") or ""
        else:
            texto = str(item).strip()
            tipo = "base"

        if texto_valido(texto):
            respuestas_validas.append(texto)

            if tipo == "base":
                principales_validas.append(texto)

            if cantidad_palabras(texto) >= 10:
                respuestas_largas.append(texto)

    relato_valido = cantidad_palabras(relato) >= 18
    link_valido = ("http://" in link.lower()) or ("https://" in link.lower()) or ("www." in link.lower())

    tokens = 0

    tokens += len(respuestas_validas)

    if len(respuestas_validas) >= 4:
        tokens += 2

    if len(principales_validas) >= 5:
        tokens += 3

    tokens += len(respuestas_largas)

    if relato_valido:
        tokens += 2

    if link_valido:
        tokens += 2

    nivel = "Inicial"
    if len(respuestas_validas) >= 3:
        nivel = "Intermedio"
    if len(principales_validas) >= 5:
        nivel = "Completo"
    if len(principales_validas) >= 5 and (relato_valido or link_valido):
        nivel = "Experto"

    with transaction.atomic():
        grupo = Grupo.objects.select_for_update().get(pk=grupo.pk)
        sesion = Sesion.objects.select_for_update().get(pk=grupo.sesion_id)

        if getattr(grupo, "bubble_tokens_otorgados", False):
            return JsonResponse({
                "ok": True,
                "ya_otorgados": True,
                "tokens_otorgados": 0,
                "tokens_totales": grupo.tokensgrupo or 0,
                "nivel": nivel,
                "rutaAlumno": reverse("ranking") if sesion.fase_actual == "f2_ranking" else reverse("bubblemap"),
            })
        BubbleMapRespuesta.objects.filter(
            sesion=sesion,
            grupo=grupo
        ).delete()

        for item in burbujas:
            if isinstance(item, dict):
                BubbleMapRespuesta.objects.create(
                    sesion=sesion,
                    grupo=grupo,
                    desafio=grupo.desafio_elegido,
                    tipo=item.get("tipo") or "",
                    titulo=item.get("titulo") or "",
                    texto=(item.get("texto") or "").strip(),
                    relato=relato,
                    link=link
                )

        grupo.tokensgrupo = (grupo.tokensgrupo or 0) + tokens
        grupo.bubble_tokens_otorgados = True
        grupo.save(update_fields=["tokensgrupo", "bubble_tokens_otorgados"])

        total = Grupo.objects.filter(sesion=sesion).count()
        terminados = Grupo.objects.filter(
            sesion=sesion,
            bubble_tokens_otorgados=True
        ).count()

        todos_terminaron = total > 0 and terminados == total

        if todos_terminaron:
            sesion.fase_actual = "f2_ranking"
            sesion.segundos_restantes = 0
            sesion.timer_corriendo = False
            sesion.timer_inicio_at = None
            sesion.timer_fin_at = None
            sesion.inicio_fase_habilitado = True
            sesion.save(update_fields=[
                "fase_actual",
                "segundos_restantes",
                "timer_corriendo",
                "timer_inicio_at",
                "timer_fin_at",
                "inicio_fase_habilitado",
            ])

            Grupo.objects.filter(sesion=sesion).update(
                listo_f6=False,
                listo_ranking=False,
            )

    return JsonResponse({
        "ok": True,
        "ya_otorgados": False,
        "tokens_otorgados": tokens,
        "tokens_totales": grupo.tokensgrupo,
        "nivel": nivel,
        "respuestas_validas": len(respuestas_validas),
        "principales_validas": len(principales_validas),
        "respuestas_largas": len(respuestas_largas),
        "relato_valido": relato_valido,
        "link_valido": link_valido,
        "todos_terminaron": todos_terminaron,
        "rutaAlumno": reverse("ranking") if todos_terminaron else reverse("bubblemap"),
    })
