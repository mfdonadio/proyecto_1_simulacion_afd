import re
import ValidadorAFD
import AFD

class CargadorAFD:
    """
    Gestiona la creación de AFD de dos formas:
    1. Creación manual: el usuario ingresa manualmente Q, Σ, q0, F y δ
    2. Carga desde archivo: lee un archivo .txt con formato específico
    
    Formato de archivo esperado:
    ├─ NOMBRE=MiAFD
    ├─ ESTADOS=q0,q1,q2
    ├─ ALFABETO=a,b
    ├─ INICIAL=q0
    ├─ FINALES=q2
    ├─ TRANSICIONES:
    ├─ q0,a,q1
    ├─ q0,b,q0
    ├─ q1,a,q2
    └─ q1,b,q1
    """

    @staticmethod
    def pedir_conjunto(mensaje, permitir_vacio=False):
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
            
            # Si pasó todas las validaciones, retornamos el set
            return set(elementos)

    @staticmethod
    def crear_manual():
        """
        Guía al usuario a través de la creación manual de un AFD.
        Solicita los 5 componentes: Q, Σ, q0, F, δ
        """
        print("\n=== CREACION MANUAL DEL AFD ===")
        afd = AFD()
        
        # ========== PASO 1: NOMBRE DEL AFD ==========
        # Solicitar nombre hasta que sea válido
        while afd.nombre.strip() == "":
            afd.nombre = input("Nombre del automata: ").strip()
            if afd.nombre == "":
                print("El nombre no puede estar vacio.")
        
        # ========== PASO 2: CONJUNTO DE ESTADOS (Q) ==========
        # Ejemplo: q0,q1,q2
        afd.estados = CargadorAFD.pedir_conjunto(
            "Estados separados por coma (ej. q0,q1,q2): "
        )
        
        # ========== PASO 3: ALFABETO (Σ) ==========
        # Ejemplo: a,b
        while True:
            alfabeto = CargadorAFD.pedir_conjunto(
                "Simbolos del alfabeto separados por coma (ej. a,b): "
            )

            contiene_epsilon = False
            simbolos_largos = []

            for simbolo in alfabeto:
                if ValidadorAFD.es_simbolo_epsilon(simbolo):
                    contiene_epsilon = True
                elif len(simbolo) != 1:
                    simbolos_largos.append(simbolo)

            if contiene_epsilon:
                print(
                    "Error: un AFD no puede contener transiciones "
                    "epsilon o símbolos que representen la cadena vacía."
                )
                continue

            if len(simbolos_largos) > 0:
                print(
                    "Error: cada símbolo debe tener exactamente un carácter."
                )
                print("Símbolos inválidos:", simbolos_largos)
                continue

            afd.alfabeto = alfabeto
            break
                
        # ========== PASO 4: ESTADO INICIAL (q0) ==========
        # Debe ser un elemento de Q
        while True:
            inicial = input("Estado inicial (debe estar en Q): ").strip()
            
            if inicial in afd.estados:
                afd.estado_inicial = inicial
                break
            
            print("Error: el estado inicial debe pertenecer al conjunto Q.")
        
        # ========== PASO 5: ESTADOS FINALES (F) ==========
        # Deben ser un subconjunto de Q. Pueden estar vacíos.
        while True:
            finales = CargadorAFD.pedir_conjunto(
                "Estados finales separados por coma (Enter si no hay): ",
                permitir_vacio=True,
            )
            
            # Verificar que todos los estados finales estén en Q
            if finales.issubset(afd.estados):
                afd.estados_finales = finales
                break
            
            print("Error: todos los estados finales deben pertenecer a Q.")
        
        # ========== PASO 6: FUNCIÓN DE TRANSICIÓN (δ) ==========
        print("\nIngrese la función de transición.")
        print("Para cada pareja (estado, símbolo), ingrese el estado destino.")
        print("Esto creará un AFD completo y determinista.\n")
        
        # Solicitar una transición para CADA combinación (estado, símbolo)
        # Al hacerlo así, el AFD es automáticamente determinista y completo
        for estado in sorted(afd.estados):
            for simbolo in sorted(afd.alfabeto):
                while True:
                    destino = input(
                        "δ(" + estado + ", " + simbolo + ") = "
                    ).strip()
                    
                    # El destino debe ser un estado válido
                    if destino in afd.estados:
                        afd.agregar_transicion(estado, simbolo, destino)
                        break
                    
                    print("Error: el estado destino debe pertenecer a Q.")
        
        return afd

    # ========== PATRONES REGEX PARA VALIDACIÓN DE ARCHIVOS ==========
    # Expresiones regulares para validar la sintaxis del archivo .txt
    # Cada patrón valida una línea específica del archivo
    _PATRON_ENCABEZADO = {
        "NOMBRE": re.compile(r"^NOMBRE=(?P<valor>.+)$"),
        "ESTADOS": re.compile(r"^ESTADOS=(?P<valor>.+)$"),
        "ALFABETO": re.compile(r"^ALFABETO=(?P<valor>.+)$"),
        "INICIAL": re.compile(r"^INICIAL=(?P<valor>.+)$"),
        "FINALES": re.compile(r"^FINALES=(?P<valor>.*)$"),
    }
    # Patrón para transiciones: origen,símbolo,destino (sin espacios)
    _PATRON_TRANSICION = re.compile(
        r"^(?P<origen>[^,\s]+),(?P<simbolo>[^,\s]+),(?P<destino>[^,\s]+)$"
    )

    @staticmethod
    def cargar_archivo(ruta):
        """
        Carga un AFD desde un archivo .txt con formato específico.
        
        Formato esperado:
            Línea 1: NOMBRE=NombreDelAFD
            Línea 2: ESTADOS=q0,q1,q2,...
            Línea 3: ALFABETO=a,b,c,...
            Línea 4: INICIAL=q0
            Línea 5: FINALES=q1,q2,...  (puede ser vacío)
            Línea 6: TRANSICIONES:
            Líneas 7+: origen,símbolo,destino
        
        Parámetros:
            ruta: Ruta al archivo .txt
        
        Retorna:
            Objeto AFD si se cargó correctamente, None si hay errores
        """
        
        # ========== PASO 1: LEER EL ARCHIVO ==========
        try:
            archivo = open(ruta, "r", encoding="utf-8")
            lineas = archivo.readlines()
            archivo.close()
        except Exception as error:
            print("Error: No fue posible abrir el archivo:", error)
            return None
        
        # ========== PASO 2: LIMPIAR LÍNEAS ==========
        # Removemos saltos de línea pero preservamos líneas vacías
        # para reportar errores con número de línea exacto
        limpias = []
        for linea in lineas:
            limpias.append(linea.strip())
        
        # Verificar estructura mínima: al menos 6 líneas
        if len(limpias) < 6:
            print("Error: El archivo no contiene la estructura mínima requerida.")
            print("Se necesitan 6 líneas mínimo (encabezados + TRANSICIONES:)")
            return None
        
        afd = AFD()
        errores = []
        
        # ========== PASO 3: VALIDAR ENCABEZADOS ==========
        # Las primeras 5 líneas deben cumplir el patrón CLAVE=valor
        claves_orden = ["NOMBRE", "ESTADOS", "ALFABETO", "INICIAL", "FINALES"]
        valores_encabezado = {}
        
        for indice, clave in enumerate(claves_orden):
            # Validar con expresión regular
            coincidencia = CargadorAFD._PATRON_ENCABEZADO[clave].match(limpias[indice])
            
            if coincidencia is None:
                # Error de sintaxis: la línea no sigue el patrón esperado
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": se esperaba el patrón '"
                    + clave
                    + "=...'."
                )
            else:
                # Extraer el valor después del "="
                valores_encabezado[clave] = coincidencia.group("valor").strip()
        
        # Validar línea 6: debe ser exactamente "TRANSICIONES:"
        if not re.match(r"^TRANSICIONES:$", limpias[5]):
            errores.append("Línea 6: se esperaba exactamente 'TRANSICIONES:'.")
        
        # Si hay errores de sintaxis, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None
        
        # ========== PASO 4: EXTRAER COMPONENTES ==========
        afd.nombre = valores_encabezado["NOMBRE"]
        
        estados_texto = valores_encabezado["ESTADOS"]
        alfabeto_texto = valores_encabezado["ALFABETO"]
        afd.estado_inicial = valores_encabezado["INICIAL"]
        finales_texto = valores_encabezado["FINALES"]
        
        # Convertir strings a sets, validando duplicados
        estados, error_estados = CargadorAFD._convertir_lista_archivo(
            estados_texto, "ESTADOS", permitir_vacio=False
        )
        alfabeto, error_alfabeto = CargadorAFD._convertir_lista_archivo(
            alfabeto_texto, "ALFABETO", permitir_vacio=False
        )
        finales, error_finales = CargadorAFD._convertir_lista_archivo(
            finales_texto, "FINALES", permitir_vacio=True
        )

        # ========== VALIDAR SÍMBOLOS DEL ALFABETO DEL ARCHIVO ==========
        if error_alfabeto is None:
            for simbolo in alfabeto:
                if ValidadorAFD.es_simbolo_epsilon(simbolo):
                    errores.append(
                        "Línea 3: el alfabeto de un AFD no puede contener ε."
                    )
                elif len(simbolo) != 1:
                    errores.append(
                        "Línea 3: el símbolo '"
                        + simbolo
                        + "' debe tener exactamente un carácter."
                    )


        # Verificar si hubo errores al convertir
        if error_estados is not None:
            errores.append(error_estados)
        if error_alfabeto is not None:
            errores.append(error_alfabeto)
        if error_finales is not None:
            errores.append(error_finales)
        
        # Si hay errores de validación semántica, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron problemas en los datos:")
            for error in errores:
                print("-", error)
            return None
        
        # Asignar componentes validados al AFD
        afd.estados = estados
        afd.alfabeto = alfabeto
        afd.estados_finales = finales
        
        # ========== PASO 5: PROCESAR TRANSICIONES ==========
        # Las líneas después de "TRANSICIONES:" contienen las transiciones
        # Cada línea debe cumplir el patrón: origen,símbolo,destino
        for indice in range(6, len(limpias)):
            linea = limpias[indice]
            
            # No se permiten líneas vacías en la sección de transiciones
            if linea == "":
                errores.append(
                    "Línea " + str(indice + 1) + ": no se permiten líneas vacías."
                )
                continue
            
            # Validar formato de transición
            coincidencia = CargadorAFD._PATRON_TRANSICION.match(linea)
            
            if coincidencia is None:
                errores.append(
                    "Línea "
                    + str(indice + 1)
                    + ": una transición debe tener formato origen,símbolo,destino "
                    + "(sin espacios ni campos vacíos)."
                )
                continue
            
            # Extraer componentes de la transición
            origen = coincidencia.group("origen")
            simbolo = coincidencia.group("simbolo")
            destino = coincidencia.group("destino")
            
            # ========== VALIDACIÓN SEMÁNTICA DE LA TRANSICIÓN ==========
            linea_valida = True
            numero_linea = indice + 1

            # El estado origen debe existir en Q
            if origen not in afd.estados:
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": el estado origen '"
                    + origen
                    + "' no pertenece a Q."
                )
                linea_valida = False

            # El símbolo no puede representar epsilon
            if ValidadorAFD.es_simbolo_epsilon(simbolo):
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": no se permiten transiciones ε en un AFD."
                )
                linea_valida = False

            # El símbolo debe tener un solo carácter
            elif len(simbolo) != 1:
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": el símbolo '"
                    + simbolo
                    + "' debe tener exactamente un carácter."
                )
                linea_valida = False

            # El símbolo debe pertenecer al alfabeto
            elif simbolo not in afd.alfabeto:
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": el símbolo '"
                    + simbolo
                    + "' no pertenece al alfabeto Σ."
                )
                linea_valida = False

            # El estado destino debe existir en Q
            if destino not in afd.estados:
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": el estado destino '"
                    + destino
                    + "' no pertenece a Q."
                )
                linea_valida = False

            # Si la línea contiene algún error, no se agrega a δ
            if not linea_valida:
                continue

            # Detectar múltiples transiciones para la misma pareja
            if not afd.agregar_transicion(origen, simbolo, destino):
                errores.append(
                    "Línea "
                    + str(numero_linea)
                    + ": existen múltiples transiciones para ("
                    + origen
                    + ", "
                    + simbolo
                    + ")."
                )
        
        # Si hay errores, reportar y salir
        if len(errores) > 0:
            print("\nError: Se encontraron errores de sintaxis:")
            for error in errores:
                print("-", error)
            return None
        
        return afd

    @staticmethod
    def _convertir_lista_archivo(texto, nombre_campo, permitir_vacio):
        """
        Convierte un string separado por comas en un set.
        Valida que no haya elementos vacíos ni duplicados.
        
        Parámetros:
            texto: String con elementos separados por comas
            nombre_campo: Nombre del campo (para mensajes de error)
            permitir_vacio: Si False, requiere al menos un elemento
        
        Retorna:
            Tupla (set_elementos, error_mensaje)
            Si no hay error, error_mensaje es None
        """
        # ========== CASO: CAMPO VACÍO ==========
        if texto == "":
            if permitir_vacio:
                # Si se permite vacío (e.g., FINALES), retornar set vacío
                return set(), None
            # Si no se permite (e.g., ESTADOS), retornar error
            return None, "Error: El campo " + nombre_campo + " no puede estar vacío."
        
        # ========== PROCESAR ELEMENTOS ==========
        partes = texto.split(",")
        elementos = []
        
        for parte in partes:
            elemento = parte.strip()
            
            # Detectar elementos vacíos (ej: "q0,,q1")
            if elemento == "":
                return None, (
                    "Error: El campo " + nombre_campo + " contiene un elemento vacío."
                )
            
            elementos.append(elemento)
        
        # ========== VALIDAR DUPLICADOS ==========
        if len(elementos) != len(set(elementos)):
            return None, (
                "Error: El campo " + nombre_campo + " contiene elementos duplicados."
            )
        
        return set(elementos), None
