def guardar_imagen_tematica(request_file):

    if not request_file:
        return ""

    nombre_webp, contenido_webp = convertir_imagen_a_webp(
        request_file,
        max_size=(1400, 900),
        quality=80,
    )

    ruta = default_storage.save(f"tematicas/{nombre_webp}", contenido_webp)

    return settings.MEDIA_URL + ruta

def porcentaje(parte, total):
    if not total:
        return 0
    return round((parte / total) * 100)