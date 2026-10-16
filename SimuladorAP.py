"""
SimuladorAP.py — Motor de simulación BFS para Autómatas de Pila (APD/APND).

Implementa la exploración por niveles (BFS) sobre la séptupla del AP.
No usa recursión para explorar ramas; usa collections.deque.
No impone un timeout oculto que devuelva RECHAZADA.

Acuerdos de diseño relevantes (docs/kiro/DECISIONES.md):
  D01  — BFS con deque; pila como tupla; presupuesto al admitir.
  D05  — Aceptación: entrada consumida + estado ∈ F; no exige pila vacía.

Convención de pila (AutomataPila.py):
  La pila es una tupla de tokens de Γ; el TOPE está en el ÍNDICE 0.
  Sustitución al aplicar una transición:
      nueva_pila = reemplazo + pila[1:]
  Ejemplo: pila=('A','Z0'), reemplazo=('B','C') → ('B','C','Z0').

Por qué EPS no avanza la posición:
  EPS como símbolo de entrada representa una transición espontánea;
  el autómata actúa sin consumir el siguiente símbolo de la cadena.

Por qué el presupuesto se aplica al ADMITIR y no al desencolar:
  Si se aplicara al desencolar, la frontera pendiente podría crecer sin
  cota, desbordando la memoria antes de que el límite sea relevante.
  Aplicarlo al admitir garantiza que la cola nunca supera `limite` nodos.

Por qué una raíz ya admitida (admitidas=1, límite=1) se puede procesar:
  El límite es de admisión, no de procesamiento. El nodo raíz ya fue
  contado al encolarlo (admitidas=1). Sacarlo de la cola y procesarlo
  no requiere una nueva admisión; si acepta, el resultado es ACEPTADA.

Detección de ciclos (dentro del mismo camino):
  Cada nodo lleva un frozenset `ancestros` con las configuraciones de
  todos sus antecesores en el camino (estado, posicion, pila_completa).
  Si la nueva configuración ya está en `ancestros`, ese camino ha entrado
  en un ciclo: seguir explorándolo nunca produciría una aceptación que no
  pudiera alcanzarse por otro medio dentro del presupuesto.
  IMPORTANTE: misma pareja (estado, posicion) con PILA DIFERENTE NO es
  ciclo; pueden ser ejecuciones distintas con diferente contenido de pila.
  La clave de ciclo incluye la pila completa.
"""

import collections
from dataclasses import dataclass, field
from typing import Optional

from AutomataPila import EPS


# ---------------------------------------------------------------------------
# Constantes de resultado (R07, diseño.md)
# ---------------------------------------------------------------------------

ACEPTADA            = "ACEPTADA"
RECHAZADA           = "RECHAZADA"
DETENIDA_POR_LIMITE = "DETENIDA_POR_LIMITE"
ENTRADA_INVALIDA    = "ENTRADA_INVALIDA"


# ---------------------------------------------------------------------------
# ResultadoSimulacion
# ---------------------------------------------------------------------------

@dataclass
class ResultadoSimulacion:
    """
    Resumen estructurado de la ejecución del motor BFS sobre un AP.

    Campos
    ------
    estado_resultado  : una de las cuatro constantes de módulo.
    motivo            : explicación breve del resultado.
    cadena            : cadena evaluada (tal como la recibió evaluar).
    admitidas         : número de nodos que entraron en la cola.
    procesadas        : número de nodos que salieron de la cola y se procesaron.
    generadas         : número total de alternativas generadas (intentos de expansión).
    podadas_limite    : alternativas no admitidas por presupuesto agotado.
    limite_usado      : valor del límite aplicado en esta evaluación.
    pasos             : lista de diccionarios con eventos de la exploración.
    id_nodo_aceptador : id del nodo que satisfizo la condición de aceptación, o None.
    camino_testigo    : lista de nodos (raíz → aceptador) en orden, o [] si no acepta.
    """
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


# ---------------------------------------------------------------------------
# Funciones internas del motor BFS
# ---------------------------------------------------------------------------

