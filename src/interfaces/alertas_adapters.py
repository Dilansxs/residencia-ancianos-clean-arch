from typing import List
from src.application.bc_alertas import (
    IIncidenteRepositoryPort,
    INotificacionExternaPort
)
from src.domain.bc_alertas import IncidenteAlerta, EstadoIncidente
from src.infrastructure.drivers import HttpClient, DatabaseClient


#Adaptador de notificacion externa para Emergencias y SMS
class RestEmergenciasAdapter(INotificacionExternaPort):
    def __init__(self, httpClient: HttpClient):
        self.httpClient = httpClient

    def notificarEmergencias(self, incidencia: IncidenteAlerta) -> bool:
        payload = {
            "incidenteId": incidencia.incidenteId,
            "residenciaId": incidencia.residenciaId,
            "residenteId": incidencia.residenteId,
            "severidad": incidencia.severidad.nivel
        }
        status = self.httpClient.post("https://api.emergencias911.gob/despacho", payload)
        return status == 200

    def notificarFamiliarSMS(self, residenteId: int, mensaje: str) -> None:
        self.httpClient.post(
            "https://gateway.sms-familiares.com/send",
            {"residenteId": residenteId, "sms": mensaje}
        )

    def enviarInformeSalud(self, incidencia: IncidenteAlerta) -> None:
        self.httpClient.post(
            "https://api.centrosalud.org/informes-clinicos",
            {"incidenteId": incidencia.incidenteId, "estado": incidencia.estado.value}
        )


# Adaptador de Persistencia
class IncidenteRepositoryAdapter(IIncidenteRepositoryPort):
    def __init__(self, databaseClient: DatabaseClient):
        self.databaseClient = databaseClient

    def guardar(self, incidente: IncidenteAlerta) -> None:
        self.databaseClient.tabla_incidentes[incidente.incidenteId] = incidente
        print(f"  [BD Central] Incidente #{incidente.incidenteId} registrado con estado: {incidente.estado.value}")

    def listarAbiertos(self) -> List[IncidenteAlerta]:
        return [
            inc for inc in self.databaseClient.tabla_incidentes.values()
            if inc.estado == EstadoIncidente.ABIERTO
        ]