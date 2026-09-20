import axios from 'axios';
import {
  Vocabulary,
  Grammar,
  Source,
  ContentStatus,
  PaginatedResponse,
  VocabularyQueryParams,
  GrammarQueryParams,
  SourceQueryParams,
  ImportResult,
} from '@/types';

const API_BASE_URL =
  process.env.ADMIN_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:7000/api/content';

// Axios Instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 10000,
});

// Fallback Memory Store
let vocabulariesStore: Vocabulary[] = [];
let grammarsStore: Grammar[] = [];
let sourcesStore: Source[] = [];
let isLiveBackendConnected = false;

// Helper to format response into PaginatedResponse structure
function formatPaginatedResponse<T>(
  data: any,
  fallbackList: T[],
  page = 1,
  pageSize = 10
): PaginatedResponse<T> {
  if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
    return {
      count: data.count !== undefined ? data.count : data.results.length,
      next: data.next || null,
      previous: data.previous || null,
      results: data.results as T[],
    };
  }

  // If raw array returned
  if (Array.isArray(data)) {
    const total = data.length;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return {
      count: total,
      next: end < total ? `?page=${page + 1}` : null,
      previous: page > 1 ? `?page=${page - 1}` : null,
      results: data.slice(start, end) as T[],
    };
  }

  // Local fallback
  const total = fallbackList.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  return {
    count: total,
    next: end < total ? `?page=${page + 1}` : null,
    previous: page > 1 ? `?page=${page - 1}` : null,
    results: fallbackList.slice(start, end),
  };
}

