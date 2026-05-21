"use client";

import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

import { CopilotKit } from "@copilotkit/react-core";

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
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
