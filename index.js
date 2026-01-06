require('dotenv').config();
const { IgApiClient } = require('instagram-private-api');
const { exec, promisify } = require('child_process');
const execAsync = promisify(exec);
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');
const Optimizer = require('./utils/optimizer');
const Gumroad = require('./utils/gumroad');
const ClickTracker = require('./utils/clickTracker');
const MarketingAgent = require('./utils/marketingAgent');

const ig = new IgApiClient();
const gumroad = new Gumroad(process.env.GUMROAD_TOKEN);
const optimizer = new Optimizer(process.env.GUMROAD_TOKEN);
const clickTracker = new ClickTracker();
const marketingAgent = new MarketingAgent(process.env.MARKETING_AGENT_URL || 'http://localhost:8000');

// Check if Marketing Agent is available (fallback to simple tracker)
let useMarketingAgent = false;
(async () => {
    useMarketingAgent = await marketingAgent.isAvailable();
    if (useMarketingAgent) {
        console.log('[+] Marketing Agent V2 connected - using advanced tracking');
    } else {
        console.log('[!] Marketing Agent V2 not available - using simple tracker');
    }
})();

// Dynamic product mapping from ENV with caching
let productCatalogCache = null;
let productCatalogCacheTime = 0;
const PRODUCT_CATALOG_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getProductCatalog() {
    const now = Date.now();
    if (productCatalogCache && (now - productCatalogCacheTime) < PRODUCT_CATALOG_CACHE_TTL) {
        return productCatalogCache;
    }
    
    const products = {};
    Object.keys(process.env).forEach(key => {
        if (key.endsWith('_ID')) {
            const name = key.replace('_ID', '');
            products[name] = process.env[`${name}_LINK`] || `https://gumroad.com/l/${name.toLowerCase()}`;
        }
    });
    
    productCatalogCache = products;
    productCatalogCacheTime = now;
    return products;
}

async function login(account) {
    ig.state.generateDevice(account.username);
    try {
        await ig.simulate.preLoginFlow();
    } catch (e) {}
    await ig.account.login(account.username, account.password);
    process.nextTick(async () => {
        try { await ig.simulate.postLoginFlow(); } catch(e) {}
    });
}

// Track processed messages to avoid duplicates
const processedMessages = new Set();
const PROCESSED_MESSAGE_TTL = 24 * 60 * 60 * 1000; // 24 hours

