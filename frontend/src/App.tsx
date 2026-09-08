import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box, CircularProgress } from '@mui/material';
import { useAuthStore } from './store/authStore';
import { authApi } from './api/endpoints';
import Layout from './components/Layout/Layout';
import LoginPage from './pages/Login';
import DashboardPage from './pages/Dashboard';
import PortfolioPage from './pages/Portfolio';
import RecommendationsPage from './pages/Recommendations';
import ReportsPage from './pages/Reports';
import SettingsPage from './pages/Settings';
import ZerodhaCallbackPage from './pages/ZerodhaCallback';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3b82f6' },
    secondary: { main: '#10b981' },
    background: { default: '#0f172a', paper: '#1e293b' },
    success: { main: '#16a34a' },
    error: { main: '#dc2626' },
    warning: { main: '#d97706' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.06)' },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, setUser, logout } = useAuthStore();
  const [loading, setLoading] = React.useState(!user);

  // The JWT persists in localStorage across refreshes, but the `user` object
  // (name, email, Zerodha connection status, etc.) only ever gets populated
  // right after login — refreshing the page reset it to null with nothing to
  // reload it. Bootstrap it here so it survives refreshes on any page.
  React.useEffect(() => {
    if (!isAuthenticated || user) {
      setLoading(false);
      return;
    }
    authApi.me()
      .then((res) => setUser(res.data))
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, setUser, logout]);

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/zerodha/callback"
            element={
              <ProtectedRoute>
                <ZerodhaCallbackPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
