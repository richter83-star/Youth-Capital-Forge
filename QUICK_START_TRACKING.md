# Quick Start: Click Tracking System

## ✅ System Status: READY TO USE

The click tracking system is fully integrated and operational.

## How to Use

### Option 1: Local Testing (Current Setup)

1. **Start the redirect server:**
   ```bash
   node utils/redirectServer.js
   ```
   Server runs on `http://localhost:3000`

2. **Run your Instagram bot:**
   ```bash
   node index.js
   ```

3. **Test it:**
   - Send a DM to your Instagram account with a product keyword (e.g., "FORGE")
   - Bot will respond with a tracking URL like: `http://localhost:3000/track/abc123...`
   - Click the link → Redirects to Gumroad
   - Click is automatically logged

4. **View statistics:**
   ```bash
   node utils/verifyTracking.js
   ```

### Option 2: Production Deployment

1. **Deploy redirect server** to your domain (e.g., `track.yourdomain.com`)

2. **Update `.env` file:**
   ```
   REDIRECT_DOMAIN=https://track.yourdomain.com
   ```

3. **Run your bot** - it will automatically use the production domain

## What's Already Working

✅ **Automatic Tracking** - All DM links are tracked  
✅ **Click Logging** - Every click is logged with metadata  
✅ **Statistics** - View clicks by product, user, time  
✅ **Redirects** - Working redirects to Gumroad  
✅ **Integrated** - Already in your `index.js`  

## Current Integration

The system is **already integrated** into your Instagram bot:
- When users send product keywords in DMs, tracking URLs are automatically generated
- All clicks are logged to `logs/clicks/`
- Statistics are available via `utils/verifyTracking.js`

## Test It Now

```bash
# Terminal 1: Start redirect server
node utils/redirectServer.js

# Terminal 2: Run your bot
node index.js

# Terminal 3: Check stats
node utils/verifyTracking.js
```

## Next Steps

1. **For local testing:** Just start the redirect server and run your bot
2. **For production:** Deploy redirect server and set `REDIRECT_DOMAIN` in `.env`

The system is **ready to use right now!** 🚀
