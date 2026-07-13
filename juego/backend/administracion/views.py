from juego.backend.administracion.services import (
    guardar_imagen_tematica,
    porcentaje,
)


def dashboardadmin(request):
    total_grupos = Grupo.objects.count()

    grupos_sopa = Grupo.objects.filter(sopa_ganada=True).count()
    grupos_pitch = Grupo.objects.exclude(pitch_texto__isnull=True).exclude(pitch_texto__exact="").count()
    grupos_lego = Grupo.objects.exclude(foto_lego__isnull=True).exclude(foto_lego__exact="").count()

    tematicas_raw = (
        Grupo.objects
        .exclude(tema_elegido__isnull=True)
        .exclude(tema_elegido__exact="")
        .values("tema_elegido")
        .annotate(total=Count("idgrupo"))
        .order_by("-total")[:5]
    )

    max_tematica = max([x["total"] for x in tematicas_raw], default=0)

    tematicas_stats = []
    for item in tematicas_raw:
        nombre = item["tema_elegido"]
        tematica = Tematica.objects.filter(slug=nombre).first()
        tematicas_stats.append({
            "nombre": tematica.title if tematica else nombre,
            "total": item["total"],
            "porcentaje": porcentaje(item["total"], max_tematica),
        })

    desafios_raw = (
        Grupo.objects
        .exclude(desafio_nombre__isnull=True)
        .exclude(desafio_nombre__exact="")
        .values("desafio_nombre")
        .annotate(total=Count("idgrupo"))
        .order_by("-total")[:5]
    )

    max_desafio = max([x["total"] for x in desafios_raw], default=0)

    desafios_stats = [
        {
            "nombre": item["desafio_nombre"],
            "total": item["total"],
            "porcentaje": porcentaje(item["total"], max_desafio),
        }
        for item in desafios_raw
    ]

    sesiones_recientes = []
    for sesion in Sesion.objects.all().order_by("-idsesion")[:6]:
        grupos = Grupo.objects.filter(sesion=sesion)
        total = grupos.count()

        sesiones_recientes.append({
            "nombre": f"Sesión {sesion.idsesion}",
            "fase_actual": sesion.fase_actual,
            "total_grupos": total,
            "sopa": porcentaje(grupos.filter(sopa_ganada=True).count(), total),
            "pitch": porcentaje(
                grupos.exclude(pitch_texto__isnull=True).exclude(pitch_texto__exact="").count(),
                total
            ),
            "lego": porcentaje(
                grupos.exclude(foto_lego__isnull=True).exclude(foto_lego__exact="").count(),
                total
            ),
        })

    kpis = {
        "profesores": Profesor.objects.count(),
        "grupos": total_grupos,
        "sesiones": Sesion.objects.count(),
        "desafios_activos": Desafio.objects.filter(activo=True).count(),
        "pct_sopa": porcentaje(grupos_sopa, total_grupos),
        "pct_pitch": porcentaje(grupos_pitch, total_grupos),
        "pct_lego": porcentaje(grupos_lego, total_grupos),
    }

    return render(request, "dashboardadmin.html", {
        "kpis": kpis,
        "tematicas_stats": tematicas_stats,
        "desafios_stats": desafios_stats,
        "sesiones_recientes": sesiones_recientes,
    })

