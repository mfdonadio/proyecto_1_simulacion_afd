"""
CargadorAP.py — Carga y construcción manual de Autómatas de Pila (APD/APND).

Dos puntos de entrada públicos:
  cargar_archivo(ruta)  -> AutomataPila | None
  crear_manual()        -> AutomataPila | None

Ambos devuelven None y muestran mensajes de error si la definición es inválida,
sin modificar el autómata activo de la sesión (la atomicidad es responsabilidad
de quien llama, típicamente main.py).

Formato de archivo soportado (idéntico a ejemplos/fase3/):
--------------------------------------------------------------
NOMBRE=APD_ANBN
TIPO=APD
ESTADOS=q0,q1,q2
ALFABETO=a,b
ALFABETO_PILA=Z0,A
INICIAL=q0
INICIAL_PILA=Z0
FINALES=q2
TRANSICIONES:
q0,a,Z0,q0,A;Z0
q0,b,A,q1,EPS
q0,a,Z0,qm,Z0|qf,Z0   <- alternativas APND con '|'

Convenciones clave
------------------
- Reemplazo 'EPS' → tupla vacía () (desapilar sin insertar).
- Reemplazo 'A;Z0' → ('A', 'Z0') (tokens separados por ';').
- Nunca mezclar EPS con tokens: 'A;EPS' y 'EPS;Z0' son errores.
- El tope nunca puede ser EPS.
- Alternativas APND: primer tramo con 5 campos, tramos adicionales con 2.
  No repetir origen/entrada/tope después de '|'.
- Líneas vacías dentro de la sección TRANSICIONES: son error de formato.
- Un duplicado exacto de transición → diagnóstico, no se añade.
- Una clave APND con alternativas distintas en varias líneas → se unen.
"""

import re
import os

from AutomataPila import AutomataPila, EPS
import ValidadorAP
# Reutilizamos normalizar_ruta de CargadorAFD para manejar comillas y espacios.
from CargadorAFD import CargadorAFD

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Encabezados reconocidos en el formato AP, en el orden oficial de escritura.
_ENCABEZADOS_AP = (
    "NOMBRE",
    "TIPO",
    "ESTADOS",
    "ALFABETO",
    "ALFABETO_PILA",
    "INICIAL",
    "INICIAL_PILA",
    "FINALES",
)

# Regex para una línea de encabezado: CLAVE=valor (valor puede estar vacío).
_RE_ENCABEZADO = re.compile(r"^([A-Z_]+)=(.*)$")

# Regex para el marcador de sección de transiciones.
_RE_TRANSICIONES = re.compile(r"^TRANSICIONES:$")

# Regex para un token de estado/símbolo de pila: texto imprimible sin
# espacios, comas, puntos y comas ni '|'. EPS está reservado.
_RE_TOKEN = re.compile(r"^[^\s,;|]+$")


# ---------------------------------------------------------------------------
# Helpers internos de parsing
# ---------------------------------------------------------------------------

def _parsear_reemplazo(texto):
    """
    Convierte el texto de un reemplazo en una tupla de tokens de Γ.

    Reglas:
      - 'EPS'   → ()          (desapilar sin insertar nada).
      - 'A;Z0'  → ('A', 'Z0') (tokens separados por ';').
      - ''      → error (campo vacío).
      - 'A;EPS' → error (EPS mezclado con tokens).
      - 'EPS;Z0'→ error (EPS mezclado con tokens).
      - 'A;;Z0' → error (token vacío entre separadores).

    Parámetros
    ----------
    texto : str  Texto crudo del campo reemplazo.

    Retorna
    -------
    (tuple | None, str | None)
        (tupla, None)  si no hay error.
        (None, mensaje) si hay error.
    """
    if texto == "":
        return None, "El campo reemplazo no puede estar vacío."

    if texto == EPS:
        # Caso canónico: EPS solo representa desapilar sin insertar.
        return (), None

    # Separar por ';' para obtener los tokens individuales.
    partes = texto.split(";")

    tokens = []
    for parte in partes:
        tok = parte.strip()
        if tok == "":
            return None, (
                "Reemplazo '{}': campo vacío entre separadores ';'.".format(texto)
            )
        if tok == EPS:
            # EPS mezclado con otros tokens es ilegal (R04.3).
            return None, (
                "Reemplazo '{}': EPS no puede mezclarse con otros tokens.".format(texto)
            )
        tokens.append(tok)

    return tuple(tokens), None


