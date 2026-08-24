import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, Chip,
  Table, TableHead, TableRow, TableCell, TableBody, TableContainer,
  Button, Alert, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, IconButton, Tooltip, CircularProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { portfolioApi } from '../api/endpoints';
import type { Holding } from '../types';

function fmt(n: number, d = 2) {
  return Number(n).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
}

const EXCHANGES = ['NSE', 'BSE'];

interface HoldingFormState {
  tradingsymbol: string;
  exchange: string;
  quantity: string;
  average_price: string;
}

const EMPTY_FORM: HoldingFormState = { tradingsymbol: '', exchange: 'NSE', quantity: '', average_price: '' };

export default function PortfolioPage() {
  const qc = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [editHolding, setEditHolding] = useState<Holding | null>(null);
  const [form, setForm] = useState<HoldingFormState>(EMPTY_FORM);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [apiError, setApiError] = useState('');

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['holdings'] });
    qc.invalidateQueries({ queryKey: ['portfolio-summary'] });
    qc.invalidateQueries({ queryKey: ['allocations'] });
  };

  const { data: holdings } = useQuery({
    queryKey: ['holdings'],
    queryFn: () => portfolioApi.holdings().then((r) => r.data),
  });

  const { data: summary } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: () => portfolioApi.summary().then((r) => r.data),
  });

  const { data: allocations } = useQuery({
    queryKey: ['allocations'],
    queryFn: () => portfolioApi.allocations().then((r) => r.data),
  });

  const addMutation = useMutation({
    mutationFn: () => portfolioApi.addHolding({
      tradingsymbol: form.tradingsymbol.trim().toUpperCase(),
      exchange: form.exchange,
      quantity: parseInt(form.quantity),
      average_price: parseFloat(form.average_price),
    }),
    onSuccess: () => { invalidate(); setAddOpen(false); setForm(EMPTY_FORM); setApiError(''); },
    onError: (e: any) => setApiError(e.response?.data?.detail || 'Failed to add stock'),
  });

  const editMutation = useMutation({
    mutationFn: () => portfolioApi.updateHolding(editHolding!.id, {
      quantity: parseInt(form.quantity),
      average_price: parseFloat(form.average_price),
    }),
    onSuccess: () => { invalidate(); setEditHolding(null); setForm(EMPTY_FORM); setApiError(''); },
    onError: (e: any) => setApiError(e.response?.data?.detail || 'Failed to update'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => portfolioApi.deleteHolding(id),
    onSuccess: () => { invalidate(); setDeleteId(null); },
  });

  const refreshMutation = useMutation({
    mutationFn: () => portfolioApi.refreshPrices(),
    onSuccess: () => invalidate(),
  });

  const openEdit = (h: Holding) => {
    setEditHolding(h);
    setForm({ tradingsymbol: h.tradingsymbol, exchange: h.exchange, quantity: String(h.quantity), average_price: String(h.average_price) });
    setApiError('');
  };

  const violations = allocations?.violations ?? [];
  const totalPnl = Number(summary?.total_pnl ?? 0);
  const dayChg = Number(summary?.total_day_change ?? 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Box>
          <Typography variant="h4">My Portfolio</Typography>
          <Typography variant="body2" color="text.secondary">
            Add your Zerodha holdings here. Prices auto-refresh from Yahoo Finance (free).
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={refreshMutation.isPending ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            Refresh Prices
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setAddOpen(true); setForm(EMPTY_FORM); setApiError(''); }}>
            Add Stock
          </Button>
        </Box>
      </Box>

      {refreshMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => refreshMutation.reset()}>
          Prices refreshed from Yahoo Finance ✓
        </Alert>
      )}

      {violations.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Portfolio Rule Violations:</strong>
          <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
            {violations.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </Alert>
      )}

      {(!holdings || holdings.length === 0) && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No stocks added yet. Click <strong>"Add Stock"</strong> and enter your Zerodha holdings manually.
          You only need to do this once — prices update automatically every day.
        </Alert>
      )}

      {/* Summary cards */}
      {summary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { l: 'Invested', v: `₹${fmt(summary.total_invested, 0)}` },
            { l: 'Current Value', v: `₹${fmt(summary.total_current_value, 0)}` },
            { l: 'Total P&L', v: `${totalPnl >= 0 ? '+' : ''}₹${fmt(totalPnl, 0)}`, c: totalPnl >= 0 ? 'success.main' : 'error.main' },
            { l: 'P&L %', v: `${Number(summary.total_pnl_pct) >= 0 ? '+' : ''}${fmt(summary.total_pnl_pct)}%`, c: Number(summary.total_pnl_pct) >= 0 ? 'success.main' : 'error.main' },
            { l: "Today's Change", v: `${dayChg >= 0 ? '+' : ''}₹${fmt(dayChg, 0)}`, c: dayChg >= 0 ? 'success.main' : 'error.main' },
          ].map((item) => (
            <Grid item xs={6} sm={4} md={2.4} key={item.l}>
              <Card>
                <CardContent sx={{ pb: '12px !important' }}>
                  <Typography variant="caption" color="text.secondary">{item.l}</Typography>
                  <Typography variant="h6" fontWeight={700} sx={{ color: item.c || 'text.primary' }}>{item.v}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Holdings table */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Holdings</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {['Stock', 'Sector', 'Qty', 'Avg Price', 'LTP', 'Invested', 'Current', 'P&L', 'P&L %', 'Day Chg%', 'Weight%', ''].map((h) => (
                    <TableCell key={h} sx={{ fontWeight: 700, fontSize: '0.75rem', whiteSpace: 'nowrap' }}>{h}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {(holdings ?? []).map((h) => (
                  <TableRow key={h.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={700}>{h.tradingsymbol}</Typography>
                      <Typography variant="caption" color="text.secondary">{h.exchange}</Typography>
                    </TableCell>
                    <TableCell><Chip label={h.sector} size="small" sx={{ fontSize: '0.65rem' }} /></TableCell>
                    <TableCell>{h.quantity}</TableCell>
                    <TableCell>₹{fmt(h.average_price)}</TableCell>
                    <TableCell>₹{fmt(h.last_price)}</TableCell>
                    <TableCell>₹{fmt(h.invested_value, 0)}</TableCell>
                    <TableCell>₹{fmt(h.current_value, 0)}</TableCell>
                    <TableCell sx={{ color: Number(h.pnl) >= 0 ? 'success.main' : 'error.main', fontWeight: 600 }}>
                      {Number(h.pnl) >= 0 ? '+' : ''}₹{fmt(h.pnl, 0)}
                    </TableCell>
                    <TableCell sx={{ color: Number(h.pnl_pct) >= 0 ? 'success.main' : 'error.main', fontWeight: 600 }}>
                      {Number(h.pnl_pct) >= 0 ? '+' : ''}{fmt(h.pnl_pct)}%
                    </TableCell>
                    <TableCell sx={{ color: Number(h.day_change_pct) >= 0 ? 'success.main' : 'error.main' }}>
                      {Number(h.day_change_pct) >= 0 ? '+' : ''}{fmt(h.day_change_pct)}%
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={`${fmt(h.portfolio_weight_pct, 1)}%`}
                        size="small"
                        sx={{
                          bgcolor: h.portfolio_weight_pct > 10 ? 'rgba(220,38,38,0.15)' : 'rgba(59,130,246,0.1)',
                          color: h.portfolio_weight_pct > 10 ? 'error.main' : 'primary.main',
                          fontWeight: 700, fontSize: '0.7rem',
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => openEdit(h)}><EditIcon fontSize="small" /></IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" color="error" onClick={() => setDeleteId(h.id)}><DeleteIcon fontSize="small" /></IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
                {(!holdings || holdings.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={12} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                      No holdings yet. Click "Add Stock" to add your Zerodha portfolio.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Add Stock Dialog */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Add Stock from Zerodha</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          {apiError && <Alert severity="error">{apiError}</Alert>}
          <TextField
            label="Symbol (e.g. RELIANCE, TCS, INFY)"
            value={form.tradingsymbol}
            onChange={(e) => setForm((f) => ({ ...f, tradingsymbol: e.target.value.toUpperCase() }))}
            size="small" fullWidth autoFocus
          />
          <TextField
            select label="Exchange" value={form.exchange}
            onChange={(e) => setForm((f) => ({ ...f, exchange: e.target.value }))}
            size="small" fullWidth
          >
            {EXCHANGES.map((ex) => <MenuItem key={ex} value={ex}>{ex}</MenuItem>)}
          </TextField>
          <TextField
            label="Quantity (shares you hold)"
            type="number" value={form.quantity}
            onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
            size="small" fullWidth
          />
          <TextField
            label="Average Buy Price (₹)"
            type="number" value={form.average_price}
            onChange={(e) => setForm((f) => ({ ...f, average_price: e.target.value }))}
            size="small" fullWidth
            helperText="Check your Zerodha app → Holdings → Avg. cost"
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setAddOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!form.tradingsymbol || !form.quantity || !form.average_price || addMutation.isPending}
            onClick={() => addMutation.mutate()}
          >
            {addMutation.isPending ? <CircularProgress size={18} color="inherit" /> : 'Add Stock'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editHolding} onClose={() => setEditHolding(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit {editHolding?.tradingsymbol}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          {apiError && <Alert severity="error">{apiError}</Alert>}
          <TextField
            label="Quantity" type="number" value={form.quantity}
            onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
            size="small" fullWidth
          />
          <TextField
            label="Average Buy Price (₹)" type="number" value={form.average_price}
            onChange={(e) => setForm((f) => ({ ...f, average_price: e.target.value }))}
            size="small" fullWidth
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setEditHolding(null)}>Cancel</Button>
          <Button variant="contained" disabled={editMutation.isPending} onClick={() => editMutation.mutate()}>
            {editMutation.isPending ? <CircularProgress size={18} color="inherit" /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirm Dialog */}
      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)} maxWidth="xs">
        <DialogTitle>Remove this stock?</DialogTitle>
        <DialogContent>
          <Typography>This will remove the holding from your dashboard. Your Zerodha account is not affected.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={() => deleteMutation.mutate(deleteId!)} disabled={deleteMutation.isPending}>
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
import SignalBadge from '../components/common/SignalBadge';

function fmt(n: number, d = 2) {
  return n.toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
}

export default function PortfolioPage() {
  const qc = useQueryClient();

  const { data: holdings } = useQuery({
    queryKey: ['holdings'],
    queryFn: () => portfolioApi.holdings().then((r) => r.data),
  });

  const { data: summary } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: () => portfolioApi.summary().then((r) => r.data),
  });

  const { data: allocations } = useQuery({
    queryKey: ['allocations'],
    queryFn: () => portfolioApi.allocations().then((r) => r.data),
  });

  const syncMutation = useMutation({
    mutationFn: () => portfolioApi.sync(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['holdings'] }),
  });

  const violations = allocations?.violations ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">My Portfolio</Typography>
        <Button variant="outlined" startIcon={<SyncIcon />} onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
          {syncMutation.isPending ? 'Syncing...' : 'Sync from Zerodha'}
        </Button>
      </Box>

      {!allocations?.portfolio_summary?.last_synced_at && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No portfolio data yet. Connect your Zerodha account in Settings and click Sync.
        </Alert>
      )}

      {violations.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Portfolio Rule Violations:</strong>
          <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
            {violations.map((v, i) => <li key={i}>{v}</li>)}
          </ul>
        </Alert>
      )}

      {/* Summary cards */}
      {summary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { l: 'Invested', v: `₹${fmt(summary.total_invested, 0)}` },
            { l: 'Current Value', v: `₹${fmt(summary.total_current_value, 0)}` },
            { l: 'Total P&L', v: `${summary.total_pnl >= 0 ? '+' : ''}₹${fmt(summary.total_pnl, 0)}`, color: summary.total_pnl >= 0 ? 'success.main' : 'error.main' },
            { l: 'P&L %', v: `${summary.total_pnl_pct >= 0 ? '+' : ''}${fmt(summary.total_pnl_pct)}%`, color: summary.total_pnl_pct >= 0 ? 'success.main' : 'error.main' },
            { l: "Today's Change", v: `${summary.total_day_change >= 0 ? '+' : ''}₹${fmt(summary.total_day_change, 0)}`, color: summary.total_day_change >= 0 ? 'success.main' : 'error.main' },
          ].map((item) => (
            <Grid item xs={6} sm={4} md={2.4} key={item.l}>
              <Card>
                <CardContent sx={{ pb: '12px !important' }}>
                  <Typography variant="caption" color="text.secondary">{item.l}</Typography>
                  <Typography variant="h6" fontWeight={700} sx={{ color: item.color || 'text.primary' }}>{item.v}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Holdings table */}
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Holdings</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {['Stock', 'Sector', 'Qty', 'Avg Price', 'LTP', 'Invested', 'Current', 'P&L', 'P&L %', 'Day Chg', 'Weight %'].map((h) => (
                    <TableCell key={h} sx={{ fontWeight: 700, fontSize: '0.75rem', whiteSpace: 'nowrap' }}>{h}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {(holdings ?? []).map((h) => (
                  <TableRow key={h.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={700}>{h.tradingsymbol}</Typography>
                      <Typography variant="caption" color="text.secondary">{h.exchange}</Typography>
                    </TableCell>
                    <TableCell><Chip label={h.sector} size="small" sx={{ fontSize: '0.65rem' }} /></TableCell>
                    <TableCell>{h.quantity}</TableCell>
                    <TableCell>₹{fmt(h.average_price)}</TableCell>
                    <TableCell>₹{fmt(h.last_price)}</TableCell>
                    <TableCell>₹{fmt(h.invested_value, 0)}</TableCell>
                    <TableCell>₹{fmt(h.current_value, 0)}</TableCell>
                    <TableCell sx={{ color: h.pnl >= 0 ? 'success.main' : 'error.main', fontWeight: 600 }}>
                      {h.pnl >= 0 ? '+' : ''}₹{fmt(h.pnl, 0)}
                    </TableCell>
                    <TableCell sx={{ color: h.pnl_pct >= 0 ? 'success.main' : 'error.main', fontWeight: 600 }}>
                      {h.pnl_pct >= 0 ? '+' : ''}{fmt(h.pnl_pct)}%
                    </TableCell>
                    <TableCell sx={{ color: h.day_change >= 0 ? 'success.main' : 'error.main' }}>
                      {h.day_change >= 0 ? '+' : ''}₹{fmt(h.day_change)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={`${h.portfolio_weight_pct.toFixed(1)}%`}
                        size="small"
                        sx={{
                          bgcolor: h.portfolio_weight_pct > 10 ? 'rgba(220,38,38,0.15)' : 'rgba(59,130,246,0.1)',
                          color: h.portfolio_weight_pct > 10 ? 'error.main' : 'primary.main',
                          fontSize: '0.7rem', fontWeight: 700,
                        }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {(!holdings || holdings.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={11} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                      No holdings. Sync your Zerodha portfolio.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
