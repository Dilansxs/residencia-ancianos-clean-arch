from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


class EstadoResidente(Enum):
    ACTIVO = "ACTIVO"
    EN_OBSERVACION = "EN_OBSERVACION"
    INACTIVO = "INACTIVO"


#Objeto de valor
@dataclass(frozen=True)
class UbicacionResidencia:
    numeroPlanta: int
    codigoHabitacion: str

    def validarUbicacion(self) -> bool:
        return self.numeroPlanta >= 0 and len(self.codigoHabitacion.strip()) > 0


#Objeto de valor
@dataclass(frozen=True)
class UmbralClinico:
    bpmMinimo: int
    bpmMaximo: int
    temperaturaMaxima: float
    tiempoMaximoInactividad: timedelta

    def validarRangos(self) -> bool:
        return (
            30 <= self.bpmMinimo < self.bpmMaximo <= 220
            and 36.0 <= self.temperaturaMaxima <= 42.0
            and self.tiempoMaximoInactividad.total_seconds() > 0
        )


#Objeto de valor
@dataclass(frozen=True)
class PerfilMonitorizacion:
    umbralClinico: UmbralClinico
    frecuenciaLectura: timedelta
    monitorizacionActiva: bool

    def validarConfiguracion(self) -> bool:
        return (
            self.umbralClinico.validarRangos()
            and self.frecuenciaLectura.total_seconds() >= 1
        )


#Agregado
@dataclass
class Residente:
    residenteId: int
    codigo: str
    nombre: str
    estado: EstadoResidente
    ubicacion: UbicacionResidencia
    perfil: PerfilMonitorizacion

    def registrarResidente(self) -> None:
        if not self.ubicacion.validarUbicacion():
            raise ValueError("Ubicación de residencia inválida.")
        if not self.perfil.validarConfiguracion():
            raise ValueError("Perfil de monitorización inválido.")
        self.estado = EstadoResidente.ACTIVO

    def actualizarUbicacion(self, nueva_ubicacion: UbicacionResidencia) -> None:
        if not nueva_ubicacion.validarUbicacion():
            raise ValueError("La nueva ubicación no es válida.")
        self.ubicacion = nueva_ubicacion

    def actualizarPerfil(self, nuevo_perfil: PerfilMonitorizacion) -> None:
        if not nuevo_perfil.validarConfiguracion():
            raise ValueError("El nuevo perfil de monitorización no es válido.")
        self.perfil = nuevo_perfil

    def desactivarResidente(self) -> None:
        self.estado = EstadoResidente.INACTIVO