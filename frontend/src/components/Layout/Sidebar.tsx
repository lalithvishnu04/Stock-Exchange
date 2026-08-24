import React from 'react';
import { List, ListItemButton, ListItemIcon, ListItemText, Divider, Box, Typography } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import AssessmentIcon from '@mui/icons-material/Assessment';
import SettingsIcon from '@mui/icons-material/Settings';
import { useNavigate, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { label: 'My Portfolio', icon: <AccountBalanceWalletIcon />, path: '/portfolio' },
  { label: 'Recommendations', icon: <LightbulbIcon />, path: '/recommendations' },
  { label: 'Reports', icon: <AssessmentIcon />, path: '/reports' },
];

interface SidebarProps {
  onClose?: () => void;
}

export default function Sidebar({ onClose }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const go = (path: string) => {
    navigate(path);
    onClose?.();
  };

  return (
    <Box sx={{ pt: 2 }}>
      <List dense>
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              onClick={() => go(item.path)}
              selected={active}
              sx={{
                mx: 1,
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': {
                  bgcolor: 'rgba(59,130,246,0.12)',
                  '& .MuiListItemIcon-root': { color: 'primary.main' },
                  '& .MuiListItemText-primary': { color: 'primary.main', fontWeight: 600 },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: 'grey.500' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>

      <Divider sx={{ my: 1, borderColor: 'rgba(255,255,255,0.06)' }} />

      <List dense>
        <ListItemButton
          onClick={() => go('/settings')}
          selected={location.pathname === '/settings'}
          sx={{ mx: 1, borderRadius: 2 }}
        >
          <ListItemIcon sx={{ minWidth: 36, color: 'grey.500' }}>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItemButton>
      </List>

      <Box sx={{ position: 'absolute', bottom: 16, left: 16, right: 16 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
          AI Stock Advisor v1.0
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', fontSize: '0.65rem' }}>
          Not financial advice. You decide.
        </Typography>
      </Box>
    </Box>
  );
}
