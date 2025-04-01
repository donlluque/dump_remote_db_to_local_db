import mysql.connector
import re
import subprocess
from datetime import datetime
import time
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv(override=True)

# Configuración de la base de datos remota
REMOTE_DB_CONFIG = {
    'host': os.getenv("remote_host"),
    'port': os.getenv("remote_port"),
    'user': os.getenv("remote_user"),
    'password': os.getenv("remote_password"),
    'database': os.getenv("remote_database"),
    'auth_plugin': os.getenv("auth_plugin"),
}

# Configuración de la base de datos local
LOCAL_DB_CONFIG = {
    'host': os.getenv("local_host"),
    'port': os.getenv("local_port"),
    'user': os.getenv("local_user"),
    'password': os.getenv("local_password"),
    'database': os.getenv("local_database")
}

# Configuración adicional
OPENVPN_PROFILE_NAME = os.getenv("openvpn_profile_name")
LOG_PATH = os.getenv("log_path")
DUMP_PATH = os.getenv("dump_path")


# Función para generar el nombre del archivo dump con la fecha actual
def get_dump_file_name():
    timestamp = datetime.now().strftime('%Y_%m_%d')
    os.makedirs(DUMP_PATH, exist_ok=True)
    return os.path.join(DUMP_PATH, f"_dump_{timestamp}.sql")

DUMP_FILE = get_dump_file_name()

# Función para generar el nombre del archivo log con la fecha actual
def get_log_file_name():
    timestamp = datetime.now().strftime('%Y_%m_%d')
    os.makedirs(LOG_PATH, exist_ok=True)
    return os.path.join(LOG_PATH, f"_log_{timestamp}.txt")

LOG_FILE = get_log_file_name()

# Función para escribir en el log
def write_log(message):
    timestamp = datetime.now().strftime('%Y_%m_%d %H:%M:%S')
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f'[{timestamp}] {message}\n')


