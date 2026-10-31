# Arquitectura de Software para una Residencia de Ancianos (Clean Architecture & DDD)

Prototipo funcional implementado en Python aplicando **Arquitectura Limpia (Clean Architecture)** y **Diseño Dirigido por el Dominio (DDD)** para la monitorización biométrica, gestión operativa de residentes y despacho de alertas médicas críticas.

## 1. Contexto Cuantitativo y Cualitativo de la Solución

* **Distribución Geográfica y Usuarios Concurrentes:**
  * **Número total de residencias:** 5 residencias distribuidas en un radio geográfico máximo de 50 km.
  * **Capacidad y concurrencia:** 100 residentes por residencia (500 residentes en total) y 25 trabajadores concurrentes por turno en cada sede (enfermeros, médicos de planta, operadores).
* **Dispositivos Embebidos Involucrados:**
  * **Nodos vestibles (Wearables biométricos):** 1 por residente (100 por residencia) equipados con sensores de pulso (BPM), temperatura corporal (I2C/SPI) y acelerómetro para caídas. Frecuencia de muestreo: **cada 2 segundos**.
  * **Sensores ambientales y de habitación:** 150 por residencia (apertura de puertas, presencia PIR, temperatura ambiental) conectados por GPIO. Frecuencia de muestreo: **cada 60 segundos** (o disparo por interrupción/evento).
* **Middlewares y Protocolos de Comunicación:**
  * **Módulo Embebido $\rightarrow$ Pasarela Local:** **MQTT v5 sobre TLS** (bajo consumo energético, cabeceras mínimas de 2 bytes, soporte QoS 1 para telemetría ordinaria y QoS 2 para alertas críticas).
  * **Pasarela Local $\rightarrow$ Centro de Control:** **gRPC (HTTP/2 + Protobuf)** para llamadas síncronas de baja latencia y **RabbitMQ (AMQP)** para colas asíncronas de eventos de integración garantizando tolerancia a desconexiones temporales (Edge Buffering).
  * **Centro de Control $\rightarrow$ Entidades Externas:** **HTTPS REST** hacia el Servicio de Emergencias y Centro de Salud; **WebPush / SMS Gateway** hacia la App de Familiares y Proveedores.
* **Volumen de Transaccionalidad y Latencia (SLA):**
  * **Eventos por segundo (horas pico):** ~300 mensajes/segundo agregados en las 5 residencias (~60 msg/s por residencia).
  * **Tamaño medio por transacción:** 256 bytes (payload JSON/Protobuf compacto).
  * **Latencia máxima admisible:** $< 500\text{ ms}$ en red local (activación de relé de alarma en habitación) y $< 3\text{ segundos}$ extremo a extremo para alertas críticas despachadas a Emergencias.

## 2. Bounded Contexts Identificados (DDD)

1. **BC: Monitorización (Módulo Embebido Sensor/Actuador):**
   * *Aggregate Root:* `SesionMonitorizacion`
   * *Entities & Value Objects:* `DispositivoEmbebido`, `LecturaBiometrica`, `ConfiguracionMonitorizacionLocal`
   * *Domain Event:* `LecturaCriticaDetectada`
2. **BC: Operaciones (Centro de Control Central de la Residencia):**
   * *Aggregate Root:* `Residente`
   * *Value Objects:* `UbicacionResidencia`, `PerfilMonitorizacion`, `UmbralClinico`
3. **BC: Alertas (Servicio Central de Gestión de Alertas):**
   * *Aggregate Root:* `IncidenteAlerta`
   * *Entities & Value Objects:* `NotificacionDespachada`, `NivelSeveridad`
   * *Domain Event:* `AlertaEscaladaAEmergencias`

## 3. Estructura de Carpetas (Clean Architecture)

* `src/domain/`: **Entities & Business Rules.** Contiene los *Aggregate Roots*, *Entities*, *Value Objects* y *Domain Events* puros, sin dependencias externas.
* `src/application/`: **Use Cases (Interactors & Ports).** Define los puertos de entrada/salida (interfaces abstractas) e implementa los casos de uso que orquestan las entidades de dominio.
* `src/interfaces/`: **Interface Adapters.** Implementa las interfaces de la capa de aplicación (`MqttTelemetriaAdapter`, `ResidenteRepositoryAdapter`, `RestEmergenciasAdapter`).
* `src/infrastructure/`: **Frameworks & Drivers.** Simula los clientes de bajo nivel (`DatabaseClient`, `HttpClient`).
* `main.py`: **Punto de entrada** que inyecta las dependencias y ejecuta la simulación completa.

## 4. Instrucciones de Ejecución

Requisitos: **Python 3.10 o superior** (no requiere instalar librerías externas).

```bash
python main.py
```

El ejemplo simula tres lecturas biométricas: dos normales y una con valores críticos.
Los sensores, la base de datos, MQTT y las notificaciones externas son adaptadores
simulados; no se necesita hardware ni se realizan llamadas reales a esos servicios.