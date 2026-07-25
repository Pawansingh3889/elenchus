import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UserState {
  currentUserId: string | null;
  setCurrentUserId: (id: string | null) => void;
}

// The acting dev-auth user. Persisted so a reload keeps the selection; the API
// client reads it out of band for the X-User-Id header.
export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      currentUserId: null,
      setCurrentUserId: (id) => set({ currentUserId: id }),
    }),
    { name: "viewops-user" },
  ),
);

interface DraftNoteState {
  pending: Record<string, string>;
  setPendingNote: (templateId: string, note: string) => void;
  clearPendingNote: (templateId: string) => void;
}

// Hands the generation note from the home page to the builder across the navigation
// that opens the fresh draft. Ephemeral (not persisted): the builder reads it once at
// mount and clears it so it doesn't re-seed on a later visit.
export const useDraftNoteStore = create<DraftNoteState>((set) => ({
  pending: {},
  setPendingNote: (templateId, note) =>
    set((s) => ({ pending: { ...s.pending, [templateId]: note } })),
  clearPendingNote: (templateId) =>
    set((s) => {
      if (!(templateId in s.pending)) return s;
      const next = { ...s.pending };
      delete next[templateId];
      return { pending: next };
    }),
}));
