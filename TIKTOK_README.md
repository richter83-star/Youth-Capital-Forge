# TikTok Automation Integration

## Overview

TikTok automation has been integrated into the multi-platform automation system. The TikTok module follows the same architecture as Instagram for consistency.

## Features

✅ **Video Posting** - Upload videos from queue with captions  
✅ **Comment Monitoring** - Watch for keywords (FORGE, PROMPTS, HUSTLE)  
✅ **DM Automation** - Send product links via DMs  
✅ **Click Tracking** - Integrated with Marketing Agent V2  
✅ **Account Management** - Support for multiple TikTok accounts  

## Setup

### 1. Configure TikTok Accounts

Edit `tiktok_accounts.json`:
```json
{
  "accounts": [
    {
      "username": "your_tiktok_username",
      "password": "your_password",
      "email": "your_email@example.com"
    }
  ]
}
```

### 2. Environment Variables

Add to `.env`:
```
ENABLE_TIKTOK=true
MARKETING_AGENT_URL=http://localhost:9000
```

### 3. Run TikTok Bot

```bash
# Run TikTok only
node tiktok_index.js

# Run both Instagram and TikTok
node multi_platform.js
```

## Architecture

### TikTokAutomation Class (`utils/tiktok.js`)
- Handles TikTok API interactions
- Video posting with unique hash processing
- Comment monitoring and keyword detection
- DM sending with tracking links
- Integration with Marketing Agent

### TikTok Bot (`tiktok_index.js`)
- Main automation loop
- Video queue processing
- Adaptive posting intervals
- Comment monitoring
- Error handling and account rotation

## Important Notes

⚠️ **TikTok API Limitations**

TikTok doesn't have an official public API for posting content. The current implementation uses placeholder methods that need to be replaced with:

1. **TikTok Private API** (similar to `instagram-private-api`)
2. **Browser Automation** (Puppeteer/Playwright)
3. **TikTok Business API** (for official business accounts)

### Recommended Approach

For production use, consider:

1. **Browser Automation** (Puppeteer/Playwright):
   ```javascript
   const puppeteer = require('puppeteer');
   // Automate TikTok web interface
   ```

2. **TikTok Private API Library**:
   - Similar to `instagram-private-api`
   - Requires reverse engineering TikTok's mobile API
   - More reliable but needs maintenance

3. **TikTok Business API**:
   - Official API for business accounts
   - Limited features but more stable

## Integration with Marketing Agent

TikTok links are automatically tracked through Marketing Agent V2:
- Campaign: "Instagram Automation" (shared with Instagram)
- Channel: "tiktok_dm"
- Full analytics: clicks, bots, device types, geo-location

## Usage Examples

### Post a Video
```javascript
const TikTokAutomation = require('./utils/tiktok');
const tiktok = new TikTokAutomation(account);

await tiktok.postVideo('queue/video.mp4', 'Check link in bio! #wealth #ai', {
    privacy: 0,
    hashtags: ['#wealth', '#ai', '#success']
});
```

### Monitor Comments
```javascript
await tiktok.monitorComments('video_id_123', ['FORGE', 'PROMPTS']);
```

### Send DM
```javascript
await tiktok.sendDM('user_id_456', 'FORGE');
```

## Next Steps

1. **Implement TikTok API** - Replace placeholder methods with actual TikTok API calls
2. **Add Browser Automation** - Use Puppeteer for web-based automation
3. **Test Integration** - Verify posting, comments, and DMs work correctly
4. **Production Deployment** - Deploy with proper error handling and monitoring

## Status

✅ **Module Created** - TikTok automation structure ready  
⚠️ **API Integration** - Needs actual TikTok API implementation  
✅ **Tracking Integration** - Marketing Agent V2 ready  
✅ **Multi-Platform** - Can run alongside Instagram  

---

**Note**: The TikTok module is ready for integration but requires actual TikTok API implementation for production use.
