from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class EstadoIncidente(Enum):
    ABIERTO = "ABIERTO"
    CONFIRMADO = "CONFIRMADO"
    ESCALADO = "ESCALADO"
    CERRADO = "CERRADO"


# «ValueObject» NivelSeveridad
@dataclass(frozen=True)
class NivelSeveridad:
    nivel: str
    segundosMaximos: int

    def requiereAmbulanciaInmediata(self) -> bool:
        # Si es CRITICA o el SLA es menor o igual a 30 segundos, requiere ambulancia
        return self.nivel.upper() == "CRITICA" or self.segundosMaximos <= 30


# «Entity» NotificacionDespachada
@dataclass
class NotificacionDespachada:
    notificacionId: int
    canalDestino: str
    referenciaProveedor: str
    fechaEnvio: datetime = field(default_factory=datetime.now)
    estadoEntrega: bool = False

    def marcarComoEntregada(self) -> None:
        self.estadoEntrega = True

    def registrarFallo(self) -> None:
        self.estadoEntrega = False


# «DomainEvent» AlertaEscaladaAEmergencias
@dataclass(frozen=True)
class AlertaEscaladaAEmergencias:
    eventoId: int
    incidenteId: int
    residenciaId: int
    coordenadas: str
    motivoClinico: str
    fecha: datetime = field(default_factory=datetime.now)


# «AggregateRoot» IncidenteAlerta
@dataclass
class IncidenteAlerta:
    incidenteId: int
    residenciaId: int
    residenteId: int
    sesionId: int
    severidad: NivelSeveridad
    estado: EstadoIncidente = EstadoIncidente.ABIERTO
    fechaDeteccion: datetime = field(default_factory=datetime.now)
    notificaciones: List[NotificacionDespachada] = field(default_factory=list)
    operadorConfirmacionId: int = 0
    resolucion: str = ""

    def confirmarRecepcion(self, operadorId: int) -> None:
        self.operadorConfirmacionId = operadorId
        self.estado = EstadoIncidente.CONFIRMADO

    def escalarIncidente(self, coordenadas: str = "-1.4836, -78.0025", motivo: str = "Anomalía biométrica crítica") -> AlertaEscaladaAEmergencias:
        self.estado = EstadoIncidente.ESCALADO
        return AlertaEscaladaAEmergencias(
            eventoId=int(datetime.now().timestamp() * 1000),
            incidenteId=self.incidenteId,
            residenciaId=self.residenciaId,
            coordenadas=coordenadas,
            motivoClinico=motivo
        )

    def cerrarIncidente(self, res: str) -> None:
        self.resolucion = res
        self.estado = EstadoIncidente.CERRADO