def _parsear_linea_transicion(linea, numero):
    """
    Descompone una línea de transición en una lista de cúplas listas para
    ser añadidas al autómata.

    Formato del primer tramo (5 campos separados por ','):
        origen,entrada,tope,destino,reemplazo

    Tramos adicionales APND (separados por '|', cada uno con 2 campos):
        destino2,reemplazo2

    El origen, entrada y tope se heredan del primer tramo.

    Parámetros
    ----------
    linea  : str  Texto de la línea (ya sin salto de línea).
    numero : int  Número de línea real para diagnósticos.

    Retorna
    -------
    (list[(origen, entrada, tope, destino, reemplazo)] | None, list[str])
        Si hay errores fatales → (None, [errores]).
        Si todo es correcto → (lista_de_cúplas, []).
        Errores recuperables parciales → (None, [errores]).
    """
    errores = []

    # Dividir por '|' para separar primer tramo de tramos APND adicionales.
    tramos = linea.split("|")

    # -----------------------------------------------------------------
    # Primer tramo: debe tener exactamente 5 campos separados por ','.
    # -----------------------------------------------------------------
    campos_primer = tramos[0].split(",")
    if len(campos_primer) != 5:
        errores.append(
            "Línea {}: se esperaban 5 campos (origen,entrada,tope,destino,reemplazo), "
            "se encontraron {}: '{}'.".format(numero, len(campos_primer), tramos[0])
        )
        return None, errores

    origen, entrada, tope, destino1, reemplazo1_txt = [c.strip() for c in campos_primer]

    # Validar que ningún campo de posición fija esté vacío.
    for nombre_campo, valor in [
        ("origen", origen),
        ("entrada", entrada),
        ("tope", tope),
        ("destino", destino1),
        ("reemplazo", reemplazo1_txt),
    ]:
        if valor == "":
            errores.append(
                "Línea {}: campo '{}' vacío.".format(numero, nombre_campo)
            )

    if errores:
        return None, errores

    # Validar tokens de origen, tope y destino (no vacíos, sin caracteres especiales).
    for nombre_campo, valor in [
        ("origen", origen),
        ("tope", tope),
        ("destino", destino1),
    ]:
        if not _RE_TOKEN.match(valor):
            errores.append(
                "Línea {}: '{}' contiene caracteres no permitidos en '{}'.".format(
                    numero, valor, nombre_campo
                )
            )

    # El tope nunca puede ser EPS (R04.3 + diseño).
    if tope == EPS:
        errores.append(
            "Línea {}: el tope de pila no puede ser EPS.".format(numero)
        )

    # Parsear el reemplazo del primer tramo.
    reemplazo1, error_remp = _parsear_reemplazo(reemplazo1_txt)
    if error_remp is not None:
        errores.append("Línea {}: {}.".format(numero, error_remp))

    if errores:
        return None, errores

    resultado = [(origen, entrada, tope, destino1, reemplazo1)]

    # -----------------------------------------------------------------
    # Tramos adicionales APND (si los hay).
    # -----------------------------------------------------------------
    for i, tramo in enumerate(tramos[1:], start=2):
        campos_alt = tramo.split(",")
        if len(campos_alt) != 2:
            errores.append(
                "Línea {}: tramo alternativo {} debe tener exactamente 2 campos "
                "(destino,reemplazo), se encontraron {}: '{}'.".format(
                    numero, i, len(campos_alt), tramo
                )
            )
            continue

        destino_alt, reemplazo_alt_txt = [c.strip() for c in campos_alt]

        if destino_alt == "":
            errores.append(
                "Línea {}: tramo alternativo {}: campo 'destino' vacío.".format(
                    numero, i
                )
            )
            continue

        if reemplazo_alt_txt == "":
            errores.append(
                "Línea {}: tramo alternativo {}: campo 'reemplazo' vacío.".format(
                    numero, i
                )
            )
            continue

        if not _RE_TOKEN.match(destino_alt):
            errores.append(
                "Línea {}: tramo alternativo {}: destino '{}' contiene "
                "caracteres no permitidos.".format(numero, i, destino_alt)
            )
            continue

        reemplazo_alt, error_alt = _parsear_reemplazo(reemplazo_alt_txt)
        if error_alt is not None:
            errores.append(
                "Línea {}: tramo alternativo {}: {}.".format(numero, i, error_alt)
            )
            continue

        # Los tramos adicionales heredan origen/entrada/tope del primer tramo.
        resultado.append((origen, entrada, tope, destino_alt, reemplazo_alt))

    if errores:
        return None, errores

    return resultado, []


