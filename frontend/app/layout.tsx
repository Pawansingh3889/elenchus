import type { Metadata } from "next";

import { TopBar } from "@/components/TopBar";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Survey Service",
  description: "Author and conduct surveys",
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
