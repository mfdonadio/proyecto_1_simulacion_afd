"""
AutomataPila.py — Representación del modelo de un Autómata de Pila (AP).

Soporta tanto APD (Autómata de Pila Determinista) como APND (No Determinista).
La diferencia reside en el campo `tipo` y se verifica en ValidadorAP.py.

Este módulo SOLO contiene el modelo de datos:
  - CargadorAP.py  se encarga de leer archivos y captura manual.
  - ValidadorAP.py verifica séptupla, tipos y determinismo.
  - SimuladorAP.py ejecuta la exploración BFS sobre el modelo validado.

Convención de pila (D05 / DECISIONES.md):
  La pila se representa como una tupla de tokens de Γ.
  El TOPE es siempre el elemento en el ÍNDICE 0.
  Sustitución: reemplazo + pila[1:]
    - Ejemplo: pila = ('A', 'Z0'), reemplazo = ('B', 'C')
               → nueva pila = ('B', 'C', 'Z0')
  El uso de tupla (inmutable) garantiza que cada rama de exploración
  mantenga su propia copia de la pila sin compartir referencias mutables.
"""

# Constante reservada para representar la cadena vacía como símbolo de entrada
# o como reemplazo de pila.
#   - Como entrada  → la transición NO consume un símbolo de la cadena.
#   - Como reemplazo → se desapila el tope sin insertar nada.
# EPS está PROHIBIDO en Σ (alfabeto de entrada) y en Γ (alfabeto de pila).
EPS = "EPS"


