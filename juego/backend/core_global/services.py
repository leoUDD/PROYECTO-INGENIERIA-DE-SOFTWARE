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