def _crear_nodo(nodo_id, id_padre, id_rama, profundidad,
                estado, posicion, pila, transicion, ancestros):
    """
    Crea un diccionario que representa un nodo de exploración BFS.

    Parámetros
    ----------
    nodo_id    : int              Identificador único (0 = raíz).
    id_padre   : int | None       id del nodo que lo generó; None para raíz.
    id_rama    : int              id del primer nodo de la bifurcación actual.
    profundidad: int              Nivel en el árbol BFS (0 = raíz).
    estado     : str              Estado del AP en esta configuración.
    posicion   : int              Índice en la cadena (0 = inicio, len = agotada).
    pila       : tuple            Tupla de tokens; tope en índice 0. Inmutable.
    transicion : str | None       Descripción de la transición aplicada; None en raíz.
    ancestros  : frozenset        Configuraciones (estado, posicion, pila) de todos
                                  los antecesores en este camino. Permite detectar ciclos
                                  exactos dentro del mismo camino sin visitar globales.

    Retorna
    -------
    dict con los campos descritos.
    """
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


def _reconstruir_testigo(nodo_aceptador, nodos_por_id):
    """
    Reconstruye el camino desde la raíz hasta el nodo aceptador.

    Sigue la cadena de `id_padre` hacia atrás y luego invierte el resultado.

    Parámetros
    ----------
    nodo_aceptador : dict          El nodo que cumplió la condición de aceptación.
    nodos_por_id   : dict[int, dict]  Mapa de id → nodo para todos los nodos admitidos.

    Retorna
    -------
    list[dict]  Lista de nodos en orden raíz → aceptador.
    """
    camino = []
    nodo_actual = nodo_aceptador
    while nodo_actual is not None:
        camino.append(nodo_actual)
        id_padre = nodo_actual["id_padre"]
        nodo_actual = nodos_por_id.get(id_padre)  # None cuando id_padre es None (raíz)
    camino.reverse()
    return camino


def _texto_transicion(entrada, tope, destino, reemplazo):
    """
    Produce una descripción legible de la transición aplicada para los eventos.

    Ejemplos:
        "(a, Z0) → (q1, A;Z0)"
        "(EPS, A) → (q1, EPS)"
    """
    if reemplazo:
        texto_remp = ";".join(reemplazo)
    else:
        texto_remp = EPS  # reemplazo vacío = desapilar
    return "({}, {}) -> ({}, {})".format(entrada, tope, destino, texto_remp)


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------

