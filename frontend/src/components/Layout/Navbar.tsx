import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box, Chip, Avatar, Tooltip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsIcon from '@mui/icons-material/Notifications';
import LogoutIcon from '@mui/icons-material/Logout';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { recommendationsApi } from '../../api/endpoints';

interface NavbarProps {
  drawerWidth: number;
  onMenuClick: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const { data: market } = useQuery({
    queryKey: ['market-overview'],
    queryFn: () => recommendationsApi.marketOverview().then((r) => r.data),
    refetchInterval: 60_000,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const niftyChg = market?.nifty50_change_pct ?? 0;
  const marketOpen = market?.market_status === 'OPEN';

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: 1 }}>
        <IconButton color="inherit" onClick={onMenuClick} sx={{ display: { md: 'none' } }}>
          <MenuIcon />
        </IconButton>

        <TrendingUpIcon sx={{ color: 'primary.main', mr: 1 }} />
        <Typography variant="h6" sx={{ fontWeight: 700, color: 'white', flexGrow: 0, mr: 2 }}>
          Stock Advisor
        </Typography>

        {/* Live market pill */}
        <Box sx={{ display: { xs: 'none', sm: 'flex' }, gap: 1, flexGrow: 1, alignItems: 'center' }}>
          <Chip
            size="small"
            label={marketOpen ? '● MARKET OPEN' : '● MARKET CLOSED'}
            sx={{
              bgcolor: marketOpen ? 'rgba(22,163,74,0.15)' : 'rgba(107,114,128,0.15)',
              color: marketOpen ? 'success.main' : 'grey.400',
              fontWeight: 600,
              fontSize: '0.7rem',
            }}
          />
          {market && (
            <>
              <Chip
                size="small"
                label={`NIFTY50  ${market.nifty50.toLocaleString('en-IN', { maximumFractionDigits: 2 })}  ${niftyChg >= 0 ? '+' : ''}${niftyChg.toFixed(2)}%`}
                sx={{
                  bgcolor: niftyChg >= 0 ? 'rgba(22,163,74,0.1)' : 'rgba(220,38,38,0.1)',
                  color: niftyChg >= 0 ? 'success.main' : 'error.main',
                  fontWeight: 600,
                  fontSize: '0.72rem',
                }}
              />
              <Chip
                size="small"
                label={`SENSEX  ${market.sensex.toLocaleString('en-IN', { maximumFractionDigits: 2 })}  ${market.sensex_change_pct >= 0 ? '+' : ''}${market.sensex_change_pct.toFixed(2)}%`}
                sx={{
                  bgcolor: market.sensex_change_pct >= 0 ? 'rgba(22,163,74,0.1)' : 'rgba(220,38,38,0.1)',
                  color: market.sensex_change_pct >= 0 ? 'success.main' : 'error.main',
                  fontWeight: 600,
                  fontSize: '0.72rem',
                }}
              />
            </>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <Tooltip title="Alerts">
            <IconButton color="inherit" onClick={() => navigate('/portfolio')}>
              <NotificationsIcon />
            </IconButton>
          </Tooltip>
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: '0.8rem' }}>
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </Avatar>
          <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>
            {user?.username}
          </Typography>
          <Tooltip title="Logout">
            <IconButton color="inherit" onClick={handleLogout} size="small">
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
