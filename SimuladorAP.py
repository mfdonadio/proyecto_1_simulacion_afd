# Este simulador recorre por niveles las ramas de un APD o APND.
# La pila interna es persistente e inmutable, con el tope en el primer nodo;
# los testigos públicos conservan tuplas con el tope en el índice 0.
# Una cadena se acepta cuando se consumió completa y el estado es final,
# sin exigir que la pila quede vacía.

import collections
from dataclasses import dataclass, field
from typing import Optional

from AutomataPila import EPS


# Estos cuatro estados distinguen un rechazo real de un límite de recursos.
ACEPTADA            = "ACEPTADA"
RECHAZADA           = "RECHAZADA"
DETENIDA_POR_LIMITE = "DETENIDA_POR_LIMITE"
ENTRADA_INVALIDA    = "ENTRADA_INVALIDA"


# Nodo interno de una pila persistente. La igualdad por identidad es correcta
# porque cada evaluación reutiliza un único nodo para cada par (símbolo, resto).
# Así, ramas con el mismo contenido pueden compartir memoria sin poder mutarse.
class _NodoPila:
    __slots__ = ("simbolo", "resto")

    def __init__(self, simbolo, resto):
        self.simbolo = simbolo
        self.resto = resto


def _apilar_tokens(tokens, fondo, cache_pilas):
    pila = fondo
    for simbolo in reversed(tokens):
        clave = (simbolo, pila)
        nodo = cache_pilas.get(clave)
        if nodo is None:
            nodo = _NodoPila(simbolo, pila)
            cache_pilas[clave] = nodo
        pila = nodo
    return pila


def _pila_interna_a_tupla(pila):
    simbolos = []
    actual = pila
    while actual is not None:
        simbolos.append(actual.simbolo)
        actual = actual.resto
    return tuple(simbolos)


# Reúne el veredicto, los contadores y el camino que demuestra una aceptación.
@dataclass
class ResultadoSimulacion:
    estado_resultado: str
    motivo: str
    cadena: str
    admitidas: int
    procesadas: int
    generadas: int
    podadas_limite: int
    limite_usado: int
    pasos: list = field(default_factory=list)
    id_nodo_aceptador: Optional[int] = None
    camino_testigo: list = field(default_factory=list)


# Cada nodo conserva su padre para reconstruir el camino y comprobar si una
# configuración anterior pertenece a esa misma rama sin copiar sus ancestros.
def _crear_nodo(nodo_id, id_padre, id_rama, profundidad,
                estado, posicion, pila, transicion, datos_transicion):
    return {
        "id": nodo_id,
        "id_padre": id_padre,
        "id_rama": id_rama,
        "profundidad": profundidad,
        "estado": estado,
        "posicion": posicion,
        "pila": pila,
        "transicion": transicion,
        "datos_transicion": datos_transicion,
    }


# Comprueba la relación de ascendencia usando las profundidades y los enlaces
# de padre. El índice global solo localiza configuraciones iguales: una
# coincidencia de otra rama no se trata como ciclo.
def _es_ancestro(id_candidato, nodo, nodos_por_id):
    candidato = nodos_por_id[id_candidato]
    if candidato["profundidad"] > nodo["profundidad"]:
        return False

    actual = nodo
    while actual["profundidad"] > candidato["profundidad"]:
        actual = nodos_por_id[actual["id_padre"]]

    return actual["id"] == id_candidato


def _configuracion_en_camino(configuracion, nodo, ids_por_configuracion,
                             nodos_por_id):
    for id_candidato in ids_por_configuracion.get(configuracion, ()):
        if _es_ancestro(id_candidato, nodo, nodos_por_id):
            return True
    return False

