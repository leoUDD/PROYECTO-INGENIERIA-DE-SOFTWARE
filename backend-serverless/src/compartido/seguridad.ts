import { createHmac, timingSafeEqual } from "node:crypto";
import type { APIGatewayProxyEventV2 } from "aws-lambda";
import { ErrorAplicacion } from "./respuestas.js";

export interface ContextoGrupo {
  sesionId: string;
  grupoId: string;
}

interface ContenidoToken extends ContextoGrupo {
  exp: number;
}

function claveToken(): string {
  const clave = process.env.CLAVE_TOKEN;

  if (!clave) {
    throw new Error("Falta la variable de entorno CLAVE_TOKEN");
  }

  return clave;
}

function firmar(texto: string): string {
  return createHmac("sha256", claveToken()).update(texto).digest("base64url");
}

export function crearToken(contexto: ContextoGrupo): string {
  const duracion = Number(process.env.DURACION_TOKEN_SEGUNDOS || 43200);
  const contenido: ContenidoToken = {
    ...contexto,
    exp: Math.floor(Date.now() / 1000) + duracion,
  };

  const cuerpo = Buffer.from(JSON.stringify(contenido)).toString("base64url");
  return `${cuerpo}.${firmar(cuerpo)}`;
}

export function validarToken(token: string): ContextoGrupo {
  const [cuerpo, firmaRecibida] = token.split(".");

  if (!cuerpo || !firmaRecibida) {
    throw new ErrorAplicacion("Token inválido", 401, "TOKEN_INVALIDO");
  }

  const firmaEsperada = firmar(cuerpo);
  const a = Buffer.from(firmaRecibida);
  const b = Buffer.from(firmaEsperada);

  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    throw new ErrorAplicacion("Token inválido", 401, "TOKEN_INVALIDO");
  }

  let contenido: ContenidoToken;

  try {
    contenido = JSON.parse(Buffer.from(cuerpo, "base64url").toString("utf8"));
  } catch {
    throw new ErrorAplicacion("Token inválido", 401, "TOKEN_INVALIDO");
  }

  if (contenido.exp < Math.floor(Date.now() / 1000)) {
    throw new ErrorAplicacion("La sesión expiró", 401, "TOKEN_EXPIRADO");
  }

  return {
    sesionId: contenido.sesionId,
    grupoId: contenido.grupoId,
  };
}

export function contextoDesdeEvento(event: APIGatewayProxyEventV2): ContextoGrupo {
  const autorizacion = event.headers.authorization || event.headers.Authorization;

  if (!autorizacion?.startsWith("Bearer ")) {
    throw new ErrorAplicacion("Falta el token de acceso", 401, "SIN_TOKEN");
  }

  return validarToken(autorizacion.slice(7));
}
