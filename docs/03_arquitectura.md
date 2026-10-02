# Arquitectura

Trabajo local en VS Code, una sola persona escribe el código. Un cuaderno orquesta el flujo y presenta los resultados. La lógica que el jurado puede auditar vive en módulos pequeños de `src/satmm/`. Todo corre sin internet, salvo el fondo del mapa (tiles de OpenStreetMap) y el modelo de lenguaje opcional.

## Estructura del repositorio

```
simulacro hackaton/
├── data/                          # datos originales, solo lectura
│   ├── emergencias_santander.csv
│   ├── panel_municipio_mes.csv
│   ├── municipios_santander.csv
│   └── santander_municipios.geojson
├── docs/                          # esta documentación + enunciado PDF
├── src/satmm/
│   ├── datos.py                   # carga y validación de esquemas
│   ├── variables.py               # rezagos, climatología, mes cíclico
│   ├── validacion.py              # pliegues por año, métricas, líneas base
│   ├── modelo.py                  # entrenar, umbral, semáforo, SHAP
│   ├── mapa.py                    # Folium
│   └── boletin.py                 # plantilla + verificador
├── tests/test_boletin.py          # el verificador debe rechazar cifras inventadas
├── alerta.ipynb                   # orquestación y presentación
├── out/                           # mapa, boletines, gráficas (generado)
└── pyproject.toml                 # dependencias fijadas, Python 3.12
```

## Vista de componentes

```mermaid
flowchart TB
    subgraph Datos["data/ (solo lectura)"]
        E[(emergencias_santander.csv)]
        P[(panel_municipio_mes.csv)]
        M[(municipios_santander.csv)]
        G[(santander_municipios.geojson)]
    end

    subgraph Nucleo["src/satmm"]
        D[datos.py<br/>carga + validación de esquemas]
        V[variables.py<br/>rezagos sin fuga]
        VA[validacion.py<br/>pliegues por año + métricas]
        MO[modelo.py<br/>XGBoost + umbral + SHAP]
        MA[mapa.py<br/>Folium]
        B[boletin.py<br/>plantilla + verificador]
    end

    NB[[alerta.ipynb<br/>orquestación y presentación]]

    subgraph Salidas["out/"]
        O1[mapa_alertas.html]
        O2[boletin_municipio.md]
        O3[metricas.csv + gráficas SHAP]
    end

    E & P & M --> D --> V --> VA --> MO
    MO --> MA --> O1
    G --> MA
    MO --> B --> O2
    VA --> O3
    NB -. llama .-> D & V & VA & MO & MA & B
```

## Diagrama de clases

Los módulos son funcionales. Las clases son contenedores de datos (`dataclass`), para que las firmas sean claras.

```mermaid
classDiagram
    direction LR

    class Datos {
        +cargar_panel(ruta) DataFrame
        +cargar_emergencias(ruta) DataFrame
        +cargar_municipios(ruta) DataFrame
        +validar_esquema(df, columnas) None
    }

    class Variables {
        +FEATURES list~str~
        +EXCLUIDAS list~str~
        +construir(panel, emergencias, municipios) DataFrame
        +climatologia(df, anios_train) DataFrame
        -rezago(df, col, k) Series
        -suma_movil_previa(df, col, n) Series
    }

    class Pliegue {
        +int anio_valida
        +list~int~ anios_train
    }

    class Validacion {
        +pliegues(desde, hasta) list~Pliegue~
        +linea_base_anio_anterior(df) Series
        +linea_base_climatologia(df) Series
        +metricas(y, p, umbral) dict
        +precision_top_k(df, p, k) float
    }

    class ModeloAlerta {
        +XGBClassifier clf
        +float umbral
        +list~str~ features
        +entrenar(X, y) ModeloAlerta
        +predecir(X) ndarray
        +elegir_umbral(y, p, recall_min) float
        +semaforo(p) str
        +explicar(X) DataFrame
        +razones(fila, shap, k) list~Razon~
    }

    class Razon {
        +str variable
        +float valor
        +float aporte_shap
        +str frase
    }

    class Alerta {
        +int codigo_dane
        +str municipio
        +int anio
        +int mes
        +float probabilidad
        +str nivel
        +list~Razon~ razones
    }

    class Mapa {
        +construir(alertas, geojson) folium.Map
        +guardar(mapa, ruta) None
    }

    class Boletin {
        +cifras(alerta, historial) dict
        +redactar(cifras, plantilla) str
        +verificar(texto, cifras) set~float~
        +generar(alerta, historial) str
    }

    Datos --> Variables : DataFrames
    Variables --> Validacion : tabla de modelado
    Validacion --> Pliegue : crea
    Validacion --> ModeloAlerta : entrena por pliegue
    ModeloAlerta --> Alerta : produce
    Alerta *-- Razon
    Alerta --> Mapa
    Alerta --> Boletin
```

## Secuencia: correr la alerta de un mes

```mermaid
sequenceDiagram
    autonumber
    actor U as Analista (cuaderno)
    participant D as datos
    participant V as variables
    participant M as ModeloAlerta
    participant MA as mapa
    participant B as boletin

    U->>D: cargar panel, emergencias, municipios
    D-->>U: DataFrames validados
    U->>V: construir(panel, emergencias, municipios)
    V-->>U: tabla con rezagos (sin lluvia_mm)
    U->>M: entrenar(X ≤ 2024, y)
    U->>M: predecir(X del mes objetivo)
    M-->>U: probabilidades
    U->>M: semaforo(p) + explicar(X)
    M-->>U: lista de Alerta con 3 razones
    U->>MA: construir(alertas, geojson)
    MA-->>U: out/mapa_alertas.html
    U->>B: generar(alerta roja de mayor p, historial)
    B->>B: cifras → plantilla → verificar
    alt número intruso
        B->>B: rechazar y usar la plantilla base
    end
    B-->>U: out/boletin_municipio.md
```

## Estados del semáforo

```mermaid
stateDiagram-v2
    [*] --> Verde
    Verde --> Amarillo : p ≥ umbral/2
    Amarillo --> Rojo : p ≥ umbral
    Rojo --> Amarillo : umbral/2 ≤ p < umbral
    Amarillo --> Verde : p < umbral/2
    Verde --> Rojo : p ≥ umbral
    Rojo --> Verde : p < umbral/2
    note right of Rojo
        Genera boletín al
        consejo municipal
    end note
```

El estado se recalcula desde cero cada mes. El diagrama muestra transiciones posibles, no memoria entre meses.

## Decisiones de diseño

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Cuaderno + módulos pequeños | Solo cuaderno | Los módulos permiten probar el verificador y mostrar código limpio al jurado; el cuaderno sigue siendo la presentación |
| XGBoost | Bosque aleatorio | Igual de rápido con este tamaño, maneja el desbalance con `scale_pos_weight` y tiene SHAP exacto con `TreeExplainer` |
| Folium + GeoJSON | GeoPandas + matplotlib | Mapa interactivo con ventanas emergentes, sin dependencias GDAL |
| Plantilla Jinja2 como base | Solo modelo de lenguaje | Funciona sin internet y es determinista; el modelo de lenguaje es opcional y pasa por el verificador |
| Unir por `codigo_dane` | Unir por nombre | Los nombres cambian (tildes, mayúsculas); el código no |
| Python 3.12 en `.venv` (uv) | Python 3.14 del sistema | shap depende de numba, que puede no tener versión para 3.14 |