# Seguimos los padres desde el nodo aceptador y luego invertimos el recorrido.
def _reconstruir_testigo(nodo_aceptador, nodos_por_id):
    camino = []
    nodo_actual = nodo_aceptador
    while nodo_actual is not None:
        camino.append(nodo_actual)
        id_padre = nodo_actual["id_padre"]
        nodo_actual = nodos_por_id.get(id_padre)  # None cuando id_padre es None (raíz)
    camino.reverse()

    # El detalle interno de la pila compartida no forma parte del resultado
    # público. Solo el camino aceptador, normalmente pequeño, se materializa.
    camino_publico = []
    for nodo in camino:
        copia = dict(nodo)
        copia["pila"] = _pila_interna_a_tupla(nodo["pila"])
        camino_publico.append(copia)
    return camino_publico

# Convertimos la transición al texto que después utiliza la tabla del testigo.
def _texto_transicion(entrada, tope, destino, reemplazo):
    if reemplazo:
        texto_remp = ";".join(reemplazo)
    else:
        texto_remp = EPS  # reemplazo vacío = desapilar
    return "({}, {}) -> ({}, {})".format(entrada, tope, destino, texto_remp)


# Evalúa la cadena con BFS y devuelve un ResultadoSimulacion.
# El límite cuenta configuraciones admitidas e incluye el nodo inicial.
def evaluar(ap, cadena, limite=10000, mostrar_traza=True):
    # Parámetro conservado por compatibilidad. evaluar() siempre es el núcleo
    # silencioso; evaluar_y_mostrar() se encarga de presentar la traza.
    _ = mostrar_traza

    # Defensa ante modelos antiguos o modificados sin revalidar: el motor avanza
    # por caracteres, así que no puede interpretar símbolos de entrada más largos.
    simbolos_entrada_invalidos = [
        simbolo
        for simbolo in ap.alfabeto
        if not isinstance(simbolo, str) or len(simbolo) != 1
    ]
    if simbolos_entrada_invalidos:
        return ResultadoSimulacion(
            estado_resultado=ENTRADA_INVALIDA,
            motivo=(
                "Alfabeto de entrada inválido: cada símbolo de Σ debe ser una "
                "cadena de exactamente un carácter; se encontró: {}."
            ).format(
                ", ".join(
                    repr(simbolo)
                    for simbolo in sorted(simbolos_entrada_invalidos, key=repr)
                )
            ),
            cadena=cadena,
            admitidas=0,
            procesadas=0,
            generadas=0,
            podadas_limite=0,
            limite_usado=limite,
        )

    # Sin la marca de validación no iniciamos la exploración.
    if not ap.es_valido:
        return ResultadoSimulacion(
            estado_resultado=ENTRADA_INVALIDA,
            motivo="AP no validado; ejecutar ValidadorAP.validar(ap) antes de simular.",
            cadena=cadena,
            admitidas=0,
            procesadas=0,
            generadas=0,
            podadas_limite=0,
            limite_usado=limite,
        )

    # La cadena vacía es válida; cualquier otro símbolo debe pertenecer a Σ.
    simbolos_invalidos = [s for s in cadena if s not in ap.alfabeto]
    if simbolos_invalidos:
        invalidos_unicos = sorted(set(simbolos_invalidos))
        return ResultadoSimulacion(
            estado_resultado=ENTRADA_INVALIDA,
            motivo="Símbolo(s) fuera de Σ: {}.".format(", ".join(invalidos_unicos)),
            cadena=cadena,
            admitidas=0,
            procesadas=0,
            generadas=0,
            podadas_limite=0,
            limite_usado=limite,
        )

    # El presupuesto debe ser un entero positivo y los booleanos no cuentan.
    if not isinstance(limite, int) or isinstance(limite, bool) or limite <= 0:
        return ResultadoSimulacion(
            estado_resultado=ENTRADA_INVALIDA,
            motivo="El límite debe ser un entero positivo (se recibió: {!r}).".format(limite),
            cadena=cadena,
            admitidas=0,
            procesadas=0,
            generadas=0,
            podadas_limite=0,
            limite_usado=limite,
        )

    longitud = len(cadena)

    # La raíz representa el estado inicial, la posición cero y la pila con Z0.
    cache_pilas = {}
    pila_inicial = _apilar_tokens(
        (ap.simbolo_inicial_pila,), None, cache_pilas
    )
    nodo_raiz = _crear_nodo(
        nodo_id=0,
        id_padre=None,
        id_rama=0,
        profundidad=0,
        estado=ap.estado_inicial,
        posicion=0,
        pila=pila_inicial,
        transicion=None,
        datos_transicion=None,
    )

    cola = collections.deque([nodo_raiz])

    # Relacionamos cada identificador con su nodo para reconstruir el testigo.
    nodos_por_id = {0: nodo_raiz}

    # Este índice evita recorrer y copiar todos los ancestros de cada nodo.
    # No elimina configuraciones globalmente: solo permite buscar candidatos
    # iguales y luego confirmar que pertenezcan al camino de la rama actual.
    config_raiz = (
        nodo_raiz["estado"], nodo_raiz["posicion"], nodo_raiz["pila"]
    )
    ids_por_configuracion = {config_raiz: [0]}

    # El siguiente contador asigna un identificador distinto a cada nodo.
    siguiente_id = 1

    # Estos contadores permiten explicar cuánto trabajo realizó la exploración.
    admitidas = 1      # La raíz ya fue admitida al encolarse.
    procesadas = 0
    generadas = 0
    podadas_limite = 0
    hubo_poda = False  # True si se omitió al menos un nodo por presupuesto.

    # Guardamos los eventos que después se muestran en la traza y el diagnóstico.
    pasos = []

    # Procesamos las configuraciones por niveles hasta aceptar o vaciar la cola.
    while cola:
        nodo = cola.popleft()
        procesadas += 1

        estado   = nodo["estado"]
        posicion = nodo["posicion"]
        pila     = nodo["pila"]

        # Comprobamos primero la aceptación porque no depende del contenido de la pila.
        if posicion == longitud and estado in ap.estados_finales:
            testigo = _reconstruir_testigo(nodo, nodos_por_id)
            pasos.append({
                "tipo": "aceptacion",
                "id_nodo": nodo["id"],
                "id_padre": nodo["id_padre"],
                "id_rama": nodo["id_rama"],
                "profundidad": nodo["profundidad"],
                "estado": estado,
                "posicion": posicion,
                "pila": _pila_interna_a_tupla(pila),
            })

            # BFS puede dejar nodos admitidos en la cola cuando encuentra el
            # primer testigo. Se identifican como pendientes, no rechazados.
            for pendiente in cola:
                pasos.append({
                    "tipo": "rama_pendiente_por_aceptacion",
                    "id_nodo": pendiente["id"],
                    "id_padre": pendiente["id_padre"],
                    "id_rama": pendiente["id_rama"],
                    "profundidad": pendiente["profundidad"],
                    "estado": pendiente["estado"],
                    "posicion": pendiente["posicion"],
                    "pila": pendiente["pila"],
                })
            return ResultadoSimulacion(
                estado_resultado=ACEPTADA,
                motivo="Entrada consumida con estado final '{}'.".format(estado),
                cadena=cadena,
                admitidas=admitidas,
                procesadas=procesadas,
                generadas=generadas,
                podadas_limite=podadas_limite,
                limite_usado=limite,
                pasos=pasos,
                id_nodo_aceptador=nodo["id"],
                camino_testigo=testigo,
            )

        # Sin tope no se puede aplicar otra transición; si no aceptó, la rama termina.
        if not pila:
            pasos.append({
                "tipo": "rama_muerta_pila_vacia",
                "id_nodo": nodo["id"],
                "id_padre": nodo["id_padre"],
                "id_rama": nodo["id_rama"],
                "profundidad": nodo["profundidad"],
                "estado": estado,
                "posicion": posicion,
                "pila": None,
            })
            continue

        tope = pila.simbolo

        # Revisamos primero EPS y luego consumo, respetando el orden declarado.
        alternativas = []

        # Agregamos primero las transiciones EPS, que no avanzan la posición.
        for destino, reemplazo in ap.obtener_alternativas(estado, EPS, tope):
            alternativas.append((EPS, destino, reemplazo))

        # Si queda entrada, agregamos después las transiciones que la consumen.
        if posicion < longitud:
            simbolo = cadena[posicion]
            for destino, reemplazo in ap.obtener_alternativas(estado, simbolo, tope):
                alternativas.append((simbolo, destino, reemplazo))

        if not alternativas:
            # Ninguna transición aplicable: rama muerta por bloqueo.
            pasos.append({
                "tipo": "rama_muerta_bloqueada",
                "id_nodo": nodo["id"],
                "id_padre": nodo["id_padre"],
                "id_rama": nodo["id_rama"],
                "profundidad": nodo["profundidad"],
                "estado": estado,
                "posicion": posicion,
                "pila": pila,
            })
            continue

        for entrada, destino, reemplazo in alternativas:
            generadas += 1

            # La posición solo avanza cuando la transición consume un símbolo.
            if entrada == EPS:
                nueva_posicion = posicion
            else:
                nueva_posicion = posicion + 1

            # El reemplazo se inserta en lugar del tope. Como el índice 0 es
            # la cima, su primer token queda arriba; () representa desapilar.
            nueva_pila = _apilar_tokens(reemplazo, pila.resto, cache_pilas)

            config_nueva = (destino, nueva_posicion, nueva_pila)

            # Solo cerramos un ciclo si estado, posición y pila completa ya
            # aparecieron en esta rama. Configuraciones de ramas hermanas no se
            # confunden, y un auto-bucle se reconoce sin gastar presupuesto.
            if _configuracion_en_camino(
                    config_nueva, nodo, ids_por_configuracion, nodos_por_id):
                pasos.append({
                    "tipo": "ciclo_detectado",
                    "id_nodo": nodo["id"],
                    "id_padre": nodo["id_padre"],
                    "id_rama": nodo["id_rama"],
                    "profundidad": nodo["profundidad"],
                    "estado": estado,
                    "posicion": posicion,
                    "pila": pila,
                    "config_repetida": (
                        config_nueva[0], config_nueva[1],
                        _pila_interna_a_tupla(config_nueva[2]),
                    ),
                    "entrada": entrada,
                    "tope": tope,
                    "destino": destino,
                    "reemplazo": reemplazo,
                })
                continue

            # Limitamos al admitir para acotar la frontera. Los nodos que ya
            # entraron en la cola se procesan porque todavía pueden aceptar.
            if admitidas < limite:
                id_hijo = siguiente_id
                siguiente_id += 1

                # Cuando hay varias alternativas, cada hija recibe una rama propia.
                if len(alternativas) > 1:
                    id_rama_hijo = id_hijo
                else:
                    # Única continuación: hereda la rama del padre.
                    id_rama_hijo = nodo["id_rama"]

                datos_transicion = {
                    "entrada": entrada,
                    "tope": tope,
                    "destino": destino,
                    "reemplazo": reemplazo,
                }

                descripcion_trans = _texto_transicion(
                    entrada, tope, destino, reemplazo
                )

                nodo_hijo = _crear_nodo(
                    nodo_id=id_hijo,
                    id_padre=nodo["id"],
                    id_rama=id_rama_hijo,
                    profundidad=nodo["profundidad"] + 1,
                    estado=destino,
                    posicion=nueva_posicion,
                    pila=nueva_pila,
                    transicion=descripcion_trans,
                    datos_transicion=datos_transicion,
                )

                nodos_por_id[id_hijo] = nodo_hijo
                ids_por_configuracion.setdefault(config_nueva, []).append(id_hijo)
                admitidas += 1
                cola.append(nodo_hijo)

                pasos.append({
                    "tipo": "expansion",
                    "id_padre": nodo["id"],
                    "id_hijo": id_hijo,
                    "id_rama": id_rama_hijo,
                    "profundidad": nodo_hijo["profundidad"],
                    "estado_origen": estado,
                    "posicion_antes": posicion,
                    "pila_antes": pila,
                    "entrada": entrada,
                    "tope": tope,
                    "destino": destino,
                    "reemplazo": reemplazo,
                    "nueva_posicion": nueva_posicion,
                    "nueva_pila": nueva_pila,
                })

            else:
                # Presupuesto agotado: no se puede admitir esta alternativa.
                # Se registra la poda pero no se aborta; las configuraciones
                # ya admitidas pueden contener aceptación y se siguen procesando.
                podadas_limite += 1
                hubo_poda = True
                pasos.append({
                    "tipo": "podada_por_limite",
                    "id_padre": nodo["id"],
                    "id_rama": nodo["id_rama"],
                    "profundidad": nodo["profundidad"] + 1,
                    "estado_origen": estado,
                    "posicion_antes": posicion,
                    "pila_antes": pila,
                    "entrada": entrada,
                    "tope": tope,
                    "destino": destino,
                    "reemplazo": reemplazo,
                    "nueva_posicion": nueva_posicion,
                    "nueva_pila": nueva_pila,
                    "limite": limite,
                })

    # Una poda por presupuesto deja el resultado inconcluso; sin podas, el
    # agotamiento de todas las ramas sí permite responder RECHAZADA.
    if hubo_poda:
        detalle_poda = (
            "1 alternativa no explorada"
            if podadas_limite == 1
            else "{} alternativas no exploradas".format(podadas_limite)
        )
        motivo = (
            "Presupuesto de {} configuraciones agotado; "
            "{}.".format(limite, detalle_poda)
        )
        return ResultadoSimulacion(
            estado_resultado=DETENIDA_POR_LIMITE,
            motivo=motivo,
            cadena=cadena,
            admitidas=admitidas,
            procesadas=procesadas,
            generadas=generadas,
            podadas_limite=podadas_limite,
            limite_usado=limite,
            pasos=pasos,
        )
    else:
        return ResultadoSimulacion(
            estado_resultado=RECHAZADA,
            motivo="Se agotaron todas las posibilidades sin encontrar aceptación.",
            cadena=cadena,
            admitidas=admitidas,
            procesadas=procesadas,
            generadas=generadas,
            podadas_limite=0,
            limite_usado=limite,
            pasos=pasos,
        )


