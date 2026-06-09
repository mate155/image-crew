"use client";
import { useState, useRef, useEffect } from "react";
import styles from "./page.module.css";

type Stage = "idle" | "finetuning" | "creating" | "reviewing" | "done" | "error";

interface Result {
  image_url: string;
  refined_prompt: string;
  revised_prompt: string;
  review: string;
  score: string;
}

const STAGE_LABELS: Record<Stage, string> = {
  idle: "",
  finetuning: "Optimizando el prompt...",
  creating: "Generando imagen...",
  reviewing: "Evaluando resultado...",
  done: "",
  error: "",
};

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [showReview, setShowReview] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }, [prompt]);

  const simulateStages = () => {
    setStage("finetuning");
    timerRef.current = setTimeout(() => setStage("creating"), 8000);
    timerRef.current = setTimeout(() => setStage("reviewing"), 28000);
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || stage !== "idle") return;
    setError("");
    setResult(null);
    setShowReview(false);
    simulateStages();

    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Error del servidor");
      }
      const data: Result = await res.json();
      setResult(data);
      setStage("done");
    } catch (e: unknown) {
      setStage("error");
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  };

  const handleReset = () => {
    setStage("idle");
    setResult(null);
    setError("");
    setPrompt("");
    setShowReview(false);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const isLoading = ["finetuning", "creating", "reviewing"].includes(stage);

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>ImgBoost</h1>
      </header>

      <div className={styles.pipeline}>
        {(["finetuner", "creador", "reviewer"] as const).map((agent, i) => {
          const stageMap = { finetuner: "finetuning", creador: "creating", reviewer: "reviewing" };
          const doneMap = { finetuner: ["creating","reviewing","done"], creador: ["reviewing","done"], reviewer: ["done"] };
          const isActive = stage === stageMap[agent];
          const isDone = (doneMap[agent] as Stage[]).includes(stage);
          return (
            <div key={agent} className={styles.pipelineItem}>
              <div className={`${styles.dot} ${isActive ? styles.dotActive : ""} ${isDone ? styles.dotDone : ""}`}>
                {isDone ? "✓" : i + 1}
              </div>
              <span className={`${styles.agentName} ${isActive ? styles.agentActive : ""}`}>
                {agent}
              </span>
            </div>
          );
        })}
      </div>

      {(stage === "idle" || isLoading) && (
        <section className={styles.inputSection}>
          <div className={styles.inputWrapper}>
            <textarea
              ref={textareaRef}
              className={styles.textarea}
              placeholder="Describí la imagen que querés generar..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isLoading}
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleGenerate();
              }}
            />
            <button
              className={`${styles.btn} ${isLoading ? styles.btnLoading : ""}`}
              onClick={handleGenerate}
              disabled={isLoading || !prompt.trim()}
            >
              {isLoading ? <span className={styles.spinner} /> : "Generar →"}
            </button>
          </div>
          <p className={styles.hint}>⌘ + Enter para generar</p>
          {isLoading && (
            <div className={styles.statusBar}>
              <span className={styles.statusDot} />
              {STAGE_LABELS[stage]}
            </div>
          )}
        </section>
      )}

      {stage === "done" && result && (
        <section className={styles.result}>
          <div className={styles.imageContainer}>
            {result.image_url ? (
              <img src={result.image_url} alt="Imagen generada" className={styles.generatedImage} />
            ) : (
              <div className={styles.noImage}>No se encontró URL de imagen</div>
            )}
            <div className={styles.imageBadge}>{result.score}</div>
          </div>
          <div className={styles.meta}>
            <p className={styles.originalPrompt}>
              <span className={styles.metaLabel}>Tu prompt</span>
              {prompt}
            </p>
            <button className={styles.reviewToggle} onClick={() => setShowReview(!showReview)}>
              {showReview ? "Ocultar análisis ↑" : "Ver análisis del Reviewer ↓"}
            </button>
            {showReview && (
              <div className={styles.review}>
                <pre className={styles.reviewText}>{result.review}</pre>
              </div>
            )}
            <div className={styles.actions}>
              <a href={result.image_url} target="_blank" rel="noopener noreferrer" className={styles.btnSecondary}>
                Abrir imagen ↗
              </a>
              <button className={styles.btnPrimary} onClick={handleReset}>Nueva imagen</button>
            </div>
          </div>
        </section>
      )}

      {stage === "error" && (
        <section className={styles.errorSection}>
          <p className={styles.errorText}>✗ {error}</p>
          <button className={styles.btnPrimary} onClick={handleReset}>Reintentar</button>
        </section>
      )}
    </main>
  );
}
