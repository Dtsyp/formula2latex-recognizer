// API Types
export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export interface UserRegister {
  email: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Wallet {
  id: string;
  balance: number;
  owner_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Transaction {
  id: string;
  type: 'top_up' | 'spend';
  amount: number;
  post_balance: number;
  created_at: string;
}

export interface MLModel {
  id: string;
  name: string;
  credit_cost: number;
  is_active: boolean;
}

export interface Task {
  id: string;
  status: 'pending' | 'in_progress' | 'done' | 'error';
  credits_charged: number;
  output_data?: string;
  error_message?: string;
  created_at: string;
}

export interface PredictionRequest {
  model_id: string;
  file_content: string;
  filename: string;
}

export interface TopUpRequest {
  amount: number;
}

// UI Types
export interface AppState {
  user: User | null;
  wallet: Wallet | null;
  models: MLModel[];
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
}

export interface Theme {
  isDark: boolean;
}

export type UserRole = 'user' | 'admin';