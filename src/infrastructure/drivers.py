from typing import Dict, Any


# Driver simulado de Base de Datos (Almacén Local y BD Central)
class DatabaseClient:
    def __init__(self, nombre_bd: str):
        self.nombre_bd = nombre_bd
        self.tabla_residentes: Dict[int, Any] = {}
        self.tabla_incidentes: Dict[int, Any] = {}


# Driver simulado de Cliente HTTP/HTTPS para Servicios Externos
class HttpClient:
    def post(self, url: str, payload: dict) -> int:
        print(f"  [HTTPS POST -> {url}] Payload enviado: {payload}")
        return 200