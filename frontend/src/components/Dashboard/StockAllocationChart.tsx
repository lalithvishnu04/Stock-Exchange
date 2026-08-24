import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Tooltip, LinearProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { portfolioApi } from '../../api/endpoints';

export default function StockAllocationChart() {
  const { data } = useQuery({
    queryKey: ['allocations'],
    queryFn: () => portfolioApi.allocations().then((r) => r.data),
  });

  const stocks = data?.stock_allocations ?? [];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={700}>Stock Allocation</Typography>
          <Tooltip title="Max 10% per stock rule">
            <Chip label="MAX 10% RULE" size="small" sx={{ bgcolor: 'rgba(59,130,246,0.1)', color: 'primary.main', fontWeight: 600, fontSize: '0.65rem' }} />
          </Tooltip>
        </Box>

        {stocks.length === 0 ? (
          <Typography color="text.secondary" variant="body2" sx={{ textAlign: 'center', py: 4 }}>
            No holdings data. Sync your portfolio.
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, maxHeight: 320, overflow: 'auto' }}>
            {stocks.map((s) => (
              <Box key={s.symbol}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" fontWeight={600}>
                    {s.symbol}
                    {s.is_over_limit && (
                      <Chip label="OVER LIMIT" size="small" sx={{ ml: 1, bgcolor: 'rgba(220,38,38,0.15)', color: 'error.main', fontSize: '0.6rem', height: 16 }} />
                    )}
                  </Typography>
                  <Typography
                    variant="body2"
                    fontWeight={700}
                    sx={{ color: s.is_over_limit ? 'error.main' : s.allocation_pct > 8 ? 'warning.main' : 'text.primary' }}
                  >
                    {s.allocation_pct.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(s.allocation_pct, 100)}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: 'rgba(255,255,255,0.06)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: s.is_over_limit ? '#dc2626' : s.allocation_pct > 8 ? '#d97706' : '#3b82f6',
                      borderRadius: 3,
                    },
                  }}
                />
                {/* 10% marker */}
                <Box sx={{ position: 'relative', height: 4 }}>
                  <Box sx={{ position: 'absolute', left: '10%', top: 0, width: 1, height: 8, bgcolor: 'rgba(220,38,38,0.5)', mt: '-6px' }} />
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
