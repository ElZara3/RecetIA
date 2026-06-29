"""Entrena un XGBoost de demanda sobre el dataset de muestra y guarda el modelo.

Salidas en ml/models/:
- forecast_xgb.json     (modelo XGBoost, formato nativo)
- metadata.json         (orden de features, nivel global para cold-start, MAE)

Features: nivel_base + calendario (mes, semana, día de semana, fin de semana,
quincena). El modelo aprende el multiplicador estacional sobre el nivel base, de
modo que sirve para cualquier producto/comercio dándole su nivel_base en runtime.
"""

import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

FEATURES = ["nivel_base", "mes", "semana", "dia_semana", "es_fin_de_semana", "es_quincena"]
HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "ventas_muestra.csv")
MODELS_DIR = os.path.join(HERE, "models")


def construir_features(df: pd.DataFrame, nivel_por_producto: dict[str, float]) -> pd.DataFrame:
    fechas = pd.to_datetime(df["fecha"])
    out = pd.DataFrame()
    out["nivel_base"] = df["producto"].map(nivel_por_producto).astype(float)
    out["mes"] = fechas.dt.month
    out["semana"] = fechas.dt.isocalendar().week.astype(int)
    out["dia_semana"] = fechas.dt.dayofweek
    out["es_fin_de_semana"] = (fechas.dt.dayofweek >= 5).astype(int)
    dia = fechas.dt.day
    out["es_quincena"] = dia.isin([14, 15, 16, 29, 30, 31, 1]).astype(int)
    return out[FEATURES]


def main() -> None:
    if not os.path.exists(DATA):
        raise SystemExit(f"No existe {DATA}. Corre primero: python ml/generate_data.py")

    df = pd.read_csv(DATA)
    nivel = df.groupby("producto")["cantidad"].mean().to_dict()

    X = construir_features(df, nivel)
    y = df["cantidad"].astype(float)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X.to_numpy(), y.to_numpy(), test_size=0.2, random_state=42
    )
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    # Entrena con numpy (sin nombres de columnas) para que el servicio pueda
    # predecir con arrays sin warnings de feature names.
    model.fit(X_tr, y_tr)

    mae = float(mean_absolute_error(y_te, model.predict(X_te)))

    os.makedirs(MODELS_DIR, exist_ok=True)
    model.save_model(os.path.join(MODELS_DIR, "forecast_xgb.json"))
    metadata = {
        "features": FEATURES,
        "global_mean_nivel": float(np.mean(list(nivel.values()))),
        "trained_rows": int(len(df)),
        "mae": mae,
        "importancias": {
            f: float(i) for f, i in zip(FEATURES, model.feature_importances_)
        },
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Modelo entrenado. MAE(test) = {mae:.2f} unidades.")
    print("Importancia de features:", metadata["importancias"])


if __name__ == "__main__":
    main()
