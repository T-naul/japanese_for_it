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
  | 'imperative'
  | 'ikou'
  | 'kenshi'
  | 'jiouken';

export const VERB_FORM_LABELS: Record<VerbFormType, string> = {
  suru: '辞書 (Thể nguyên thể / Từ điển)',
  masu: 'ます形 (Thể Masu / Lịch sự)',
  nai: 'ない形 (Thể Nai / Phủ định)',
  ta: 'た形 (Thể Ta / Quá khứ)',
  te: 'て形 (Thể Te)',
  kano: '可能形 (Thể khả năng)',
  ukemi: '受身形 (Thể bị động)',
  shieki: '使役形 (Thể sai khiến)',
  shieki_ukemi: '使役受身形 (Thể sai khiến bị động)',
  imperative: '命令形 (Thể mệnh lệnh)',
  ikou: '意向形 (Thể ý hướng)',
  kenshi: '禁止形 (Thể cấm chỉ)',
  jiouken: '条件形 (Thể điều kiện)',
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