class AutomataPila:
    """
    Representa la séptupla M = (Q, Σ, Γ, δ, q0, Z0, F) de un Autómata de Pila.

    Atributos
    ---------
    nombre            : str          Identificador del autómata.
    tipo              : str          "APD" o "APND".
    estados           : set[str]     Q — conjunto de estados.
    alfabeto          : set[str]     Σ — puede ser vacío (autómata solo-EPS).
    alfabeto_pila     : set[str]     Γ — al menos Z0; no puede incluir EPS.
    estado_inicial    : str          q0.
    simbolo_inicial_pila : str       Z0.
    estados_finales   : set[str]     F — puede ser vacío.
    transiciones      : dict         δ (ver estructura abajo).
    es_valido         : bool         True solo después de validación exitosa.
    historial         : list         Resultados de evaluaciones registrados.

    Estructura de `transiciones`
    ----------------------------
    clave : tuple(str, str, str)     (estado_origen, simbolo_entrada, tope_pila)
      - simbolo_entrada puede ser EPS (constante "EPS").
      - tope_pila es un token de Γ; NUNCA puede ser EPS.
    valor : list[tuple(str, tuple[str,...])]
      - Cada elemento es (estado_destino, reemplazo_pila).
      - reemplazo_pila es una tupla de tokens de Γ, o () para representar EPS
        (desapilar sin insertar nada).
      - Se usa lista para preservar el orden de declaración, relevante para
        trazas reproducibles.
    """

    def __init__(self, nombre="", tipo="APND"):
        """
        Inicializa un Autómata de Pila vacío.

        Parámetros
        ----------
        nombre : str   Identificador del autómata (puede cambiarse después).
        tipo   : str   "APD" o "APND"; el validador lo comprueba formalmente.
        """
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

        # δ: diccionario de transiciones; vacío hasta que se carguen transiciones.
        # Ver docstring de clase para la estructura completa.
        self.transiciones = {}

        # Falso hasta que ValidadorAP.validar(ap) lo establezca en True.
        # Cualquier modificación posterior al modelo lo vuelve a False,
        # porque la validación anterior ya no aplica a la nueva estructura.
        self.es_valido = False

        # Lista de resúmenes de evaluaciones.
        # Cada elemento es el objeto/dict que produce SimuladorAP.
        self.historial = []

    # ------------------------------------------------------------------
    # Manipulación de transiciones
    # ------------------------------------------------------------------

    def agregar_alternativa(self, origen, entrada, tope, destino, reemplazo):
        """
        Añade una alternativa a la función de transición δ del AP.

        Por qué el reemplazo es una tupla
        ----------------------------------
        Las tuplas son inmutables, lo que permite:
          1. Usarlas directamente como parte de claves de diccionario (e.g., en
             conjuntos de configuraciones visitadas del simulador).
          2. Garantizar que copias de la pila en distintas ramas no compartan
             referencias; cada rama trabaja con su propia tupla independiente.

        Parámetros
        ----------
        origen    : str             Estado origen (debe pertenecer a Q).
        entrada   : str             Símbolo de Σ o la constante EPS.
        tope      : str             Token de Γ en la cima de la pila (nunca EPS).
        destino   : str             Estado destino (debe pertenecer a Q).
        reemplazo : tuple[str, ...] Tokens de Γ a colocar en la pila, o () para EPS.

        Retorna
        -------
        True  — si la alternativa se añadió exitosamente.
        False — si la alternativa ya existía de forma idéntica (duplicado exacto).
                Un duplicado idéntico no es no-determinismo; es un error de formato.

        Notas
        -----
        Invalida `es_valido` porque la estructura del autómata cambió y la
        validación anterior ya no garantiza corrección de la nueva definición.
        """
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

    def obtener_alternativas(self, estado, entrada, tope):
        """
        Retorna todas las alternativas disponibles para la clave (estado, entrada, tope).

        Parámetros
        ----------
        estado  : str  Estado origen.
        entrada : str  Símbolo de entrada o EPS.
        tope    : str  Símbolo en la cima de la pila.

        Retorna
        -------
        list[tuple(str, tuple[str,...])]  Lista de (destino, reemplazo).
            Lista vacía si no existe ninguna transición para esa clave.
            Nunca lanza excepción por clave ausente.
        """
        return self.transiciones.get((estado, entrada, tope), [])

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------

    def agregar_evaluacion_historial(self, resultado):
        """
        Registra el resumen de una evaluación en el historial del autómata.

        El historial asocia resultados a su autómata: no se mezclan registros
        de autómatas distintos dentro de la misma sesión (R09).

        Parámetros
        ----------
        resultado : dict o dataclass  Objeto de resumen producido por SimuladorAP.
            Este método no valida su estructura; eso es responsabilidad del simulador.
        """
        self.historial.append(resultado)

    # ------------------------------------------------------------------
    # Visualización
    # ------------------------------------------------------------------

    def mostrar_definicion_formal(self):
        """
        Imprime la definición formal completa del AP en la consola.

        Muestra nombre, tipo y cada componente de la séptupla
        M = (Q, Σ, Γ, δ, q0, Z0, F), incluyendo la tabla de transiciones.
        """
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

    def mostrar_tabla_transicion(self):
        """
        Imprime δ en formato tabular.

        Filas  : pares (q, X) con q ∈ Q, X ∈ Γ, en orden estable (ordenados).
        Columnas: una por símbolo de Σ (ordenado), más columna EPS si existe
                  al menos una transición con entrada = EPS.
        Celdas : todas las alternativas (destino, reemplazo) o '-' si no hay.

        Convenciones de visualización
        -----------------------------
        - Reemplazo ()      → se muestra como "EPS" (desapila sin insertar).
        - Reemplazo ('A','Z0') → "A;Z0" (tokens separados por ';').
        - El tope es el símbolo más a la izquierda de la pila (índice 0).
        - Anchos calculados con datos reales; no hay constante fija.
        - Con Σ vacío, se muestra únicamente la columna EPS.
        """
        if not self.estados or not self.alfabeto_pila:
            print("  (Sin estados o alfabeto de pila definidos; tabla no disponible.)")
            return

        estados_ord = sorted(self.estados)
        pila_ord = sorted(self.alfabeto_pila)
        sigma_ord = sorted(self.alfabeto)

        # Determinar si hay alguna transición EPS para incluir esa columna.
        hay_eps = any(clave[1] == EPS for clave in self.transiciones)

        # Construir la lista de columnas: símbolos de Σ + EPS si corresponde.
        columnas = sigma_ord + ([EPS] if hay_eps else [])

        if not columnas:
            print("  (Sin símbolos de entrada ni transiciones EPS; tabla no disponible.)")
            return

        # -----------------------------------------------------------------
        # Función auxiliar: convertir un reemplazo (tupla) a texto legible.
        # -----------------------------------------------------------------
        def texto_reemplazo(reemplazo):
            """() → 'EPS'; ('A', 'Z0') → 'A;Z0'."""
            if not reemplazo:
                return EPS
            return ";".join(reemplazo)

        def texto_celda(q, X):
            """Retorna el contenido de la celda (q, X) como texto."""
            alts = self.obtener_alternativas(q, X, tope_actual)
            if not alts:
                return "-"
            partes = []
            for dest, remp in alts:
                partes.append("({},{})".format(dest, texto_reemplazo(remp)))
            return " ".join(partes)

        # -----------------------------------------------------------------
        # Calcular anchos de columna con los datos reales.
        # -----------------------------------------------------------------
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
                    tope_actual = X  # variable usada por texto_celda
                    celda = texto_celda(q, col)
                    if len(celda) > max_celda:
                        max_celda = len(celda)
            anchos_col[col] = max_celda + 2

        # -----------------------------------------------------------------
        # Imprimir la tabla.
        # -----------------------------------------------------------------
        print("\n--- TABLA DE TRANSICIONES DEL AP (tope en índice 0 de la pila) ---")

        # Encabezado
        linea_enc = encabezado_fila.ljust(ancho_fila)
        for col in columnas:
            linea_enc += col.ljust(anchos_col[col])
        print(linea_enc)
        print("-" * len(linea_enc))

        # Filas
        for q in estados_ord:
            for X in pila_ord:
                tope_actual = X  # variable para texto_celda
                etiqueta = "({}, {})".format(q, X)
                fila = etiqueta.ljust(ancho_fila)
                for col in columnas:
                    celda = texto_celda(q, col)
                    fila += celda.ljust(anchos_col[col])
                print(fila)
