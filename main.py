"""Menú principal del motor de validación y conversión de AFD y AFND."""

# Importamos las clases que representan los dos tipos de autómatas
from AFD import AFD
from AFND import AFND

# Importamos los cargadores para crear autómatas manualmente o desde archivos
from CargadorAFD import CargadorAFD
from CargadorAFND import CargadorAFND

# Importamos la clase encargada de transformar un AFND en un AFD
from ConvertidorAFND import ConvertidorAFND

# Importamos el simulador y los validadores de cada tipo de autómata
from SimuladorAFD import SimuladorAFD
from ValidadorAFD import ValidadorAFD
from ValidadorAFND import ValidadorAFND


def mostrar_menu():
    """Muestra las quince opciones solicitadas en el enunciado."""

    # Creamos el encabezado principal del programa
    print("\n" + "=" * 68)
    print("MOTOR DE VALIDACIÓN Y CONVERSIÓN DE AUTÓMATAS".center(68))
    print("elaborado por: Gerber Perez y Marco Donadio".center(68))
    print("=" * 68)

    # Mostramos todas las opciones disponibles para el usuario
    print(" 1. Crear un AFD manualmente")
    print(" 2. Cargar un AFD desde un archivo .txt")
    print(" 3. Crear un AFND manualmente")
    print(" 4. Cargar un AFND desde un archivo .txt")
    print(" 5. Mostrar la definición formal y la tabla del autómata cargado")
    print(" 6. Validar la estructura del autómata")
    print(" 7. Convertir el AFND cargado en un AFD equivalente")
    print(" 8. Mostrar la tabla de equivalencias de macroestados")
    print(" 9. Mostrar la tabla de transición del AFD generado")
    print("10. Evaluar una cadena")
    print("11. Evaluar un archivo de cadenas")
    print("12. Consultar el historial de evaluaciones")
    print("13. Realizar el análisis estructural")
    print("14. Cargar o crear otro autómata")
    print("15. Salir")


def mostrar_validacion(automata):
    """Valida el tipo de autómata activo y muestra un reporte comprensible."""

    # Antes de validar, comprobamos que exista un autómata cargado
    if automata is None:
        print("\nError: primero debe crear o cargar un autómata.")
        return

    # Si el objeto es un AFND, utilizamos su validador correspondiente
    if isinstance(automata, AFND):
        valido, errores = ValidadorAFND.validar(automata)
        print("\n--- VALIDACIÓN DEL AFND ---")
        print("Clasificación:", "AFND VÁLIDO" if valido else "AFND INVÁLIDO")
        _mostrar_lista_errores(errores)
        return

    # Si no es un AFND, trabajamos con las validaciones propias de un AFD
    valido, errores = ValidadorAFD.validar(automata)
    clasificacion = ValidadorAFD.clasificar(automata)
    print("\n--- VALIDACIÓN DEL AFD ---")
    print("Clasificación:", clasificacion)

    # Si no hay errores, el AFD puede utilizarse para evaluar cadenas
    if valido:
        print("El AFD es determinista, completo y estructuralmente válido.")
        return

    # Si la validación falla, mostramos todos los errores encontrados
    _mostrar_lista_errores(errores)

    # Solo se ofrece completar cuando la incompletitud es el único problema.
    if clasificacion == "AFD INCOMPLETO":
        respuesta = input(
            "¿Desea completarlo con un estado de trampa? (s/n): "
        ).strip().lower()

        # Si el usuario acepta, completamos las transiciones faltantes
        if respuesta in ("s", "si", "sí"):
            nombre, cantidad = ValidadorAFD.completar_con_estado_trampa(automata)
            ValidadorAFD.validar(automata)
            print("Estado de trampa agregado:", nombre)
            print("Transiciones completadas:", cantidad)
            print("Nueva clasificación:", ValidadorAFD.clasificar(automata))


def obtener_afd_operativo(automata, afd_generado):
    """Selecciona el AFD directo o el resultado de una conversión."""

    # Si se cargó directamente un AFD, ese será el autómata utilizado
    if isinstance(automata, AFD):
        return automata

    # Si se cargó un AFND, necesitamos utilizar su AFD equivalente
    if isinstance(automata, AFND):

        # No permitimos evaluar el AFND si todavía no fue convertido
        if afd_generado is None:
            print("\nError: convierta el AFND antes de usar esta función.")
            return None
        return afd_generado

    print("\nError: primero debe crear o cargar un autómata.")
    return None


def asegurar_afd_valido(afd):
    """Impide simulaciones sobre un AFD inválido, incompleto o no determinista."""

    # Si no recibimos ningún AFD, no se puede continuar con la operación
    if afd is None:
        return False

    # Ejecutamos nuevamente la validación para trabajar con datos actualizados
    valido, errores = ValidadorAFD.validar(afd)

    # Si cumple todas las reglas, indicamos que puede ser utilizado
    if valido:
        return True

    # Mostramos por qué el AFD no puede procesar cadenas
    print("\nError: el AFD no está listo para procesar cadenas.")
    print("Clasificación:", ValidadorAFD.clasificar(afd))
    _mostrar_lista_errores(errores)
    return False