def _convertir_lista(texto, nombre_campo, permitir_vacio):
    """
    Convierte un texto separado por comas en una lista de tokens sin duplicados.

    Parámetros
    ----------
    texto          : str   Texto crudo (puede estar vacío).
    nombre_campo   : str   Nombre para diagnósticos.
    permitir_vacio : bool  Si False, requiere al menos un elemento.

    Retorna
    -------
    (list[str] | None, str | None)
        (lista, None)   si no hay error.
        (None, mensaje) si hay error.
    """
    if texto.strip() == "":
        if permitir_vacio:
            return [], None
        return None, "El campo '{}' no puede estar vacío.".format(nombre_campo)

    partes = texto.split(",")
    elementos = []
    for parte in partes:
        elem = parte.strip()
        if elem == "":
            return None, (
                "El campo '{}' contiene un elemento vacío entre comas.".format(
                    nombre_campo
                )
            )
        elementos.append(elem)

    # Detectar duplicados antes de convertir a set (R03.7).
    vistos = set()
    for elem in elementos:
        if elem in vistos:
            return None, (
                "El campo '{}' contiene el elemento duplicado '{}'.".format(
                    nombre_campo, elem
                )
            )
        vistos.add(elem)

    return elementos, None


def _construir_ap_desde_datos(datos_enc, lineas_transicion, errores_acum):
    """
    Construye un AutomataPila a partir de los encabezados ya parseados y
    las líneas de transición crudas.  Añade errores a errores_acum.

    Parámetros
    ----------
    datos_enc        : dict   Mapa clave→valor de encabezados.
    lineas_transicion: list   Lista de (numero_linea, texto_linea).
    errores_acum     : list   Lista mutable donde se acumulan errores.

    Retorna
    -------
    AutomataPila | None
    """
    ap = AutomataPila()

    # ---------------------------------------------------------------
    # Asignar nombre
    # ---------------------------------------------------------------
    nombre = datos_enc.get("NOMBRE", "").strip()
    if nombre == "":
        errores_acum.append("NOMBRE no puede estar vacío.")
    ap.nombre = nombre

    # ---------------------------------------------------------------
    # Asignar tipo
    # ---------------------------------------------------------------
    tipo = datos_enc.get("TIPO", "").strip()
    if tipo not in ("APD", "APND"):
        errores_acum.append(
            "TIPO debe ser APD o APND; se encontró '{}'.".format(tipo)
        )
    ap.tipo = tipo

    # ---------------------------------------------------------------
    # Conjuntos: ESTADOS, ALFABETO, ALFABETO_PILA, FINALES
    # ---------------------------------------------------------------
    estados_lista, err = _convertir_lista(
        datos_enc.get("ESTADOS", ""), "ESTADOS", permitir_vacio=False
    )
    if err:
        errores_acum.append("ESTADOS: " + err)
        estados_lista = []

    alfabeto_lista, err = _convertir_lista(
        datos_enc.get("ALFABETO", ""), "ALFABETO", permitir_vacio=True
    )
    if err:
        errores_acum.append("ALFABETO: " + err)
        alfabeto_lista = []

    alfa_pila_lista, err = _convertir_lista(
        datos_enc.get("ALFABETO_PILA", ""), "ALFABETO_PILA", permitir_vacio=False
    )
    if err:
        errores_acum.append("ALFABETO_PILA: " + err)
        alfa_pila_lista = []

    finales_lista, err = _convertir_lista(
        datos_enc.get("FINALES", ""), "FINALES", permitir_vacio=True
    )
    if err:
        errores_acum.append("FINALES: " + err)
        finales_lista = []

    # EPS no puede aparecer en Σ ni en Γ (R04.3), detectar aquí para
    # dar un mensaje en contexto de encabezado antes de llegar al validador.
    if EPS in alfabeto_lista:
        errores_acum.append(
            "ALFABETO: '{}' está reservado y no puede pertenecer a Σ.".format(EPS)
        )
    if EPS in alfa_pila_lista:
        errores_acum.append(
            "ALFABETO_PILA: '{}' está reservado y no puede pertenecer a Γ.".format(EPS)
        )

    ap.estados = set(estados_lista)
    ap.alfabeto = set(alfabeto_lista)
    ap.alfabeto_pila = set(alfa_pila_lista)
    ap.estados_finales = set(finales_lista)

    # ---------------------------------------------------------------
    # Estado inicial
    # ---------------------------------------------------------------
    ap.estado_inicial = datos_enc.get("INICIAL", "").strip()

    # ---------------------------------------------------------------
    # Símbolo inicial de pila
    # ---------------------------------------------------------------
    ap.simbolo_inicial_pila = datos_enc.get("INICIAL_PILA", "").strip()

    # ---------------------------------------------------------------
    # Si hubo errores en encabezados, no continuar con transiciones
    # para evitar mensajes en cascada inútiles.
    # ---------------------------------------------------------------
    if errores_acum:
        return None

    # ---------------------------------------------------------------
    # Procesar líneas de transición
    # ---------------------------------------------------------------
    for numero_linea, texto_linea in lineas_transicion:
        entradas, errs_linea = _parsear_linea_transicion(texto_linea, numero_linea)
        if errs_linea:
            errores_acum.extend(errs_linea)
            continue

        # Validación de pertenencia a Q, Σ, Γ (R03.6: separar sintaxis de semántica).
        for origen, entrada, tope, destino, reemplazo in entradas:
            error_semantico = False

            if origen not in ap.estados:
                errores_acum.append(
                    "Línea {}: estado origen '{}' no pertenece a Q.".format(
                        numero_linea, origen
                    )
                )
                error_semantico = True

            if entrada != EPS and entrada not in ap.alfabeto:
                errores_acum.append(
                    "Línea {}: símbolo de entrada '{}' no pertenece a Σ ni es EPS.".format(
                        numero_linea, entrada
                    )
                )
                error_semantico = True

            if tope not in ap.alfabeto_pila:
                errores_acum.append(
                    "Línea {}: tope '{}' no pertenece a Γ.".format(
                        numero_linea, tope
                    )
                )
                error_semantico = True

            if destino not in ap.estados:
                errores_acum.append(
                    "Línea {}: estado destino '{}' no pertenece a Q.".format(
                        numero_linea, destino
                    )
                )
                error_semantico = True

            for token in reemplazo:
                if token not in ap.alfabeto_pila:
                    errores_acum.append(
                        "Línea {}: token de reemplazo '{}' no pertenece a Γ.".format(
                            numero_linea, token
                        )
                    )
                    error_semantico = True

            if error_semantico:
                continue

            # Intentar agregar; agregar_alternativa retorna False si es duplicado exacto.
            agregado = ap.agregar_alternativa(origen, entrada, tope, destino, reemplazo)
            if not agregado:
                errores_acum.append(
                    "Línea {}: transición ({}, {}, {}) -> ({}, {}) ya existe "
                    "(duplicado exacto de formato; no se añade).".format(
                        numero_linea, origen, entrada, tope, destino,
                        "EPS" if reemplazo == () else ";".join(reemplazo),
                    )
                )

    if errores_acum:
        return None

    return ap


