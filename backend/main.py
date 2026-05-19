import os
import warnings
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew
from crewai.tools import tool

warnings.filterwarnings("ignore")

app = FastAPI(title="Image Crew API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OpenAI config ──────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# ── Tool: DALL-E 3 ─────────────────────────────────────────────────────────────
@tool("generate_image")
def generate_image(prompt: str) -> str:
    """
    Genera una imagen usando DALL-E 3.
    Args:
        prompt: Prompt optimizado para la generación.
    Returns:
        URL de la imagen y revised_prompt.
    """
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard",
            "response_format": "url",
        },
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    image_url = data["data"][0]["url"]
    revised = data["data"][0].get("revised_prompt", prompt)
    return f"IMAGE_URL: {image_url}\nREVISED_PROMPT: {revised}"


# ── Agents ─────────────────────────────────────────────────────────────────────
def build_crew():
    finetuner = Agent(
        role="Prompt Engineer especializado en generación de imágenes",
        goal="Transformar el prompt del usuario en un prompt técnico y detallado optimizado para DALL-E 3.",
        backstory=(
            "Sos un experto en prompt engineering para DALL-E 3. "
            "Convertís ideas del usuario en prompts en inglés que extraen el máximo potencial del modelo, "
            "especificando estilo artístico, iluminación, composición, paleta y calidad técnica."
        ),
        allow_delegation=False,
        verbose=True,
    )

    creator = Agent(
        role="Artista digital y generador de imágenes con IA",
        goal="Usar el prompt optimizado para generar la imagen con DALL-E 3 y reportar la URL resultante.",
        backstory=(
            "Sos el brazo ejecutor del equipo. Recibís el prompt pulido del Finetuner "
            "y lo enviás a DALL-E 3. Tu responsabilidad es ejecutar la generación y reportar el resultado."
        ),
        tools=[generate_image],
        allow_delegation=False,
        verbose=True,
    )

    reviewer = Agent(
        role="Crítico de arte y analista de calidad de imágenes generadas por IA",
        goal="Evaluar la imagen generada y producir un informe con score y recomendaciones.",
        backstory=(
            "Sos un crítico de arte con experiencia en producción visual e IA generativa. "
            "Analizás si la imagen cumple con la intención del usuario y das recomendaciones concretas."
        ),
        allow_delegation=False,
        verbose=True,
    )

    finetune_task = Task(
        description=(
            "El usuario quiere generar: '{user_prompt}'\n"
            "Construí un prompt detallado en inglés para DALL-E 3 con: sujeto, estilo artístico, "
            "iluminación, composición, paleta de colores y palabras clave de calidad."
        ),
        expected_output="Un prompt en inglés optimizado para DALL-E 3, de 100-300 palabras.",
        agent=finetuner,
    )

    create_task = Task(
        description=(
            "Enviá el prompt optimizado del Finetuner a la tool 'generate_image'. "
            "Reportá la URL de la imagen y el revised_prompt de DALL-E."
        ),
        expected_output="URL de imagen generada + revised_prompt + confirmación de éxito o error.",
        agent=creator,
        context=[finetune_task],
    )

    review_task = Task(
        description=(
            "Prompt original: '{user_prompt}'\n"
            "Evaluá si el prompt optimizado captó la intención del usuario. "
            "Asigná un score (1-10) y dá recomendaciones concretas de mejora."
        ),
        expected_output=(
            "Informe con: URL final de la imagen, score (1-10), "
            "análisis de alineación y recomendaciones de mejora."
        ),
        agent=reviewer,
        context=[finetune_task, create_task],
    )

    return Crew(
        agents=[finetuner, creator, reviewer],
        tasks=[finetune_task, create_task, review_task],
        verbose=2,
    )


# ── Schemas ────────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    image_url: str
    refined_prompt: str
    revised_prompt: str
    review: str
    score: str


# ── Helpers ────────────────────────────────────────────────────────────────────
def extract_image_url(text: str) -> str:
    for line in text.splitlines():
        if "IMAGE_URL:" in line:
            return line.split("IMAGE_URL:")[-1].strip()
        if line.strip().startswith("http") and ("openai" in line or "oaistatic" in line):
            return line.strip()
    # fallback: find any https URL in the text
    import re
    urls = re.findall(r'https://[^\s\)\"\']+', text)
    for url in urls:
        if "oaistatic" in url or "openai" in url or "dalle" in url.lower():
            return url
    return urls[0] if urls else ""


def extract_score(text: str) -> str:
    import re
    matches = re.findall(r'\b([0-9]|10)\s*/\s*10\b', text)
    return matches[0] + "/10" if matches else "—"


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío.")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY no configurada.")

    try:
        crew = build_crew()
        result = crew.kickoff(inputs={"user_prompt": req.prompt})
        result_str = str(result)

        # Extract fields from the full crew output
        image_url = extract_image_url(result_str)
        score = extract_score(result_str)

        # Get refined prompt from tasks output
        tasks_output = crew.tasks
        refined = ""
        revised = ""
        for task in tasks_output:
            out = str(getattr(task, "output", "") or "")
            if "IMAGE_URL:" in out and not image_url:
                image_url = extract_image_url(out)
            if "REVISED_PROMPT:" in out:
                for line in out.splitlines():
                    if "REVISED_PROMPT:" in line:
                        revised = line.split("REVISED_PROMPT:")[-1].strip()
            if refined == "" and out and "IMAGE_URL:" not in out and "REVISED_PROMPT:" not in out:
                refined = out[:500]

        return GenerateResponse(
            image_url=image_url,
            refined_prompt=refined or "—",
            revised_prompt=revised or "—",
            review=result_str,
            score=score,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
