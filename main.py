"""Menú principal del motor de autómatas: AFD, AFND y Autómatas de Pila."""

import os
from copy import deepcopy

# --- Módulos de fases 1 y 2 ---
from AFD import AFD
from AFND import AFND
from CargadorAFD import CargadorAFD
from CargadorAFND import CargadorAFND
from ConvertidorAFND import ConvertidorAFND
from SimuladorAFD import SimuladorAFD
from ValidadorAFD import ValidadorAFD
from ValidadorAFND import ValidadorAFND

# --- Módulos de fase 3: Autómatas de Pila ---
from AutomataPila import AutomataPila, EPS
import CargadorAP
import ValidadorAP
import SimuladorAP
from SimuladorAP import (
    ACEPTADA, RECHAZADA, DETENIDA_POR_LIMITE, ENTRADA_INVALIDA,
)


# ---------------------------------------------------------------------------
# Presentación del menú
# ---------------------------------------------------------------------------

def mostrar_menu():
    """Muestra las dieciocho opciones de las tres fases del proyecto."""
    print("\n" + "=" * 68)
    print("MOTOR DE VALIDACIÓN Y CONVERSIÓN DE AUTÓMATAS".center(68))
    print("elaborado por: Gerber Perez y Marco Donadio".center(68))
    print("=" * 68)
    print(" 1. Crear un AFD manualmente")
    print(" 2. Cargar un AFD desde un archivo .txt")
    print(" 3. Crear un AFND manualmente")
    print(" 4. Cargar un AFND desde un archivo .txt")
    print(" 5. Mostrar la definición formal y la tabla del autómata cargado")
    print(" 6. Validar el autómata original y el AFD generado, si existe")
    print(" 7. Convertir el AFND cargado en un AFD equivalente")
    print(" 8. Mostrar la tabla de equivalencias de macroestados")
    print(" 9. Mostrar la definición formal y la tabla del AFD generado")
    print("10. Evaluar una cadena")
    print("11. Evaluar un archivo de cadenas")
    print("12. Consultar el historial de evaluaciones")
    print("13. Realizar el análisis estructural")
    print("14. Cargar o crear otro autómata (AFD/AFND)")
    print("15. Salir")
    print("--- Fase 3: Autómatas de Pila ---")
    print("16. Crear un APD o APND manualmente")
    print("17. Cargar un APD o APND desde un archivo .txt")
    print("18. Ajustar el límite de exploración para AP")


# ---------------------------------------------------------------------------
# Lógica de AFD y AFND (sin cambios de la fase 2)
# ---------------------------------------------------------------------------

def mostrar_validacion(automata):
    """Valida el tipo de autómata activo y muestra un reporte comprensible."""
    if automata is None:
        print("\nError: primero debe crear o cargar un autómata.")
        return

    if isinstance(automata, AFND):
        valido, errores = ValidadorAFND.validar(automata)
        print("\n--- VALIDACIÓN DEL AFND ---")
        print("Clasificación:", "AFND VÁLIDO" if valido else "AFND INVÁLIDO")
        _mostrar_lista_errores(errores)
        return

    valido, errores = ValidadorAFD.validar(automata)
    clasificacion = ValidadorAFD.clasificar(automata)
    print("\n--- VALIDACIÓN DEL AFD ---")
    print("Clasificación:", clasificacion)

    if valido:
        print("El AFD es determinista, completo y estructuralmente válido.")
        return

    _mostrar_lista_errores(errores)

    if clasificacion == "AFD INCOMPLETO":
        respuesta = input(
            "¿Desea completarlo con un estado de trampa? (s/n): "
        ).strip().lower()
        if respuesta in ("s", "si", "sí"):
            nombre, cantidad = ValidadorAFD.completar_con_estado_trampa(automata)
            ValidadorAFD.validar(automata)
            print("Estado de trampa agregado:", nombre)
            print("Transiciones completadas:", cantidad)
            print("Nueva clasificación:", ValidadorAFD.clasificar(automata))


def obtener_afd_operativo(automata, afd_generado):
    """Selecciona el AFD directo o el resultado de una conversión."""
    if isinstance(automata, AFD):
        return automata
    if isinstance(automata, AFND):
        if afd_generado is None:
            print("\nError: convierta el AFND antes de usar esta función.")
            return None
        print("Se utiliza el AFD equivalente generado:", afd_generado.nombre)
        return afd_generado
    print("\nError: primero debe crear o cargar un autómata AFD o AFND.")
    return None