export const contentApi = {
  // Check Connection Status
  getBackendConnectionStatus: async (): Promise<{ isConnected: boolean; url: string }> => {
    try {
      await apiClient.get('/sources/');
      isLiveBackendConnected = true;
      return { isConnected: true, url: API_BASE_URL };
    } catch (err) {
      isLiveBackendConnected = false;
      return { isConnected: false, url: API_BASE_URL };
    }
  },

  // ---------------- Sources API ----------------
  getSources: async (params?: SourceQueryParams): Promise<PaginatedResponse<Source>> => {
    const page = params?.page || 1;
    const pageSize = params?.page_size || 10;
    const cleanParams: Record<string, any> = {};
    if (params?.page) cleanParams.page = params.page;
    if (params?.page_size) cleanParams.page_size = params.page_size;
    if (params?.search) cleanParams.search = params.search;

    try {
      const res = await apiClient.get('/sources/', { params: cleanParams });
      isLiveBackendConnected = true;
      if (Array.isArray(res.data)) {
        sourcesStore = res.data;
      } else if (res.data?.results) {
        sourcesStore = res.data.results;
      }
      return formatPaginatedResponse<Source>(res.data, sourcesStore, page, pageSize);
    } catch (err) {
      isLiveBackendConnected = false;
      let filtered = [...sourcesStore];
      if (params?.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(
          (s) => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q)
        );
      }
      return formatPaginatedResponse<Source>(null, filtered, page, pageSize);
    }
  },

  createSource: async (data: Omit<Source, 'id' | 'created_at'>): Promise<Source> => {
    try {
      const res = await apiClient.post<Source>('/sources/', data);
      sourcesStore.unshift(res.data);
      return res.data;
    } catch (err) {
      const newSource: Source = {
        ...data,
        id: `src-${Date.now()}`,
        created_at: new Date().toISOString(),
      };
      sourcesStore.unshift(newSource);
      return newSource;
    }
  },

  updateSource: async (id: string, data: Partial<Source>): Promise<Source> => {
    try {
      const res = await apiClient.patch<Source>(`/sources/${id}/`, data);
      const idx = sourcesStore.findIndex((s) => s.id === id);
      if (idx !== -1) sourcesStore[idx] = res.data;
      return res.data;
    } catch (err) {
      const index = sourcesStore.findIndex((s) => s.id === id);
      if (index === -1) throw new Error('Source not found');
      sourcesStore[index] = { ...sourcesStore[index], ...data };
      return sourcesStore[index];
    }
  },

  deleteSource: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/sources/${id}/`);
    } catch (err) {
      console.warn('Backend delete failed, using local store');
    }
    sourcesStore = sourcesStore.filter((s) => s.id !== id);
  },

  // ---------------- Vocabularies API ----------------
  getVocabularies: async (params?: VocabularyQueryParams): Promise<PaginatedResponse<Vocabulary>> => {
    const page = params?.page || 1;
    const pageSize = params?.page_size || 10;
    const cleanParams: Record<string, any> = {};
    if (params?.page) cleanParams.page = params.page;
    if (params?.page_size) cleanParams.page_size = params.page_size;
    if (params?.search) cleanParams.search = params.search;
    if (params?.level && params.level !== 'ALL') cleanParams.level = params.level;
    if (params?.word_type && params.word_type !== 'ALL') cleanParams.word_type = params.word_type;
    if (params?.status && params.status !== 'ALL') cleanParams.status = params.status;

    try {
      const res = await apiClient.get('/vocabularies/', { params: cleanParams });
      isLiveBackendConnected = true;
      if (Array.isArray(res.data)) {
        vocabulariesStore = res.data;
      } else if (res.data?.results) {
        vocabulariesStore = res.data.results;
      }
      return formatPaginatedResponse<Vocabulary>(res.data, vocabulariesStore, page, pageSize);
    } catch (err) {
      isLiveBackendConnected = false;
      let filtered = [...vocabulariesStore];
      if (params?.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(
          (v) =>
            v.kanji.toLowerCase().includes(q) ||
            v.hiragana.toLowerCase().includes(q) ||
            v.meaning.toLowerCase().includes(q)
        );
      }
      if (params?.level && params.level !== 'ALL') {
        filtered = filtered.filter((v) => v.level === params.level);
      }
      if (params?.word_type && params.word_type !== 'ALL') {
        filtered = filtered.filter((v) => v.word_type === params.word_type);
      }
      if (params?.status && params.status !== 'ALL') {
        filtered = filtered.filter((v) => v.status === params.status);
      }
      return formatPaginatedResponse<Vocabulary>(null, filtered, page, pageSize);
    }
  },

  // Fetch full details of single Vocabulary including forms, synonyms, sources (GET /api/content/vocabularies/{id}/)
  getVocabularyById: async (id: string): Promise<Vocabulary> => {
    try {
      const res = await apiClient.get<Vocabulary>(`/vocabularies/${id}/`);
      return res.data;
    } catch (err) {
      const found = vocabulariesStore.find((v) => v.id === id);
      if (found) return found;
      throw new Error(`Vocabulary ${id} not found`);
    }
  },

  createVocabulary: async (
    data: Omit<Vocabulary, 'id' | 'version' | 'created_at' | 'updated_at'>
  ): Promise<Vocabulary> => {
    if (
      !data.word_type.startsWith('verb') &&
      data.word_type !== 'verb_1' &&
      data.word_type !== 'verb_2' &&
      data.word_type !== 'verb_3' &&
      data.forms &&
      data.forms.length > 0
    ) {
      throw new Error('Chỉ từ loại Động từ mới được tạo verb forms.');
    }

    try {
      const res = await apiClient.post<Vocabulary>('/vocabularies/', data);
      vocabulariesStore.unshift(res.data);
      return res.data;
    } catch (err: any) {
      const newVocab: Vocabulary = {
        ...data,
        id: `voc-${Date.now()}`,
        version: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      vocabulariesStore.unshift(newVocab);
      return newVocab;
    }
  },

  updateVocabulary: async (id: string, data: Partial<Vocabulary>): Promise<Vocabulary> => {
    try {
      const res = await apiClient.patch<Vocabulary>(`/vocabularies/${id}/`, data);
      const idx = vocabulariesStore.findIndex((v) => v.id === id);
      if (idx !== -1) vocabulariesStore[idx] = res.data;
      return res.data;
    } catch (err) {
      const index = vocabulariesStore.findIndex((v) => v.id === id);
      if (index === -1) throw new Error('Vocabulary not found');

      const current = vocabulariesStore[index];
      const newWordType = data.word_type || current.word_type;

      let forms = data.forms !== undefined ? data.forms : current.forms;
      if (!newWordType.startsWith('verb')) {
        forms = [];
      }

      const updated: Vocabulary = {
        ...current,
        ...data,
        forms,
        version: current.version + 1,
        updated_at: new Date().toISOString(),
      };

      vocabulariesStore[index] = updated;
      return updated;
    }
  },

  deleteVocabulary: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/vocabularies/${id}/`);
    } catch (err) {
      console.warn('Backend delete failed, using local store');
    }
    vocabulariesStore = vocabulariesStore.filter((v) => v.id !== id);
  },

  // ---------------- Grammars API ----------------
  getGrammars: async (params?: GrammarQueryParams): Promise<PaginatedResponse<Grammar>> => {
    const page = params?.page || 1;
    const pageSize = params?.page_size || 10;
    const cleanParams: Record<string, any> = {};
    if (params?.page) cleanParams.page = params.page;
    if (params?.page_size) cleanParams.page_size = params.page_size;
    if (params?.search) cleanParams.search = params.search;
    if (params?.level && params.level !== 'ALL') cleanParams.level = params.level;
    if (params?.status && params.status !== 'ALL') cleanParams.status = params.status;

    try {
      const res = await apiClient.get('/grammars/', { params: cleanParams });
      isLiveBackendConnected = true;
      if (Array.isArray(res.data)) {
        grammarsStore = res.data;
      } else if (res.data?.results) {
        grammarsStore = res.data.results;
      }
      return formatPaginatedResponse<Grammar>(res.data, grammarsStore, page, pageSize);
    } catch (err) {
      isLiveBackendConnected = false;
      let filtered = [...grammarsStore];
      if (params?.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(
          (g) => g.pattern.toLowerCase().includes(q) || g.meaning.toLowerCase().includes(q)
        );
      }
      if (params?.level && params.level !== 'ALL') {
        filtered = filtered.filter((g) => g.level === params.level);
      }
      if (params?.status && params.status !== 'ALL') {
        filtered = filtered.filter((g) => g.status === params.status);
      }
      return formatPaginatedResponse<Grammar>(null, filtered, page, pageSize);
    }
  },

  getGrammarById: async (id: string): Promise<Grammar> => {
    try {
      const res = await apiClient.get<Grammar>(`/grammars/${id}/`);
      return res.data;
    } catch (err) {
      const found = grammarsStore.find((g) => g.id === id);
      if (found) return found;
      throw new Error(`Grammar ${id} not found`);
    }
  },

  createGrammar: async (
    data: Omit<Grammar, 'id' | 'version' | 'created_at' | 'updated_at'>
  ): Promise<Grammar> => {
    try {
      const res = await apiClient.post<Grammar>('/grammars/', data);
      grammarsStore.unshift(res.data);
      return res.data;
    } catch (err) {
      const newGrammar: Grammar = {
        ...data,
        id: `gra-${Date.now()}`,
        version: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      grammarsStore.unshift(newGrammar);
      return newGrammar;
    }
  },

  updateGrammar: async (id: string, data: Partial<Grammar>): Promise<Grammar> => {
    try {
      const res = await apiClient.patch<Grammar>(`/grammars/${id}/`, data);
      const idx = grammarsStore.findIndex((g) => g.id === id);
      if (idx !== -1) grammarsStore[idx] = res.data;
      return res.data;
    } catch (err) {
      const index = grammarsStore.findIndex((g) => g.id === id);
      if (index === -1) throw new Error('Grammar not found');

      const current = grammarsStore[index];
      const updated: Grammar = {
        ...current,
        ...data,
        version: current.version + 1,
        updated_at: new Date().toISOString(),
      };

      grammarsStore[index] = updated;
      return updated;
    }
  },

  deleteGrammar: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/grammars/${id}/`);
    } catch (err) {
      console.warn('Backend delete failed, using local store');
    }
    grammarsStore = grammarsStore.filter((g) => g.id !== id);
  },

  // ---------------- Review Queue Helper ----------------
  updateItemStatus: async (
    type: 'vocabulary' | 'grammar',
    id: string,
    status: ContentStatus
  ): Promise<void> => {
    if (type === 'vocabulary') {
      await contentApi.updateVocabulary(id, { status });
    } else {
      await contentApi.updateGrammar(id, { status });
    }
  },

  // ---------------- File Import API ----------------
  importVocabularies: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await apiClient.post<ImportResult>('/vocabularies/import_file/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000,
      });
      return res.data;
    } catch (err: any) {
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          throw new Error(err.response.data);
        }
        throw new Error(err.response.data.error || JSON.stringify(err.response.data));
      }
      throw err;
    }
  },

  importGrammars: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await apiClient.post<ImportResult>('/grammars/import_file/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000,
      });
      return res.data;
    } catch (err: any) {
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          throw new Error(err.response.data);
        }
        throw new Error(err.response.data.error || JSON.stringify(err.response.data));
      }
      throw err;
    }
  },
};

