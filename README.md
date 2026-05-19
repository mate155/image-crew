# Image Crew 🎨

Sistema multi-agente para generación de imágenes con DALL-E 3.
**Pipeline:** Finetuner → Creador → Reviewer

---

## Estructura del proyecto

```
image-crew/
├── backend/          ← FastAPI  (deploy en Railway)
│   ├── main.py
│   ├── requirements.txt
│   ├── Procfile
│   └── railway.toml
└── frontend/         ← Next.js  (deploy en Vercel)
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── page.module.css
    │   └── globals.css
    ├── next.config.js
    ├── package.json
    └── vercel.json
```

---

## Deploy — Paso a paso

### 1. Subir el código a GitHub

```bash
cd image-crew
git init
git add .
git commit -m "init: image crew multi-agent"
git remote add origin https://github.com/TU_USUARIO/image-crew.git
git push -u origin main
```

---

### 2. Deploy del Backend en Railway

1. Entrá a **[railway.app](https://railway.app)** y creá una cuenta (gratis).
2. Hacé clic en **"New Project" → "Deploy from GitHub repo"**.
3. Seleccioná tu repo y elegí la carpeta **`backend`** como root directory.
   - En Railway: Settings → Source → Root Directory → `backend`
4. En **Variables de entorno** agregá:
   ```
   OPENAI_API_KEY=sk-...tu_clave_aqui...
   ```
5. Railway detecta automáticamente el `Procfile` y despliega.
6. Una vez deployado, copiá la URL pública (ej: `https://image-crew-backend.railway.app`).
7. Verificá que funciona: `https://TU_URL.railway.app/health` → debe devolver `{"status":"ok"}`

> ⚠️ El plan gratuito de Railway incluye $5/mes de créditos, suficiente para pruebas.

---

### 3. Deploy del Frontend en Vercel

1. Entrá a **[vercel.com](https://vercel.com)** y creá una cuenta.
2. Hacé clic en **"Add New Project" → importá tu repo de GitHub**.
3. Configurá el proyecto:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Next.js (se detecta automáticamente)
4. En **Environment Variables** agregá:
   ```
   NEXT_PUBLIC_API_URL=https://TU_URL.railway.app
   ```
   (reemplazá con la URL real de Railway del paso anterior)
5. Hacé clic en **Deploy**.
6. ¡Listo! Vercel te da una URL pública del tipo `https://image-crew.vercel.app`.

---

## Desarrollo local

### Backend
```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Editá .env.local y ponés: NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
Abrí [http://localhost:3000](http://localhost:3000)

---

## Variables de entorno

| Variable | Dónde | Descripción |
|---|---|---|
| `OPENAI_API_KEY` | Railway (backend) | Tu API key de OpenAI |
| `NEXT_PUBLIC_API_URL` | Vercel (frontend) | URL del backend deployado |

---

## Notas

- La generación tarda ~40-60 segundos (3 agentes en secuencia + DALL-E 3).
- Las URLs de DALL-E 3 expiran en ~1 hora; descargá la imagen si la necesitás guardar.
- Para producción seria, considerá el plan Pro de Railway para evitar cold starts.
