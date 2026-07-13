import { TransactionCanceledException } from "@aws-sdk/client-dynamodb";
import {
  GetCommand,
  QueryCommand,
  TransactWriteCommand,
} from "@aws-sdk/lib-dynamodb";
import { baseDatos, nombreTabla } from "../compartido/baseDatos.js";

export interface SesionFase1 {
  sesionId: string;
  fase: string;
  totalGrupos: number;
  gruposSopaCompletada: number;
  primerGrupoSopaId?: string;
  timerInicio?: string;
}

export interface GrupoFase1 {
  grupoId: string;
  nombreGrupo: string;
  tokens: number;
  sopaCompletada: boolean;
  sopaTiempoSegundos?: number;
}

export interface DatosCompletarSopa {
  sesionId: string;
  grupoId: string;
  cantidadEsperada: number;
  nuevaCantidad: number;
  esPrimerGrupo: boolean;
  todosCompletaron: boolean;
  bonificacion: number;
  segundosTranscurridos?: number;
}

export interface RepositorioFase1 {
  buscarSesion(sesionId: string): Promise<SesionFase1 | null>;
  buscarGrupo(sesionId: string, grupoId: string): Promise<GrupoFase1 | null>;
  listarPalabras(sesionId: string, grupoId: string): Promise<string[]>;
  palabraExiste(sesionId: string, grupoId: string, palabra: string): Promise<boolean>;
  registrarPalabraAtomica(
    sesionId: string,
    grupoId: string,
    palabra: string,
    recompensa: number,
  ): Promise<boolean>;
  completarSopaAtomica(datos: DatosCompletarSopa): Promise<boolean>;
}

const claveSesion = (sesionId: string) => ({
  PK: `SESION#${sesionId}`,
  SK: "METADATOS",
});

const claveGrupo = (sesionId: string, grupoId: string) => ({
  PK: `SESION#${sesionId}`,
  SK: `GRUPO#${grupoId}`,
});

const clavePalabra = (sesionId: string, grupoId: string, palabra: string) => ({
  PK: `GRUPO#${sesionId}#${grupoId}`,
  SK: `PALABRA#${palabra}`,
});

