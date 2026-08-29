"""Clase AFD que representa formalmente un Autómata Finito Determinista."""
class AFD:
    #Constructor de la clase AFD
    def __init__(afd, nombre=""):
        #Asignamos el nombre del AFD"""
        afd.nombre = nombre
        #Seteamos los estados del AFD
        afd.estados = set()
        #Seteamos el alfabeto del AFD
        afd.alfabeto = set()
        #Inicializamos el estado inicial del AFD
        afd.estado_inicial = ""
        #Seteamos los estados finales del AFD
        afd.estados_finales = set()
        #Por ultimmo, incializamos el conjunto de transiciones del AFD
        afd.transiciones = {}

        #Si durante una carga de AFD, se detecta la misma pareja de estado y simbolo (estado, simblo)
        # mas de una vez, se guarda en la siguiente variable para no perder esa informacion
        afd.transiciones_repetidas = set()

        #Suponiendo que un AFD ya pudo haber pasado por el motor de validacion.
        #Inicializamos un booleano que nos indique si este, en efecto, ya fue validado o no.
        afd.validado = False

        #Y para el historial propia del automata que estamos evaluando...
        afd.historial = []

        def agregar_transicion(afd, estado_origen, simbolo, estado_destino):
            """
            Esta funcion agrega una transicion al diccionario de transiciones del AFD.
            La llave del diccionario es la tupla del AFD (estado, simbolo) y el valor es el estado destino.
            """

            #Definimos la clave
            clave = (estado_origen, simbolo)

            #Verificamos si la clave ya existe en el diccionario de transiciones
            if clave in afd.transiciones:
                #Si ya existe, la agregamos a las transiciones repetidas
                afd.transiciones_repetidas.append((estado_origen, simbolo, estado_destino))
                #Retornamos False para indicar que no se pudo agregar la transicion
                return False

            #Si no existe, agregamos la transicion al diccionario de transiciones
            afd.transiciones[clave] = estado_destino
            #Retornamos True para indicar que se agrego la transicion correctamente
            return True

        """Funcion que muestra la definicion formal del AFD (es decir, su quintupla)"""
        def mostrar_definicion_formal(afd):
            print("\n--- DEFINICION FORMAL DEL AFD ---")
            print("Nombre: " , afd.nombre)
            print("Q =", afd.estados)
            print("Σ =", afd.alfabeto)
            print("q0 =", afd.estado_inicial)
            print("F =", afd.estados_finales)
            print("δ =")

            #Para las transiciones, vamos a recorrer el diccionario de transiciones y mostrar cada una de ellas (iterando con un for jeje)
            for clave, destino in afd.transiciones.items():
                estado_origen, simbolo = clave
                print("  δ(" + estado_origen + ", " + simbolo + ") = " + destino)

        """Funcion para mostrar la tabla de transiciones del AFD (en formato de tabla)"""
        def mostrar_tabla_transiciones(afd):
            #Si no existen estados o alfabeto defnidos, no podemos mostrar la tabla de transiciones
            if not afd.estados or not afd.alfabeto:
                print("\nNo hay datos suficientes para mostrar la tabla de transicion.")
                return
            
            #En caso de que si existan estados y alfabeto, vamos a mostrar la tabla de transiciones
            #Primero ordenamos los estados y el alfabeto para que la tabla se vea tuanis
            estados_ordenados = sorted(afd.estados)
            alfabeto_ordenado = sorted(afd.alfabeto)

            #Definimos el ancho de la tabla
            ancho = 15
            #Tambien definimos el encabezado, lo ajustamos a la izquierda y le damos un ancho de 15 caracteres
            encabezado = "Estado".ljust(ancho)

            #Por cada simbolo del alfabeto, vamos a agregarlo al encabezado de la tabla con la misma logica de ajuste a la izquierda y ancho de 15 caracteres
            for simbolo in alfabeto_ordenado:
                encabezado += simbolo.ljust(ancho)

            #Imprimimos el encabezado de la tabla
            print("\n--- TABLA DE TRANSICIONES DEL AFD ---")
            print(encabezado)
            print("-" * len(encabezado))

            #Vamos llenando las filas de la tabla con los estados y sus transiciones
            for estado in estados_ordenados:
                fila = estado.ljust(ancho)

                for simbolo in alfabeto_ordenado:
                    destino = afd.transiciones.get((estado, simbolo), "---")
                    fila += destino.ljust(ancho)

                print(fila)

