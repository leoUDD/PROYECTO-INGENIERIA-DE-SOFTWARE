FASES_ORDEN = [
    "intro_habilidades",
    "f1_bienvenida",
    "f1_conocidos",
    "f1_pre_sopa",
    "f1_sopa",
    "f1_ranking",

    "mapa_f2_empatia",
    "f2_transicion",
    "f2_tematicas",
    "f2_transicion_empatia",
    "f2_bubblemap",
    "f2_ranking",

    "mapa_f3_creatividad",
    "f3_transicion_creatividad",
    "f3_lego",
    "f3_ranking",

    "mapa_f4_final",
    "f4_transicion_comunicacion",
    "f4_construccion_pitch",
    "f4_orden_pitch",
    "f4_presentacion_pitch",
    "f5_evaluacion_pitch",

    "f6_ranking",
    "reflexion",
]


RUTA_POR_FASE = {
    "lobby": "pantalla_espera",
    "intro_habilidades": "habilidades_intro",
    "f1_bienvenida": "pantalla_inicio",
    "f1_conocidos": "promptconocidos",
    "f1_pre_sopa": "trabajoenequipo",
    "f1_sopa": "minijuego1",
    "f1_ranking": "ranking",

    "f2_transicion": "transiciondesafio",
    "f2_tematicas": "tematicas",
    "f2_transicion_empatia": "transicionempatia",
    "f2_bubblemap": "bubblemap",
    "f2_ranking": "ranking",
    "mapa_f2_empatia": "habilidades_intro",
    "mapa_f3_creatividad": "habilidades_intro",
    "mapa_f4_final": "habilidades_intro",

    "f3_transicion_creatividad": "transicioncreatividad",
    "f3_lego": "lego",
    "f3_ranking": "ranking",

    "f4_transicion_comunicacion": "transicioncomunicacion",
    "f4_construccion_pitch": "pitch",
    "f4_orden_pitch": "orden_presentacion_alumno",
    "f4_presentacion_pitch": "presentar_pitch",

    "f5_transicion_apoyo": "transicionapoyo",
    "f5_evaluacion_pitch": "peer_review",

    "f6_ranking": "ranking",
    "reflexion": "reflexion",
}

ETIQUETA_FASE = {

    "intro_habilidades": "Mapa · Trabajo en equipo",
    "mapa_f2_empatia": "Mapa · Empatía",
    "mapa_f3_creatividad": "Mapa · Creatividad",
    "mapa_f4_final": "Mapa · Misión final",
    "f1_bienvenida": "F1 · Bienvenida",
    "f1_conocidos": "F1 · Conocerse",
    "f1_pre_sopa": "F1 · Trabajo en equipo",
    "f1_sopa": "F1 · Sopa de letras",
    "f1_ranking": "F1 · Ranking",

    "f2_transicion": "F2 · Desafíos",
    "f2_tematicas": "F2 · Temáticas",
    "f2_transicion_empatia": "F2 · Transición Empatía",
    "f2_bubblemap": "F2 · Bubble Map",
    "f2_ranking": "F2 · Ranking",

    "f3_transicion_creatividad": "F3 · Transición Creatividad",
    "f3_lego": "F3 · Lego",
    "f3_ranking": "F3 · Ranking",

    "f4_transicion_comunicacion": "F4 · Transición Comunicación",
    "f4_construccion_pitch": "F4 · Construcción pitch",
    "f4_orden_pitch": "F4 · Sorteo orden pitch",
    "f4_presentacion_pitch": "F4 · Presentación pitch",

    "f5_transicion_apoyo": "F5 · Transición Apoyo",
    "f5_evaluacion_pitch": "F5 · Evaluación pitch",

    "f6_ranking": "Ranking final",
    "reflexion": "Cierre",
}

FASES_CON_INICIO_POR_ALUMNOS = {
    "f1_conocidos",
    "f1_sopa",
    "f2_tematicas",
    "f2_bubblemap",
    "f3_lego",
    "f4_construccion_pitch",
}