def connect_to_openvpn():
    print("Conectando a OpenVPN...")
    write_log("Conectando a OpenVPN...")
    process = subprocess.Popen(
        ["openvpn-gui", "--connect", OPENVPN_PROFILE_NAME],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    # Esperar un tiempo prudente para la conexión
    time.sleep(10)
    # Verificar si el proceso de conexión aún está activo
    if process.poll() is None:
        print("Conexión a OpenVPN exitosa.")
        write_log("Conexión a OpenVPN exitosa.")
    else:
        print("Error al conectar a OpenVPN.")
        write_log("Error al conectar a OpenVPN.")
        raise Exception("No se pudo conectar a OpenVPN")

# Función para desconectarse de OpenVPN y cerrar la GUI
def disconnect_from_openvpn():
    print("Desconectando de OpenVPN...")
    write_log("Desconectando de OpenVPN...")

    # Cerrar la conexión VPN (proceso de openvpn.exe)
    process_vpn = subprocess.Popen(
        ["taskkill", "/F", "/IM", "openvpn.exe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    output_vpn, error_vpn = process_vpn.communicate()

    if process_vpn.returncode == 0:
        print("Conexión VPN cerrada correctamente.")
        write_log("Conexión VPN cerrada correctamente.")
    else:
        print(f"Error al desconectar la VPN: {error_vpn.decode()}")
        write_log(f"Error al desconectar la VPN: {error_vpn.decode()}")
        raise Exception("No se pudo desconectar la VPN")

    # Cerrar también la GUI de OpenVPN
    print("Cerrando la GUI de OpenVPN...")
    write_log("Cerrando la GUI de OpenVPN...")
    process_gui = subprocess.Popen(
        ["taskkill", "/F", "/IM", "openvpn-gui.exe"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    output_gui, error_gui = process_gui.communicate()

    if process_gui.returncode == 0:
        print("GUI de OpenVPN cerrada correctamente.")
        write_log("GUI de OpenVPN cerrada correctamente.")
    else:
        print(f"Error al cerrar la GUI de OpenVPN: {error_gui.decode()}")
        write_log(f"Error al cerrar la GUI de OpenVPN: {error_gui.decode()}")
        raise Exception("No se pudo cerrar la GUI de OpenVPN")

# Función para realizar el dump manual de la base de datos remota
def dump_remote_database_manual(dump_file):
    try:
        print("\nRealizando el DUMP de la base remota")
        write_log("\nRealizando el DUMP de la base remota")

        # Conectar a la base de datos remota
        remote_conn = mysql.connector.connect(**REMOTE_DB_CONFIG)
        cursor = remote_conn.cursor()

        # Dump de tablas
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';")
        tables = cursor.fetchall()

        with open(dump_file, 'w') as file:
            file.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            for table in tables:
                table_name = table[0]
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`;")
                create_table = cursor.fetchone()[1]
                file.write(f"{create_table};\n\n")

                cursor.execute(f"SELECT * FROM `{table_name}`;")
                rows = cursor.fetchall()
                for row in rows:
                    values = ', '.join([f"'{str(x).replace('\'', '\\\'')}'" if x is not None else 'NULL' for x in row])
                    file.write(f"INSERT INTO `{table_name}` VALUES ({values});\n")
                file.write("\n")

            file.write("SET FOREIGN_KEY_CHECKS = 1;\n\n")

        print("\nDump completado exitosamente.")
        write_log("\nDump completado exitosamente.")
        cursor.close()
        remote_conn.close()

    except mysql.connector.Error as err:
        print(f"\nError: {err}")
        write_log(f"\nError: {err}")
        raise

# Función para eliminar la base de datos local
def drop_local_database():
    try:
        local_conn = mysql.connector.connect(
            host=LOCAL_DB_CONFIG['host'],
            user=LOCAL_DB_CONFIG['user'],
            password=LOCAL_DB_CONFIG['password']
        )
        local_cursor = local_conn.cursor()

        database_name = LOCAL_DB_CONFIG['database']
        drop_statement = f"DROP DATABASE IF EXISTS `{database_name}`;"
        local_cursor.execute(drop_statement)
        print(f"\nBase de datos {database_name} eliminada.")
        write_log(f"\nBase de datos {database_name} eliminada.")

        create_statement = f"CREATE DATABASE `{database_name}`;"
        local_cursor.execute(create_statement)
        print(f"Base de datos {database_name} creada nuevamente.")
        write_log(f"Base de datos {database_name} creada nuevamente.")

        local_cursor.close()
        local_conn.close()

    except mysql.connector.Error as err:
        print(f"\nError al eliminar la base de datos local: {err}")
        write_log(f"\nError al eliminar la base de datos local: {err}")
        raise

# Extrae las sentencias de creación de tablas y las restricciones de claves foráneas
def extract_table_statements():
    table_statements = []
    foreign_key_constraints = []
    with open(DUMP_FILE, 'r') as dump_file:
        current_statement = ""
        for line in dump_file:
            if line.strip():
                current_statement += line
                if line.strip().endswith(";"):
                    if current_statement.upper().startswith("CREATE TABLE"):
                        # Extraer restricciones de claves foráneas
                        table_name_match = re.search(r"CREATE TABLE `(\w+)`", current_statement)
                        if table_name_match:
                            table_name = table_name_match.group(1)
                        else:
                            current_statement = ""
                            continue

                        # Separar definición de columnas y restricciones
                        columns_and_constraints = re.search(r"\((.*)\)", current_statement, re.DOTALL).group(1)
                        columns = []
                        constraints = []
                        parentheses_counter = 0
                        buffer = ''
                        for char in columns_and_constraints:
                            buffer += char
                            if char == '(':
                                parentheses_counter += 1
                            elif char == ')':
                                parentheses_counter -= 1
                            elif char == ',' and parentheses_counter == 0:
                                if 'CONSTRAINT' in buffer or 'FOREIGN KEY' in buffer:
                                    constraints.append(buffer.strip().rstrip(','))
                                else:
                                    columns.append(buffer.strip().rstrip(','))
                                buffer = ''
                        if buffer:
                            if 'CONSTRAINT' in buffer or 'FOREIGN KEY' in buffer:
                                constraints.append(buffer.strip().rstrip(','))
                            else:
                                columns.append(buffer.strip().rstrip(','))

                        # Reconstruir CREATE TABLE sin restricciones
                        new_create_table = f"CREATE TABLE `{table_name}` (\n  {',\n  '.join(columns)}\n) ENGINE=InnoDB;\n"
                        table_statements.append(new_create_table)

                        # Agregar restricciones de claves foráneas
                        for constraint in constraints:
                            foreign_key_constraints.append(f"ALTER TABLE `{table_name}` ADD {constraint};")

                    current_statement = ""
    return table_statements, foreign_key_constraints

# Crea todas las tablas sin restricciones de claves foráneas
def create_tables(cursor, table_statements):
    for statement in table_statements:
        table_name_match = re.search(r"CREATE TABLE `(\w+)`", statement)
        if table_name_match:
            table_name = table_name_match.group(1)
        else:
            continue
        try:
            print(f"Creando tabla: {table_name}")
            write_log(f"Creando tabla: {table_name}")
            cursor.execute(statement)
        except mysql.connector.Error as err:
            print(f"Error al crear tabla '{table_name}': {err}")
            write_log(f"Error al crear tabla '{table_name}': {err}")
            raise

# Agrega las restricciones de claves foráneas a las tablas
def add_foreign_keys(cursor, foreign_key_constraints):
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    for constraint in foreign_key_constraints:
        try:
            print(f"Agregando restricción de clave foránea: {constraint}")
            write_log(f"Agregando restricción de clave foránea: {constraint}")
            cursor.execute(constraint)
        except mysql.connector.Error as err:
            print(f"Error al agregar clave foránea: {err}")
            write_log(f"Error al agregar clave foránea: {err}")
            raise
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

# Restaura los datos en las tablas locales basados en el dump
def restore_data_from_dump(cursor):
    current_table = None
    with open(DUMP_FILE, 'r') as dump_file:
        current_statement = ""
        for line in dump_file:
            if line.strip():
                current_statement += line
                if line.strip().endswith(";"):
                    if current_statement.upper().startswith("INSERT INTO"):
                        # Corregir valores para columnas BIT(1)
                        current_statement = re.sub(r"'(0|1)'", r"\1", current_statement)  # Eliminar comillas en 0 y 1
                        current_statement = re.sub(r"'NULL'", r"NULL", current_statement)  # Eliminar comillas en NULL

                        # Obtener el nombre de la tabla
                        table_name = re.search(r"INSERT INTO `(\w+)`", current_statement)
                        if table_name:
                            table_name = table_name.group(1)
                            # Solo imprime cuando cambia de tabla
                            if table_name != current_table:
                                current_table = table_name
                                print(f"Cargando los datos de la tabla: {current_table}")
                                write_log(f"Cargando los datos de la tabla: {current_table}")

                        try:
                            cursor.execute(current_statement)
                        except mysql.connector.Error as err:
                            print(f"\nError: {err}")
                            write_log(f"\nError: {err}")
                            raise
                    current_statement = ""

# Crea las tablas y restaura los datos en la base de datos local
def setup_database():
    try:
        local_conn = mysql.connector.connect(
            host=LOCAL_DB_CONFIG['host'],
            user=LOCAL_DB_CONFIG['user'],
            password=LOCAL_DB_CONFIG['password'],
            database=LOCAL_DB_CONFIG['database']
        )
        local_cursor = local_conn.cursor()

        # Crear todas las tablas primero
        table_statements, foreign_key_constraints = extract_table_statements()
        create_tables(local_cursor, table_statements)

        # Restaurar los datos
        restore_data_from_dump(local_cursor)

        # Agregar claves foráneas
        add_foreign_keys(local_cursor, foreign_key_constraints)

        local_conn.commit()
        local_cursor.close()
        local_conn.close()

        print("\nBase de datos restaurada exitosamente.")
        write_log("\nBase de datos restaurada exitosamente.")

    except mysql.connector.Error as err:
        print(f"\nError: {err}")
        write_log(f"\nError: {err}")
        raise

# Script principal
import traceback

if __name__ == "__main__":
    try:
        # Conectar a OpenVPN
        connect_to_openvpn()

        # Realizar el dump de la base de datos remota
        dump_file_name = get_dump_file_name()
        dump_remote_database_manual(dump_file_name)

        # Desconectar de OpenVPN
        disconnect_from_openvpn()

    except Exception as e:
        print(f"\nError durante el proceso de dump: {e}")
        print(f"Detalles del error:\n{traceback.format_exc()}")
        write_log(f"\nError durante el proceso de dump: {e}")
        write_log(f"Detalles del error:\n{traceback.format_exc()}")
        sys.exit(1)

    try:
        # Eliminar la base de datos local
        drop_local_database()

        # Restaurar tablas y datos
        setup_database()

    except Exception as e:
        print(f"\nError durante el proceso de restauración: {e}")
        print(f"Detalles del error:\n{traceback.format_exc()}")
        write_log(f"\nError durante el proceso de restauración: {e}")
        write_log(f"Detalles del error:\n{traceback.format_exc()}")
        sys.exit(1)

    print("\nProceso completado con éxito.")
    write_log("\nProceso completado con éxito.")
