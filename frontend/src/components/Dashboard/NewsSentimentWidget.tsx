import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Link, Divider } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { recommendationsApi } from '../../api/endpoints';

const SENTIMENT_COLOR = {
  POSITIVE: { color: '#16a34a', bg: 'rgba(22,163,74,0.12)' },
  NEGATIVE: { color: '#dc2626', bg: 'rgba(220,38,38,0.12)' },
  NEUTRAL:  { color: '#6b7280', bg: 'rgba(107,114,128,0.12)' },
};

export default function NewsSentimentWidget() {
  const { data: news } = useQuery({
    queryKey: ['market-news'],
    queryFn: () => recommendationsApi.news().then((r) => r.data),
    refetchInterval: 300_000,
  });

  const items = news ?? [];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          📰 News & Sentiment
        </Typography>

        {items.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            No news available. Add a NEWS_API_KEY in settings.
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {items.slice(0, 8).map((item, i) => {
              const cfg = SENTIMENT_COLOR[item.sentiment] ?? SENTIMENT_COLOR.NEUTRAL;
              return (
                <Box key={i}>
                  <Box sx={{ display: 'flex', gap: 1.5, py: 1.5, alignItems: 'flex-start' }}>
                    <Chip
                      label={item.sentiment}
                      size="small"
                      sx={{ bgcolor: cfg.bg, color: cfg.color, fontWeight: 700, fontSize: '0.65rem', flexShrink: 0, height: 20, mt: 0.3 }}
                    />
                    <Box sx={{ flexGrow: 1 }}>
                      <Link
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        color="inherit"
                        underline="hover"
                        sx={{ fontWeight: 500, fontSize: '0.85rem', lineHeight: 1.4 }}
                      >
                        {item.title}
                      </Link>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.3 }}>
                        {item.source} · {new Date(item.published_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        {item.stock_symbols.length > 0 && ` · ${item.stock_symbols.join(', ')}`}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: cfg.color, fontWeight: 700, flexShrink: 0 }}>
                      {item.sentiment_score >= 0 ? '+' : ''}{item.sentiment_score.toFixed(2)}
                    </Typography>
                  </Box>
                  {i < Math.min(items.length, 8) - 1 && <Divider sx={{ borderColor: 'rgba(255,255,255,0.04)' }} />}
                </Box>
              );
            })}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