async function handleDMs() {
    console.log("[*] Checking DMs...");
    const PRODUCTS = getProductCatalog();
    try {
        const inbox = ig.feed.directInbox();
        const threads = await inbox.items();
        
        // Process threads in parallel batches (max 5 at a time)
        const batchSize = 5;
        for (let i = 0; i < threads.length; i += batchSize) {
            const batch = threads.slice(i, i + batchSize);
            await Promise.all(batch.map(async (thread) => {
                const lastMessage = thread.last_permanent_item;
                if (!lastMessage || lastMessage.item_type !== 'text') return;

                // Skip if already processed
                const messageId = `${thread.thread_id}_${lastMessage.item_id}`;
                if (processedMessages.has(messageId)) return;
                processedMessages.add(messageId);

                const text = lastMessage.text.trim();
                const trigger = text.toUpperCase();

                // Match keywords
                if (PRODUCTS[trigger]) {
                    const userId = thread.users?.[0]?.pk || thread.thread_id;
                    const destinationUrl = PRODUCTS[trigger];
                    
                    // Generate tracking URL - use Marketing Agent if available, otherwise fallback
                    let trackingUrl;
                    try {
                        if (useMarketingAgent) {
                            trackingUrl = await marketingAgent.createTrackingLink(trigger, destinationUrl, userId.toString(), 'instagram');
                        } else {
                            trackingUrl = await clickTracker.generateTrackingUrl(trigger, destinationUrl, userId.toString());
                        }
                    } catch (error) {
                        console.error(`[!] Tracking URL generation failed, using fallback: ${error.message}`);
                        // Fallback to simple tracker if Marketing Agent fails
                        trackingUrl = await clickTracker.generateTrackingUrl(trigger, destinationUrl, userId.toString());
                    }
                    
                    await ig.realtime.direct.sendText({
                        threadId: thread.thread_id,
                        text: `Here is your link: ${trackingUrl}`
                    });
                    
                    console.log(`[+] Sent tracking link for ${trigger} to user ${userId} (${useMarketingAgent ? 'Marketing Agent' : 'Simple Tracker'})`);
                    return;
                }

                // Verify License
                const licenseMatch = text.match(/[A-Z0-9]{8}-[A-Z0-9]{8}-[A-Z0-9]{8}-[A-Z0-9]{8}/i);
                if (licenseMatch) {
                    const key = licenseMatch[0];
                    // Process products in parallel
                    const verificationPromises = Object.keys(PRODUCTS).map(async (prodName) => {
                        const prodId = process.env[`${prodName}_ID`];
                        if (!prodId) return null;
                        const result = await gumroad.verifyLicense(prodId, key);
                        if (result.success) {
                            return { prodName, key };
                        }
                        return null;
                    });
                    
                    const results = await Promise.all(verificationPromises);
                    const verified = results.find(r => r !== null);
                    
                    if (verified) {
                        const userId = thread.users?.[0]?.pk || thread.thread_id;
                        const downloadUrl = `https://yourdomain.com/download/${verified.key}`;
                        
                        // Generate tracking URL for download link
                        let trackingUrl;
                        try {
                            if (useMarketingAgent) {
                                trackingUrl = await marketingAgent.createTrackingLink(`${verified.prodName}_DOWNLOAD`, downloadUrl, userId.toString(), 'instagram');
                            } else {
                                trackingUrl = await clickTracker.generateTrackingUrl(`${verified.prodName}_DOWNLOAD`, downloadUrl, userId.toString());
                            }
                        } catch (error) {
                            console.error(`[!] Tracking URL generation failed, using fallback: ${error.message}`);
                            trackingUrl = await clickTracker.generateTrackingUrl(`${verified.prodName}_DOWNLOAD`, downloadUrl, userId.toString());
                        }
                        
                        await ig.realtime.direct.sendText({
                            threadId: thread.thread_id,
                            text: `✅ Verified! Access: ${trackingUrl}`
                        });
                        
                        console.log(`[+] Sent verified download link for ${verified.prodName} to user ${userId}`);
                    }
                }
            }));
        }
        
        // Cleanup old processed messages (older than TTL)
        const now = Date.now();
        if (processedMessages.size > 1000) {
            // Simple cleanup - in production, use a proper TTL cache
            const keysToDelete = Array.from(processedMessages).slice(0, 100);
            keysToDelete.forEach(key => processedMessages.delete(key));
        }
    } catch (e) {
        console.error(`[!] DM Error: ${e.message}`);
    }
}

// Track posted videos to prevent duplicates
const postedVideos = new Set();
const POSTED_VIDEOS_FILE = path.join(__dirname, 'logs', 'posted_videos.json');

// Load previously posted videos
async function loadPostedVideos() {
    try {
        // Load from JSON file
        if (await fs.pathExists(POSTED_VIDEOS_FILE)) {
            const data = await fs.readJson(POSTED_VIDEOS_FILE);
            data.forEach(video => postedVideos.add(video));
        }
        
        // Also load from processed directory (videos that were already posted)
        const processedDir = path.join(__dirname, 'logs/processed');
        if (await fs.pathExists(processedDir)) {
            const processedFiles = (await fs.readdir(processedDir).catch(() => []))
                .filter(f => f.endsWith('.mp4'))
                .map(f => {
                    // Extract original filename (remove _processed suffix if present)
                    return f.replace(/_processed\.mp4$/, '.mp4');
                });
            processedFiles.forEach(video => postedVideos.add(video));
        }
        
        if (postedVideos.size > 0) {
            console.log(`[+] Loaded ${postedVideos.size} previously posted videos (duplicates will be skipped)`);
        }
    } catch (error) {
        console.warn(`[!] Could not load posted videos history: ${error.message}`);
    }
}

// Save posted videos to file
async function savePostedVideo(videoName) {
    postedVideos.add(videoName);
    try {
        await fs.ensureDir(path.dirname(POSTED_VIDEOS_FILE));
        await fs.writeJson(POSTED_VIDEOS_FILE, Array.from(postedVideos), { spaces: 2 });
    } catch (error) {
        console.warn(`[!] Could not save posted videos history: ${error.message}`);
    }
}

