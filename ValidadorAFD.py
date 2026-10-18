class ValidadorAFD:
    # Comprobamos que cada componente del AFD cumpla su definición formal.

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
    def validar_nombre_estado(estado):
        # Usamos la misma regla para los nombres en cargadores y validadores.
        if not isinstance(estado, str) or not estado:
            return "El nombre de un estado debe ser texto no vacío."
        # Estos textos ya tienen un significado en el formato de destinos.
        if estado in ("∅", "{}") or any(caracter in ",|" for caracter in estado):
            return "Nombre reservado: , y | separan elementos; ∅ y {} indican ausencia de destinos."
        if any(caracter.isspace() or not caracter.isprintable() for caracter in estado):
            return "El nombre de un estado no admite espacios ni caracteres de control en las transiciones."
        return None

    @staticmethod
    def es_simbolo_epsilon(simbolo):
        # Reconocemos las formas de escribir epsilon, que no se permite en un AFD.
        return isinstance(simbolo, str) and simbolo.strip().lower() in ValidadorAFD._SIMBOLOS_EPSILON

    @staticmethod
    def obtener_transiciones_faltantes(afd):
        # Buscamos las parejas de estado y símbolo que no tienen una transición.
        faltantes = []

        # Solo buscamos parejas cuando sus componentes tienen tipos válidos.
        if not isinstance(afd.estados, set) or not isinstance(afd.alfabeto, set):
            return faltantes
        if not isinstance(afd.transiciones, dict):
            return faltantes
        if any(not isinstance(estado, str) for estado in afd.estados):
            return faltantes
        if any(not isinstance(simbolo, str) for simbolo in afd.alfabeto):
            return faltantes

        for estado in sorted(afd.estados):
            for simbolo in sorted(afd.alfabeto):
                if (estado, simbolo) not in afd.transiciones:
                    faltantes.append((estado, simbolo))

        return faltantes
    
    @staticmethod
    def validar(afd):
        # Revisamos toda la estructura y devolvemos su validez junto con los errores.
        errores = []
        afd.es_valido = False

        # Comprobamos los tipos antes de recorrer los componentes.
        for nombre in ("estados", "alfabeto", "estados_finales"):
            componente = getattr(afd, nombre)
            if not isinstance(componente, set):
                errores.append("El componente " + nombre + " debe ser un conjunto.")
            elif any(not isinstance(elemento, str) for elemento in componente):
                errores.append("Los elementos de " + nombre + " deben ser texto.")
        if not isinstance(afd.transiciones, dict):
            errores.append("Las transiciones deben ser un diccionario.")
        if not isinstance(afd.transiciones_repetidas, list):
            errores.append("Las transiciones repetidas deben ser una lista.")
        if not isinstance(afd.estado_inicial, str):
            errores.append("El estado inicial debe ser texto.")
        if errores:
            return False, errores
        
        # Los componentes básicos deben existir y usar valores permitidos.
        # Un AFD debe tener un identificador
        if not isinstance(afd.nombre, str) or afd.nombre.strip() == "":
            errores.append("El automata no tiene un nombre definido o un identificador.")
        
        # Q (conjunto de estados) no puede estar vacío
        if len(afd.estados) == 0:
            errores.append("El conjunto de estados Q no puede estar vacío.")
        for estado in afd.estados:
            error = ValidadorAFD.validar_nombre_estado(estado)
            if error:
                errores.append(repr(estado) + ": " + error)
        
        # Σ (alfabeto) no puede estar vacío
        if len(afd.alfabeto) == 0:
            errores.append("El alfabeto Σ no puede estar vacío.")

        # Cada símbolo del alfabeto debe ser un carácter distinto de epsilon.
        for simbolo in afd.alfabeto:
            if ValidadorAFD.es_simbolo_epsilon(simbolo):
                errores.append(
                    "El alfabeto de un AFD no puede contener ε, "
                    "porque representa la cadena vacía."
                )
            elif len(simbolo) != 1 or not simbolo.isprintable() or simbolo.isspace():
                errores.append(
                    "El símbolo '"
                    + simbolo
                    + "' no es válido: cada símbolo del alfabeto "
                    + "debe tener exactamente un carácter."
                )
        
        # El estado inicial q0 debe pertenecer al conjunto Q.
        if afd.estado_inicial not in afd.estados:
            errores.append("El estado inicial q0 no pertenece al conjunto de estados Q.")
        
        # Todos los estados finales F deben pertenecer al conjunto Q.
        for estado_final in afd.estados_finales:
            if estado_final not in afd.estados:
                errores.append(
                    "El estado final " + estado_final + " no pertenece al conjunto Q."
                )
        
        # Revisamos que cada parte de una transición pertenezca al componente correcto.
        # Cada transición δ(q, a) = q' debe cumplir:
        # - q ∈ Q (origen en estados)
        # - a ∈ Σ (símbolo en alfabeto)
        # - q' ∈ Q (destino en estados)
        for clave, estado_destino in afd.transiciones.items():
            if not isinstance(clave, tuple) or len(clave) != 2:
                errores.append("Existe una clave de transición con formato inválido.")
                continue
            estado_origen, simbolo = clave
            if not isinstance(estado_origen, str) or not isinstance(simbolo, str):
                errores.append("El origen y el símbolo de una transición deben ser texto.")
                continue
            if not isinstance(estado_destino, str):
                errores.append("El estado destino de un AFD debe ser texto.")
                continue
            
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
        
        # Una pareja de estado y símbolo no puede llevar a destinos distintos.
        # Un AFD debe ser determinista: no puede haber dos transiciones
        # diferentes para la misma pareja (estado, símbolo)
        for repetida in afd.transiciones_repetidas:
            if (
                not isinstance(repetida, tuple)
                or len(repetida) != 3
                or any(not isinstance(elemento, str) for elemento in repetida)
            ):
                errores.append("Existe una transición repetida con formato inválido.")
                continue
            estado_origen, simbolo, estado_destino = repetida
            clave = (estado_origen, simbolo)
            # Revisamos también las referencias de las líneas que no entraron en δ.
            if estado_origen not in afd.estados:
                errores.append("Transición repetida con origen inexistente: " + estado_origen)
            if simbolo not in afd.alfabeto:
                errores.append("Transición repetida con símbolo inexistente: " + simbolo)
            if estado_destino not in afd.estados:
                errores.append("Transición repetida con destino inexistente: " + estado_destino)
            if clave not in afd.transiciones:
                errores.append("Transición repetida sin una transición original.")
            elif afd.transiciones[clave] == estado_destino:
                errores.append("Transición duplicada idéntica: " + repr(repetida)
                               + ". Error de formato; no introduce no determinismo.")
            else:
                errores.append("No es determinista: destinos distintos para " + repr(clave) + ".")
        
        # Un AFD completo necesita una transición para cada pareja posible.
        faltantes = ValidadorAFD.obtener_transiciones_faltantes(afd)

        for estado_origen, simbolo in faltantes:
            errores.append(
                "Falta la transición δ("
                + estado_origen
                + ", "
                + simbolo
                + ")."
            )
        
        # El AFD solo queda marcado como válido cuando no encontramos errores.
        afd.es_valido = len(errores) == 0
        
        return afd.es_valido, errores

    @staticmethod
    def analizar_estructura(afd):
        # Recorremos el AFD desde q0 para encontrar estados alcanzables e inaccesibles.
        
        # Usamos una búsqueda en profundidad para encontrar los estados alcanzables.
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
        
        # Con el recorrido terminado, calculamos los resultados del análisis.
        # Los estados inaccesibles son aquellos a los que no se puede llegar desde q0.
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
        # Enviamos las transiciones faltantes a un estado trampa con ciclos propios.
        # No completamos una definición con otros errores ni creamos nombres inválidos.
        if ValidadorAFD.clasificar(afd) != "AFD INCOMPLETO":
            return None, 0
        error = ValidadorAFD.validar_nombre_estado(nombre_base)
        if error:
            raise ValueError(error)
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

    @staticmethod
    def clasificar(afd):
        # Al clasificar, priorizamos datos inválidos, no determinismo e incompletitud.

        valido, errores = ValidadorAFD.validar(afd)

        if valido:
            return "AFD VÁLIDO"

        # Una referencia inválida tiene prioridad aunque también falten transiciones
        # o existan destinos distintos. Una duplicación idéntica es error de formato.
        if any(not error.startswith(("Falta la transición δ(", "No es determinista:"))
               for error in errores):
            return "AFD INVÁLIDO"
        if any(error.startswith("No es determinista:") for error in errores):
            return "DEFINICIÓN NO DETERMINISTA"
        return "AFD INCOMPLETO"