def asegurar_afd_valido(afd):
    """Impide simulaciones sobre un AFD inválido, incompleto o no determinista."""
    if afd is None:
        return False
    valido, errores = ValidadorAFD.validar(afd)
    if valido:
        return True
    print("\nError: el AFD no está listo para procesar cadenas.")
    print("Clasificación:", ValidadorAFD.clasificar(afd))
    _mostrar_lista_errores(errores)
    return False


def evaluar_archivo_cadenas_afd(afd):
    """Evalúa cada línea de un archivo sobre un AFD."""
    if not asegurar_afd_valido(afd):
        return
    ruta = input("Ruta del archivo de cadenas: ").strip()
    try:
        with open(CargadorAFD.normalizar_ruta(ruta), "r", encoding="utf-8-sig") as archivo:
            print("\n--- EVALUACIÓN POR LOTES (AFD) ---")
            for numero, linea in enumerate(archivo, start=1):
                cadena = linea.rstrip("\r\n")
                print("\nCadena", str(numero) + ":", repr(cadena))
                aceptada, resultado = SimuladorAFD.evaluar(afd, cadena, True)
                if resultado not in ("Aceptada", "Rechazada"):
                    print("Error:", resultado)
    except (OSError, UnicodeError, ValueError) as error:
        print("Error: no fue posible leer el archivo:", error)


def mostrar_historial_afd(afd):
    """Muestra las evaluaciones del AFD activo en orden cronológico."""
    if afd is None:
        return
    if not afd.historial:
        print("\nNo hay evaluaciones registradas.")
        return
    print("\n--- HISTORIAL DE EVALUACIONES (AFD/AFND) ---")
    for indice, registro in enumerate(afd.historial, start=1):
        print(
            str(indice) + ". Cadena: " + repr(registro["cadena"])
            + " | Estado final: " + registro["estado_final"]
            + " | Resultado: " + registro["resultado"]
        )


def mostrar_analisis_afd(afd):
    """Presenta accesibilidad, estados inútiles y posible lenguaje vacío de un AFD."""
    if not asegurar_afd_valido(afd):
        return
    analisis = ValidadorAFD.analizar_estructura(afd)
    print("\n--- ANÁLISIS ESTRUCTURAL (AFD) ---")
    print("Estados alcanzables:", _formatear_conjunto(analisis["alcanzables"]))
    print("Estados inaccesibles:", _formatear_conjunto(analisis["inaccesibles"]))
    print(
        "Estados finales alcanzables:",
        _formatear_conjunto(analisis["finales_alcanzables"]),
    )
    if analisis["lenguaje_posiblemente_vacio"]:
        print("El lenguaje es vacío: no existe un estado final alcanzable.")
    else:
        print("El lenguaje no es vacío: existe al menos un estado final alcanzable.")


def crear_o_cargar_afxnd(opcion=None):
    """Centraliza las cuatro formas de ingresar un AFD o AFND."""
    if opcion is None:
        print("\n1. Crear AFD manualmente")
        print("2. Cargar AFD desde archivo")
        print("3. Crear AFND manualmente")
        print("4. Cargar AFND desde archivo")
        opcion = input("Seleccione una opción (1-4): ").strip()

    if opcion == "1":
        return CargadorAFD.crear_manual()
    if opcion == "2":
        ruta = input("Ruta del archivo AFD: ").strip()
        return CargadorAFD.cargar_archivo(ruta)
    if opcion == "3":
        return CargadorAFND.crear_manual()
    if opcion == "4":
        ruta = input("Ruta del archivo AFND: ").strip()
        return CargadorAFND.cargar_archivo(ruta)
    print("Error: opción inválida.")
    return None


def preparar_nuevo_automata_afxnd(automata):
    """Valida un AFND, muestra su tabla y ejecuta la conversión automática."""
    if not isinstance(automata, AFND):
        return None, {}
    valido, errores = ValidadorAFND.validar(automata)
    if not valido:
        print("\nEl AFND fue cargado, pero contiene errores:")
        _mostrar_lista_errores(errores)
        return None, {}
    automata.mostrar_tabla_transicion()
    afd, equivalencias, errores = ConvertidorAFND.convertir(automata)
    if errores:
        print("\nNo fue posible realizar la conversión automática:")
        _mostrar_lista_errores(errores)
        return None, {}
    print("Conversión automática completada. Macroestados:", len(equivalencias))
    return afd, equivalencias


