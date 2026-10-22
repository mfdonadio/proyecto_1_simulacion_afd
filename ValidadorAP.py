# Este validador revisa la séptupla del AP y, cuando es APD, también comprueba
# que sus transiciones sean deterministas. Devuelve el resultado junto con todos
# los errores encontrados y actualiza ap.es_valido.
# Las reglas no se comparten con AFD y AFND: un AP admite transiciones EPS,
# símbolos de pila de varios caracteres, una función parcial y un F vacío.

from AutomataPila import EPS


def validar(ap):
    # Revisamos primero los componentes de la séptupla y después cada transición.
    # Al terminar devolvemos (True, []) o (False, errores) y dejamos es_valido
    # sincronizado con ese resultado.
    errores = []

    # Sin un tipo APD o APND no podemos aplicar las reglas correspondientes.
    if ap.tipo not in ("APD", "APND"):
        errores.append(
            "TIPO '{}' no reconocido; debe ser APD o APND.".format(ap.tipo)
        )
        # Sin tipo válido no se puede continuar con determinismo.
        ap.es_valido = False
        return False, errores

    # Comprobamos que el estado inicial pertenezca a Q.
    if ap.estado_inicial not in ap.estados:
        errores.append(
            "El estado inicial '{}' no pertenece a Q.".format(ap.estado_inicial)
        )

    # Todos los estados finales deben formar un subconjunto de Q.
    ajenos_f = ap.estados_finales - ap.estados
    if ajenos_f:
        errores.append(
            "Estados finales ajenos a Q: {}.".format(sorted(ajenos_f))
        )

    # El símbolo con el que inicia la pila debe pertenecer a Γ.
    if ap.simbolo_inicial_pila not in ap.alfabeto_pila:
        errores.append(
            "El símbolo inicial de pila '{}' no pertenece a Γ.".format(
                ap.simbolo_inicial_pila
            )
        )

    # EPS se reserva para las transiciones y no puede formar parte de Σ ni de Γ.
    if EPS in ap.alfabeto:
        errores.append(
            "'{}' está reservado y no puede aparecer en Σ.".format(EPS)
        )
    if EPS in ap.alfabeto_pila:
        errores.append(
            "'{}' está reservado y no puede aparecer en Γ.".format(EPS)
        )

    # La entrada se recorre carácter por carácter. Por eso cada elemento de Σ
    # debe ser una cadena con exactamente un carácter; Γ conserva tokens como Z0.
    simbolos_entrada_invalidos = [
        simbolo
        for simbolo in ap.alfabeto
        if simbolo != EPS
        and (not isinstance(simbolo, str) or len(simbolo) != 1)
    ]
    if simbolos_entrada_invalidos:
        errores.append(
            "Cada símbolo de Σ debe ser una cadena de exactamente un carácter; "
            "se encontró: {}.".format(
                ", ".join(
                    repr(simbolo)
                    for simbolo in sorted(simbolos_entrada_invalidos, key=repr)
                )
            )
        )

    # Ahora validamos el origen, la entrada, el tope y cada alternativa de δ.
    for (origen, entrada, tope), alternativas in ap.transiciones.items():
        prefijo = "Transición ({}, {}, {}):".format(origen, entrada, tope)

        # El estado de origen debe pertenecer a Q.
        if origen not in ap.estados:
            errores.append(
                "{} estado origen '{}' no pertenece a Q.".format(prefijo, origen)
            )

        # La entrada debe ser un símbolo de Σ o EPS.
        if entrada != EPS and entrada not in ap.alfabeto:
            errores.append(
                "{} símbolo de entrada '{}' no pertenece a Σ ni es EPS.".format(
                    prefijo, entrada
                )
            )

        # El tope debe pertenecer a Γ y nunca puede ser EPS.
        if tope == EPS:
            errores.append(
                "{} el tope de pila no puede ser EPS.".format(prefijo)
            )
        elif tope not in ap.alfabeto_pila:
            errores.append(
                "{} tope de pila '{}' no pertenece a Γ.".format(prefijo, tope)
            )

        # En cada alternativa, el destino pertenece a Q y el reemplazo usa Γ.
        for destino, reemplazo in alternativas:
            if destino not in ap.estados:
                errores.append(
                    "{} estado destino '{}' no pertenece a Q.".format(
                        prefijo, destino
                    )
                )
            for token in reemplazo:
                if token not in ap.alfabeto_pila:
                    errores.append(
                        "{} token de reemplazo '{}' no pertenece a Γ.".format(
                            prefijo, token
                        )
                    )

    # En un APD cada clave puede tener una sola alternativa. Además, si existe
    # δ(q, EPS, X), no puede coexistir δ(q, a, X) para ningún símbolo de Σ.
    if ap.tipo == "APD":
        # Primero rechazamos las claves que tengan más de una alternativa distinta.
        for clave, alternativas in ap.transiciones.items():
            if len(alternativas) > 1:
                origen, entrada, tope = clave
                errores.append(
                    "APD: conflicto de determinismo en ({}, {}, {}): "
                    "{} alternativas distintas.".format(
                        origen, entrada, tope, len(alternativas)
                    )
                )

        # Después reunimos las parejas (q, X) con transición EPS y comprobamos
        # que ninguna de ellas tenga también una transición que consuma entrada.
        parejas_con_eps = set()
        for (origen, entrada, tope) in ap.transiciones:
            if entrada == EPS:
                parejas_con_eps.add((origen, tope))

        for (origen, entrada, tope) in ap.transiciones:
            if entrada != EPS and (origen, tope) in parejas_con_eps:
                errores.append(
                    "APD: conflicto EPS/consumo en estado '{}', tope '{}': "
                    "existe δ({}, EPS, {}) y δ({}, {}, {}).".format(
                        origen, tope, origen, tope, origen, entrada, tope
                    )
                )

    # El indicador es_valido siempre refleja el resultado de esta revisión.
    if errores:
        ap.es_valido = False
        return False, errores

    ap.es_valido = True
    return True, []
