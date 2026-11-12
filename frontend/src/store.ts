import { create } from "zustand";
import { persist } from "zustand/middleware";
type S = { token: string | null; refreshToken: string | null; role: string | null; dark: boolean; toast: string;
  login: (t: string | null, r: string | null, refresh?: string | null) => void; toggle: () => void; say: (m: string) => void };
export const useStore = create<S>()(persist((set) => ({
  token: null, refreshToken: null, role: null, dark: true, toast: "",
  login: (token, role, refreshToken = null) => set({ token, role, refreshToken }),
  toggle: () => set(s => ({ dark: !s.dark })),
  say: (m) => { set({ toast: m }); setTimeout(() => set({ toast: "" }), 3200); }
}), { name: "sf", partialize: s => ({ token: s.token, refreshToken: s.refreshToken, role: s.role, dark: s.dark }) }));