# ---------------------------------------------------------------------------
# Lógica de AP (fase 3)
# ---------------------------------------------------------------------------

def mostrar_validacion_ap(ap):
    """Valida el AP activo y muestra el reporte."""
    valido, errores = ValidadorAP.validar(ap)
    tipo = ap.tipo
    print("\n--- VALIDACIÓN DEL {} ---".format(tipo))
    print("Resultado:", "VÁLIDO" if valido else "INVÁLIDO")
    _mostrar_lista_errores(errores)


def evaluar_cadena_ap(ap, limite):
    """Evalúa una cadena individual sobre el AP activo."""
    cadena = input("Ingrese la cadena (Enter representa ε): ")
    resultado = SimuladorAP.evaluar_y_mostrar(ap, cadena, limite=limite)
    # Registrar en historial solo evaluaciones que no sean ENTRADA_INVALIDA
    if resultado.estado_resultado != ENTRADA_INVALIDA:
        resumen = {
            "cadena": cadena,
            "tipo": ap.tipo,
            "resultado": resultado.estado_resultado,
            "motivo": resultado.motivo,
            "limite": resultado.limite_usado,
            "admitidas": resultado.admitidas,
            "procesadas": resultado.procesadas,
        }
        ap.agregar_evaluacion_historial(resumen)


def evaluar_archivo_cadenas_ap(ap, limite):
    """Evalúa cada línea de un archivo sobre el AP activo."""
    if not ap.es_valido:
        print("\nError: el AP no está validado. Use la opción 6.")
        return
    ruta = input("Ruta del archivo de cadenas: ").strip()
    try:
        with open(CargadorAFD.normalizar_ruta(ruta), "r", encoding="utf-8-sig") as archivo:
            print("\n--- EVALUACIÓN POR LOTES ({}) ---".format(ap.tipo))
            for numero, linea in enumerate(archivo, start=1):
                # Las cadenas de lote pierden solo CR/LF; no se aplica strip().
                cadena = linea.rstrip("\r\n")
                print("\nCadena {}: {!r}".format(numero, cadena))
                # Presupuesto se reinicia por cada cadena del lote.
                resultado = SimuladorAP.evaluar(ap, cadena, limite=limite)
                print("Resultado: {} — {}".format(
                    resultado.estado_resultado, resultado.motivo
                ))
                if resultado.estado_resultado != ENTRADA_INVALIDA:
                    resumen = {
                        "cadena": cadena,
                        "tipo": ap.tipo,
                        "resultado": resultado.estado_resultado,
                        "motivo": resultado.motivo,
                        "limite": resultado.limite_usado,
                        "admitidas": resultado.admitidas,
                        "procesadas": resultado.procesadas,
                    }
                    ap.agregar_evaluacion_historial(resumen)
    except (OSError, UnicodeError, ValueError) as error:
        print("Error: no fue posible leer el archivo:", error)


def mostrar_historial_ap(ap):
    """Muestra el historial de evaluaciones del AP activo."""
    if not ap.historial:
        print("\nNo hay evaluaciones registradas para este AP.")
        return
    print("\n--- HISTORIAL DE EVALUACIONES ({}) ---".format(ap.tipo))
    for indice, registro in enumerate(ap.historial, start=1):
        print(
            "{}. Cadena: {!r} | Tipo: {} | Resultado: {} | Motivo: {}".format(
                indice,
                registro.get("cadena", ""),
                registro.get("tipo", ""),
                registro.get("resultado", ""),
                registro.get("motivo", ""),
            )
        )