# Muestra el resumen y el recorrido realmente explorado. Las entradas inválidas
# no tienen recorrido porque se detectan antes de crear la configuración raíz.
def mostrar_traza(resultado, ap):
    print()
    print("=" * 62)
    print("RESULTADO DE SIMULACIÓN — {}".format(ap.nombre))
    print("=" * 62)
    print("Cadena evaluada : {!r}".format(resultado.cadena))
    print("Resultado       : {}".format(resultado.estado_resultado))
    print("Motivo          : {}".format(resultado.motivo))
    print("Límite usado    : {}".format(resultado.limite_usado))
    print("Configuraciones admitidas  : {}".format(resultado.admitidas))
    print("Configuraciones procesadas : {}".format(resultado.procesadas))
    print("Alternativas generadas     : {}".format(resultado.generadas))
    print("Alternativas podadas       : {}".format(resultado.podadas_limite))

    if resultado.estado_resultado == ENTRADA_INVALIDA:
        print()
        print("No se inició un recorrido: la entrada o la configuración es inválida.")
    else:
        print()
        print("Convención de pila: tope → fondo (el tope es el primer token).")
        if resultado.camino_testigo:
            ids_testigo = [str(nodo["id"]) for nodo in resultado.camino_testigo]
            print("Camino testigo (nodos): {}".format(" -> ".join(ids_testigo)))
        _imprimir_recorrido(resultado, ap)

    if resultado.estado_resultado == DETENIDA_POR_LIMITE:
        print()
        print("Nota: el presupuesto se agotó antes de completar la exploración.")
        print("      No se puede afirmar rechazo; puede haber cadenas aceptadas")
        print("      en las ramas no exploradas.")
    elif resultado.estado_resultado == RECHAZADA:
        print()
        print("Conclusión: todas las ramas explorables cerraron sin aceptar.")

    print("=" * 62)

