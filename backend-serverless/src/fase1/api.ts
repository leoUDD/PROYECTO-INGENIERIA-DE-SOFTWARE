import type {
  APIGatewayProxyEventV2,
  APIGatewayProxyResultV2,
} from "aws-lambda";
import { contextoDesdeEvento } from "../compartido/seguridad.js";
import {
  leerJson,
  responderError,
  respuestaJson,
} from "../compartido/respuestas.js";
import { repositorioFase1 } from "./repositorio.js";
import {
  completarSopa,
  obtenerEstadoFase1,
  registrarPalabra,
} from "./servicio.js";

interface CuerpoPalabra {
  palabra?: string;
}

export async function manejador(
  event: APIGatewayProxyEventV2,
): Promise<APIGatewayProxyResultV2> {
  try {
    const ruta = event.requestContext.http.path;
    const metodo = event.requestContext.http.method;
    const contexto = contextoDesdeEvento(event);

    if (ruta === "/api/fase1/estado" && metodo === "GET") {
      const resultado = await obtenerEstadoFase1(
        contexto.sesionId,
        contexto.grupoId,
        repositorioFase1,
      );
      return respuestaJson(200, resultado);
    }

    if (ruta === "/api/fase1/palabras" && metodo === "POST") {
      const cuerpo = leerJson<CuerpoPalabra>(event);
      const resultado = await registrarPalabra(
        contexto.sesionId,
        contexto.grupoId,
        cuerpo.palabra || "",
        repositorioFase1,
      );
      return respuestaJson(200, resultado);
    }

    if (ruta === "/api/fase1/completar" && metodo === "POST") {
      const resultado = await completarSopa(
        contexto.sesionId,
        contexto.grupoId,
        repositorioFase1,
      );
      return respuestaJson(200, resultado);
    }

    return respuestaJson(404, {
      ok: false,
      error: "Ruta no encontrada",
    });
  } catch (error) {
    return responderError(error);
  }
}
