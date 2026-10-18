import re
import os
from ValidadorAFD import ValidadorAFD
from AFD import AFD

class CargadorAFD:
    # Permitimos crear un AFD desde la consola o cargarlo desde un archivo de texto.

    @staticmethod
    def pedir_conjunto(mensaje, permitir_vacio=False, nombres_estados=False):
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

            # Usamos la misma regla en consola, archivos y validación estructural.
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
        # Construimos el AFD pidiendo al usuario cada componente de la quíntupla.
        print("\n=== CREACION MANUAL DEL AFD ===")
        afd = AFD()
        
        # Primero pedimos un nombre para identificar el AFD.
        # Solicitar nombre hasta que sea válido
        while afd.nombre.strip() == "":
            afd.nombre = input("Nombre del automata: ").strip()
            if afd.nombre == "":
                print("El nombre no puede estar vacio.")
        
        # Luego leemos el conjunto de estados Q.
        # Ejemplo: q0,q1,q2
        afd.estados = CargadorAFD.pedir_conjunto(
            "Estados separados por coma (ej. q0,q1,q2): ", nombres_estados=True
        )
        
        # El alfabeto Σ contiene los símbolos que podrá procesar el AFD.
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
                elif len(simbolo) != 1 or simbolo.isspace() or not simbolo.isprintable():
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
                
        # El estado inicial q0 debe pertenecer al conjunto Q.
        while True:
            inicial = input("Estado inicial (debe estar en Q): ").strip()
            
            if inicial in afd.estados:
                afd.estado_inicial = inicial
                break
            
            print("Error: el estado inicial debe pertenecer al conjunto Q.")
        
        # Los estados finales F deben pertenecer a Q, aunque el conjunto puede quedar vacío.
        while True:
            finales = CargadorAFD.pedir_conjunto(
                "Estados finales separados por coma (Enter si no hay): ",
                permitir_vacio=True,
                nombres_estados=True,
            )
            
            # Verificar que todos los estados finales estén en Q
            if finales.issubset(afd.estados):
                afd.estados_finales = finales
                break
            
            print("Error: todos los estados finales deben pertenecer a Q.")
        
        # Por último, pedimos una transición por cada pareja de estado y símbolo.
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

    # Estos patrones describen la sintaxis permitida en los archivos de AFD.
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
    def normalizar_ruta(ruta):
        # Interpretamos las rutas relativas desde la carpeta donde se ejecutó Python.
        ruta = os.fspath(ruta)
        if isinstance(ruta, str):
            ruta = ruta.strip()
            # Solo quitamos un par de comillas exteriores coincidentes.
            if len(ruta) >= 2 and ruta[0] == ruta[-1] and ruta[0] in ("'", '"'):
                ruta = ruta[1:-1]
            if "\x00" in ruta:
                raise ValueError("La ruta no puede contener un carácter nulo.")
        return ruta

    @staticmethod
    def cargar_archivo(ruta):
        # Cargamos el AFD desde un archivo de texto y devolvemos None si hay errores.
        
        # Antes de leer, comprobamos que la ruta apunte a un archivo .txt.
        # Se acepta .txt en cualquier combinación de mayúsculas/minúsculas.
        ruta_normalizada = CargadorAFD.normalizar_ruta(ruta)
        _, extension = os.path.splitext(ruta_normalizada)
        if extension.lower() != ".txt":
            print("Error: el archivo debe tener extensión .txt")
            return None
        try:
            with open(ruta_normalizada, "r", encoding="utf-8-sig") as archivo:
                lineas = archivo.readlines()
        except (OSError, UnicodeError, ValueError) as error:
            print("Error: No fue posible abrir el archivo:", error)
            return None
        
        # Quitamos los saltos de línea y conservamos los vacíos para reportarlos con precisión.
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
        
        # Las primeras cinco líneas deben tener la forma CLAVE=valor.
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
        
        # Con los encabezados válidos, asignamos los componentes del AFD.
        afd.nombre = valores_encabezado["NOMBRE"]
        
        estados_texto = valores_encabezado["ESTADOS"]
        alfabeto_texto = valores_encabezado["ALFABETO"]
        afd.estado_inicial = valores_encabezado["INICIAL"]
        finales_texto = valores_encabezado["FINALES"]
        
        # Convertir strings a sets, validando duplicados
        estados, error_estados = CargadorAFD.convertir_lista_archivo(
            estados_texto, "ESTADOS", permitir_vacio=False
        )
        alfabeto, error_alfabeto = CargadorAFD.convertir_lista_archivo(
            alfabeto_texto, "ALFABETO", permitir_vacio=False
        )
        finales, error_finales = CargadorAFD.convertir_lista_archivo(
            finales_texto, "FINALES", permitir_vacio=True
        )

        # Aplicamos al alfabeto del archivo las mismas reglas de la entrada manual.
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

        # El estado inicial debe pertenecer a Q
        if afd.estado_inicial not in afd.estados:
            errores.append("El estado inicial no pertenece a Q.")

        # Todos los estados finales deben pertenecer a Q
        if not afd.estados_finales.issubset(afd.estados):
            errores.append("Existen estados finales que no pertenecen a Q.")

        if errores:
            print("\nErrores en los datos:")
            for error in errores:
                print("-", error)
            return None
        
        # Después de TRANSICIONES: leemos cada línea como origen,símbolo,destino.
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
            
            # Validamos que el origen, el símbolo y el destino ya estén declarados.
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

            # Conservamos las repeticiones para que el validador compare sus destinos.
            afd.agregar_transicion(origen, simbolo, destino)

        # Si hay errores de sintaxis o referencias, la definición es inválida.
        # En otro caso distinguimos duplicaciones idénticas y no determinismo.
        clasificacion = ValidadorAFD.clasificar(afd)
        _, errores_estructura = ValidadorAFD.validar(afd)
        if errores or clasificacion in ("AFD INVÁLIDO", "DEFINICIÓN NO DETERMINISTA"):
            print("\nClasificación:", "AFD INVÁLIDO" if errores else clasificacion)
            for error in errores + errores_estructura:
                print("-", error)
            return None
        
        print("Clasificación:", clasificacion)
        return afd

    @staticmethod
    def convertir_lista_archivo(texto, nombre_campo, permitir_vacio):
        # Convertimos una lista separada por comas en un conjunto y devolvemos cualquier error.
        # Primero resolvemos el caso de un campo vacío.
        if texto == "":
            if permitir_vacio:
                # Si se permite vacío (e.g., FINALES), retornar set vacío
                return set(), None
            # Si no se permite (e.g., ESTADOS), retornar error
            return None, "Error: El campo " + nombre_campo + " no puede estar vacío."
        
        # Separamos y limpiamos todos los elementos del campo.
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

        # Los estados deben poder escribirse sin ambigüedad en las transiciones.
        if nombre_campo in ("ESTADOS", "FINALES"):
            for elemento in elementos:
                error = ValidadorAFD.validar_nombre_estado(elemento)
                if error:
                    return None, nombre_campo + ": " + repr(elemento) + ": " + error
        
        # Rechazamos los valores repetidos antes de construir el conjunto.
        if len(elementos) != len(set(elementos)):
            return None, (
                "Error: El campo " + nombre_campo + " contiene elementos duplicados."
            )
        
        return set(elementos), None
