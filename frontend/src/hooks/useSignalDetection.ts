/**
 * Signal detection hook – detects when recommendations change
 * and tracks alerts for new BUY/SELL signals
 */
import { useEffect, useRef, useCallback } from 'react';
import type { Recommendation, TodayRecommendations } from '../types';

interface SignalAlert {
  symbol: string;
  signal: string;
  confidence_score: number;
  price: number;
  reason: string;
  timestamp: number;
}

export const useSignalDetection = (
  recommendations: Recommendation[] | undefined,
  todayRecs: TodayRecommendations | undefined,
) => {
  const previousRecsRef = useRef<Map<string, Recommendation>>(new Map());
  const alertsRef = useRef<SignalAlert[]>([]);
  const hasNewAlertRef = useRef(false);
  const initializedRef = useRef(false);

  const detectNewSignals = useCallback(() => {
    if (!recommendations) return [];

    const newAlerts: SignalAlert[] = [];
    const currentRecs = new Map(recommendations.map(r => [r.stock_symbol, r]));

    recommendations.forEach((rec) => {
      const previousRec = previousRecsRef.current.get(rec.stock_symbol);
      
      // New signal detected
      if (initializedRef.current && previousRec?.signal !== rec.signal) {
        // Only alert for BUY, SELL, or ADD_MORE signals
        if (['BUY', 'SELL', 'ADD_MORE'].includes(rec.signal)) {
          const alert: SignalAlert = {
            symbol: rec.stock_symbol,
            signal: rec.signal,
            confidence_score: rec.confidence_score,
            price: rec.current_price,
            reason: rec.reason || '',
            timestamp: Date.now(),
          };
          
          newAlerts.push(alert);
          hasNewAlertRef.current = true;
          
          // Show browser notification if available
          if ('Notification' in window && Notification.permission === 'granted') {
            const emoji = rec.signal === 'SELL' ? '🔴' : rec.signal === 'BUY' ? '🟢' : '🟡';
            new Notification(`Stock Alert: ${rec.stock_symbol}`, {
              body: `${emoji} ${rec.signal} @ ₹${rec.current_price} (${rec.confidence_score}% confidence)`,
              tag: `stock-${rec.stock_symbol}-${rec.signal}`,
              requireInteraction: rec.signal === 'SELL', // Keep SELL alerts on screen
            });
          }
        }
      }
    });

    // Update previous recommendations map
    previousRecsRef.current = currentRecs;
    initializedRef.current = true;

    // Keep last 20 alerts
    alertsRef.current = [...alertsRef.current, ...newAlerts].slice(-20);

    return newAlerts;
  }, [recommendations]);

  const getRecentAlerts = useCallback(() => {
    return alertsRef.current;
  }, []);

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      void Notification.requestPermission();
    }
    if (recommendations) {
      detectNewSignals();
    }
  }, [recommendations, detectNewSignals]);

  return {
    recentAlerts: getRecentAlerts(),
    hasNewAlert: hasNewAlertRef.current,
    buySignals: recommendations?.filter(r => r.signal === 'BUY') ?? [],
    sellSignals: recommendations?.filter(r => r.signal === 'SELL') ?? [],
    addMoreSignals: recommendations?.filter(r => r.signal === 'ADD_MORE') ?? [],
  };
};
