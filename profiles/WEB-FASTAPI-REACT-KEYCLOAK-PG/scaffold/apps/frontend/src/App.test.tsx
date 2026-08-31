import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { App } from "./App";

test("keeps the isolated component state explicit without integration", () => {
  render(<App />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("incremento vertical");
  expect(screen.getByText("OIDC pendiente de entorno")).toBeInTheDocument();
  expect(screen.getByText("Scaffold listo")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Guardar elemento" })).not.toBeInTheDocument();
});
