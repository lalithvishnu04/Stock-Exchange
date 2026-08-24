// Core domain types matching the backend models

export type Signal = 'BUY' | 'ADD_MORE' | 'HOLD' | 'PARTIAL_SELL' | 'SELL' | 'AVOID';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type MarketStatus = 'OPEN' | 'CLOSED' | 'PRE_OPEN';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  email_alerts_enabled: boolean;
  telegram_alerts_enabled: boolean;
  has_zerodha_connected: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Holding {
  id: number;
  tradingsymbol: string;
  exchange: string;
  company_name: string;
  sector: string;
  industry: string;
  quantity: number;
  average_price: number;
  last_price: number;
  current_value: number;
  invested_value: number;
  pnl: number;
  pnl_pct: number;
  day_change: number;
  day_change_pct: number;
  portfolio_weight_pct: number;
  last_synced_at: string | null;
}

export interface PortfolioSummary {
  total_invested: number;
  total_current_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  total_day_change: number;
  total_day_change_pct: number;
  holdings_count: number;
  last_synced_at: string | null;
}

export interface SectorAllocation {
  sector: string;
  allocation_pct: number;
  current_value: number;
  is_over_limit: boolean;
  stocks: string[];
}

export interface StockAllocation {
  symbol: string;
  company_name: string;
  allocation_pct: number;
  current_value: number;
  is_over_limit: boolean;
}

export interface AllocationRulesStatus {
  portfolio_summary: PortfolioSummary;
  sector_allocations: SectorAllocation[];
  stock_allocations: StockAllocation[];
  violations: string[];
}

export interface Recommendation {
  id: number;
  stock_symbol: string;
  stock_name: string;
  sector: string;
  exchange: string;
  signal: Signal;
  risk_level: RiskLevel;
  confidence_score: number;
  current_price: number;
  target_price: number | null;
  stop_loss: number | null;
  upside_potential: number | null;
  reason: string;
  technical_summary: string | null;
  fundamental_summary: string | null;
  sentiment_summary: string | null;
  portfolio_allocation_pct: number | null;
  sector_allocation_pct: number | null;
  allocation_warning: string | null;
  created_at: string;
}

export interface TodayRecommendations {
  date: string;
  buy: Recommendation[];
  add_more: Recommendation[];
  hold: Recommendation[];
  partial_sell: Recommendation[];
  sell: Recommendation[];
  avoid: Recommendation[];
  total_count: number;
  last_updated: string | null;
}

export interface MarketOverview {
  nifty50: number;
  nifty50_change: number;
  nifty50_change_pct: number;
  niftybank: number;
  niftybank_change: number;
  niftybank_change_pct: number;
  sensex: number;
  sensex_change: number;
  sensex_change_pct: number;
  nifty_midcap: number;
  nifty_midcap_change_pct: number;
  market_status: MarketStatus;
  as_of: string;
}

export interface SectorPerformance {
  sector: string;
  change_pct: number;
  sentiment: string;
}

export interface NewsItem {
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  sentiment_score: number;
  stock_symbols: string[];
  summary: string;
}

export interface AlertLog {
  id: number;
  alert_type: string;
  subject: string;
  message: string;
  stock_symbol: string | null;
  signal: string | null;
  is_sent: boolean;
  created_at: string;
}