def evaluar_archivo_cadenas(afd):
    """Evalúa cada línea de un archivo, incluida una línea que represente ε."""

    # Antes de leer el archivo, comprobamos que el AFD sea válido
    if not asegurar_afd_valido(afd):
        return

    # Solicitamos la ubicación del archivo que contiene las cadenas
    ruta = input("Ruta del archivo de cadenas: ").strip()

    # Intentamos abrir y leer todas las líneas del archivo
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            lineas = archivo.readlines()
    except (OSError, UnicodeError) as error:
        print("Error: no fue posible abrir el archivo:", error)
        return

    print("\n--- EVALUACIÓN POR LOTES ---")

    # Cada línea del archivo representa una cadena independiente
    for numero, linea in enumerate(lineas, start=1):

        # Quitamos únicamente el salto de línea para conservar la cadena original
        cadena = linea.rstrip("\r\n")
        print("\nCadena", str(numero) + ":", repr(cadena))
        # Enviamos la cadena al simulador y solicitamos su traza completa
        aceptada, resultado = SimuladorAFD.evaluar(afd, cadena, True)

        # Si el simulador devuelve un mensaje diferente, ocurrió un error
        if resultado not in ("Aceptada", "Rechazada"):
            print("Error:", resultado)


def mostrar_historial(afd):
    """Muestra las evaluaciones del AFD activo en orden cronológico."""

    # Sin un AFD activo no existe un historial que consultar
    if afd is None:
        return

    # Avisamos cuando todavía no se ha evaluado ninguna cadena
    if not afd.historial:
        print("\nNo hay evaluaciones registradas.")
        return

    print("\n--- HISTORIAL DE EVALUACIONES ---")
    # Recorremos los registros y los numeramos desde uno
    for indice, registro in enumerate(afd.historial, start=1):
        print(
            str(indice)
            + ". Cadena: "
            + repr(registro["cadena"])
            + " | Estado final: "
            + registro["estado_final"]
            + " | Resultado: "
            + registro["resultado"]
        )


def mostrar_analisis(afd):
    """Presenta accesibilidad, estados inútiles y posible lenguaje vacío."""

    # El análisis solamente puede realizarse sobre un AFD válido
    if not asegurar_afd_valido(afd):
        return

    # Obtenemos los conjuntos calculados por el validador
    analisis = ValidadorAFD.analizar_estructura(afd)
    print("\n--- ANÁLISIS ESTRUCTURAL ---")
    print("Estados alcanzables:", _formatear_conjunto(analisis["alcanzables"]))
    print("Estados inaccesibles:", _formatear_conjunto(analisis["inaccesibles"]))
    print(
        "Estados finales alcanzables:",
        _formatear_conjunto(analisis["finales_alcanzables"]),
    )
    # Si ningún estado final es alcanzable, ninguna cadena puede aceptarse
    if analisis["lenguaje_posiblemente_vacio"]:
        print("El lenguaje es vacío: no existe un estado final alcanzable.")
    else:
        print("El lenguaje no es vacío: existe al menos un estado final alcanzable.")


def crear_o_cargar(opcion=None):
    """Centraliza las cuatro formas de ingresar un autómata."""

    # Si no recibimos una opción, mostramos un pequeño menú de carga
    if opcion is None:
        print("\n1. Crear AFD manualmente")
        print("2. Cargar AFD desde archivo")
        print("3. Crear AFND manualmente")
        print("4. Cargar AFND desde archivo")
        opcion = input("Seleccione una opción (1-4): ").strip()

    # Creamos manualmente un AFD
    if opcion == "1":
        return CargadorAFD.crear_manual()

    # Cargamos la definición de un AFD desde un archivo
    if opcion == "2":
        ruta = input("Ruta del archivo AFD: ").strip()
        return CargadorAFD.cargar_archivo(ruta)
    # Creamos manualmente un AFND
    if opcion == "3":
        return CargadorAFND.crear_manual()

    # Cargamos la definición de un AFND desde un archivo
    if opcion == "4":
        ruta = input("Ruta del archivo AFND: ").strip()
        return CargadorAFND.cargar_archivo(ruta)

    print("Error: opción inválida.")
    return None


def preparar_nuevo_automata(automata):
    """Valida un AFND, muestra su tabla y ejecuta la conversión automática."""

    # Un AFD cargado directamente no necesita ninguna conversión
    if not isinstance(automata, AFND):
        return None, {}

    # Validamos el AFND antes de intentar convertirlo
    valido, errores = ValidadorAFND.validar(automata)
    if not valido:
        print("\nEl AFND fue cargado, pero contiene errores:")
        _mostrar_lista_errores(errores)
        return None, {}

    # Mostramos la tabla del AFND válido antes de realizar la conversión
    automata.mostrar_tabla_transicion()

    # Aplicamos el algoritmo de construcción de subconjuntos
    afd, equivalencias, errores = ConvertidorAFND.convertir(automata)
    if errores:
        print("\nNo fue posible realizar la conversión automática:")
        _mostrar_lista_errores(errores)
        return None, {}

    # Informamos cuántos macroestados fueron creados en el AFD equivalente
    print("Conversión automática completada. Macroestados:", len(equivalencias))
    return afd, equivalencias


