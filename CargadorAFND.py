import re
from AFND import AFND
from CargadorAFD import CargadorAFD
from ValidadorAFND import ValidadorAFND
from ValidadorAFD import ValidadorAFD

class CargadorAFND:
    """
Gestiona la creación de AFND de dos formas:
1. Creación manual: el usuario ingresa manualmente Q, Σ, q0, F y δ
2. Carga desde archivo: lee un archivo .txt con formato específico

Formato de archivo esperado:
├─ NOMBRE=MiAFND
├─ TIPO=AFND
├─ ESTADOS=q0,q1,q2
├─ ALFABETO=a,b
├─ INICIAL=q0
├─ FINALES=q2
├─ TRANSICIONES:
├─ q0,a,q0|q1 ---> la barra vertical separa los diferentes destinos
├─ q0,b,q0
├─ q1,a,q2
└─ q1,b,q1
    """

        # Identificamos los encabezados y sus valores
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
        """
        Solicita al usuario un conjunto de elementos separados por comas.
        Valida que no haya elementos vacíos ni duplicados.
        
        Parámetros:
            mensaje: Texto que se muestra al usuario pidiendo entrada
            permitir_vacio: Si True, acepta entrada vacía; si False, requiere al menos un elemento
        
        Retorna:
            Un set con los elementos ingresados, o set vacío si se permite y el usuario ingresa vacío
        
        Ejemplo:
            pedir_conjunto("Estados: ") -> {"q0", "q1", "q2"}
        """
        
        while True:
            # Obtenemos y limpiamos la entrada
            entrada = input(mensaje).strip()
            
            # ========== CASO: ENTRADA VACÍA ==========
            # Si la entrada está vacía y se permite, retornamos set vacío
            if entrada == "" and permitir_vacio:
                return set()
            
            # Si la entrada está vacía pero NO se permite, pedimos de nuevo
            if entrada == "":
                print("La entrada no puede estar vacia.")
                continue
            
            # ========== PROCESAR ENTRADA ==========
            # Dividimos por comas y limpiamos espacios de cada elemento
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
            
            # ========== VALIDACIÓN: SIN ESPACIOS VACÍOS ==========
            if hay_vacios:
                print("No se permiten elementos vacios entre comas.")
                continue
            
            # ========== VALIDACIÓN: SIN DUPLICADOS ==========
            # Comparamos cantidad de elementos con cantidad de elementos únicos
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
        """
        Guía al usuario a través de la creación manual de un AFND.
        Solicita los 5 componentes: Q, Σ, q0, F, δ
        """
        print("\n=== CREACION MANUAL DEL AFND ===")
        afnd = AFND()
        
        # ========== PASO 1: NOMBRE DEL AFND ==========
        # Solicitar nombre hasta que sea válido
        while afnd.nombre.strip() == "":
            afnd.nombre = input("Nombre del automata: ").strip()
            if afnd.nombre == "":
                print("El nombre no puede estar vacio.")
        
        # ========== PASO 2: CONJUNTO DE ESTADOS (Q) ==========
        # Ejemplo: q0,q1,q2
        afnd.estados = CargadorAFND.pedir_conjunto_afnd(
            "Estados separados por coma (ej. q0,q1,q2): ", nombres_estados=True
        )
        
        # ========== PASO 3: ALFABETO (Σ) ==========
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
                
        # ========== PASO 4: ESTADO INICIAL (q0) ==========
        # Debe ser un elemento de Q
        while True:
            inicial = input("Estado inicial (debe estar en Q): ").strip()
            
            if inicial in afnd.estados:
                afnd.estado_inicial = inicial
                break
            
            print("Error: el estado inicial debe pertenecer al conjunto Q.")
        
        # ========== PASO 5: ESTADOS FINALES (F) ==========
        # Deben ser un subconjunto de Q. Pueden estar vacíos.
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
        
        # ========== PASO 6: FUNCIÓN DE TRANSICIÓN (δ) ==========
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
        """Carga un AFND y muestra los errores encontrados."""

        # Leemos el archivo y quitamos espacios en los extremos
        try:
            with open(CargadorAFD.normalizar_ruta(ruta), "r", encoding="utf-8-sig") as archivo:
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
            #Convierte los textos validados en conjuntos y transiciones.#
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
        #Convierte destino1|destino2 en un conjunto;  ∅ produce set().#
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
