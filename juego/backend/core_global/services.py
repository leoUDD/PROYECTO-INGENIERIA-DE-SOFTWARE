from juego.backend.core_global.constants import (
    RUTA_POR_FASE,
    FASES_CON_INICIO_POR_ALUMNOS,
)

from juego.models import Grupo

from django.utils import timezone

# CAMBIAR TIMERS
def tiempo_por_fase(sesion, fase):
    tiempos = {
        "f1_conocidos": getattr(sesion, "t_rompehielo", 10),
        "f1_pre_sopa": 0,
        "f1_sopa": getattr(sesion, "t_diferencias", 60),
        "f1_ranking": 0,

        "f2_transicion": 0,
        "f2_tematicas": getattr(sesion, "t_tematicas", 120),
        "f2_transicion_empatia": 0,
        "f2_bubblemap": getattr(sesion, "t_empatia", 10),
        "f2_ranking": 0,

        "f3_transicion_creatividad": 0,
        "f3_lego": getattr(sesion, "t_creatividad", 10),
        "f3_ranking": 0,

        "f4_transicion_comunicacion": 0,
        "f4_construccion_pitch": getattr(sesion, "t_pitch_prep", 10),
        "f4_orden_pitch": 0,
        "f4_presentacion_pitch": 90,

        "f5_evaluacion_pitch": 90,
        "f6_ranking": 0,
        "reflexion": 0,
        "f1_bienvenida": 0,
        "lobby": 0,
    }

    return int(tiempos.get(fase, 0))


def reset_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)

    if fase == "f1_conocidos":
        grupos.update(listo_lobby=False)

    elif fase == "f1_sopa":
        grupos.update(
            listo_f1=False,
            sopa_ganada=False,
            sopa_tiempo_segundos=None,
            sopa_completada_en=None,
        )

    elif fase == "f2_bubblemap":
        grupos.update(listo_f2=False, bubble_tokens_otorgados=False)

    elif fase == "f3_lego":
        grupos.update(listo_inicio_f3=False)
        grupos.update(listo_f3=False)

    elif fase == "f2_tematicas":
        grupos.update(
            listo_f2_tematicas=False,
        listo_f2_desafio=False,
    )

    elif fase == "f4_construccion_pitch":
        grupos.update(listo_f4=False)

    sesion.inicio_fase_habilitado = False
    sesion.save(update_fields=["inicio_fase_habilitado"])


def borrar_fotos_lego_sesion(sesion):

    grupos = Grupo.objects.filter(
        sesion=sesion,
        foto_lego__isnull=False,
    ).exclude(foto_lego="")

    for grupo in grupos:
        borrar_foto_lego_grupo(grupo)

