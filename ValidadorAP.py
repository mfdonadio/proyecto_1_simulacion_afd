"""
ValidadorAP.py — Validación estructural y de determinismo de un Autómata de Pila.

Comprueba la séptupla M = (Q, Σ, Γ, δ, q0, Z0, F) y, si el tipo es APD,
verifica que no haya conflictos de determinismo.

Contrato público
----------------
  validar(ap) -> (bool, list[str])
      True y lista vacía si el AP es estructuralmente válido.
      False y lista de mensajes de error si hay algún problema.
      Actualiza ap.es_valido según el resultado.

Por qué NO se importa ValidadorAFD
-----------------------------------
Las reglas de AP son distintas de las de AFD/AFND en varios puntos clave:
  - EPS es un valor válido como símbolo de entrada de una transición.
  - Los símbolos de pila (Γ) admiten tokens de varios caracteres, como "Z0".
  - δ no necesita ser total; ausencia de transición es semánticamente válida.
  - F puede ser vacío.
  - El determinismo APD incluye prohibir EPS+consumo para el mismo (q, X).
Mezclar los validadores produciría falsos rechazos.
"""

from AutomataPila import EPS


def validar(ap):
    """
    Verifica la corrección estructural de un AutomataPila.

    Orden de comprobaciones (R04, R05):
      1. ap.tipo ∈ {"APD", "APND"}.
      2. q0 ∈ Q.
      3. F ⊆ Q.
      4. Z0 ∈ Γ.
      5. EPS no aparece en Σ ni en Γ.
      6. Para cada transición: origen/destino ∈ Q, entrada ∈ Σ ∪ {EPS},
         tope ∈ Γ, cada token del reemplazo ∈ Γ.
      7. Si tipo == "APD": comprobar determinismo.

    Parámetros
    ----------
    ap : AutomataPila

    Retorna
    -------
    (bool, list[str])
        True, []                  — AP válido; ap.es_valido se pone en True.
        False, [mensajes...]      — AP inválido; ap.es_valido se pone en False.
    """
    errores = []

    # ------------------------------------------------------------------
    # 1. Tipo reconocido
    # ------------------------------------------------------------------
    if ap.tipo not in ("APD", "APND"):
        errores.append(
            "TIPO '{}' no reconocido; debe ser APD o APND.".format(ap.tipo)
        )
        # Sin tipo válido no se puede continuar con determinismo.
        ap.es_valido = False
        return False, errores

    # ------------------------------------------------------------------
    # 2. Estado inicial ∈ Q
    # ------------------------------------------------------------------
    if ap.estado_inicial not in ap.estados:
        errores.append(
            "El estado inicial '{}' no pertenece a Q.".format(ap.estado_inicial)
        )

    # ------------------------------------------------------------------
    # 3. Estados finales ⊆ Q
    # ------------------------------------------------------------------
    ajenos_f = ap.estados_finales - ap.estados
    if ajenos_f:
        errores.append(
            "Estados finales ajenos a Q: {}.".format(sorted(ajenos_f))
        )

    # ------------------------------------------------------------------
    # 4. Símbolo inicial de pila ∈ Γ
    # ------------------------------------------------------------------
    if ap.simbolo_inicial_pila not in ap.alfabeto_pila:
        errores.append(
            "El símbolo inicial de pila '{}' no pertenece a Γ.".format(
                ap.simbolo_inicial_pila
            )
        )

    # ------------------------------------------------------------------
    # 5. EPS no puede estar en Σ ni en Γ (R04.3)
    # ------------------------------------------------------------------
    if EPS in ap.alfabeto:
        errores.append(
            "'{}' está reservado y no puede aparecer en Σ.".format(EPS)
        )
    if EPS in ap.alfabeto_pila:
        errores.append(
            "'{}' está reservado y no puede aparecer en Γ.".format(EPS)
        )

    # ------------------------------------------------------------------
    # 6. Validación de cada transición
    # ------------------------------------------------------------------
    for (origen, entrada, tope), alternativas in ap.transiciones.items():
        prefijo = "Transición ({}, {}, {}):".format(origen, entrada, tope)

        # Origen ∈ Q
        if origen not in ap.estados:
            errores.append(
                "{} estado origen '{}' no pertenece a Q.".format(prefijo, origen)
            )

        # Entrada ∈ Σ ∪ {EPS}
        if entrada != EPS and entrada not in ap.alfabeto:
            errores.append(
                "{} símbolo de entrada '{}' no pertenece a Σ ni es EPS.".format(
                    prefijo, entrada
                )
            )

        # Tope ∈ Γ; nunca EPS
        if tope == EPS:
            errores.append(
                "{} el tope de pila no puede ser EPS.".format(prefijo)
            )
        elif tope not in ap.alfabeto_pila:
            errores.append(
                "{} tope de pila '{}' no pertenece a Γ.".format(prefijo, tope)
            )

        # Cada alternativa: destino ∈ Q; tokens del reemplazo ∈ Γ
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

    # ------------------------------------------------------------------
    # 7. Determinismo APD (R05)
    #    Regla A: cada clave (q, a, X) tiene como máximo una alternativa.
    #    Regla B: si existe δ(q, EPS, X), no puede existir δ(q, a, X)
    #             para ningún a ∈ Σ (independiente de si está en la cadena).
    # ------------------------------------------------------------------
    if ap.tipo == "APD":
        # Regla A — más de una alternativa distinta para la misma clave.
        for clave, alternativas in ap.transiciones.items():
            if len(alternativas) > 1:
                origen, entrada, tope = clave
                errores.append(
                    "APD: conflicto de determinismo en ({}, {}, {}): "
                    "{} alternativas distintas.".format(
                        origen, entrada, tope, len(alternativas)
                    )
                )

        # Regla B — construir el conjunto de parejas (q, X) con transición EPS.
        # Luego buscar si existe alguna transición (q, a, X) con a ∈ Σ.
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

    # ------------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------------
    if errores:
        ap.es_valido = False
        return False, errores

    ap.es_valido = True
    return True, []
