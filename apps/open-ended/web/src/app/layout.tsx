"use client";

import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";

import { Fraunces } from "next/font/google";
import { CopilotKitProvider } from "@copilotkit/react-core/v2";

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
        <title>Open-Ended Generative UI — MCP Apps + Sandboxed UI</title>
        <meta name="description" content="Open-ended generative UI demo: sandboxed generated interfaces and MCP Apps with CopilotKit and AG-UI" />
      </head>
      <body>
        <CopilotKitProvider runtimeUrl="/api/copilotkit">{children}</CopilotKitProvider>
      </body>
    </html>
  );
}
