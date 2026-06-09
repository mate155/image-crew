import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ImgBoost",
  description: "Generador de imágenes con IA",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
