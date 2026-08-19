import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { App } from "./App";

test("explains that business behavior still depends on confirmed requirements", () => {
  render(<App />);
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("incremento vertical");
  expect(screen.getByText("OIDC pendiente de entorno")).toBeInTheDocument();
});
