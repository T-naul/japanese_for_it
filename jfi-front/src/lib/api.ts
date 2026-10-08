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
  User,
  LoginCredentials,
  AuthResponse,
  StudyPlan,
  StudyPlanDay,
  StudyPlanDayProgress,
  ReviewAvailableSummary,
  TodayStudyState,
  LearningMaterial,
  MaterialLesson,
  MaterialSection,
  UserMaterial,
  UserMaterialDetail,
  LessonCompletionResult,
  ShadowingVideo,
  ShadowingSegment,
  UserShadowingVideo,
  UserShadowingDetail,
  SegmentCompletionResult,
} from '@/types';

export const API_BASE_URL =
  process.env.ADMIN_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  '/api/content';

export const BACKEND_ROOT_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.ADMIN_BASE_URL ? process.env.ADMIN_BASE_URL.replace(/\/api\/content\/?$/, '') : '') ||
  '';

export const AUTH_API_URL = `/api/auth`;

// ---------------- Token & User Storage Helpers ----------------
export const TOKEN_STORAGE_KEY = 'jfi_access_token';
export const REFRESH_STORAGE_KEY = 'jfi_refresh_token';
export const USER_STORAGE_KEY = 'jfi_auth_user';

export const authStorage = {
  getAccessToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  },
  getRefreshToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(REFRESH_STORAGE_KEY);
  },
  setTokens: (access: string, refresh?: string) => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_STORAGE_KEY, access);
    if (refresh) {
      localStorage.setItem(REFRESH_STORAGE_KEY, refresh);
    }
  },
  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    try {
      const data = localStorage.getItem(USER_STORAGE_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },
  setUser: (user: User) => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  },
  clear: () => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(REFRESH_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  },
};

// Axios Instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 10000,
});

// Attach Authorization Bearer token to all apiClient requests
apiClient.interceptors.request.use((config) => {
  const token = authStorage.getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 Unauthorized responses
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest?._retry) {
      originalRequest._retry = true;
      const newToken = await authApi.refreshToken();
      if (newToken && originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

// ---------------- Auth API ----------------
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const res = await axios.post<AuthResponse>(`${AUTH_API_URL}/login/`, credentials, {
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      timeout: 10000,
    });
    if (res.data.access) {
      authStorage.setTokens(res.data.access, res.data.refresh);
    }
    if (res.data.user) {
      authStorage.setUser(res.data.user);
    }
    return res.data;
  },

  getCurrentUser: async (token?: string): Promise<User> => {
    const accessToken = token || authStorage.getAccessToken();
    if (!accessToken) {
      throw new Error('No access token available');
    }
    const res = await axios.get<User>(`${AUTH_API_URL}/me/`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: 'application/json',
      },
      timeout: 10000,
    });
    authStorage.setUser(res.data);
    return res.data;
  },

  logout: async (refreshToken?: string): Promise<void> => {
    const refresh = refreshToken || authStorage.getRefreshToken();
    const token = authStorage.getAccessToken();
    if (refresh && token) {
      try {
        await axios.post(
          `${AUTH_API_URL}/logout/`,
          { refresh },
          {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            timeout: 5000,
          }
        );
      } catch (err) {
        console.warn('Backend logout failed or token already invalid', err);
      }
    }
    authStorage.clear();
  },

  refreshToken: async (): Promise<string | null> => {
    const refresh = authStorage.getRefreshToken();
    if (!refresh) return null;
    try {
      const res = await axios.post<{ access: string }>(
        `${AUTH_API_URL}/refresh/`,
        { refresh },
        { timeout: 5000 }
      );
      if (res.data?.access) {
        authStorage.setTokens(res.data.access);
        return res.data.access;
      }
      return null;
    } catch {
      authStorage.clear();
      return null;
    }
  },
};

