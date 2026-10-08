export type JLPTLevel = 'N5' | 'N4' | 'N3' | 'N2' | 'N1';

export type ContentStatus = 'upload' | 'review' | 'accepted';

export type WordType = 'noun' | 'verb_1' | 'verb_2' | 'verb_3' | 'adjective';

export type VerbFormType =
  | 'suru'
  | 'masu'
  | 'nai'
  | 'ta'
  | 'te'
  | 'kano'
  | 'ukemi'
  | 'shieki'
  | 'shieki_ukemi'
  | 'meirei'
  | 'ikou'
  | 'kenshi'
  | 'jiouken';

export const VERB_FORM_LABELS: Record<VerbFormType, string> = {
  suru: 'Thể từ điển',
  masu: 'Thể lịch sự (masu)',
  nai: 'Thể phủ định (nai)',
  ta: 'Thể quá khứ (ta)',
  te: 'Thể nối (te)',
  kano: 'Thể khả năng',
  ukemi: 'Thể bị động',
  shieki: 'Thể sai khiến',
  shieki_ukemi: 'Thể sai khiến bị động',
  meirei: 'Thể mệnh lệnh',
  ikou: 'Thể ý chí',
  kenshi: 'Thể cấm đoán',
  jiouken: 'Thể điều kiện',
};

export const WORD_TYPE_LABELS: Record<WordType, string> = {
  noun: 'Danh từ',
  verb_1: 'Động từ nhóm 1',
  verb_2: 'Động từ nhóm 2',
  verb_3: 'Động từ nhóm 3',
  adjective: 'Tính từ',
};

