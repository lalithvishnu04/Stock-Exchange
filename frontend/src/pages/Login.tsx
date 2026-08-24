import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button,
  Alert, InputAdornment, IconButton, Divider, CircularProgress,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../api/endpoints';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();
  const [isRegister, setIsRegister] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '', full_name: '' });
  const [error, setError] = useState('');

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(form.username, form.password),
    onSuccess: async (res) => {
      setTokens(res.data.access_token, res.data.refresh_token);
      const meRes = await authApi.me();
      setUser(meRes.data);
      navigate('/dashboard');
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Login failed'),
  });

  const registerMutation = useMutation({
    mutationFn: () => authApi.register({ username: form.username, email: form.email, password: form.password, full_name: form.full_name }),
    onSuccess: () => {
      setIsRegister(false);
      setError('');
      setForm((f) => ({ ...f, password: '' }));
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Registration failed'),
  });

  const isLoading = loginMutation.isPending || registerMutation.isPending;

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1 }}>
              <TrendingUpIcon sx={{ color: 'primary.main', fontSize: 36 }} />
              <Typography variant="h5" fontWeight={700}>Stock Advisor</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              AI-powered Indian stock market intelligence
            </Typography>
          </Box>

          {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Username"
              value={form.username}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
              fullWidth size="small"
            />
            {isRegister && (
              <>
                <TextField
                  label="Full Name"
                  value={form.full_name}
                  onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                  fullWidth size="small"
                />
                <TextField
                  label="Email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  fullWidth size="small"
                />
              </>
            )}
            <TextField
              label="Password"
              type={showPass ? 'text' : 'password'}
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              fullWidth size="small"
              onKeyDown={(e) => e.key === 'Enter' && !isRegister && loginMutation.mutate()}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setShowPass(!showPass)}>
                      {showPass ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              variant="contained"
              fullWidth
              disabled={isLoading}
              onClick={() => isRegister ? registerMutation.mutate() : loginMutation.mutate()}
              sx={{ py: 1.2, fontWeight: 700 }}
            >
              {isLoading ? <CircularProgress size={20} color="inherit" /> : isRegister ? 'Create Account' : 'Sign In'}
            </Button>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="body2" color="text.secondary" align="center">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <Button size="small" onClick={() => { setIsRegister(!isRegister); setError(''); }}>
              {isRegister ? 'Sign In' : 'Register'}
            </Button>
          </Typography>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(59,130,246,0.08)', borderRadius: 2 }}>
            <Typography variant="caption" color="text.secondary" component="div">
              ⚠️ <strong>Disclaimer:</strong> This platform provides AI-assisted analysis only.
              You are the final decision maker. Never invest more than 10% in a single stock.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
