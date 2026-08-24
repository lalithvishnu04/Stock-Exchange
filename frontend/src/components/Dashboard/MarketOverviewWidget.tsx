import React from 'react';
import { Card, CardContent, Grid, Box, Typography, Chip, Skeleton } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { recommendationsApi } from '../../api/endpoints';

function IndexCard({ label, price, change, changePct, loading }: {
  label: string; price: number; change: number; changePct: number; loading?: boolean;
}) {
  const isUp = changePct >= 0;
  return (
    <Box
      sx={{
        p: 2, borderRadius: 2,
        bgcolor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
        flex: 1, minWidth: 160,
      }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
        {label}
      </Typography>
      {loading ? (
        <Skeleton variant="text" height={34} />
      ) : (
        <Typography variant="h6" fontWeight={700} sx={{ mt: 0.5 }}>
          {price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
      )}
      {!loading && (
        <Typography
          variant="caption"
          sx={{ color: isUp ? 'success.main' : 'error.main', fontWeight: 600 }}
        >
          {isUp ? '▲' : '▼'} {change.toFixed(2)} ({Math.abs(changePct).toFixed(2)}%)
        </Typography>
      )}
    </Box>
  );
}

export default function MarketOverviewWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['market-overview'],
    queryFn: () => recommendationsApi.marketOverview().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const { data: sectors } = useQuery({
    queryKey: ['sector-performance'],
    queryFn: () => recommendationsApi.sectorPerformance().then((r) => r.data),
    refetchInterval: 300_000,
  });

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={700}>Market Overview</Typography>
          <Chip
            size="small"
            label={data?.market_status === 'OPEN' ? '● LIVE' : '● CLOSED'}
            sx={{
              bgcolor: data?.market_status === 'OPEN' ? 'rgba(22,163,74,0.15)' : 'rgba(107,114,128,0.15)',
              color: data?.market_status === 'OPEN' ? 'success.main' : 'grey.500',
              fontWeight: 700,
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <IndexCard label="NIFTY 50" price={data?.nifty50 ?? 0} change={data?.nifty50_change ?? 0} changePct={data?.nifty50_change_pct ?? 0} loading={isLoading} />
          <IndexCard label="BANK NIFTY" price={data?.niftybank ?? 0} change={data?.niftybank_change ?? 0} changePct={data?.niftybank_change_pct ?? 0} loading={isLoading} />
          <IndexCard label="SENSEX" price={data?.sensex ?? 0} change={data?.sensex_change ?? 0} changePct={data?.sensex_change_pct ?? 0} loading={isLoading} />
          <IndexCard label="MIDCAP" price={data?.nifty_midcap ?? 0} change={0} changePct={data?.nifty_midcap_change_pct ?? 0} loading={isLoading} />
        </Box>

        {sectors && sectors.length > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              SECTOR PERFORMANCE
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {sectors.map((s) => (
                <Chip
                  key={s.sector}
                  size="small"
                  label={`${s.sector}  ${s.change_pct >= 0 ? '+' : ''}${s.change_pct.toFixed(2)}%`}
                  sx={{
                    bgcolor: s.change_pct >= 0 ? 'rgba(22,163,74,0.1)' : 'rgba(220,38,38,0.1)',
                    color: s.change_pct >= 0 ? 'success.main' : 'error.main',
                    fontWeight: 600, fontSize: '0.72rem',
                  }}
                />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
