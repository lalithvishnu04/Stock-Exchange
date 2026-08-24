import React from 'react';
import { Chip } from '@mui/material';
import type { Signal } from '../../types';

const SIGNAL_CONFIG: Record<Signal, { label: string; color: string; bg: string }> = {
  BUY:          { label: 'BUY TODAY',          color: '#fff', bg: '#16a34a' },
  ADD_MORE:     { label: 'ADD MORE TODAY',      color: '#fff', bg: '#22c55e' },
  HOLD:         { label: 'HOLD TODAY',          color: '#fff', bg: '#2563eb' },
  PARTIAL_SELL: { label: 'PARTIAL SELL TODAY',  color: '#fff', bg: '#d97706' },
  SELL:         { label: 'SELL TODAY',          color: '#fff', bg: '#dc2626' },
  AVOID:        { label: 'AVOID TODAY',         color: '#fff', bg: '#6b7280' },
};

interface Props {
  signal: Signal;
  size?: 'small' | 'medium';
}

export default function SignalBadge({ signal, size = 'small' }: Props) {
  const cfg = SIGNAL_CONFIG[signal] ?? { label: signal, color: '#fff', bg: '#374151' };
  return (
    <Chip
      label={cfg.label}
      size={size}
      sx={{
        bgcolor: cfg.bg,
        color: cfg.color,
        fontWeight: 700,
        fontSize: size === 'small' ? '0.7rem' : '0.8rem',
        borderRadius: 1,
      }}
    />
  );
}
