import React from 'react';
import {
  Card, CardContent, Box, Typography, Divider, Chip, Tooltip, Stack,
  LinearProgress, IconButton, Collapse,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SignalBadge from '../common/SignalBadge';
import RiskBadge from '../common/RiskBadge';
import type { Recommendation } from '../../types';

function pct(n: number | null | undefined) {
  if (n == null) return null;
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
}

function rup(n: number | null | undefined) {
  if (n == null) return '–';
  return `₹${n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const SIGNAL_BORDER: Record<string, string> = {
  BUY: '#16a34a', ADD_MORE: '#22c55e', HOLD: '#2563eb',
  PARTIAL_SELL: '#d97706', SELL: '#dc2626', AVOID: '#6b7280',
};

const HORIZON_LABEL: Record<string, string> = {
  INTRADAY: 'Intraday', SWING: 'Swing', LONGTERM: 'Long-term',
};

interface Props {
  rec: Recommendation;
}

export default function RecommendationCard({ rec }: Props) {
  const [expanded, setExpanded] = React.useState(false);
  const border = SIGNAL_BORDER[rec.signal] ?? '#374151';
  const hasWarning = !!rec.allocation_warning;

  return (
    <Card
      sx={{
        borderLeft: `4px solid ${border}`,
        height: '100%',
        transition: 'transform 0.15s',
        '&:hover': { transform: 'translateY(-2px)' },
      }}
    >
      <CardContent sx={{ pb: '8px !important' }}>
        {/* Title row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box>
            <Typography variant="subtitle1" fontWeight={700}>{rec.stock_symbol}</Typography>
            <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 160, display: 'block' }}>
              {rec.stock_name}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
            <SignalBadge signal={rec.signal} />
            <RiskBadge level={rec.risk_level} />
          </Box>
        </Box>

        {/* Trade horizon */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
          <Chip label={HORIZON_LABEL[rec.trade_horizon] ?? rec.trade_horizon} size="small" sx={{ fontSize: '0.65rem', height: 20, bgcolor: 'rgba(139,92,246,0.15)', color: '#a78bfa' }} />
        </Box>

        {/* Price row */}
        <Box sx={{ display: 'flex', gap: 2, mb: 1.5, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="caption" color="text.secondary">Price</Typography>
            <Typography variant="body2" fontWeight={600}>{rup(rec.current_price)}</Typography>
          </Box>
          {rec.target_price && (
            <Box>
              <Typography variant="caption" color="text.secondary">Target</Typography>
              <Typography variant="body2" fontWeight={600} color="success.main">{rup(rec.target_price)}</Typography>
            </Box>
          )}
          {rec.stop_loss && (
            <Box>
              <Typography variant="caption" color="text.secondary">Stop Loss</Typography>
              <Typography variant="body2" fontWeight={600} color="error.main">{rup(rec.stop_loss)}</Typography>
            </Box>
          )}
          {rec.upside_potential != null && (
            <Box>
              <Typography variant="caption" color="text.secondary">Upside</Typography>
              <Typography variant="body2" fontWeight={600} color="success.main">
                {pct(rec.upside_potential)}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Confidence */}
        <Box sx={{ mb: 1.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">AI Confidence</Typography>
            <Typography variant="caption" fontWeight={600}>{rec.confidence_score.toFixed(0)}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={rec.confidence_score}
            sx={{
              height: 5, borderRadius: 3,
              bgcolor: 'rgba(255,255,255,0.08)',
              '& .MuiLinearProgress-bar': { bgcolor: border },
            }}
          />
        </Box>

        {/* Sector & portfolio allocation */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
          <Chip label={rec.sector} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 20 }} />
          {rec.portfolio_allocation_pct != null && (
            <Chip
              label={`Portfolio: ${rec.portfolio_allocation_pct.toFixed(1)}%`}
              size="small"
              sx={{
                bgcolor: rec.portfolio_allocation_pct > 10 ? 'rgba(220,38,38,0.15)' : 'rgba(59,130,246,0.1)',
                color: rec.portfolio_allocation_pct > 10 ? 'error.main' : 'text.secondary',
                fontSize: '0.65rem', height: 20,
              }}
            />
          )}
          {rec.sector_allocation_pct != null && (
            <Chip
              label={`Sector: ${rec.sector_allocation_pct.toFixed(1)}%`}
              size="small"
              sx={{
                bgcolor: rec.sector_allocation_pct > 25 ? 'rgba(220,38,38,0.15)' : 'rgba(59,130,246,0.1)',
                color: rec.sector_allocation_pct > 25 ? 'error.main' : 'text.secondary',
                fontSize: '0.65rem', height: 20,
              }}
            />
          )}
        </Box>

        {hasWarning && (
          <Box sx={{ bgcolor: 'rgba(220,38,38,0.1)', borderRadius: 1, p: 0.75, mb: 1 }}>
            <Typography variant="caption" color="error.main">
              ⚠️ {rec.allocation_warning}
            </Typography>
          </Box>
        )}

        {/* Reason */}
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.78rem', lineHeight: 1.5, mb: 1 }}>
          {rec.reason}
        </Typography>

        {/* Expandable detail */}
        <Box
          onClick={() => setExpanded(!expanded)}
          sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 0.5, color: 'text.secondary' }}
        >
          <Typography variant="caption">More details</Typography>
          <ExpandMoreIcon
            fontSize="small"
            sx={{ transition: '0.2s', transform: expanded ? 'rotate(180deg)' : 'none' }}
          />
        </Box>

        <Collapse in={expanded}>
          <Divider sx={{ my: 1 }} />
          {rec.technical_summary && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              📈 <strong>Technical:</strong> {rec.technical_summary}
            </Typography>
          )}
          {rec.fundamental_summary && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              📊 <strong>Fundamental:</strong> {rec.fundamental_summary}
            </Typography>
          )}
          {rec.sentiment_summary && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              📰 <strong>Sentiment:</strong> {rec.sentiment_summary}
            </Typography>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
}
