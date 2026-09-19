"""
Conversión de un AFND a un AFD mediante el algoritmo
de construcción de subconjuntos.
"""

# Importamos la clase utilizada para crear el AFD equivalente
from AFD import AFD

# Importamos los validadores de ambos tipos de autómatas
from ValidadorAFD import ValidadorAFD
from ValidadorAFND import ValidadorAFND


class ConvertidorAFND:
    """
    Convierte un AFND válido en un AFD equivalente.

    Cada estado del AFD representa un conjunto de estados
    del AFND original. A estos conjuntos se les llama macroestados.
    """

    @staticmethod
    def convertir(afnd):
        """
        Convierte el AFND recibido en un AFD equivalente.

        Retorna:
            afd: AFD generado mediante construcción de subconjuntos
            equivalencias: relación entre macroestados y subconjuntos
            errores: lista de errores encontrados durante la conversión
        """

        # Antes de convertir, validamos que el AFND tenga
        # una estructura correcta
        valido, errores = ValidadorAFND.validar(afnd)

        # Si el AFND contiene errores, detenemos la conversión
        # y devolvemos la lista con los problemas encontrados
        if not valido:
            return None, {}, errores

        # Creamos el AFD equivalente.
        # Su nombre se forma agregando "_AFD" al nombre del AFND original
        afd = AFD(afnd.nombre + "_AFD")

        # El AFD generado utiliza el mismo alfabeto que el AFND
        # Se crea una copia para evitar modificar el conjunto original
        afd.alfabeto = set(afnd.alfabeto)

        # El primer macroestado contiene únicamente
        # el estado inicial del AFND
        inicial = frozenset([afnd.estado_inicial])

        # Este diccionario relaciona cada subconjunto del AFND
        # con el identificador que tendrá dentro del AFD
        #
        # Ejemplo:
        # frozenset({"q0", "q1"}) -> "B"
        subconjunto_a_nombre = {
            inicial: "A"
        }

        # Este diccionario guarda la relación en el sentido contrario:
        # nombre del macroestado -> conjunto de estados del AFND
        #
        # Ejemplo:
        # "B" -> {"q0", "q1"}
        equivalencias = {
            "A": set(inicial)
        }

        # La lista pendientes funciona como una cola.
        # Aquí se almacenan los macroestados que todavía
        # deben procesarse
        pendientes = [inicial]

        # Posición indica cuál macroestado de la cola
        # se está procesando actualmente
        posicion = 0

        # Repetimos el proceso mientras todavía existan
        # macroestados pendientes de revisar
        while posicion < len(pendientes):

            # Obtenemos el macroestado ubicado en la posición actual
            macroestado = pendientes[posicion]

            # Avanzamos la posición para procesar después
            # el siguiente macroestado de la cola
            posicion += 1

            # Buscamos el identificador asignado al macroestado actual
            nombre_origen = subconjunto_a_nombre[macroestado]

            # Probamos cada símbolo del alfabeto sobre el macroestado
            for simbolo in sorted(afnd.alfabeto):

                # Aquí uniremos todos los estados alcanzables
                # desde los estados que forman el macroestado actual
                union_destinos = set()

                # Recorremos cada estado contenido en el macroestado
                for estado in macroestado:

                    # Obtenemos sus destinos con el símbolo actual
                    # y los unimos con los destinos encontrados anteriormente
                    union_destinos.update(
                        afnd.obtener_destinos(
                            estado,
                            simbolo
                        )
                    )

                # Convertimos el conjunto de destinos en frozenset
                # para poder utilizarlo como clave de un diccionario
                destino = frozenset(union_destinos)

                # Si este subconjunto todavía no existe en el AFD,
                # debemos registrarlo como un nuevo macroestado
                if destino not in subconjunto_a_nombre:

                    # Creamos un identificador según la cantidad
                    # de macroestados registrados: A, B, C, ..., AA...
                    nombre = ConvertidorAFND._crear_identificador(
                        len(subconjunto_a_nombre)
                    )

                    # Relacionamos el subconjunto con su nuevo identificador
                    subconjunto_a_nombre[destino] = nombre

                    # Guardamos la equivalencia en el sentido contrario
                    equivalencias[nombre] = set(destino)

                    # Agregamos el nuevo macroestado a la cola
                    # para procesar posteriormente sus transiciones
                    pendientes.append(destino)

                # Agregamos al AFD la transición desde el macroestado actual
                # hacia el macroestado que representa la unión de destinos
                afd.agregar_transicion(
                    nombre_origen,
                    simbolo,
                    subconjunto_a_nombre[destino]
                )

        # Los identificadores registrados en equivalencias
        # se convierten en el conjunto de estados Q del AFD
        afd.estados = set(equivalencias)

        # El macroestado inicial siempre recibe el identificador A
        afd.estado_inicial = "A"

        # Recorremos cada macroestado para determinar
        # cuáles deben ser estados finales del AFD
        for nombre, subconjunto in equivalencias.items():

            # Un macroestado es final si contiene por lo menos
            # un estado final del AFND original
            if subconjunto.intersection(afnd.estados_finales):
                afd.estados_finales.add(nombre)

        # Validamos el AFD generado para confirmar que sea
        # determinista, completo y estructuralmente válido
        ValidadorAFD.validar(afd)

        # Retornamos el AFD, su tabla de equivalencias
        # y una lista vacía porque la conversión fue exitosa
        return afd, equivalencias, []

    @staticmethod
    def mostrar_equivalencias(equivalencias):
        """
        Muestra la relación entre los macroestados del AFD
        y los subconjuntos de estados del AFND.
        """

        # Si no existen equivalencias, significa que todavía
        # no se ha realizado una conversión correctamente
        if not equivalencias:
            print(
                "\nNo existe una conversión "
                "con equivalencias disponibles."
            )
            return

        # Calculamos el ancho de la primera columna.
        # Se toma en cuenta el encabezado y los identificadores existentes
        ancho = max(
            len("Macroestado"),
            max(len(nombre) for nombre in equivalencias)
        ) + 3

        # Mostramos el encabezado de la tabla
        print("\n--- TABLA DE EQUIVALENCIAS ---")
        print(
            "Macroestado".ljust(ancho)
            + "Conjunto de estados del AFND"
        )
        print("-" * (ancho + 30))

        # Recorremos los macroestados en el mismo orden
        # en que fueron descubiertos durante la conversión
        for nombre in ConvertidorAFND._ordenar_identificadores(
            equivalencias
        ):

            # Obtenemos el subconjunto representado por el macroestado
            conjunto = equivalencias[nombre]

            # Si el conjunto está vacío, utilizamos el símbolo ∅.
            # De lo contrario, mostramos sus estados entre llaves
            if not conjunto:
                texto = "∅"
            else:
                texto = (
                    "{"
                    + ", ".join(sorted(conjunto))
                    + "}"
                )

            # Imprimimos el identificador junto con su subconjunto
            print(nombre.ljust(ancho) + texto)

    @staticmethod
    def _crear_identificador(indice):
        """
        Crea identificadores siguiendo este orden:

        A, B, C, ..., Z, AA, AB, ..., AZ, BA...

        Esto permite nombrar cualquier cantidad de macroestados.
        """

        # Aquí construiremos el identificador final
        resultado = ""

        # Copiamos el índice para modificarlo sin alterar
        # el valor recibido originalmente
        numero = indice

        # Repetimos el proceso hasta convertir todo el índice
        # en letras
        while True:

            # numero % 26 obtiene una posición entre 0 y 25.
            # Luego, chr y ord convierten esa posición en una letra
            resultado = (
                chr(ord("A") + numero % 26)
                + resultado
            )

            # Dividimos entre 26 para avanzar hacia
            # la siguiente posición del identificador
            #
            # Se resta uno porque el sistema empieza en A,
            # no existe un símbolo equivalente al cero
            numero = numero // 26 - 1

            # Cuando el número queda debajo de cero,
            # el identificador está completo
            if numero < 0:
                return resultado

    @staticmethod
    def _ordenar_identificadores(equivalencias):
        """
        Retorna los identificadores en el mismo orden
        en que fueron agregados al diccionario.
        """

        # Desde Python 3.7, los diccionarios conservan
        # el orden de inserción de sus elementos
        return list(equivalencias.keys())