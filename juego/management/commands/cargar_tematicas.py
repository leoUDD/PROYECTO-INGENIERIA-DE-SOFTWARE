from django.core.management.base import BaseCommand
from juego.models import Tematica, Desafio
from juego.tematicas_data import THEMES


class Command(BaseCommand):
    help = "Carga las temáticas y desafíos desde tematicas_data.py a la base de datos"

    def handle(self, *args, **options):
        for orden_tema, (slug, data) in enumerate(THEMES.items(), start=1):
            tematica, _ = Tematica.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data.get("title", ""),
                    "hero": data.get("hero", ""),
                    "chips": data.get("chips", []),
                    "accent": data.get("accent", "#3b82f6"),
                    "image": data.get("image", ""),
                    "activa": True,
                    "orden": orden_tema,
                }
            )

            for orden_desafio, desafio_data in enumerate(data.get("challenges", []), start=1):
                Desafio.objects.update_or_create(
                    tematica=tematica,
                    nombredesafio=desafio_data.get("name", ""),
                    defaults={
                        "summary": desafio_data.get("summary", ""),
                        "descripciondesafio": desafio_data.get("desc", ""),
                        "tokensdesafio": 0,
                        "activo": True,
                        "orden": orden_desafio,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Temáticas y desafíos cargados correctamente."))