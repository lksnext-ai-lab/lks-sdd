import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { bootstrapAuthentication } from "./auth";
import "./styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("Missing #root element");

async function bootstrap() {
  try {
    const auth = await bootstrapAuthentication(import.meta.env);
    createRoot(root as HTMLElement).render(<StrictMode><App auth={auth} /></StrictMode>);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown identity configuration error";
    createRoot(root as HTMLElement).render(<StrictMode><App configurationError={message} /></StrictMode>);
  }
}

void bootstrap();