async function postNextReel() {
    try {
        // Verify we're still logged in before attempting to post
        try {
            await ig.account.currentUser();
        } catch (authError) {
            if (authError.message && (authError.message.includes('challenge_required') || authError.message.includes('login_required'))) {
                console.error(`[!!] Authentication Error: ${authError.message}`);
                console.error(`[!!] Instagram requires a security challenge. Please verify the account manually.`);
                throw new Error('INSTAGRAM_CHALLENGE_REQUIRED');
            }
            throw authError;
        }
        
        const strategy = await optimizer.analyzeAndPivot(ig);
        const queueDir = path.join(__dirname, 'queue');
        const files = (await fs.readdir(queueDir).catch(() => [])).filter(f => f.endsWith('.mp4'));

        if (files.length === 0) {
            console.log("[!] Queue empty. Waiting for next window.");
            // Return 4 hours minimum
            return Math.max(strategy.currentInterval, 4 * 60 * 60 * 1000);
        }

        // Filter out already posted videos
        const availableFiles = files.filter(f => !postedVideos.has(f));
        
        if (availableFiles.length === 0) {
            console.log("[!] All videos in queue have already been posted. Waiting for new videos.");
            console.log(`[!] Posted videos count: ${postedVideos.size}`);
            // Return 4 hours minimum
            return Math.max(strategy.currentInterval, 4 * 60 * 60 * 1000);
        }

        console.log(`[+] Found ${availableFiles.length} new videos (${files.length - availableFiles.length} already posted)`);
        
        // Select first available video (or random if you prefer)
        const videoName = availableFiles[0];
        const videoPath = path.join(queueDir, videoName);
        const coverPath = path.join(__dirname, `temp_cover_${Date.now()}.jpg`);
        
        console.log(`[*] Processing video: ${videoName}`);

        let coverBuffer;
        let videoBuffer;

        try {
        videoBuffer = await fs.readFile(videoPath);
        
        // Try to extract cover with ffmpeg (async for better performance)
        try {
            console.log(`[*] Extracting cover frame...`);
            
            // Run ffmpeg asynchronously
            await execAsync(`ffmpeg -y -i "${videoPath}" -ss 00:00:01 -vframes 1 "${coverPath}" -loglevel error`);
            
            if (await fs.pathExists(coverPath)) {
                // Process image in parallel with video read
                coverBuffer = await sharp(coverPath)
                    .resize(1080, 1920, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 1 } })
                    .jpeg({ quality: 90 }) // Optimize quality
                    .toBuffer();
                await fs.unlink(coverPath).catch(() => {});
                console.log(`[+] Cover extracted successfully.`);
            } else {
                throw new Error("ffmpeg finished but cover file not found");
            }
        } catch (ffmpegErr) {
            console.warn(`[!] ffmpeg failed or not found, using fallback image: ${ffmpegErr.message}`);
            const fallbackPath = path.join(__dirname, 'upload/image.png');
            if (await fs.pathExists(fallbackPath)) {
                coverBuffer = await sharp(fallbackPath)
                    .resize(1080, 1920, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 1 } })
                    .jpeg({ quality: 90 })
                    .toBuffer();
            } else {
                console.error("[!!] Fallback image missing! Using empty buffer.");
                coverBuffer = Buffer.alloc(0);
            }
        }

        const baseCaptions = [
            "Automate your income. Check link in bio.",
            "Stop trading time for money.",
            "The digital revolution is here."
        ];
        const caption = `${baseCaptions[Math.floor(Math.random() * baseCaptions.length)]} ${strategy.activeHashtags.join(' ')}`;

        const intervalHours = Math.max(strategy.currentInterval, 4 * 60 * 60 * 1000) / (60 * 60 * 1000);
        console.log(`[*] Posting Reel (next post in ${intervalHours.toFixed(2)}h - minimum 4h interval)...`);
        const result = await ig.publish.video({
            video: videoBuffer,
            coverImage: coverBuffer,
            caption: caption
        });
        
        await optimizer.logActivity(result.media.id, caption);
        
        // Mark video as posted to prevent duplicates
        await savePostedVideo(videoName);
        console.log(`[+] Video marked as posted: ${videoName} (will never be posted again)`);
        
        // Move to processed directory
        const processedDir = path.join(__dirname, 'logs/processed');
        await fs.ensureDir(processedDir);
        await fs.move(videoPath, path.join(processedDir, videoName));
        console.log(`[+] Post success: ${result.media.id}`);

        } catch (e) {
            console.error(`[!] Detailed Post error: ${e.stack || e.message}`);
            if (e.message.includes('unsupported image format')) {
                console.error(`[!] Sharp error detected. Check if the input file is a valid image/video.`);
            }
            if (e.message && (e.message.includes('challenge_required') || e.message.includes('login_required'))) {
                console.error(`[!!] CRITICAL: Instagram challenge required - automation paused`);
                console.error(`[!!] Please verify the account manually, then restart the automation`);
                // Return longer interval to avoid spamming
                return 24 * 60 * 60 * 1000; // 24 hours
            }
            // Don't mark as posted if upload failed
            console.log(`[!] Video ${videoName} will be retried (not marked as posted)`);
        }

        // Always return minimum 4-hour interval
        return Math.max(strategy.currentInterval, 4 * 60 * 60 * 1000);
    } catch (outerError) {
        console.error(`[!!] Fatal error in postNextReel: ${outerError.message}`);
        if (outerError.message === 'INSTAGRAM_CHALLENGE_REQUIRED' || (outerError.message && outerError.message.includes('challenge_required'))) {
            console.error(`[!!] Instagram Challenge Required - Please verify account manually`);
            return 24 * 60 * 60 * 1000; // 24 hours
        }
        return 4 * 60 * 60 * 1000; // Default 4 hours
    }
}