export const STATUS_LABELS: Record<ContentStatus, { label: string; color: string }> = {
  upload: { label: 'Upload', color: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
  review: { label: 'Review', color: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
  accepted: { label: 'Accepted', color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
};

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface VocabularyQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  level?: string;
  word_type?: string;
  status?: string;
}

export interface GrammarQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  level?: string;
  status?: string;
}

export interface SourceQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface Source {
  id: string;
  name: string;
  description: string;
  created_at?: string;
}

export interface VocabularyForm {
  id?: string;
  form_type: VerbFormType;
  value: string;
}

export interface VocabularySynonymDetail {
  id: string;
  kanji: string;
  hiragana: string;
  meaning?: string;
}

export interface Vocabulary {
  id: string;
  kanji: string;
  hiragana: string;
  han_viet: string;
  meaning: string;
  word_type: WordType;
  level: JLPTLevel;
  example: string;
  forms?: VocabularyForm[];
  synonyms?: string[];
  synonyms_detail?: VocabularySynonymDetail[];
  sources?: string[];
  status: ContentStatus;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Grammar {
  id: string;
  pattern: string;
  meaning: string;
  level: JLPTLevel;
  explanation: string;
  example: string;
  sources?: string[];
  status: ContentStatus;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ImportError {
  row: number;
  kanji?: string;
  pattern?: string;
  errors: string[];
}

export interface ImportResult {
  total_rows: number;
  created_count: number;
  error_count: number;
  errors: ImportError[];
}

// ---------------- Auth Types ----------------
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_staff: boolean;
  date_joined?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  access?: string;
  refresh?: string;
}

// ---------------- Study Plan & Learning Types ----------------
export type StudyPlanStatus = 'active' | 'completed' | 'cancelled';

export interface StudyPlan {
  id: string;
  level: JLPTLevel;
  total_days: number;
  start_date: string;
  status: StudyPlanStatus;
  created_at: string;
  updated_at: string;
}

export interface StudyPlanDay {
  id: string;
  day_number: number;
  date: string;
}

export interface SubProgress {
  total: number;
  learned: number;
  remaining: number;
}

export interface StudyPlanDayProgress {
  total: number;
  learned: number;
  remaining: number;
  percentage: number;
  completed: boolean;
  vocabulary: SubProgress;
  grammar: SubProgress;
}

export interface ReviewAvailableSummary {
  available: boolean;
  vocabulary_count: number;
  grammar_count: number;
  total: number;
  reason?: string;
  message?: string;
}

export interface TodayStudyState {
  hasActivePlan: boolean;
  plan?: StudyPlan;
  day?: StudyPlanDay;
  progress?: StudyPlanDayProgress;
  isToday: boolean;
}

// ---------------- Learning Materials Types ----------------
export type MaterialStatusType = 'uploaded' | 'processing' | 'ready' | 'failed';

export interface LearningMaterial {
  id: string;
  title: string;
  description: string;
  material_type: string;
  level: JLPTLevel | string;
  language: string;
  file_size?: number;
  page_count?: number;
  status: MaterialStatusType;
  metadata?: Record<string, unknown>;
  file_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MaterialLesson {
  id: string;
  title: string;
  lesson_number: number;
  description?: string;
  page_start?: number;
  page_end?: number;
  is_completed?: boolean;
  content?: string;
  metadata?: Record<string, unknown>;
  sections_count?: number;
}

export type SectionType =
  | 'text'
  | 'vocabulary'
  | 'grammar'
  | 'dialogue'
  | 'reading'
  | 'exercise'
  | 'explanation'
  | 'note'
  | 'table'
  | 'image'
  | string;

export interface MaterialSection {
  id: string;
  title: string;
  section_type: SectionType;
  order: number;
  page_start?: number;
  page_end?: number;
  content: string;
  data?: Record<string, unknown>;
  vocabulary?: {
    id: string;
    kanji: string;
    hiragana: string;
    meaning: string;
    level: string;
  } | null;
  grammar?: {
    id: string;
    pattern: string;
    meaning: string;
    level: string;
  } | null;
}

export interface UserMaterialLesson {
  id: string;
  lesson_id: string;
  lesson_number: number;
  title: string;
  completed: boolean;
  started_at?: string;
  completed_at?: string | null;
}

export interface UserMaterial {
  id: string;
  material: LearningMaterial;
  status: string;
  progress: number;
  completed_lessons: number;
  total_lessons: number;
  started_at?: string;
  completed_at?: string | null;
}

export interface UserMaterialDetail extends UserMaterial {
  lessons: UserMaterialLesson[];
}

export interface LessonCompletionResult {
  lesson_id: string;
  completed: boolean;
  completed_at: string | null;
  material_progress: number;
  material_status: string;
}

// ---------------- Shadowing Types ----------------
export type ShadowingVideoStatusType = 'uploaded' | 'processing' | 'ready' | 'failed';

export interface ShadowingSegment {
  id: string;
  sequence: number;
  start_time: number;
  end_time: number;
  text: string;
  reading?: string;
  speaker?: string;
  metadata?: Record<string, unknown>;
}

export interface ShadowingVideo {
  id: string;
  title: string;
  description: string;
  level: JLPTLevel | string;
  language: string;
  duration_seconds?: number;
  file_size?: number;
  status: ShadowingVideoStatusType;
  metadata?: Record<string, unknown>;
  video_url?: string | null;
  audio_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserShadowingSegment {
  id: string;
  sequence: number;
  text: string;
  reading?: string;
  speaker?: string;
  start_time: number;
  end_time: number;
  start_seconds: number;
  end_seconds: number;
  is_completed: boolean;
  completed_at?: string | null;
}

export interface UserShadowingVideo {
  id: string;
  video_id: string;
  title: string;
  level: string;
  language: string;
  video?: ShadowingVideo;
  status: string;
  completed_segments: number;
  total_segments: number;
  percentage: number;
  started_at?: string;
  completed_at?: string | null;
}

export interface UserShadowingDetail {
  id: string;
  video: ShadowingVideo;
  status: string;
  progress: {
    completed_segments: number;
    total_segments: number;
    percentage: number;
    completed: boolean;
  };
  segments: UserShadowingSegment[];
  started_at?: string;
  completed_at?: string | null;
}

export interface SegmentCompletionResult {
  segment_id: string;
  completed: boolean;
  completed_at: string | null;
  completed_segments: number;
  total_segments: number;
  percentage: number;
  video_status: string;
}

