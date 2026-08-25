import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Grid, TextField,
  Button, Alert, Switch, FormControlLabel, CircularProgress, Link, Divider,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../api/endpoints';
import { useAuthStore } from '../store/authStore';


export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const [form, setForm] = useState({
    full_name: user?.full_name ?? '',
    email_alerts_enabled: user?.email_alerts_enabled ?? true,
    telegram_alerts_enabled: user?.telegram_alerts_enabled ?? true,
    telegram_chat_id: '',
    zerodha_api_key: '',
    zerodha_api_secret: '',
  });
  const [saved, setSaved] = useState(false);

  const updateMutation = useMutation({
    mutationFn: () => authApi.updateSettings(form),
    onSuccess: (res) => { setUser(res.data); setSaved(true); setTimeout(() => setSaved(false), 3000); },
  });

  const zerodhaLoginUrl = `${import.meta.env.VITE_API_BASE_URL || ''}/api/auth/zerodha/login-url`;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Settings</Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Settings saved successfully!</Alert>}

      <Grid container spacing={3}>
        {/* Profile */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Profile</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField label="Username" value={user?.username} disabled size="small" />
                <TextField label="Email" value={user?.email} disabled size="small" />
                <TextField
                  label="Full Name"
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Notifications</Typography>
              <FormControlLabel
                control={<Switch checked={form.email_alerts_enabled} onChange={(e) => setForm((f) => ({ ...f, email_alerts_enabled: e.target.checked }))} />}
                label="Email Alerts"
              />
              <FormControlLabel
                control={<Switch checked={form.telegram_alerts_enabled} onChange={(e) => setForm((f) => ({ ...f, telegram_alerts_enabled: e.target.checked }))} />}
                label="Telegram Alerts"
              />
              {form.telegram_alerts_enabled && (
                <TextField
                  label="Telegram Chat ID"
                  value={form.telegram_chat_id}
                  onChange={(e) => setForm((f) => ({ ...f, telegram_chat_id: e.target.value }))}
                  size="small"
                  fullWidth
                  sx={{ mt: 2 }}
                  helperText="Find your Chat ID by messaging @userinfobot on Telegram"
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Zerodha */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={700}>Zerodha Integration</Typography>
                {user?.has_zerodha_connected && (
                  <Alert severity="success" sx={{ py: 0 }}>✓ Connected</Alert>
                )}
              </Box>

              <Alert severity="info" sx={{ mb: 2 }}>
                This platform reads your portfolio <strong>read-only</strong>. It cannot place trades.
                You need a Zerodha Kite Connect app. Create one at{' '}
                <Link href="https://developers.kite.trade" target="_blank" rel="noopener">developers.kite.trade</Link>.
              </Alert>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Kite API Key"
                    value={form.zerodha_api_key}
                    onChange={(e) => setForm((f) => ({ ...f, zerodha_api_key: e.target.value }))}
                    size="small" fullWidth
                    type="password"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Kite API Secret"
                    value={form.zerodha_api_secret}
                    onChange={(e) => setForm((f) => ({ ...f, zerodha_api_secret: e.target.value }))}
                    size="small" fullWidth
                    type="password"
                  />
                </Grid>
              </Grid>

              <Button variant="outlined" sx={{ mt: 2 }} onClick={() => window.open(zerodhaLoginUrl, '_blank')}>
                Authorize with Zerodha
              </Button>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                After authorizing, you'll be redirected back to the app. Your holdings will be synced automatically.
              </Typography>

              <Divider sx={{ my: 3 }} />
              <Box sx={{ bgcolor: 'rgba(59,130,246,0.06)', p: 2, borderRadius: 2 }}>
                <Typography variant="subtitle2" fontWeight={700}>Portfolio Rules in Effect</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  • Maximum <strong>10%</strong> allocation in a single stock<br />
                  • Maximum <strong>25%</strong> allocation in a single sector<br />
                  • AI will never recommend investing entire capital in one stock<br />
                  • Every recommendation shows risk level: LOW / MEDIUM / HIGH
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, textAlign: 'right' }}>
        <Button
          variant="contained"
          onClick={() => updateMutation.mutate()}
          disabled={updateMutation.isPending}
          startIcon={updateMutation.isPending ? <CircularProgress size={16} color="inherit" /> : null}
        >
          Save Settings
        </Button>
      </Box>
    </Box>
  );
}