async function scheduler() {
    try {
        const nextInterval = await postNextReel();
        // Ensure minimum 4-hour interval
        const minInterval = 4 * 60 * 60 * 1000; // 4 hours
        const actualInterval = Math.max(nextInterval, minInterval);
        const hours = (actualInterval / (60 * 60 * 1000)).toFixed(2);
        console.log(`[Scheduler] Next post in ${hours} hours (minimum 4 hours)`);
        setTimeout(scheduler, actualInterval);
    } catch (error) {
        console.error(`[!] Scheduler Error: ${error.message}`);
        console.error(`[!] Stack: ${error.stack}`);
        // Retry after 4 hours if scheduler fails (maintain interval)
        console.log(`[Scheduler] Retrying in 4 hours...`);
        setTimeout(scheduler, 4 * 60 * 60 * 1000);
    }
}

async function main() {
    try {
        console.log('[+] Starting Instagram Automation Engine...');
        
        // Load posted videos history to prevent duplicates
        await loadPostedVideos();
        
        const accounts = await fs.readJson(path.join(__dirname, 'accounts.json'));
        const activeAccount = accounts[0];
        
        console.log(`[+] Logging in as ${activeAccount.username}...`);
        await login(activeAccount);
        console.log('[+] Login successful!');
        
        // Verify login by checking current user
        try {
            const currentUser = await ig.account.currentUser();
            console.log(`[+] Verified login: ${currentUser.username} (${currentUser.full_name || 'No name'})`);
        } catch (verifyError) {
            if (verifyError.message && verifyError.message.includes('challenge_required')) {
                console.error(`[!!] CRITICAL: Instagram Challenge Required!`);
                console.error(`[!!] The account needs manual verification.`);
                console.error(`[!!] Please:`);
                console.error(`[!!]   1. Log into Instagram manually`);
                console.error(`[!!]   2. Complete any security challenges`);
                console.error(`[!!]   3. Restart the automation`);
                throw new Error('INSTAGRAM_CHALLENGE_REQUIRED');
            }
            throw verifyError;
        }

        // Initial check
        console.log('[+] Performing initial DM check...');
        await handleDMs();
        
        // Set periodic DM checks (optimized: 5 mins for better responsiveness)
        setInterval(handleDMs, 5 * 60 * 1000); // 5 mins
        console.log('[+] DM checker started (every 5 minutes)');
        
        // Start adaptive scheduler for posting
        console.log('[+] Starting post scheduler...');
        await scheduler();
    } catch (error) {
        console.error(`[!!] Fatal Error in main(): ${error.message}`);
        console.error(`[!!] Stack: ${error.stack}`);
        console.log('[!] Restarting in 5 minutes...');
        setTimeout(main, 5 * 60 * 1000);
    }
}

main().catch(console.error);
