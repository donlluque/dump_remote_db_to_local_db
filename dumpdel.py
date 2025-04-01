import os
import pathlib
from dotenv import load_dotenv


# Cargar variables de entorno desde un archivo .env
load_dotenv(override=True)

DUMP_PATH = os.getenv("dump_path")

def limpiar_directorio(ruta_directorio, max_archivos=14):
    # Verifica que la ruta exista
    if not os.path.isdir(ruta_directorio):
        print(f"La ruta {ruta_directorio} no existe o no es un directorio.")
        return
    
    # Obtiene la lista de archivos en el directorio
    archivos = [pathlib.Path(ruta_directorio) / archivo for archivo in os.listdir(ruta_directorio)]
    
    # Filtra solo los archivos, excluyendo subdirectorios
    archivos = [archivo for archivo in archivos if archivo.is_file()]
    
    # Ordena los archivos por fecha de modificación (de más antiguo a más reciente)
    archivos.sort(key=lambda archivo: archivo.stat().st_mtime)
    
    # Si hay más de 14 archivos, elimina los más antiguos
    if len(archivos) > max_archivos:
        archivos_a_borrar = archivos[:-max_archivos]  # Selecciona los archivos a borrar
        for archivo in archivos_a_borrar:
            try:
                os.remove(archivo)
                print(f"Archivo eliminado: {archivo}")
            except Exception as e:
                print(f"No se pudo eliminar el archivo {archivo}: {e}")
    else:
        print(f"No hay más de {max_archivos} archivos en el directorio.")

# Ejemplo de uso
ruta_directorio = DUMP_PATH
limpiar_directorio(ruta_directorio)
