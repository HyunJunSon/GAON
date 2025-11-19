export interface AnalysisHistoryItem {
  conversationId: string;
  title?: string;
  createdAt: string;
  status: 'processing' | 'ready' | 'failed';
  summary?: string;
}

const STORAGE_KEY = 'gaon_analysis_history';
const MAX_HISTORY = 20; // 최대 20개까지 저장

export const analysisHistoryStorage = {
  // 전체 히스토리 조회
  getAll(): AnalysisHistoryItem[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },

  // 특정 분석 조회
  get(conversationId: string): AnalysisHistoryItem | null {
    const history = this.getAll();
    return history.find(item => item.conversationId === conversationId) || null;
  },

  // 분석 추가/업데이트
  save(item: AnalysisHistoryItem): void {
    try {
      let history = this.getAll();
      
      // 기존 항목 업데이트 또는 새 항목 추가
      const existingIndex = history.findIndex(h => h.conversationId === item.conversationId);
      if (existingIndex >= 0) {
        history[existingIndex] = { ...history[existingIndex], ...item };
      } else {
        history.unshift(item); // 최신 항목을 맨 앞에
      }

      // 최대 개수 제한
      if (history.length > MAX_HISTORY) {
        history = history.slice(0, MAX_HISTORY);
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('분석 히스토리 저장 실패:', error);
    }
  },

  // 최근 분석 조회
  getLatest(): AnalysisHistoryItem | null {
    const history = this.getAll();
    return history[0] || null;
  },

  // 특정 분석 삭제
  remove(conversationId: string): void {
    try {
      const history = this.getAll().filter(item => item.conversationId !== conversationId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('분석 히스토리 삭제 실패:', error);
    }
  },

  // 전체 히스토리 삭제
  clear(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('분석 히스토리 초기화 실패:', error);
    }
  }
};
