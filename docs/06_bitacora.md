# Bitácora de construcción

Registro de cómo nos fue en cada fase: qué hicimos, qué se complicó, qué decidimos y qué queda pendiente. Es para guiarnos nosotros, no para el jurado. Las horas son aproximadas.

**Cómo vamos:** resultado completo a las 14:52 (antes del hito de las 14:55) y modelo final probado en 2025 a las 15:00. Todo construido y verificado a las 15:12. Vamos unos 30 minutos adelantados; solo falta ensayar.

| Fase | Estado | Terminó |
|---|---|---|
| Preparación: propuesta y docs | Hecha | 14:20 |
| F0 · Entorno y carga de datos | Hecha | 14:46 |
| F1 · Variables | Hecha | 14:47 |
| F2 · Validación y modelo simple | Hecha | 14:48 |
| F3 · Primer resultado completo | Hecha | 14:52 |
| F4 · Modelo principal y umbral | Hecha | 15:00 |
| F5 · Explicación por municipio | Hecha | 15:03 |
| F6 · Mapa, boletines y tablero | Hecha | 15:07 |
| F7 · Cierre | Hecha | 15:12 |
| F8 · Ensayo | Guion listo; falta ensayar | 15:20 |

---

## Preparación: propuesta y documentación

**Qué hicimos:** leímos el enunciado del reto avanzado, armamos la propuesta y bajamos el repositorio con los datos. Organizamos todo en `data/` y `docs/`.

**Qué se complicó:** el primer push falló porque la cuenta de GitHub no tenía permiso sobre el repositorio. Lo resolvimos dando acceso.

**Lo que aprendimos de los datos:**
- Vienen muy limpios, posiblemente simulados (el "plan B" del enunciado). Hay que preguntarle a la comisión.
- Hay un GeoJSON con la forma de cada municipio, así que el mapa puede colorear municipios completos y no solo poner puntos.
- Los deslizamientos se concentran en dos temporadas: abril–mayo y octubre–noviembre.

## F0 · Entorno y carga de datos

**Qué hicimos:** creamos el entorno de Python, instalamos las librerías y escribimos la carga de datos con una tabla de problemas encontrados.

**Qué se complicó:** la instalación tardó más de 20 minutos por el internet lento (unos 200 KB/s). XGBoost intentaba bajar unos 300 MB de drivers de NVIDIA que no necesitamos; lo cambiamos por la versión solo CPU.

**Lección:** el día del reto no se puede contar con instalar nada. Todo tiene que llegar instalado.

## F1 · Variables

**Qué hicimos:** construimos las variables del modelo usando solo lo que se sabe el primer día del mes: lluvia de los dos meses anteriores, deslizamientos del último año, lo que suele pasar en ese municipio y mes, altitud y ubicación.

**Decisiones:**
- **No usamos la lluvia del mismo mes.** Es la trampa del reto: ese dato no existe al inicio del mes. Lo dejamos bloqueado en el código para que no se cuele por error.
- **El mes lo representamos con dos ciclos al año,** porque hay dos temporadas de lluvia. Con un solo ciclo el mes casi no aportaba; con dos, se volvió la variable más útil.
- **2015 solo sirve para alimentar a 2016,** porque le falta historia previa.

**Cómo lo comprobamos:** pruebas automáticas que revisan, municipio por municipio, que los datos de meses anteriores caen en el lugar correcto.

## F2 · Validación y modelo simple

**Qué hicimos:** probamos el modelo como si estuviéramos en el pasado. Entrenamos hasta 2020 y probamos en 2021; luego hasta 2021 y probamos en 2022; y así hasta 2024. **2025 no se toca** hasta el final.

**Cómo nos fue:**
- El modelo simple (regresión logística) le gana a las dos referencias en todos los años, no solo en promedio.
- Detecta el 71 % de los meses con deslizamiento. La referencia del reto ("repetir lo del año pasado") solo detecta el 18 %.
- Medimos la trampa: si usáramos la lluvia del mismo mes, el modelo parecería bastante mejor. Esa mejora es falsa, y la tenemos lista para mostrársela al jurado.

**Lo que nos preocupó:**
1. **Demasiadas alertas.** Para detectar el 71 % hay que alertar a unos 37 de 87 municipios por mes. No es un error: la señal disponible a inicio de mes es débil. Es un intercambio: más sensibilidad cuesta más falsas alarmas.
2. **Porcentajes inflados.** La probabilidad que da el modelo es más alta que la real. El orden de los municipios sí sirve, pero el porcentaje no se debe publicar tal cual.

Ninguno bloquea; los dos se resuelven en F4.

## F3 · Primer resultado completo

**Qué hicimos:**
- **Un semáforo de dos niveles de acción.** El amarillo es amplio y barato: vigilancia, detecta el 71 %. El rojo es estrecho, unos 10 municipios al mes en promedio, para mover recursos.
- **El mapa** de Santander coloreado por nivel; al pasar el mouse muestra el municipio, su puesto y sus cifras.
- **El boletín** para el consejo municipal, con un verificador que revisa que cada número salga de los datos.

