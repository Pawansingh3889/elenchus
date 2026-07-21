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
