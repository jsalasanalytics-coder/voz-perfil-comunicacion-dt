import type { Metadata } from "next";
import "./globals.css";
import Shell from "@/components/Shell";

export const metadata: Metadata = {
  title: "Voz",
  description: "Perfil de comunicación de entrenadores mediante NLP (Topic Modeling)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="font-sans antialiased text-ink">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
