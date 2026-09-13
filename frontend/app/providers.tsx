"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { ApiContractError, ApiError } from "@/lib/api";

// A 4xx is an answer, not a blip: retrying it only delays showing the user why.
function retry(failureCount: number, error: Error): boolean {
  // A response in the wrong shape will be the same shape on the next attempt.
  if (error instanceof ApiContractError) return false;
  if (error instanceof ApiError && error.status < 500) return false;
  return failureCount < 2;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false, retry } } }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
