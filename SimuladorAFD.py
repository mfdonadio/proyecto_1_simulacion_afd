from ValidadorAFD import ValidadorAFD


class SimuladorAFD:
    # Simulamos una cadena en el AFD y podemos mostrar la traza de su recorrido.
    
    @staticmethod
    def evaluar(afd, cadena, mostrar_traza=True):
        # Procesamos la cadena y devolvemos tanto la aceptación como su explicación.
        # Primero comprobamos que el AFD haya pasado la validación.
        if not afd.es_valido:
            return False, "El AFD debe validarse antes de evaluar cadenas."

        # Revisamos cambios directos que no hayan invalidado la marca anterior.
        valido, errores = ValidadorAFD.validar(afd)
        if not valido:
            return False, "El AFD tiene una estructura inválida: " + "; ".join(errores)

        if not isinstance(cadena, str):
            return False, "La cadena debe ser de tipo texto."
        
        # Todos los símbolos de la cadena deben pertenecer al alfabeto.
        for simbolo in cadena:
            if simbolo not in afd.alfabeto:
                return False, (
                    "La cadena contiene el símbolo '"
                    + simbolo
                    + "' que no pertenece al alfabeto Σ."
                )
        
        # La simulación comienza en el estado inicial q0.
        estado_actual = afd.estado_inicial
        
        # Mostrar inicio si se pide traza
        if mostrar_traza:
            print("\n--- TRAZA DE EJECUCION ---")
            print("Estado inicial: ", estado_actual)
        
        # Recorremos la cadena y seguimos una transición por cada símbolo.
        for simbolo in cadena:
            # Buscamos el siguiente estado: δ(estado_actual, símbolo)
            if (estado_actual, simbolo) not in afd.transiciones:
                afd.es_valido = False
                return False, "El AFD tiene una estructura inválida: falta una transición."
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
        
        # La cadena se acepta si termina en F y se rechaza en cualquier otro estado.
        aceptada = estado_actual in afd.estados_finales
        resultado = "Aceptada" if aceptada else "Rechazada"
        
        # Mostrar resultado si se pide traza
        if mostrar_traza:
            print("Estado final: ", estado_actual)
            print("Resultado: " + resultado)
        
        # Guardamos el resultado para consultarlo después en el historial.
        afd.historial.append(
            {
                "cadena": cadena,
                "estado_final": estado_actual,
                "resultado": resultado,
            }
        )
        
        return aceptada, resultado
