import re  # Módulo para validar patrones de entrada usando expresiones regulares

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
        afd.validado = False
        
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

class ValidadorAFD:
    """
    Valida que un AFD cumpla con la definición formal.
    Un AFD válido debe cumplir:
    1. Tener todos sus componentes definidos (Q, Σ, δ, q0, F)
    2. q0 ∈ Q (estado inicial en Q)
    3. F ⊆ Q (estados finales en Q)
    4. Para cada transición: origen ∈ Q, símbolo ∈ Σ, destino ∈ Q
    5. Ser determinista: una sola transición por (estado, símbolo)
    6. Ser completo: una transición para cada (estado, símbolo) posible
    """
    @staticmethod
    def validar(afd):
        """
        Realiza validación estructural completa del AFD.
        
        Retorna:
            Tupla (booleano_validez, lista_de_errores)
        """
        errores = []
        
        # ========== VALIDACIONES BÁSICAS DE COMPONENTES ==========
        # Un AFD debe tener un identificador
        if afd.nombre.strip() == "":
            errores.append("El automata no tiene un nombre definido o un identificador.")
        
        # Q (conjunto de estados) no puede estar vacío
        if len(afd.estados) == 0:
            errores.append("El conjunto de estados Q no puede estar vacío.")
        
        # Σ (alfabeto) no puede estar vacío
        if len(afd.alfabeto) == 0:
            errores.append("El alfabeto Σ no puede estar vacío.")
        
        # ========== VALIDAR q0 (ESTADO INICIAL) ==========
        # El estado inicial q0 debe pertenecer al conjunto Q
        if afd.estado_inicial not in afd.estados:
            errores.append("El estado inicial q0 no pertenece al conjunto de estados Q.")
        
        # ========== VALIDAR F (ESTADOS FINALES) ==========
        # Todos los estados finales deben pertenecer a Q
        for estado_final in afd.estados_finales:
            if estado_final not in afd.estados:
                errores.append(
                    "El estado final " + estado_final + " no pertenece al conjunto Q."
                )
        
        # ========== VALIDAR TRANSICIONES ==========
        # Cada transición δ(q, a) = q' debe cumplir:
        # - q ∈ Q (origen en estados)
        # - a ∈ Σ (símbolo en alfabeto)
        # - q' ∈ Q (destino en estados)
        for clave, estado_destino in afd.transiciones.items():
            estado_origen, simbolo = clave
            
            # Verificar estado origen
            if estado_origen not in afd.estados:
                errores.append(
                    "La transición usa el estado origen inexistente " + estado_origen + "'."
                )
            
            # Verificar símbolo
            if simbolo not in afd.alfabeto:
                errores.append(
                    "La transición usa el símbolo inexistente " + simbolo + "'."
                )
            
            # Verificar estado destino
            if estado_destino not in afd.estados:
                errores.append(
                    "La transición apunta al estado destino inexistente " + estado_destino + "."
                )
        
        # ========== VALIDAR DETERMINISMO ==========
        # Un AFD debe ser determinista: no puede haber dos transiciones
        # diferentes para la misma pareja (estado, símbolo)
        for repetida in afd.transiciones_repetidas:
            estado_origen, simbolo, estado_destino = repetida
            errores.append(
                "No es determinista: existen múltiples transiciones para ("
                + estado_origen
                + ", "
                + simbolo
                + "). Una va a: '"
                + estado_destino
                + "'."
            )
        
        # ========== VALIDAR COMPLETITUD ==========
        # Un AFD completo debe tener una transición para CADA combinación
        # de (estado, símbolo). Esto garantiza que siempre hay un siguiente estado.
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
        
        # ========== RESULTADO FINAL ==========
        # AFD es válido si no hay errores
        afd.es_valido = len(errores) == 0
        
        return afd.es_valido, errores

    @staticmethod
    def analizar_estructura(afd):
        """
        Analiza la estructura del AFD para detectar problemas de accesibilidad.
        
        Calcula:
        1. Estados alcanzables: aquellos a los que se puede llegar desde q0
        2. Estados inaccesibles: aquellos que nunca se alcanzan (son código muerto)
        3. Estados finales alcanzables: estados aceptadores realmente útiles
        4. Lenguaje vacío: si no hay manera de aceptar ninguna cadena
        
        Usa búsqueda en profundidad (DFS) desde el estado inicial.
        """
        
        # ========== ENCONTRAR ESTADOS ALCANZABLES ==========
        # Usamos DFS (Depth-First Search) con una pila (lista)
        # para explorar todos los estados accesibles desde q0
        
        estados_alcanzables = set()  # Estados ya visitados
        pendientes = [afd.estado_inicial]  # Pila de estados a procesar
        
        # Procesamos estados hasta que la pila esté vacía
        while len(pendientes) > 0:
            # Sacamos un estado de la pila (estrategia LIFO para DFS)
            estado_actual = pendientes.pop()
            
            # Si ya lo visitamos, saltamos (evita ciclos infinitos)
            if estado_actual in estados_alcanzables:
                continue
            
            # Marcamos como visitado
            estados_alcanzables.add(estado_actual)
            
            # Exploramos todos los vecinos: intentamos todas las transiciones
            # desde este estado usando cada símbolo del alfabeto
            for simbolo in afd.alfabeto:
                # Obtenemos el siguiente estado si existe la transición
                siguiente = afd.transiciones.get((estado_actual, simbolo))
                
                # Si hay transición y el destino aún no está visitado, lo agregamos
                if siguiente is not None and siguiente not in estados_alcanzables:
                    pendientes.append(siguiente)
        
        # ========== CALCULAR RESULTADOS ==========
        # Estados inaccesibles: los que NO se pueden alcanzar desde q0
        inaccesibles = afd.estados - estados_alcanzables
        
        # Estados finales útiles: solo los que realmente se alcanzan
        finales_alcanzables = afd.estados_finales.intersection(estados_alcanzables)
        
        # Lenguaje vacío: si no hay ningún estado final alcanzable,
        # el AFD nunca aceptará ninguna cadena
        lenguaje_posiblemente_vacio = len(finales_alcanzables) == 0
        
        return {
            "alcanzables": estados_alcanzables,
            "inaccesibles": inaccesibles,
            "finales_alcanzables": finales_alcanzables,
            "lenguaje_posiblemente_vacio": lenguaje_posiblemente_vacio,
        }
    
