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
2. Afinar el umbral por temporada: en meses secos el sistema casi no alerta, y ahí se concentran los falsos negativos.
3. Construir una curva de costo con el consejo: cuánto cuesta una falsa alarma frente a un evento no anticipado, para fijar el umbral con su criterio y no solo con el nuestro.

## Preguntas que probablemente harán

**¿Usaron `lluvia_mm`?**
No. Es la lluvia del mismo mes y no se conoce el día 1. Medimos el efecto: con `lluvia_mm` la PR-AUC de la logística sube de 0,190 a 0,243, que es una mejora falsa. En producción se reemplazaría por un pronóstico.

**¿Por qué ese umbral?**
Son dos reglas. El amarillo se fijó en 2024 para detectar al menos el 70 % de los meses con movimiento en masa, y se congeló antes de mirar 2025; en 2025 detectó el 84 %. El rojo son los 10 municipios más altos de cada mes, que es la capacidad que suponemos del consejo departamental; en rojo, 1 de cada 5 alertas acierta, el doble de la tasa base (9,5 %). Bajarlo detecta más eventos y trae más falsas alarmas; demasiadas falsas alarmas hacen que el consejo deje de creer en el sistema. Mostramos la curva de precisión contra sensibilidad.

**¿Qué es un falso negativo aquí?**
En 2025, 16 de 99 meses con movimiento en masa quedaron en verde; por ejemplo, Jesús María en enero y Pinchote en diciembre (405 mm de lluvia en dos meses). Dos patrones: 11 de los 16 ocurrieron en meses secos (enero, febrero, julio, agosto y diciembre), cuando el sistema casi no alerta, y la mitad (8) no tenía movimientos en masa en los 12 meses previos. El modelo depende de la temporada y del historial: un evento fuera de temporada en un municipio sin reportes previos es casi invisible. Ese es el costo concreto del subregistro.

**¿Por qué no exactitud?**
Con 8 % de positivos, un modelo que nunca alerta acierta el 92 % de las veces y es inútil.

**¿Qué municipio podría estar en verde por reportar poco?**
Los que tienen altitud y lluvia altas pero pocos reportes históricos. Los listamos aparte como "posible subregistro". El modelo no puede distinguir entre "no pasa" y "no se reporta".

**¿Por qué sale [municipio] en alerta?**
Se muestra su cascada SHAP: [lluvia de dos meses = X mm], [movimientos en masa en 12 meses = Y] y [mes de temporada de lluvias].
