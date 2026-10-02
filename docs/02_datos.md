# Datos: diccionario y hallazgos

Revisión hecha sobre los archivos de `data/` (repositorio del equipo, commit `89f4280`). Las cifras de esta página salen de esa revisión; hay que recalcularlas si cambian los datos.

## Archivos

| Archivo | Filas | Granularidad | Uso |
|---|---|---|---|
| `emergencias_santander.csv` | 1.472 | Un evento | Historial por tipo; cálculo de `mm_12m` |
| `panel_municipio_mes.csv` | 11.484 | Municipio × mes (87 × 132) | Tabla de modelado |
| `municipios_santander.csv` | 87 | Municipio | Coordenadas y altitud de la cabecera |
| `santander_municipios.geojson` | 87 polígonos | Municipio | Mapa coroplético |

Cobertura temporal: enero de 2015 a diciembre de 2025 (11 años, 132 meses).

## Diccionario

### `emergencias_santander.csv`

| Columna | Tipo | Nota |
|---|---|---|
| `fecha` | fecha `YYYY-MM-DD` | Sin fechas inválidas |
| `municipio` | texto | 87 nombres, uno por código |
| `codigo_dane` | entero | Llave |
| `evento` | categoría | Movimiento en masa (1.009), Inundación (184), Incendio forestal (131), Vendaval (80), Creciente súbita (68) |
| `personas_afectadas` | entero | 24 eventos con 0 |
| `viviendas_afectadas` | entero | |
| `vias_afectadas` | 0/1 | Bandera, no conteo |

### `panel_municipio_mes.csv`

| Columna | ¿Se conoce el día 1 del mes? | Nota |
|---|---|---|
| `codigo_dane`, `municipio`, `anio`, `mes` | Sí | Llaves; sin duplicados |
| `lluvia_mm` | **No, es fuga** | Lluvia del mismo mes |
| `lluvia_mm_mes_anterior` | Sí | Coincide 100 % con el rezago de `lluvia_mm` |
| `eventos_mes` | **No** | Total de emergencias del mes |
| `hubo_mm` | Objetivo | Coincide 100 % con el archivo de emergencias |
| `eventos_12m` | Sí | Emergencias de los 12 meses anteriores, sin el mes actual |
| `altitud_m` | Sí | Constante por municipio |

### `municipios_santander.csv`

`codigo_dane`, `municipio`, `latitud`, `longitud`, `altitud_m`. Sin nulos.

## Hallazgos

1. **Datos limpios.** No hay nulos, duplicados ni nombres de municipio escritos de varias formas. Los 87 códigos DANE coinciden en los cuatro archivos. Aun así unimos siempre por `codigo_dane`, nunca por nombre. Que estén tan limpios sugiere que son el panel sintético del plan B; hay que confirmarlo con la comisión.
2. **La trampa de fuga se confirma.** La correlación de `hubo_mm` con `lluvia_mm` (mismo mes) es 0,26. Con `lluvia_mm_mes_anterior` es 0,14. Un modelo que use `lluvia_mm` se verá mucho mejor de lo que será en la práctica.
3. **`eventos_12m` en 2015 trae historia de 2014.** En 2015 no coincide con la suma móvil del panel (466 filas difieren) porque incluye eventos anteriores al panel. Por eso conviene descartar 2015 como año de entrenamiento si usamos rezagos de 12 meses calculados por nosotros.
4. **Desbalance.** La tasa de `hubo_mm` es 8,3 % (unos 950 positivos). Varía mucho por año: 3,6 % en 2016 y 14,6 % en 2022. La validación debe incluir años secos y húmedos.
5. **Bimodalidad estacional.** La tasa mensual de `hubo_mm` muestra dos temporadas:

| Mes | Ene | Feb | Mar | **Abr** | **May** | Jun | Jul | Ago | Sep | **Oct** | **Nov** | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tasa `hubo_mm` | 1,4 % | 2,1 % | 7,6 % | **15,6 %** | **13,9 %** | 6,0 % | 4,3 % | 4,9 % | 6,7 % | **17,6 %** | **14,8 %** | 4,4 % |

   Por eso el mes se codifica con seno y coseno, que capturan el ciclo sin saltos de diciembre a enero.
6. **Cola pesada de lluvia.** La mediana de `lluvia_mm` es 109 mm, el percentil 99 es 707 mm y el máximo 2.071 mm. Los árboles lo toleran. Para la regresión logística usamos `log1p`.
7. **Magnitud por tipo.** Las inundaciones afectan en promedio a 97 personas por evento; los movimientos en masa a 23. Los movimientos en masa son más frecuentes pero menos masivos, y eso conviene decirlo en el boletín.
