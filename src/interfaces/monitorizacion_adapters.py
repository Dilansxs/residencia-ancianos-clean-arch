from datetime import datetime
from typing import List
from src.application.bc_monitorizacion import (
    IActuadorLocalPort,
    IPublicarTelemetriaPort,
    ISensorHardwarePort
)
from src.domain.bc_monitorizacion import LecturaBiometrica, LecturaCriticaDetectada


# «InfrastructureAdapter» MqttTelemetriaAdapter
class MqttTelemetriaAdapter(IPublicarTelemetriaPort):
    def __init__(self, brokerUrl: str, qosLevel: int = 1):
        self.brokerUrl = brokerUrl
        self.qosLevel = qosLevel
        self.eventos_publicados: List[LecturaCriticaDetectada] = []

    def publicarTelemetria(self, lectura: LecturaBiometrica) -> None:
        print(
            f"  [MQTT v5 TLS -> {self.brokerUrl} | QoS {self.qosLevel}] "
            f"Telemetría: {lectura.pulsacionesBPM} BPM | {lectura.temperaturaCelsius}°C"
        )

    def publicarEventoCritico(self, evento: LecturaCriticaDetectada) -> None:
        self.eventos_publicados.append(evento)
        print(
            f"  [MQTT v5 TLS ALERTA CRÍTICA -> {self.brokerUrl} | QoS 2] "
            f"Evento #{evento.eventoId}: {evento.tipoAnomalia.value} "
            f"(Valor: {evento.valorObservado})"
        )


# Adaptador de Entrada de Sensores Simulados (I2C/SPI)
class SensorBiometricoSimuladoAdapter(ISensorHardwarePort):
    def __init__(self, lecturas_simuladas: List[tuple]):
        self.lecturas = lecturas_simuladas
        self.indice = 0

    def leerSensorBiometrico(self) -> LecturaBiometrica:
        bpm, temp = self.lecturas[self.indice % len(self.lecturas)]
        self.indice += 1
        return LecturaBiometrica(
            pulsacionesBPM=bpm,
            temperaturaCelsius=temp,
            timestamp=datetime.now()
        )


# Adaptador de Salida de Actuador Local (Relé)
class ActuadorLocalReleAdapter(IActuadorLocalPort):
    def activarReleAlarma(self, motivo: str) -> None:
        print(f"  [GPIO/Relé Actuador Local] ¡ALARMA SONORA/LED ACTIVADA EN HABITACIÓN! Motivo: {motivo}")