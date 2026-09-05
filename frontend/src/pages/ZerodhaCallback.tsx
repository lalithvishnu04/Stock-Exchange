import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, Card, CardContent, Typography, CircularProgress, Alert } from '@mui/material';
import { authApi } from '../api/endpoints';

// Landing page for the Zerodha login redirect (configured as the Kite Connect
// app's "Redirect URL"). Captures request_token and completes the connection.
export default function ZerodhaCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'connecting' | 'success' | 'error'>('connecting');
  const [error, setError] = useState('');

  useEffect(() => {
    const requestToken = searchParams.get('request_token');
    const kiteStatus = searchParams.get('status');

    if (kiteStatus !== 'success' || !requestToken) {
      setStatus('error');
      setError('Zerodha login was not completed successfully.');
      return;
    }

    authApi.zerodhaConnect(requestToken)
      .then(() => {
        setStatus('success');
        setTimeout(() => navigate('/settings', { replace: true }), 1500);
      })
      .catch((err) => {
        setStatus('error');
        setError(err?.response?.data?.detail || 'Failed to complete Zerodha connection.');
      });
  }, [searchParams, navigate]);

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', bgcolor: '#0f172a' }}>
      <Card sx={{ maxWidth: 420 }}>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          {status === 'connecting' && (
            <>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography>Connecting to Zerodha…</Typography>
            </>
          )}
          {status === 'success' && (
            <Alert severity="success">Zerodha connected! Redirecting to Settings…</Alert>
          )}
          {status === 'error' && (
            <>
              <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
              <Typography variant="body2" color="text.secondary">
                Go back to Settings and try "Authorize with Zerodha" again.
              </Typography>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