class ValidadorAFD:
    """Clase que se encarga de validar un AFD y su funcionamiento."""
    @staticmethod

    #Creamos una funcion que nos permita validar un AFD y nos devuelva una lista de errores encontrados en el mismo
    def validar(afd):
        errores = []

        #Validaciones basicas de los atributos del AFD
        if afd.nombre.strip() == "":
            errores.append("El automata no tiene un nombre definido o un identificador.")

        if len(afd.estados) == 0:
            errores.append("El conjunto de estados Q no puede estar vacío.")

        if len(afd.alfabeto) == 0:
            errores.append("el alfabeto Σ no puede estar vacío.")

        #q0 y F deben ser parte de Q, por lo que vamos a validar que el estado inicial y los estados finales esten dentro del conjunto de estados
        if afd.estado_inicial not in afd.estados:
            errores.append("El estado inicial q0 no pertenece al conjunto de estados Q.")

        #Ahora para F
        for estado_final in afd.estados_finales:
            if estado_final not in afd.estados:
                errores.append(
                    "El estado final " + estado_final + " no pertenece al conjunto Q."
                )

        #Ademas, toda transicion debe usar estados de Q y simbolos de Σ, por lo que vamos a validar que todas las transiciones cumplan con esto
        for clave, estado_destino in afd.transiciones.items():
            estado_origen, simbolo = clave

            if estado_origen not in afd.estados:
                errores.append(
                    "La transición usa el estado origen inexistente " + estado_origen + "'."
                )

            if simbolo not in afd.alfabeto:
                errores.append(
                    "La transición usa el símbolo inexistente " + simbolo + "'."
                )

            if estado_destino not in afd.estados:
                errores.append(
                    "La transición apunta al estado destino inexistente " + estado_destino + "."
                )

        #Si una pareja (estado_origen, simbolo) aparecio mas de una vez, quiere decir que este automata no es eterminista
        for repetida in afd.transiciones_repetidas:
            estado_origen, simbolo, estado_destino = repetida
            errores.append(
                "Existe más de una transición para ("
                + estado_origen
                + ", "
                + simbolo
                + "). Se detectó también destino '"
                + estado_destino
                + "'."
            )

        #Por ultimo, sabemos que en un AFD completo debe existir exactamente una transicion
        # para cada combinacion de (estado_origen, simbolo).
        for estado_origen in afd.estados:
            for simbolo in afd.alfabeto:
                if (estado_origen, simbolo) not in afd.transiciones:
                    errores.append(
                         "Falta la transición δ("
                        + estado_origen
                        + ", "
                        + simbolo
                        + ")."
                    )
        #Booleano que nos indica si, en efecto, el AFD es valido o no.
        #Si la lista de errores esta vacia, es valido, si no, pues no.
        afd.es_valido = len(errores) == 0
        #Retornamos el booleano y la lista de errores
        return afd.es_valido, errores

    @staticmethod
    def analizar_estructura(afd):
        """
        Esta funcion analiza las estrcutura del AFD para calcular:
            1. Los estados alcanzables
            2. Los estados inalcanzables
            3. Los estados inaccesibles
            4. Los estados finales alcanzables
            5. Por ultimo, la posibilidad de lenguaje vacio (que el afd acepte cadenas vacias, epselon).
        """

        #Creamos un set para almacenar los estados alcanzables
        estados_alcanzables = set()
        #Inicializamos una variable "pendientes" con el estado inicial del AFD
        pendientes = [afd.estado_inicial]

        #Para recorrer los estados pendientes, utilizamos un recorrido tipo DFS haciendo uso de una lista commo pila.
        while len(pendientes) > 0:
            estado_actual = pendientes.pop()

            if estado_actual in estados_alcanzables: continue

            #Agregamos el estado actual a los estados alcanzables
            estados_alcanzables.add(estado_actual)

            #Ahora hacemos un for para recorrer el alfabeto y buscar los estados alcanzables desde el estado actual
            for simbolo in afd.alfabeto:
                #Para obtener el estado siguiente, hacemos uso del diccionario de transiciones del AFD, utilizando la tupla (estado_actual, simbolo) como clave.
                siguiente = afd.transiciones.get((estado_actual, simbolo))

                #Si el estado siguiente no es None (null) y el siguiente no esta en los estados inalcanzables...
                #agregamos el siguiente estado a la lista de pendientes
                if siguiente is not None and siguiente not in estados_alcanzables:
                    pendientes.append(siguiente)

        inaccesibles = afd.estados - estados_alcanzables
        finales_alcanzables = afd.estados_finales.intersection(estados_alcanzables)
        lenguaje_posiblemente_vacio = len(finales_alcanzables) == 0

        return{
            "alcanzables": estados_alcanzables,
            "inaccesibles": inaccesibles,
            "finales_alcanzables": finales_alcanzables,
            "lenguaje_posiblemente_vacio": lenguaje_posiblemente_vacio,
        }
    
