# ml/ — Forecasting (Pilar B)

Predicción de demanda por producto para el panel de comercio, expuesta vía
`GET /comercio/forecast`. Modelo: **XGBoost** (tabular, rápido, interpretable, §10).

## Generar dataset + entrenar
Desde la raíz del repo, con el venv del backend (que ya trae xgboost/pandas/sklearn):

```bash
backend/.venv/Scripts/python ml/generate_data.py   # -> ml/data/ventas_muestra.csv
backend/.venv/Scripts/python ml/train.py           # -> ml/models/forecast_xgb.json + metadata.json
```

(En macOS/Linux: `backend/.venv/bin/python`.)

## Cómo funciona
- `generate_data.py` crea ventas **sintéticas** (~2 años, 10 productos de cocina
  mexicana) con estacionalidad por mes, fin de semana y quincena (días de pago).
- `train.py` entrena un `XGBRegressor` con features `[nivel_base, mes, semana,
  día_semana, es_fin_de_semana, es_quincena]` → `cantidad`. Aprende el multiplicador
  estacional sobre el **nivel base** del producto, así generaliza a cualquier
  comercio: en runtime el backend calcula `nivel_base` del histórico real del
  comercio (`VentaRegistro`) y pide la predicción.
- **Cold-start**: un comercio nuevo usa `global_mean_nivel` (prior) hasta tener datos.
- El backend ([backend/app/services/forecasting.py](../backend/app/services/forecasting.py))
  carga `ml/models/forecast_xgb.json`. Si no existe, cae a una heurística estacional
  simple (`fuente: "heuristica"`), así el endpoint funciona aunque no se haya entrenado.

## Salidas del endpoint
Demanda diaria estimada (serie para la gráfica) + por producto: demanda del periodo,
existencias, **recomendación de reabasto** y flag de **riesgo de merma**.
