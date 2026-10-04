export interface AdminStats {
  users: {
    total: number;
    students: number;
    teachers: number;
  };
  payments: {
    successful_transactions: number;
    credits_sold: number;
    revenue_euros: string;
  };
  popular_courses: Array<{
    id: number;
    title: string;
    enroll_count: number;
  }>;
  average_completion_percent: number;
}

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  credit_balance: number;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
}

export interface AdminUserWrite {
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  credit_balance?: number;
  is_active?: boolean;
  is_staff?: boolean;
  password?: string;
}
