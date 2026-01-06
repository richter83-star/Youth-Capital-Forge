# Click-Through Tracking System

## Overview

The click-through tracking system monitors when users click on product links sent via Instagram DMs. It generates tracking URLs that redirect to the final Gumroad destination while logging all click events.

## How It Works

1. **User sends DM** with product keyword (e.g., "FORGE", "PROMPTS")
2. **System generates tracking URL** like: `http://localhost:3000/track/{trackingId}`
3. **User clicks tracking URL** → Redirects to final Gumroad link
4. **Click is logged** with metadata (timestamp, user ID, product name)

## Components

### 1. ClickTracker (`utils/clickTracker.js`)
- Generates unique tracking URLs
- Stores redirect mappings
- Logs click events
- Provides statistics

### 2. Redirect Server (`utils/redirectServer.js`)
- HTTP server that handles redirects
- Endpoints:
  - `/track/{trackingId}` - Redirects to destination
  - `/stats` - View click statistics (JSON)
  - `/recent` - Recent clicks (JSON)

### 3. DM Handler (Updated `index.js`)
- Automatically generates tracking URLs for product links
- Sends tracking links instead of direct Gumroad URLs

## Setup

### 1. Start Redirect Server

```bash
node utils/redirectServer.js
```

Server runs on `http://localhost:3000` by default.

### 2. Configure Domain (Production)

Set `REDIRECT_DOMAIN` in `.env`:
```
REDIRECT_DOMAIN=https://track.yourdomain.com
```

### 3. Verify Tracking

```bash
# Test the tracking system
node test_tracking.js

# View statistics
node utils/verifyTracking.js
```

## Usage

### In Instagram DMs

When a user sends a product keyword:
- **User sends:** "FORGE"
- **Bot responds:** "Here is your link: http://localhost:3000/track/abc123..."
- **User clicks link** → Redirects to Gumroad
- **Click is logged** automatically

### View Statistics

```bash
node utils/verifyTracking.js
```

Or access via HTTP:
```bash
curl http://localhost:3000/stats
```

## Tracking Data

All clicks are stored in:
- `logs/clicks/clicks.json` - Click events
- `logs/clicks/redirects.json` - Redirect mappings

## Features

✅ **Automatic Tracking** - All DM links are tracked  
✅ **Click Logging** - Timestamp, user ID, product name  
✅ **Statistics** - Total clicks, clicks by product, unique users  
✅ **Redirect Server** - Handles redirects with 302 status  
✅ **Production Ready** - Configurable domain for deployment  

## Testing

Run the test suite:
```bash
node test_tracking.js
```

This will:
1. Generate tracking URLs
2. Simulate clicks
3. Display statistics
4. Show recent clicks

## Production Deployment

1. Deploy redirect server to your domain
2. Set `REDIRECT_DOMAIN` in `.env`
3. Update DNS to point tracking subdomain
4. Ensure server is accessible from Instagram

## Status

✅ **System Status:** Active and Working  
✅ **Tracking:** Functional  
✅ **Redirects:** Working  
✅ **Statistics:** Available  
