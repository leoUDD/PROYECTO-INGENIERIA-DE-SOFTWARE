import { ErrorAplicacion } from "../compartido/respuestas.js";
import type { RepositorioFase1 } from "./repositorio.js";

export async function obtenerEstadoFase1(
  sesionId: string,
  grupoId: string,
  repositorio: RepositorioFase1,
) {
  const [sesion, grupo, palabras] = await Promise.all([
    repositorio.buscarSesion(sesionId),
    repositorio.buscarGrupo(sesionId, grupoId),
    repositorio.listarPalabras(sesionId, grupoId),
  ]);

  if (!sesion || !grupo) {
    throw new ErrorAplicacion("No se encontró la sesión o el grupo", 404, "CONTEXTO_NO_ENCONTRADO");
  }

  return {
    ok: true,
    fase: sesion.fase,
    grupo,
    palabras,
    progreso: {
      completados: sesion.gruposSopaCompletada,
      totalGrupos: sesion.totalGrupos,
    },
  };
}

export async function registrarPalabra(
  sesionId: string,
  grupoId: string,
  palabraRecibida: string,
  repositorio: RepositorioFase1,
) {
  const palabra = palabraRecibida.trim().toUpperCase();

  if (!palabra) {
    throw new ErrorAplicacion("Debes enviar una palabra", 400, "PALABRA_REQUERIDA");
  }

  const grupo = await repositorio.buscarGrupo(sesionId, grupoId);

  if (!grupo) {
    throw new ErrorAplicacion("Grupo no encontrado", 404, "GRUPO_NO_ENCONTRADO");
  }

  const creada = await repositorio.registrarPalabraAtomica(
    sesionId,
    grupoId,
    palabra,
    1,
  );

  if (!creada && !(await repositorio.palabraExiste(sesionId, grupoId, palabra))) {
    throw new ErrorAplicacion("No se pudo guardar la palabra", 409, "CONFLICTO_PALABRA");
  }

  const grupoActualizado = await repositorio.buscarGrupo(sesionId, grupoId);

  return {
    ok: true,
    palabra,
    nueva: creada,
    recompensa: creada ? 1 : 0,
    tokens: grupoActualizado?.tokens ?? grupo.tokens,
  };
}

export async function completarSopa(
  sesionId: string,
  grupoId: string,
  repositorio: RepositorioFase1,
) {
  for (let intento = 1; intento <= 5; intento += 1) {
    const [sesion, grupo] = await Promise.all([
      repositorio.buscarSesion(sesionId),
      repositorio.buscarGrupo(sesionId, grupoId),
    ]);

    if (!sesion || !grupo) {
      throw new ErrorAplicacion("No se encontró la sesión o el grupo", 404, "CONTEXTO_NO_ENCONTRADO");
    }

    if (grupo.sopaCompletada) {
      return {
        ok: true,
        yaCompletada: true,
        bonificacion: 0,
        tokens: grupo.tokens,
        fase: sesion.fase,
      };
    }

    if (sesion.totalGrupos <= 0) {
      throw new ErrorAplicacion("La sesión no tiene grupos configurados", 409, "SESION_SIN_GRUPOS");
    }

    const nuevaCantidad = sesion.gruposSopaCompletada + 1;
    const esPrimerGrupo = !sesion.primerGrupoSopaId;
    const todosCompletaron = nuevaCantidad >= sesion.totalGrupos;
    const bonificacion = esPrimerGrupo ? 5 : 3;

    const segundosTranscurridos = sesion.timerInicio
      ? Math.max(0, Math.floor((Date.now() - Date.parse(sesion.timerInicio)) / 1000))
      : undefined;

    const completada = await repositorio.completarSopaAtomica({
      sesionId,
      grupoId,
      cantidadEsperada: sesion.gruposSopaCompletada,
      nuevaCantidad,
      esPrimerGrupo,
      todosCompletaron,
      bonificacion,
      ...(segundosTranscurridos === undefined ? {} : { segundosTranscurridos }),
    });

    if (!completada) {
      continue;
    }

    const [sesionActualizada, grupoActualizado] = await Promise.all([
      repositorio.buscarSesion(sesionId),
      repositorio.buscarGrupo(sesionId, grupoId),
    ]);

    return {
      ok: true,
      yaCompletada: false,
      esPrimerGrupo,
      todosCompletaron,
      bonificacion,
      tokens: grupoActualizado?.tokens ?? grupo.tokens + bonificacion,
      fase: sesionActualizada?.fase ?? (todosCompletaron ? "f1_ranking" : sesion.fase),
    };
  }

  throw new ErrorAplicacion(
    "Otro grupo actualizó la sesión al mismo tiempo. Intenta nuevamente.",
    409,
    "CONFLICTO_CONCURRENCIA",
  );
}
