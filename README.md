# Hackathon UDES: SATMM Santander

Prototipo de alerta temprana de movimientos en masa para los 87 municipios de Santander (reto avanzado).

**Ver el resultado:** abrir [`out/tablero.html`](out/tablero.html) en el navegador. Arrancar en abril de 2025 (temporada de lluvias).

## Contenido
- `data/`: datos del reto (emergencias UNGRD, panel municipio-mes, cabeceras, GeoJSON).
- `docs/`: propuesta, arquitectura, plan, sustentación y bitácora. Empezar por [docs/README.md](docs/README.md).
- `src/satmm/`: código (datos, variables, validación, modelo, explicación, mapa, boletín, tablero).
- `alerta.ipynb`: cuaderno de presentación, ejecutado de principio a fin.
- `out/`: tablero, mapas por mes, 98 boletines verificados y gráficas SHAP.

## Reproducir
Requiere [uv](https://docs.astral.sh/uv/). Con internet, una sola vez:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv pandas numpy scikit-learn xgboost-cpu shap folium jinja2 matplotlib ipykernel pytest nbclient nbformat
```

Luego, sin internet:

```bash
.venv/bin/python -m pytest -q tests
```

Abrir `alerta.ipynb` en VS Code con el kernel `.venv` y ejecutar *Run All* (unos 15 s). Regenera todo `out/`.
