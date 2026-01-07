# LinkedIn Quick Setup Guide

You have your LinkedIn OAuth credentials:
- **Client ID**: `YOUR_CLIENT_ID`
- **Client Secret**: `YOUR_CLIENT_SECRET`

## Quick Method: Get Developer Token (Easiest)

1. Go to [LinkedIn Developers Dashboard](https://www.linkedin.com/developers/apps)
2. Click on your app
3. Go to the **"Auth"** tab
4. Scroll down to **"Developer tokens"** section
5. Click **"Generate token"**
6. Select scope: `w_member_social`
7. Copy the token (this is your `LINKEDIN_ACCESS_TOKEN`)
8. The token expires in 60 days, but you can regenerate it anytime

## Alternative: OAuth Flow (For Production)

If you need a long-lived token or want to post on behalf of other users:

1. **Set up redirect URI** in your LinkedIn app:
   - Go to **"Auth"** tab
   - Add redirect URI: `http://localhost:8000/callback` (or your production URL)

2. **Get authorization code**:
   - Visit this URL in your browser (replace `YOUR_REDIRECT_URI`):
   ```
   https://www.linkedin.com/oauth/v2/authorization?
       response_type=code&
       client_id=YOUR_CLIENT_ID&
       redirect_uri=YOUR_REDIRECT_URI&
       state=random123&
       scope=w_member_social
   ```
   - Authorize the app
   - Copy the `code` parameter from the redirect URL

3. **Exchange code for token**:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=authorization_code&code=YOUR_CODE&redirect_uri=YOUR_REDIRECT_URI&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
   ```
   - Copy the `access_token` from the response

## Add to .env File

Once you have the access token, add to your `.env` file:

```env
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_CLIENT_ID=YOUR_CLIENT_ID
LINKEDIN_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

**Note**: The system only needs `LINKEDIN_ACCESS_TOKEN` to post. The Client ID and Secret are stored for reference but not used in the current implementation.

## Test Your Setup

After adding the token, restart the Cash Engine and check logs for:
- `✅ Posted to LinkedIn` messages
- Any authentication errors

## Troubleshooting

**Error 401: Unauthorized**
- Token expired or invalid
- Regenerate Developer Token or complete OAuth flow again

**Error 403: Forbidden**
- Check that your app has "Marketing Developer Platform" access approved
- Verify scope includes `w_member_social`

**Error 429: Rate Limit**
- LinkedIn limit: 500 calls/day for ugcPosts
- Wait and retry later
