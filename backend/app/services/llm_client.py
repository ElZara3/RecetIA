"""Cliente del LLM (Anthropic / Claude) para el motor de recetas.

- La clave viene de `LLM_API_KEY` (entorno); NUNCA se hardcodea (§13).
- Usa salida estructurada (`messages.parse` + esquema Pydantic) para garantizar
  el JSON estricto de la §7 sin parseo frágil.
- Modelo por defecto: `claude-opus-4-8` (configurable con `LLM_MODEL`).
"""

from app.core.config import settings
from app.schemas.recipes import RecetasLLM

_SYSTEM = (
    "Eres el motor de recetas de RecetIA. Diseñas recetas realistas de cocina "
    "mexicana casera y económica que aprovechan sobre todo los ingredientes que el "
    "hogar YA tiene —priorizando los más próximos a caducar— y minimizan compras "
    "extra. Los costos por porción y el ahorro estimado van en pesos mexicanos (MXN) "
    "con valores realistas para México."
)


def _construir_prompt(
    ingredientes_txt: str,
    restricciones_txt: str,
    presupuesto_txt: str,
    por_caducar_txt: str,
    n: int,
) -> str:
    return (
        "Ingredientes disponibles (ordenados: usar primero los más próximos a "
        f"caducar):\n{ingredientes_txt}\n\n"
        f"Prioriza usar estos que están por caducar: {por_caducar_txt or 'ninguno'}\n"
        f"Restricciones del hogar: {restricciones_txt or 'ninguna'}\n"
        f"Presupuesto orientativo semanal: {presupuesto_txt}\n\n"
        f"Genera exactamente {n} recetas que aprovechen sobre todo lo que ya hay, "
        "minimizando los ingredientes faltantes. Para cada receta calcula el costo "
        "por porción y el ahorro estimado (vs. comprar/pedir comida) en MXN."
    )


def generar_con_llm(
    ingredientes_txt: str,
    restricciones_txt: str,
    presupuesto_txt: str,
    por_caducar_txt: str,
    n: int,
) -> RecetasLLM:
    # Import diferido: el SDK solo se necesita cuando hay clave configurada.
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.llm_api_key)
    prompt = _construir_prompt(
        ingredientes_txt, restricciones_txt, presupuesto_txt, por_caducar_txt, n
    )
    response = client.messages.parse(
        model=settings.llm_model,
        max_tokens=4096,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=RecetasLLM,
    )
    parsed = response.parsed_output
    if parsed is None:
        raise RuntimeError("El LLM no devolvió recetas con el formato esperado")
    return parsed
