# Facebook Quick Setup Guide

This guide will help you get Facebook Page Access Token and Page ID for posting content.

## Prerequisites
- Facebook account
- Facebook Page (create one at [facebook.com/pages/create](https://www.facebook.com/pages/create) if you don't have one)

## Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** as the app type
4. Fill in app details:
   - **App Name**: "Cash Engine" (or your preferred name)
   - **Contact Email**: Your email
5. Click **"Create App"**

## Step 2: Add Facebook Login Product

1. In your app dashboard, click **"Add Product"**
2. Find **"Facebook Login"** and click **"Set Up"**
3. Select **"Web"** platform
4. Enter your site URL: `http://localhost:8000` (or your domain)
5. Click **"Save"**

## Step 3: Get Page Access Token (Quick Method)

### Option A: Using Graph API Explorer (Easiest)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown (top right)
3. Click **"Generate Access Token"** button
4. Select these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
5. Click **"Generate Access Token"** and copy the token

### Option B: Get Long-Lived Token (Recommended - 60 days)

1. In Graph API Explorer, click **"i"** icon next to your token
2. Note the expiration time
3. Make this API call to get a long-lived token:
   ```
   GET https://graph.facebook.com/v18.0/oauth/access_token?
       grant_type=fb_exchange_token&
       client_id={YOUR_APP_ID}&
       client_secret={YOUR_APP_SECRET}&
       fb_exchange_token={SHORT_LIVED_TOKEN}
   ```
   - Replace `{YOUR_APP_ID}` with your App ID
   - Replace `{YOUR_APP_SECRET}` with your App Secret (found in Settings → Basic)
   - Replace `{SHORT_LIVED_TOKEN}` with the token from Graph API Explorer
4. Copy the `access_token` from the response

## Step 4: Get Page Access Token

1. Make this API call to get your pages:
   ```
   GET https://graph.facebook.com/v18.0/me/accounts?access_token={LONG_LIVED_TOKEN}
   ```
   - Replace `{LONG_LIVED_TOKEN}` with the long-lived token from Step 3
2. Find your page in the response and copy:
   - **`access_token`** (this is your Page Access Token)
   - **`id`** (this is your Page ID)

## Step 5: Add to .env File

Add these lines to your `.env` file:

```env
FACEBOOK_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_PAGE_ID=your_page_id_here
```

## Step 6: Test Your Setup

After adding credentials, test with:
```bash
python test_facebook_auth.py
```

Or restart the Cash Engine and check logs for:
- `✅ Posted to Facebook` messages
- Any authentication errors

## Troubleshooting

**Error 190: Token expired or invalid**
- Token has expired (short-lived tokens last 1-2 hours)
- Get a new long-lived token using Step 3 Option B

**Error 4/17: Rate limit exceeded**
- Facebook limit: 200 calls/hour per user
- Wait 1 hour and retry

**Error 506: Duplicate post**
- This is normal - post was already published
- Treated as success

## Notes

- Page Access Tokens don't expire (unless revoked)
- Make sure your app has "Read and Write" permissions
- Test with a single post first before enabling auto-posting