def autoavanzar_si_todos_listos(sesion):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if total == 0:
        return False

    fase_actual = sesion.fase_actual
    nueva_fase = None

    if fase_actual == "f1_bienvenida":
        if grupos.filter(listo_lobby=True).count() == total:
            nueva_fase = "f1_conocidos"

    elif fase_actual == "f1_pre_sopa":
        if grupos.filter(listo_f1=True).count() == total:
            nueva_fase = "f1_sopa"

    elif fase_actual == "f1_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f2_empatia"

    elif fase_actual == "f2_transicion":
        if grupos.filter(listo_f2=True).count() == total:
            nueva_fase = "f2_tematicas"

    elif fase_actual == "f2_tematicas":
        if grupos.filter(listo_f2_desafio=True).count() == total:
            nueva_fase = "f2_transicion_empatia"

    elif fase_actual == "f2_transicion_empatia":
        if grupos.filter(listo_f2_empatia=True).count() == total:
            nueva_fase = "f2_bubblemap"

    elif fase_actual == "f2_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f3_creatividad"

    elif fase_actual == "f3_transicion_creatividad":
        if grupos.filter(listo_f3=True).count() == total:
            nueva_fase = "f3_lego"

    elif fase_actual == "f3_lego":
        if grupos.filter(listo_f3_lego=True).count() == total:
            nueva_fase = "f3_ranking"

    elif fase_actual == "f3_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "mapa_f4_final"

    elif fase_actual == "f4_transicion_comunicacion":
        if grupos.filter(listo_f4=True).count() == total:
            nueva_fase = "f4_construccion_pitch"

    elif fase_actual == "f4_orden_pitch":
        listos_orden = grupos.filter(listo_f4_orden=True).count()

        if not sesion.orden_sorteado:
            if listos_orden == total:
                grupos_lista = list(
                    Grupo.objects.filter(sesion=sesion).order_by("idgrupo")
                )
                random.shuffle(grupos_lista)

                for i, grupo in enumerate(grupos_lista, start=1):
                    grupo.orden_presentacion = i
                    grupo.save(update_fields=["orden_presentacion"])

                sesion.orden_sorteado = True
                sesion.grupo_presentando = sorted(
                    grupos_lista,
                    key=lambda g: g.orden_presentacion
                )[0]

                Grupo.objects.filter(sesion=sesion).update(listo_f4_orden=False)

                sesion.segundos_restantes = 0
                sesion.timer_corriendo = False
                sesion.timer_inicio_at = None
                sesion.timer_fin_at = None
                sesion.inicio_fase_habilitado = True
                sesion.save(update_fields=[
                    "orden_sorteado",
                    "grupo_presentando",
                    "segundos_restantes",
                    "timer_corriendo",
                    "timer_inicio_at",
                    "timer_fin_at",
                    "inicio_fase_habilitado",
                ])
                return True

        else:
            if listos_orden == total:
                nueva_fase = "f4_presentacion_pitch"

    elif fase_actual == "f6_ranking":
        if grupos.filter(listo_f6=True).count() == total:
            nueva_fase = "reflexion"
            borrar_fotos_lego_sesion(sesion)

    if not nueva_fase:
        return False

    sesion.fase_actual = nueva_fase
    sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)
    sesion.timer_corriendo = False
    sesion.timer_inicio_at = None
    sesion.timer_fin_at = None

    if nueva_fase in {"f5_evaluacion_pitch"}:
        ahora = timezone.now()
        sesion.timer_corriendo = sesion.segundos_restantes > 0
        sesion.timer_inicio_at = ahora if sesion.timer_corriendo else None
        sesion.timer_fin_at = ahora + timedelta(seconds=sesion.segundos_restantes) if sesion.timer_corriendo else None

    if nueva_fase in {"f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"}:
        Grupo.objects.filter(sesion=sesion).update(
            listo_f6=False,
            listo_ranking=False,
        )

    if nueva_fase == "f4_presentacion_pitch":
        sesion.grupo_presentando = Grupo.objects.filter(
            sesion=sesion,
            orden_presentacion__isnull=False
        ).order_by("orden_presentacion").first()

    if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
        sesion.inicio_fase_habilitado = False
        sesion.save(update_fields=[
            "fase_actual",
            "segundos_restantes",
            "timer_corriendo",
            "timer_inicio_at",
            "timer_fin_at",
            "inicio_fase_habilitado",
            "grupo_presentando",
        ])
        reset_listos_inicio_fase(sesion, nueva_fase)
        return True

    sesion.inicio_fase_habilitado = True
    sesion.save(update_fields=[
        "fase_actual",
        "segundos_restantes",
        "timer_corriendo",
        "timer_inicio_at",
        "timer_fin_at",
        "inicio_fase_habilitado",
        "grupo_presentando",
    ])
    return True


def contar_listos_inicio_fase(sesion, fase):
    grupos = Grupo.objects.filter(sesion=sesion)
    total = grupos.count()

    if fase == "f1_conocidos":
        listos = grupos.filter(listo_lobby=True).count()

    elif fase == "f1_sopa":
        listos = grupos.filter(listo_f1=True).count()

    elif fase == "f2_tematicas":
        listos = grupos.filter(listo_f2_tematicas=True).count()

    elif fase == "f2_bubblemap":
        listos = grupos.filter(listo_f2=True).count()

    elif fase == "f3_lego":
        listos = grupos.filter(listo_inicio_f3=True).count()

    elif fase == "f4_construccion_pitch":
        listos = grupos.filter(listo_f4=True).count()

    else:
        listos = total

    return total, listos, (total > 0 and listos == total)

def siguiente_fase_automatica(fase_actual):
    try:
        idx = FASES_ORDEN.index(fase_actual)
        if idx + 1 < len(FASES_ORDEN):
            return FASES_ORDEN[idx + 1]
    except ValueError:
        pass

    return fase_actual