// ---------------- Learning & Study Plan API ----------------
export const learningApi = {
  getPlans: async (): Promise<StudyPlan[]> => {
    const token = authStorage.getAccessToken();
    if (!token) return [];
    try {
      const res = await axios.get<StudyPlan[] | { results: StudyPlan[] }>(
        `${BACKEND_ROOT_URL}/api/learning/plans/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      if (Array.isArray(res.data)) return res.data;
      if (res.data && 'results' in res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return [];
    } catch {
      return [];
    }
  },

  getPlanDays: async (planId: string): Promise<StudyPlanDay[]> => {
    const token = authStorage.getAccessToken();
    if (!token) return [];
    try {
      const res = await axios.get<StudyPlanDay[]>(
        `${BACKEND_ROOT_URL}/api/learning/plans/${planId}/days/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      return Array.isArray(res.data) ? res.data : [];
    } catch {
      return [];
    }
  },

  getDayProgress: async (planId: string, dayId: string): Promise<StudyPlanDayProgress> => {
    const token = authStorage.getAccessToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    const res = await axios.get<StudyPlanDayProgress>(
      `${BACKEND_ROOT_URL}/api/learning/plans/${planId}/days/${dayId}/progress/`,
      {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000,
      }
    );
    return res.data;
  },

  getTodayStudyState: async (): Promise<TodayStudyState> => {
    const token = authStorage.getAccessToken();
    if (!token) {
      return { hasActivePlan: false, isToday: false };
    }

    const plans = await learningApi.getPlans();
    const activePlan = plans.find((p) => p.status === 'active') || plans[0];

    if (!activePlan) {
      return { hasActivePlan: false, isToday: false };
    }

    const days = await learningApi.getPlanDays(activePlan.id);
    if (!days || days.length === 0) {
      return { hasActivePlan: true, plan: activePlan, isToday: false };
    }

    // Format local date YYYY-MM-DD
    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

    // Find day for today
    let matchedDay = days.find((d) => d.date === todayStr);
    let isToday = true;

    // If today is not in plan (e.g. before start or after end), pick the first day or last day
    if (!matchedDay) {
      isToday = false;
      if (todayStr < days[0].date) {
        matchedDay = days[0];
      } else {
        matchedDay = days[days.length - 1];
      }
    }

    try {
      const progress = await learningApi.getDayProgress(activePlan.id, matchedDay.id);
      return {
        hasActivePlan: true,
        plan: activePlan,
        day: matchedDay,
        progress,
        isToday,
      };
    } catch {
      return {
        hasActivePlan: true,
        plan: activePlan,
        day: matchedDay,
        isToday,
      };
    }
  },
};

// ---------------- Review API ----------------
export const reviewApi = {
  getAvailableSummary: async (): Promise<ReviewAvailableSummary | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.get<ReviewAvailableSummary>(
        `${BACKEND_ROOT_URL}/api/review/available/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      return res.data;
    } catch {
      return null;
    }
  },
};

// ---------------- Materials API ----------------
export const materialsApi = {
  getMaterials: async (params?: { level?: string; search?: string }): Promise<LearningMaterial[]> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000, params: {} };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    if (params?.level && params.level !== 'ALL') config.params.level = params.level;
    if (params?.search) config.params.search = params.search;

    try {
      const res = await axios.get<LearningMaterial[] | { results: LearningMaterial[] }>(
        `${BACKEND_ROOT_URL}/api/materials/`,
        config
      );
      if (Array.isArray(res.data)) return res.data;
      if (res.data && 'results' in res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return [];
    } catch {
      return [];
    }
  },

  getMaterial: async (id: string): Promise<LearningMaterial | null> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<LearningMaterial>(`${BACKEND_ROOT_URL}/api/materials/${id}/`, config);
      return res.data;
    } catch {
      return null;
    }
  },

  getLessons: async (materialId: string): Promise<MaterialLesson[]> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<MaterialLesson[]>(
        `${BACKEND_ROOT_URL}/api/materials/${materialId}/lessons/`,
        config
      );
      return Array.isArray(res.data) ? res.data : [];
    } catch {
      return [];
    }
  },

  getLessonDetail: async (materialId: string, lessonId: string): Promise<MaterialLesson | null> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<MaterialLesson>(
        `${BACKEND_ROOT_URL}/api/materials/${materialId}/lessons/${lessonId}/`,
        config
      );
      return res.data;
    } catch {
      return null;
    }
  },

  getLessonSections: async (materialId: string, lessonId: string): Promise<MaterialSection[]> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<MaterialSection[]>(
        `${BACKEND_ROOT_URL}/api/materials/${materialId}/lessons/${lessonId}/sections/`,
        config
      );
      return Array.isArray(res.data) ? res.data : [];
    } catch {
      return [];
    }
  },

  enroll: async (materialId: string): Promise<{ enrolled: boolean; material_id: string; status: string } | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.post(
        `${BACKEND_ROOT_URL}/api/materials/${materialId}/enroll/`,
        {},
        { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 }
      );
      return res.data;
    } catch {
      return null;
    }
  },
};

export const userMaterialsApi = {
  getMyMaterials: async (): Promise<UserMaterial[]> => {
    const token = authStorage.getAccessToken();
    if (!token) return [];
    try {
      const res = await axios.get<UserMaterial[] | { results: UserMaterial[] }>(
        `${BACKEND_ROOT_URL}/api/my/materials/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      if (Array.isArray(res.data)) return res.data;
      if (res.data && 'results' in res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return [];
    } catch {
      return [];
    }
  },

  getMyMaterial: async (materialId: string): Promise<UserMaterialDetail | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.get<UserMaterialDetail>(`${BACKEND_ROOT_URL}/api/my/materials/${materialId}/`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000,
      });
      return res.data;
    } catch {
      return null;
    }
  },

  completeLesson: async (materialId: string, lessonId: string): Promise<LessonCompletionResult | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.post<LessonCompletionResult>(
        `${BACKEND_ROOT_URL}/api/my/materials/${materialId}/lessons/${lessonId}/complete/`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      return res.data;
    } catch {
      return null;
    }
  },
};

