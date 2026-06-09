import os, re, requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Image Crew API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_KEY = os.environ.get("OPENAI_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def chat(system: str, user: str) -> str:
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=HEADERS,
        json={"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def dalle(prompt: str) -> dict:
    r = requests.post("https://api.openai.com/v1/images/generations", headers=HEADERS,
        json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024", "response_format": "url"}, timeout=90)
    r.raise_for_status()
    d = r.json()["data"][0]
    return {"url": d["url"], "revised": d.get("revised_prompt", prompt)}

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    image_url: str
    refined_prompt: str
    revised_prompt: str
    review: str
    score: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if not req.prompt.strip():
        raise HTTPException(400, "Prompt vacio")
    if not API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY no configurada")

    refined = chat(
        "Eres un experto en prompt engineering para DALL-E 3. "
        "Transforma el prompt del usuario en un prompt tecnico detallado en ingles "
        "especificando estilo artistico, iluminacion, composicion, paleta y calidad. "
        "Responde SOLO con el prompt, sin explicaciones.",
        req.prompt
    )

    result = dalle(refined)

    review = chat(
        "Eres un critico de arte especializado en IA generativa. "
        "Evalua el proceso de generacion y da un score del 1 al 10 con justificacion y recomendaciones. "
        "Formato: Score: X/10 seguido de tu analisis.",
        f"Prompt original: {req.prompt}\nPrompt optimizado: {refined}\nPrompt revisado por DALL-E: {result['revised']}"
    )

    score_match = re.search(r'\b([0-9]|10)\s*/\s*10\b', review)
    score = score_match.group(0) if score_match else "-"

    return GenerateResponse(
        image_url=result["url"],
        refined_prompt=refined,
        revised_prompt=result["revised"],
        review=review,
        score=score,
    )
