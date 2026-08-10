import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { Transcript } from "@/components/Transcript";

/**
 * A smoke test, and only that.
 *
 * It proves the harness works end to end: TypeScript compiles, JSX transforms, the `@/`
 * alias resolves through tsconfig, jsdom provides a DOM, and Testing Library can query
 * it. It asserts nothing about behaviour on purpose. Real tests get written when
 * something breaks, so that each one names a bug that actually happened.
 *
 * `Transcript` is the subject because it takes props and returns markup: no store, no
 * provider, no network. If this fails, the harness is broken rather than the app.
 */
test("the harness renders a component and can query it", () => {
  render(
    <Transcript
      messages={[
        { role: "assistant", content: "What's your role?", created_at: "2026-08-10T00:00:00Z" },
        { role: "user", content: "Line lead", created_at: "2026-08-10T00:00:01Z" },
      ]}
    />,
  );

  expect(screen.getByText("What's your role?")).toBeDefined();
  expect(screen.getByText("Line lead")).toBeDefined();
});
