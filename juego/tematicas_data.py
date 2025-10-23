# app/themes_data.py

THEMES = {
    "salud": {
        "title": "Desafíos — Salud",
        "hero": "Mejora hábitos y bienestar en tu comunidad.",
        "chips": ["🫶 Empatía", "💪 Bienestar", "💡 Innovación"],
        "accent": "#22c55e",
        "image": "images/tema_salud.png",
        "challenges": [
            {
                "id": 1,
                "name": "Rutina Saludable",
                "desc": "El sedentarismo y la mala alimentación afectan a muchos jóvenes. "
                "Valentina, de 25 años, pasa largas horas frente al computador. Se siente cansada y busca incorporar hábitos simples y saludables para mejorar su bienestar físico y mental."
            },
            {
                "id": 2,
                "name": "Acceso Médico Rural",
                "desc": "El acceso a médica oportuna sigue siendo un problema en zonas rurales. "
                "José, un campesino de 62 años, debe viajar más de dos horas para una consulta médica y muchas veces no logra obtener hora con especialistas."
            },
            {
                "id": 3,
                "name": "Salud Mental Post Pandemia",
                "desc": "La salud mental se ha visto afectada tras la pandemia. "
                "Carolina, una profesora de 38 años, siente ansiedad constante por la sobrecarga laboral y la falta de apoyo emocional en su entorno."
            },
        ],
    },
    "sustentabilidad": {
        "title": "Desafíos — Sustentabilidad",
        "hero": "Crea impacto ambiental positivo y medible.",
        "chips": ["🌱 Ambiental", "♻️ Circular", "⚙️ Creativo"],
        "accent": "#16a34a",
        "image": "images/tema_sustentabilidad.png",
        "challenges": [
            {
                "id": 1,
                "name": "Reciclaje Universitario",
                "desc": "El manejo ineficiente de residuos contamina los barrios urbanos. "
                "Martín, un joven de 19 años, nota que en su universidad no existen puntos de reciclaje y la mayoría de los residuos terminan mezclados."
            },
            {
                "id": 2,
                "name": "Plásticos Marinos",
                "desc": "El uso excesivo de plásticos afecta los ecosistemas marinos. "
                "Fernanda, de 27 años, vive en una ciudad costera y ha visto cómo las playas están llenas de microplásticos que dañan la fauna local."
            },
            {
                "id": 3,
                "name": "Transporte Limpio",
                "desc": "La contaminación por transporte urbano ha aumentado en los últimos años. "
                "Andrés, de 35 años, usa su automóvil todos los días para ir al trabajo y le gustaría encontrar alternativas más limpias y económicas."
            },
        ],
    },
    "educacion": {
        "title": "Desafíos — Educación",
        "hero": "Mejora la experiencia de aprendizaje e inclusión.",
        "chips": ["🗣️ Comunicar", "🎓 Liderazgo", "💭 Ideas"],
        "accent": "#3b82f6",
        "image": "images/tema_educacion.png",
        "challenges": [
            {
                "id": 1,
                "name": "Conectividad Rural", 
                "desc": "La brecha digital en la educación rural limita el aprendizaje. "
                "Rosa, una estudiante de 13 años, vive en una zona sin buena conexión a internet y no puede acceder a clases en línea ni recursos educativos."
            },
            {
                "id": 2,
                "name": "Motivación Escolar",
                "desc": "La desmotivación estudiantil se ha incrementado tras la pandemia. "
                "Diego, de 17 años, siente que la escuela no le ofrece actividades prácticas o cercanas a sus intereses personales."
            },
            {
                "id": 3,
                "name": "Educación Emocional",
                "desc": "La falta de educación emocional afecta la convivencia escolar. "
                "María José, de 10 años, tiene dificultades para manejar sus emociones y no existen instancias en su colegio para aprender sobre empatía o autocontrol."
            },
        ],
    },
}

def get_theme(slug):
    return THEMES.get(slug.lower())
