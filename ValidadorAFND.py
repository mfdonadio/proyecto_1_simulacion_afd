# Aquí validamos la estructura completa de un AFND.

from ValidadorAFD import ValidadorAFD

class ValidadorAFND:
    # Comprobamos la quíntupla del AFND sin exigir que todas las transiciones existan.

    # Estas son las formas reconocidas de escribir epsilon.
    _SIMBOLOS_EPSILON = {"","ε", "ϵ", "λ", "epsilon", "eps", "lambda"}

    # Revisamos si un texto representa una transición epsilon.
    @staticmethod
    def es_simbolo_epsilon(simbolo):
        return isinstance(simbolo, str) and simbolo.strip().lower() in ValidadorAFND._SIMBOLOS_EPSILON

    # Validamos toda la estructura del AFND y reunimos los errores encontrados.
    @staticmethod
    def validar(afnd):
        # Empezamos con una lista vacía y retiramos cualquier validación anterior.
        errores = []
        afnd.es_valido = False

        # Comprobamos los tipos antes de recorrer los componentes.
        for nombre in ("estados", "alfabeto", "estados_finales"):
            componente = getattr(afnd, nombre)
            if not isinstance(componente, set):
                errores.append("El componente " + nombre + " debe ser un conjunto.")
            elif any(not isinstance(elemento, str) for elemento in componente):
                errores.append("Los elementos de " + nombre + " deben ser texto.")
        if not isinstance(afnd.transiciones, dict):
            errores.append("Las transiciones deben ser un diccionario.")
        if not isinstance(afnd.estado_inicial, str):
            errores.append("El estado inicial debe ser texto.")
        if errores:
            return False, errores

        # El AFND necesita un nombre que lo identifique.
        if not isinstance(afnd.nombre, str) or afnd.nombre.strip() == "":
            errores.append("El AFND no tiene nombre definido.")

        # El conjunto Q debe contener estados con nombres válidos.
        if not afnd.estados:
            errores.append("El conjunto de estados Q no puede estar vacio.")
        for estado in afnd.estados:
            error = ValidadorAFD.validar_nombre_estado(estado)
            if error:
                errores.append(repr(estado) + ": " + error)

        # El alfabeto debe contener al menos un símbolo.
        if not afnd.alfabeto:
            errores.append("El alfabeto Σ no puede estar vacio.")

        # Cada símbolo debe ser un carácter distinto de epsilon.
        for simbolo in sorted(afnd.alfabeto):
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                errores.append("Las transiciones epsilon no estan permitidas en la fase 2.")
            elif len(simbolo) != 1:
                errores.append("El simbolo " + simbolo + " debe tener exactamente un caracter.")
            elif simbolo.isspace() or not simbolo.isprintable():
                errores.append("No pueden existir espacios en los simbolos.")

        # El estado inicial debe pertenecer al conjunto Q.
        if afnd.estado_inicial not in afnd.estados:
            errores.append("El estado inicial q0 no pertenece al conjunto Q.")

        # Todos los estados finales deben pertenecer al conjunto Q.
        for estado in sorted(afnd.estados_finales):
            if estado not in afnd.estados:
                errores.append("El estado final '" + estado + "' no pertenece al conjunto Q.")

        # En cada transición validamos el origen, el símbolo y todos sus destinos.
        for clave, destinos in afnd.transiciones.items():
            if not isinstance(clave, tuple) or len(clave) != 2:
                errores.append("Existe una clave de transición con formato inválido.")
                continue

            # Separamos el estado de origen y el símbolo de la transición.
            origen, simbolo = clave
            if not isinstance(origen, str) or not isinstance(simbolo, str):
                errores.append("El origen y el símbolo de una transición deben ser texto.")
                continue

            # El origen debe ser uno de los estados declarados.
            if origen not in afnd.estados:
                errores.append("La transición usa el estado origen inexistente '" + origen + "'.")

            # Las transiciones epsilon no forman parte de esta fase.
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                errores.append("No se permiten transiciones epsilon desde '" + origen + "'.")

            # Cualquier otro símbolo debe pertenecer al alfabeto.
            elif simbolo not in afnd.alfabeto:
                errores.append("La transición usa el símbolo inexistente '" + simbolo + "'.")

            # Los destinos se guardan en un conjunto, incluso si solo hay uno.
            if not isinstance(destinos, set):
                errores.append("Los destinos de (" + origen + ", " + simbolo + ") deben ser un conjunto.")
                continue

            # Cada destino también debe pertenecer al conjunto de estados.
            for destino in destinos:
                if not isinstance(destino, str):
                    errores.append("Los estados destino deben ser texto.")
                elif destino not in afnd.estados:
                    errores.append("La transición apunta al estado inexistente '" + destino + "'.")

        # El AFND solo queda marcado como válido cuando no encontramos errores.
        afnd.es_valido = len(errores) == 0
        return afnd.es_valido, errores

    @staticmethod
    def validar_alfabeto(alfabeto):
        if not isinstance(alfabeto, set):
            return "El alfabeto debe ser un conjunto."
        # El alfabeto debe contener al menos un símbolo.
        if not alfabeto:
            return "El alfabeto no puede estar vacio."

        for simbolo in alfabeto:
            if not isinstance(simbolo, str):
                return "Los símbolos deben ser texto."

            # Epsilon no se acepta como parte del alfabeto.
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                return "Los simbolos no pueden ser epsilon."

            # Cada símbolo debe tener exactamente un carácter.
            if len(simbolo) != 1:
                return "La longitud de los simbolos debe ser de exactamente 1."

            # Tampoco permitimos espacios ni caracteres de control.
            if simbolo.isspace() or not simbolo.isprintable():
                return "No pueden existir espacios en los simbolos"

        # Al llegar aquí, el alfabeto cumple todas las reglas.
        return None