def evaluar(ap, cadena, limite=10000, mostrar_traza=True):
    """
    Evalúa si el AP acepta la cadena usando exploración BFS (búsqueda por niveles).

    Pre-condiciones — si alguna falla, retorna ENTRADA_INVALIDA sin explorar:
      1. ap.es_valido debe ser True (el AP pasó por ValidadorAP.validar).
      2. Todos los símbolos de la cadena deben pertenecer a ap.alfabeto,
         o la cadena debe ser vacía.
      3. limite debe ser un entero positivo (> 0).

    Parámetros
    ----------
    ap            : AutomataPila   Autómata validado.
    cadena        : str            Cadena a evaluar (puede ser vacía).
    limite        : int            Número máximo de nodos a admitir en la cola.
                                   Incluye el nodo raíz (la raíz ya cuenta como 1).
    mostrar_traza : bool           No usado en la lógica central; se conserva
                                   para compatibilidad con evaluar_y_mostrar.

    Retorna
    -------
    ResultadoSimulacion con estado_resultado en {ACEPTADA, RECHAZADA,
    DETENIDA_POR_LIMITE, ENTRADA_INVALIDA}.

    Algoritmo BFS resumido:
      1. Crear nodo raíz con configuración inicial (q0, 0, (Z0,)).
      2. Encolarlo; admitidas = 1.
      3. Mientras la cola no esté vacía:
         a. Desencolar; procesadas += 1.
         b. Comprobar aceptación (posicion == len(cadena) y estado ∈ F).
         c. Si pila vacía: rama muerta (sin tope para ninguna transición).
         d. Recopilar alternativas EPS y de consumo.
         e. Por cada alternativa: calcular config_nueva; detectar ciclo en
            ancestros del nodo; si hay presupuesto, admitir hijo; si no, podar.
      4. Sin aceptación: DETENIDA_POR_LIMITE o RECHAZADA según hubo_poda.
    """
    # ------------------------------------------------------------------
    # Pre-condición 1: AP validado
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Pre-condición 2: todos los símbolos en Σ
    # (cadena vacía siempre es válida)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Pre-condición 3: límite entero positivo
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Inicialización del BFS
    # ------------------------------------------------------------------
    longitud = len(cadena)

    # Nodo raíz: configuración inicial del AP.
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

    # Mapa de id → nodo para reconstruir el testigo sin copiar ramas.
    nodos_por_id = {0: nodo_raiz}

    # Contador de id único para nodos generados.
    siguiente_id = 1

    # Contadores de exploración.
    admitidas = 1      # La raíz ya fue admitida al encolarse.
    procesadas = 0
    generadas = 0
    podadas_limite = 0
    hubo_poda = False  # True si se omitió al menos un nodo por presupuesto.

    # Lista de eventos para trazas y diagnósticos.
    pasos = []

    # ------------------------------------------------------------------
    # Bucle principal BFS
    # ------------------------------------------------------------------
    while cola:
        nodo = cola.popleft()
        procesadas += 1

        estado   = nodo["estado"]
        posicion = nodo["posicion"]
        pila     = nodo["pila"]

        # ------------------------------------------------------------------
        # Comprobar ACEPTACIÓN antes que cualquier otra cosa.
        # (D05) Acepta si la entrada fue completamente consumida y el estado
        # pertenece a F, independientemente del contenido de la pila.
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # Pila vacía → no hay tope; ninguna transición puede aplicarse.
        # Si ya comprobamos aceptación y no aceptó, esta rama muere aquí.
        # Nota: el criterio de aceptación (D05) no exige pila vacía;
        # pila vacía con entrada pendiente o estado no final es rama muerta.
        # ------------------------------------------------------------------
        if not pila:
            pasos.append({
                "tipo": "rama_muerta_pila_vacia",
                "id_nodo": nodo["id"],
                "estado": estado,
                "posicion": posicion,
            })
            continue

        tope = pila[0]

        # ------------------------------------------------------------------
        # Recopilar alternativas aplicables.
        # Orden: EPS primero (transiciones espontáneas), luego consumo.
        # Dentro de cada grupo se respeta el orden de declaración del modelo.
        # ------------------------------------------------------------------
        alternativas = []

        # Transiciones espontáneas (EPS no avanza la posición).
        for destino, reemplazo in ap.obtener_alternativas(estado, EPS, tope):
            alternativas.append((EPS, destino, reemplazo))

        # Transiciones de consumo (solo si queda entrada).
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

        # ------------------------------------------------------------------
        # Expandir cada alternativa.
        # ------------------------------------------------------------------
        for entrada, destino, reemplazo in alternativas:
            generadas += 1

            # Calcular nueva posición.
            # EPS no avanza: la transición espontánea no consume símbolo.
            if entrada == EPS:
                nueva_posicion = posicion
            else:
                nueva_posicion = posicion + 1

            # Calcular nueva pila.
            # El reemplazo se inserta en lugar del tope; la convención es
            # tope en índice 0, así que el primer token del reemplazo queda
            # en la cima. Reemplazo () (EPS) desapila sin insertar nada.
            nueva_pila = reemplazo + pila[1:]

            config_nueva = (destino, nueva_posicion, nueva_pila)

            # ----------------------------------------------------------
            # Detección de ciclo dentro del camino.
            # Si la nueva configuración ya es ancestro de este nodo,
            # el camino cerraría un ciclo exacto: el mismo estado,
            # misma posición y MISMA PILA COMPLETA ya fueron visitados
            # en el mismo camino. No hay nueva información que explorar.
            # IMPORTANTE: misma pareja (estado, posición) con pila
            # DIFERENTE no es ciclo; puede ser una ejecución distinta.
            # ----------------------------------------------------------
            if config_nueva in nodo["ancestros"]:
                pasos.append({
                    "tipo": "ciclo_detectado",
                    "id_nodo": nodo["id"],
                    "config_repetida": config_nueva,
                    "entrada": entrada,
                })
                continue

            # ----------------------------------------------------------
            # Aplicar presupuesto: admitir solo si hay cupo.
            # El presupuesto se aplica AL ADMITIR, no al desencolar,
            # para que la cola nunca exceda `limite` nodos.
            # Las configuraciones ya admitidas siguen procesándose aunque
            # el límite se haya alcanzado; pueden contener aceptación.
            # ----------------------------------------------------------
            if admitidas < limite:
                id_hijo = siguiente_id
                siguiente_id += 1

                # Determinar id_rama: si hay más de una alternativa
                # en este nivel, cada hijo recibe su propio id de rama.
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

    # ------------------------------------------------------------------
    # Cola vacía sin haber encontrado aceptación.
    # Si hubo poda por recursos: DETENIDA_POR_LIMITE.
    #   No podemos garantizar rechazo porque existían alternativas no exploradas.
    # Si no hubo poda: se exploró el espacio completo; RECHAZADA.
    # ------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Presentación de trazas