def _mostrar_lista_errores(errores):
    """Muestra errores o confirma que no se encontró ninguno."""

    # Una lista vacía significa que la estructura pasó la validación
    if not errores:
        print("No se encontraron errores estructurales.")
        return
    # Imprimimos cada error por separado para facilitar su lectura
    for error in errores:
        print("-", error)


def _formatear_conjunto(elementos):
    """Da una salida estable para los resultados del análisis."""

    # Representamos un conjunto sin elementos mediante el símbolo vacío
    if not elementos:
        return "∅"

    # Ordenamos los elementos y los mostramos separados por comas
    return "{" + ", ".join(sorted(elementos)) + "}"


def main():
    """Mantiene el autómata original y, cuando aplica, su AFD equivalente."""

    # Guarda el AFD o AFND que el usuario cargó originalmente
    automata_actual = None

    # Guarda el resultado de convertir un AFND en un AFD
    afd_generado = None

    # Relaciona cada macroestado del AFD con un subconjunto del AFND
    equivalencias = {}

    print("\nBienvenido al motor de AFD y AFND - Proyecto 2")

    # El menú se repite hasta que el usuario seleccione la opción de salir
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción (1-15): ").strip()

        # Opciones 1 a 4: crear o cargar un nuevo autómata
        if opcion in ("1", "2", "3", "4"):
            nuevo = crear_o_cargar(opcion)

            # Solo reemplazamos los datos actuales si la carga fue correcta
            if nuevo is not None:
                automata_actual = nuevo
                afd_generado, equivalencias = preparar_nuevo_automata(nuevo)
                print("\nAutómata cargado. Los datos anteriores fueron limpiados.")

        # Opción 5: mostrar el autómata cargado originalmente
        elif opcion == "5":
            if automata_actual is None:
                print("\nError: primero debe crear o cargar un autómata.")
            else:
                automata_actual.mostrar_definicion_formal()
                automata_actual.mostrar_tabla_transicion()

        # Opción 6: validar según sea AFD o AFND
        elif opcion == "6":
            mostrar_validacion(automata_actual)

        # Opción 7: volver a convertir el AFND cargado
        elif opcion == "7":
            if not isinstance(automata_actual, AFND):
                print("\nError: debe existir un AFND cargado para convertirlo.")
            else:
                # Ejecutamos la conversión sin perder el AFND original
                afd_nuevo, nuevas_equivalencias, errores = ConvertidorAFND.convertir(
                    automata_actual
                )
                if errores:
                    print("\nNo fue posible convertir el AFND:")
                    _mostrar_lista_errores(errores)
                else:
                    afd_generado = afd_nuevo
                    equivalencias = nuevas_equivalencias
                    print("\nAFND convertido correctamente en un AFD equivalente.")
                    print("Macroestados generados:", len(equivalencias))

        # Opción 8: mostrar qué subconjunto representa cada macroestado
        elif opcion == "8":
            ConvertidorAFND.mostrar_equivalencias(equivalencias)

        # Opción 9: mostrar únicamente la tabla del AFD equivalente
        elif opcion == "9":
            if afd_generado is None:
                print("\nError: todavía no existe un AFD generado; convierta un AFND primero.")
                continue
            print("\n--- TABLA DE TRANSICIONES DEL AFD GENERADO ---")
            afd_generado.mostrar_tabla_transicion()

        # Opción 10: evaluar una cadena individual y mostrar su traza
        elif opcion == "10":
            afd = obtener_afd_operativo(automata_actual, afd_generado)
            if asegurar_afd_valido(afd):
                cadena = input("Ingrese la cadena (Enter representa ε): ")
                aceptada, resultado = SimuladorAFD.evaluar(afd, cadena, True)
                if resultado not in ("Aceptada", "Rechazada"):
                    print("Error:", resultado)

        # Opción 11: evaluar todas las cadenas contenidas en un archivo
        elif opcion == "11":
            afd = obtener_afd_operativo(automata_actual, afd_generado)
            evaluar_archivo_cadenas(afd)

        # Opción 12: consultar los resultados acumulados durante la sesión
        elif opcion == "12":
            afd = obtener_afd_operativo(automata_actual, afd_generado)
            mostrar_historial(afd)

        # Opción 13: calcular estados alcanzables, inaccesibles y finales útiles
        elif opcion == "13":
            afd = obtener_afd_operativo(automata_actual, afd_generado)
            mostrar_analisis(afd)

        # Opción 14: reemplazar el autómata y limpiar los datos anteriores
        elif opcion == "14":
            nuevo = crear_o_cargar()
            if nuevo is not None:
                automata_actual = nuevo
                afd_generado, equivalencias = preparar_nuevo_automata(nuevo)
                print("\nNuevo autómata cargado; sesión anterior limpiada.")

        # Opción 15: finalizar el ciclo principal del programa
        elif opcion == "15":
            print("\nPrograma finalizado.")
            break

        else:
            print("\nError: ingrese un número del 1 al 15.")
            
if __name__ == "__main__":
    main()
