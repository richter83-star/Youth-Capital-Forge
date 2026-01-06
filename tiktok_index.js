require('dotenv').config();
const fs = require('fs-extra');
const path = require('path');
const TikTokAutomation = require('./utils/tiktok');
const MarketingAgent = require('./utils/marketingAgent');
const ClickTracker = require('./utils/clickTracker');
const Optimizer = require('./utils/optimizer');
const Gumroad = require('./utils/gumroad');

const gumroad = new Gumroad(process.env.GUMROAD_TOKEN);
const optimizer = new Optimizer(process.env.GUMROAD_TOKEN);
const clickTracker = new ClickTracker();
const marketingAgent = new MarketingAgent(process.env.MARKETING_AGENT_URL || 'http://localhost:9000');

// Check if Marketing Agent is available
let useMarketingAgent = false;
(async () => {
    useMarketingAgent = await marketingAgent.isAvailable();
    if (useMarketingAgent) {
        console.log('[+] Marketing Agent V2 connected - using advanced tracking');
    } else {
        console.log('[!] Marketing Agent V2 not available - using simple tracker');
    }
})();

// TikTok captions
const TIKTOK_CAPTIONS = [
    "Automate your income. Link in bio.",
    "Stop trading time for money.",
    "The digital revolution is here.",
    "30k/mo system. Comment FORGE below.",
    "Build wealth while you sleep.",
    "AI is changing everything."
];

/**
 * Load TikTok accounts
 */
async function loadAccounts() {
    const accountsPath = path.join(__dirname, 'tiktok_accounts.json');
    
    if (!(await fs.pathExists(accountsPath))) {
        // Create default accounts file
        await fs.writeJson(accountsPath, {
            accounts: [
                {
                    username: "your_tiktok_username",
                    password: "your_password",
                    email: "your_email@example.com"
                }
            ]
        });
        console.log(`[!] Created ${accountsPath} - please add your TikTok accounts`);
        process.exit(1);
    }
    
    return await fs.readJson(accountsPath);
}

/**
 * Post next video to TikTok
 */
async function postNextVideo(tiktok) {
    const queueDir = path.join(__dirname, 'queue');
    const files = (await fs.readdir(queueDir).catch(() => [])).filter(f => f.endsWith('.mp4'));

    if (files.length === 0) {
        console.log("[TikTok] Queue empty. Waiting for next window.");
        return 4 * 60 * 60 * 1000; // 4 hours default
    }

    const videoName = files[0];
    const videoPath = path.join(queueDir, videoName);
    
    console.log(`[TikTok] Processing video: ${videoName}`);

    try {
        // Get strategy from optimizer
        const strategy = await optimizer.analyzeAndPivot(null);
        
        // Select random caption
        const caption = `${TIKTOK_CAPTIONS[Math.floor(Math.random() * TIKTOK_CAPTIONS.length)]} ${strategy.activeHashtags.join(' ')}`;
        
        // Post video
        const result = await tiktok.postVideo(videoPath, caption, {
            privacy: 0, // Public
            hashtags: strategy.activeHashtags
        });

        // Move to processed
        const processedDir = path.join(__dirname, 'logs', 'processed');
        await fs.ensureDir(processedDir);
        await fs.move(videoPath, path.join(processedDir, `tiktok_${videoName}`));

        // Start monitoring comments
        setTimeout(() => {
            tiktok.monitorComments(result.videoId, ['FORGE', 'PROMPTS', 'HUSTLE']);
        }, 60000); // Start monitoring after 1 minute

        console.log(`[TikTok] Post success: ${result.videoId}`);
        return strategy.currentInterval;
    } catch (error) {
        console.error(`[TikTok] Post error: ${error.message}`);
        return 4 * 60 * 60 * 1000; // Wait 4 hours on error
    }
}

/**
 * Main TikTok automation loop
 */
async function main() {
    try {
        const accountsData = await loadAccounts();
        const activeAccount = accountsData.accounts[0];
        
        // Initialize TikTok automation
        const tiktok = new TikTokAutomation(
            activeAccount,
            useMarketingAgent ? marketingAgent : null,
            clickTracker
        );

        // Login
        await tiktok.login();

        // Start posting loop
        async function scheduler() {
            try {
                const nextInterval = await postNextVideo(tiktok);
                console.log(`[TikTok] Next post in ${nextInterval / (60 * 60 * 1000)} hours`);
                setTimeout(scheduler, nextInterval);
            } catch (error) {
                console.error(`[TikTok] Scheduler error: ${error.message}`);
                setTimeout(scheduler, 4 * 60 * 60 * 1000); // Retry in 4 hours
            }
        }

        // Start scheduler
        await scheduler();

    } catch (error) {
        console.error(`[TikTok] Fatal error: ${error.message}`);
        process.exit(1);
    }
}

    // Handle graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n[TikTok] Shutting down gracefully...');
    if (tiktok) {
        await tiktok.closeBrowser();
    }
    process.exit(0);
});

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main };
