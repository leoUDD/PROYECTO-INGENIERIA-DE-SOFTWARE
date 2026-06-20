from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from juego.models import Grupo

from juego.backend.core_global.services import (
    obtener_grupo_desde_session,
    acceso_permitido,
)

def ranking_view(request):
    grupo_id = request.session.get("grupo_id")
    if not grupo_id:
        messages.error(request, "No pudimos identificar tu grupo.")
        return redirect("registro")

    grupo_actual = get_object_or_404(Grupo, pk=grupo_id)
    sesion = grupo_actual.sesion

    if not sesion:
        messages.error(request, "Tu grupo no está asociado a ninguna sesión.")
        return redirect("registro")

    grupos = (
        Grupo.objects
        .filter(sesion=sesion)
        .order_by("-tokensgrupo", "idgrupo")
    )

    rankings = []
    last_tokens = None
    current_rank = 0
    position = 0

    for g in grupos:
        position += 1
        tokens = g.tokensgrupo or 0

        if tokens != last_tokens:
            current_rank = position
            last_tokens = tokens

        rankings.append({
            "team_name": g.nombregrupo or f"Grupo {g.idgrupo}",
            "tokens": tokens,
            "is_me": g.idgrupo == grupo_actual.idgrupo,
            "rank": current_rank,
        })

    context = {
        "session": sesion,
        "grupo": grupo_actual,
        "rankings": rankings,
    }
    return render(request, "ranking/ranking.html", context)

@require_POST
def marcar_listo_ranking(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)

    grupo.listo_ranking = True
    grupo.save(update_fields=["listo_ranking"])

    sesion = grupo.sesion
    total_grupos = Grupo.objects.filter(sesion=sesion).count()
    grupos_listos_ranking = Grupo.objects.filter(sesion=sesion, listo_ranking=True).count()


    return JsonResponse({
        "ok": True,
        "grupoId": grupo.idgrupo,
        "listoRanking": True,
        "gruposListosRanking": grupos_listos_ranking,
        "totalGrupos": total_grupos,
        "todosListosRanking": total_grupos > 0 and grupos_listos_ranking == total_grupos,
    })