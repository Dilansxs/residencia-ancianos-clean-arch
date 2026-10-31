from datetime import timedelta
from src.infrastructure.drivers import DatabaseClient, HttpClient
from src.domain.bc_operaciones import UbicacionResidencia, UmbralClinico, PerfilMonitorizacion
from src.application.bc_operaciones import (
    RegistrarResidenciaCommand,
    RegistrarResidenteUseCase,
    ActualizarUbicacionResidenteUseCase
)
from src.interfaces.operaciones_adapters import ResidenteRepositoryAdapter, RabbitMQIntegracionAdapter

from src.domain.bc_monitorizacion import (
    DispositivoEmbebido,
    ConfiguracionMonitorizacionLocal,
    SesionMonitorizacion
)
from src.application.bc_monitorizacion import RegistrarLecturaUseCase
from src.interfaces.monitorizacion_adapters import (
    MqttTelemetriaAdapter,
    SensorBiometricoSimuladoAdapter,
    ActuadorLocalReleAdapter
)

from src.application.bc_alertas import EventoAlertaRecibida, GestionarYNotificarAlertaUseCase
from src.interfaces.alertas_adapters import RestEmergenciasAdapter, IncidenteRepositoryAdapter


def ejecutar_simulacion():
    print("=" * 80)
    print("SISTEMA DE MONITORIZACIÓN Y ALERTAS PARA RESIDENCIA DE ANCIANOS (CLEAN ARCH & DDD)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. BOUNDED CONTEXT: OPERACIONES (Centro de Control Central de la Residencia)
    # -------------------------------------------------------------------------
    print("\n--- [1] BC: OPERACIONES (Registro y Configuración en Pasarela Local) ---")
    db_local = DatabaseClient("Almacen_Local_Residencia_1")
    residente_repo = ResidenteRepositoryAdapter(db_local)
    bus_integracion = RabbitMQIntegracionAdapter()

    registrar_residente_uc = RegistrarResidenteUseCase(residente_repo)
    actualizar_ubicacion_uc = ActualizarUbicacionResidenteUseCase(residente_repo, bus_integracion)

    umbral_clinico = UmbralClinico(
        bpmMinimo=50,
        bpmMaximo=110,
        temperaturaMaxima=37.8,
        tiempoMaximoInactividad=timedelta(minutes=30)
    )
    perfil = PerfilMonitorizacion(
        umbralClinico=umbral_clinico,
        frecuenciaLectura=timedelta(seconds=2),
        monitorizacionActiva=True
    )
    ubicacion_inicial = UbicacionResidencia(numeroPlanta=2, codigoHabitacion="HAB-204")

    cmd_registro = RegistrarResidenciaCommand(
        residenteId=101,
        codigo="RES-2026-01",
        nombre="Carlos Mendoza",
        ubicacion=ubicacion_inicial,
        perfil=perfil
    )
    residente_id = registrar_residente_uc.ejecutar(cmd_registro)
    actualizar_ubicacion_uc.procesarEvento(
        residente_id,
        UbicacionResidencia(numeroPlanta=2, codigoHabitacion="HAB-205")
    )

    # -------------------------------------------------------------------------
    # 2. BOUNDED CONTEXT: MONITORIZACIÓN (Módulo Embebido Sensor/Actuador)
    # -------------------------------------------------------------------------
    print("\n--- [2] BC: MONITORIZACIÓN (Muestreo de Sensores Embebidos) ---")
    dispositivo = DispositivoEmbebido(macAddress="AA:BB:CC:11:22:33", porcentajeBateria=85)
    config_local = ConfiguracionMonitorizacionLocal(
        residenteId=residente_id,
        bpmMinimo=umbral_clinico.bpmMinimo,
        bpmMaximo=umbral_clinico.bpmMaximo,
        temperaturaMaxima=umbral_clinico.temperaturaMaxima
    )
    sesion = SesionMonitorizacion(
        sesionId=5001,
        residenteId=residente_id,
        dispositivoId=1,
        dispositivo=dispositivo,
        configuracion=config_local
    )
    sesion.iniciarSesion()

    # Simulamos 3 lecturas: 2 normales y 1 crítica (Taquicardia 145 BPM + Fiebre 38.9°C)
    lecturas_simuladas = [
        (72, 36.5),
        (76, 36.7),
        (145, 38.9)
    ]
    sensor_adapter = SensorBiometricoSimuladoAdapter(lecturas_simuladas)
    mqtt_adapter = MqttTelemetriaAdapter(brokerUrl="mqtts://pasarela-local.residencia1:8883", qosLevel=1)
    actuador_adapter = ActuadorLocalReleAdapter()

    registrar_lectura_uc = RegistrarLecturaUseCase(
        sensorPort=sensor_adapter,
        pasarelaPort=mqtt_adapter,
        actuadorPort=actuador_adapter,
        sesion=sesion
    )

    eventos_detectados = []
    for ciclo in range(1, 4):
        print(f"\n> Ciclo de muestreo #{ciclo}:")
        eventos = registrar_lectura_uc.ejecutarCicloMuestreo()
        eventos_detectados.extend(eventos)

    sesion.finalizarSesion()

    # -------------------------------------------------------------------------
    # 3. BOUNDED CONTEXT: ALERTAS (Servicio Central de Gestión de Alertas)
    # -------------------------------------------------------------------------
    print("\n--- [3] BC: ALERTAS (Despacho a Emergencias, Familiares y Centro de Salud) ---")
    db_central = DatabaseClient("BD_Central_Alertas")
    http_client = HttpClient()
    incidente_repo = IncidenteRepositoryAdapter(db_central)
    rest_emergencias = RestEmergenciasAdapter(http_client)

    gestionar_alerta_uc = GestionarYNotificarAlertaUseCase(
        incidenteRepo=incidente_repo,
        notificacionPort=rest_emergencias
    )

    for idx, ev in enumerate(eventos_detectados, start=1):
        print(f"\n> Procesando evento crítico recibido #{idx} ({ev.tipoAnomalia.value}):")
        dto_alerta = EventoAlertaRecibida(
            incidenteId=9000 + idx,
            residenciaId=1,
            residenteId=ev.residenteId,
            sesionId=ev.sesionId,
            nivelSeveridad="CRITICA",
            segundosMaximosSLA=15,
            motivoClinico=f"{ev.tipoAnomalia.value} detectada con valor {ev.valorObservado}"
        )
        incidente = gestionar_alerta_uc.recibirYDespacharAlerta(dto_alerta)
        incidente.confirmarRecepcion(operadorId=77)

    print("\n" + "=" * 80)
    print("SIMULACIÓN FINALIZADA EXITOSAMENTE")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_simulacion()