# Devuelve el sufijo de entrada visible en una configuración.
def _entrada_restante(cadena, posicion):
    if posicion < len(cadena):
        return cadena[posicion:]
    return "ε"


# Las exploraciones grandes se resumen antes de convertir pilas a texto. Todos
# los eventos permanecen disponibles en ResultadoSimulacion.pasos.
def _seleccionar_eventos(eventos):
    if len(eventos) <= 50:
        return list(eventos), 0
    seleccion = list(eventos[:25]) + [None] + list(eventos[-10:])
    return seleccion, len(eventos) - 35


def _avisar_resumen(nombre, total, omitidos):
    if omitidos:
        print(
            "[AVISO] {} contiene {} eventos; se muestran los primeros 25 y "
            "los últimos 10 ({} omitidos en pantalla).".format(
                nombre, total, omitidos
            )
        )
        print("        El detalle estructurado completo se conserva en resultado.pasos.")


def _imprimir_tabla(encabezados, filas):
    anchos = [len(enc) for enc in encabezados]
    for fila in filas:
        for j, celda in enumerate(fila):
            if len(celda) > anchos[j]:
                anchos[j] = len(celda)

    sep = " | "
    linea_enc = sep.join(enc.ljust(anchos[k]) for k, enc in enumerate(encabezados))
    print(linea_enc)
    print("-" * len(linea_enc))
    for fila in filas:
        print(sep.join(celda.ljust(anchos[k]) for k, celda in enumerate(fila)))


