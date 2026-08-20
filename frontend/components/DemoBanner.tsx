"use client";

import { useState } from "react";

import { useResetDemo } from "@/lib/queries";

export function DemoBanner() {
  const resetDemo = useResetDemo();
  const [confirming, setConfirming] = useState(false);

  const handleReset = () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    resetDemo.mutate(undefined, {
      onSuccess: () => {
        setConfirming(false);
      },
    });
  };

  return (
    <div className="demo-banner">
      <span className="demo-banner-text">
        This is a demo. All data is public and resets on reload.
      </span>
      <button
        className="btn btn-secondary demo-banner-btn"
        onClick={handleReset}
        disabled={resetDemo.isPending}
      >
        {resetDemo.isPending
          ? "Resetting..."
          : confirming
            ? "Confirm reset"
            : "Reset demo"}
      </button>
      {confirming && (
        <button
          className="btn btn-quiet demo-banner-btn"
          onClick={() => setConfirming(false)}
        >
          Cancel
        </button>
      )}
    </div>
  );
}
