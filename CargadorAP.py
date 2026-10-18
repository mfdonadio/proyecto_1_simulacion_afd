# Este módulo permite cargar un APD o APND desde un archivo y crearlo a mano.
# Si la definición tiene errores, las funciones públicas muestran el diagnóstico
# y devuelven None para que el programa conserve el autómata activo anterior.
# EPS representa un desapilado, mientras que ";" separa los símbolos que se
# insertan en la pila. Las alternativas de un APND se separan con "|".

import re
import os

from AutomataPila import AutomataPila, EPS
import ValidadorAP
# Reutilizamos normalizar_ruta de CargadorAFD para manejar comillas y espacios.
from CargadorAFD import CargadorAFD

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


# Estas funciones convierten el texto del archivo en los datos internos del AP.

def _parsear_reemplazo(texto):
    # Convertimos el reemplazo en una tupla y devolvemos aparte cualquier error.
    # EPS se convierte en (), y los demás símbolos se separan mediante ";".
    if texto == "":
        return None, "El campo reemplazo no puede estar vacío."

    if texto == EPS:
        # Cuando el reemplazo es EPS, quitamos el tope sin insertar otro símbolo.
        return (), None

    # Los demás reemplazos se separan por ";" para conservar símbolos como Z0.
    partes = texto.split(";")

    tokens = []
    for parte in partes:
        tok = parte.strip()
        if tok == "":
            return None, (
                "Reemplazo '{}': campo vacío entre separadores ';'.".format(texto)
            )
        if tok == EPS:
            # EPS debe aparecer solo, porque representa un reemplazo vacío.
            return None, (
                "Reemplazo '{}': EPS no puede mezclarse con otros tokens.".format(texto)
            )
        tokens.append(tok)

    return tuple(tokens), None


def _parsear_linea_transicion(linea, numero):
    # El primer tramo define origen, entrada, tope, destino y reemplazo.
    # Las alternativas posteriores solo cambian destino y reemplazo, por lo que
    # heredan los tres primeros datos. También devolvemos los errores encontrados.
    errores = []

    # Separamos con "|" el tramo principal de las alternativas adicionales.
    tramos = linea.split("|")

    # Primero comprobamos los cinco campos obligatorios de la transición.
    campos_primer = tramos[0].split(",")
    if len(campos_primer) != 5:
        errores.append(
            "Línea {}: se esperaban 5 campos (origen,entrada,tope,destino,reemplazo), "
            "se encontraron {}: '{}'.".format(numero, len(campos_primer), tramos[0])
        )
        return None, errores

    origen, entrada, tope, destino1, reemplazo1_txt = [c.strip() for c in campos_primer]

    # Comprobamos que ninguno de los cinco campos obligatorios esté vacío.
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

    # El origen, el tope y el destino no admiten separadores ni espacios.
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

    # EPS no puede usarse como tope porque no es un símbolo de Γ.
    if tope == EPS:
        errores.append(
            "Línea {}: el tope de pila no puede ser EPS.".format(numero)
        )

    # Convertimos también el reemplazo del primer tramo a su forma interna.
    reemplazo1, error_remp = _parsear_reemplazo(reemplazo1_txt)
    if error_remp is not None:
        errores.append("Línea {}: {}.".format(numero, error_remp))

    if errores:
        return None, errores

    resultado = [(origen, entrada, tope, destino1, reemplazo1)]

    # Después procesamos las alternativas adicionales que puede tener un APND.
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
    # Convertimos un campo separado por comas en una lista sin duplicados.
    # El resultado y el posible mensaje de error se devuelven por separado.
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

    # Buscamos duplicados antes de convertir la lista en un conjunto.
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
    # Armamos el AP con los encabezados y las transiciones ya separadas.
    # Los problemas se agregan a errores_acum para poder mostrarlos juntos.
    ap = AutomataPila()

    # Comenzamos con el nombre y el tipo declarados en el archivo.
    nombre = datos_enc.get("NOMBRE", "").strip()
    if nombre == "":
        errores_acum.append("NOMBRE no puede estar vacío.")
    ap.nombre = nombre

    tipo = datos_enc.get("TIPO", "").strip()
    if tipo not in ("APD", "APND"):
        errores_acum.append(
            "TIPO debe ser APD o APND; se encontró '{}'.".format(tipo)
        )
    ap.tipo = tipo

    # Luego convertimos los campos que representan conjuntos del autómata.
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

    # Detectamos EPS en Σ o Γ desde los encabezados para dar un mensaje directo.
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

    # Guardamos el estado inicial y el símbolo que inicia la pila.
    ap.estado_inicial = datos_enc.get("INICIAL", "").strip()

    ap.simbolo_inicial_pila = datos_enc.get("INICIAL_PILA", "").strip()

    # Si los encabezados fallaron, evitamos producir errores en cascada.
    if errores_acum:
        return None

    # Con la definición básica correcta, ya podemos procesar las transiciones.
    for numero_linea, texto_linea in lineas_transicion:
        entradas, errs_linea = _parsear_linea_transicion(texto_linea, numero_linea)
        if errs_linea:
            errores_acum.extend(errs_linea)
            continue

        # Después de revisar la sintaxis, comprobamos la pertenencia a Q, Σ y Γ.
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

            # El modelo devuelve False cuando la alternativa es un duplicado exacto.
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


