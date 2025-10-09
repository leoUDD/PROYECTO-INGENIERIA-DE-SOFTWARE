# evaluation/views.py
from django.shortcuts import render

def peer_review_view(request, session_id):
    # Datos MOCK para que funcione sin BD (luego lo conectan a sus modelos)
    class Obj: pass
    session = Obj(); session.name = "Sesión Demo"
    evaluator_team = Obj(); evaluator_team.id = 1; evaluator_team.name = "Equipo Alpha"
    target_teams = []
    for i, name in [(2, "Equipo Beta"), (3, "Equipo Gamma"), (4, "Equipo Delta")]:
        t = Obj(); t.id = i; t.name = name; target_teams.append(t)

    criteria = [
        {"key": "claridad", "label": "Claridad de la solución"},
        {"key": "creatividad", "label": "Creatividad/Innovación"},
        {"key": "viabilidad", "label": "Viabilidad"},
        {"key": "equipo", "label": "Trabajo en equipo"},
        {"key": "presentacion", "label": "Presentación (TED)"},
    ]

    context = {
        "session": session,
        "evaluator_team": evaluator_team,
        "target_teams": target_teams,
        "criteria": criteria,
        "submitted": False,
    }

    if request.method == "POST":
        # Aquí podrías procesar y guardar; por ahora solo mostramos "enviado"
        context["submitted"] = True

    return render(request, "evaluation/peer_review.html", context)
