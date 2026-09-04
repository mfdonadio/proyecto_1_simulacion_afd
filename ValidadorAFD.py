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

    _SIMBOLOS_EPSILON = {
        "",
        "ε",
        "ϵ",
        "λ",
        "epsilon",
        "eps",
        "lambda",
    }
    @staticmethod
    def es_simbolo_epsilon(simbolo):
        """
        Determina si un valor representa la cadena vacía o una
        transición epsilon, la cual no está permitida en un AFD.
        """
        return simbolo.strip().lower() in ValidadorAFD._SIMBOLOS_EPSILON

    @staticmethod
    def obtener_transiciones_faltantes(afd):
        """
        Retorna todas las parejas (estado, símbolo) para las cuales
        la función de transición no está definida.
        """
        faltantes = []

        for estado in sorted(afd.estados):
            for simbolo in sorted(afd.alfabeto):
                if (estado, simbolo) not in afd.transiciones:
                    faltantes.append((estado, simbolo))

        return faltantes
    
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

        # ========== VALIDAR SÍMBOLOS DEL ALFABETO ==========
        for simbolo in afd.alfabeto:
            if ValidadorAFD.es_simbolo_epsilon(simbolo):
                errores.append(
                    "El alfabeto de un AFD no puede contener ε, "
                    "porque representa la cadena vacía."
                )
            elif len(simbolo) != 1:
                errores.append(
                    "El símbolo '"
                    + simbolo
                    + "' no es válido: cada símbolo del alfabeto "
                    + "debe tener exactamente un carácter."
                )
        
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
            if ValidadorAFD.es_simbolo_epsilon(simbolo):
                errores.append(
                    "No se permiten transiciones ε en un AFD: "
                    + estado_origen
                    + " --ε--> "
                    + estado_destino
                    + "."
                )
            elif simbolo not in afd.alfabeto:
                errores.append(
                    "La transición usa el símbolo inexistente '" + simbolo + "'."
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
        faltantes = ValidadorAFD.obtener_transiciones_faltantes(afd)

        for estado_origen, simbolo in faltantes:
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


    @staticmethod
    def completar_con_estado_trampa(afd, nombre_base="q_trampa"):
        """
        Completa las transiciones faltantes enviándolas a un nuevo
        estado trampa. El estado trampa posee ciclos para todos los
        símbolos del alfabeto.

        Retorna:
            Tupla (nombre_estado_trampa, cantidad_transiciones_completadas)
        """
        faltantes = ValidadorAFD.obtener_transiciones_faltantes(afd)

        if len(faltantes) == 0:
            return None, 0

        # Buscar un nombre que no colisione con estados existentes
        nombre_trampa = nombre_base
        contador = 1

        while nombre_trampa in afd.estados:
            nombre_trampa = nombre_base + "_" + str(contador)
            contador += 1

        # Agregar el nuevo estado a Q
        afd.estados.add(nombre_trampa)

        # Dirigir todas las transiciones faltantes hacia el estado trampa
        for estado, simbolo in faltantes:
            afd.agregar_transicion(
                estado,
                simbolo,
                nombre_trampa
            )

        # El estado trampa debe regresar a sí mismo con cualquier símbolo
        for simbolo in afd.alfabeto:
            afd.agregar_transicion(
                nombre_trampa,
                simbolo,
                nombre_trampa
            )

        afd.es_valido = False

        return nombre_trampa, len(faltantes)