# Script para Dump de una bbdd remota y restauración del dump en una bbdd local

Este script, llamado `dump.py`, realiza un dump de una base de datos MySQL remota (por ejemplo de AWS), lo almacena en una carpeta local de dumps, y luego lo restaura en una base de datos local. Durante este proceso, se maneja la conexión y desconexión de OpenVPN, además de registrar logs en una carpeta específica.

## Características

- Se conecta a una VPN con OpenVPNutilizando el perfil `perfil_openvpn`.
- Realiza el dump de la base de datos remota.
- Cierra la conexión a la VPN antes de iniciar la restauración en la base de datos local.
- Guarda los archivos de dump en una carpeta local específica.
- Registra y guarda logs en una carpeta local específica.
- Utiliza un archivo `.env` para almacenar configuraciones como rutas y credenciales.

## Requisitos

- Python 3.x
- MySQL
- OpenVPN
- Archivo `.env` con las configuraciones necesarias
- Dependencias instaladas mediante `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```sh
   git clone <repositorio>
   cd <repositorio>
   ```
2. Crear y activar un entorno virtual (opcional pero recomendado):
   ```sh
   python -m venv venv
   source venv/bin/activate  # En Linux/macOS
   source venv/Scripts/activate     # En Windows
   ```
3. Instalar dependencias:
   ```sh
   pip install -r requirements.txt
   ```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
OPENVPN_PROFILE_NAME = <perfil_openvpn>
LOG_PATH = ruta/del/archivo/log
DUMP_PATH = ruta/del/archivo/dump

# Configuración de la base de datos remota
remote_host= RUTA_HOST_REMOTO
remote_port= 3306
remote_user= USUARIO_REMOTO
remote_password= PASSWORD_HOST_REMOTO
remote_database= NOMBRE_BBDD_REMOTA
auth_plugin= caching_sha2_password

# Configuración de la base de datos local
local_host= RUTA_HOST_LOCAL
local_port= 3306
local_user= USUARIO_LOCAL
local_password= PASSWORD_HOST_LOCAL
local_database= NOMBRE_BBDD_LOCAL
```

## Uso

Para ejecutar el script:

```sh
python dump.py
```

## Flujo del Script

1. Conectar a la VPN con `perfil_openvpn`.
2. Realizar el dump de la base de datos remota y guardarlo en `ruta/del/archivo/dump`.
3. Cerrar la conexión a la VPN.
4. Restaurar la base de datos local con el dump generado.
5. Registrar el proceso en `ruta/del/archivo/log`.

## Logs

Todos los eventos y errores se registran en la carpeta de logs especificada en el `.env`. Esto facilita la depuración y seguimiento de errores.

# EXTRA funcionalidad

También se incluye un segundo script `dumpdel.py` el cual busca en la ruta establecida donde se guardan los dumps y elimina los mas antiguos manteniendo siempre una cantidad de 14 dumps.

## Uso

Para ejecutar el script:

```sh
python dumpdel.py
```
