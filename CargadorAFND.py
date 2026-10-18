import re
import os
from AFND import AFND
from CargadorAFD import CargadorAFD
from ValidadorAFND import ValidadorAFND
from ValidadorAFD import ValidadorAFD

class CargadorAFND:
    # Permitimos crear un AFND desde la consola o cargarlo desde un archivo de texto.

    # Identificamos los encabezados y sus valores.
    _PATRON_ENCABEZADO = re.compile(
        r"^(?P<clave>NOMBRE|TIPO|ESTADOS|ALFABETO|INICIAL|FINALES)="
        r"(?P<valor>.*)$"
    )

    # Separamos el origen, símbolo y destinos de cada transición
    _PATRON_TRANSICION = re.compile(
        r"^(?P<origen>[^,\s]+),"
        r"(?P<simbolo>[^,\s]+),"
        r"(?P<destinos>[^,\s]+)$"
    )

    # Representaciones permitidas para un conjunto vacío
    _VACIO = {"∅", "{}"}


    @staticmethod
    def pedir_conjunto_afnd(mensaje, permitir_vacio=False, nombres_estados=False):
        # Pedimos elementos separados por comas y rechazamos vacíos o duplicados.
        
        while True:
            # Obtenemos y limpiamos la entrada
            entrada = input(mensaje).strip()
            
            # Si el campo opcional está vacío, devolvemos un conjunto vacío.
            if entrada == "" and permitir_vacio:
                return set()
            
            # Si el campo es obligatorio, una entrada vacía se pide de nuevo.
            if entrada == "":
                print("La entrada no puede estar vacia.")
                continue
            
            # Separamos la entrada por comas y limpiamos cada elemento.
            partes = entrada.split(",")
            elementos = []
            hay_vacios = False
            
            # Validar cada elemento después de dividir
            for parte in partes:
                elemento = parte.strip()
                
                # Detectar elementos vacíos (ej: "q0,,q1")
                if elemento == "":
                    hay_vacios = True
                    break
                
                elementos.append(elemento)
            
            # Una coma sin contenido entre elementos hace inválida la entrada.
            if hay_vacios:
                print("No se permiten elementos vacios entre comas.")
                continue
            
            # Comparamos las cantidades para detectar elementos repetidos.
            if len(elementos) != len(set(elementos)):
                print("No se permiten estados o símbolos duplicados.")
                continue

            # Compartimos la regla de nombres con la carga de archivos y el AFD.
            if nombres_estados:
                errores = [ValidadorAFD.validar_nombre_estado(elemento) for elemento in elementos]
                if any(errores):
                    for error in errores:
                        if error:
                            print(error)
                    continue
            
            # Si pasó todas las validaciones, retornamos el set
            return set(elementos)
    
    @staticmethod
    def crear_manual():
        # Construimos el AFND pidiendo al usuario cada componente de la quíntupla.
        print("\n=== CREACION MANUAL DEL AFND ===")
        afnd = AFND()
        
        # Primero pedimos un nombre para identificar el AFND.
        # Solicitar nombre hasta que sea válido
        while afnd.nombre.strip() == "":
            afnd.nombre = input("Nombre del automata: ").strip()
            if afnd.nombre == "":
                print("El nombre no puede estar vacio.")
        
        # Luego leemos el conjunto de estados Q.
        # Ejemplo: q0,q1,q2
        afnd.estados = CargadorAFND.pedir_conjunto_afnd(
            "Estados separados por coma (ej. q0,q1,q2): ", nombres_estados=True
        )
        
        # El alfabeto Σ contiene los símbolos que podrá procesar el AFND.
        # Ejemplo: a,b
        while True:
            alfabeto = CargadorAFND.pedir_conjunto_afnd(
                "Simbolos del alfabeto separados por coma (ej. a,b): "
            )

            contiene_epsilon = False
            simbolos_largos = []

            for simbolo in alfabeto:
                if ValidadorAFND.es_simbolo_epsilon(simbolo):
                    contiene_epsilon = True
                elif len(simbolo) != 1 or simbolo.isspace() or not simbolo.isprintable():
                    simbolos_largos.append(simbolo)

            if contiene_epsilon:
                print(
                    "Error: un AFND de esta fase no puede contener transiciones "
                    "epsilon o símbolos que representen la cadena vacía."
                )
                continue

            if len(simbolos_largos) > 0:
                print(
                    "Error: cada símbolo debe tener exactamente un carácter."
                )
                print("Símbolos inválidos:", simbolos_largos)
                continue

            afnd.alfabeto = alfabeto
            break
                
        # El estado inicial q0 debe pertenecer al conjunto Q.
        while True:
            inicial = input("Estado inicial (debe estar en Q): ").strip()
            
            if inicial in afnd.estados:
                afnd.estado_inicial = inicial
                break
            
            print("Error: el estado inicial debe pertenecer al conjunto Q.")
        
        # Los estados finales F deben pertenecer a Q, aunque el conjunto puede quedar vacío.
        while True:
            finales = CargadorAFND.pedir_conjunto_afnd(
                "Estados finales separados por coma (Enter si no hay): ",
                permitir_vacio=True,
                nombres_estados=True,
            )
            
            # Verificar que todos los estados finales estén en Q
            if finales.issubset(afnd.estados):
                afnd.estados_finales = finales
                break
            
            print("Error: todos los estados finales deben pertenecer a Q.")
        
        # Por último, pedimos los posibles destinos de cada pareja de transición.
        print("\nIngrese la función de transición.")
        print("Para cada pareja (estado, símbolo), ingrese el estado(s) destino.")
        print("Puede indicar varios destinos o un conjunto vacío.\n")
        
        # Solicitar las transiciones para CADA combinación (estado, símbolo)
        # Cada pareja admite un conjunto de destinos, incluso vacío.
        print("\nIngrese la función de transición.")
        print("Use | entre destinos o ∅ cuando no exista ninguno.")

        for estado in sorted(afnd.estados):
            for simbolo in sorted(afnd.alfabeto):
                while True:
                    texto = input(
                        "δ(" + estado + ", " + simbolo + ") = "
                    ).strip()

                    # Convertimos la entrada en un conjunto de destinos
                    destinos, error = CargadorAFND.convertir_destinos(texto)

                    if error is not None:
                        print(error)
                        continue

                    # Todos los destinos deben pertenecer a Q
                    if not destinos.issubset(afnd.estados):
                        print("Todos los destinos deben pertenecer a Q.")
                        continue

                    # Guardamos el conjunto completo en una sola llamada
                    afnd.agregar_transicion(estado, simbolo, destinos)
                    break
        
        return afnd

    
    @staticmethod
    def cargar_archivo(ruta):
        # Cargamos el AFND desde un archivo y mostramos cualquier error encontrado.

        # Validar extensión antes de intentar abrir el archivo.
        # Se acepta .txt en cualquier combinación de mayúsculas/minúsculas.
        ruta_normalizada = CargadorAFD.normalizar_ruta(ruta)
        _, extension = os.path.splitext(ruta_normalizada)
        if extension.lower() != ".txt":
            print("Error: el archivo debe tener extensión .txt")
            return None

        # Leemos el archivo y quitamos espacios en los extremos
        try:
            with open(ruta_normalizada, "r", encoding="utf-8-sig") as archivo:
                lineas = [linea.strip() for linea in archivo]
        except (OSError, UnicodeError, ValueError) as error:
            print("No se pudo leer el archivo:", error)
            return None

        # Guardamos los encabezados, transiciones y errores
        encabezados = {}
        transiciones = []
        errores = []
        en_transiciones = False

        # Recorremos las líneas conservando su número
        for numero_linea, linea in enumerate(lineas, start=1):

            # Identificamos el inicio de las transiciones
            if linea == "TRANSICIONES:":
                if en_transiciones:
                    errores.append(
                        "Línea " + str(numero_linea)
                        + ": sección TRANSICIONES repetida."
                    )

                en_transiciones = True
                continue

            # No permitimos líneas vacías
            if linea == "":
                errores.append(
                    "Línea " + str(numero_linea)
                    + ": no se permiten líneas vacías."
                )
                continue

            # Antes de TRANSICIONES, procesamos los encabezados
            if not en_transiciones:
                coincidencia = (
                    CargadorAFND._PATRON_ENCABEZADO.fullmatch(linea)
                )

                if coincidencia is None:
                    errores.append(
                        "Línea " + str(numero_linea)
                        + ": encabezado con formato inválido."
                    )
                    continue

                clave = coincidencia.group("clave")
                valor = coincidencia.group("valor").strip()

                # Cada encabezado debe aparecer una sola vez
                if clave in encabezados:
                    errores.append(
                        "Línea " + str(numero_linea)
                        + ": encabezado repetido '" + clave + "'."
                    )
                else:
                    encabezados[clave] = valor

                continue

            # Después de TRANSICIONES, procesamos sus componentes
            coincidencia = (
                CargadorAFND._PATRON_TRANSICION.fullmatch(linea)
            )

            if coincidencia is None:
                errores.append(
                    "Línea " + str(numero_linea)
                    + ": use origen,símbolo,destino1|destino2 "
                    + "o origen,símbolo,∅."
                )
                continue

            # Guardamos la transición para validarla después
            transiciones.append(
                (
                    coincidencia.group("origen"),
                    coincidencia.group("simbolo"),
                    coincidencia.group("destinos"),
                    numero_linea
                )
            )

        # Revisamos los encabezados después de leer todo el archivo
        requeridos = {
            "NOMBRE",
            "TIPO",
            "ESTADOS",
            "ALFABETO",
            "INICIAL",
            "FINALES"
        }

        for clave in sorted(requeridos - set(encabezados)):
            errores.append("Falta el encabezado " + clave + ".")

        if not en_transiciones:
            errores.append("Falta la línea TRANSICIONES:.")

        # Validamos los campos presentes sin repetir errores por ausencia
        if "TIPO" in encabezados:
            if encabezados["TIPO"].upper() != "AFND":
                errores.append("TIPO debe ser AFND.")

        if "NOMBRE" in encabezados:
            if encabezados["NOMBRE"] == "":
                errores.append("NOMBRE no puede estar vacío.")

        # Si la estructura del archivo falla, cancelamos la carga
        if errores:
            print("\nErrores de sintaxis:")
            for error in errores:
                print("- " + error)
            return None

        # Construimos el AFND con los datos leídos
        afnd, errores = CargadorAFND.construir_afnd(
            encabezados,
            transiciones
        )

        # Mostramos los errores encontrados en los componentes
        if errores:
            print("\nErrores en los datos:")
            for error in errores:
                print("- " + error)
            return None

        # La carga solo termina si todos los componentes del AFND son válidos.
        valido, errores = ValidadorAFND.validar(afnd)
        if not valido:
            for error in errores:
                print("-", error)
            return None
        return afnd

    @staticmethod
    def construir_afnd(encabezados, transiciones):
            # Convertimos los textos ya validados en conjuntos y transiciones.
            errores = []
            afnd = AFND(encabezados["NOMBRE"].strip())
            estados, error = CargadorAFD.convertir_lista_archivo(
                encabezados["ESTADOS"], "ESTADOS", False
            )
            if error:
                errores.append(error)
            alfabeto, error = CargadorAFD.convertir_lista_archivo(
                encabezados["ALFABETO"], "ALFABETO", False
            )
            if error:
                errores.append(error)
            finales, error = CargadorAFD.convertir_lista_archivo(
                encabezados["FINALES"], "FINALES", True
            )
            if error:
                errores.append(error)

            if errores:
                return None, errores

            afnd.estados = estados
            afnd.alfabeto = alfabeto
            afnd.estado_inicial = encabezados["INICIAL"].strip()
            afnd.estados_finales = finales

            error_alfabeto=ValidadorAFND.validar_alfabeto(alfabeto)
            if error_alfabeto:
                errores.append(error_alfabeto)
            if afnd.estado_inicial not in estados:
                errores.append("INICIAL no pertenece al conjunto Q.")
            if not finales.issubset(estados):
                errores.append("FINALES contiene estados que no pertenecen a Q.")

            for origen, simbolo, texto_destinos, numero_linea in transiciones:
                destinos, error = CargadorAFND.convertir_destinos(texto_destinos)
                if origen not in estados:
                    errores.append(
                        "Línea " + str(numero_linea) + ": origen inexistente '" + origen + "'."   
                    )
                elif ValidadorAFND.es_simbolo_epsilon(simbolo):
                    errores.append(
                        "Línea "
                        + str(numero_linea)
                        + ": las transiciones epsilon no forman parte de esta fase."
                    )
                elif simbolo not in alfabeto:
                    errores.append(
                        "Línea " + str(numero_linea) + ": símbolo inexistente '" + simbolo + "'."
                    )
                elif error is not None:
                    errores.append("Línea " + str(numero_linea) + ": " + error)
                elif not destinos.issubset(estados):
                    inexistentes= destinos-estados
                    errores.append(
                        "Línea "
                        + str(numero_linea)
                        + ": destinos inexistentes "
                        + str(sorted(inexistentes))
                        + "."
                    )
                else:
                    afnd.agregar_transicion(origen,simbolo,destinos)

            return afnd, errores

    @staticmethod
    def convertir_destinos(texto):
        # Convertimos destino1|destino2 en un conjunto; ∅ produce set().
        texto =texto.strip()
        if texto in CargadorAFND._VACIO:
            return set(), None
        if texto == "":
            return None, "El destino no puede quedar vacío; use ∅."
        partes = [parte.strip() for parte in texto.split("|")]
        if "" in partes:
                return None, "Existen destinos vacíos entre separadores |."
        if len(partes) != len(set(partes)):
                return None, "Existen destinos duplicados."
        if any(parte in CargadorAFND._VACIO for parte in partes):
                return None, "∅ no puede combinarse con otros destinos."
        for parte in partes:
            error = ValidadorAFD.validar_nombre_estado(parte)
            if error:
                return None, error
        return set(partes), None