export const repositorioFase1: RepositorioFase1 = {
  async buscarSesion(sesionId: string): Promise<SesionFase1 | null> {
    const resultado = await baseDatos.send(
      new GetCommand({
        TableName: nombreTabla(),
        Key: claveSesion(sesionId),
        ConsistentRead: true,
      }),
    );

    const item = resultado.Item;
    if (!item) return null;

    return {
      sesionId,
      fase: String(item.fase || "f1_sopa"),
      totalGrupos: Number(item.totalGrupos || 0),
      gruposSopaCompletada: Number(item.gruposSopaCompletada || 0),
      ...(item.primerGrupoSopaId
        ? { primerGrupoSopaId: String(item.primerGrupoSopaId) }
        : {}),
      ...(item.timerInicio ? { timerInicio: String(item.timerInicio) } : {}),
    };
  },

  async buscarGrupo(sesionId: string, grupoId: string): Promise<GrupoFase1 | null> {
    const resultado = await baseDatos.send(
      new GetCommand({
        TableName: nombreTabla(),
        Key: claveGrupo(sesionId, grupoId),
        ConsistentRead: true,
      }),
    );

    const item = resultado.Item;
    if (!item) return null;

    return {
      grupoId,
      nombreGrupo: String(item.nombreGrupo || "Grupo"),
      tokens: Number(item.tokens || 0),
      sopaCompletada: Boolean(item.sopaCompletada),
      ...(item.sopaTiempoSegundos !== undefined
        ? { sopaTiempoSegundos: Number(item.sopaTiempoSegundos) }
        : {}),
    };
  },

  async listarPalabras(sesionId: string, grupoId: string): Promise<string[]> {
    const resultado = await baseDatos.send(
      new QueryCommand({
        TableName: nombreTabla(),
        KeyConditionExpression: "PK = :pk AND begins_with(SK, :prefijo)",
        ExpressionAttributeValues: {
          ":pk": `GRUPO#${sesionId}#${grupoId}`,
          ":prefijo": "PALABRA#",
        },
        ConsistentRead: true,
      }),
    );

    return (resultado.Items ?? [])
      .map(
        (item: Record<string, unknown>) =>
          String(item.palabra ?? ""),
      )
      .filter((palabra) => palabra !== "");
  },

  async palabraExiste(sesionId: string, grupoId: string, palabra: string): Promise<boolean> {
    const resultado = await baseDatos.send(
      new GetCommand({
        TableName: nombreTabla(),
        Key: clavePalabra(sesionId, grupoId, palabra),
        ConsistentRead: true,
      }),
    );

    return Boolean(resultado.Item);
  },

  async registrarPalabraAtomica(
    sesionId: string,
    grupoId: string,
    palabra: string,
    recompensa: number,
  ): Promise<boolean> {
    const ahora = new Date().toISOString();

    try {
      await baseDatos.send(
        new TransactWriteCommand({
          TransactItems: [
            {
              Put: {
                TableName: nombreTabla(),
                Item: {
                  ...clavePalabra(sesionId, grupoId, palabra),
                  tipo: "PALABRA_FASE1",
                  sesionId,
                  grupoId,
                  palabra,
                  fechaCreacion: ahora,
                },
                ConditionExpression: "attribute_not_exists(PK)",
              },
            },
            {
              Update: {
                TableName: nombreTabla(),
                Key: claveGrupo(sesionId, grupoId),
                UpdateExpression:
                  "SET tokens = if_not_exists(tokens, :cero) + :recompensa, fechaActualizacion = :ahora",
                ConditionExpression: "attribute_exists(PK)",
                ExpressionAttributeValues: {
                  ":cero": 0,
                  ":recompensa": recompensa,
                  ":ahora": ahora,
                },
              },
            },
          ],
        }),
      );

      return true;
    } catch (error) {
      if (error instanceof TransactionCanceledException) {
        return false;
      }
      throw error;
    }
  },

  async completarSopaAtomica(datos: DatosCompletarSopa): Promise<boolean> {
    const ahora = new Date().toISOString();

    const valoresSesion: Record<string, unknown> = {
      ":esperada": datos.cantidadEsperada,
      ":nueva": datos.nuevaCantidad,
      ":ahora": ahora,
    };

    const cambiosSesion = [
      "gruposSopaCompletada = :nueva",
      "fechaActualizacion = :ahora",
    ];

    let condicionSesion =
      "attribute_exists(PK) AND (attribute_not_exists(gruposSopaCompletada) OR gruposSopaCompletada = :esperada)";

    if (datos.esPrimerGrupo) {
      cambiosSesion.push("primerGrupoSopaId = :grupoId");
      valoresSesion[":grupoId"] = datos.grupoId;
      condicionSesion += " AND attribute_not_exists(primerGrupoSopaId)";
    } else {
      condicionSesion += " AND attribute_exists(primerGrupoSopaId)";
    }

    if (datos.todosCompletaron) {
      cambiosSesion.push(
        "#fase = :ranking",
        "timerCorriendo = :falso",
        "segundosRestantes = :cero",
      );
      valoresSesion[":ranking"] = "f1_ranking";
      valoresSesion[":falso"] = false;
      valoresSesion[":cero"] = 0;
    }

    const valoresGrupo: Record<string, unknown> = {
      ":falso": false,
      ":verdadero": true,
      ":cero": 0,
      ":bonificacion": datos.bonificacion,
      ":ahora": ahora,
    };

    const cambiosGrupo = [
      "tokens = if_not_exists(tokens, :cero) + :bonificacion",
      "sopaCompletada = :verdadero",
      "fechaSopaCompletada = :ahora",
      "fechaActualizacion = :ahora",
    ];

    if (datos.segundosTranscurridos !== undefined) {
      cambiosGrupo.push("sopaTiempoSegundos = :segundos");
      valoresGrupo[":segundos"] = datos.segundosTranscurridos;
    }

    try {
      await baseDatos.send(
        new TransactWriteCommand({
          TransactItems: [
            {
              Update: {
                TableName: nombreTabla(),
                Key: claveSesion(datos.sesionId),
                UpdateExpression: `SET ${cambiosSesion.join(", ")}`,
                ConditionExpression: condicionSesion,
                ...(datos.todosCompletaron
                  ? { ExpressionAttributeNames: { "#fase": "fase" } }
                  : {}),
                ExpressionAttributeValues: valoresSesion,
              },
            },
            {
              Update: {
                TableName: nombreTabla(),
                Key: claveGrupo(datos.sesionId, datos.grupoId),
                UpdateExpression: `SET ${cambiosGrupo.join(", ")}`,
                ConditionExpression:
                  "attribute_exists(PK) AND (attribute_not_exists(sopaCompletada) OR sopaCompletada = :falso)",
                ExpressionAttributeValues: valoresGrupo,
              },
            },
          ],
        }),
      );

      return true;
    } catch (error) {
      if (error instanceof TransactionCanceledException) {
        return false;
      }
      throw error;
    }
  },
};
