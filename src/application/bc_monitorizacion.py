from abc import ABC, abstractmethod
from typing import List
from src.domain.bc_monitorizacion import (
    LecturaBiometrica,
    LecturaCriticaDetectada,
    SesionMonitorizacion
)


# Interfaz de telemetria
class IPublicarTelemetriaPort(ABC):
    @abstractmethod
    def publicarTelemetria(self, lectura: LecturaBiometrica) -> None:
        pass

    @abstractmethod
    def publicarEventoCritico(self, evento: LecturaCriticaDetectada) -> None:
        pass


# Interfaz de sensor hardware
class ISensorHardwarePort(ABC):
    @abstractmethod
    def leerSensorBiometrico(self) -> LecturaBiometrica:
        pass


# Interfaz de actuador local
class IActuadorLocalPort(ABC):
    @abstractmethod
    def activarReleAlarma(self, motivo: str) -> None:
        pass


# Caso de uso
class RegistrarLecturaUseCase:
    def __init__(
        self,
        sensorPort: ISensorHardwarePort,
        pasarelaPort: IPublicarTelemetriaPort,
        actuadorPort: IActuadorLocalPort,
        sesion: SesionMonitorizacion
    ):
        self.sensorPort = sensorPort
        self.pasarelaPort = pasarelaPort
        self.actuadorPort = actuadorPort
        self.sesion = sesion

    def ejecutarCicloMuestreo(self) -> List[LecturaCriticaDetectada]:
        # 1. Leer datos del sensor embebido (I2C/SPI simulado)
        lectura = self.sensorPort.leerSensorBiometrico()

        # 2. Registrar en el Aggregate Root y evaluar reglas de dominio
        eventos_criticos = self.sesion.registrarLectura(lectura)

        # 3. Publicar telemetría normal hacia la pasarela local
        self.pasarelaPort.publicarTelemetria(lectura)

        # 4. Si hay eventos de dominio críticos, activar actuador local y publicar alerta
        for evento in eventos_criticos:
            self.actuadorPort.activarReleAlarma(
                f"{evento.tipoAnomalia.value}: {evento.valorObservado}"
            )
            self.pasarelaPort.publicarEventoCritico(evento)

        return eventos_criticos