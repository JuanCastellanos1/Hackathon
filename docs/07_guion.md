# Guion de sustentación (5 minutos)

**Qué tener abierto antes de empezar:**
1. `out/tablero.html` en el navegador, en **abril de 2025**.
2. `alerta.ipynb` en VS Code, ya ejecutado.
3. `src/satmm/boletin.py` en una pestaña aparte.

## Minuto a minuto

| Tiempo | Qué decir | Qué mostrar |
|---|---|---|
| 0:00–0:30 | **El problema.** El consejo departamental necesita saber, el primer día de cada mes, qué municipios reforzar ante deslizamientos. Construimos un sistema que lo responde con datos y explica por qué. | Tablero, abril de 2025 |
| 0:30–1:15 | **Cómo lee el mapa.** Abril es temporada de lluvias: casi todo Santander queda en vigilancia (amarillo), y los **10 rojos** son los que necesitan acción, porque es lo que el consejo puede atender. La columna "¿Ocurrió?" es el dato real de 2025: en abril, los 23 municipios con deslizamiento quedaron en rojo o amarillo. | Clic en San Andrés; mostrar sus 3 razones |
| 1:15–2:00 | **Por qué sale en alerta.** San Andrés: 529,6 mm de lluvia en dos meses, cabecera a 1.650 m y 2 deslizamientos en el último año. Lo que más pesa en el modelo: temporada, lluvia reciente y relieve. Comprobamos que el riesgo **sube** con la lluvia y la altitud, como debe ser. | Pestaña Boletín; luego la gráfica de factores en el cuaderno |
| 2:00–2:45 | **El boletín no inventa cifras.** Todas salen de un solo diccionario, y un verificador revisa cada número del texto. Generamos 98 boletines y ninguno tuvo cifras sin fuente. Prueba en vivo: le agregamos "350 viviendas" y el verificador lo rechaza. | Celda "Prueba del verificador" del cuaderno |
| 2:45–3:45 | **Cómo validamos.** Entrenamos con años pasados y probamos con el año siguiente, sin mezclar años. 2025 lo tocamos **una sola vez**, al final. **No usamos la lluvia del mismo mes,** porque no se conoce el día 1: si la usáramos, el modelo parecería mejor (0,190 → 0,243), pero sería falso. Resultado en 2025: detectamos el 84 % de los meses con deslizamiento; repetir lo del año anterior detecta el 11 %. | Pestaña Desempeño 2025 |
| 3:45–4:30 | **Qué no puede anticipar.** 16 de 99 deslizamientos se escaparon, la mayoría en meses secos, y la mitad en municipios sin historial reciente. Lo que no se reporta, el sistema no lo ve. La lluvia mensual de la cabecera no capta aguaceros de pocas horas. | Pestaña Límites |
| 4:30–5:00 | **Cierre.** Un prototipo que corre sin servidores, se explica municipio por municipio y no inventa cifras. Con lluvia diaria, la alerta podría ser semanal. | Volver al mapa |

## Código que probablemente señale el jurado

| Tema | Dónde | Qué explicar |
|---|---|---|
| Rezagos sin fuga | [variables.py:38](../src/satmm/variables.py) y [:40](../src/satmm/variables.py) | `groupby("codigo_dane").shift(k)`: sin el `groupby`, la lluvia de un municipio se filtraría al siguiente. `shift(1)` antes de `rolling(12)` deja fuera el mes actual. |
| Candado contra la fuga | [variables.py:15](../src/satmm/variables.py) | Si `lluvia_mm` entra a las variables, el programa se detiene. |
| Climatología solo con el pasado | [variables.py:23](../src/satmm/variables.py) | `shift(1).expanding().mean()` por municipio y mes: solo usa años anteriores al de la fila. |
| Validación por años | [validacion.py:23](../src/satmm/validacion.py) y [:31](../src/satmm/validacion.py) | Ventana expansiva; el `assert` impide entrenar con un año igual o posterior al de prueba. |
| Semáforo | [modelo.py:43](../src/satmm/modelo.py) | Amarillo: umbral fijo de sensibilidad. Rojo: puesto ≤ 10 dentro de su mes **y** sobre el amarillo. |
| Por qué XGBoost sin peso | [modelo.py:13](../src/satmm/modelo.py) | Sin peso de clase, la probabilidad sale calibrada (Brier 0,082) y se puede publicar. El desbalance se maneja con el umbral. |
| Verificador del boletín | [boletin.py:96](../src/satmm/boletin.py) y [:100](../src/satmm/boletin.py) | Expresión regular para números colombianos (1.234,5); cada número debe estar en el diccionario de cifras con una tolerancia de 0,05. |
| Razones legibles | [explicacion.py:48](../src/satmm/explicacion.py) | Descarta razones que se leerían al revés, como "lluvia 0,7 veces su promedio" como motivo de alerta. |

## Preguntas obligatorias, en una frase

- **¿Qué decidieron no construir?** Un tablero con servidor, un pronóstico de lluvia, un modelo espacial y el ajuste fino de hiperparámetros: sumaban riesgo sin cambiar la decisión del consejo.
- **¿Qué harían con dos horas más?** Agregar el riesgo de los municipios vecinos, afinar el umbral por temporada, y construir con el consejo una curva de costo de falsa alarma frente a evento perdido.

Respuestas largas en [05_sustentacion.md](05_sustentacion.md).

## Si algo falla en vivo

| Falla | Plan B |
|---|---|
| El mapa no carga el fondo | Los municipios se siguen viendo; el fondo es solo contexto |
| El navegador no abre el tablero | Mostrar el cuaderno ya ejecutado: tiene todas las tablas y gráficas |
| El portátil falla | Copia del proyecto en USB; también está en GitHub |
