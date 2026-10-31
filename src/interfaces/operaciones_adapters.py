from typing import List, Optional
from src.application.bc_operaciones import (
    IPublicarEventosIntegracionPort,
    IResidenteRepository
)
from src.domain.bc_operaciones import Residente
from src.infrastructure.drivers import DatabaseClient


# «InfrastructureAdapter» ResidenteRepositoryAdapter
class ResidenteRepositoryAdapter(IResidenteRepository):
    def __init__(self, databaseClient: DatabaseClient):
        self.databaseClient = databaseClient

    def guardar(self, residente: Residente) -> None:
        self.databaseClient.tabla_residentes[residente.residenteId] = residente
        print(f"  [Almacén Local DB] Residente guardado: {residente.nombre} (Hab: {residente.ubicacion.codigoHabitacion})")

    def obtenerPorId(self, id: int) -> Optional[Residente]:
        return self.databaseClient.tabla_residentes.get(id)

    def existePorCodigo(self, codigo: str) -> bool:
        return any(r.codigo == codigo for r in self.databaseClient.tabla_residentes.values())

    def listar(self) -> List[Residente]:
        return list(self.databaseClient.tabla_residentes.values())


# Adaptador de Salida de Red (gRPC + RabbitMQ hacia Centro de Control)
class RabbitMQIntegracionAdapter(IPublicarEventosIntegracionPort):
    def publicarEventoIntegracion(self, topico: str, payload: dict) -> None:
        print(f"  [gRPC + RabbitMQ -> Centro Control] Tópico '{topico}' | Payload: {payload}")