def admin_desafios(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "editar_desafio":
            desafio_id = request.POST.get("desafio_id")
            desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

            desafio.nombredesafio = request.POST.get("nombre", "").strip()
            desafio.summary = request.POST.get("summary", "").strip()
            desafio.descripciondesafio = request.POST.get("descripcion", "").strip()
            desafio.activo = bool(request.POST.get("activo"))

            tematica_id = request.POST.get("tematica_id")
            if tematica_id:
                desafio.tematica = Tematica.objects.filter(idtematica=tematica_id).first()

            if request.FILES.get("imagen_desafio"):
                desafio.imagen_desafio = request.FILES.get("imagen_desafio")

            desafio.save()
            messages.success(request, "Desafío actualizado correctamente.")
            return redirect("admin_desafios")

        if accion == "crear_desafio":
            nombre = request.POST.get("nombre", "").strip()
            summary = request.POST.get("summary", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tematica_id = request.POST.get("tematica_id")

            tematica = Tematica.objects.filter(idtematica=tematica_id).first()

            if nombre and tematica:
                desafio = Desafio.objects.create(
                    tematica=tematica,
                    nombredesafio=nombre,
                    summary=summary,
                    descripciondesafio=descripcion,
                    activo=True,
                    orden=tematica.desafios.count() + 1
                )

                if request.FILES.get("imagen_desafio"):
                    desafio.imagen_desafio = request.FILES.get("imagen_desafio")
                    desafio.save()

                messages.success(request, "Desafío creado correctamente.")
            else:
                messages.error(request, "Debes completar nombre y temática.")

            return redirect("admin_desafios")

        if accion == "eliminar_desafio":
            desafio_id = request.POST.get("desafio_id")
            desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

            if Grupo.objects.filter(desafio_elegido=desafio).exists():
                messages.warning(request, "No se puede eliminar porque ya fue elegido por grupos. Puedes desactivarlo.")
            else:
                desafio.delete()
                messages.success(request, "Desafío eliminado correctamente.")

            return redirect("admin_desafios")

    desafios = []

    for desafio in Desafio.objects.select_related("tematica").all().order_by("tematica__orden", "orden"):
        grupos_desafio = Grupo.objects.filter(desafio_elegido=desafio)

        if not grupos_desafio.exists():
            grupos_desafio = Grupo.objects.filter(desafio_id_externo=str(desafio.iddesafio))

        desafios.append({
            "id": desafio.iddesafio,
            "nombre": desafio.nombredesafio,
            "summary": desafio.summary,
            "descripcion": desafio.descripciondesafio,
            "activo": desafio.activo,
            "tematica_id": desafio.tematica.idtematica if desafio.tematica else "",
            "tematica": desafio.tematica.title if desafio.tematica else "Sin temática",
            "total_usos": grupos_desafio.count(),
            "grupos": grupos_desafio.order_by("-idgrupo")[:10],
            "imagen": desafio.imagen_desafio.url if desafio.imagen_desafio else "",
        })

    return render(request, "admin_desafios.html", {
        "desafios": desafios,
        "tematicas": Tematica.objects.filter(activa=True).order_by("orden", "title"),
    })

def admin_tematicas(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear_tematica":
            title = request.POST.get("title", "").strip()
            hero = request.POST.get("hero", "").strip()
            chips_raw = request.POST.get("chips", "").strip()
            accent = request.POST.get("accent", "#3b82f6").strip()

            if title and hero:
                slug_base = slugify(title)
                slug = slug_base
                contador = 1

                while Tematica.objects.filter(slug=slug).exists():
                    contador += 1
                    slug = f"{slug_base}-{contador}"

                image = guardar_imagen_tematica(request.FILES.get("image_file"))

                tematica = Tematica.objects.create(
                    slug=slug,
                    title=title,
                    hero=hero,
                    chips=[c.strip() for c in chips_raw.split(",") if c.strip()],
                    accent=accent,
                    image=image,
                    activa=True,
                    orden=Tematica.objects.count() + 1
                )

                if request.POST.get("crear_desafio_ahora"):
                    nombre = request.POST.get("desafio_nombre", "").strip()
                    summary = request.POST.get("desafio_summary", "").strip()
                    desc = request.POST.get("desafio_desc", "").strip()

                    if nombre:
                        Desafio.objects.create(
                            tematica=tematica,
                            nombredesafio=nombre,
                            summary=summary,
                            descripciondesafio=desc,
                            activo=True,
                            orden=tematica.desafios.count() + 1
                        )

                messages.success(request, "Temática creada correctamente.")
            else:
                messages.error(request, "Debes completar nombre y descripción de la temática.")

            return redirect("admin_tematicas")

        if accion == "editar_tematica":
            tematica_id = request.POST.get("tematica_id")
            tematica = get_object_or_404(Tematica, idtematica=tematica_id)

            tematica.title = request.POST.get("title", "").strip()
            tematica.hero = request.POST.get("hero", "").strip()
            tematica.chips = [c.strip() for c in request.POST.get("chips", "").split(",") if c.strip()]
            tematica.accent = request.POST.get("accent", "#3b82f6").strip()
            tematica.activa = bool(request.POST.get("activa"))

            nueva_imagen = guardar_imagen_tematica(request.FILES.get("image_file"))
            if nueva_imagen:
                tematica.image = nueva_imagen

            tematica.save()
            messages.success(request, "Temática actualizada correctamente.")
            return redirect("admin_tematicas")

        if accion == "eliminar_tematica":
            tematica_id = request.POST.get("tematica_id")
            tematica = get_object_or_404(Tematica, idtematica=tematica_id)

            if tematica.desafios.exists():
                messages.warning(request, "No se puede eliminar porque tiene desafíos asociados. Elimina o reasigna esos desafíos primero.")
            else:
                tematica.delete()
                messages.success(request, "Temática eliminada correctamente.")

            return redirect("admin_tematicas")

    tematicas = []

    for tematica in Tematica.objects.all().order_by("orden", "title"):
        grupos_tematica = Grupo.objects.filter(tema_elegido=tematica.slug)

        desafios = []
        for desafio in tematica.desafios.all().order_by("orden", "nombredesafio"):
            usos = Grupo.objects.filter(desafio_elegido=desafio).count()

            if usos == 0:
                usos = Grupo.objects.filter(desafio_id_externo=str(desafio.iddesafio)).count()

            desafios.append({
                "id": desafio.iddesafio,
                "nombre": desafio.nombredesafio,
                "total_usos": usos,
            })

        desafios = sorted(desafios, key=lambda x: x["total_usos"], reverse=True)

        tematicas.append({
            "id": tematica.idtematica,
            "slug": tematica.slug,
            "title": tematica.title,
            "hero": tematica.hero,
            "chips_texto": ", ".join(tematica.chips or []),
            "accent": tematica.accent,
            "image": tematica.image,
            "activa": tematica.activa,
            "total_usos": grupos_tematica.count(),
            "total_desafios": tematica.desafios.count(),
            "desafios": desafios,
        })

    return render(request, "admin_tematicas.html", {
        "tematicas": tematicas,
    })

def admin_desafio_info(request, desafio_id):
    desafio = get_object_or_404(Desafio, iddesafio=desafio_id)

    grupos = Grupo.objects.filter(
        desafio_elegido=desafio
    ).select_related("sesion").order_by("-idgrupo")

    if not grupos.exists():
        grupos = Grupo.objects.filter(
            desafio_id_externo=str(desafio.iddesafio)
        ).select_related("sesion").order_by("-idgrupo")

    return render(request, "admin_desafio_info.html", {
        "desafio": desafio,
        "grupos": grupos,
    })




def admin_ruleta(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "guardar_todo":
            ids = request.POST.getlist("opcion_id")

            opciones_temporales = []

            for opcion_id in ids:
                opciones_temporales.append({
                    "id": int(opcion_id),
                    "titulo": request.POST.get(f"titulo_{opcion_id}", "").strip(),
                    "emoji": request.POST.get(f"emoji_{opcion_id}", "").strip(),
                    "descripcion": request.POST.get(f"descripcion_{opcion_id}", "").strip(),
                    "tokens": int(request.POST.get(f"tokens_{opcion_id}") or 0),
                    "porcentaje": int(request.POST.get(f"porcentaje_{opcion_id}") or 0),
                    "activa": request.POST.get(f"activa_{opcion_id}") == "on",
                })

            activas = [o for o in opciones_temporales if o["activa"]]
            total_porcentaje = sum(o["porcentaje"] for o in activas)

            if len(activas) > 8:
                messages.error(request, "No se puede guardar. La ruleta permite máximo 8 opciones activas.")
                return redirect("admin_ruleta")

            if total_porcentaje != 100:
                messages.error(request, f"No se puede guardar. Las opciones activas suman {total_porcentaje}%. Deben sumar exactamente 100%.")
                return redirect("admin_ruleta")

            with transaction.atomic():
                for data in opciones_temporales:
                    opcion = RuletaLegoOpcion.objects.get(idopcion=data["id"])
                    opcion.titulo = data["titulo"]
                    opcion.emoji = data["emoji"]
                    opcion.descripcion = data["descripcion"]
                    opcion.tokens = data["tokens"]
                    opcion.porcentaje = data["porcentaje"]
                    opcion.activa = data["activa"]
                    opcion.save()

            messages.success(request, "Ruleta guardada correctamente.")
            return redirect("admin_ruleta")

        if accion == "crear":
            if RuletaLegoOpcion.objects.count() >= 8:
                messages.error(request, "No se puede crear otra opción. La ruleta permite máximo 8 opciones.")
                return redirect("admin_ruleta")

            titulo = request.POST.get("titulo", "").strip()
            emoji = request.POST.get("emoji", "").strip()
            descripcion = request.POST.get("descripcion", "").strip()
            tokens = int(request.POST.get("tokens") or 0)
            porcentaje = int(request.POST.get("porcentaje") or 0)

            codigo_base = slugify(titulo)
            codigo = codigo_base
            contador = 1

            while RuletaLegoOpcion.objects.filter(codigo=codigo).exists():
                contador += 1
                codigo = f"{codigo_base}-{contador}"

            RuletaLegoOpcion.objects.create(
                codigo=codigo,
                emoji=emoji,
                titulo=titulo,
                descripcion=descripcion,
                tokens=tokens,
                porcentaje=porcentaje,
                activa=False,
                orden=RuletaLegoOpcion.objects.count() + 1
            )

            messages.success(request, "Opción creada como inactiva. Ajusta la ruleta completa y luego presiona Guardar ruleta completa.")
            return redirect("admin_ruleta")

        if accion == "eliminar":
            opcion = get_object_or_404(RuletaLegoOpcion, idopcion=request.POST.get("opcion_id"))
            opcion.delete()
            messages.success(request, "Opción eliminada. Revisa que la ruleta activa siga sumando 100%.")
            return redirect("admin_ruleta")

    opciones = RuletaLegoOpcion.objects.all().order_by("orden", "titulo")
    total_porcentaje = sum(o.porcentaje for o in opciones if o.activa)
    total_activas = sum(1 for o in opciones if o.activa)

    return render(request, "admin_ruleta.html", {
        "opciones": opciones,
        "total_porcentaje": total_porcentaje,
        "total_activas": total_activas,
    })

def admin_tiempos(request):
    if request.method == "POST":
        ids = request.POST.getlist("tiempo_id")

        for tiempo_id in ids:
            tiempo = get_object_or_404(TiempoFase, idtiempo=tiempo_id)
            tiempo.segundos = int(request.POST.get(f"segundos_{tiempo_id}") or 60)
            tiempo.activo = request.POST.get(f"activo_{tiempo_id}") == "on"
            tiempo.save(update_fields=["segundos", "activo"])

        messages.success(request, "Tiempos actualizados correctamente.")
        return redirect("admin_tiempos")

    tiempos = TiempoFase.objects.all().order_by("orden", "nombre")

    return render(request, "admin_tiempos.html", {
        "tiempos": tiempos,
    })

