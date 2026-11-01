from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List
from src.domain.bc_alertas import (
    AlertaEscaladaAEmergencias,
    EstadoIncidente,
    IncidenteAlerta,
    NivelSeveridad,
    NotificacionDespachada
)


#Clase de DTO
@dataclass
class EventoAlertaRecibida:
    incidenteId: int
    residenciaId: int
    residenteId: int
    sesionId: int
    nivelSeveridad: str
    segundosMaximosSLA: int
    motivoClinico: str


#Intefaz de notificacion externa
class INotificacionExternaPort(ABC):
    @abstractmethod
    def notificarEmergencias(self, incidencia: IncidenteAlerta) -> bool:
        pass

    @abstractmethod
    def notificarFamiliarSMS(self, residenteId: int, mensaje: str) -> None:
        pass

    @abstractmethod
    def enviarInformeSalud(self, incidencia: IncidenteAlerta) -> None:
        pass


#Repositorio de incidentes
class IIncidenteRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, incidente: IncidenteAlerta) -> None:
        pass

    @abstractmethod
    def listarAbiertos(self) -> List[IncidenteAlerta]:
        pass


#Caso de Uso
class GestionarYNotificarAlertaUseCase:
    def __init__(
        self,
        incidenteRepo: IIncidenteRepositoryPort,
        notificacionPort: INotificacionExternaPort
    ):
        self.incidenteRepo = incidenteRepo
        self.notificacionPort = notificacionPort

    def recibirYDespacharAlerta(self, dto: EventoAlertaRecibida) -> IncidenteAlerta:
        severidad = NivelSeveridad(
            nivel=dto.nivelSeveridad,
            segundosMaximos=dto.segundosMaximosSLA
        )
        incidente = IncidenteAlerta(
            incidenteId=dto.incidenteId,
            residenciaId=dto.residenciaId,
            residenteId=dto.residenteId,
            sesionId=dto.sesionId,
            severidad=severidad
        )

        # Si requiere ambulancia inmediata, escalar y avisar a emergencias
        if severidad.requiereAmbulanciaInmediata():
            incidente.escalarIncidente(motivo=dto.motivoClinico)
            exito_emergencia = self.notificacionPort.notificarEmergencias(incidente)
            notif = NotificacionDespachada(
                notificacionId=1,
                canalDestino="SERVICIO_EMERGENCIAS_911",
                referenciaProveedor="HTTPS_REST_911"
            )
            if exito_emergencia:
                notif.marcarComoEntregada()
            else:
                notif.registrarFallo()
            incidente.notificaciones.append(notif)

        # Notificar a familiares por SMS/WebPush y al Centro de Salud
        self.notificacionPort.notificarFamiliarSMS(
            dto.residenteId,
            f"Alerta {dto.nivelSeveridad}: {dto.motivoClinico}"
        )
        self.notificacionPort.enviarInformeSalud(incidente)

        self.incidenteRepo.guardar(incidente)
        return incidente

    def verificarVencimientoSLA(self) -> List[AlertaEscaladaAEmergencias]:
        eventos_escalados: List[AlertaEscaladaAEmergencias] = []
        ahora = datetime.now()

        for incidente in self.incidenteRepo.listarAbiertos():
            segundos_transcurridos = (ahora - incidente.fechaDeteccion).total_seconds()
            if (
                incidente.estado == EstadoIncidente.ABIERTO
                and segundos_transcurridos > incidente.severidad.segundosMaximos
            ):
                evento = incidente.escalarIncidente(motivo="Vencimiento de SLA sin confirmación")
                self.notificacionPort.notificarEmergencias(incidente)
                eventos_escalados.append(evento)

        return eventos_escalados