// ---------------- Shadowing API ----------------
export const shadowingApi = {
  getVideos: async (params?: { level?: string; search?: string }): Promise<ShadowingVideo[]> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000, params: {} };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    if (params?.level && params.level !== 'ALL') config.params.level = params.level;
    if (params?.search) config.params.search = params.search;

    try {
      const res = await axios.get<ShadowingVideo[] | { results: ShadowingVideo[] }>(
        `${BACKEND_ROOT_URL}/api/shadowing/videos/`,
        config
      );
      if (Array.isArray(res.data)) return res.data;
      if (res.data && 'results' in res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return [];
    } catch {
      return [];
    }
  },

  getVideo: async (id: string): Promise<ShadowingVideo | null> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<ShadowingVideo>(`${BACKEND_ROOT_URL}/api/shadowing/videos/${id}/`, config);
      return res.data;
    } catch {
      return null;
    }
  },

  getVideoSegments: async (videoId: string): Promise<ShadowingSegment[]> => {
    const token = authStorage.getAccessToken();
    const config: any = { timeout: 10000 };
    if (token) config.headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get<ShadowingSegment[]>(
        `${BACKEND_ROOT_URL}/api/shadowing/videos/${videoId}/segments/`,
        config
      );
      return Array.isArray(res.data) ? res.data : [];
    } catch {
      return [];
    }
  },

  enroll: async (videoId: string): Promise<{ enrolled: boolean; video_id: string; status: string } | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.post(
        `${BACKEND_ROOT_URL}/api/shadowing/videos/${videoId}/enroll/`,
        {},
        { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 }
      );
      return res.data;
    } catch {
      return null;
    }
  },
};

export const userShadowingApi = {
  getMyShadowing: async (): Promise<UserShadowingVideo[]> => {
    const token = authStorage.getAccessToken();
    if (!token) return [];
    try {
      const res = await axios.get<UserShadowingVideo[] | { results: UserShadowingVideo[] }>(
        `${BACKEND_ROOT_URL}/api/my/shadowing/`,
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      if (Array.isArray(res.data)) return res.data;
      if (res.data && 'results' in res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return [];
    } catch {
      return [];
    }
  },

  getMyShadowingVideo: async (videoId: string): Promise<UserShadowingDetail | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.get<UserShadowingDetail>(`${BACKEND_ROOT_URL}/api/my/shadowing/${videoId}/`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 10000,
      });
      return res.data;
    } catch {
      return null;
    }
  },

  completeSegment: async (videoId: string, segmentId: string): Promise<SegmentCompletionResult | null> => {
    const token = authStorage.getAccessToken();
    if (!token) return null;
    try {
      const res = await axios.post<SegmentCompletionResult>(
        `${BACKEND_ROOT_URL}/api/my/shadowing/${videoId}/segments/${segmentId}/complete/`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 10000,
        }
      );
      return res.data;
    } catch {
      return null;
    }
  },
};

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

let lastConnectionCheckTime = 0;
let lastConnectionStatus = false;

export const contentApi = {
  // Check Connection Status
  getBackendConnectionStatus: async (): Promise<{ isConnected: boolean; url: string }> => {
    const now = Date.now();
    if (now - lastConnectionCheckTime < 30000 && lastConnectionCheckTime > 0) {
      return { isConnected: lastConnectionStatus, url: API_BASE_URL };
    }
    try {
      await apiClient.get('/sources/');
      isLiveBackendConnected = true;
      lastConnectionStatus = true;
      lastConnectionCheckTime = now;
      return { isConnected: true, url: API_BASE_URL };
    } catch (err) {
      isLiveBackendConnected = false;
      lastConnectionStatus = false;
      lastConnectionCheckTime = now;
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

