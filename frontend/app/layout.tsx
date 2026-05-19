import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Image Crew — Multi-Agent Image Generator",
  description: "Tres agentes de IA colaboran para generar tu imagen perfecta con DALL-E 3",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