# ---------------------------------------------------------------------------
# Función pública: cargar_archivo
# ---------------------------------------------------------------------------

def cargar_archivo(ruta):
    """
    Carga un AutomataPila desde un archivo .txt con formato AP.

    El proceso es completamente atómico: si cualquier error aparece (sintaxis,
    semántica o validación estructural) la función imprime los errores y
    retorna None sin modificar ningún estado externo.

    Parámetros
    ----------
    ruta : str  Ruta al archivo.  Se aceptan rutas con espacios y comillas
                exteriores (simple o doble) coincidentes.

    Retorna
    -------
    AutomataPila  si la carga y validación son exitosas.
    None          si hay cualquier error.
    """
    # ------------------------------------------------------------------
    # Normalizar ruta y verificar extensión.
    # ------------------------------------------------------------------
    try:
        ruta_norm = CargadorAFD.normalizar_ruta(ruta)
    except ValueError as exc:
        print("Error en la ruta:", exc)
        return None

    _, ext = os.path.splitext(ruta_norm)
    if ext.lower() != ".txt":
        print("Error: el archivo debe tener extensión .txt")
        return None

    # ------------------------------------------------------------------
    # Leer el archivo.
    # ------------------------------------------------------------------
    try:
        with open(ruta_norm, "r", encoding="utf-8-sig") as archivo:
            lineas = archivo.readlines()
    except (OSError, UnicodeError, ValueError) as exc:
        print("Error: no fue posible abrir el archivo:", exc)
        return None

    # ------------------------------------------------------------------
    # Parsear encabezados y transiciones.
    # ------------------------------------------------------------------
    errores = []
    datos_enc = {}       # clave → valor de los encabezados encontrados
    enc_vistos = set()   # para detectar repetición
    lineas_transicion = []  # (numero_real, texto_limpio)
    en_transiciones = False

    for indice, linea_cruda in enumerate(lineas):
        numero = indice + 1
        linea = linea_cruda.rstrip("\r\n")  # solo quitar el salto de línea
        linea_limpia = linea.strip()        # para encabezados y transiciones

        if en_transiciones:
            # Dentro de la sección de transiciones.
            if linea_limpia == "":
                # Línea vacía es un error de formato en el cuerpo del AP.
                errores.append(
                    "Línea {}: no se permiten líneas vacías en la sección "
                    "TRANSICIONES.".format(numero)
                )
                continue
            lineas_transicion.append((numero, linea_limpia))
            continue

        # Antes de TRANSICIONES:
        if linea_limpia == "":
            # Línea vacía antes de TRANSICIONES también es error.
            errores.append(
                "Línea {}: no se permiten líneas vacías antes de TRANSICIONES.".format(
                    numero
                )
            )
            continue

        if _RE_TRANSICIONES.match(linea_limpia):
            en_transiciones = True
            continue

        # Intentar hacer coincidir con un encabezado CLAVE=valor.
        m = _RE_ENCABEZADO.match(linea_limpia)
        if m is None:
            errores.append(
                "Línea {}: formato no reconocido '{}'.".format(numero, linea_limpia)
            )
            continue

        clave = m.group(1)
        valor = m.group(2)  # No aplicamos strip() para conservar contenido exacto.

        if clave not in _ENCABEZADOS_AP:
            errores.append(
                "Línea {}: encabezado desconocido '{}'.".format(numero, clave)
            )
            continue

        if clave in enc_vistos:
            errores.append(
                "Línea {}: encabezado '{}' repetido.".format(numero, clave)
            )
            continue

        enc_vistos.add(clave)
        datos_enc[clave] = valor

    # Verificar que TRANSICIONES: haya aparecido.
    if not en_transiciones and not errores:
        errores.append("No se encontró el marcador 'TRANSICIONES:'.")

    # Verificar que todos los encabezados obligatorios estén presentes.
    for enc in _ENCABEZADOS_AP:
        if enc not in enc_vistos:
            errores.append("Encabezado obligatorio '{}' no encontrado.".format(enc))

    if errores:
        print("\nError al cargar el archivo:")
        for e in errores:
            print(" -", e)
        return None

    # ------------------------------------------------------------------
    # Construir el AP con los datos obtenidos.
    # ------------------------------------------------------------------
    errores_construccion = []
    ap = _construir_ap_desde_datos(datos_enc, lineas_transicion, errores_construccion)

    if errores_construccion or ap is None:
        print("\nError en la definición del autómata:")
        for e in errores_construccion:
            print(" -", e)
        return None

    # ------------------------------------------------------------------
    # Validación estructural y de determinismo (ValidadorAP).
    # ------------------------------------------------------------------
    valido, errores_val = ValidadorAP.validar(ap)
    if not valido:
        print("\nEl autómata no pasó la validación:")
        for e in errores_val:
            print(" -", e)
        return None

    print("Autómata '{}' ({}) cargado y validado correctamente.".format(
        ap.nombre, ap.tipo
    ))
    return ap


