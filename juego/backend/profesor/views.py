def dashboardprofesor(request):
    profesor = Profesor.objects.first()
    sesion = None

    if profesor:
        sesion = Sesion.objects.filter(profesor=profesor).order_by("-fecha_creacion").first()

    return render(request, "dashboardprofesor.html", {"sesion": sesion})

def registrarprofesor(request):
    if request.method == "POST":
        email = request.POST.get("email")
        facultad = request.POST.get("facultad")

        if email and facultad:
            usuario = Usuario.objects.create(password="temp")

            Profesor.objects.create(
                usuario_idusuario=usuario,
                emailprofesor=email,
                facultad=facultad
            )

            messages.success(request, "Profesor registrado correctamente.")
            return redirect("registrarprofesor")

    profesores = Profesor.objects.all().order_by("emailprofesor")

    return render(request, "registrarprofesor.html", {
        "profesores": profesores
    })
@require_POST
def eliminar_profesor(request, profesor_id):
    profesor = get_object_or_404(Profesor, idprofesor=profesor_id)

    alumnos_asociados = Alumno.objects.filter(profesor_idprofesor=profesor).count()
    sesiones_asociadas = Sesion.objects.filter(profesor=profesor).count()

    if alumnos_asociados > 0 or sesiones_asociadas > 0:
        messages.warning(
            request,
            f"No se puede eliminar directamente. Tiene {alumnos_asociados} alumnos y {sesiones_asociadas} sesiones asociadas. "
            f"Usa eliminación forzada si quieres borrar todo lo relacionado."
        )
        return redirect("registrarprofesor")

    try:
        with transaction.atomic():
            usuario = profesor.usuario_idusuario
            profesor.delete()
            if not Profesor.objects.filter(usuario_idusuario=usuario).exists():
                usuario.delete()
        messages.success(request, "Profesor eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar: {e}")

    return redirect("registrarprofesor")


@require_POST
def eliminar_profesor_forzado(request, profesor_id):
    profesor = get_object_or_404(Profesor, idprofesor=profesor_id)

    Alumno.objects.filter(profesor_idprofesor=profesor).delete()
    Sesion.objects.filter(profesor=profesor).delete()

    profesor.delete()

    messages.success(request, "Profesor y datos asociados eliminados correctamente.")
    return redirect("registrarprofesor")