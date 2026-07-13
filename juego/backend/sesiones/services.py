import csv
import io

import openpyxl

def leer_filas_archivo(archivo):
    """Lee un .xlsx (openpyxl) o .csv (csv nativo) y devuelve una lista de
    diccionarios {encabezado: valor}, usando '' para celdas vacias.
    Reemplaza a pandas para no depender de pandas/numpy en produccion."""
    nombre = archivo.name.lower()

    if nombre.endswith(".xlsx"):
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        ws = wb.active
        iterador = ws.iter_rows(values_only=True)
        try:
            encabezados = [
                str(c).strip() if c is not None else "" for c in next(iterador)
            ]
        except StopIteration:
            return []
        filas = []
        for fila in iterador:
            if fila is None or all(v is None for v in fila):
                continue
            filas.append(
                {
                    clave: ("" if valor is None else valor)
                    for clave, valor in zip(encabezados, fila)
                }
            )
        return filas

    if nombre.endswith(".csv"):
        archivo.seek(0)
        texto = io.TextIOWrapper(archivo, encoding="utf-8-sig", newline="")
        return [
            {clave: (valor if valor is not None else "") for clave, valor in fila.items()}
            for fila in csv.DictReader(texto)
        ]

    raise ValueError("Formato no soportado. Usa .xlsx o .csv.")





def crear_alumnos_en_sesion(df, profesor, sesion):
    alumnos_creados = []

    for row in df:
        alumno = Alumno.objects.create(
            profesor_idprofesor=profesor,
            sesion=sesion,
            emailalumno=row.get("Correo", ""),
            rutalumno=row.get("RUT", ""),
            nombrealumno=row.get("Nombre", ""),
            apellidopaternoalumno=row.get("Apellido Paterno", ""),
            apellidomaternoalumno=row.get("Apellido Materno", ""),
            carreraalumno=row.get("Carrera", ""),
        )
        alumnos_creados.append(alumno)

    return alumnos_creados

def generar_codigo_grupo_profesor():
    while True:
        codigo = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Grupo.objects.filter(codigoacceso=codigo).exists():
            return codigo

def crear_grupos_para_alumnos(sesion, alumnos, max_por_grupo=8, cantidad_grupos_manual=None):
    if not alumnos:
        return 0

    if cantidad_grupos_manual:
        cantidad_grupos = max(1, int(cantidad_grupos_manual))
    else:
        cantidad_grupos = ceil(len(alumnos) / max_por_grupo)

    grupos = []

    for i in range(cantidad_grupos):
        grupo = Grupo.objects.create(
            sesion=sesion,
            nombregrupo=f"Grupo {i + 1}",
            tokensgrupo=10,
            etapa=1,
            codigoacceso=generar_codigo_grupo_profesor(),
        )
        grupos.append(grupo)

    for index, alumno in enumerate(alumnos):
        grupo = grupos[index % len(grupos)]
        alumno.grupo = grupo
        alumno.save(update_fields=["grupo"])

    return len(grupos)