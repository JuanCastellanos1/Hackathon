# Sustentación: respuestas preparadas

Las cifras entre corchetes se llenan con los resultados reales del cuaderno.

## Preguntas específicas del reto avanzado

**¿Cómo comprobaron que el boletín no inventa datos?**
Todas las cifras salen de un solo diccionario construido desde el modelo y los CSV. La plantilla solo las inserta. Un verificador extrae todos los números del texto final y rechaza el boletín si alguno no está en ese diccionario. Lo mostramos en vivo: agregamos una cifra falsa y el verificador la detecta. Además hay una prueba automática en `tests/test_boletin.py`.

**¿Qué cambiaría si tuvieran lluvia diaria en lugar de mensual?**
Usaríamos máximos de 1, 3 y 7 días y lluvia antecedente con decaimiento, que son las variables de los umbrales físicos de deslizamiento. La alerta podría ser semanal. Hoy un aguacero de 3 horas se diluye en el total del mes.

## Preguntas obligatorias

**Explicar una porción del código.** Las más probables:
- **Rezagos:** `groupby("codigo_dane").shift(k)` sobre datos ordenados. Sin el `groupby`, la lluvia de un municipio se filtraría al siguiente.
- **Pliegues:** el entrenamiento usa años estrictamente menores que el de validación, y nunca se mezclan meses de años distintos.
- **Verificador:** busca números con una expresión regular, los normaliza (coma decimal, punto de miles, %) y calcula la diferencia de conjuntos con las cifras permitidas.

**¿Qué decidieron no construir?**
Un tablero web, un pronóstico de lluvia, un modelo espacial con vecinos y el ajuste fino de hiperparámetros. Para el consejo, el mapa en HTML y el boletín resuelven la necesidad; lo demás suma riesgo de fallar sin cambiar la decisión.

**¿Qué harían con dos horas más?**
1. Agregar el riesgo de los municipios vecinos.
2. Calibrar la probabilidad (isotónica), porque el boletín la publica como porcentaje.
3. Construir una curva de costo con el consejo: cuánto cuesta una falsa alarma frente a un evento no anticipado, para fijar el umbral con su criterio y no solo con el nuestro.

## Preguntas que probablemente harán

**¿Usaron `lluvia_mm`?**
No. Es la lluvia del mismo mes y no se conoce el día 1. Medimos el efecto: con `lluvia_mm` la PR-AUC sube a [X], que es una mejora falsa. En producción se reemplazaría por un pronóstico.

**¿Por qué ese umbral?**
Lo fijamos en 2024 para detectar al menos el 70 % de los meses con movimiento en masa y lo congelamos antes de mirar 2025. Bajarlo detecta más eventos y trae más falsas alarmas; demasiadas falsas alarmas hacen que el consejo deje de creer en el sistema. Mostramos la curva de precisión contra sensibilidad.

**¿Qué es un falso negativo aquí?**
[Municipio] en [mes] de 2025: el modelo lo dejó en verde o amarillo y hubo un movimiento en masa con [n] personas afectadas. Así se ve el costo concreto.

**¿Por qué no exactitud?**
Con 8 % de positivos, un modelo que nunca alerta acierta el 92 % de las veces y es inútil.

**¿Qué municipio podría estar en verde por reportar poco?**
Los que tienen altitud y lluvia altas pero pocos reportes históricos. Los listamos aparte como "posible subregistro". El modelo no puede distinguir entre "no pasa" y "no se reporta".

**¿Por qué sale [municipio] en alerta?**
Se muestra su cascada SHAP: [lluvia de dos meses = X mm], [movimientos en masa en 12 meses = Y] y [mes de temporada de lluvias].