def _imprimir_recorrido(resultado, ap):
    print("\n--- RECORRIDO DE EXPLORACIÓN ---")
    expansiones = [p for p in resultado.pasos if p["tipo"] == "expansion"]
    seleccion, omitidos = _seleccionar_eventos(expansiones)
    _avisar_resumen("El recorrido", len(expansiones), omitidos)

    ids_testigo = {nodo["id"] for nodo in resultado.camino_testigo}
    cadena = resultado.cadena
    pila_raiz = (ap.simbolo_inicial_pila,)
    filas = [[
        "0", "0", "-", "0", ap.estado_inicial,
        _entrada_restante(cadena, 0), _pila_a_texto(pila_raiz),
        "-", pila_raiz[0], "-", "-", "-",
        "TESTIGO" if 0 in ids_testigo else "INICIAL",
    ]]

    for evento in seleccion:
        if evento is None:
            filas.append(["..."] * 13)
            continue
        reemplazo = (
            ";".join(evento["reemplazo"])
            if evento["reemplazo"] else EPS
        )
        filas.append([
            str(evento["profundidad"]),
            str(evento["id_hijo"]),
            str(evento["id_padre"]),
            str(evento["id_rama"]),
            evento["estado_origen"],
            _entrada_restante(cadena, evento["posicion_antes"]),
            _pila_a_texto(evento["pila_antes"]),
            evento["entrada"],
            evento["tope"],
            evento["destino"],
            reemplazo,
            _pila_a_texto(evento["nueva_pila"]),
            "TESTIGO" if evento["id_hijo"] in ids_testigo else "",
        ])

    _imprimir_tabla([
        "Paso", "Nodo", "Padre", "Rama", "Estado", "Entrada restante",
        "Pila antes", "Consumido", "Tope", "Destino", "Reemplazo",
        "Pila después", "Marca",
    ], filas)

    _imprimir_cierres(resultado)
    _imprimir_podas(resultado)


