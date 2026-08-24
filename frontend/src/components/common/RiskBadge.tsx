import React from 'react';
import { Chip } from '@mui/material';
import type { RiskLevel } from '../../types';

const RISK_CONFIG: Record<RiskLevel, { color: string; bg: string }> = {
  LOW:    { color: '#fff', bg: '#16a34a' },
  MEDIUM: { color: '#fff', bg: '#d97706' },
  HIGH:   { color: '#fff', bg: '#dc2626' },
};

interface Props {
  level: RiskLevel;
  size?: 'small' | 'medium';
}

export default function RiskBadge({ level, size = 'small' }: Props) {
  const cfg = RISK_CONFIG[level] ?? { color: '#fff', bg: '#374151' };
  return (
    <Chip
      label={`${level} RISK`}
      size={size}
      sx={{ bgcolor: cfg.bg, color: cfg.color, fontWeight: 700, fontSize: '0.68rem', borderRadius: 1 }}
    />
  );
}
