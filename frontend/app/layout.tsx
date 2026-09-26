import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import { TopBar } from "@/components/TopBar";
import "./globals.css";
import { Providers } from "./providers";

/* The three faces the theme in globals.css names as --font, --font-display and
 * --font-mono. next/font self-hosts them at build time (no third-party request at
 * runtime, no flash of fallback text), and exposes each as a CSS variable that the
 * stylesheet's font tokens read straight from, rather than duplicating the family
 * name in two places. */
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-space-grotesk",
});
const jetBrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "Elenchus",
  description: "Author and conduct surveys",
};

/** Stated rather than left to the framework default, because two of these are choices.
 *  `maximumScale` is deliberately absent: capping zoom is the most common accessibility
 *  mistake on mobile, and a respondent who needs to enlarge a question must be able to.
 *  `viewportFit: "cover"` lets the layout reach under a notch, which matters for the
 *  runner, where the chat thread is the full height of the screen. */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetBrainsMono.variable}`}
    >
      <body>
        <Providers>
          <TopBar />
          <main className="app-main">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
