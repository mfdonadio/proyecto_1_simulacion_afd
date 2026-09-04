import re  # Módulo para validar patrones de entrada usando expresiones regulares
import AFD  # Importamos la clase AFD desde el archivo AFD.py
import ValidadorAFD  # Importamos la clase ValidadorAFD para validar la estructura del AFD
import SimuladorAFD  # Importamos la clase SimuladorAFD para evaluar cadenas con el AFD
import CargadorAFD  # Importamos la clase CargadorAFD para crear o cargar AFD desde archivos



# ==================== FUNCIONES DEL MENÚ PRINCIPAL ====================
# Estas funciones manejan la interfaz del usuario y el flujo del programa

def mostrar_validacion(afd):
    """
    Valida un AFD y muestra un reporte completo de su estructura.
    Si el AFD es válido, también analiza su accesibilidad.
    """
    valido, errores = ValidadorAFD.validar(afd)
    
    print("\n--- VALIDACIÓN DEL AFD ---")
    
    if valido:
        # ========== AFD VÁLIDO ==========
        print("Estado: VÁLIDO")
        print("El autómata cumple con todas las validaciones estructurales del AFD.")
        
        # Realizar análisis de accesibilidad
        analisis = ValidadorAFD.analizar_estructura(afd)
        print("\nAnálisis de accesibilidad:")
        print("  Estados alcanzables:", analisis["alcanzables"])
        print("  Estados inaccesibles (código muerto):", analisis["inaccesibles"])
        print("  Estados finales alcanzables:", analisis["finales_alcanzables"])
        
        # Verificar si el lenguaje es vacío
        if analisis["lenguaje_posiblemente_vacio"]:
            print("\n⚠️  ADVERTENCIA: El lenguaje reconocido podría ser vacío.")
            print("   (No hay estados finales alcanzables desde q0)")
        else:
            print("\n✅ El autómata puede aceptar al menos una cadena.")
    else:
          # ========== AFD INVÁLIDO ==========
        print("Estado: INVÁLIDO")
        print(
            "El autómata NO cumple con las validaciones. "
            "Errores encontrados:"
        )

        for error in errores:
            print("-", error)

        # Verificar si el único problema es la falta de transiciones
        faltantes = ValidadorAFD.obtener_transiciones_faltantes(afd)

        if len(faltantes) > 0 and len(errores) == len(faltantes):
            print(
                "\nEl AFD es estructuralmente consistente, "
                "pero su función de transición está incompleta."
            )
            print(
                "Puede completarse automáticamente mediante "
                "un estado trampa."
            )

            while True:
                respuesta = input(
                    "¿Desea completar el AFD con un estado trampa? (s/n): "
                ).strip().lower()

                if respuesta in ("s", "si", "sí"):
                    nombre_trampa, cantidad = (
                        ValidadorAFD.completar_con_estado_trampa(afd)
                    )

                    print(
                        "\nSe agregó el estado trampa:",
                        nombre_trampa
                    )
                    print(
                        "Transiciones faltantes completadas:",
                        cantidad
                    )

                    # Mostrar nuevamente la validación actualizada
                    mostrar_validacion(afd)
                    return

                if respuesta in ("n", "no"):
                    print(
                        "El AFD permanecerá incompleto y no podrá "
                        "evaluar cadenas."
                    )
                    break

                print("Error: responda únicamente s o n.")


def asegurar_afd_valido(afd):
    """
    Valida que exista un AFD válido antes de realizar operaciones.
    Retorna True si el AFD es válido, False si no o no existe.
    """
    # ========== VERIFICAR QUE EXISTE AFD ==========
    if afd is None:
        print("\nError: Primero debe crear o cargar un autómata.")
        return False
    
    # ========== VALIDAR AFD ==========
    valido, errores = ValidadorAFD.validar(afd)
    
    if not valido:
        print("\nError: El autómata no puede procesarse porque no es válido.")
        print("Errores encontrados:")
        for error in errores:
            print("-", error)
        return False
    
    return True


