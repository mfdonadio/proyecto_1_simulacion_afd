# Este simulador recorre por niveles las ramas de un APD o APND.
# La pila es una tupla con el tope en el índice 0 y EPS no consume entrada.
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


# Cada nodo conserva su padre y sus ancestros para reconstruir el camino y
# reconocer una configuración repetida dentro de esa misma rama.
def _crear_nodo(nodo_id, id_padre, id_rama, profundidad,
                estado, posicion, pila, transicion, ancestros):
    return {
        "id": nodo_id,
        "id_padre": id_padre,
        "id_rama": id_rama,
        "profundidad": profundidad,
        "estado": estado,
        "posicion": posicion,
        "pila": pila,
        "transicion": transicion,
        "ancestros": ancestros,
    }

# Seguimos los padres desde el nodo aceptador y luego invertimos el recorrido.
def _reconstruir_testigo(nodo_aceptador, nodos_por_id):
    camino = []
    nodo_actual = nodo_aceptador
    while nodo_actual is not None:
        camino.append(nodo_actual)
        id_padre = nodo_actual["id_padre"]
        nodo_actual = nodos_por_id.get(id_padre)  # None cuando id_padre es None (raíz)
    camino.reverse()
    return camino

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
    nodo_raiz = _crear_nodo(
        nodo_id=0,
        id_padre=None,
        id_rama=0,
        profundidad=0,
        estado=ap.estado_inicial,
        posicion=0,
        pila=(ap.simbolo_inicial_pila,),
        transicion=None,
        ancestros=frozenset(),
    )

    cola = collections.deque([nodo_raiz])

    # Relacionamos cada identificador con su nodo para reconstruir el testigo.
    nodos_por_id = {0: nodo_raiz}

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
                "estado": estado,
                "posicion": posicion,
                "pila": pila,
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
                "estado": estado,
                "posicion": posicion,
            })
            continue

        tope = pila[0]

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
            nueva_pila = reemplazo + pila[1:]

            config_nueva = (destino, nueva_posicion, nueva_pila)

            # Solo cerramos un ciclo si coinciden estado, posición y pila completa.
            # La misma posición con otra pila todavía representa otra ejecución.
            if config_nueva in nodo["ancestros"]:
                pasos.append({
                    "tipo": "ciclo_detectado",
                    "id_nodo": nodo["id"],
                    "config_repetida": config_nueva,
                    "entrada": entrada,
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

                # Los ancestros del hijo incluyen la configuración actual
                # del padre, para que el hijo pueda detectar ciclos.
                ancestros_hijo = nodo["ancestros"] | {
                    (estado, posicion, pila)
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
                    ancestros=ancestros_hijo,
                )

                nodos_por_id[id_hijo] = nodo_hijo
                admitidas += 1
                cola.append(nodo_hijo)

                pasos.append({
                    "tipo": "expansion",
                    "id_padre": nodo["id"],
                    "id_hijo": id_hijo,
                    "id_rama": id_rama_hijo,
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
                    "entrada": entrada,
                    "destino": destino,
                    "limite": limite,
                })

    # Una poda por presupuesto deja el resultado inconcluso; sin podas, el
    # agotamiento de todas las ramas sí permite responder RECHAZADA.
    if hubo_poda:
        motivo = (
            "Presupuesto de {} configuraciones agotado; "
            "{} alternativas no exploradas.".format(limite, podadas_limite)
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


# Muestra el resumen y, cuando existe, el camino que demuestra la aceptación.
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

    if resultado.estado_resultado == ACEPTADA and resultado.camino_testigo:
        print()
        # Orientación de pila explícita para el lector.
        print("Convención de pila: tope → fondo (el tope es el primer token).")
        print()
        _imprimir_tabla_testigo(resultado.camino_testigo, resultado.cadena)

    elif resultado.estado_resultado == DETENIDA_POR_LIMITE:
        print()
        print("Nota: el presupuesto se agotó antes de completar la exploración.")
        print("      No se puede afirmar rechazo; puede haber cadenas aceptadas")
        print("      en las ramas no exploradas.")

    print("=" * 62)

# La tabla conserva el estado y la pila antes y después de cada transición.
# Si el testigo es muy largo, muestra el inicio y el final con un aviso.
def _imprimir_tabla_testigo(camino, cadena):
    total = len(camino)

    # Seleccionamos todos los pasos o un resumen de los extremos si la traza es larga.
    if total > 50:
        print(
            "[AVISO] El camino testigo tiene {} pasos. "
            "Se muestran los primeros 25 y los últimos 10.".format(total)
        )
        pasos_mostrar = list(range(25)) + list(range(total - 10, total))
        truncado = True
    else:
        pasos_mostrar = list(range(total))
        truncado = False

    # Definimos las columnas que explican cada cambio de configuración.
    encabezados = [
        "Paso", "Rama", "Estado", "Entrada restante",
        "Pila antes", "Consumido", "Tope", "Destino", "Reemplazo", "Pila después",
    ]

    # Construimos las filas a partir del nodo inicial y las transiciones del testigo.
    # Cada fila parte del nodo padre, muestra la transición y termina en el nodo
    # actual. En la raíz solo mostramos la configuración inicial.
    filas = []
    for paso_idx, i in enumerate(pasos_mostrar):
        nodo = camino[i]
        id_rama = str(nodo["id_rama"])

        if nodo["transicion"] is None:
            # Fila raíz: configuración inicial sin transición previa.
            estado    = nodo["estado"]
            posicion  = nodo["posicion"]
            pila      = nodo["pila"]
            entrada_restante = cadena[posicion:] if posicion < len(cadena) else "ε"
            pila_antes_texto = _pila_a_texto(pila)
            consumido  = "-"
            tope_texto = pila[0] if pila else "∅"
            destino    = "-"
            reemplazo  = "-"
            pila_despues = "-"
        else:
            # Fila de transición: "pila antes" es la pila del nodo padre.
            nodo_padre = camino[i - 1] if i > 0 else nodo
            pila_padre = nodo_padre["pila"]
            estado = nodo_padre["estado"]
            posicion = nodo_padre["posicion"]
            entrada_restante = cadena[posicion:] if posicion < len(cadena) else "ε"
            pila_antes_texto = _pila_a_texto(pila_padre)
            tope_texto = pila_padre[0] if pila_padre else "∅"
            # La transición aplicada está registrada en el nodo actual.
            consumido, destino, reemplazo = _parsear_trans_desc(nodo["transicion"])
            pila_despues = _pila_a_texto(nodo["pila"])

        filas.append([
            str(i),
            id_rama,
            estado,
            entrada_restante,
            pila_antes_texto,
            consumido,
            tope_texto,
            destino,
            reemplazo,
            pila_despues,
        ])

        # Separador visual si la salida está truncada.
        if truncado and paso_idx == 24:
            filas.append(["...", "...", "...", "...", "...", "...", "...", "...", "...", "..."])

    # Calculamos cada ancho con el contenido real para no recortar información.
    anchos = [len(enc) for enc in encabezados]
    for fila in filas:
        for j, celda in enumerate(fila):
            if len(celda) > anchos[j]:
                anchos[j] = len(celda)

    # Imprimimos primero el encabezado de la tabla.
    sep = " | "
    linea_enc = sep.join(enc.ljust(anchos[k]) for k, enc in enumerate(encabezados))
    print(linea_enc)
    print("-" * len(linea_enc))

    # Finalmente imprimimos cada configuración seleccionada.
    for fila in filas:
        print(sep.join(celda.ljust(anchos[k]) for k, celda in enumerate(fila)))

# Convierte la tupla de pila a texto con el tope del lado izquierdo.
def _pila_a_texto(pila):
    if not pila:
        return "vacía"
    return "[" + ",".join(pila) + "]"

# Recupera los tres datos que necesita la tabla desde el texto de transición.
def _parsear_trans_desc(descripcion):
    try:
        # Partir por " -> "
        partes = descripcion.split(" -> ")
        izq = partes[0].strip("() ")
        der = partes[1].strip("() ")
        consumido = izq.split(",")[0].strip()
        destino   = der.split(",")[0].strip()
        reemplazo = der.split(",")[1].strip()
        return consumido, destino, reemplazo
    except Exception:
        return "?", "?", "?"


# Evalúa y muestra el resultado en una sola llamada para simplificar el menú.
def evaluar_y_mostrar(ap, cadena, limite=10000):
    resultado = evaluar(ap, cadena, limite=limite, mostrar_traza=False)
    mostrar_traza(resultado, ap)
    return resultado
