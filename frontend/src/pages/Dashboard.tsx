import React from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Skeleton,
  Alert, Button, Tooltip, LinearProgress, Stack, Divider, Chip,
  ToggleButtonGroup, ToggleButton, Slider, FormControl, InputLabel, Select, MenuItem,
} from '@mui/material';
import SyncIcon from '@mui/icons-material/Sync';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { portfolioApi, recommendationsApi } from '../api/endpoints';
import RecommendationCard from '../components/Dashboard/RecommendationCard';
import MarketOverviewWidget from '../components/Dashboard/MarketOverviewWidget';
import SectorAllocationChart from '../components/Dashboard/SectorAllocationChart';
import StockAllocationChart from '../components/Dashboard/StockAllocationChart';
import NewsSentimentWidget from '../components/Dashboard/NewsSentimentWidget';
import type { Recommendation, TradeHorizon, RiskLevel } from '../types';

function fmt(n: number, decimals = 2) {
  return n.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function StatCard({
  label, value, subvalue, positive, negative, loading,
}: { label: string; value: string; subvalue?: string; positive?: boolean; negative?: boolean; loading?: boolean }) {
  const color = positive ? 'success.main' : negative ? 'error.main' : 'text.primary';
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
          {label}
        </Typography>
        {loading ? (
          <Skeleton variant="text" height={40} />
        ) : (
          <Typography variant="h5" fontWeight={700} sx={{ color, mt: 0.5 }}>
            {value}
          </Typography>
        )}
        {subvalue && !loading && (
          <Typography variant="caption" sx={{ color }}>{subvalue}</Typography>
        )}
      </CardContent>
    </Card>
  );
}

