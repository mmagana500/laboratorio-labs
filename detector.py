import csv
import os
import time
from collections import defaultdict
from datetime import datetime

LOG_EVENTOS = "eventos.log"
LOG_RESPUESTA = "respuesta.log"
RESULTADOS = "resultados.csv"
UMBRAL = 3
FORMATO = "%Y-%m-%d %H:%M:%S"


def registrar_respuesta(accion, usuario):
    fecha = datetime.now().strftime(FORMATO)
    with open(LOG_RESPUESTA, "a", encoding="utf-8") as archivo:
        archivo.write(f"{fecha},{accion},{usuario}\n")
    return fecha


def ultimo_bloqueo():
    """Fecha del último bloqueo por usuario, para no procesar dos veces los mismos intentos."""
    bloqueos = {}
    if os.path.exists(LOG_RESPUESTA):
        with open(LOG_RESPUESTA, encoding="utf-8") as archivo:
            for linea in archivo:
                partes = linea.strip().split(",")
                if len(partes) == 3 and partes[1] == "USUARIO_BLOQUEADO":
                    bloqueos[partes[2]] = datetime.strptime(partes[0], FORMATO)
    return bloqueos


def leer_fallidos():
    fallidos = defaultdict(list)
    bloqueos = ultimo_bloqueo()
    if not os.path.exists(LOG_EVENTOS):
        return fallidos
    with open(LOG_EVENTOS, encoding="utf-8") as archivo:
        for linea in archivo:
            partes = linea.strip().split(",")
            if len(partes) != 3:
                continue
            fecha_txt, evento, usuario = partes
            fecha = datetime.strptime(fecha_txt, FORMATO)
            if evento == "LOGIN_FALLIDO" and fecha > bloqueos.get(usuario, datetime.min):
                fallidos[usuario].append(fecha_txt)
    return fallidos


def guardar_resultado(mttd, mttr):
    numero = 1
    if os.path.exists(RESULTADOS):
        with open(RESULTADOS, encoding="utf-8") as lectura:
            numero = sum(1 for _ in lectura)  # encabezado + filas previas = siguiente número
    with open(RESULTADOS, "a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        if numero == 1:
            escritor.writerow(["prueba", "MTTD", "MTTR"])
        escritor.writerow([numero, mttd, mttr])


def mostrar_promedios():
    if not os.path.exists(RESULTADOS):
        return
    with open(RESULTADOS, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        return
    print("\nResultados acumulados")
    print("Prueba | MTTD (s) | MTTR (s)")
    for f in filas:
        print(f"{f['prueba']:>6} | {f['MTTD']:>8} | {f['MTTR']:>8}")
    prom_mttd = sum(float(f["MTTD"]) for f in filas) / len(filas)
    prom_mttr = sum(float(f["MTTR"]) for f in filas) / len(filas)
    print(f"\nMTTD promedio: {prom_mttd:.1f} segundos")
    print(f"MTTR promedio: {prom_mttr:.1f} segundos")


def main():
    fallidos = leer_fallidos()
    alertas = 0

    for usuario, registros in fallidos.items():
        if len(registros) >= UMBRAL:
            alertas += 1
            primer_intento = registros[0]
            deteccion = datetime.now().strftime(FORMATO)

            print("\nALERTA DE SEGURIDAD")
            print(f"Usuario: {usuario}")
            print(f"Intentos fallidos: {len(registros)}")
            print(f"Primer intento: {primer_intento}")
            print(f"Detección: {deteccion}")

            # Respuesta simulada: bloqueo del usuario
            time.sleep(1)
            respuesta = registrar_respuesta("USUARIO_BLOQUEADO", usuario)
            print("Acción aplicada: bloqueo de usuario")
            print(f"Respuesta: {respuesta}")

            t_primero = datetime.strptime(primer_intento, FORMATO)
            t_deteccion = datetime.strptime(deteccion, FORMATO)
            t_respuesta = datetime.strptime(respuesta, FORMATO)

            mttd = (t_deteccion - t_primero).total_seconds()
            mttr = (t_respuesta - t_deteccion).total_seconds()
            print(f"MTTD: {mttd} segundos")
            print(f"MTTR: {mttr} segundos")
            guardar_resultado(mttd, mttr)

    if alertas == 0:
        print("Sin incidentes: no hay usuarios con 3 o más intentos fallidos nuevos.")
    mostrar_promedios()


if __name__ == "__main__":
    main()
