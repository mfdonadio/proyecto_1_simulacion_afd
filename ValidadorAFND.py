"""Validacion estructural de AFND"""

class ValidadorAFND:
    """Comprueba la quintupla de un AFND. No exige completitud segun los lineamientos del proyecto."""

    #Conjunto de simbolos posibles que pueden representar el simbolo de epsilon en la gramatica
    _SIMBOLOS_EPSILON = {"","ε", "ϵ", "λ", "epsilon", "eps", "lambda"}

    #Verificamos que las transiciones sean o no epsilon.
    @staticmethod
    def es_simbolo_epsilon(simbolo):
        """Indica si el texto representa una transicion epsilon."""
        return simbolo.strip().lower() in ValidadorAFND._SIMBOLOS_EPSILON

    #Validamos el AFND
    @staticmethod
    def validar(afnd):
        """Retorna si el AFND es valido y tambien una lita de los posibles errores encontrados luego de revisar toda la estructura."""

        #Inicializamos la lista de errores
        errores = []

        #Validamos que el AFND tenga un nombre
        if not isinstance(afnd.nombre, str) or afnd.nombre.strip() == "":
            errores.append("El AFND no tiene nombre definido.")

        #Validamos los estados del AFND
        if not afnd.estados:
            errores.append("El conjunto de estados Q no puede estar vacio.")

        #Validamos el alfabeto del AFND
        if not afnd.alfabeto:
            errores.append("El alfabeto Σ no puede estar vacio.")

        #Validamos las transiciones epsilon y que las transiciones sean de un solo caracter
        for simbolo in sorted(afnd.alfabeto):
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                errores.append("Las transiciones epsilon no estan permitidas en la fase 2.")
            elif len(simbolo) != 1:
                errores.append("El simbolo " + simbolo + " debe tener exactamente un caracter.")

        #Validamos el estado inicial del AFND
        if afnd.estado_inicial not in afnd.estados:
            errores.append("El estado inicial q0 no pertenece al conjunto Q.")

        #Validamos los estados finales del AFND
        for estado in sorted(afnd.estados_finales):
            if estado not in afnd.estados:
                errores.append("El estado final '" + estado + "' no pertenece al conjunto Q.")

        #Validamos las transiciones del AFND
        for clave, destinos in afnd.transiciones.items():
            if not isinstance(clave, tuple) or len(clave) != 2:
                errores.append("Existe una clave de transición con formato inválido.")
                continue

            #Obtenemos el estado origen y el simbolo de la transicion
            origen, simbolo = clave

            #Si el origen no pertene al conjunto de estados...
            if origen not in afnd.estados:
                errores.append("La transición usa el estado origen inexistente '" + origen + "'.")

            #Si el simbolo es  epsilon...
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                errores.append("No se permiten transiciones epsilon desde '" + origen + "'.")

            #Si el simbolo no pertenece al alfabeto...
            elif simbolo not in afnd.alfabeto:
                errores.append("La transición usa el símbolo inexistente '" + simbolo + "'.")

            #Si los destinos no son un conjunto...
            if not isinstance(destinos, set):
                errores.append("Los destinos de (" + origen + ", " + simbolo + ") deben ser un conjunto.")
            continue

        #Para cada destino de la transicion, verificamos que pertenezca al conjunto de estados
        for destino in sorted(destinos):
            if destino not in afnd.estados:
                errores.append("La transición apunta al estado inexistente '" + destino + "'.")

        #Si len(errores) > 0, el AFND no es valido. Por el contrario, si len(errores) == 0, el AFND es valido.
        afnd.es_valido = len(errores) == 0
        return afnd.es_valido, errores

    @staticmethod
    def validar_alfabeto(alfabeto):
        #Verificamos que exista un alfabeto
        if not alfabeto:
            return "El alfabeto no puede estar vacio."

        for simbolo in alfabeto:

            #Verificamos que no sean epsilon
            if ValidadorAFND.es_simbolo_epsilon(simbolo):
                return "Los simbolos no pueden ser epsilon."

            #Verificamos que su longitud sea exclusivamente 1
            if len(simbolo) != 1:
                return "La longitud de los simbolos debe ser de exactamente 1."

            #Por ultimo, vemos que no hayan espacios en los simbolos
            if simbolo.isspace():
                return "No pueden existir espacios en los simbolos"

        #Si cumple todas las condiciones
        return None


