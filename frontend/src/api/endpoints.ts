import { apiClient } from './client';
import type {
  TokenResponse, User, Holding, PortfolioSummary, AllocationRulesStatus,
  TodayRecommendations, Recommendation, MarketOverview, SectorPerformance,
  NewsItem, AlertLog,
} from '../types';

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post<TokenResponse>('/auth/login', { username, password }),
  register: (data: { username: string; email: string; password: string; full_name?: string }) =>
    apiClient.post<User>('/auth/register', data),
  me: () => apiClient.get<User>('/auth/me'),
  updateSettings: (data: Partial<User>) =>
    apiClient.put<User>('/auth/settings', data),
};

// ── Portfolio ─────────────────────────────────────────────────────────────────
export const portfolioApi = {
  addHolding: (data: { tradingsymbol: string; exchange: string; quantity: number; average_price: number }) =>
    apiClient.post<Holding>('/portfolio/holdings', data),
  updateHolding: (id: number, data: { quantity?: number; average_price?: number }) =>
    apiClient.put<Holding>(`/portfolio/holdings/${id}`, data),
  deleteHolding: (id: number) => apiClient.delete(`/portfolio/holdings/${id}`),
  refreshPrices: () => apiClient.post('/portfolio/refresh-prices'),
  holdings: () => apiClient.get<Holding[]>('/portfolio/holdings'),
  summary: () => apiClient.get<PortfolioSummary>('/portfolio/summary'),
  allocations: () => apiClient.get<AllocationRulesStatus>('/portfolio/allocations'),
  alerts: (limit = 50) => apiClient.get<AlertLog[]>(`/portfolio/alerts?limit=${limit}`),
  reports: (limit = 30) => apiClient.get<any[]>(`/portfolio/reports?limit=${limit}`),
  reportContent: (id: number) => apiClient.get<string>(`/portfolio/reports/${id}`),
};

// ── Recommendations ───────────────────────────────────────────────────────────
export const recommendationsApi = {
  today: () => apiClient.get<TodayRecommendations>('/recommendations/today'),
  history: (limit = 100, symbol?: string) =>
    apiClient.get<Recommendation[]>(`/recommendations/history?limit=${limit}${symbol ? `&symbol=${symbol}` : ''}`),
  analyse: (symbol: string, exchange = 'NSE') =>
    apiClient.post<Recommendation>('/recommendations/analyse', { symbol, exchange }),
  analyseAll: () =>
    apiClient.post<{ analysed: number; recommendations: Recommendation[] }>('/recommendations/analyse-all'),
  marketPicks: () =>
    apiClient.get<Recommendation[]>('/recommendations/market-picks'),
  marketOverview: () => apiClient.get<MarketOverview>('/recommendations/market-overview'),
  sectorPerformance: () => apiClient.get<SectorPerformance[]>('/recommendations/sector-performance'),
  news: (symbol?: string) =>
    apiClient.get<NewsItem[]>(`/recommendations/news${symbol ? `?symbol=${symbol}` : ''}`),
};
