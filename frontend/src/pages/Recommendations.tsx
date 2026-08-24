import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, Grid,
  Tabs, Tab, Chip, Alert, CircularProgress,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useQuery, useMutation } from '@tanstack/react-query';
import { recommendationsApi } from '../api/endpoints';
import RecommendationCard from '../components/Dashboard/RecommendationCard';
import SignalBadge from '../components/common/SignalBadge';
import type { Signal } from '../types';

const TABS: { label: string; key: Signal | 'ALL' }[] = [
  { label: 'All', key: 'ALL' },
  { label: 'BUY', key: 'BUY' },
  { label: 'ADD MORE', key: 'ADD_MORE' },
  { label: 'HOLD', key: 'HOLD' },
  { label: 'PARTIAL SELL', key: 'PARTIAL_SELL' },
  { label: 'SELL', key: 'SELL' },
  { label: 'AVOID', key: 'AVOID' },
];

export default function RecommendationsPage() {
  const [tab, setTab] = useState<Signal | 'ALL'>('ALL');
  const [symbol, setSymbol] = useState('');

  const { data: today, isLoading } = useQuery({
    queryKey: ['today-recommendations'],
    queryFn: () => recommendationsApi.today().then((r) => r.data),
  });

  const analyseMutation = useMutation({
    mutationFn: () => recommendationsApi.analyse(symbol.trim().toUpperCase()),
    onSuccess: () => setSymbol(''),
  });

  const allRecs = today
    ? [...today.buy, ...today.add_more, ...today.hold, ...today.partial_sell, ...today.sell, ...today.avoid]
    : [];
  const filtered = tab === 'ALL' ? allRecs : allRecs.filter((r) => r.signal === tab);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Recommendations</Typography>

      {/* On-demand analysis */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Analyse a Stock</Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Stock Symbol (e.g. RELIANCE)"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              size="small"
              sx={{ flexGrow: 1 }}
              onKeyDown={(e) => e.key === 'Enter' && symbol && analyseMutation.mutate()}
            />
            <Button
              variant="contained"
              startIcon={analyseMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <SearchIcon />}
              disabled={!symbol || analyseMutation.isPending}
              onClick={() => analyseMutation.mutate()}
            >
              Analyse
            </Button>
          </Box>

          {analyseMutation.data && (
            <Box sx={{ mt: 2, maxWidth: 400 }}>
              <RecommendationCard rec={analyseMutation.data} />
            </Box>
          )}
          {analyseMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {(analyseMutation.error as any)?.response?.data?.detail || 'Analysis failed'}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Today's grouped by signal */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={700}>Today's Analysis</Typography>
            {today?.last_updated && (
              <Typography variant="caption" color="text.secondary">
                Updated {new Date(today.last_updated).toLocaleTimeString('en-IN')}
              </Typography>
            )}
          </Box>

          <Tabs
            value={tab}
            onChange={(_, v) => setTab(v)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
          >
            {TABS.map((t) => (
              <Tab
                key={t.key}
                label={t.label}
                value={t.key}
                sx={{ fontSize: '0.78rem', minWidth: 80 }}
              />
            ))}
          </Tabs>

          {isLoading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}

          {!isLoading && filtered.length === 0 && (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No {tab === 'ALL' ? '' : tab} recommendations today.
            </Typography>
          )}

          <Grid container spacing={2}>
            {filtered.map((r) => (
              <Grid item xs={12} sm={6} lg={4} key={r.id}>
                <RecommendationCard rec={r} />
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}