# ---------------------------------------------------------------------------

def mostrar_traza(resultado, ap):
    """
    Imprime la traza de la evaluación en la consola.

    Si el resultado es ACEPTADA: muestra el camino testigo paso a paso
    en formato tabular. Si la traza supera 50 pasos, se muestran los
    primeros 25 y los últimos 10 con aviso explícito.

    Si el resultado es RECHAZADA o DETENIDA_POR_LIMITE: muestra únicamente
    los contadores; no hay camino testigo que mostrar.

    Parámetros
    ----------
    resultado : ResultadoSimulacion  Producido por evaluar().
    ap        : AutomataPila         El autómata evaluado (para contexto).
    """
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


def _imprimir_tabla_testigo(camino, cadena):
    """
    Imprime el camino testigo en formato tabular.

    Columnas: Paso | Rama | Estado | Entrada restante | Pila antes |
              Consumido | Tope | Destino | Reemplazo | Pila después.

    Acorta la salida a 25+10 pasos si supera 50, anunciándolo.

    Parámetros
    ----------
    camino : list[dict]   Lista de nodos raíz → aceptador.
    cadena : str          Cadena evaluada (para calcular entrada restante).
    """
    total = len(camino)

    # Decidir qué pasos mostrar.
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

    # Encabezados de la tabla.
    encabezados = [
        "Paso", "Rama", "Estado", "Entrada restante",
        "Pila antes", "Consumido", "Tope", "Destino", "Reemplazo", "Pila después",
    ]

    # Construir filas de datos.
    # Cada fila muestra: el estado ANTES de la transición (el nodo padre),
    # la transición aplicada, y el estado DESPUÉS (el nodo actual).
    # Para el nodo raíz (sin transición): mostrar solo la configuración inicial.
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

    # Calcular anchos de columna.
    anchos = [len(enc) for enc in encabezados]
    for fila in filas:
        for j, celda in enumerate(fila):
            if len(celda) > anchos[j]:
                anchos[j] = len(celda)

    # Imprimir encabezado.
    sep = " | "
    linea_enc = sep.join(enc.ljust(anchos[k]) for k, enc in enumerate(encabezados))
    print(linea_enc)
    print("-" * len(linea_enc))

    # Imprimir filas.
    for fila in filas:
        print(sep.join(celda.ljust(anchos[k]) for k, celda in enumerate(fila)))


def _pila_a_texto(pila):
    """
    Convierte una tupla de pila a texto legible.

    ()            → 'vacía'
    ('Z0',)       → '[Z0]'
    ('A','Z0')    → '[A,Z0]'
    """
    if not pila:
        return "vacía"
    return "[" + ",".join(pila) + "]"


def _parsear_trans_desc(descripcion):
    """
    Extrae (consumido, destino, reemplazo) desde la descripción de transición.

    Formato esperado: "(entrada, tope) -> (destino, reemplazo)"
    Ejemplo: "(a, Z0) -> (q0, A;Z0)"
    """
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


# ---------------------------------------------------------------------------
# Función de conveniencia para integración con main.py
# ---------------------------------------------------------------------------

def evaluar_y_mostrar(ap, cadena, limite=10000):
    """
    Evalúa la cadena y muestra la traza a continuación.

    Simplifica la integración con main.py: una sola llamada produce el
    resultado y lo presenta sin que el llamador deba gestionar mostrar_traza.

    Parámetros
    ----------
    ap     : AutomataPila   Autómata validado.
    cadena : str            Cadena a evaluar.
    limite : int            Presupuesto de configuraciones admitidas.

    Retorna
    -------
    ResultadoSimulacion  — el mismo objeto que retorna evaluar().
    """
    resultado = evaluar(ap, cadena, limite=limite, mostrar_traza=False)
    mostrar_traza(resultado, ap)
    return resultado