# ---------------------------------------------------------------------------
# Función pública: crear_manual
# ---------------------------------------------------------------------------

def crear_manual():
    """
    Guía al usuario a través de la creación manual de un APD o APND.

    Sigue el mismo flujo que CargadorAFD.crear_manual pero adaptado a la
    séptupla de AP: Q, Σ, Γ, q0, Z0, F y transiciones.

    Retorna
    -------
    AutomataPila  si la definición es válida.
    None          si el usuario cancela o la definición es inválida.
    """
    print("\n=== CREACION MANUAL DEL AUTOMATA DE PILA ===")
    print("(Presione Enter en el nombre para cancelar.)")

    ap = AutomataPila()

    # ------------------------------------------------------------------
    # Nombre
    # ------------------------------------------------------------------
    while True:
        nombre = input("Nombre del autómata: ").strip()
        if nombre == "":
            print("Creación cancelada.")
            return None
        ap.nombre = nombre
        break

    # ------------------------------------------------------------------
    # Tipo
    # ------------------------------------------------------------------
    while True:
        tipo = input("Tipo (APD / APND): ").strip().upper()
        if tipo in ("APD", "APND"):
            ap.tipo = tipo
            break
        print("Error: el tipo debe ser APD o APND.")

    # ------------------------------------------------------------------
    # Conjunto de estados Q
    # ------------------------------------------------------------------
    while True:
        texto = input("Estados separados por coma (ej. q0,q1,q2): ").strip()
        if texto == "":
            print("Q no puede estar vacío.")
            continue
        lista, err = _convertir_lista(texto, "ESTADOS", permitir_vacio=False)
        if err:
            print("Error:", err)
            continue
        ap.estados = set(lista)
        break

    # ------------------------------------------------------------------
    # Alfabeto de entrada Σ (puede estar vacío para autómata solo-EPS)
    # ------------------------------------------------------------------
    while True:
        texto = input(
            "Alfabeto de entrada separado por coma (Enter si solo usa EPS): "
        ).strip()
        lista, err = _convertir_lista(texto, "ALFABETO", permitir_vacio=True)
        if err:
            print("Error:", err)
            continue
        if EPS in lista:
            print(
                "Error: '{}' está reservado y no puede pertenecer a Σ.".format(EPS)
            )
            continue
        ap.alfabeto = set(lista)
        break

    # ------------------------------------------------------------------
    # Alfabeto de pila Γ
    # ------------------------------------------------------------------
    while True:
        texto = input(
            "Alfabeto de pila separado por coma (ej. Z0,A): "
        ).strip()
        lista, err = _convertir_lista(texto, "ALFABETO_PILA", permitir_vacio=False)
        if err:
            print("Error:", err)
            continue
        if EPS in lista:
            print(
                "Error: '{}' está reservado y no puede pertenecer a Γ.".format(EPS)
            )
            continue
        ap.alfabeto_pila = set(lista)
        break

    # ------------------------------------------------------------------
    # Estado inicial q0
    # ------------------------------------------------------------------
    while True:
        q0 = input("Estado inicial (debe estar en Q): ").strip()
        if q0 in ap.estados:
            ap.estado_inicial = q0
            break
        print("Error: '{}' no pertenece a Q.".format(q0))

    # ------------------------------------------------------------------
    # Símbolo inicial de pila Z0
    # ------------------------------------------------------------------
    while True:
        z0 = input("Símbolo inicial de pila Z0 (debe estar en Γ): ").strip()
        if z0 in ap.alfabeto_pila:
            ap.simbolo_inicial_pila = z0
            break
        print("Error: '{}' no pertenece a Γ.".format(z0))

    # ------------------------------------------------------------------
    # Estados finales F (pueden ser vacíos)
    # ------------------------------------------------------------------
    while True:
        texto = input(
            "Estados finales separados por coma (Enter si F es vacío): "
        ).strip()
        lista, err = _convertir_lista(texto, "FINALES", permitir_vacio=True)
        if err:
            print("Error:", err)
            continue
        finales = set(lista)
        if not finales.issubset(ap.estados):
            ajenos = finales - ap.estados
            print(
                "Error: los siguientes estados finales no pertenecen a Q: {}.".format(
                    sorted(ajenos)
                )
            )
            continue
        ap.estados_finales = finales
        break

    # ------------------------------------------------------------------
    # Transiciones
    # ------------------------------------------------------------------
    print("\nIngrese transiciones en el formato:")
    print("  APD/APND:  origen,entrada,tope,destino,reemplazo")
    print("  APND alt:  origen,entrada,tope,destino1,reemplazo1|destino2,reemplazo2")
    print("  Reemplazo: EPS (desapilar) o tokens separados por ';' (ej. A;Z0)")
    print("  (Línea vacía para terminar.)\n")

    numero_virtual = 1  # Numeración interna para diagnósticos de la entrada manual.
    errores_transicion = []

    while True:
        linea = input("Transición {}: ".format(numero_virtual)).strip()
        if linea == "":
            break

        entradas_man, errs = _parsear_linea_transicion(linea, numero_virtual)
        if errs:
            for e in errs:
                print("  Error:", e)
            print("  La línea no se agregó; corrija e intente de nuevo.")
            continue

        # Validación semántica de pertenencia a Q, Σ, Γ.
        hay_error_semantico = False
        for origen, entrada, tope, destino, reemplazo in entradas_man:
            if origen not in ap.estados:
                print(
                    "  Error: estado origen '{}' no pertenece a Q.".format(origen)
                )
                hay_error_semantico = True
            if entrada != EPS and entrada not in ap.alfabeto:
                print(
                    "  Error: símbolo '{}' no pertenece a Σ ni es EPS.".format(entrada)
                )
                hay_error_semantico = True
            if tope not in ap.alfabeto_pila:
                print(
                    "  Error: tope '{}' no pertenece a Γ.".format(tope)
                )
                hay_error_semantico = True
            if destino not in ap.estados:
                print(
                    "  Error: estado destino '{}' no pertenece a Q.".format(destino)
                )
                hay_error_semantico = True
            for token in reemplazo:
                if token not in ap.alfabeto_pila:
                    print(
                        "  Error: token de reemplazo '{}' no pertenece a Γ.".format(
                            token
                        )
                    )
                    hay_error_semantico = True

        if hay_error_semantico:
            print("  La línea no se agregó; corrija e intente de nuevo.")
            continue

        for origen, entrada, tope, destino, reemplazo in entradas_man:
            agregado = ap.agregar_alternativa(origen, entrada, tope, destino, reemplazo)
            if not agregado:
                print(
                    "  Aviso: transición ({}, {}, {}) -> ({}, {}) ya existe; "
                    "no se agrega.".format(
                        origen, entrada, tope, destino,
                        "EPS" if reemplazo == () else ";".join(reemplazo),
                    )
                )
            else:
                numero_virtual += 1

    # ------------------------------------------------------------------
    # Validación estructural final.
    # ------------------------------------------------------------------
    valido, errores_val = ValidadorAP.validar(ap)
    if not valido:
        print("\nEl autómata no pasó la validación:")
        for e in errores_val:
            print(" -", e)
        return None

    print(
        "\nAutómata '{}' ({}) creado y validado correctamente.".format(
            ap.nombre, ap.tipo
        )
    )
    return ap
