"""Genera un dataset SINTÉTICO de ventas retail (cocina mexicana) para el demo.

Salida: ml/data/ventas_muestra.csv  (columnas: producto, fecha, cantidad)

El patrón es aprendible: cantidad ≈ nivel_base[producto] * factor_mes * factor_finde
* factor_quincena * ruido. Así el modelo XGBoost puede generalizar a cualquier
producto a partir de su "nivel_base" (promedio reciente), que se calcula en runtime.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

# Producto -> nivel base de ventas diarias (unidades).
PRODUCTOS = {
    "jitomate": 40,
    "cebolla": 30,
    "huevo": 60,
    "tortilla": 90,
    "leche": 50,
    "frijol": 25,
    "arroz": 28,
    "pollo": 35,
    "aguacate": 22,
    "chile": 18,
}

# Estacionalidad mensual (índice 1..12). Más consumo a fin de año / fiestas.
MES_FACTOR = {
    1: 0.95, 2: 0.92, 3: 0.98, 4: 1.0, 5: 1.05, 6: 1.0,
    7: 1.02, 8: 1.0, 9: 1.03, 10: 1.05, 11: 1.1, 12: 1.25,
}


def es_quincena(d: date) -> bool:
    # En México la quincena (días de pago) sube el consumo.
    return d.day in (14, 15, 16, 29, 30, 31, 1)


def main() -> None:
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "ventas_muestra.csv")

    fin = date.today()
    inicio = fin - timedelta(days=730)  # ~2 años

    filas = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["producto", "fecha", "cantidad"])
        d = inicio
        while d <= fin:
            factor_mes = MES_FACTOR[d.month]
            factor_finde = 1.3 if d.weekday() >= 5 else 1.0
            factor_q = 1.25 if es_quincena(d) else 1.0
            for prod, nivel in PRODUCTOS.items():
                ruido = random.gauss(1.0, 0.15)
                cantidad = nivel * factor_mes * factor_finde * factor_q * ruido
                cantidad = max(0, round(cantidad))
                w.writerow([prod, d.isoformat(), cantidad])
                filas += 1
            d += timedelta(days=1)

    print(f"Dataset generado: {path} ({filas} filas, {len(PRODUCTOS)} productos)")


if __name__ == "__main__":
    main()