class SimuladorAFD:
    """
    Evalua el automata (generacion completa de la traza y del comportamiento)
    """

    @staticmethod
    def evaluar(afd, cadena, mostrar_traza=True):
        if not afd.es_valido:
            return False, "El AFD debe validarse antes de evaluar cadenas."

        #De primero, comprobamos que todos los simbolos pertenezcan al alfabeto.
        for simbolo in cadena:
            if simbolo not in afd.alfabeto:
                return False,(
                    "La cadena contiene el simbolo "
                    + simbolo
                    + " , que no pertenece al alfabeto."
                )

            #Ahora definimos el estado inicial
            estado_actual = afd.estado_inicial
            #Y comenzamos con la traza... :D
            if mostrar_traza:
                print("\n--- TRAZA DE EJECUCION ---")
                print("Estado inicial: ", estado_actual)

                #Por cada simbolo... mostramos su traza
                for simbolo in cadena:
                    siguiente_estado = afd.transiciones[(estado_actual, simbolo)]

                    if mostrar_traza:
                        print(
                            estado_actual
                            + " ---"
                            + simbolo 
                            + " -->"
                            + siguiente_estado
                        )

                    #Nos movemos de estado
                    estado_actual = siguiente_estado

                #Evaluamos si el estado esta entre el conjunto de estados finales
                aceptada = estado_actual in afd.estados_finales
                resultado = "Aceptada" if aceptada else "Rechazada"

                #Mostramos el resumen de la evaluacion
                if mostrar_traza:
                    print("Estado final: ", estado_actual)
                    print("Resultado: " + resultado)

                #Actualizamos el historial
                afd.historial.append(
                    {
                        "cadena": cadena, 
                        "estado_final": estado_actual,
                        "resultado": resultado,
                    }
                )
                #Retornamos su estado de aceptacion
                return aceptada, resultado