def _motivo_cierre(evento, resultado):
    tipo = evento["tipo"]
    posicion = evento["posicion"]
    entrada_agotada = posicion == len(resultado.cadena)

    if tipo == "rama_muerta_pila_vacia":
        if entrada_agotada:
            return "Pila vacía y entrada agotada en estado no final."
        return "Pila vacía con entrada pendiente."

    if tipo == "rama_muerta_bloqueada":
        if entrada_agotada:
            return "Entrada agotada en estado no final."
        simbolo = resultado.cadena[posicion]
        return "Sin transición aplicable para entrada {!r}.".format(simbolo)

    if tipo == "ciclo_detectado":
        return (
            "Alternativa cerrada por ciclo exacto al usar {} hacia {}.".format(
                evento["entrada"], evento["destino"]
            )
        )

    if tipo == "aceptacion":
        return "ACEPTACIÓN: entrada consumida en estado final."

    return "PENDIENTE: no se procesó porque otra rama ya aceptó."


def _imprimir_cierres(resultado):
    tipos = {
        "rama_muerta_pila_vacia",
        "rama_muerta_bloqueada",
        "ciclo_detectado",
        "aceptacion",
        "rama_pendiente_por_aceptacion",
    }
    eventos = [p for p in resultado.pasos if p["tipo"] in tipos]
    if not eventos:
        return

    seleccion, omitidos = _seleccionar_eventos(eventos)
    print("\n--- CIERRE O ESTADO DE RAMAS ---")
    _avisar_resumen("Los cierres de ramas", len(eventos), omitidos)
    filas = []
    for evento in seleccion:
        if evento is None:
            filas.append(["..."] * 8)
            continue
        filas.append([
            str(evento.get("profundidad", "-")),
            str(evento["id_nodo"]),
            str(evento.get("id_padre", "-")),
            str(evento.get("id_rama", "-")),
            evento["estado"],
            _entrada_restante(resultado.cadena, evento["posicion"]),
            _pila_a_texto(evento.get("pila")),
            _motivo_cierre(evento, resultado),
        ])

    _imprimir_tabla([
        "Paso", "Nodo", "Padre", "Rama", "Estado", "Entrada restante",
        "Pila", "Motivo",
    ], filas)


