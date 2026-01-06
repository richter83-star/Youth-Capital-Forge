# Instagram Automation Engine - Wealth Niche

A modular Instagram automation engine for the Wealth niche that handles account rotation, content processing, Reel uploads, and automated DM responses.

## Features

- **Account Rotation**: Automatically rotates between accounts when encountering bans or checkpoints
- **Content Engine**: Randomly selects videos from queue and processes them for unique MD5 hashes
- **Reel Upload**: Uploads Reels with automated captions
- **DM Plugin**: Monitors comments for "FORGE" keyword, likes them, and sends DMs with a 7-minute delay
- **Simulation**: Always runs pre-login and post-login flow simulations for better stealth

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Accounts**
   - Copy `accounts.json` and add your Instagram accounts:
   ```json
   {
     "accounts": [
       {
         "username": "your_username_1",
         "password": "your_password_1"
       }
     ]
   }
   ```

3. **Configure Environment Variables**
   - Create a `.env` file in the root directory:
   ```
   IG_USERNAME=your_default_username
   FORGE_LINK=https://your-forge-link.com
   ```

4. **Add Videos to Queue**
   - Place your MP4 files in the `./queue` directory
   - The engine will randomly select videos from this directory

## Usage

Run the automation engine:
```bash
node index.js
```

The engine will:
1. Load accounts from `accounts.json`
2. Attempt login with account rotation on failures
3. Select a random video from `./queue`
4. Process the video for unique MD5 hash
5. Upload as Reel with caption: "30k/mo system. Comment FORGE below."
6. Start monitoring comments for "FORGE" keyword
7. Like matching comments and send DMs after 7-minute delay

## Architecture

### AccountManager
Handles account rotation when bans or checkpoints are detected.

### ContentEngine
Selects random videos and processes them to ensure unique MD5 hashes using Jimp.

### PostManager
Manages Reel uploads with automated captions.

### DMPlugin
Monitors comments, likes "FORGE" comments, and sends automated DMs with configurable delay.

## Notes

- The engine uses Instagram Private API which may require frequent updates
- Always use responsibly and in compliance with Instagram's Terms of Service
- Account rotation helps distribute load and reduce ban risk
- Video processing ensures each upload has a unique hash to avoid duplicate detection

## Error Handling

- Automatic account rotation on ban/checkpoint detection
- Graceful error handling with detailed logging
- Process cleanup on shutdown (Ctrl+C)

