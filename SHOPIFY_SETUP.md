# Shopify Integration Setup Guide

This guide will help you configure Shopify integration for the Cash Engine.

## Step 1: Create Shopify Private App

1. Go to your Shopify Admin: `https://dracanus-ai.myshopify.com/admin`
2. Navigate to **Settings** → **Apps and sales channels**
3. Click **Develop apps** (or **Create an app**)
4. Click **Create an app**
5. Name it: `Cash Engine Integration`
6. Click **Create app**

## Step 2: Configure Admin API Access

1. In your app settings, click **Configure Admin API scopes**
2. Enable these scopes:
   - `read_products` - To fetch product catalog
   - `read_orders` - To receive order webhooks (optional, but recommended)
3. Click **Save**

## Step 3: Generate Admin API Access Token

1. In your app settings, click **API credentials**
2. Click **Install app** (if prompted)
3. Click **Reveal token** or **Generate token**
4. **Copy the Admin API access token** - you'll need this for `SHOPIFY_ACCESS_TOKEN`

## Step 4: Get Store Domain

Your store domain is: `dracanus-ai.myshopify.com`
(Use without `https://` in the .env file)

## Step 5: Create Webhook for Order Tracking

1. In Shopify Admin, go to **Settings** → **Notifications**
2. Scroll to **Webhooks** section
3. Click **Create webhook**
4. Configure:
   - **Event**: `Order creation`
   - **Format**: `JSON`
   - **URL**: `http://your-server-ip:5000/webhooks/shopify/orders`
     - Replace `your-server-ip` with your actual server IP
     - If using localhost for testing: `http://localhost:5000/webhooks/shopify/orders`
5. Click **Save webhook**
6. **Copy the webhook secret** - you'll need this for `SHOPIFY_WEBHOOK_SECRET`

## Step 6: Add to .env File

Add these variables to your `.env` file:

```env
# Shopify Configuration
SHOPIFY_STORE_DOMAIN=dracanus-ai.myshopify.com
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_ACCESS_TOKEN=your_access_token_here
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret_here
SHOPIFY_ENABLED=true
```

**Note**: 
- `SHOPIFY_API_KEY` and `SHOPIFY_API_SECRET` are optional if you only use the Admin API access token
- If you don't have an API key/secret, you can leave them empty or set to placeholder values
- The `SHOPIFY_ACCESS_TOKEN` is required - this is the Admin API access token from Step 3
- The `SHOPIFY_WEBHOOK_SECRET` is optional but recommended for security

## Step 7: Test the Integration

Run the test script to verify your setup:

```bash
python test_shopify_connection.py
```

## Step 8: Enable Product Sync

The system will automatically sync products every 6 hours. To manually trigger a sync:

```python
from cash_engine import CashEngine
engine = CashEngine()
engine.sync_shopify_products()
```

## Troubleshooting

### "Shopify API authentication failed (401)"
- Verify your `SHOPIFY_ACCESS_TOKEN` is correct
- Make sure the app has the required scopes enabled
- Check that the app is installed (click "Install app" in API credentials)

### "Webhook signature verification failed"
- Verify your `SHOPIFY_WEBHOOK_SECRET` matches the webhook secret from Shopify
- Check that the webhook URL is accessible from the internet (use ngrok for local testing)

### "Shopify not enabled"
- Set `SHOPIFY_ENABLED=true` in your .env file
- Restart the Cash Engine

### Products not syncing
- Check that `SHOPIFY_ACCESS_TOKEN` is set correctly
- Verify the app has `read_products` scope
- Check logs for specific error messages

## Features Enabled

Once configured, the Cash Engine will:
- ✅ Automatically sync products from Shopify every 6 hours
- ✅ Track orders and revenue in real-time via webhooks
- ✅ Promote Shopify products in social media content posts
- ✅ Display Shopify revenue statistics in the dashboard
- ✅ Support both Shopify and Gumroad products simultaneously
