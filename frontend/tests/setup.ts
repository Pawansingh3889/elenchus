import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Unmount between tests. Without it every render stays in the document and a query that
// should match one element matches several, which surfaces as a confusing "found multiple
// elements" failure in whichever test happens to run second.
afterEach(cleanup);
