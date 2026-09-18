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

        afnd.estados=CargadorAFND.pedir_conjunto(
            "Estados separados por coma (ej. q0, q1, q2): "
        )

        while True:
            alfabeto= CargadorAFD.pedir_conjunto(
                "Simbolos del alfabeto separados por coma (ej. a,b): "
            )
            error= CargadorAFD._validar_alfabeto(alfabeto)
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

        print ("\n Use | entre multiples destinos o 0 cuando no exista ninguno.")
        for estado in sorted(afnd.estados):
            for simbolo in sorted (afnd.alfabeto):
                while True:
                    texto =input(
                        "δ(" + estado + ", " + simbolo + ") = "
                    ).strip
                    destinos, error= CargadorAFND._convertir_destinos(texto)
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
    #Carga un AFND y reporta erorres con su numero de linea#
    lineas= CargadorAFD._leer_lineas(ruta)
    if lineas is None:
        return None

    encabezados={}
    transiciones=[]
    errores=[]
    en_transiciones=False

    for indice, linea in enumerate(lineas,start=1):
        if linea== "TRANSICIONES:":
            if en_transiciones:
                errores.append("Línea " + str(indice) + ": sección repetida.")
                en_transiciones=True
                continue
        if linea == "":
                errores.append("Línea " + str(indice) + ": no se permiten líneas vacías.")
                continue
        if not en_transiciones:
            coincidencia= CargadorAFND._PATRON_ENCABEZADO.fullmatch(linea)
            if coincidencia is None:
                errores.append(
                        "Línea " + str(indice) + ": encabezado con formato inválido."
                )
            else: 
                clave= coincidencia.group("clave")
                if clave in encabezados:
                    errores.append("Línea " + str(indice) + ": encabezado repetido.")
                else:
                    encabezados[clave]= coincidencia.group("valor")
                    continue
                coincidencia=CargadorAFND._PATRON_TRANSICION.fullmatch(linea)
                if coincidencia is None:
                    errores.append(
                        "Línea "
                    + str(indice)
                    + ": use origen,símbolo,destino1|destino2 o ∅."
                    )
                else:
                    transiciones.append(
                         (
                        coincidencia.group("origen"),
                        coincidencia.group("simbolo"),
                        coincidencia.group("destinos"),
                        indice,
                        )
                    )
                requeridos= {"NOMBRE", "TIPO", "ESTADOS", "ALFABETO", "INICIAL", "FINALES"}
                for clave in sorted(requeridos - set(encabezados)):
                    errores.append("Falta el encabezado "+clave+".")
                if not en_transiciones:
                    errores.append("Falta la línea TRANSICIONES:.")
                if encabezados.get("TIPO", "").upper() != "AFND":
                    erorres.append("TIPO debe ser AFND.")

                if errores:
                    CargadorAFD._mostrar_errores("sintaxis", errores)
                    return None
                afnd, errores= CargadorAFND._construir_afnd(encabezados,transiciones)
                if errores:
                    CargadorAFD._mostrar_errores("datos",errores)
                    return None
            return afnd

@staticmethod
def _construir_afnd(encabezados, transiciones):
        #Convierte los textos validados en conjuntos y transiciones.#
        errores = []
        afnd = AFND(encabezados["NOMBRE"].strip())
        estados, error = CargadorAFD._convertir_lista(
            encabezados["ESTADOS"], "ESTADOS", False
        )
        if error:
            errores.append(error)
        alfabeto, error = CargadorAFD._convertir_lista(
            encabezados["ALFABETO"], "ALFABETO", False
        )
        if error:
            errores.append(error)
        finales, error = CargadorAFD._convertir_lista(
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

        error_alfabeto=CargadorAFD._validar_alfabeto(alfabeto)
        if error_alfabeto:
            errores.append(error_alfabeto)
        if afnd.estado_inicial not in estados:
            errores.append("INICIAL no pertenece al conjunto Q.")
        if not finales.issubset(estados):
            errores.append("FINALES contiene estados que no pertenecen a Q.")

        for origen, simbolo, texto_destinos, numero_linea in transiciones:
            destinos, error = CargadorAFND._convertir_destinos(texto_destinos)
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
def _convertir_destinos(texto):
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
