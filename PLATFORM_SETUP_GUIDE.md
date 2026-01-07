# Platform Setup Guide

This guide provides step-by-step instructions for obtaining API credentials for Facebook, LinkedIn, and Instagram to enable multi-platform content distribution.

## Table of Contents

1. [Facebook Setup](#facebook-setup)
2. [LinkedIn Setup](#linkedin-setup)
3. [Instagram Setup](#instagram-setup)
4. [Environment Variables](#environment-variables)
5. [Troubleshooting](#troubleshooting)

---

## Facebook Setup

### Prerequisites
- Facebook account
- Facebook Page (create one at [facebook.com/pages/create](https://www.facebook.com/pages/create))

### Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** as the app type
4. Fill in app details:
   - **App Name**: "Cash Engine" (or your preferred name)
   - **Contact Email**: Your email
5. Click **"Create App"**

### Step 2: Add Facebook Login Product

1. In your app dashboard, click **"Add Product"**
2. Find **"Facebook Login"** and click **"Set Up"**
3. Select **"Web"** platform
4. Enter your site URL (can be `http://localhost` for testing)
5. Click **"Save"**

### Step 3: Get Page Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click **"Generate Access Token"**
4. Select these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
5. Click **"Generate Access Token"** and copy the token

### Step 4: Get Long-Lived Token (Recommended)

1. In Graph API Explorer, click **"i"** icon next to your token
2. Note the expiration time
3. To get a long-lived token (60 days), make this API call:
   ```
   GET https://graph.facebook.com/v18.0/oauth/access_token?
       grant_type=fb_exchange_token&
       client_id={your_app_id}&
       client_secret={your_app_secret}&
       fb_exchange_token={short_lived_token}
   ```
4. Copy the `access_token` from the response

### Step 5: Get Page Access Token

1. Make this API call to get your pages:
   ```
   GET https://graph.facebook.com/v18.0/me/accounts?access_token={long_lived_token}
   ```
2. Find your page in the response and copy its `access_token` (this is the Page Access Token)
3. Also note the `id` field (this is your Page ID)

### Step 6: Add to Environment Variables

Add to your `.env` file:
```
FACEBOOK_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_PAGE_ID=your_page_id_here
```

---

## LinkedIn Setup

### Prerequisites
- LinkedIn account
- LinkedIn Developer account (free)

### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click **"Create app"**
3. Fill in app details:
   - **App name**: "Cash Engine"
   - **LinkedIn Page**: Select your company page (or personal profile)
   - **Privacy policy URL**: Your website's privacy policy (can use a placeholder)
   - **App logo**: Upload a logo (optional)
4. Agree to terms and click **"Create app"**

### Step 2: Request API Access

1. In your app dashboard, go to **"Products"** tab
2. Find **"Sign In with LinkedIn using OpenID Connect"** and click **"Request access"**
3. Also request **"Marketing Developer Platform"** if available
4. Wait for approval (usually instant for basic access)

### Step 3: Get OAuth 2.0 Credentials

1. Go to **"Auth"** tab in your app dashboard
2. Note your **Client ID** and **Client Secret**
3. Add authorized redirect URLs:
   - `http://localhost:8000/callback` (for testing)
   - Your production callback URL

### Step 4: Get Access Token

#### Option A: Using OAuth 2.0 Flow (Recommended for Production)

1. Construct authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?
       response_type=code&
       client_id={your_client_id}&
       redirect_uri={your_redirect_uri}&
       state=random_state_string&
       scope=w_member_social
   ```
2. Visit the URL in your browser
3. Authorize the app
4. Copy the `code` from the redirect URL
5. Exchange code for token:
   ```
   POST https://www.linkedin.com/oauth/v2/accessToken
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&
   code={authorization_code}&
   redirect_uri={your_redirect_uri}&
   client_id={your_client_id}&
   client_secret={your_client_secret}
   ```
6. Copy the `access_token` from the response

#### Option B: Using Developer Token (Testing Only)

1. In your app dashboard, go to **"Auth"** tab
2. Click **"Generate token"** under **"Developer tokens"**
3. Select scope: `w_member_social`
4. Copy the token (expires in 60 days)

### Step 5: Get User URN (Optional)

1. Make this API call:
   ```
   GET https://api.linkedin.com/v2/me
   Headers: Authorization: Bearer {access_token}
   ```
2. Copy the `id` field (this is your URN, e.g., `urn:li:person:123456`)

### Step 6: Add to Environment Variables

Add to your `.env` file:
```
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_URN=urn:li:person:123456  # Optional, can be auto-detected
```

---

## Instagram Setup

### Prerequisites
- Instagram Business Account (convert from personal at [business.instagram.com](https://business.instagram.com/))
- Facebook Page connected to Instagram Business Account
- Facebook App (from Facebook Setup above)

### Step 1: Connect Instagram to Facebook Page

1. Go to your Facebook Page settings
2. Click **"Instagram"** in the left sidebar
3. Click **"Connect Account"**
4. Enter your Instagram Business Account credentials
5. Confirm connection

### Step 2: Get Instagram Business Account ID

1. Make this API call:
   ```
   GET https://graph.facebook.com/v18.0/{page_id}?
       fields=instagram_business_account&
       access_token={page_access_token}
   ```
2. Copy the `id` from `instagram_business_account` object (this is your Instagram Business Account ID)

### Step 3: Add to Environment Variables

Add to your `.env` file:
```
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id_here
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token_here  # Same as Facebook
```

**Note**: Instagram uses the same Facebook Page Access Token as Facebook posting.

---

## Environment Variables

Complete `.env` configuration for all platforms:

```env
# Facebook
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_facebook_page_id

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_URN=urn:li:person:123456  # Optional

# Instagram (requires Facebook setup)
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id

# Twitter (existing)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Distribution Settings
AUTO_DISTRIBUTE_CONTENT=true
DISTRIBUTION_PLATFORMS=facebook,linkedin,instagram  # Comma-separated
```

---

## Troubleshooting

### Facebook Errors

**Error 190: Token expired or invalid**
- Solution: Regenerate Page Access Token using steps above
- Ensure token has `pages_manage_posts` permission

**Error 4/17: Rate limit exceeded**
- Solution: Wait 1 hour, reduce posting frequency
- Facebook limit: 200 calls/hour per user

**Error 506: Duplicate post**
- Solution: This is normal - post was already published, treated as success

### LinkedIn Errors

**Error 401: Unauthorized**
- Solution: Token expired, regenerate using OAuth flow
- Ensure token has `w_member_social` scope

**Error 403: Forbidden**
- Solution: Check app permissions in LinkedIn Developer Portal
- Ensure "Marketing Developer Platform" access is approved

**Error 429: Rate limit exceeded**
- Solution: Wait and retry, LinkedIn limit: 500 calls/day for ugcPosts

### Instagram Errors

**Error 190: Token expired or invalid**
- Solution: Use same Facebook Page Access Token, regenerate if needed

**Error: "Instagram Business Account required"**
- Solution: Convert Instagram account to Business Account
- Connect to Facebook Page

**Error: "Media container creation failed"**
- Solution: Instagram API requires images for most post types
- Text-only posts may not be supported (consider adding an image)

### General Issues

**Platform marked as unhealthy**
- Solution: System automatically skips unhealthy platforms for 1 hour
- Check logs for specific error messages
- Verify credentials are correct

**No posts appearing**
- Solution: Check platform status in dashboard
- Verify credentials in `.env` file
- Check logs for error messages
- Ensure `AUTO_DISTRIBUTE_CONTENT=true` is set

---

## Platform-Specific Limitations

### Facebook
- **Rate Limits**: 200 calls/hour per user, 4800 calls/day per app
- **Content Limits**: 5000 characters per post
- **Hashtags**: Up to 30 hashtags supported
- **Links**: Supported in posts

### LinkedIn
- **Rate Limits**: 500 calls/day for ugcPosts
- **Content Limits**: 3000 characters per post
- **Hashtags**: Not recommended in main text (use in comments)
- **Tone**: Professional content only

### Instagram
- **Rate Limits**: Same as Facebook (shared quota)
- **Content Limits**: 2200 characters per caption
- **Hashtags**: Up to 30 hashtags supported
- **Media**: Most post types require an image/video

### Twitter
- **Rate Limits**: 300 tweets/3 hours (user auth), 1500 tweets/15 min (app auth)
- **Content Limits**: 280 characters per tweet
- **Hashtags**: Supported

---

## Testing

After setting up credentials, test each platform:

1. **Check platform status**:
   ```python
   # In Python console or script
   from cash_engine import CashEngine
   engine = CashEngine()
   # Check platform status in logs
   ```

2. **Test single platform**:
   - Set `DISTRIBUTION_PLATFORMS=facebook` (or `linkedin`, `instagram`)
   - Run content syndication
   - Check platform feed for post

3. **Monitor logs**:
   - Look for `✅ Posted to [Platform]` messages
   - Check for error messages with platform name

---

## Support

For additional help:
- Facebook API Docs: [developers.facebook.com/docs](https://developers.facebook.com/docs)
- LinkedIn API Docs: [docs.microsoft.com/en-us/linkedin](https://docs.microsoft.com/en-us/linkedin/)
- Instagram API Docs: [developers.facebook.com/docs/instagram-api](https://developers.facebook.com/docs/instagram-api)
