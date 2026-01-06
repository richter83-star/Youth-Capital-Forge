# Instagram API Migration Guide

## Current Status

- **Package**: `instagram-private-api@1.46.1` (deprecated)
- **Vulnerabilities**: 7 (4 moderate, 1 high, 2 critical)
- **Usage**: `index.js` - Instagram automation (login, posting, DM handling)

## Migration Options

### Option A: Puppeteer-Based Solution (Recommended)

**Pros:**
- Already in dependencies (`puppeteer@23.11.1`)
- More maintainable and actively developed
- Better stealth capabilities
- More flexible for future changes

**Cons:**
- Requires significant code refactoring
- Higher resource usage (browser instances)
- Slower than direct API calls

**Implementation Approach:**

1. **Login Function**:
```javascript
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

async function login(username, password) {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.goto('https://www.instagram.com/accounts/login/');
  
  // Wait for login form
  await page.waitForSelector('input[name="username"]');
  
  // Fill credentials
  await page.type('input[name="username"]', username);
  await page.type('input[name="password"]', password);
  
  // Submit
  await page.click('button[type="submit"]');
  await page.waitForNavigation();
  
  return { browser, page };
}
```

2. **Post Reel Function**:
```javascript
async function postReel(page, videoPath, caption) {
  // Navigate to create post
  await page.goto('https://www.instagram.com/');
  await page.click('svg[aria-label="New post"]');
  
  // Upload video
  const input = await page.$('input[type="file"]');
  await input.uploadFile(videoPath);
  
  // Wait for upload
  await page.waitForSelector('button:contains("Next")');
  await page.click('button:contains("Next")');
  
  // Add caption
  await page.type('textarea[aria-label="Write a caption..."]', caption);
  
  // Post
  await page.click('button:contains("Share")');
}
```

3. **DM Handling**:
```javascript
async function handleDMs(page) {
  await page.goto('https://www.instagram.com/direct/inbox/');
  
  // Wait for messages
  await page.waitForSelector('[role="listbox"]');
  
  // Get unread threads
  const threads = await page.$$('[role="listbox"] > div');
  
  for (const thread of threads) {
    // Check for keywords
    const text = await thread.$eval('span', el => el.textContent);
    if (text.includes('FORGE')) {
      // Open thread and respond
      await thread.click();
      await page.waitForSelector('textarea[placeholder="Message..."]');
      await page.type('textarea[placeholder="Message..."]', 'Here is your link: ...');
      await page.keyboard.press('Enter');
    }
  }
}
```

### Option B: Update Package (If Available)

```bash
# Check for updates
npm view instagram-private-api versions

# If newer version exists
npm install instagram-private-api@latest

# Test thoroughly
npm test
```

### Option C: Instagram Basic Display API (Official)

**Pros:**
- Official API
- More stable
- Better long-term support

**Cons:**
- Limited functionality
- Requires app approval
- Cannot post content (read-only)
- Not suitable for automation

## Recommended Migration Path

### Phase 1: Preparation (1 week)
1. Create feature branch
2. Set up Puppeteer test environment
3. Implement basic login functionality
4. Test with staging account

### Phase 2: Core Functions (2 weeks)
1. Implement posting functionality
2. Implement DM handling
3. Add error handling and retries
4. Test all scenarios

### Phase 3: Integration (1 week)
1. Replace old code in `index.js`
2. Update dependencies
3. Remove `instagram-private-api`
4. Test end-to-end

### Phase 4: Production (1 week)
1. Deploy to staging
2. Monitor for 1 week
3. Deploy to production
4. Keep old code as backup for 2 weeks

## Code Changes Required

### `index.js` Changes:

**Before:**
```javascript
const { IgApiClient } = require('instagram-private-api');
const ig = new IgApiClient();
await ig.account.login(username, password);
```

**After:**
```javascript
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

// Use Puppeteer for all Instagram interactions
```

### `package.json` Changes:

**Remove:**
```json
"instagram-private-api": "^1.46.1"
```

**Ensure:**
```json
"puppeteer": "^23.11.1",
"puppeteer-extra": "^3.3.6",
"puppeteer-extra-plugin-stealth": "^2.11.2"
```

## Testing Checklist

- [ ] Login with valid credentials
- [ ] Login with invalid credentials (error handling)
- [ ] Post Reel successfully
- [ ] Handle DM keywords correctly
- [ ] Account rotation on errors
- [ ] Rate limiting compliance
- [ ] Error recovery
- [ ] Logging and monitoring

## Rollback Plan

1. Keep old `index.js` as `index.js.backup`
2. Keep `instagram-private-api` in `package.json.backup`
3. If issues occur:
   ```bash
   cp index.js.backup index.js
   npm install instagram-private-api@1.46.1
   npm restart
   ```

## Success Criteria

- All functionality maintained
- No increase in error rate
- Improved stealth (fewer bans)
- All vulnerabilities resolved
- Performance acceptable (< 2x slower acceptable)

## Timeline

- **Total Duration**: 4-5 weeks
- **Risk Level**: Medium-High
- **Priority**: HIGH (Security Critical)

## Notes

- Monitor Instagram's Terms of Service changes
- Consider implementing rate limiting
- Add comprehensive logging
- Test with multiple accounts
- Consider using proxy rotation for better stealth
