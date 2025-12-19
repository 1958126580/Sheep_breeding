import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserState {
  user: any | null;
  token: string | null;
  setUser: (user: any) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      setUser: (user) => set({ user }),
      setToken: (token) => {
        if (token) localStorage.setItem('access_token', token);
        else localStorage.removeItem('access_token');
        set({ token });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null });
      },
    }),
    { name: 'user-storage' }
  )
);

interface AppState {
  collapsed: boolean;
  theme: 'light' | 'dark';
  toggleCollapsed: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      collapsed: false,
      theme: 'light',
      toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'app-storage' }
  )
);
