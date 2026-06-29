#!/usr/bin/env bash
# Prueba con curl del motor de recetas (Fase 1).
# Requiere el servidor corriendo:  uvicorn app.main:app --reload
# Uso:  bash scripts/test_recipes.sh
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-demo@recetia.mx}"
PASS="${PASS:-superseguro123}"

echo "== 1) Registro (ignora si ya existe) =="
curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"nombre\":\"Demo\",\"rol\":\"cliente\"}" \
  >/dev/null || true

echo "== 2) Login -> JWT =="
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "token OK (${#TOKEN} chars)"

PAYLOAD='{
  "despensa":[
    {"nombre":"pechuga de pollo","cantidad":500,"unidad":"g","fecha_caducidad":"2026-06-30"},
    {"nombre":"jitomate","cantidad":4,"unidad":"pza","fecha_caducidad":"2026-07-05"},
    {"nombre":"arroz","cantidad":1,"unidad":"kg"},
    {"nombre":"cebolla","cantidad":2,"unidad":"pza"}
  ],
  "restricciones":["sin cerdo"],
  "presupuesto_semanal":800,
  "n_recetas":3
}'

echo "== 3) POST /recipes/generate (1ra vez: genera) =="
curl -s -X POST "$BASE/recipes/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | python -m json.tool

echo "== 4) POST /recipes/generate (2da vez: debe venir de caché) =="
curl -s -X POST "$BASE/recipes/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | python -c "import sys,json;d=json.load(sys.stdin);print('cache_hit =',d['cache_hit'],'| fuente =',d['fuente'])"

echo "== 5) GET /recipes/1 (detalle) =="
curl -s "$BASE/recipes/1" -H "Authorization: Bearer $TOKEN" | python -m json.tool
