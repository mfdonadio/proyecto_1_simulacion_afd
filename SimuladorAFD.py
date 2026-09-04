class SimuladorAFD:
    """
    Simula la ejecución del AFD sobre cadenas de entrada.
    Lee la cadena símbolo por símbolo y sigue las transiciones.
    Genera una traza completa del procesamiento (opcional).
    """
    
    @staticmethod
    def evaluar(afd, cadena, mostrar_traza=True):
        """
        Procesa una cadena en el AFD y determina si es aceptada.
        
        Parámetros:
            afd: El autómata a simular (debe estar validado)
            cadena: String a evaluar
            mostrar_traza: Si True, muestra paso a paso la ejecución
        
        Retorna:
            Tupla (aceptada, resultado)
            - aceptada: bool indicando si la cadena fue aceptada
            - resultado: String descriptivo del resultado
        """
        # ========== VALIDACIÓN PREVIA ==========
        # El AFD debe haber pasado validación antes de usarlo
        if not afd.es_valido:
            return False, "El AFD debe validarse antes de evaluar cadenas."
        
        # ========== VALIDAR SÍMBOLOS DE LA CADENA ==========
        # Todos los símbolos de la cadena deben estar en el alfabeto
        for simbolo in cadena:
            if simbolo not in afd.alfabeto:
                return False, (
                    "La cadena contiene el símbolo '"
                    + simbolo
                    + "' que no pertenece al alfabeto Σ."
                )
        
        # ========== INICIALIZAR SIMULACIÓN ==========
        # Comenzamos en el estado inicial q0
        estado_actual = afd.estado_inicial
        
        # Mostrar inicio si se pide traza
        if mostrar_traza:
            print("\n--- TRAZA DE EJECUCION ---")
            print("Estado inicial: ", estado_actual)
        
        # ========== PROCESAR CADENA SÍMBOLO POR SÍMBOLO ==========
        # Para cada símbolo, seguimos la transición correspondiente
        for simbolo in cadena:
            # Buscamos el siguiente estado: δ(estado_actual, símbolo)
            siguiente_estado = afd.transiciones[(estado_actual, simbolo)]
            
            # Mostramos la transición si se pide traza
            if mostrar_traza:
                print(
                    estado_actual
                    + " ---"
                    + simbolo
                    + "--> "
                    + siguiente_estado
                )
            
            # Avanzamos al siguiente estado
            estado_actual = siguiente_estado
        
        # ========== VERIFICAR ACEPTACIÓN ==========
        # La cadena se ACEPTA si terminamos en un estado final (F)
        # La cadena se RECHAZA si terminamos en un estado no final
        aceptada = estado_actual in afd.estados_finales
        resultado = "Aceptada" if aceptada else "Rechazada"
        
        # Mostrar resultado si se pide traza
        if mostrar_traza:
            print("Estado final: ", estado_actual)
            print("Resultado: " + resultado)
        
        # ========== REGISTRAR EN HISTORIAL ==========
        # Guardamos la evaluación para consultas posteriores
        afd.historial.append(
            {
                "cadena": cadena,
                "estado_final": estado_actual,
                "resultado": resultado,
            }
        )
        
        return aceptada, resultado