class SimuladorAFD:
    """
    Simula la ejecución del AFD sobre cadenas de entrada.
    Lee la cadena símbolo por símbolo y sigue las transiciones.
    Genera una traza completa del procesamiento (opcional).
    """
    
    @staticmethod
    def evaluar(afd, cadena, mostrar_traza=True):
        """
        Procesa una cadena en el AFD y determina si es aceptada.
        
        Parámetros:
            afd: El autómata a simular (debe estar validado)
            cadena: String a evaluar
            mostrar_traza: Si True, muestra paso a paso la ejecución
        
        Retorna:
            Tupla (aceptada, resultado)
            - aceptada: bool indicando si la cadena fue aceptada
            - resultado: String descriptivo del resultado
        """
        # ========== VALIDACIÓN PREVIA ==========
        # El AFD debe haber pasado validación antes de usarlo
        if not afd.es_valido:
            return False, "El AFD debe validarse antes de evaluar cadenas."
        
        # ========== VALIDAR SÍMBOLOS DE LA CADENA ==========
        # Todos los símbolos de la cadena deben estar en el alfabeto
        for simbolo in cadena:
            if simbolo not in afd.alfabeto:
                return False, (
                    "La cadena contiene el símbolo '"
                    + simbolo
                    + "' que no pertenece al alfabeto Σ."
                )
        
        # ========== INICIALIZAR SIMULACIÓN ==========
        # Comenzamos en el estado inicial q0
        estado_actual = afd.estado_inicial
        
        # Mostrar inicio si se pide traza
        if mostrar_traza:
            print("\n--- TRAZA DE EJECUCION ---")
            print("Estado inicial: ", estado_actual)
        
        # ========== PROCESAR CADENA SÍMBOLO POR SÍMBOLO ==========
        # Para cada símbolo, seguimos la transición correspondiente
        for simbolo in cadena:
            # Buscamos el siguiente estado: δ(estado_actual, símbolo)
            siguiente_estado = afd.transiciones[(estado_actual, simbolo)]
            
            # Mostramos la transición si se pide traza
            if mostrar_traza:
                print(
                    estado_actual
                    + " ---"
                    + simbolo
                    + "--> "
                    + siguiente_estado
                )
            
            # Avanzamos al siguiente estado
            estado_actual = siguiente_estado
        
        # ========== VERIFICAR ACEPTACIÓN ==========
        # La cadena se ACEPTA si terminamos en un estado final (F)
        # La cadena se RECHAZA si terminamos en un estado no final
        aceptada = estado_actual in afd.estados_finales
        resultado = "Aceptada" if aceptada else "Rechazada"
        
        # Mostrar resultado si se pide traza
        if mostrar_traza:
            print("Estado final: ", estado_actual)
            print("Resultado: " + resultado)
        
        # ========== REGISTRAR EN HISTORIAL ==========
        # Guardamos la evaluación para consultas posteriores
        afd.historial.append(
            {
                "cadena": cadena,
                "estado_final": estado_actual,
                "resultado": resultado,
            }
        )
        
        return aceptada, resultado

