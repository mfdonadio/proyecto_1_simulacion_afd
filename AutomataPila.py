# Este módulo guarda los datos de un APD o APND; la carga, validación y
# simulación se realizan en sus módulos correspondientes.
# La pila usa tuplas con el tope en el índice 0. Cada transición construye
# una nueva tupla, por lo que una rama no puede modificar la pila de otra.

# Usamos EPS para representar la cadena vacía. Como entrada no consume un
# símbolo; como reemplazo quita el tope sin insertar nada. Por eso EPS se
# reserva para las transiciones y no puede pertenecer a Σ ni a Γ.
EPS = "EPS"


# Representa la séptupla M = (Q, Σ, Γ, δ, q0, Z0, F) de un autómata de pila.
# Cada clave de transiciones es (origen, entrada, tope) y guarda una lista
# ordenada de alternativas (destino, reemplazo).
class AutomataPila:
    # Crea un autómata vacío que el cargador completará antes de validarlo.
    def __init__(self, nombre="", tipo="APND"):
        self.nombre = nombre
        self.tipo = tipo

        # Conjuntos vacíos; el cargador los rellena antes de validar.
        self.estados = set()
        self.alfabeto = set()          # Σ; se permite vacío para autómata solo-EPS
        self.alfabeto_pila = set()     # Γ; debe contener al menos Z0 para ser válido

        # Componentes de la séptupla
        self.estado_inicial = ""
        self.simbolo_inicial_pila = ""  # Z0
        self.estados_finales = set()

        # Cada clave de δ guardará una lista con sus alternativas de transición.
        self.transiciones = {}

        # Falso hasta que ValidadorAP.validar(ap) lo establezca en True.
        # Cualquier modificación posterior al modelo lo vuelve a False,
        # porque la validación anterior ya no aplica a la nueva estructura.
        self.es_valido = False

        # Lista de resúmenes de evaluaciones.
        # Cada elemento es el objeto/dict que produce SimuladorAP.
        self.historial = []

    # Agrega una alternativa y devuelve False si ya existía exactamente igual.
    # El reemplazo es una tupla: () representa EPS y, por tanto, desapilar.
    def agregar_alternativa(self, origen, entrada, tope, destino, reemplazo):
        clave = (origen, entrada, tope)
        alternativa = (destino, reemplazo)

        # Toda modificación del modelo invalida la validación anterior.
        # El simulador exigirá revalidar antes de operar.
        self.es_valido = False

        if clave not in self.transiciones:
            # Primera alternativa para esta clave; crear la lista.
            self.transiciones[clave] = [alternativa]
            return True

        # La clave ya existe: comprobar si la alternativa es idéntica (duplicado).
        if alternativa in self.transiciones[clave]:
            # Duplicado exacto — diagnóstico de formato, no añadir.
            return False

        # Alternativa distinta para la misma clave → no-determinismo (APND) o
        # conflicto (APD). El validador es quien decide si es aceptable según el tipo.
        self.transiciones[clave].append(alternativa)
        return True

    # Devuelve las alternativas de una clave o una lista vacía si no existe.
    def obtener_alternativas(self, estado, entrada, tope):
        return self.transiciones.get((estado, entrada, tope), [])

    # El historial pertenece al autómata para no mezclar sesiones distintas.
    def agregar_evaluacion_historial(self, resultado):
        self.historial.append(resultado)

    # Muestra los componentes de la séptupla y su tabla de transiciones.
    def mostrar_definicion_formal(self):
        print("\n--- DEFINICION FORMAL DEL AP ---")
        print("Nombre :", self.nombre)
        print("Tipo   :", self.tipo)
        print("Q      =", sorted(self.estados))
        print("Σ      =", sorted(self.alfabeto) if self.alfabeto else "∅ (solo-EPS)")
        print("Γ      =", sorted(self.alfabeto_pila))
        print("q0     =", self.estado_inicial)
        print("Z0     =", self.simbolo_inicial_pila)
        print("F      =", sorted(self.estados_finales) if self.estados_finales else "∅")
        print("δ      =")
        self.mostrar_tabla_transicion()

    # Organiza una fila por cada pareja (estado, tope) y una columna por entrada.
    # La columna EPS solo aparece cuando existe alguna transición espontánea.
    def mostrar_tabla_transicion(self):
        if not self.estados or not self.alfabeto_pila:
            print("  (Sin estados o alfabeto de pila definidos; tabla no disponible.)")
            return

        estados_ord = sorted(self.estados)
        pila_ord = sorted(self.alfabeto_pila)
        sigma_ord = sorted(self.alfabeto)

        # Incluimos la columna EPS únicamente cuando alguna transición la utiliza.
        hay_eps = any(clave[1] == EPS for clave in self.transiciones)

        # Las demás columnas corresponden a los símbolos declarados en Σ.
        columnas = sigma_ord + ([EPS] if hay_eps else [])

        if not columnas:
            print("  (Sin símbolos de entrada ni transiciones EPS; tabla no disponible.)")
            return

        # En la tabla, una tupla vacía se presenta como EPS.
        def texto_reemplazo(reemplazo):
            if not reemplazo:
                return EPS
            return ";".join(reemplazo)

        # Construimos la celda con el estado, la columna y el tope de la fila.
        def texto_celda(q, entrada, tope):
            alts = self.obtener_alternativas(q, entrada, tope)
            if not alts:
                return "-"
            partes = []
            for dest, remp in alts:
                partes.append("({},{})".format(dest, texto_reemplazo(remp)))
            return " ".join(partes)

        # Calculamos los anchos con los datos reales para conservar la alineación.
        encabezado_fila = "Estado / Tope"  # Etiqueta de la columna de filas

        # Ancho de la columna de fila: máximo entre etiqueta y los textos "(q, X)".
        textos_fila = [encabezado_fila] + [
            "({}, {})".format(q, X) for q in estados_ord for X in pila_ord
        ]
        ancho_fila = max(len(t) for t in textos_fila) + 2

        # Ancho de cada columna de símbolo: máximo entre el encabezado y las celdas.
        anchos_col = {}
        for col in columnas:
            max_celda = len(col)
            for q in estados_ord:
                for X in pila_ord:
                    celda = texto_celda(q, col, X)
                    if len(celda) > max_celda:
                        max_celda = len(celda)
            anchos_col[col] = max_celda + 2

        print("\n--- TABLA DE TRANSICIONES DEL AP (tope en índice 0 de la pila) ---")

        # Primero imprimimos el encabezado con los anchos ya calculados.
        linea_enc = encabezado_fila.ljust(ancho_fila)
        for col in columnas:
            linea_enc += col.ljust(anchos_col[col])
        print(linea_enc)
        print("-" * len(linea_enc))

        # Después imprimimos una fila por cada pareja de estado y tope.
        for q in estados_ord:
            for X in pila_ord:
                etiqueta = "({}, {})".format(q, X)
                fila = etiqueta.ljust(ancho_fila)
                for col in columnas:
                    celda = texto_celda(q, col, X)
                    fila += celda.ljust(anchos_col[col])
                print(fila)
