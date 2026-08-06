import type { Metadata, Viewport } from "next";

import { TopBar } from "@/components/TopBar";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Survey Service",
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
    <html lang="en">
      <body>
        <Providers>
          <TopBar />
          <main className="app-main">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
