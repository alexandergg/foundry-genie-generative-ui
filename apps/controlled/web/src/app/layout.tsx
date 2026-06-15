"use client";

import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

import { Fraunces } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";

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
        <title>Risk & Exposure Intelligence Copilot</title>
        <meta name="description" content="Generative UI demo with Azure AI Foundry, Databricks Genie and AG-UI" />
      </head>
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
