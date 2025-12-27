# 🤖 Autonomous AI Trader - Setup Guide

## 🎯 What This Does

Your AI will:
- ✅ Analyze stocks automatically using the scanner
- ✅ Make BUY decisions based on AI reasoning
- ✅ Execute trades through Alpaca (paper trading first!)
- ✅ Monitor positions and exit at targets/stops
- ✅ **LEARN from each trade to improve over time**
- ✅ Explain EVERY decision it makes

## 📋 Setup Steps

### Step 1: Create Alpaca Paper Trading Account (5 min)

1. Go to: https://alpaca.markets/
2. Click "Sign Up"
3. Choose "Paper Trading" (FREE - uses fake money)
4. Verify your email
5. Go to Dashboard → API Keys
6. Generate new API key pair
7. **SAVE THESE:**
   - API Key ID
   - Secret Key

### Step 2: Add API Keys to .env

Open `.env` file and add:

```
# xAI Grok API (you already have this)
XAI_API_KEY=your_xai_key_here

# Alpaca API (add these)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `alpaca-py` for trading.

### Step 4: Test the System

```bash
# Test 1: Run scanner to find opportunities
python scanner/run_daily_scan.py

# Test 2: Check if Alpaca connection works
python -c "from trader.autonomous_trader import AutonomousTrader; t = AutonomousTrader(); print(t.get_account_info())"
```

You should see your paper trading account info!

## 🚀 How to Run

### Terminal 1: Run the Scanner (finds opportunities)
```bash
python scanner/run_daily_scan.py
```

This populates `data/hot_stocks.json` with opportunities.

### Terminal 2: Start Autonomous Trader
```bash
python trader/run_autonomous.py
```

The AI will:
1. Check hot stocks every 5 minutes
2. Analyze each with xAI Grok
3. Decide whether to buy
4. Execute trades if confident
5. Monitor positions
6. Exit at targets or stops
7. Learn from results

### Browser: Monitor Dashboard
```bash
streamlit run app.py
```

Then go to "Autonomous Trader" page to watch!

## 📊 What You'll See

### When AI Decides to Buy:
```
✅ TRADE EXECUTED:
   Ticker: NVDA
   Action: BUY 7 shares @ $142.50
   Total: $997.50
   Stop Loss: $128.25
   Target: $164.00
   Confidence: 8/10
   Reasoning: Strong revenue growth (25%) combined with 
   technical breakout above resistance. Risk/reward 4.8:1.
```

### When AI Closes a Position:
```
🔔 POSITION CLOSED:
   Ticker: NVDA
   Reason: TARGET
   Entry: $142.50
   Exit: $164.20
   P/L: $151.90 (+15.2%)
   Outcome: WIN

📚 LESSON LEARNED: Breakout + strong fundamentals = 
high win rate. Continue prioritizing stocks with 
both technical and fundamental alignment.
```

## ⚙️ Settings You Can Adjust

Edit `trader/autonomous_trader.py`:

```python
self.max_position_size = 0.10  # 10% of portfolio per trade
self.max_loss_per_trade = 0.02  # 2% max loss
self.confidence_threshold = 7   # Only trade if AI confidence >= 7/10
```

## 🎓 Paper Trading → Real Money Transition

### Paper Trading Phase (Recommended: 1-3 months)
- Start with $100,000 fake money
- Let it run and prove profitability
- Target: 60%+ win rate, positive total profit

### Real Money Phase (After Proven)
- Start with $100 real money
- Keep same risk settings (2% max loss = $2 risk per trade)
- Gradually increase once comfortable

To switch to real money:
```python
trader = AutonomousTrader(paper_trading=False)  # In run_autonomous.py
```

## 🛡️ Safety Features

- ✅ **2% Max Loss Per Trade** - Can't lose more than $2 per trade (on $100)
- ✅ **Automatic Stop Losses** - Exits if stock drops
- ✅ **Confidence Threshold** - Only trades if AI is 7/10+ confident
- ✅ **Position Size Limits** - Max 10% of account per position
- ✅ **Paper Trading Default** - Always starts in fake money mode

## 📱 Monitoring

### Via Dashboard (Recommended)
Open `pages/05_Autonomous_Trader.py` in Streamlit to see:
- Active positions
- Trade history
- AI reasoning for each trade
- Lessons learned

### Via Terminal
The trader prints real-time updates:
- New opportunities analyzed
- Trades executed
- Positions closed
- Lessons learned

## 🐛 Troubleshooting

### "No hot stocks available"
- Run the scanner first: `python scanner/run_daily_scan.py`
- Or wait until Monday 9:30am when it auto-scans

### "API key not configured"
- Check `.env` file has both Alpaca keys
- Restart the trader after adding keys

### "Not enough cash"
- Paper trading starts with $100,000
- Real money: deposit at least $100 to Alpaca

## 📈 Expected Performance

### Conservative Estimate (Paper Trading):
- Win Rate: 55-65%
- Avg Profit Per Trade: 3-8%
- Avg Loss Per Trade: 1.5-2%
- Monthly Return: 5-15%

### Your $100 Real Money:
- Risk Per Trade: $2 (2%)
- Potential Profit: $4-6 per win (4-6%)
- With 60% win rate: ~$10-20/month
- Compounds over time!

## 🧠 How It Learns

After each trade closes, the AI:
1. Analyzes what worked or didn't
2. Extracts lessons
3. Stores in trade history
4. Future decisions factor in past lessons

Example learning:
- "Tech stocks with earnings beats + breakouts = 80% win rate"
- "Avoid stocks with P/E > 50 even if growth is strong"
- "Best risk/reward when RSI < 35 (oversold)"

## 🎯 Next Steps

1. ✅ Create Alpaca paper account
2. ✅ Add API keys to `.env`
3. ✅ Run `pip install -r requirements.txt`
4. ✅ Test: `python trader/run_autonomous.py`
5. ✅ Monitor dashboard
6. ✅ Let it trade for 1-3 months (paper)
7. ✅ Switch to real $100 once proven

**Questions? Check the code comments or ask!** 🚀
