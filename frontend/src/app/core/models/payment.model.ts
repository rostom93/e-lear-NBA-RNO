export type TransactionStatus = 'SUCCESS' | 'PENDING' | 'FAILED';

export interface CreditPack {
  id: number;
  name: string;
  credits: number;
  price_euros: string;
  is_active: boolean;
}

export interface Transaction {
  id: number;
  user: number;
  user_email: string;
  pack: number | null;
  pack_name: string | null;
  credits: number;
  amount_euros: string;
  status: TransactionStatus;
  created_at: string;
  updated_at: string;
}

export interface PurchaseResponse {
  transaction: Transaction;
  credit_balance: number;
}