def evaluar_archivo_cadenas(afd):
    """
    Evalúa múltiples cadenas de un archivo de forma masiva.
    Cada línea del archivo es una cadena a procesar.
    
    Formato del archivo:
        Línea 1: primera cadena
        Línea 2: segunda cadena
        ...
    """
    # ========== VALIDAR AFD ==========
    if not asegurar_afd_valido(afd):
        return
    
    # ========== SOLICITAR RUTA ==========
    ruta = input("\nRuta del archivo de cadenas: ").strip()
    
    # ========== LEER ARCHIVO ==========
    try:
        archivo = open(ruta, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()
    except Exception as error:
        print("Error: No fue posible abrir el archivo:", error)
        return
    
    # ========== PROCESAR CADENAS ==========
    print("\n=== EVALUACIÓN POR LOTE ===")
    print(f"Procesando {len(lineas)} cadena(s)...\n")
    
    # Procesar cada línea como una cadena
    for numero, linea in enumerate(lineas, start=1):
        cadena = linea.strip()
        print(f"\nCadena {numero}: {repr(cadena)}")
        
        # Evaluar la cadena
        aceptada, resultado = SimuladorAFD.evaluar(
            afd, cadena, mostrar_traza=True
        )
        
        # Si resultado contiene un mensaje de error (símbolo inválido), mostrarlo
        if isinstance(resultado, str) and resultado not in ("Aceptada", "Rechazada"):
            print("Error:", resultado)


def mostrar_historial(afd):
    """
    Muestra el historial de todas las cadenas evaluadas durante la sesión.
    """
    # ========== VALIDAR QUE EXISTA AFD ==========
    if afd is None:
        print("\nError: Primero debe crear o cargar un autómata.")
        return
    
    # ========== VERIFICAR SI HAY HISTORIAL ==========
    if len(afd.historial) == 0:
        print("\nNo hay evaluaciones registradas en el historial.")
        return
    
    # ========== MOSTRAR HISTORIAL ==========
    print("\n--- HISTORIAL DE EVALUACIONES ---")
    print(f"Total de evaluaciones: {len(afd.historial)}\n")
    
    # Mostrar cada evaluación registrada
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


def crear_o_cargar_otro():
    """
    Menú para crear o cargar un nuevo AFD en memoria.
    Reemplaza el AFD actual.
    """
    print("\n--- CREAR O CARGAR AFD ---")
    print("1. Crear manualmente")
    print("2. Cargar desde archivo .txt")
    opcion = input("Seleccione una opción (1-2): ").strip()
    
    if opcion == "1":
        # Crear AFD manualmente
        return CargadorAFD.crear_manual()
    
    if opcion == "2":
        # Cargar AFD desde archivo
        ruta = input("Ruta del archivo .txt: ").strip()
        return CargadorAFD.cargar_archivo(ruta)
    
    print("Error: Opción inválida.")
    return None


def mostrar_menu():
    """
    Muestra el menú principal del programa con todas las opciones disponibles.
    """
    print("\n" + "=" * 60)
    print(" SIMULADOR DE AUTÓMATA FINITO DETERMINISTA (AFD)".center(60))
    print("=" * 60)
    print("\nOpciones disponibles:")
    print("\n  Gestión del AFD:")
    print("    1. Crear un AFD manualmente")
    print("    2. Cargar un AFD desde un archivo .txt")
    print("    9. Cargar o crear otro autómata (reemplazar el actual)")
    print("\n  Visualización:")
    print("    3. Mostrar la definición formal del AFD (Q, Σ, q0, F, δ)")
    print("    4. Mostrar la tabla de transiciones")
    print("\n  Validación:")
    print("    5. Validar la estructura del autómata")
    print("\n  Evaluación:")
    print("    6. Evaluar una cadena individual")
    print("    7. Evaluar múltiples cadenas desde un archivo")
    print("\n  Historial:")
    print("    8. Consultar el historial de evaluaciones")
    print("\n  Salida:")
    print("   10. Salir del programa")
    print()


def main():
    """
    Función principal: menú interactivo que gestiona el programa.
    Permite crear/cargar AFD, validarlos, y evaluar cadenas.
    """
    afd_actual = None  # Almacena el AFD en memoria durante la sesión
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   BIENVENIDO AL SIMULADOR DE AFD                         ║
    ║   Lenguajes Formales - Proyecto 1                        ║
    ║    Desarrollado por: Gerber Perez y Marco Donadio        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    while True:
        # ========== MOSTRAR MENÚ ==========
        mostrar_menu()
        opcion = input("Seleccione una opción (1-10): ").strip()
        
        # ========== OPCIÓN 1: CREAR MANUALMENTE ==========
        if opcion == "1":
            afd_actual = CargadorAFD.crear_manual()
            print("\n✅ AFD creado correctamente.")
        
        # ========== OPCIÓN 2: CARGAR DESDE ARCHIVO ==========
        elif opcion == "2":
            ruta = input("\nRuta del archivo .txt: ").strip()
            nuevo_afd = CargadorAFD.cargar_archivo(ruta)
            
            if nuevo_afd is not None:
                afd_actual = nuevo_afd
                print("\n✅ AFD cargado correctamente.")
        
        # ========== OPCIÓN 3: MOSTRAR DEFINICIÓN FORMAL ==========
        elif opcion == "3":
            if afd_actual is None:
                print("\nError: Primero debe crear o cargar un autómata.")
            else:
                afd_actual.mostrar_definicion_formal()
        
        # ========== OPCIÓN 4: MOSTRAR TABLA DE TRANSICIONES ==========
        elif opcion == "4":
            if afd_actual is None:
                print("\nError: Primero debe crear o cargar un autómata.")
            else:
                afd_actual.mostrar_tabla_transicion()
        
        # ========== OPCIÓN 5: VALIDAR ESTRUCTURA ==========
        elif opcion == "5":
            if afd_actual is None:
                print("\nError: Primero debe crear o cargar un autómata.")
            else:
                mostrar_validacion(afd_actual)
        
        # ========== OPCIÓN 6: EVALUAR UNA CADENA ==========
        elif opcion == "6":
            if asegurar_afd_valido(afd_actual):
                cadena = input("\nIngrese la cadena a evaluar: ")
                aceptada, resultado = SimuladorAFD.evaluar(
                    afd_actual, cadena, mostrar_traza=True
                )
                
                # Si resultado no es "Aceptada" ni "Rechazada", es un error
                if resultado not in ("Aceptada", "Rechazada"):
                    print("\nError:", resultado)
        
        # ========== OPCIÓN 7: EVALUAR ARCHIVO DE CADENAS ==========
        elif opcion == "7":
            evaluar_archivo_cadenas(afd_actual)
        
        # ========== OPCIÓN 8: MOSTRAR HISTORIAL ==========
        elif opcion == "8":
            mostrar_historial(afd_actual)
        
        # ========== OPCIÓN 9: CARGAR OTRO AFD ==========
        elif opcion == "9":
            nuevo_afd = crear_o_cargar_otro()
            
            if nuevo_afd is not None:
                afd_actual = nuevo_afd
                print("\n✅ Nuevo autómata cargado en memoria (reemplazó al anterior).")
        
        # ========== OPCIÓN 10: SALIR ==========
        elif opcion == "10":
            print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   Gracias por usar el Simulador de AFD.                  ║
    ║   Programa finalizado.                                   ║
    ╚══════════════════════════════════════════════════════════╝
            """)
            break
        
        # ========== OPCIÓN INVÁLIDA ==========
        else:
            print("\nError: Opción inválida. Ingrese un número del 1 al 10.")


# ========== PUNTO DE ENTRADA DEL PROGRAMA ==========
# Este bloque asegura que main() solo se ejecute cuando se corre el script directamente,
# no cuando se importa como módulo en otro archivo
if __name__ == "__main__":
    main()