def calcular_segundos_restantes(sesion):
    if not sesion.timer_corriendo or not sesion.timer_fin_at:
        return max(int(sesion.segundos_restantes or 0), 0)

    restantes = int((sesion.timer_fin_at - timezone.now()).total_seconds())

    if restantes <= 0:
        fase_vencida = sesion.fase_actual

        sesion.timer_corriendo = False
        sesion.segundos_restantes = 0
        sesion.timer_inicio_at = None
        sesion.timer_fin_at = None

        # ===================== F4 PRESENTACION PITCH =====================
        if fase_vencida == "f4_presentacion_pitch":
            sesion.fase_actual = "f5_evaluacion_pitch"
            sesion.save(update_fields=[
                "fase_actual",
                "timer_corriendo",
                "segundos_restantes",
                "timer_inicio_at",
                "timer_fin_at",
            ])
            return 0

        # ===================== F2 TEMATICAS =====================
        fases_con_autoavance = {
            "f1_conocidos",
            "f1_sopa",
            "f4_construccion_pitch",
        }

        if fase_vencida == "f2_tematicas":
            asignar_tematica_y_desafio_aleatorio(sesion)
            sesion.fase_actual = "f2_transicion_empatia"
            sesion.segundos_restantes = tiempo_por_fase(sesion, "f2_transicion_empatia")
            sesion.save(update_fields=[
                "fase_actual",
                "timer_corriendo",
                "segundos_restantes",
                "timer_inicio_at",
                "timer_fin_at",
            ])
            return 0

        # ===================== F5 EVALUACION PITCH =====================
        if fase_vencida == "f5_evaluacion_pitch":
            # 1️⃣ Completar evaluaciones faltantes (penalización a los que no enviaron)
            completar_evaluaciones_faltantes(sesion)

            # 2️⃣ Recompensar al/los grupo(s) mejor evaluado(s) según los puntajes recibidos
            evaluaciones = Evaluacion.objects.filter(sesion=sesion)
            puntaje_recibido = {}  # {grupo_id: total_puntaje}

            for e in evaluaciones:
                total = (e.claridad or 0) + (e.creatividad or 0) + (e.viabilidad or 0) + (e.equipo or 0) + (e.presentacion or 0)
                gid = e.grupo_evaluado.id
                puntaje_recibido[gid] = puntaje_recibido.get(gid, 0) + total

            if puntaje_recibido:
                max_puntaje = max(puntaje_recibido.values())
                mejores = [gid for gid, puntaje in puntaje_recibido.items() if puntaje == max_puntaje]

                for gid in mejores:
                    grupo = Grupo.objects.get(pk=gid)
                    grupo.tokensgrupo = (grupo.tokensgrupo or 0) + 3
                    grupo.save(update_fields=["tokensgrupo"])

            # 3️⃣ Avanzar al siguiente pitch o ranking
            avanzar_al_siguiente_pitch_o_ranking(sesion)
            return 0

        # ===================== OTRAS FASES CON AUTOAVANCE =====================
        if fase_vencida in fases_con_autoavance:
            nueva_fase = siguiente_fase_automatica(fase_vencida)
            sesion.fase_actual = nueva_fase
            sesion.segundos_restantes = tiempo_por_fase(sesion, nueva_fase)

            if nueva_fase in FASES_CON_INICIO_POR_ALUMNOS:
                sesion.inicio_fase_habilitado = False
                sesion.save(update_fields=[
                    "fase_actual",
                    "timer_corriendo",
                    "segundos_restantes",
                    "timer_inicio_at",
                    "timer_fin_at",
                    "inicio_fase_habilitado",
                ])
                reset_listos_inicio_fase(sesion, nueva_fase)
                return 0

        sesion.save(update_fields=[
            "fase_actual",
            "timer_corriendo",
            "segundos_restantes",
            "timer_inicio_at",
            "timer_fin_at",
        ])
        return 0

    return max(restantes, 0)

def obtener_grupo_desde_session(request):
    grupo_id = request.session.get("grupo_id")
    sesion_id = request.session.get("sesion_id")

    print("obtener_grupo_desde_session -> grupo_id:", grupo_id, "| sesion_id:", sesion_id)

    if not grupo_id or not sesion_id:
        return None

    try:
        grupo = Grupo.objects.select_related("sesion").get(
            pk=grupo_id,
            sesion_id=sesion_id,
        )
    except Grupo.DoesNotExist:
        print("obtener_grupo_desde_session -> grupo no existe, flush session")
        request.session.flush()
        return None

    print("obtener_grupo_desde_session -> grupo real:", grupo.idgrupo, "| nombre:", grupo.nombregrupo)
    return grupo

def acceso_permitido(grupo, nombre_vista):
    if not grupo or not grupo.sesion:
        return False

    fases_por_vista = {
        "pantalla_espera": ["lobby"],

        "pantalla_inicio": ["f1_bienvenida"],
        "conocidos": ["f1_conocidos"],
        "promptconocidos": ["f1_conocidos"],
        "conocidos_rapido": ["f1_conocidos"],
        "trabajoenequipo": ["f1_pre_sopa"],
        "minijuego1": ["f1_sopa"],

        "transiciondesafio": ["f2_transicion"],
        "tematicas": ["f2_tematicas"],
        "desafios": ["f2_tematicas"],
        "transicionempatia": ["f2_transicion_empatia"],
        "bubblemap": ["f2_bubblemap"],

        "transicioncreatividad": ["f3_transicion_creatividad"],
        "lego": ["f3_lego"],

        "transicioncomunicacion": ["f4_transicion_comunicacion"],
        "pitch": ["f4_construccion_pitch"],
        "orden_presentacion_alumno": ["f4_orden_pitch"],
        "presentar_pitch": ["f4_presentacion_pitch"],

        "transicionapoyo": ["f5_transicion_apoyo"],
        "peer_review": ["f5_evaluacion_pitch"],
        "mision_cumplida": ["f5_evaluacion_pitch"],

        "ranking": ["f1_ranking", "f2_ranking", "f3_ranking", "f6_ranking"],
        "reflexion": ["reflexion"],
    }

    return grupo.sesion.fase_actual in fases_por_vista.get(nombre_vista, [])

def ruta_alumno_por_estado(grupo):
    fase = grupo.sesion.fase_actual

    if fase == "f2_tematicas":
        if not (grupo.tema_elegido or "").strip():
            return "tematicas"
        return "desafios"

    if fase == "f5_evaluacion_pitch":
        return "peer_review"

    return RUTA_POR_FASE.get(fase, "pantalla_espera")