// Split today's recommendations into labelled groups
function SignalGroup({ title, recs, color }: { title: string; recs: Recommendation[]; color: string }) {
  if (!recs.length) return null;
  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <Box sx={{ width: 4, height: 20, bgcolor: color, borderRadius: 2 }} />
        <Typography variant="h6" fontWeight={700}>{title}</Typography>
        <Chip label={recs.length} size="small" sx={{ bgcolor: color, color: '#fff', fontWeight: 700, height: 20 }} />
      </Box>
      <Grid container spacing={2}>
        {recs.map((r) => (
          <Grid item xs={12} sm={6} lg={4} key={r.id}>
            <RecommendationCard rec={r} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default function DashboardPage() {
  const qc = useQueryClient();
  const [horizonFilter, setHorizonFilter] = React.useState<TradeHorizon | 'ALL'>('ALL');
  const [riskFilter, setRiskFilter] = React.useState<RiskLevel | 'ALL'>('ALL');
  const [minConfidence, setMinConfidence] = React.useState(0);

  const { data: summary, isLoading: summLoading } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: () => portfolioApi.summary().then((r) => r.data),
    refetchInterval: 120_000,
  });

  const { data: today, isLoading: recLoading } = useQuery({
    queryKey: ['today-recommendations', horizonFilter],
    queryFn: () => recommendationsApi.today(horizonFilter === 'ALL' ? undefined : horizonFilter).then((r) => r.data),
    refetchInterval: 300_000,
  });

  const { data: allocations } = useQuery({
    queryKey: ['allocations'],
    queryFn: () => portfolioApi.allocations().then((r) => r.data),
  });

  const syncMutation = useMutation({
    mutationFn: () => portfolioApi.sync(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio-summary'] });
      qc.invalidateQueries({ queryKey: ['allocations'] });
    },
  });

  const totalPnl = summary?.total_pnl ?? 0;
  const dayChg = summary?.total_day_change ?? 0;
  const violations = allocations?.violations ?? [];

  const filterRecs = (recs: Recommendation[] = []) =>
    recs.filter((r) => (riskFilter === 'ALL' || r.risk_level === riskFilter) && r.confidence_score >= minConfidence);

  return (
    <Box>
      {/* Page header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4">Dashboard</Typography>
          <Typography variant="body2" color="text.secondary">
            {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<SyncIcon />}
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending ? 'Syncing...' : 'Sync Portfolio'}
        </Button>
      </Box>

      {syncMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => syncMutation.reset()}>
          Portfolio synced successfully!
        </Alert>
      )}

      {violations.length > 0 && (
        <Alert severity="warning" icon={<WarningAmberIcon />} sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight={600}>Portfolio Rule Violations Detected:</Typography>
          <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
            {violations.map((v, i) => <li key={i}><Typography variant="body2">{v}</Typography></li>)}
          </ul>
        </Alert>
      )}

      {/* Summary stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Portfolio Value"
            value={`₹${fmt(summary?.total_current_value ?? 0, 0)}`}
            loading={summLoading}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Total P&L"
            value={`${totalPnl >= 0 ? '+' : ''}₹${fmt(totalPnl, 0)}`}
            subvalue={`${(summary?.total_pnl_pct ?? 0).toFixed(2)}%`}
            positive={totalPnl >= 0}
            negative={totalPnl < 0}
            loading={summLoading}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Today's Change"
            value={`${dayChg >= 0 ? '+' : ''}₹${fmt(dayChg, 0)}`}
            subvalue={`${(summary?.total_day_change_pct ?? 0).toFixed(2)}%`}
            positive={dayChg >= 0}
            negative={dayChg < 0}
            loading={summLoading}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Holdings"
            value={`${summary?.holdings_count ?? 0}`}
            subvalue={`Total invested ₹${fmt(summary?.total_invested ?? 0, 0)}`}
            loading={summLoading}
          />
        </Grid>
      </Grid>

      {/* Market overview */}
      <Box sx={{ mb: 3 }}>
        <MarketOverviewWidget />
      </Box>

      {/* Today's Recommendations */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
            <Typography variant="h6" fontWeight={700}>
              📊 Today's Recommendations
            </Typography>
            {today?.last_updated && (
              <Typography variant="caption" color="text.secondary">
                Updated {new Date(today.last_updated).toLocaleTimeString('en-IN')}
              </Typography>
            )}
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2, mb: 2 }}>
            <ToggleButtonGroup
              value={horizonFilter}
              exclusive
              size="small"
              onChange={(_, v) => v && setHorizonFilter(v)}
            >
              <ToggleButton value="ALL">All</ToggleButton>
              <ToggleButton value="INTRADAY">Intraday</ToggleButton>
              <ToggleButton value="SWING">Swing</ToggleButton>
              <ToggleButton value="LONGTERM">Long-term</ToggleButton>
            </ToggleButtonGroup>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="risk-filter-label">Risk</InputLabel>
              <Select
                labelId="risk-filter-label"
                label="Risk"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as RiskLevel | 'ALL')}
              >
                <MenuItem value="ALL">All Risk</MenuItem>
                <MenuItem value="LOW">Low</MenuItem>
                <MenuItem value="MEDIUM">Medium</MenuItem>
                <MenuItem value="HIGH">High</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 220 }}>
              <Typography variant="body2" color="text.secondary" whiteSpace="nowrap">
                Min Confidence: {minConfidence}%
              </Typography>
              <Slider
                value={minConfidence}
                onChange={(_, v) => setMinConfidence(v as number)}
                min={0}
                max={90}
                step={10}
                size="small"
                sx={{ width: 120 }}
              />
            </Box>
          </Box>

          {recLoading && <LinearProgress sx={{ mb: 2 }} />}

          {!recLoading && today?.total_count === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                No recommendations yet today. Sync your portfolio to generate analysis.
              </Typography>
            </Box>
          )}

          {today && today.total_count > 0 &&
            filterRecs(today.buy).length + filterRecs(today.add_more).length + filterRecs(today.hold).length
              + filterRecs(today.partial_sell).length + filterRecs(today.sell).length + filterRecs(today.avoid).length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                No recommendations match these filters. Try lowering the confidence threshold or changing risk level.
              </Typography>
            </Box>
          )}

          {today && (
            <>
              <SignalGroup title="BUY TODAY" recs={filterRecs(today.buy)} color="#16a34a" />
              <SignalGroup title="ADD MORE TODAY" recs={filterRecs(today.add_more)} color="#22c55e" />
              <SignalGroup title="HOLD TODAY" recs={filterRecs(today.hold)} color="#2563eb" />
              <SignalGroup title="PARTIAL SELL TODAY" recs={filterRecs(today.partial_sell)} color="#d97706" />
              <SignalGroup title="SELL TODAY" recs={filterRecs(today.sell)} color="#dc2626" />
              <SignalGroup title="AVOID TODAY" recs={filterRecs(today.avoid)} color="#6b7280" />
            </>
          )}
        </CardContent>
      </Card>

      {/* Bottom widgets */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <SectorAllocationChart />
        </Grid>
        <Grid item xs={12} md={6}>
          <StockAllocationChart />
        </Grid>
        <Grid item xs={12}>
          <NewsSentimentWidget />
        </Grid>
      </Grid>
    </Box>
  );
}
