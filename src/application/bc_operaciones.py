from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from src.domain.bc_operaciones import (
    EstadoResidente,
    PerfilMonitorizacion,
    Residente,
    UbicacionResidencia
)


# DTO Command para registro
@dataclass
class RegistrarResidenciaCommand:
    residenteId: int
    codigo: str
    nombre: str
    ubicacion: UbicacionResidencia
    perfil: PerfilMonitorizacion


# «Interface» IResidenteRepository
class IResidenteRepository(ABC):
    @abstractmethod
    def guardar(self, residente: Residente) -> None:
        pass

    @abstractmethod
    def obtenerPorId(self, id: int) -> Optional[Residente]:
        pass

    @abstractmethod
    def existePorCodigo(self, codigo: str) -> bool:
        pass

    @abstractmethod
    def listar(self) -> List[Residente]:
        pass


# «Interface» IPublicarEventosIntegracionPort
class IPublicarEventosIntegracionPort(ABC):
    @abstractmethod
    def publicarEventoIntegracion(self, topico: str, payload: dict) -> None:
        pass


# «UseCase» RegistrarResidenteUseCase
class RegistrarResidenteUseCase:
    def __init__(self, residenteRepository: IResidenteRepository):
        self.residenteRepository = residenteRepository

    def ejecutar(self, datos: RegistrarResidenciaCommand) -> int:
        if self.residenteRepository.existePorCodigo(datos.codigo):
            raise ValueError(f"Ya existe un residente con el código {datos.codigo}")

        nuevo_residente = Residente(
            residenteId=datos.residenteId,
            codigo=datos.codigo,
            nombre=datos.nombre,
            estado=EstadoResidente.ACTIVO,
            ubicacion=datos.ubicacion,
            perfil=datos.perfil
        )
        nuevo_residente.registrarResidente()
        self.residenteRepository.guardar(nuevo_residente)
        return nuevo_residente.residenteId


# «UseCase» ActualizarPerfilMonitorizacionUseCase
class ActualizarPerfilMonitorizacionUseCase:
    def __init__(
        self,
        residenteRepository: IResidenteRepository,
        eventoPort: IPublicarEventosIntegracionPort
    ):
        self.residenteRepository = residenteRepository
        self.eventoPort = eventoPort

    def ejecutar(self, residenteId: int, nuevoPerfil: PerfilMonitorizacion) -> None:
        residente = self.residenteRepository.obtenerPorId(residenteId)
        if not residente:
            raise ValueError(f"Residente {residenteId} no encontrado.")

        residente.actualizarPerfil(nuevoPerfil)
        self.residenteRepository.guardar(residente)
        self.eventoPort.publicarEventoIntegracion(
            "operaciones.perfil.actualizado",
            {"residenteId": residenteId, "bpmMax": nuevoPerfil.umbralClinico.bpmMaximo}
        )


# «UseCase» ActualizarUbicacionResidenteUseCase
class ActualizarUbicacionResidenteUseCase:
    def __init__(
        self,
        residenteRepository: IResidenteRepository,
        eventoPort: IPublicarEventosIntegracionPort
    ):
        self.residenteRepository = residenteRepository
        self.eventoPort = eventoPort

    def procesarEvento(self, residenteId: int, ubicacion: UbicacionResidencia) -> None:
        residente = self.residenteRepository.obtenerPorId(residenteId)
        if not residente:
            raise ValueError(f"Residente {residenteId} no encontrado.")

        residente.actualizarUbicacion(ubicacion)
        self.residenteRepository.guardar(residente)
        self.eventoPort.publicarEventoIntegracion(
            "operaciones.ubicacion.actualizada",
            {"residenteId": residenteId, "habitacion": ubicacion.codigoHabitacion}
        )