def _imprimir_podas(resultado):
    eventos = [
        p for p in resultado.pasos if p["tipo"] == "podada_por_limite"
    ]
    if not eventos:
        return

    seleccion, omitidos = _seleccionar_eventos(eventos)
    print("\n--- ALTERNATIVAS OMITIDAS POR LÍMITE (NO EJECUTADAS) ---")
    _avisar_resumen("Las alternativas omitidas", len(eventos), omitidos)
    filas = []
    for evento in seleccion:
        if evento is None:
            filas.append(["..."] * 11)
            continue
        reemplazo = (
            ";".join(evento["reemplazo"])
            if evento["reemplazo"] else EPS
        )
        filas.append([
            str(evento["profundidad"]),
            str(evento["id_padre"]),
            str(evento["id_rama"]),
            evento["estado_origen"],
            _entrada_restante(resultado.cadena, evento["posicion_antes"]),
            _pila_a_texto(evento["pila_antes"]),
            evento["entrada"],
            evento["tope"],
            evento["destino"],
            reemplazo,
            _pila_a_texto(evento["nueva_pila"]),
        ])

    _imprimir_tabla([
        "Paso", "Padre", "Rama origen", "Estado", "Entrada restante",
        "Pila antes", "Entrada", "Tope", "Destino", "Reemplazo",
        "Pila potencial",
    ], filas)


# Convierte la pila pública o interna a texto con el tope del lado izquierdo.
def _pila_a_texto(pila):
    if not pila:
        return "vacía"
    if isinstance(pila, tuple):
        simbolos = pila
    else:
        simbolos = _pila_interna_a_tupla(pila)
    return "[" + ",".join(simbolos) + "]"

# Evalúa y muestra el resultado en una sola llamada para simplificar el menú.
def evaluar_y_mostrar(ap, cadena, limite=10000):
    resultado = evaluar(ap, cadena, limite=limite, mostrar_traza=False)
    mostrar_traza(resultado, ap)
    return resultado
