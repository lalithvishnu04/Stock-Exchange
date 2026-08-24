import React from 'react';
import { Box, Typography, Card, CardContent, Button, List, ListItem, ListItemText, Divider, CircularProgress } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery, useMutation } from '@tanstack/react-query';
import { portfolioApi } from '../api/endpoints';

export default function ReportsPage() {
  const { data: reports, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: () => portfolioApi.reports().then((r) => r.data),
  });

  const generateMutation = useMutation({
    mutationFn: () => fetch('/api/reports/generate/daily', { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } }),
    onSuccess: () => refetch(),
  });

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Reports</Typography>
        <Button
          variant="contained"
          startIcon={generateMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
        >
          Generate Daily Report
        </Button>
      </Box>

      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>Report History</Typography>
          {(!reports || reports.length === 0) ? (
            <Typography color="text.secondary">No reports generated yet. Click "Generate Daily Report" above.</Typography>
          ) : (
            <List>
              {reports.map((r: any, i: number) => (
                <React.Fragment key={r.id}>
                  <ListItem
                    secondaryAction={
                      <Button size="small" startIcon={<DownloadIcon />} onClick={() => window.open(`/api/portfolio/reports/${r.id}`, '_blank')}>
                        View
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={r.title}
                      secondary={`${r.report_type.toUpperCase()} · ${new Date(r.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })}`}
                    />
                  </ListItem>
                  {i < reports.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(59,130,246,0.06)', borderRadius: 2 }}>
        <Typography variant="caption" color="text.secondary">
          📋 Daily reports are auto-generated at 5 PM IST on weekdays. Weekly reports are sent every Friday.
          Reports are also sent via Telegram and Email if configured.
        </Typography>
      </Box>
    </Box>
  );
}