def mostrar_analisis_ap(ap):
    """
    Análisis estructural del AP.

    D03 (DECISIONES.md) está pendiente de resolución. Mientras tanto se
    muestra únicamente conectividad orientativa del grafo de estados, con
    la aclaración explícita de que no demuestra que haya una ejecución
    realizable ni que el lenguaje sea no vacío (el grafo ignora pila y
    entrada).
    """
    print("\n--- ANÁLISIS ESTRUCTURAL ({}) ---".format(ap.tipo))
    print("NOTA: El siguiente análisis se basa en conectividad del grafo de estados.")
    print("      No tiene en cuenta la pila ni los símbolos de entrada.")
    print("      Un estado conectado no garantiza que exista una ejecución realizable.")
    print("      La decisión D03 sobre el alcance exacto de este análisis está pendiente.\n")

    if not ap.estados:
        print("Sin estados definidos.")
        return

    # Calcular estados alcanzables desde q0 ignorando pila y entrada.
    alcanzables = set()
    frontera = {ap.estado_inicial}
    while frontera:
        estado = frontera.pop()
        if estado in alcanzables:
            continue
        alcanzables.add(estado)
        for (origen, _entrada, _tope), alternativas in ap.transiciones.items():
            if origen == estado:
                for destino, _remp in alternativas:
                    if destino not in alcanzables:
                        frontera.add(destino)

    inaccesibles = ap.estados - alcanzables
    finales_alcanzables = ap.estados_finales & alcanzables

    print("Estados (Q)          :", _formatear_conjunto(ap.estados))
    print("Alcanzables (grafo)  :", _formatear_conjunto(alcanzables))
    print("Inaccesibles (grafo) :", _formatear_conjunto(inaccesibles))
    print("Finales alcanzables  :", _formatear_conjunto(finales_alcanzables))
    if not finales_alcanzables:
        print("Observación: ningún estado final es alcanzable en el grafo.")
        print("             (No implica lenguaje vacío: depende de la pila y la entrada.)")
    else:
        print("Observación: al menos un estado final es alcanzable en el grafo.")
        print("             (No implica lenguaje no vacío: depende de la pila y la entrada.)")


def ajustar_limite_ap(limite_actual):
    """Solicita un nuevo límite de exploración y lo valida."""
    print("\nLímite actual de exploración AP:", limite_actual)
    while True:
        texto = input("Nuevo límite (entero positivo, Enter para cancelar): ").strip()
        if texto == "":
            print("Límite sin cambios.")
            return limite_actual
        try:
            nuevo = int(texto)
        except ValueError:
            print("Error: ingrese un número entero positivo.")
            continue
        if nuevo <= 0:
            print("Error: el límite debe ser mayor que cero.")
            continue
        print("Límite actualizado a:", nuevo)
        return nuevo


# ---------------------------------------------------------------------------
# Helpers comunes
# ---------------------------------------------------------------------------

def _mostrar_lista_errores(errores):
    if not errores:
        print("No se encontraron errores estructurales.")
        return
    for error in errores:
        print("-", error)


def _formatear_conjunto(elementos):
    if not elementos:
        return "∅"
    return "{" + ", ".join(sorted(elementos)) + "}"


def _copiar_definicion(automata):
    """Guarda los componentes para detectar cambios sin incluir historial."""
    return deepcopy((
        automata.nombre, automata.estados, automata.alfabeto,
        automata.estado_inicial, automata.estados_finales, automata.transiciones
    ))


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------

