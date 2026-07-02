"""Cliente del LLM para el motor de recetas (§7).

Proveedor seleccionable con `LLM_PROVIDER` (settings.llm_provider):
- "claude": Anthropic (clave LLM_API_KEY, modelo LLM_MODEL).
- "openai": OpenAI    (clave OPENAI_API_KEY, modelo OPENAI_MODEL).

Ambos usan salida estructurada (esquema Pydantic `RecetasLLM`) para garantizar
el JSON estricto de la §7 sin parseo frágil. Las claves vienen del entorno;
NUNCA se hardcodean (§13).
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


def _proveedor() -> str:
    return (settings.llm_provider or "claude").strip().lower()


def llm_disponible() -> bool:
    """True si hay clave para el proveedor configurado (si no, se usa el stub)."""
    if _proveedor() == "openai":
        return bool(settings.openai_api_key)
    return bool(settings.llm_api_key)


def modelo_actual() -> str:
    """Modelo del proveedor activo (para la etiqueta fuente='llm:<modelo>')."""
    return settings.openai_model if _proveedor() == "openai" else settings.llm_model


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
    prompt = _construir_prompt(
        ingredientes_txt, restricciones_txt, presupuesto_txt, por_caducar_txt, n
    )
    if _proveedor() == "openai":
        return _generar_openai(prompt)
    return _generar_anthropic(prompt)


def _generar_anthropic(prompt: str) -> RecetasLLM:
    # Import diferido: el SDK solo se necesita cuando hay clave configurada.
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.llm_api_key)
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


def _generar_openai(prompt: str) -> RecetasLLM:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format=RecetasLLM,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("El LLM no devolvió recetas con el formato esperado")
    return parsed
