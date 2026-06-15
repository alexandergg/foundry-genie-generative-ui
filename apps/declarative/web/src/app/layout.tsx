"use client";

import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

import { Fraunces } from "next/font/google";
import { CopilotKitProvider } from "@copilotkit/react-core/v2";
import { riskCatalog } from "@/catalog/renderers";

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-display",
});

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={fraunces.variable}>
      <head>
        <title>Declarative Generative UI — A2UI Component Catalog</title>
        <meta name="description" content="Declarative generative UI demo: A2UI fixed + dynamic schemas over a custom component catalog" />
      </head>
      <body>
        {/* Registering the catalog also ships its component schemas to the
            agent as context — the contract both A2UI modes compose against. */}
        <CopilotKitProvider runtimeUrl="/api/copilotkit" a2ui={{ catalog: riskCatalog }}>
          {children}
        </CopilotKitProvider>
      </body>
    </html>
  );
}