class CargadorAFD:
    """ Clase creada con el din de responsabiliarse de crear los AAFD manualmente o dese la carga 
    de un archivo externo.
    """

    @staticmethod
    def pedir_conjunto(mensaje, permitir_vacio=False):
        """
        Este metodo solicita elementos separados por coma y evalua duplicados.
        Devuelve un set unicamente cuando la entrada es valida.
        """

        while True:
            #Obtenemos la entrada
            entrada = input(mensaje).strip()

            #Si la entrada no contiene texto (acepta el vacio)
            if entrada == "" and permitir_vacio:
                return set()

            #Si la entrada no acepta el vacio
            if entrada == "":
                print("La entrada no puede estar vacia.")
                continue

            #Obtenemos la partes del AFD
            partes = entrada.split(",")
            #Inicializamos la lista de elementos
            elementos = []
            #Inicializamos la variable de hay_vacios como "False"
            hay_vacios = False

            #Para cada elemento contenido en partes...
            for parte in partes:
                elemento = parte.strip()

                #Si el elemento esta vacio
                if elemento == "":
                    hay_vacios = True
                    break

                #Añadimos los elementos validos a la lista
                elementos.append(elemento)

            #Si existieron vacios enla entrada
            if hay_vacios:
                print("No se permiten elementos vacios entre comas.")
                continue

            #Si la longitud de los elementos difiere 
            if len(elementos) != len(set(elementos)):
                print("No se permiten estados o símbolos duplicados.")
                continue

            return set(elementos)

        @staticmethod
        def crear_manual():
            """Esta funcion se encargara de la carga manual del AFD jeje"""
            print("\n=== CREACION MANUAL DEL AFD ===")
            afd = AFD()

            #Ingreso obligatorio del nombre del AFD
            while afd.nombre.strip == "":
                afd.nombre = input("Nombre del automata: ").strip()

                #Si el nombre se ingresa como vacio..
                if afd.nombre == "":
                    print("El nomre no puede estar vacio.")

            #Extraemos los estados
            afd.estados = CargadorAFD.pedir_conjunto(
                "Estados separados por coma (ej. q0,q1,q2): "
            )

            #Extraemos el alfabeto
            afd.alfabeto = CargadorAFD.pedir_conjunto(
                "Simbolos del alfabeto separados por coma (ej. a,b): "
            )

            while True:
                #Iniciamos con el estado inicial
                inicial = input("Estado inicial: ").strip()

                #Si el estado inial si se encuentra en los estados
                if inicial in afd.estados:
                    afd.estado_inicial = inicial

                #Si no esxiste a los estados
                print("El estado inicial depe pertenecer al conjunto de estados.")
            while True:
                #Estados finales
                finales = CargadorAFD.pedir_conjunto(
                    "Estados finales separados por coma (Enter si no hay): ",
                    permitir_vacio=True,
                )

                #Si lo estados finales son una sublista de los estados
                if finales.issubset(afd.estados):
                    afd.estados_finales = finales
                    break

                print("Todos los estados finales deben pertenecer a Q.")
            print("\nIngrese la función de transición.")
            print("Para cada combinación estado-símbolo indique el estado destino.\n")

            # Al pedir exactamente una transición para cada combinación,
            # el ingreso manual ya queda completo y determinista.
            for estado in sorted(afd.estados):
                for simbolo in sorted(afd.alfabeto):
                    while True:
                        destino = input(
                            "δ(" + estado + ", " + simbolo + ") = "
                        ).strip()

                        if destino in afd.estados:
                            afd.agregar_transicion(estado, simbolo, destino)
                            break

                        print("El estado destino debe pertenecer a Q.")

            return afd

    @staticmethod
    def cargar_archivo(ruta):
        """
        Carga el formato definido en el enunciado.
        No utiliza librerías: la sintaxis se valida mediante funciones propias.
        """
        try:
            archivo = open(ruta, "r", encoding="utf-8")
            lineas = archivo.readlines()
            archivo.close()
        except Exception as error:
            print("No fue posible abrir el archivo:", error)
            return None

        # Quitamos saltos de línea, pero conservamos líneas vacías para poder
        # reportar errores de estructura con el número correcto de línea.
        limpias = []
        for linea in lineas:
            limpias.append(linea.strip())

        if len(limpias) < 6:
            print("El archivo no contiene la estructura mínima requerida.")
            return None

        afd = AFD()
        errores = []

        # Las primeras seis secciones deben aparecer en este orden.
        encabezados = [
            "NOMBRE=",
            "ESTADOS=",
            "ALFABETO=",
            "INICIAL=",
            "FINALES=",
        ]

        for indice in range(5):
            if not limpias[indice].startswith(encabezados[indice]):
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": se esperaba '"
                    + encabezados[indice]
                    + "...'."
                )

        if len(limpias) <= 5 or limpias[5] != "TRANSICIONES:":
            errores.append("Línea 6: se esperaba exactamente 'TRANSICIONES:'.")

        if len(errores) > 0:
            print("\nSe encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None

        # Extracción de los componentes principales.
        afd.nombre = limpias[0][len("NOMBRE="):].strip()

        estados_texto = limpias[1][len("ESTADOS="):].strip()
        alfabeto_texto = limpias[2][len("ALFABETO="):].strip()
        afd.estado_inicial = limpias[3][len("INICIAL="):].strip()
        finales_texto = limpias[4][len("FINALES="):].strip()

        estados, error_estados = CargadorAFD._convertir_lista_archivo(
            estados_texto, "ESTADOS", permitir_vacio=False
        )
        alfabeto, error_alfabeto = CargadorAFD._convertir_lista_archivo(
            alfabeto_texto, "ALFABETO", permitir_vacio=False
        )
        finales, error_finales = CargadorAFD._convertir_lista_archivo(
            finales_texto, "FINALES", permitir_vacio=True
        )

        if error_estados is not None:
            errores.append(error_estados)
        if error_alfabeto is not None:
            errores.append(error_alfabeto)
        if error_finales is not None:
            errores.append(error_finales)

        if len(errores) > 0:
            print("\nSe encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None

        afd.estados = estados
        afd.alfabeto = alfabeto
        afd.estados_finales = finales

        # Cada línea después de TRANSICIONES debe tener exactamente
        # origen,símbolo,destino.
        for indice in range(6, len(limpias)):
            linea = limpias[indice]

            if linea == "":
                errores.append(
                    "Línea " + str(indice + 1) + ": no se permiten líneas vacías."
                )
                continue

            partes = linea.split(",")

            if len(partes) != 3:
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": una transición debe tener formato origen,símbolo,destino."
                )
                continue

            origen = partes[0].strip()
            simbolo = partes[1].strip()
            destino = partes[2].strip()

            if origen == "" or simbolo == "" or destino == "":
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": la transición contiene campos vacíos."
                )
                continue

            afd.agregar_transicion(origen, simbolo, destino)

        if len(errores) > 0:
            print("\nSe encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None

        return afd

    @staticmethod
    def _convertir_lista_archivo(texto, nombre_campo, permitir_vacio):
        """Convierte una línea separada por comas a set y controla duplicados."""
        if texto == "":
            if permitir_vacio:
                return set(), None
            return None, "El campo " + nombre_campo + " no puede estar vacío."

        partes = texto.split(",")
        elementos = []

        for parte in partes:
            elemento = parte.strip()

            if elemento == "":
                return None, (
                    "El campo " + nombre_campo + " contiene un elemento vacío."
                )

            elementos.append(elemento)

        if len(elementos) != len(set(elementos)):
            return None, (
                "El campo " + nombre_campo + " contiene elementos duplicados."
            )

        return set(elementos), None



#==================================================== MENU PRINCIPAL DEL PROYECTO :) ===========================================================
def mostrar_validacion(afd):
    valido, errores = ValidadorAFD.validar(afd)

    print("\n--- VALIDACIÓN DEL AFD ---")

    if valido:
        print("El autómata cumple con las validaciones estructurales del AFD.")

        analisis = ValidadorAFD.analizar_estructura(afd)
        print("Estados alcanzables:", analisis["alcanzables"])
        print("Estados inaccesibles:", analisis["inaccesibles"])
        print("Estados finales alcanzables:", analisis["finales_alcanzables"])

        if analisis["lenguaje_posiblemente_vacio"]:
            print("El lenguaje reconocido podría ser vacío.")
        else:
            print("Existe al menos un estado final alcanzable desde q0.")
    else:
        print("El autómata NO es válido.")
        for error in errores:
            print("-", error)


def asegurar_afd_valido(afd):
    """Valida automáticamente antes de cualquier evaluación."""
    if afd is None:
        print("Primero debe crear o cargar un autómata.")
        return False

    valido, errores = ValidadorAFD.validar(afd)

    if not valido:
        print("El autómata no puede procesarse porque no es válido:")
        for error in errores:
            print("-", error)
        return False

    return True


def evaluar_archivo_cadenas(afd):
    if not asegurar_afd_valido(afd):
        return

    ruta = input("Ruta del archivo de cadenas: ").strip()

    try:
        archivo = open(ruta, "r", encoding="utf-8")
        lineas = archivo.readlines()
        archivo.close()
    except Exception as error:
        print("No fue posible abrir el archivo:", error)
        return

    print("\n=== EVALUACIÓN POR LOTE ===")

    for numero, linea in enumerate(lineas, start=1):
        cadena = linea.strip()
        print("\nCadena", numero, ":", repr(cadena))

        aceptada, resultado = SimuladorAFD.evaluar(
            afd, cadena, mostrar_traza=True
        )

        # Cuando hay un símbolo inválido, 'resultado' contiene el mensaje de error.
        if isinstance(resultado, str) and resultado not in ("Aceptada", "Rechazada"):
            print(resultado)


def mostrar_historial(afd):
    if afd is None:
        print("Primero debe crear o cargar un autómata.")
        return

    if len(afd.historial) == 0:
        print("\nNo hay evaluaciones registradas.")
        return

    print("\n--- HISTORIAL DE EVALUACIONES ---")

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
    print("\n1. Crear manualmente")
    print("2. Cargar desde archivo")
    opcion = input("Seleccione una opción: ").strip()

    if opcion == "1":
        return CargadorAFD.crear_manual()

    if opcion == "2":
        ruta = input("Ruta del archivo .txt: ").strip()
        return CargadorAFD.cargar_archivo(ruta)

    print("Opción inválida.")
    return None


def mostrar_menu():
    print("\n" + "=" * 55)
    print("        SIMULADOR DE AUTÓMATA FINITO DETERMINISTA")
    print("=" * 55)
    print("1. Crear un AFD manualmente")
    print("2. Cargar un AFD desde un archivo .txt")
    print("3. Mostrar la definición formal del AFD")
    print("4. Mostrar la tabla de transición")
    print("5. Validar la estructura del autómata")
    print("6. Evaluar una cadena")
    print("7. Evaluar un archivo de cadenas")
    print("8. Consultar el historial de evaluaciones")
    print("9. Cargar o crear otro autómata")
    print("10. Salir")


def main():
    afd_actual = None

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            afd_actual = CargadorAFD.crear_manual()
            print("\nAFD creado correctamente.")

        elif opcion == "2":
            ruta = input("Ruta del archivo .txt: ").strip()
            nuevo_afd = CargadorAFD.cargar_archivo(ruta)

            if nuevo_afd is not None:
                afd_actual = nuevo_afd
                print("\nAFD cargado correctamente.")

        elif opcion == "3":
            if afd_actual is None:
                print("Primero debe crear o cargar un autómata.")
            else:
                afd_actual.mostrar_definicion_formal()

        elif opcion == "4":
            if afd_actual is None:
                print("Primero debe crear o cargar un autómata.")
            else:
                afd_actual.mostrar_tabla_transicion()

        elif opcion == "5":
            if afd_actual is None:
                print("Primero debe crear o cargar un autómata.")
            else:
                mostrar_validacion(afd_actual)

        elif opcion == "6":
            if asegurar_afd_valido(afd_actual):
                cadena = input("Ingrese la cadena a evaluar: ")
                aceptada, resultado = SimuladorAFD.evaluar(
                    afd_actual, cadena, mostrar_traza=True
                )

                if resultado not in ("Aceptada", "Rechazada"):
                    print(resultado)

        elif opcion == "7":
            evaluar_archivo_cadenas(afd_actual)

        elif opcion == "8":
            mostrar_historial(afd_actual)

        elif opcion == "9":
            nuevo_afd = crear_o_cargar_otro()

            if nuevo_afd is not None:
                afd_actual = nuevo_afd
                print("\nNuevo autómata cargado en memoria.")

        elif opcion == "10":
            print("\nPrograma finalizado.")
            break

        else:
            print("Opción inválida. Ingrese un número del 1 al 10.")


if __name__ == "__main__":
    main()