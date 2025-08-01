export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  UPLOAD: '/upload',
  HISTORY: '/history',
  WALLET: '/wallet',
  ADMIN: '/admin',
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  THEME: 'theme',
  USER: 'user',
} as const;

export const THEME = {
  LIGHT: 'light',
  DARK: 'dark',
} as const;

export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress', 
  DONE: 'done',
  ERROR: 'error',
} as const;

export const TRANSACTION_TYPE = {
  TOP_UP: 'top_up',
  SPEND: 'spend',
} as const;

export const FILE_UPLOAD = {
  MAX_SIZE: 5 * 1024 * 1024, // 5MB
  ACCEPTED_TYPES: ['image/png', 'image/jpeg', 'image/jpg'],
} as const;