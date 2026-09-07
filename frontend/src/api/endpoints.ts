import { apiClient } from './client';
import type {
  TokenResponse, User, Holding, PortfolioSummary, AllocationRulesStatus,
  TodayRecommendations, Recommendation, MarketOverview, SectorPerformance,
  NewsItem, AlertLog, TradeHorizon,
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
  zerodhaLoginUrl: () => apiClient.get<{ login_url: string }>('/auth/zerodha/login-url'),
  zerodhaConnect: (request_token: string) =>
    apiClient.post<{ message: string; user: string | null }>('/auth/zerodha/connect', { request_token }),
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
  sync: () => apiClient.get<{ message: string; count: number }>('/portfolio/sync'),
  alerts: (limit = 50) => apiClient.get<AlertLog[]>(`/portfolio/alerts?limit=${limit}`),
  reports: (limit = 30) => apiClient.get<any[]>(`/portfolio/reports?limit=${limit}`),
  reportContent: (id: number) => apiClient.get<string>(`/portfolio/reports/${id}`),
};

// ── Recommendations ───────────────────────────────────────────────────────────
export const recommendationsApi = {
  today: (horizon?: TradeHorizon) =>
    apiClient.get<TodayRecommendations>(`/recommendations/today${horizon ? `?horizon=${horizon}` : ''}`),
  history: (limit = 100, symbol?: string) =>
    apiClient.get<Recommendation[]>(`/recommendations/history?limit=${limit}${symbol ? `&symbol=${symbol}` : ''}`),
  analyse: (symbol: string, exchange = 'NSE', horizon: TradeHorizon = 'SWING') =>
    apiClient.post<Recommendation>('/recommendations/analyse', { symbol, exchange, horizon }),
  analyseAll: (horizon: TradeHorizon = 'SWING') =>
    apiClient.post<{ analysed: number; recommendations: Recommendation[] }>(`/recommendations/analyse-all?horizon=${horizon}`),
  marketPicks: (horizon: TradeHorizon = 'SWING') =>
    apiClient.get<Recommendation[]>(`/recommendations/market-picks?horizon=${horizon}`),
  scanMarket: (horizon: TradeHorizon = 'SWING') =>
    apiClient.post<{ message: string }>(`/recommendations/market-picks/scan?horizon=${horizon}`),
  marketOverview: () => apiClient.get<MarketOverview>('/recommendations/market-overview'),
  sectorPerformance: () => apiClient.get<SectorPerformance[]>('/recommendations/sector-performance'),
  news: (symbol?: string) =>
    apiClient.get<NewsItem[]>(`/recommendations/news${symbol ? `?symbol=${symbol}` : ''}`),
  // Watchlist endpoints
  getWatchlist: () => apiClient.get<any[]>('/recommendations/watchlist'),
  addToWatchlist: (data: any) => apiClient.post('/recommendations/watchlist', data),
  removeFromWatchlist: (id: number) => apiClient.delete(`/recommendations/watchlist/${id}`),
  markAsBought: (id: number) => apiClient.put(`/recommendations/watchlist/${id}/mark-bought`, {}),
};
