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