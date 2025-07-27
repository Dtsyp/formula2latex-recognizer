import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Wallet } from '../types';

interface AuthState {
  user: User | null;
  wallet: Wallet | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  setWallet: (wallet: Wallet) => void;
  setToken: (token: string) => void;
  clearAuth: () => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // State
      user: null,
      wallet: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const { authAPI } = await import('../services/api');
          const { user, wallet, token } = await authAPI.login({ email, password });

          set({
            user,
            wallet,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const { authAPI } = await import('../services/api');
          const { user, wallet, token } = await authAPI.register({ email, password });

          set({
            user,
            wallet,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          wallet: null,
          token: null,
          isAuthenticated: false,
        });
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      setWallet: (wallet: Wallet) => {
        set({ wallet });
      },

      setToken: (token: string) => {
        set({ token });
      },

      clearAuth: () => {
        set({
          user: null,
          wallet: null,
          token: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        wallet: state.wallet,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);