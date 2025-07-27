import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark';

interface ThemeState {
  theme: Theme;
  isDark: boolean;
}

interface ThemeActions {
  setTheme: (theme: Theme) => void;
  toggle: () => void;
  initializeTheme: () => void;
}

type ThemeStore = ThemeState & ThemeActions;

const applyTheme = (theme: Theme) => {
  const root = document.documentElement;
  
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      // State
      theme: 'light',
      isDark: false,

      // Actions
      setTheme: (theme: Theme) => {
        applyTheme(theme);
        set({
          theme,
          isDark: theme === 'dark',
        });
      },

      toggle: () => {
        const { theme } = get();
        const newTheme = theme === 'light' ? 'dark' : 'light';
        get().setTheme(newTheme);
      },

      initializeTheme: () => {
        const { theme } = get();
        
        // Check system preference if no stored theme
        if (!theme) {
          const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          const initialTheme = systemPrefersDark ? 'dark' : 'light';
          get().setTheme(initialTheme);
        } else {
          applyTheme(theme);
          set({ isDark: theme === 'dark' });
        }
      },
    }),
    {
      name: 'theme-storage',
      partialize: (state) => ({
        theme: state.theme,
      }),
    }
  )
);