def main():
    """
    Mantiene la sesión activa de autómatas.

    Variables de sesión:
      automata_actual  — AFD o AFND cargado actualmente (fases 1/2).
      afd_generado     — AFD equivalente producido por conversión de AFND.
      equivalencias    — Mapa macroestado → subconjunto AFND.
      ap_actual        — AutomataPila activo (APD o APND, fase 3).
      limite_ap        — Presupuesto de exploración para AP (por defecto 10 000).

    Las sesiones son independientes: cargar un AP no borra el AFD/AFND,
    y viceversa.  Las opciones 5-13 operan sobre el tipo activo pertinente
    (AFD/AFND o AP según cuál esté cargado) con mensajes comprensibles cuando
    la opción no aplica al tipo activo.
    """
    automata_actual = None   # AFD o AFND (activo cuando ap_actual es None)
    afd_generado = None      # resultado de conversión de AFND
    equivalencias = {}
    definicion_convertida = None

    ap_actual = None         # AutomataPila (APD o APND); activo cuando no es None
    limite_ap = 10000        # presupuesto por defecto para AP

    # Nota de diseño: solo hay un autómata "activo" a la vez.
    # Cargar AFD/AFND borra ap_actual; cargar AP borra automata_actual y afd_generado.
    # Esto evita ambigüedad en las opciones 5-13 que operan sobre el activo.

    print("\nBienvenido al motor de autómatas - Fases 1, 2 y 3")
    print("Las rutas relativas parten de:", os.getcwd())
    print("Puede pegar rutas absolutas o relativas entre comillas coincidentes.")

    while True:
        try:
            mostrar_menu()
            opcion = input("Seleccione una opción (1-18): ").strip()

            # Detectar cambios en el AFND que invaliden la conversión existente.
            if (afd_generado is not None
                    and automata_actual is not None
                    and isinstance(automata_actual, AFND)
                    and _copiar_definicion(automata_actual) != definicion_convertida):
                afd_generado, equivalencias = None, {}
                definicion_convertida = None
                print("El AFND cambió; vuelva a convertirlo antes de usar su equivalente.")

            # ----------------------------------------------------------
            # Opciones 1-4: crear o cargar AFD/AFND
            # ----------------------------------------------------------
            if opcion in ("1", "2", "3", "4"):
                nuevo = crear_o_cargar_afxnd(opcion)
                if nuevo is not None:
                    afd_nuevo, nuevas_equiv = preparar_nuevo_automata_afxnd(nuevo)
                    if isinstance(nuevo, AFND) and afd_nuevo is None:
                        continue
                    automata_actual = nuevo
                    afd_generado = afd_nuevo
                    equivalencias = nuevas_equiv
                    definicion_convertida = (
                        _copiar_definicion(nuevo) if afd_generado is not None else None
                    )
                    # Limpiar AP activo: sesión AFD/AFND toma el control
                    ap_actual = None
                    print("\nAutómata cargado. Los datos anteriores de AFD/AFND fueron limpiados.")

            # ----------------------------------------------------------
            # Opción 5: mostrar definición del autómata activo
            # ----------------------------------------------------------
            elif opcion == "5":
                if ap_actual is not None:
                    # Si hay un AP activo, mostrarlo
                    ap_actual.mostrar_definicion_formal()
                elif automata_actual is not None:
                    automata_actual.mostrar_definicion_formal()
                    automata_actual.mostrar_tabla_transicion()
                else:
                    print("\nError: primero debe crear o cargar un autómata.")

            # ----------------------------------------------------------
            # Opción 6: validar autómata activo
            # ----------------------------------------------------------
            elif opcion == "6":
                if ap_actual is not None:
                    mostrar_validacion_ap(ap_actual)
                elif automata_actual is not None:
                    print("\n--- AUTÓMATA ORIGINAL ---")
                    mostrar_validacion(automata_actual)
                    if afd_generado is not None:
                        print("\n--- AFD EQUIVALENTE GENERADO ---")
                        mostrar_validacion(afd_generado)
                else:
                    print("\nError: primero debe crear o cargar un autómata.")

            # ----------------------------------------------------------
            # Opción 7: convertir AFND (no aplica a AP)
            # ----------------------------------------------------------
            elif opcion == "7":
                if ap_actual is not None:
                    print("\nEsta opción convierte un AFND a AFD.")
                    print("El autómata activo es un AP ({}); la conversión no aplica.".format(
                        ap_actual.tipo
                    ))
                elif not isinstance(automata_actual, AFND):
                    print("\nError: debe existir un AFND cargado para convertirlo.")
                elif afd_generado is not None and ValidadorAFD.validar(afd_generado)[0]:
                    print("La conversión ya está disponible; se conserva el historial.")
                else:
                    afd_nuevo, nuevas_equiv, errores = ConvertidorAFND.convertir(
                        automata_actual
                    )
                    if errores:
                        print("\nNo fue posible convertir el AFND:")
                        _mostrar_lista_errores(errores)
                    else:
                        afd_generado = afd_nuevo
                        equivalencias = nuevas_equiv
                        definicion_convertida = _copiar_definicion(automata_actual)
                        print("\nAFND convertido correctamente en un AFD equivalente.")
                        print("Macroestados generados:", len(equivalencias))

            # ----------------------------------------------------------
            # Opción 8: equivalencias de macroestados (no aplica a AP)
            # ----------------------------------------------------------
            elif opcion == "8":
                if ap_actual is not None:
                    print("\nEsta opción muestra equivalencias de macroestados AFND→AFD.")
                    print("El autómata activo es un AP ({}); no aplica.".format(ap_actual.tipo))
                else:
                    ConvertidorAFND.mostrar_equivalencias(equivalencias)

            # ----------------------------------------------------------
            # Opción 9: definición del AFD generado (no aplica a AP)
            # ----------------------------------------------------------
            elif opcion == "9":
                if ap_actual is not None:
                    print("\nEsta opción muestra el AFD equivalente de un AFND.")
                    print("El autómata activo es un AP ({}); no aplica.".format(ap_actual.tipo))
                elif afd_generado is None:
                    print("\nError: todavía no existe un AFD generado; convierta un AFND primero.")
                else:
                    afd_generado.mostrar_definicion_formal()
                    print("\n--- TABLA DE TRANSICIONES DEL AFD GENERADO ---")
                    afd_generado.mostrar_tabla_transicion()

            # ----------------------------------------------------------
            # Opción 10: evaluar una cadena
            # ----------------------------------------------------------
            elif opcion == "10":
                if ap_actual is not None:
                    evaluar_cadena_ap(ap_actual, limite_ap)
                else:
                    afd = obtener_afd_operativo(automata_actual, afd_generado)
                    if asegurar_afd_valido(afd):
                        cadena = input("Ingrese la cadena (Enter representa ε): ")
                        aceptada, resultado = SimuladorAFD.evaluar(afd, cadena, True)
                        if resultado not in ("Aceptada", "Rechazada"):
                            print("Error:", resultado)

            # ----------------------------------------------------------
            # Opción 11: evaluar archivo de cadenas
            # ----------------------------------------------------------
            elif opcion == "11":
                if ap_actual is not None:
                    evaluar_archivo_cadenas_ap(ap_actual, limite_ap)
                else:
                    afd = obtener_afd_operativo(automata_actual, afd_generado)
                    evaluar_archivo_cadenas_afd(afd)

            # ----------------------------------------------------------
            # Opción 12: historial
            # ----------------------------------------------------------
            elif opcion == "12":
                if ap_actual is not None:
                    mostrar_historial_ap(ap_actual)
                else:
                    afd = obtener_afd_operativo(automata_actual, afd_generado)
                    mostrar_historial_afd(afd)

            # ----------------------------------------------------------
            # Opción 13: análisis estructural
            # ----------------------------------------------------------
            elif opcion == "13":
                if ap_actual is not None:
                    mostrar_analisis_ap(ap_actual)
                else:
                    afd = obtener_afd_operativo(automata_actual, afd_generado)
                    mostrar_analisis_afd(afd)

            # ----------------------------------------------------------
            # Opción 14: cargar o crear otro AFD/AFND
            # ----------------------------------------------------------
            elif opcion == "14":
                nuevo = crear_o_cargar_afxnd()
                if nuevo is not None:
                    afd_nuevo, nuevas_equiv = preparar_nuevo_automata_afxnd(nuevo)
                    if isinstance(nuevo, AFND) and afd_nuevo is None:
                        continue
                    automata_actual = nuevo
                    afd_generado = afd_nuevo
                    equivalencias = nuevas_equiv
                    definicion_convertida = (
                        _copiar_definicion(nuevo) if afd_generado is not None else None
                    )
                    # Limpiar AP activo: sesión AFD/AFND toma el control
                    ap_actual = None
                    print("\nNuevo autómata AFD/AFND cargado; sesión anterior limpiada.")

            # ----------------------------------------------------------
            # Opción 15: salir
            # ----------------------------------------------------------
            elif opcion == "15":
                print("\nPrograma finalizado.")
                break

            # ----------------------------------------------------------
            # Opción 16: crear AP manualmente
            # ----------------------------------------------------------
            elif opcion == "16":
                nuevo_ap = CargadorAP.crear_manual()
                if nuevo_ap is not None:
                    ap_actual = nuevo_ap
                    # Limpiar AFD/AFND activo: sesión AP toma el control
                    automata_actual = None
                    afd_generado = None
                    equivalencias = {}
                    definicion_convertida = None
                    print("\nAP ({}) cargado como autómata activo de pila.".format(ap_actual.tipo))

            # ----------------------------------------------------------
            # Opción 17: cargar AP desde archivo
            # ----------------------------------------------------------
            elif opcion == "17":
                ruta = input("Ruta del archivo AP (.txt): ").strip()
                nuevo_ap = CargadorAP.cargar_archivo(ruta)
                if nuevo_ap is not None:
                    ap_actual = nuevo_ap
                    # Limpiar AFD/AFND activo: sesión AP toma el control
                    automata_actual = None
                    afd_generado = None
                    equivalencias = {}
                    definicion_convertida = None
                    print("\nAP ({}) cargado como autómata activo de pila.".format(ap_actual.tipo))

            # ----------------------------------------------------------
            # Opción 18: ajustar límite de exploración AP
            # ----------------------------------------------------------
            elif opcion == "18":
                limite_ap = ajustar_limite_ap(limite_ap)

            else:
                print("\nError: ingrese un número del 1 al 18.")

        except EOFError:
            print("\nFin de entrada. Programa finalizado.")
            break
        except KeyboardInterrupt:
            print("\nOperación cancelada. Regresamos al menú.")


if __name__ == "__main__":
    main()
