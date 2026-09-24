"""
Clase AFND que representa formalmente un Autómata Finito NO Determinista.
Un AFND es una tupla (Q, Σ, δ, q0, F) donde:
    Q: conjunto de estados
    Σ: alfabeto (símbolos válidos)
    δ: función de transición (diccionario)
    q0: estado inicial
    F: conjunto de estados finales (aceptación)
"""


class AFND:
    """Constructor que inicializa un Autómata Finito NO Determinista vacío."""

    def __init__(afnd, nombre=""):
        # Identificador del autómata
        afnd.nombre = nombre

        # Conjunto de todos los estados posibles del autómata
        afnd.estados = set()

        # Alfabeto: conjunto de símbolos válidos que el autómata puede procesar
        afnd.alfabeto = set()

        # Estado inicial: punto de partida para procesar cualquier cadena
        afnd.estado_inicial = ""

        # Conjunto de estados finales (aceptadores): si terminamos en uno de estos,
        # la cadena es aceptada; si no, es rechazada
        afnd.estados_finales = set()

        # Diccionario de transiciones:
        # clave = (estado, símbolo)
        # valor = conjunto de estados destino
        # Esto representa la función δ del AFND formal
        afnd.transiciones = {}

        # A diferencia del AFD, en un AFND se pueden tener múltiples
        # estados destino para una misma pareja (estado, símbolo).

        # Booleano que indica si el AFND ha pasado la validación estructural
        # (cumple con ser un AFND válido)
        afnd.es_valido = False

        # Historial de todas las cadenas evaluadas:
        # registra el resultado de cada procesamiento
        afnd.historial = []

    def agregar_transicion(
        afnd,
        estado_origen,
        simbolo,
        estados_destino
    ):
        """
        Agrega o une un conjunto de destinos para una pareja de transición.

        Parámetros:
            estado_origen: estado desde el cual inicia la transición
            simbolo: símbolo que permite realizar la transición
            estados_destino: conjunto de posibles estados de llegada
        """

        # Rechazamos otros tipos antes de modificar las transiciones.
        if not isinstance(estados_destino, set):
            raise TypeError("Los estados destino deben ser un conjunto.")
        if not isinstance(estado_origen, str) or not isinstance(simbolo, str):
            raise TypeError("El origen y el símbolo deben ser texto.")
        if any(not isinstance(destino, str) for destino in estados_destino):
            raise TypeError("Todos los estados destino deben ser texto.")

        # Creamos una tupla (estado, símbolo) como clave del diccionario
        clave = (estado_origen, simbolo)

        # Cualquier modificación en δ invalida una validación anterior
        afnd.es_valido = False

        # Si no existe la clave en el diccionario de transiciones,
        # la inicializamos con un conjunto vacío
        if clave not in afnd.transiciones:
            afnd.transiciones[clave] = set()

        # Unimos los nuevos estados destino con los que ya existían
        # para la misma pareja (estado, símbolo)
        afnd.transiciones[clave].update(estados_destino)

    # Creamos una función especializada para obtener el conjunto de destinos
    # de una tupla (estado, símbolo) en el diccionario de transiciones δ
    def obtener_destinos(afnd, estado_origen, simbolo):
        """
        Retorna una copia del conjunto de destinos.
        Si la transición no fue definida, retorna el conjunto vacío ∅.
        """

        # get busca la transición. Si no existe, utiliza un conjunto vacío
        destinos = afnd.transiciones.get(
            (estado_origen, simbolo),
            set()
        )

        # Retornamos una copia para evitar que el conjunto original
        # sea modificado accidentalmente desde fuera de la clase
        return set(destinos)

    # Mostramos la definición formal completa del AFND
    def mostrar_definicion_formal(afnd):
        """
        Muestra la definición formal del AFND usando la notación matemática:

        AFND = (Q, Σ, δ, q0, F)

        Donde:
            Q: conjunto de estados
            Σ: alfabeto
            δ: función de transición
            q0: estado inicial
            F: conjunto de estados finales
        """

        print("\n--- DEFINICIÓN FORMAL DEL AFND ---")
        print("Nombre:", afnd.nombre)
        print("Q =", afnd._formatear_conjunto(afnd.estados))
        print("Σ =", afnd._formatear_conjunto(afnd.alfabeto))
        print("q0 =", afnd.estado_inicial)
        print("F =", afnd._formatear_conjunto(afnd.estados_finales))
        print("δ =")

        # Iteramos sobre todos los estados del AFND
        for estado in sorted(afnd.estados):

            # Por cada estado, recorremos todos los símbolos del alfabeto
            for simbolo in sorted(afnd.alfabeto):

                # Obtenemos el conjunto de destinos correspondiente
                destinos = afnd.obtener_destinos(
                    estado,
                    simbolo
                )

                # Mostramos la transición en formato:
                # δ(estado, símbolo) = {destinos}
                print(
                    "  δ("
                    + estado
                    + ", "
                    + simbolo
                    + ") = "
                    + afnd._formatear_conjunto(destinos)
                )

    def mostrar_tabla_transicion(afnd):
        """
        Muestra la tabla de transiciones en formato tabular.

        Cada fila representa un estado y cada columna representa
        un símbolo del alfabeto.

        Las celdas muestran los destinos como conjuntos,
        incluso cuando solamente contienen un estado.
        """

        # Necesitamos al menos un estado y un símbolo
        # para poder construir la tabla
        if not afnd.estados or not afnd.alfabeto:
            print(
                "\nNo hay datos suficientes para mostrar "
                "la tabla de transición."
            )
            return

        # Ordenamos los estados y símbolos alfabéticamente
        # para mejorar la legibilidad de la tabla
        estados_ordenados = sorted(afnd.estados)
        alfabeto_ordenado = sorted(afnd.alfabeto)

        # Esta lista almacenará temporalmente el texto de todas las celdas
        # para poder calcular el ancho necesario de las columnas
        celdas = []

        # Recorremos cada estado
        for estado in estados_ordenados:

            # Por cada estado, recorremos cada símbolo
            for simbolo in alfabeto_ordenado:

                # Obtenemos los destinos de la pareja (estado, símbolo)
                destinos = afnd.obtener_destinos(
                    estado,
                    simbolo
                )

                # Formateamos el conjunto y lo guardamos
                # para calcular posteriormente el ancho de la tabla
                celdas.append(
                    afnd._formatear_conjunto(destinos)
                )

        # Calculamos el ancho necesario para cada columna.
        # Se considera el encabezado, los estados, los símbolos
        # y el contenido de todas las celdas
        elementos_tabla = (
            estados_ordenados
            + alfabeto_ordenado
            + celdas
        )

        ancho = max(
            [len("Estado")]
            + [len(elemento) for elemento in elementos_tabla]
        ) + 3

        # Creamos la primera columna del encabezado
        encabezado = "Estado".ljust(ancho)

        # Agregamos una columna por cada símbolo del alfabeto
        for simbolo in alfabeto_ordenado:
            encabezado += simbolo.ljust(ancho)

        # Imprimimos el encabezado de la tabla
        print("\n--- TABLA DE TRANSICIONES DEL AFND ---")
        print(encabezado)
        print("-" * len(encabezado))

        # Mostramos cada estado en una fila
        for estado in estados_ordenados:
            fila = estado.ljust(ancho)

            # Agregamos a la fila el conjunto de destinos
            # correspondiente a cada símbolo
            for simbolo in alfabeto_ordenado:
                destinos = afnd.obtener_destinos(
                    estado,
                    simbolo
                )

                destino_formateado = (
                    afnd._formatear_conjunto(destinos)
                )

                fila += destino_formateado.ljust(ancho)

            # Imprimimos la fila completa
            print(fila)

    # Formato utilizado para mostrar conjuntos
    @staticmethod
    def _formatear_conjunto(elementos):
        """
        Devuelve ∅ si el conjunto está vacío.

        Si contiene elementos, los ordena y los muestra
        separados por comas dentro de llaves.
        """

        # Si no existen elementos, representamos el conjunto vacío
        if not elementos:
            return "∅"

        # Ordenamos los elementos para obtener una salida consistente
        return "{" + ", ".join(sorted(elementos)) + "}"
