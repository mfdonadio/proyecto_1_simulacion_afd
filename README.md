# Simulador de AFD y conversión de AFND

Programa de consola en Python 3, sin dependencias externas. Conserva las clases y las funcionalidades de ambas fases.

## Ejecución

Desde esta carpeta:

```powershell
py -3 main.py
py -3 -m unittest -v test_regresiones
```

Si tu instalación utiliza `python` en vez de `py -3`, sustituí ese comando. Las rutas relativas se resuelven desde la carpeta donde iniciás Python, que el programa muestra al arrancar. Se aceptan rutas absolutas y un par de comillas exteriores coincidentes; no se buscan archivos en otras carpetas.

## Uso y cambios comprobados

- Opción 5: definición formal y tabla del autómata original.
- Opción 6: validación del original y del AFD equivalente, con reportes identificados.
- Opción 7: reutiliza una conversión válida y conserva su historial y equivalencias. El menú no permite editar el AFND, pero también se compara una copia de sus componentes para descartar una conversión si cambian directamente.
- Opción 8: tabla de equivalencias de macroestados.
- Opción 9: definición formal completa y tabla del AFD equivalente.
- Opciones 10–13: evaluación individual, lotes, historial y análisis. Si se cargó un AFND, se indica que se utiliza su AFD equivalente.
- Opciones 1–4 y 14: permiten cambiar de autómata sin reiniciar. Una carga nueva correcta inicia datos e historial separados; una carga fallida o cancelada conserva la sesión anterior. La nueva sesión AFND se confirma después de convertirla correctamente.
- Ctrl+C cancela la operación y vuelve al menú. El fin de entrada termina sin traceback. La opción 15 sale normalmente.

La conversión conserva Q, alfabeto, transiciones, inicial y finales del AFND original. Cada macroestado representa un subconjunto alcanzable; el conjunto vacío se incluye si es alcanzable y es final cualquier macroestado que contenga al menos un final del original.

## Clasificación y nombres

Prioridad de clasificación: **AFD INVÁLIDO**, **DEFINICIÓN NO DETERMINISTA**, **AFD INCOMPLETO**, **AFD VÁLIDO** (completo).

Una pareja repetida con el mismo destino se rechaza como duplicación de formato: no introduce no determinismo. Dos destinos distintos para la misma pareja constituyen no determinismo si todas las referencias son válidas. Los tipos, estructuras o referencias inválidos tienen prioridad. Solo se ofrece estado trampa si faltan transiciones y no hay otros errores; su nombre no colisiona con estados existentes. Las definiciones no deterministas no se simulan como AFD.

Los nombres de estados pueden ser, por ejemplo, `inicio`, `aceptación-2` o `S_3`. No pueden estar vacíos ni contener espacios o caracteres de control. Se reservan la coma y `|` como separadores, y los nombres exactos `∅` y `{}` como ausencia de destinos. La misma regla se usa en consola, carga y validación. Se recortan espacios exteriores al leer elementos de listas.

El formato de AFD está en `prueba_afd_ab.txt`; el de AFND en `prueba_afnd_ab.txt`. El AFND incluye `TIPO=AFND`, admite destinos separados por `|` y los almacena como conjuntos. `∅` y `{}` representan conjuntos vacíos. `FINALES=` y una sección `TRANSICIONES:` sin líneas posteriores son válidos para un AFND. Los símbolos del alfabeto son caracteres individuales, sin espacios, controles ni epsilon.

Los archivos se leen con `utf-8-sig`, que admite BOM. En un archivo de cadenas se conserva cada espacio y cada línea vacía (epsilon); se retiran únicamente los saltos de línea. Los lotes se procesan línea por línea. Si la lectura falla después de evaluar algunas cadenas, esos resultados permanecen en el historial y se informa la interrupción.

## Verificación realizada

Antes de modificar el programa pasaron las **16 pruebas originales**. Después pasaron **31 pruebas**, sin eliminar pruebas ni cambiar sus expectativas anteriores. La comparación independiente entre AFND y AFD cubre 189 casos: todas las cadenas sobre `a,b` de longitud 0 a 5, con tres conjuntos de finales.

| Requisitos comprobados | Evidencia |
| --- | --- |
| Crear y cargar AFD y AFND; validar ambos | Creación manual simulada, archivos de ejemplo y BOM, tipos y referencias inválidas |
| Tabla AFND y conversión automática tras cargarlo | Recorrido del menú y comprobación de la conversión |
| Construcción de subconjuntos, vacío alcanzable y finales mixtos | Tres macroestados, ciclos del vacío y comparación independiente |
| Consultar original, equivalente y equivalencias | Opciones 5, 6, 8 y 9 después de convertir |
| Evaluación individual y por lotes, epsilon, rechazo y símbolos externos | Simulador, traza, historial y conservación de espacios y líneas vacías |
| Alcanzables, inaccesibles, finales alcanzables y lenguaje vacío | Conjuntos esperados y final inaccesible |
| Reconvertir sin perder historial; cambiar de autómata sin reiniciar | Identidad del AFD reutilizado, sesiones separadas y cargas fallidas |
| Compatibilidad de Fase 1 | Las 16 regresiones originales siguen pasando, incluyendo estado trampa |
| Protección de entrada y archivos | Consultas sin autómata, EOF, Ctrl+C, ruta nula, inexistente, directorio, sintaxis y codificación |
| Correcciones anteriores | Todos los destinos, AFND sin transiciones, tipos, validación obsoleta y propagación del error de conversión |

Las pruebas están en `test_regresiones.py` y utilizan solo la biblioteca estándar. Las interacciones de consola se automatizan con entradas controladas.

## Documentación y pendientes

Se revisaron `INSTRUCCIONES PROYECTO1.md` y el contenido textual de `Documento_Tecnico_AFD_Proyecto1-Gerber-y-Marco.pdf`. No se encontró una rúbrica separada ni el enunciado de la Fase 2 en la carpeta o en el listado del ZIP disponible. Para esa fase se verificaron los requisitos explícitos de la solicitud; no se certifica cumplimiento de documentos ausentes.

La memoria técnica PDF necesita actualizar sus acciones y numeración del menú, arquitectura para AFND, reglas de nombres, distinción de repeticiones, rutas, preservación de conversiones y complejidad. Su diagrama también debe revisarse para el menú actual. No se editó el PDF ni se verificó su presentación visual. El ZIP existente tampoco se regeneró.

No se agregaron límites arbitrarios: la construcción de subconjuntos puede producir hasta 2^n macroestados y consumir mucha memoria y tiempo. El historial crece durante la sesión y los archivos de definición todavía se almacenan completos al leerlos. El procesamiento de lotes evita guardar todas las líneas a la vez, pero conserva las evaluaciones terminadas. No se hicieron pruebas de agotamiento de memoria o cargas masivas.
