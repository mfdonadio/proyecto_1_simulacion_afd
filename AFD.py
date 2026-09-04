"""
Clase AFD que representa formalmente un Autómata Finito Determinista.
Un AFD es una tupla (Q, Σ, δ, q0, F) donde:
    Q: conjunto de estados
    Σ: alfabeto (símbolos válidos)
    δ: función de transición (diccionario)
    q0: estado inicial
    F: conjunto de estados finales (aceptación)
"""
class AFD:
    """Constructor que inicializa un Autómata Finito Determinista vacío."""
    def __init__(afd, nombre=""):
        # Identificador del autómata
        afd.nombre = nombre
        
        # Conjunto de todos los estados posibles del autómata
        afd.estados = set()
        
        # Alfabeto: conjunto de símbolos válidos que el autómata puede procesar
        afd.alfabeto = set()
        
        # Estado inicial: punto de partida para procesar cualquier cadena
        afd.estado_inicial = ""
        
        # Conjunto de estados finales (aceptadores): si terminamos en uno de estos,
        # la cadena es aceptada; si no, es rechazada
        afd.estados_finales = set()
        
        # Diccionario de transiciones: clave = (estado, símbolo), valor = estado_destino
        # Esto es la función δ del AFD formal
        afd.transiciones = {}
        
        # Lista para detectar no-determinismo: almacena transiciones duplicadas
        # Si la misma pareja (estado, símbolo) aparece más de una vez, el AFD no es determinista
        afd.transiciones_repetidas = []
        
        # Booleano que indica si el AFD ha pasado validación estructural
        # (cumple con ser un AFD válido)
        afd.es_valido = False
        
        # Historial de todas las cadenas evaluadas: registra resultado de cada procesamiento
        afd.historial = []

    def agregar_transicion(afd, estado_origen, simbolo, estado_destino):
        """
        Agrega una transición a la función δ del AFD.
        En un AFD determinista, cada pareja (estado, símbolo) debe tener EXACTAMENTE
        una transición. Si detectamos una duplicada, la registramos como anomalía.
        
        Parámetros:
            estado_origen: Estado desde el cual partimos
            simbolo: Símbolo del alfabeto que leemos
            estado_destino: Estado al cual se va después de leer el símbolo
        
        Retorna:
            True si la transición se agregó correctamente
            False si ya existía una transición para ese (estado, símbolo)
        """
        # Creamos una tupla (estado, símbolo) como clave del diccionario
        clave = (estado_origen, simbolo)

        #Cualquier modificacion en δ invalida una validacion anterior
        afd.es_valido = False
        
        # Verificamos si ya existe una transición para esta pareja
        if clave in afd.transiciones:
            # Esto viola el determinismo: registramos como transición repetida
            afd.transiciones_repetidas.append((estado_origen, simbolo, estado_destino))
            return False
        
        # Si es la primera vez que vemos esta pareja, la agregamos normalmente
        afd.transiciones[clave] = estado_destino
        return True

    def mostrar_definicion_formal(afd):
        """
        Muestra la definición formal del AFD usando la notación matemática:
        AFD = (Q, Σ, δ, q0, F)
        
        Donde:
            Q: Conjunto de estados
            Σ: Alfabeto (símbolos válidos)
            δ: Función de transición
            q0: Estado inicial
            F: Conjunto de estados finales
        """
        print("\n--- DEFINICION FORMAL DEL AFD ---")
        print("Nombre: " , afd.nombre)
        print("Q =", afd.estados)
        print("Σ =", afd.alfabeto)
        print("q0 =", afd.estado_inicial)
        print("F =", afd.estados_finales)
        print("δ =")
        
        # Iteramos sobre todas las transiciones y las mostramos en formato δ(estado, símbolo) = destino
        for clave, destino in afd.transiciones.items():
            estado_origen, simbolo = clave
            print("  δ(" + estado_origen + ", " + simbolo + ") = " + destino)

    def mostrar_tabla_transicion(afd):
        """
        Muestra la tabla de transiciones en formato tabular.
        Cada fila representa un estado, cada columna un símbolo del alfabeto.
        Las celdas contienen el estado destino para esa transición.
        """
        # Validación: necesitamos al menos un estado y un símbolo para mostrar algo útil
        if not afd.estados or not afd.alfabeto:
            print("\nNo hay datos suficientes para mostrar la tabla de transicion.")
            return
        
        # Ordenamos los estados y símbolos alfabéticamente para mejor legibilidad
        estados_ordenados = sorted(afd.estados)
        alfabeto_ordenado = sorted(afd.alfabeto)
        
        # Parámetro de formato: ancho de cada columna en caracteres
        ancho = 15
        
        # Creamos el encabezado de la tabla: primera columna es "Estado"
        encabezado = "Estado".ljust(ancho)
        
        # Agregamos una columna para cada símbolo del alfabeto
        for simbolo in alfabeto_ordenado:
            encabezado += simbolo.ljust(ancho)
        
        # Imprimimos el encabezado y separador visual
        print("\n--- TABLA DE TRANSICIONES DEL AFD ---")
        print(encabezado)
        print("-" * len(encabezado))
        
        # Llenamos las filas: una por cada estado
        for estado in estados_ordenados:
            fila = estado.ljust(ancho)
            
            # Para cada símbolo, buscamos el estado destino
            for simbolo in alfabeto_ordenado:
                # Si no existe transición, mostramos "---" (muy importante en AFD parciales)
                destino = afd.transiciones.get((estado, simbolo), "---")
                fila += destino.ljust(ancho)
            
            print(fila)