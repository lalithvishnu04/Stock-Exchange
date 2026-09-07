"""Curated universe of liquid, well-known NSE-listed stocks across sectors.

NSE lists 2000+ equities, most of them thin-volume small-caps that aren't
worth scanning (bad data quality, wide spreads, high risk). This list favours
large & mid-cap, liquid names spanning every major sector instead — a much
broader base than the previous 20-stock Nifty50 subset, while staying
realistic about what a free yfinance-based pipeline can scan on a schedule.

Update periodically — index/sector constituents shift over time.
"""

# A small, diverse (spans most major sectors), high-confidence set of
# well-known large-caps — used as the default fast scan so "Scan Market Now"
# returns in well under a minute instead of scanning the full ~190-stock
# universe, which can take several minutes.
TOP_PICKS: list[str] = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "BHARTIARTL", "ITC", "SBIN", "LT", "BAJFINANCE", "MARUTI", "SUNPHARMA",
    "TITAN", "ASIANPAINT", "ULTRACEMCO", "TATASTEEL", "NTPC", "ADANIPORTS", "WIPRO",
]

STOCK_UNIVERSE: list[str] = [
    # Banking & Financials
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK",
    "BANKBARODA", "PNB", "IDFCFIRSTB", "FEDERALBNK", "AUBANK", "BANDHANBNK",
    "RBLBANK", "CANBK", "UNIONBANK", "BANKINDIA", "INDIANB",
    "BAJFINANCE", "BAJAJFINSV", "HDFCLIFE", "SBILIFE", "ICICIPRULI", "ICICIGI",
    "HDFCAMC", "CHOLAFIN", "SHRIRAMFIN", "MUTHOOTFIN", "PFC", "RECLTD",
    "LICHSGFIN", "PEL", "LICI",

    # IT
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS",
    "PERSISTENT", "COFORGE", "LTTS", "OFSS", "KPITTECH", "TATAELXSI", "CYIENT",

    # Auto
    "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT",
    "TVSMOTOR", "ASHOKLEY", "BALKRISIND", "MOTHERSON", "BOSCHLTD", "EXIDEIND",
    "MRF", "APOLLOTYRE", "BHARATFORG",

    # FMCG / Consumer
    "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO",
    "GODREJCP", "COLPAL", "TATACONSUM", "VBL", "UBL", "JYOTHYLAB", "EMAMILTD",

    # Pharma / Healthcare
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN", "AUROPHARMA",
    "ALKEM", "TORNTPHARM", "ZYDUSLIFE", "BIOCON", "GLENMARK", "LAURUSLABS",
    "APOLLOHOSP", "MAXHEALTH", "FORTIS", "METROPOLIS", "LALPATHLAB",

    # Energy / Oil & Gas / Power
    "RELIANCE", "ONGC", "IOC", "BPCL", "HINDPETRO", "GAIL", "PETRONET",
    "IGL", "MGL", "TATAPOWER", "NTPC", "POWERGRID", "NHPC", "SJVN",
    "ADANIGREEN", "ADANIPOWER", "ADANIENSOL",

    # Metals & Mining
    "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDANTA", "COALINDIA", "NMDC",
    "SAIL", "JINDALSTEL", "NATIONALUM", "HINDZINC", "APLAPOLLO",

    # Cement
    "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT", "JKCEMENT",
    "RAMCOCEM",

    # Telecom
    "BHARTIARTL", "IDEA", "INDUSTOWER",

    # Infra / Construction / Ports
    "LT", "ADANIPORTS", "GMRINFRA", "IRB", "NCC", "NBCC", "RVNL", "CONCOR",
    "ADANIENT",

    # Chemicals
    "PIDILITIND", "SRF", "UPL", "AARTIIND", "DEEPAKNTR", "TATACHEM",
    "NAVINFLUOR", "ATUL", "VINATIORGA",

    # Capital Goods / Industrials / Defence
    "SIEMENS", "ABB", "CUMMINSIND", "HAVELLS", "VOLTAS", "BLUESTARCO",
    "POLYCAB", "CROMPTON", "THERMAX", "BEL", "BHEL", "HAL", "BEML",

    # Realty
    "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD", "BRIGADE",

    # Retail / Consumer Discretionary
    "TITAN", "TRENT", "DMART", "PAGEIND", "ABFRL", "RELAXO", "BATAINDIA",

    # Media
    "SUNTV", "ZEEL", "PVRINOX",

    # Paints
    "ASIANPAINT", "BERGEPAINT", "KANSAINER", "AKZOINDIA",

    # New-age / Internet
    "ZOMATO", "NYKAA", "PAYTM", "POLICYBZR", "IRCTC",

    # Diversified / Aviation / Others
    "INDIGO", "PIIND", "GRASIM", "BAJAJHLDNG",
]
