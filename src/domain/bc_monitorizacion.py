from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class EstadoSesion(Enum):
    INICIADA = "INICIADA"
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"


class EstadoDispositivo(Enum):
    OPERATIVO = "OPERATIVO"
    BATERIA_BAJA = "BATERIA_BAJA"
    FALLO = "FALLO"


class TipoAnomalia(Enum):
    TAQUICARDIA = "TAQUICARDIA"
    BRADICARDIA = "BRADICARDIA"
    FIEBRE_ALTA = "FIEBRE_ALTA"


# «ValueObject» LecturaBiometrica
@dataclass(frozen=True)
class LecturaBiometrica:
    pulsacionesBPM: int
    temperaturaCelsius: float
    timestamp: datetime = field(default_factory=datetime.now)

    def esValida(self) -> bool:
        # Verifica rangos fisiológicos físicamente posibles
        return 20 <= self.pulsacionesBPM <= 250 and 30.0 <= self.temperaturaCelsius <= 45.0


# «ValueObject» ConfiguracionMonitorizacionLocal
@dataclass(frozen=True)
class ConfiguracionMonitorizacionLocal:
    residenteId: int
    bpmMinimo: int
    bpmMaximo: int
    temperaturaMaxima: float
    fechaActualizacion: datetime = field(default_factory=datetime.now)

    def esValida(self) -> bool:
        # Verifica coherencia de los umbrales configurados
        return 0 < self.bpmMinimo < self.bpmMaximo and 35.0 <= self.temperaturaMaxima <= 42.0


# «Entity» DispositivoEmbebido
@dataclass
class DispositivoEmbebido:
    macAddress: str
    porcentajeBateria: int
    estado: EstadoDispositivo = EstadoDispositivo.OPERATIVO

    def verificarBateriaBaja(self) -> bool:
        # Alerta si la batería baja del 15%
        if self.porcentajeBateria < 15:
            self.estado = EstadoDispositivo.BATERIA_BAJA
            return True
        return False


# «DomainEvent» LecturaCriticaDetectada
@dataclass(frozen=True)
class LecturaCriticaDetectada:
    eventoId: int
    residenteId: int
    sesionId: int
    lecturaId: int
    tipoAnomalia: TipoAnomalia
    valorObservado: float
    fechaDeteccion: datetime = field(default_factory=datetime.now)


# «AggregateRoot» SesionMonitorizacion
@dataclass
class SesionMonitorizacion:
    sesionId: int
    residenteId: int
    dispositivoId: int
    dispositivo: DispositivoEmbebido
    configuracion: ConfiguracionMonitorizacionLocal
    fechaInicio: int = 0
    fechaFin: int = 0
    estado: EstadoSesion = EstadoSesion.INICIADA
    lecturas: List[LecturaBiometrica] = field(default_factory=list)

    def iniciarSesion(self) -> None:
        if not self.configuracion.esValida():
            raise ValueError("Configuración de monitorización inválida.")
        self.fechaInicio = int(datetime.now().timestamp())
        self.estado = EstadoSesion.ACTIVA

    def registrarLectura(self, lectura: LecturaBiometrica) -> List[LecturaCriticaDetectada]:
        if self.estado != EstadoSesion.ACTIVA:
            raise RuntimeError("No se pueden registrar lecturas en una sesión inactiva.")
        if not lectura.esValida():
            raise ValueError("Lectura biométrica descartada por ruido de sensor.")

        self.lecturas.append(lectura)
        lectura_id = len(self.lecturas)
        eventos: List[LecturaCriticaDetectada] = []

        # Evaluación de reglas de dominio frente al umbral local
        if lectura.pulsacionesBPM > self.configuracion.bpmMaximo:
            eventos.append(LecturaCriticaDetectada(
                eventoId= int(datetime.now().timestamp() * 1000) + 1,
                residenteId=self.residenteId,
                sesionId=self.sesionId,
                lecturaId=lectura_id,
                tipoAnomalia=TipoAnomalia.TAQUICARDIA,
                valorObservado=float(lectura.pulsacionesBPM)
            ))
        elif lectura.pulsacionesBPM < self.configuracion.bpmMinimo:
            eventos.append(LecturaCriticaDetectada(
                eventoId=int(datetime.now().timestamp() * 1000) + 2,
                residenteId=self.residenteId,
                sesionId=self.sesionId,
                lecturaId=lectura_id,
                tipoAnomalia=TipoAnomalia.BRADICARDIA,
                valorObservado=float(lectura.pulsacionesBPM)
            ))

        if lectura.temperaturaCelsius > self.configuracion.temperaturaMaxima:
            eventos.append(LecturaCriticaDetectada(
                eventoId=int(datetime.now().timestamp() * 1000) + 3,
                residenteId=self.residenteId,
                sesionId=self.sesionId,
                lecturaId=lectura_id,
                tipoAnomalia=TipoAnomalia.FIEBRE_ALTA,
                valorObservado=lectura.temperaturaCelsius
            ))

        return eventos

    def finalizarSesion(self) -> None:
        self.fechaFin = int(datetime.now().timestamp())
        self.estado = EstadoSesion.FINALIZADA

    def verificarEstado(self) -> EstadoSesion:
        self.dispositivo.verificarBateriaBaja()
        return self.estado