**Lo mejor de la fase:** el verificador atrapó un error real en la primera prueba. La plantilla decía "últimos 12 meses" con el 12 escrito a mano y no sacado de los datos. Eso prueba que funciona, y es justo lo que pregunta el jurado.

**Qué observamos:**
- **Enero de 2025 sale todo en verde.** Es correcto: es temporada seca y hubo un solo deslizamiento. Para la demo usamos abril, en plena temporada.
- **Abril de 2025 sale con 39 municipios en rojo, no 10,** porque el umbral es el mismo todo el año y en temporada de lluvias todos suben. En abril hubo 23 municipios con deslizamiento y el semáforo los marcó todos en rojo o amarillo, pero 39 rojos es demasiado para el consejo. **Hay que decidirlo en F4:** o el rojo se limita a los N más altos de cada mes, o aceptamos que en temporada hay más rojos y lo explicamos.
- El fondo de mapa CartoDB ahora pide clave; cambiamos a OpenStreetMap.
- El boletín decía "por qué está en alerta" aunque el municipio estuviera en verde. Lo corregimos.

**Archivos que salen:** `out/mapa_alertas.html` y `out/boletin.md`.

## F4 · Modelo principal y umbral

**Qué hicimos:** probamos XGBoost contra la logística, elegimos los umbrales con 2024 y, ya con todo congelado, hicimos la prueba final en 2025, **una sola vez**.

**La sorpresa buena:** XGBoost **sin** peso de clase resolvió dos problemas de una vez:
- predice mejor que la logística (le gana en 3 de 4 años y en 2025);
- sus porcentajes salen realistas. Si dice 20 %, pasa más o menos 1 de cada 5 veces. Eso nos deja publicar la probabilidad en el boletín sin engañar a nadie.

**Decisión:** el rojo son **los 10 municipios más altos de cada mes** (y solo si superan el umbral amarillo). Así el consejo nunca recibe más rojos de los que puede atender. En los meses secos puede haber cero rojos, y está bien.

**Cómo nos fue en 2025:**

| | Nuestro sistema | "Repetir lo del año pasado" |
|---|---|---|
| Meses con deslizamiento detectados (rojo o amarillo) | 84 % | 11 % |
| Aciertos dentro del rojo | 1 de cada 5 | n/a |

- En rojo, 1 de cada 5 municipios tuvo deslizamiento: el doble del azar (9,5 %).
- Abril y octubre: el sistema marcó en rojo o amarillo a todos los municipios que tuvieron deslizamiento.

**Lo que no salió tan bien:**
- **En temporada de lluvias, casi todo el departamento queda en amarillo** (71–77 de 87 municipios en abril, mayo y octubre). Hay que contarlo como lo que es: "temporada de lluvias, todo Santander en vigilancia". Los 10 rojos son los que necesitan acción.
- **16 de 99 deslizamientos se escaparon** (quedaron en verde). La mayoría pasó en meses secos, cuando casi no alertamos, y la mitad en municipios sin deslizamientos el año anterior. Es el límite más honesto que podemos mostrar.

**Un tropiezo:** escribimos en la sustentación que *todos* los deslizamientos no detectados eran de municipios sin historial. Lo verificamos y era falso: solo la mitad. Lo corregimos antes de que llegara al jurado. **Lección: toda cifra que vaya a la sustentación se verifica con el código.**

## F5 · Explicación por municipio

**Qué hicimos:** con SHAP medimos cuánto empuja cada dato la probabilidad de cada municipio. Agrupamos las 14 variables técnicas en 7 factores que entiende cualquiera: temporada, lluvia reciente, relieve, historial, ubicación, lluvia inusual y antecedentes en ese mes.

**Lo que aprendió el modelo, en orden de peso:**
1. **La temporada,** el factor más fuerte: abril–mayo y octubre–noviembre.
2. **La lluvia de los meses anteriores.**
3. **El relieve:** los municipios más altos tienen más riesgo.
4. **El historial reciente** de deslizamientos.

**Chequeo de sentido común:** el riesgo sube cuando sube la lluvia, el historial y la altitud. Si hubiera salido al revés, habría sido señal de un error. Salió bien.

**Decisión:** la temporada salía como primera razón en *todos* los municipios del mes, así que no ayudaba a distinguir uno de otro. La dejamos como frase de contexto ("abril es temporada de lluvias: el riesgo sube en todo el departamento") y para cada municipio mostramos sus **3 razones propias**.

**Ejemplo (San Andrés, abril de 2025, puesto 1):** 529,6 mm de lluvia en dos meses, cabecera a 1.650 m y 2 deslizamientos en el último año.

