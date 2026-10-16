# Motor de Validación y Conversión de Autómatas (AFD/AFND/AP)

Programa de consola en Python 3, sin dependencias externas.
Elaborado por Gerber Perez y Marco Donadio para el curso de Lenguajes Formales y Autómatas (Facultad de Ingeniería, URL).

Soporta tres fases del proyecto:
- **Fase 1**: AFD — Autómata Finito Determinista M=(Q,Σ,δ,q0,F)
- **Fase 2**: AFND — Autómata Finito No Determinista y conversión a AFD equivalente
- **Fase 3**: AP — Autómata de Pila (APD/APND) M=(Q,Σ,Γ,δ,q0,Z0,F)

## Ejecución

```
python main.py
```

Python 3.8 o superior. Sin dependencias externas. En Windows con caracteres especiales:

```
python -X utf8 main.py
```

## Opciones del menú

| Opción | Descripción |
|--------|-------------|
| 1-4    | Crear/cargar AFD o AFND |
| 5      | Mostrar definición formal y tabla del autómata activo |
| 6      | Validar autómata activo |
| 7      | Convertir AFND a AFD equivalente |
| 8      | Mostrar tabla de equivalencias de macroestados |
| 9      | Mostrar definición del AFD generado |
| 10     | Evaluar una cadena |
| 11     | Evaluar un archivo de cadenas (lote) |
| 12     | Historial de evaluaciones |
| 13     | Análisis estructural |
| 14     | Cargar otro AFD/AFND |
| 15     | Salir |
| 16     | Crear APD/APND manualmente |
| 17     | Cargar APD/APND desde archivo .txt |
| 18     | Ajustar límite de exploración para AP |

## Formato de archivos AP

```
NOMBRE=APD_ANBN
TIPO=APD
ESTADOS=q0,q1,q2
ALFABETO=a,b
ALFABETO_PILA=Z0,A
INICIAL=q0
INICIAL_PILA=Z0
FINALES=q2
TRANSICIONES:
q0,a,Z0,q0,A;Z0
q0,b,A,q1,EPS
q1,EPS,Z0,q2,Z0
```

Los ejemplos están en `ejemplos/fase3/`. Ver `docs/fase3/MANUAL_USUARIO.md` para detalles.

## Ejecutar pruebas

```
python -X utf8 -m unittest tests.test_regresion_afd tests.test_regresion_afnd tests.test_automata_pila -v
```

74 pruebas automatizadas cubren fases 1, 2 y 3.