/**
 * Auto-analysis hook – automatically triggers analysis every 5 minutes
 * during market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
 */
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { recommendationsApi } from '../api/endpoints';

interface UseAutoAnalysisOptions {
  enabled?: boolean;
  intervalMinutes?: number;
}

// Market hours: 9:15 AM - 3:30 PM IST (Mon-Fri)
const isMarketOpen = (): boolean => {
  const now = new Date();
  const istTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const day = istTime.getDay();
  const hour = istTime.getHours();
  const minute = istTime.getMinutes();
  
  // Check if weekday (Mon-Fri = 1-5)
  if (day === 0 || day === 6) return false;
  
  // Check time: 9:15 AM to 3:30 PM (15:30)
  const timeInMinutes = hour * 60 + minute;
  const marketOpen = 9 * 60 + 15;  // 9:15 AM
  const marketClose = 15 * 60 + 30; // 3:30 PM
  
  return timeInMinutes >= marketOpen && timeInMinutes <= marketClose;
};

// Get minutes until market close
const getMinutesUntilClose = (): number => {
  const now = new Date();
  const istTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const hour = istTime.getHours();
  const minute = istTime.getMinutes();
  
  const timeInMinutes = hour * 60 + minute;
  const marketClose = 15 * 60 + 30; // 3:30 PM
  
  return Math.max(0, marketClose - timeInMinutes);
};

export const useAutoAnalysis = (options: UseAutoAnalysisOptions = {}) => {
  const { enabled = true, intervalMinutes = 5 } = options;
  const queryClient = useQueryClient();
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastPollRef = useRef<number>(0);

  const triggerAnalysis = useCallback(async () => {
    if (!isMarketOpen()) {
      console.log('Market is closed, skipping auto-analysis');
      return;
    }

    const now = Date.now();
    const timeSinceLastPoll = now - lastPollRef.current;
    
    // Prevent duplicate polls within 30 seconds
    if (timeSinceLastPoll < 30000) {
      return;
    }

    console.log(`[Auto-Analysis] Triggering analysis at ${new Date().toLocaleTimeString('en-US', { timeZone: 'Asia/Kolkata' })}`);
    
    try {
      // Trigger analysis for all holdings
      await recommendationsApi.analyseAll();
      lastPollRef.current = now;
      
      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['today-recommendations'] });
      queryClient.invalidateQueries({ queryKey: ['market-picks'] });
    } catch (error) {
      console.error('Auto-analysis failed:', error);
    }
  }, [queryClient]);

  useEffect(() => {
    if (!enabled) return;

    // Initial analysis if market is open
    if (isMarketOpen()) {
      triggerAnalysis();
    }

    // Set up polling interval
    pollIntervalRef.current = setInterval(() => {
      if (isMarketOpen()) {
        triggerAnalysis();
      } else {
        console.log('Market closed, auto-analysis stopped');
        // Clear interval when market closes
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    }, intervalMinutes * 60 * 1000);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [enabled, intervalMinutes, triggerAnalysis]);

  return {
    isMarketOpen: isMarketOpen(),
    minutesUntilClose: getMinutesUntilClose(),
    triggerAnalysisNow: triggerAnalysis,
  };
};
