"""
Creacion manual y carga del archivo de AFND
"""
import re
from AFND import AFND
from CargadorAFD import CargadorAFD
from ValidadorAFND import ValidadorAFND

class CargadorAFND:
    #Construye AFND cuyos destinos se almacenan como conjuntos #
    _PATRON_ENCABEZADO = re.compile(
        r"^(?P<clave>NOMBRE|TIPO|ESTADOS|ALFABETO|INICIAL|FINALES)=(?P<valor>.*)$"
    )
    _PATRON_TRANSICION = re.compile(
        r"^(?P<origen>[^,\s]+),(?P<simbolo>[^,\s]+),(?P<destinos>[^,\s]+)$"
    )
    _VACIO = {"∅", "{}"}

    @staticmethod
    def crear_manual():
        #Solicita los componentes y todos los conjuntos destino del AFND#
        print ("\n=====CREACION MANUAL DEL AFND====")
        afnd=AFND()

        while afnd.nombre == "":
            afnd.nombre= input("Nombre del automata: ").strip()
            if afnd.nombre=="":
                print ("El nombre no puede estar vacio.")

        afnd.estados=CargadorAFD.pedir_conjunto(
            "Estados separados por coma (ej. q0, q1, q2): "
        )

        while True:
            alfabeto = CargadorAFD.pedir_conjunto(
                "Simbolos del alfabeto separados por coma (ej. a,b): "
            )
            error= ValidadorAFND.validar_alfabeto(alfabeto)
            if error is None:
                afnd.alfabeto=alfabeto
                break
            print(error)

        while True:
            inicial= input("Estado inicial: ").strip()
            if inicial in afnd.estados:
                afnd.estado_inicial=inicial
                break
            print("El estado inicial debe pertenecer a Q.")

        while True:
            finales=CargadorAFD.pedir_conjunto(
                "Estados finales (Enter si no hay): ", permitir_vacio=True
            )
            if finales.issubset(afnd.estados):
                afnd.estados_finales=finales
                break
            print ("Todos los estados finales deben pertenecer a Q. ")

        print ("\nUse | entre multiples destinos o ∅ cuando no exista ninguno.")
        for estado in sorted(afnd.estados):
            for simbolo in sorted (afnd.alfabeto):
                while True:
                    texto =input(
                        "δ(" + estado + ", " + simbolo + ") = "
                    ).strip()
                    destinos, error= CargadorAFND.convertir_destinos(texto)
                    if error is not None:
                        print(error)
                    elif destinos.issubset(afnd.estados):
                        afnd.agregar_transicion(estado,simbolo, destinos)
                        break
                    else:
                        print("Todos los destinos deben pertenecer a Q.")
        return afnd

    @staticmethod
    def cargar_archivo(ruta):
        """Carga un AFND y muestra los errores encontrados."""

        # Leemos el archivo y quitamos espacios en los extremos
        try:
            with open(ruta, "r", encoding="utf-8-sig") as archivo:
                lineas = [linea.strip() for linea in archivo]
        except (OSError, UnicodeError) as error:
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
        return set(partes), None
