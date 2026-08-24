import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Tooltip } from '@mui/material';
import { PieChart, Pie, Cell, Tooltip as RTooltip, Legend, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { portfolioApi } from '../../api/endpoints';

const COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#84cc16'];

export default function SectorAllocationChart() {
  const { data } = useQuery({
    queryKey: ['allocations'],
    queryFn: () => portfolioApi.allocations().then((r) => r.data),
  });

  const sectors = data?.sector_allocations ?? [];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6" fontWeight={700}>Sector Allocation</Typography>
          <Tooltip title="Max 25% per sector rule">
            <Chip label="MAX 25% RULE" size="small" sx={{ bgcolor: 'rgba(59,130,246,0.1)', color: 'primary.main', fontWeight: 600, fontSize: '0.65rem' }} />
          </Tooltip>
        </Box>

        {sectors.length === 0 ? (
          <Typography color="text.secondary" variant="body2" sx={{ textAlign: 'center', py: 4 }}>
            No holdings data. Sync your portfolio.
          </Typography>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={sectors} dataKey="allocation_pct" nameKey="sector" cx="50%" cy="50%" outerRadius={85} label={({ sector, allocation_pct }) => `${sector}: ${allocation_pct.toFixed(1)}%`} labelLine={false}>
                  {sectors.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <RTooltip formatter={(v: number) => `${v.toFixed(2)}%`} contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)' }} />
              </PieChart>
            </ResponsiveContainer>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mt: 1 }}>
              {sectors.map((s, i) => (
                <Chip
                  key={s.sector}
                  label={`${s.sector}  ${s.allocation_pct.toFixed(1)}%`}
                  size="small"
                  sx={{
                    bgcolor: s.is_over_limit ? 'rgba(220,38,38,0.15)' : `${COLORS[i % COLORS.length]}22`,
                    color: s.is_over_limit ? 'error.main' : 'text.primary',
                    border: s.is_over_limit ? '1px solid rgba(220,38,38,0.4)' : 'none',
                    fontSize: '0.68rem',
                  }}
                />
              ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
}
