import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, Grid,
  Dialog, DialogTitle, DialogContent, DialogActions, Alert, CircularProgress,
  Chip, Tab, Tabs, Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import RefreshIcon from '@mui/icons-material/Refresh';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import DeleteIcon from '@mui/icons-material/Delete';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recommendationsApi, portfolioApi } from '../api/endpoints';
import SignalBadge from '../components/common/SignalBadge';
import { useAutoAnalysis } from '../hooks/useAutoAnalysis';
import { useSignalDetection } from '../hooks/useSignalDetection';
import type { Recommendation } from '../types';

export default function RecommendationsPage() {
  const queryClient = useQueryClient();
  const [searchSymbol, setSearchSymbol] = useState('');
  const [tab, setTab] = useState<'market' | 'portfolio' | 'watchlist'>('market');

  // Buy new stock modal
  const [buyModal, setBuyModal] = useState(false);
  const [buyData, setBuyData] = useState({ symbol: '', exchange: 'NSE', quantity: 1, average_price: 0 });
  const [selectedStockForBuy, setSelectedStockForBuy] = useState<Recommendation | null>(null);

  // Add quantity modal (for existing holdings)
  const [addQtyModal, setAddQtyModal] = useState(false);
  const [addQtyData, setAddQtyData] = useState({ holdingId: 0, newQuantity: 0, newPrice: 0 });
  const [selectedStockForQty, setSelectedStockForQty] = useState<Recommendation | null>(null);

  // ── Auto-Analysis & Signal Detection ──────────────────────────────────────────
  const { isMarketOpen, minutesUntilClose, triggerAnalysisNow } = useAutoAnalysis({ enabled: true, intervalMinutes: 5 });
  
  // ── Queries ──────────────────────────────────────────────────────────────────
  const { data: marketPicks, isLoading: marketLoading } = useQuery({
    queryKey: ['market-picks'],
    queryFn: () => recommendationsApi.marketPicks().then((r) => r.data),
    refetchInterval: isMarketOpen ? 5 * 60 * 1000 : false, // Auto-refresh every 5 min if market open
  });

  const { data: portfolioRecs, isLoading: portfolioLoading } = useQuery({
    queryKey: ['today-recommendations'],
    queryFn: () => recommendationsApi.today().then((r) => r.data),
    refetchInterval: isMarketOpen ? 5 * 60 * 1000 : false,
  });

  const { data: holdings } = useQuery({
    queryKey: ['portfolio-holdings'],
    queryFn: () => portfolioApi.holdings().then((r) => r.data),
  });

  // Get all recommendations for signal detection
  const allRecs = portfolioRecs ? [
    ...portfolioRecs.buy,
    ...portfolioRecs.add_more,
    ...portfolioRecs.hold,
    ...portfolioRecs.partial_sell,
    ...portfolioRecs.sell,
    ...portfolioRecs.avoid,
  ] : [];

  // Signal detection
  const { recentAlerts, buySignals, sellSignals, addMoreSignals } = useSignalDetection(allRecs, portfolioRecs);

  // Watchlist queries
  const { data: watchlist, isLoading: watchlistLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => recommendationsApi.getWatchlist().then((r) => r.data),
  });

  // ── Mutations ────────────────────────────────────────────────────────────────
  const analyseMutation = useMutation({
    mutationFn: (symbol: string) => recommendationsApi.analyse(symbol.toUpperCase(), 'NSE'),
    onSuccess: (data) => {
      setSelectedStockForBuy(data.data);
      setBuyData((prev) => ({
        ...prev,
        symbol: data.data.stock_symbol,
        average_price: data.data.current_price || 0,
      }));
      setBuyModal(true);
    },
  });

  const buyNewStockMutation = useMutation({
    mutationFn: (payload: typeof buyData) =>
      portfolioApi.addHolding({
        tradingsymbol: payload.symbol,
        exchange: payload.exchange,
        quantity: payload.quantity,
        average_price: payload.average_price,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['market-picks'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] });
      setBuyModal(false);
      setBuyData({ symbol: '', exchange: 'NSE', quantity: 1, average_price: 0 });
      setSelectedStockForBuy(null);
      setSearchSymbol('');
    },
  });

  const analyseAllMutation = useMutation({
    mutationFn: () => recommendationsApi.analyseAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['today-recommendations'] });
    },
  });

  const addQuantityMutation = useMutation({
    mutationFn: (payload: typeof addQtyData) =>
      portfolioApi.updateHolding(payload.holdingId, {
        quantity: payload.newQuantity,
        average_price: payload.newPrice,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-holdings'] });
      queryClient.invalidateQueries({ queryKey: ['today-recommendations'] });
      setAddQtyModal(false);
      setAddQtyData({ holdingId: 0, newQuantity: 0, newPrice: 0 });
      setSelectedStockForQty(null);
    },
  });

  const addToWatchlistMutation = useMutation({
    mutationFn: (rec: Recommendation) =>
      recommendationsApi.addToWatchlist({
        stock_symbol: rec.stock_symbol,
        stock_name: rec.stock_name,
        exchange: rec.exchange || 'NSE',
        signal: rec.signal,
        confidence_score: rec.confidence_score,
        current_price: rec.current_price,
        target_price: rec.target_price,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });

  // ── Handlers ─────────────────────────────────────────────────────────────────
  const handleSearchAndAnalyse = async () => {
    if (!searchSymbol.trim()) return;
    analyseMutation.mutate(searchSymbol.trim());
  };

  const handleBuyNewStock = () => {
    buyNewStockMutation.mutate(buyData);
  };

  const handleOpenAddQtyModal = (rec: Recommendation) => {
    const holding = holdings?.find((h) => h.tradingsymbol === rec.stock_symbol);
    if (holding) {
      setSelectedStockForQty(rec);
      setAddQtyData({
        holdingId: holding.id,
        newQuantity: holding.quantity,
        newPrice: holding.average_price,
      });
      setAddQtyModal(true);
    }
  };

  const handleAddQuantity = () => {
    addQuantityMutation.mutate(addQtyData);
  };

  // ── Render market picks section ───────────────────────────────────────────────
  const renderMarketPicks = () => (
    <>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            🔍 Search & Analyse New Stocks
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              label="Stock Symbol (e.g. WIPRO, ASIANPAINT)"
              value={searchSymbol}
              onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
              size="small"
              sx={{ flexGrow: 1 }}
              onKeyDown={(e) => e.key === 'Enter' && searchSymbol && handleSearchAndAnalyse()}
            />
            <Button
              variant="contained"
              startIcon={analyseMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <SearchIcon />}
              disabled={!searchSymbol || analyseMutation.isPending}
              onClick={handleSearchAndAnalyse}
            >
              Analyse
            </Button>
          </Box>

          {selectedStockForBuy && analyseMutation.data && (
            <Card sx={{ mb: 2, bgcolor: 'action.hover' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle1" fontWeight={700}>
                      {selectedStockForBuy.stock_symbol}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <SignalBadge signal={selectedStockForBuy.signal} />
                      <Chip label={`₹${selectedStockForBuy.current_price}`} size="small" />
                      <Chip label={`Score: ${selectedStockForBuy.confidence_score}%`} size="small" />
                    </Box>
                  </Box>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<AddIcon />}
                    onClick={() => setBuyModal(true)}
                  >
                    Add to Portfolio
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}

          {analyseMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {(analyseMutation.error as any)?.response?.data?.detail || 'Analysis failed'}
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            💡 <strong>Market Recommendations:</strong> Top performers from Nifty50 (excluding holdings)
          </Typography>

          {marketLoading && <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress /></Box>}

          <Grid container spacing={2}>
            {marketPicks?.map((rec) => (
              <Grid item xs={12} sm={6} lg={4} key={rec.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="h6" fontWeight={700}>
                        {rec.stock_symbol}
                      </Typography>
                      <Chip label="NEW" size="small" color="primary" />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <SignalBadge signal={rec.signal} />
                      <Chip label={`₹${rec.current_price}`} size="small" variant="outlined" />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Confidence: <strong>{rec.confidence_score}%</strong>
                    </Typography>
                    <Typography variant="caption" display="block" color="text.secondary">
                      Reasoning: {rec.reasoning?.substring(0, 60)}...
                    </Typography>
                  </CardContent>
                  <Box sx={{ p: 1, pt: 0, display: 'flex', gap: 1 }}>
                    <Button
                      fullWidth
                      size="small"
                      variant="contained"
                      color={rec.signal === 'BUY' ? 'success' : rec.signal === 'SELL' ? 'error' : 'info'}
                      startIcon={<AddIcon />}
                      onClick={() => {
                        setSelectedStockForBuy(rec);
                        setBuyData((prev) => ({
                          ...prev,
                          symbol: rec.stock_symbol,
                          average_price: rec.current_price || 0,
                        }));
                        setBuyModal(true);
                      }}
                    >
                      Buy Now
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<BookmarkIcon />}
                      onClick={() => addToWatchlistMutation.mutate(rec)}
                      disabled={addToWatchlistMutation.isPending}
                    >
                      Watchlist
                    </Button>
                  </Box>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </>
  );

  // ── Render portfolio recommendations section ──────────────────────────────────
  const renderPortfolioRecs = () => {
    const allRecs = portfolioRecs
      ? [...portfolioRecs.buy, ...portfolioRecs.add_more, ...portfolioRecs.hold, ...portfolioRecs.partial_sell, ...portfolioRecs.sell, ...portfolioRecs.avoid]
      : [];

    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" fontWeight={700}>Portfolio Holdings - Analysis</Typography>
            <Button
              variant="contained"
              color="success"
              size="small"
              startIcon={analyseAllMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
              disabled={analyseAllMutation.isPending}
              onClick={() => analyseAllMutation.mutate()}
            >
              Analyse All Holdings
            </Button>
          </Box>

          {analyseAllMutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {(analyseAllMutation.error as any)?.response?.data?.detail || 'Bulk analysis failed'}
            </Alert>
          )}

          {portfolioLoading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}

          {!portfolioLoading && allRecs.length === 0 && (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No holdings to recommend. Add stocks to your portfolio first!
            </Typography>
          )}

          {allRecs.length > 0 && (
            <Grid container spacing={2}>
              {allRecs.map((rec) => (
                <Grid item xs={12} sm={6} lg={4} key={rec.id}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="h6" fontWeight={700}>
                          {rec.stock_symbol}
                        </Typography>
                        <Chip label="HOLDING" size="small" variant="outlined" />
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <SignalBadge signal={rec.signal} />
                        <Chip label={`₹${rec.current_price}`} size="small" variant="outlined" />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Current: <strong>{holdings?.find((h) => h.tradingsymbol === rec.stock_symbol)?.quantity || 0} units</strong>
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary">
                        Score: {rec.confidence_score}%
                      </Typography>
                    </CardContent>
                    <Box sx={{ p: 1, pt: 0, display: 'flex', gap: 1 }}>
                      {(rec.signal === 'BUY' || rec.signal === 'ADD_MORE') && (
                        <Button
                          fullWidth
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<AddIcon />}
                          onClick={() => handleOpenAddQtyModal(rec)}
                        >
                          Add Qty
                        </Button>
                      )}
                      <Button
                        fullWidth
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          // Can add view details or edit option
                        }}
                      >
                        Details
                      </Button>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </CardContent>
      </Card>
    );
  };

  // ── Modal: Buy New Stock ─────────────────────────────────────────────────────
  const BuyNewStockModal = () => (
    <Dialog open={buyModal} onClose={() => setBuyModal(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        Add New Stock to Portfolio
        {selectedStockForBuy && <Typography variant="caption" display="block" color="text.secondary">{selectedStockForBuy.stock_symbol}</Typography>}
      </DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {selectedStockForBuy && (
            <Card sx={{ bgcolor: 'action.hover' }}>
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Current Price</Typography>
                    <Typography variant="h6">₹{selectedStockForBuy.current_price}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Signal</Typography>
                    <SignalBadge signal={selectedStockForBuy.signal} />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          <TextField
            label="Symbol"
            value={buyData.symbol}
            onChange={(e) => setBuyData((prev) => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
            fullWidth
            disabled
          />
          <TextField
            select
            label="Exchange"
            value={buyData.exchange}
            onChange={(e) => setBuyData((prev) => ({ ...prev, exchange: e.target.value }))}
            fullWidth
            SelectProps={{
              native: true,
            }}
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </TextField>
          <TextField
            label="Quantity"
            type="number"
            value={buyData.quantity}
            onChange={(e) => setBuyData((prev) => ({ ...prev, quantity: Math.max(1, parseInt(e.target.value) || 1) }))}
            fullWidth
            inputProps={{ min: 1 }}
          />
          <TextField
            label="Average Price (₹)"
            type="number"
            value={buyData.average_price}
            onChange={(e) => setBuyData((prev) => ({ ...prev, average_price: parseFloat(e.target.value) || 0 }))}
            fullWidth
            step="0.01"
            inputProps={{ min: 0, step: '0.01' }}
          />
          <Typography variant="body2" color="text.secondary">
            Total Investment: ₹{(buyData.quantity * buyData.average_price).toFixed(2)}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setBuyModal(false)}>Cancel</Button>
        <Button
          variant="contained"
          color="success"
          onClick={handleBuyNewStock}
          disabled={buyNewStockMutation.isPending || !buyData.symbol || buyData.quantity < 1}
        >
          {buyNewStockMutation.isPending ? <CircularProgress size={20} /> : 'Add to Portfolio'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ── Modal: Add Quantity ──────────────────────────────────────────────────────
  const AddQuantityModal = () => (
    <Dialog open={addQtyModal} onClose={() => setAddQtyModal(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        Add More Quantity
        {selectedStockForQty && <Typography variant="caption" display="block" color="text.secondary">{selectedStockForQty.stock_symbol}</Typography>}
      </DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {selectedStockForQty && (
            <Card sx={{ bgcolor: 'action.hover' }}>
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Current Price</Typography>
                    <Typography variant="h6">₹{selectedStockForQty.current_price}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Signal</Typography>
                    <SignalBadge signal={selectedStockForQty.signal} />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          <TextField
            label="New Total Quantity"
            type="number"
            value={addQtyData.newQuantity}
            onChange={(e) => setAddQtyData((prev) => ({ ...prev, newQuantity: Math.max(1, parseInt(e.target.value) || 1) }))}
            fullWidth
            helperText="Total quantity after adding more"
            inputProps={{ min: 1 }}
          />
          <TextField
            label="New Average Price (₹)"
            type="number"
            value={addQtyData.newPrice}
            onChange={(e) => setAddQtyData((prev) => ({ ...prev, newPrice: parseFloat(e.target.value) || 0 }))}
            fullWidth
            step="0.01"
            helperText="Average price per unit"
            inputProps={{ min: 0, step: '0.01' }}
          />
          <Typography variant="body2" color="text.secondary">
            New Total Investment: ₹{(addQtyData.newQuantity * addQtyData.newPrice).toFixed(2)}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setAddQtyModal(false)}>Cancel</Button>
        <Button
          variant="contained"
          color="success"
          onClick={handleAddQuantity}
          disabled={addQuantityMutation.isPending || addQtyData.newQuantity < 1}
        >
          {addQuantityMutation.isPending ? <CircularProgress size={20} /> : 'Update Quantity'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ── Main Render ──────────────────────────────────────────────────────────────
  const renderWatchlist = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          <BookmarkIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          My Watchlist ({watchlist?.length || 0})
        </Typography>

        {watchlistLoading && <Box sx={{ textAlign: 'center', py: 3 }}><CircularProgress /></Box>}

        {!watchlist?.length && !watchlistLoading && (
          <Alert severity="info">
            💡 Add recommended stocks to your watchlist. Once you buy, one-click confirmation here!
          </Alert>
        )}

        <Grid container spacing={2}>
          {watchlist?.map((item: any) => (
            <Grid item xs={12} sm={6} lg={4} key={item.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" fontWeight={700}>
                      {item.stock_symbol}
                    </Typography>
                    <Chip
                      label={item.signal}
                      size="small"
                      color={item.signal === 'SELL' ? 'error' : item.signal === 'BUY' ? 'success' : 'warning'}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip label={`₹${item.current_price}`} size="small" variant="outlined" />
                    <Chip label={`${item.confidence_score}%`} size="small" />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Added: {new Date(item.added_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
                <Divider />
                <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    size="small"
                    color="success"
                    fullWidth
                    onClick={() => {
                      setSelectedStockForBuy({ ...item, id: 0, reason: '', stock_name: item.stock_symbol });
                      setBuyData({
                        symbol: item.stock_symbol,
                        exchange: item.exchange,
                        quantity: 1,
                        average_price: item.current_price,
                      });
                      setBuyModal(true);
                    }}
                  >
                    Buy Now
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => {
                      recommendationsApi.removeFromWatchlist(item.id);
                      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
                    }}
                  >
                    <DeleteIcon />
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Market Status & Recent Alerts */}
      <Card sx={{ mb: 3, bgcolor: isMarketOpen ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)' }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: isMarketOpen ? '#4CAF50' : '#F44336',
                    animation: isMarketOpen ? 'pulse 2s infinite' : 'none',
                    '@keyframes pulse': {
                      '0%, 100%': { opacity: 1 },
                      '50%': { opacity: 0.5 },
                    },
                  }}
                />
                <Box>
                  <Typography variant="subtitle2" fontWeight={700}>
                    {isMarketOpen ? '🟢 Market OPEN' : '🔴 Market CLOSED'}
                  </Typography>
                  {isMarketOpen && (
                    <Typography variant="caption" color="text.secondary">
                      ⏱️ {minutesUntilClose} minutes until close (3:30 PM IST)
                    </Typography>
                  )}
                </Box>
              </Box>
            </Grid>
            {isMarketOpen && (
              <Grid item xs={12} sm={6} sx={{ textAlign: { xs: 'left', sm: 'right' } }}>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => triggerAnalysisNow()}
                >
                  Refresh Now
                </Button>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* Recent Alerts (BUY/SELL Signals) */}
      {recentAlerts.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'rgba(255, 235, 59, 0.1)', borderLeft: '4px solid #FFC107' }}>
          <CardContent>
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 2 }}>
              🚨 Recent Signals (Last {recentAlerts.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {recentAlerts.slice(-10).map((alert, idx) => (
                <Chip
                  key={idx}
                  label={`${alert.symbol}: ${alert.signal} @ ₹${alert.price}`}
                  size="small"
                  color={alert.signal === 'SELL' ? 'error' : alert.signal === 'BUY' ? 'success' : 'warning'}
                  variant="outlined"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      <Typography variant="h4" sx={{ mb: 3 }}>
        <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Recommendations
      </Typography>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Tab label="Market Recommendations" value="market" />
        <Tab label="Portfolio Holdings" value="portfolio" />
        <Tab label={`Watchlist (${watchlist?.length || 0})`} value="watchlist" />
      </Tabs>

      {tab === 'market' && renderMarketPicks()}
      {tab === 'portfolio' && renderPortfolioRecs()}
      {tab === 'watchlist' && renderWatchlist()}

      <BuyNewStockModal />
      <AddQuantityModal />
    </Box>
  );
}