**Dónde se ve:** en el boletín (sección "Por qué está en alerta") y en el mapa, al hacer clic en un municipio. Las cifras de las razones también pasan por el verificador.

**Tropiezos:**
- **Una razón se leía al revés.** A algunos municipios les salía como motivo de alerta "la lluvia del mes anterior fue 0,7 veces su promedio", es decir, que llovió *menos* de lo normal. Pasa porque dos variables de lluvia se solapan y el modelo las compensa entre sí. Ahora solo mostramos razones que un lector entendería en el sentido correcto (lluvia inusual solo si fue mayor que el promedio, historial solo si lo hay). Agregamos una prueba para que no vuelva a pasar.
- Una gráfica salió encimada sobre otra al correr el código; se corrigió abriendo una figura nueva para cada gráfica.

## F6 · Mapa, boletines y tablero

**Qué hicimos:**
- **Un mapa por cada mes de 2025.** Al pasar el mouse sale el municipio, su nivel y su probabilidad; al hacer clic, sus 3 razones.
- **Un boletín para cada municipio que estuvo en rojo en 2025:** 98 boletines, y **ninguno con cifras sin fuente**. El verificador revisó los 98.
- **Un tablero estilo Windows 98** (`out/tablero.html`) que junta todo: selector de mes, mapa, lista de municipios ordenada por riesgo, razones, boletín, desempeño en 2025 y límites del sistema. Funciona sin internet, salvo el fondo del mapa.

**Para la presentación:** abrir `out/tablero.html` en el navegador y arrancar en abril (temporada de lluvias). Contraste útil: enero sale todo en verde, y en efecto hubo un solo deslizamiento.

**La columna "¿Ocurrió?"** muestra el dato real de 2025. Sirve para mostrarle al jurado, mes a mes, dónde acertó el sistema y dónde no.

**Tropiezo menor:** en la primera captura el mapa parecía tener solo los municipios verdes. Era que todavía estaba cargando; al terminar pinta los 87.

**Ojo:** la carpeta `out/` no se sube a GitHub, porque se genera al correr el cuaderno. Si queremos el tablero en el repositorio o en una USB, hay que copiarlo aparte.

## F7 · Cierre

**Qué hicimos:**
- **Ejecutamos el cuaderno completo en un kernel limpio**, como hará el jurado si le damos *Run All*: 30 celdas, sin errores, en unos 13 segundos. Quedó guardado con todos sus resultados, así que se puede mostrar sin correr nada.
- Silenciamos un aviso de una librería que ensuciaba la primera celda.
- **Completamos la sección final del cuaderno:** qué no puede anticipar el sistema, qué decidimos no construir y qué haríamos con dos horas más.
- **El README** explica cómo ver el resultado y cómo reproducirlo desde cero.
- Subimos `out/` al repositorio: el tablero, los 12 mapas y los 98 boletines están en GitHub.

**Comprobación de que es reproducible:** al volver a correr todo, los 98 boletines salieron idénticos. Los mapas cambian solo en identificadores internos que genera Folium, no en su contenido.

**Pendiente manual:** copiar la carpeta del proyecto (o al menos `out/`) a una USB como respaldo. Eso lo tenemos que hacer nosotros.

## Arreglo: el fondo del mapa

**Qué pasó:** al abrir el tablero como archivo en el navegador, el fondo del mapa salía lleno de avisos "403 Access blocked". OpenStreetMap bloquea sus mosaicos cuando la página no viene de un servidor web. Nosotros no lo habíamos visto porque lo probamos con un servidor local.

**Arreglo:** cambiamos el fondo a Esri (mapa topográfico), que funciona abriendo el archivo directamente y además muestra el relieve. Lo comprobamos abriendo el mapa como archivo.

**Lección:** probar siempre de la misma forma en que se va a presentar.

## F8 · Ensayo

**Qué hicimos:** escribimos el guion de 5 minutos en `docs/07_guion.md`. Tiene qué decir y qué mostrar en cada momento, dónde está el código que el jurado probablemente señale (con número de línea) y un plan B si algo falla en vivo.

**Falta, y es de nosotros:** ensayarlo en voz alta al menos una vez, con cronómetro, y hacer la prueba en vivo del verificador (agregar "350 viviendas" al boletín).

---

## Pendientes y preguntas abiertas

- [x] Decidir la regla del rojo en temporada de lluvias → los 10 más altos de cada mes (F4).
- [x] Corregir los porcentajes inflados → XGBoost sin peso de clase (F4).
- [x] Probar XGBoost contra la logística → gana XGBoost (F4).
- [x] Explicación por municipio: por qué sale cada uno en alerta (F5).
- [ ] Preguntarle a la comisión si los datos son simulados.
- [x] Llenar las cifras reales en `05_sustentacion.md`.
- [x] Subir `out/` al repositorio → subido.
- [ ] Copiar el proyecto a una USB de respaldo (manual).
- [ ] Ensayar el guion con cronómetro (manual).