class CargadorAFD:
    """
    Gestiona la creación de AFD de dos formas:
    1. Creación manual: el usuario ingresa manualmente Q, Σ, q0, F y δ
    2. Carga desde archivo: lee un archivo .txt con formato específico
    
    Formato de archivo esperado:
    ├─ NOMBRE=MiAFD
    ├─ ESTADOS=q0,q1,q2
    ├─ ALFABETO=a,b
    ├─ INICIAL=q0
    ├─ FINALES=q2
    ├─ TRANSICIONES:
    ├─ q0,a,q1
    ├─ q0,b,q0
    ├─ q1,a,q2
    └─ q1,b,q1
    """

    @staticmethod
    def pedir_conjunto(mensaje, permitir_vacio=False):
        """
        Solicita al usuario un conjunto de elementos separados por comas.
        Valida que no haya elementos vacíos ni duplicados.
        
        Parámetros:
            mensaje: Texto que se muestra al usuario pidiendo entrada
            permitir_vacio: Si True, acepta entrada vacía; si False, requiere al menos un elemento
        
        Retorna:
            Un set con los elementos ingresados, o set vacío si se permite y el usuario ingresa vacío
        
        Ejemplo:
            pedir_conjunto("Estados: ") -> {"q0", "q1", "q2"}
        """
        
        while True:
            # Obtenemos y limpiamos la entrada
            entrada = input(mensaje).strip()
            
            # ========== CASO: ENTRADA VACÍA ==========
            # Si la entrada está vacía y se permite, retornamos set vacío
            if entrada == "" and permitir_vacio:
                return set()
            
            # Si la entrada está vacía pero NO se permite, pedimos de nuevo
            if entrada == "":
                print("La entrada no puede estar vacia.")
                continue
            
            # ========== PROCESAR ENTRADA ==========
            # Dividimos por comas y limpiamos espacios de cada elemento
            partes = entrada.split(",")
            elementos = []
            hay_vacios = False
            
            # Validar cada elemento después de dividir
            for parte in partes:
                elemento = parte.strip()
                
                # Detectar elementos vacíos (ej: "q0,,q1")
                if elemento == "":
                    hay_vacios = True
                    break
                
                elementos.append(elemento)
            
            # ========== VALIDACIÓN: SIN ESPACIOS VACÍOS ==========
            if hay_vacios:
                print("No se permiten elementos vacios entre comas.")
                continue
            
            # ========== VALIDACIÓN: SIN DUPLICADOS ==========
            # Comparamos cantidad de elementos con cantidad de elementos únicos
            if len(elementos) != len(set(elementos)):
                print("No se permiten estados o símbolos duplicados.")
                continue
            
            # Si pasó todas las validaciones, retornamos el set
            return set(elementos)

    @staticmethod
    def crear_manual():
        """
        Guía al usuario a través de la creación manual de un AFD.
        Solicita los 5 componentes: Q, Σ, q0, F, δ
        """
        print("\n=== CREACION MANUAL DEL AFD ===")
        afd = AFD()
        
        # ========== PASO 1: NOMBRE DEL AFD ==========
        # Solicitar nombre hasta que sea válido
        while afd.nombre.strip() == "":
            afd.nombre = input("Nombre del automata: ").strip()
            if afd.nombre == "":
                print("El nombre no puede estar vacio.")
        
        # ========== PASO 2: CONJUNTO DE ESTADOS (Q) ==========
        # Ejemplo: q0,q1,q2
        afd.estados = CargadorAFD.pedir_conjunto(
            "Estados separados por coma (ej. q0,q1,q2): "
        )
        
        # ========== PASO 3: ALFABETO (Σ) ==========
        # Ejemplo: a,b
        afd.alfabeto = CargadorAFD.pedir_conjunto(
            "Simbolos del alfabeto separados por coma (ej. a,b): "
        )
        
        # ========== PASO 4: ESTADO INICIAL (q0) ==========
        # Debe ser un elemento de Q
        while True:
            inicial = input("Estado inicial (debe estar en Q): ").strip()
            
            if inicial in afd.estados:
                afd.estado_inicial = inicial
                break
            
            print("Error: el estado inicial debe pertenecer al conjunto Q.")
        
        # ========== PASO 5: ESTADOS FINALES (F) ==========
        # Deben ser un subconjunto de Q. Pueden estar vacíos.
        while True:
            finales = CargadorAFD.pedir_conjunto(
                "Estados finales separados por coma (Enter si no hay): ",
                permitir_vacio=True,
            )
            
            # Verificar que todos los estados finales estén en Q
            if finales.issubset(afd.estados):
                afd.estados_finales = finales
                break
            
            print("Error: todos los estados finales deben pertenecer a Q.")
        
        # ========== PASO 6: FUNCIÓN DE TRANSICIÓN (δ) ==========
        print("\nIngrese la función de transición.")
        print("Para cada pareja (estado, símbolo), ingrese el estado destino.")
        print("Esto creará un AFD completo y determinista.\n")
        
        # Solicitar una transición para CADA combinación (estado, símbolo)
        # Al hacerlo así, el AFD es automáticamente determinista y completo
        for estado in sorted(afd.estados):
            for simbolo in sorted(afd.alfabeto):
                while True:
                    destino = input(
                        "δ(" + estado + ", " + simbolo + ") = "
                    ).strip()
                    
                    # El destino debe ser un estado válido
                    if destino in afd.estados:
                        afd.agregar_transicion(estado, simbolo, destino)
                        break
                    
                    print("Error: el estado destino debe pertenecer a Q.")
        
        return afd

    # ========== PATRONES REGEX PARA VALIDACIÓN DE ARCHIVOS ==========
    # Expresiones regulares para validar la sintaxis del archivo .txt
    # Cada patrón valida una línea específica del archivo
    _PATRON_ENCABEZADO = {
        "NOMBRE": re.compile(r"^NOMBRE=(?P<valor>.+)$"),
        "ESTADOS": re.compile(r"^ESTADOS=(?P<valor>.+)$"),
        "ALFABETO": re.compile(r"^ALFABETO=(?P<valor>.+)$"),
        "INICIAL": re.compile(r"^INICIAL=(?P<valor>.+)$"),
        "FINALES": re.compile(r"^FINALES=(?P<valor>.*)$"),
    }
    # Patrón para transiciones: origen,símbolo,destino (sin espacios)
    _PATRON_TRANSICION = re.compile(
        r"^(?P<origen>[^,\s]+),(?P<simbolo>[^,\s]+),(?P<destino>[^,\s]+)$"
    )

    @staticmethod
    def cargar_archivo(ruta):
        """
        Carga un AFD desde un archivo .txt con formato específico.
        
        Formato esperado:
            Línea 1: NOMBRE=NombreDelAFD
            Línea 2: ESTADOS=q0,q1,q2,...
            Línea 3: ALFABETO=a,b,c,...
            Línea 4: INICIAL=q0
            Línea 5: FINALES=q1,q2,...  (puede ser vacío)
            Línea 6: TRANSICIONES:
            Líneas 7+: origen,símbolo,destino
        
        Parámetros:
            ruta: Ruta al archivo .txt
        
        Retorna:
            Objeto AFD si se cargó correctamente, None si hay errores
        """
        
        # ========== PASO 1: LEER EL ARCHIVO ==========
        try:
            archivo = open(ruta, "r", encoding="utf-8")
            lineas = archivo.readlines()
            archivo.close()
        except Exception as error:
            print("Error: No fue posible abrir el archivo:", error)
            return None
        
        # ========== PASO 2: LIMPIAR LÍNEAS ==========
        # Removemos saltos de línea pero preservamos líneas vacías
        # para reportar errores con número de línea exacto
        limpias = []
        for linea in lineas:
            limpias.append(linea.strip())
        
        # Verificar estructura mínima: al menos 6 líneas
        if len(limpias) < 6:
            print("Error: El archivo no contiene la estructura mínima requerida.")
            print("Se necesitan 6 líneas mínimo (encabezados + TRANSICIONES:)")
            return None
        
        afd = AFD()
        errores = []
        
        # ========== PASO 3: VALIDAR ENCABEZADOS ==========
        # Las primeras 5 líneas deben cumplir el patrón CLAVE=valor
        claves_orden = ["NOMBRE", "ESTADOS", "ALFABETO", "INICIAL", "FINALES"]
        valores_encabezado = {}
        
        for indice, clave in enumerate(claves_orden):
            # Validar con expresión regular
            coincidencia = CargadorAFD._PATRON_ENCABEZADO[clave].match(limpias[indice])
            
            if coincidencia is None:
                # Error de sintaxis: la línea no sigue el patrón esperado
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": se esperaba el patrón '"
                    + clave
                    + "=...'."
                )
            else:
                # Extraer el valor después del "="
                valores_encabezado[clave] = coincidencia.group("valor").strip()
        
        # Validar línea 6: debe ser exactamente "TRANSICIONES:"
        if not re.match(r"^TRANSICIONES:$", limpias[5]):
            errores.append("Línea 6: se esperaba exactamente 'TRANSICIONES:'.")
        
        # Si hay errores de sintaxis, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None
        
        # ========== PASO 4: EXTRAER COMPONENTES ==========
        afd.nombre = valores_encabezado["NOMBRE"]
        
        estados_texto = valores_encabezado["ESTADOS"]
        alfabeto_texto = valores_encabezado["ALFABETO"]
        afd.estado_inicial = valores_encabezado["INICIAL"]
        finales_texto = valores_encabezado["FINALES"]
        
        # Convertir strings a sets, validando duplicados
        estados, error_estados = CargadorAFD._convertir_lista_archivo(
            estados_texto, "ESTADOS", permitir_vacio=False
        )
        alfabeto, error_alfabeto = CargadorAFD._convertir_lista_archivo(
            alfabeto_texto, "ALFABETO", permitir_vacio=False
        )
        finales, error_finales = CargadorAFD._convertir_lista_archivo(
            finales_texto, "FINALES", permitir_vacio=True
        )

        # Verificar si hubo errores al convertir
        if error_estados is not None:
            errores.append(error_estados)
        if error_alfabeto is not None:
            errores.append(error_alfabeto)
        if error_finales is not None:
            errores.append(error_finales)
        
        # Si hay errores de validación semántica, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron problemas en los datos:")
            for error in errores:
                print("-", error)
            return None
        
        # Asignar componentes validados al AFD
        afd.estados = estados
        afd.alfabeto = alfabeto
        afd.estados_finales = finales
        
        # ========== PASO 5: PROCESAR TRANSICIONES ==========
        # Las líneas después de "TRANSICIONES:" contienen las transiciones
        # Cada línea debe cumplir el patrón: origen,símbolo,destino
        for indice in range(6, len(limpias)):
            linea = limpias[indice]
            
            # No se permiten líneas vacías en la sección de transiciones
            if linea == "":
                errores.append(
                    "Línea " + str(indice + 1) + ": no se permiten líneas vacías."
                )
                continue
            
            # Validar formato de transición
            coincidencia = CargadorAFD._PATRON_TRANSICION.match(linea)
            
            if coincidencia is None:
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": una transición debe tener formato origen,símbolo,destino "
                    + "(sin espacios ni campos vacíos)."
                )
                continue
            
            # Extraer componentes de la transición
            origen = coincidencia.group("origen")
            simbolo = coincidencia.group("simbolo")
            destino = coincidencia.group("destino")
            
            # Agregar la transición (detectará no-determinismo automáticamente)
            afd.agregar_transicion(origen, simbolo, destino)
        
        # Si hay errores, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None
        
        return afd

    @staticmethod
    def _convertir_lista_archivo(texto, nombre_campo, permitir_vacio):
        """
        Convierte un string separado por comas en un set.
        Valida que no haya elementos vacíos ni duplicados.
        
        Parámetros:
            texto: String con elementos separados por comas
            nombre_campo: Nombre del campo (para mensajes de error)
            permitir_vacio: Si False, requiere al menos un elemento
        
        Retorna:
            Tupla (set_elementos, error_mensaje)
            Si no hay error, error_mensaje es None
        """
        # ========== CASO: CAMPO VACÍO ==========
        if texto == "":
            if permitir_vacio:
                # Si se permite vacío (e.g., FINALES), retornar set vacío
                return set(), None
            # Si no se permite (e.g., ESTADOS), retornar error
            return None, "Error: El campo " + nombre_campo + " no puede estar vacío."
        
        # ========== PROCESAR ELEMENTOS ==========
        partes = texto.split(",")
        elementos = []
        
        for parte in partes:
            elemento = parte.strip()
            
            # Detectar elementos vacíos (ej: "q0,,q1")
            if elemento == "":
                return None, (
                    "Error: El campo " + nombre_campo + " contiene un elemento vacío."
                )
            
            elementos.append(elemento)
        
        # ========== VALIDAR DUPLICADOS ==========
        if len(elementos) != len(set(elementos)):
            return None, (
                "Error: El campo " + nombre_campo + " contiene elementos duplicados."
            )
        
        return set(elementos), None



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
        print("El autómata NO cumple con las validaciones. Errores encontrados:")
        for error in errores:
            print("-", error)


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