def cargar_archivo(ruta):
    # Cargamos y validamos el archivo completo antes de devolver el AP.
    # Ante cualquier error se muestra el diagnóstico y se devuelve None.
    # Primero normalizamos la ruta y comprobamos que sea un archivo de texto.
    try:
        ruta_norm = CargadorAFD.normalizar_ruta(ruta)
    except ValueError as exc:
        print("Error en la ruta:", exc)
        return None

    _, ext = os.path.splitext(ruta_norm)
    if ext.lower() != ".txt":
        print("Error: el archivo debe tener extensión .txt")
        return None

    # Abrimos el archivo con soporte para UTF-8 y su marca BOM opcional.
    try:
        with open(ruta_norm, "r", encoding="utf-8-sig") as archivo:
            lineas = archivo.readlines()
    except (OSError, UnicodeError, ValueError) as exc:
        print("Error: no fue posible abrir el archivo:", exc)
        return None

    # Separamos los encabezados de las líneas que definen transiciones.
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
            # Al entrar en TRANSICIONES, cada línea debe describir una transición.
            if linea_limpia == "":
                # Línea vacía es un error de formato en el cuerpo del AP.
                errores.append(
                    "Línea {}: no se permiten líneas vacías en la sección "
                    "TRANSICIONES.".format(numero)
                )
                continue
            lineas_transicion.append((numero, linea_limpia))
            continue

        # Antes de TRANSICIONES solo esperamos encabezados con sus valores.
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

        # Interpretamos la línea como un encabezado con la forma CLAVE=valor.
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

    # El marcador TRANSICIONES: es obligatorio aunque la sección quede vacía.
    if not en_transiciones and not errores:
        errores.append("No se encontró el marcador 'TRANSICIONES:'.")

    # También comprobamos que no falte ningún encabezado obligatorio.
    for enc in _ENCABEZADOS_AP:
        if enc not in enc_vistos:
            errores.append("Encabezado obligatorio '{}' no encontrado.".format(enc))

    if errores:
        print("\nError al cargar el archivo:")
        for e in errores:
            print(" -", e)
        return None

    # Con el formato revisado, construimos el AP con los datos obtenidos.
    errores_construccion = []
    ap = _construir_ap_desde_datos(datos_enc, lineas_transicion, errores_construccion)

    if errores_construccion or ap is None:
        print("\nError en la definición del autómata:")
        for e in errores_construccion:
            print(" -", e)
        return None

    # Al final comprobamos tanto la estructura como el determinismo declarado.
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


def crear_manual():
    # Pedimos uno por uno los componentes de la séptupla del AP.
    # Devolvemos el autómata validado, o None si se cancela o queda inválido.
    print("\n=== CREACION MANUAL DEL AUTOMATA DE PILA ===")
    print("(Presione Enter en el nombre para cancelar.)")

    ap = AutomataPila()

    # Empezamos por el nombre, que también permite cancelar la creación.
    while True:
        nombre = input("Nombre del autómata: ").strip()
        if nombre == "":
            print("Creación cancelada.")
            return None
        ap.nombre = nombre
        break

    # El tipo indica si se aplicarán las reglas de APD o de APND.
    while True:
        tipo = input("Tipo (APD / APND): ").strip().upper()
        if tipo in ("APD", "APND"):
            ap.tipo = tipo
            break
        print("Error: el tipo debe ser APD o APND.")

    # Recibimos el conjunto de estados Q sin aceptar duplicados.
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

    # El alfabeto de entrada puede quedar vacío si el autómata solo usa EPS.
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

    # El alfabeto de pila debe contener al menos el símbolo inicial que se elegirá.
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

    # El estado inicial debe ser uno de los estados definidos en Q.
    while True:
        q0 = input("Estado inicial (debe estar en Q): ").strip()
        if q0 in ap.estados:
            ap.estado_inicial = q0
            break
        print("Error: '{}' no pertenece a Q.".format(q0))

    # El símbolo inicial de pila debe pertenecer a Γ.
    while True:
        z0 = input("Símbolo inicial de pila Z0 (debe estar en Γ): ").strip()
        if z0 in ap.alfabeto_pila:
            ap.simbolo_inicial_pila = z0
            break
        print("Error: '{}' no pertenece a Γ.".format(z0))

    # Los estados finales pueden quedar vacíos, pero ninguno puede estar fuera de Q.
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

    # Por último recibimos las transiciones hasta que el usuario deje la línea vacía.
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

        # Con la sintaxis correcta, comprobamos la pertenencia a Q, Σ y Γ.
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

    # Antes de entregar el AP hacemos una última validación de toda la estructura.
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
