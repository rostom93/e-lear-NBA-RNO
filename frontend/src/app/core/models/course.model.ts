export type CourseLevel = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
export type ContentFocus = 'MIXED' | 'VIDEO' | 'PDF' | 'QUIZ';
export type ModuleType = 'PDF' | 'VIDEO' | 'QUIZ';
export type VideoProvider = 'YOUTUBE' | 'VIMEO' | 'OTHER' | '';

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface QuizChoice {
  id: number;
  text: string;
}

export interface QuizQuestion {
  id: number;
  text: string;
  order: number;
  choices: QuizChoice[];
}

export interface Quiz {
  id: number;
  title: string;
  passing_score: number;
  questions: QuizQuestion[];
}

export interface Module {
  id: number;
  title: string;
  order: number;
  module_type: ModuleType;
  pdf_url: string;
  video_url: string;
  video_provider: VideoProvider;
  captions_url: string;
  transcript: string;
  quiz: Quiz | null;
}

export interface Course {
  id: number;
  title: string;
  slug: string;
  description: string;
  teacher: number;
  teacher_email: string;
  price_credits: number;
  level: CourseLevel;
  category: string;
  content_focus: ContentFocus;
  tags: Tag[];
  is_active: boolean;
  modules_count: number;
  created_at: string;
  updated_at?: string;
  modules?: Module[];
}

export interface Enrollment {
  id: number;
  student: number;
  student_email: string;
  course: Course;
  credits_spent: number;
  progress_percent: number;
  enrolled_at: string;
}

export interface QuizAttempt {
  id: number;
  quiz: number;
  score: number;
  passed: boolean;
  answers: Record<string, number>;
  created_at: string;
}

export interface CourseFilters {
  tags?: string;
  category?: string;
  level?: string;
  content_focus?: string;
  mine?: boolean;
}

export interface ModuleWritePayload {
  title: string;
  order: number;
  module_type: ModuleType;
  pdf_url?: string;
  video_url?: string;
  video_provider?: VideoProvider;
  captions_url?: string;
  transcript?: string;
  quiz?: number | null;
}

export interface CourseWritePayload {
  title: string;
  description: string;
  price_credits: number;
  level: CourseLevel;
  category: string;
  content_focus: ContentFocus;
  tag_ids?: number[];
  is_active?: boolean;
  modules?: ModuleWritePayload[];
}

export interface StudentProgress {
  id: number;
  student: number;
  student_email: string;
  student_name: string;
  progress_percent: number;
  enrolled_at: string;
  quiz_attempts: QuizAttempt[];
}

export interface BulkEmailPayload {
  student_ids: number[];
  subject: string;
  message: string;
  include_progress?: boolean;
}

export interface QuizWritePayload {
  title: string;
  passing_score: number;
  questions: Array<{
    text: string;
    order: number;
    choices: Array<{ text: string; is_correct: boolean }>;
  }>;
}
