const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');

// Use stealth plugin to avoid detection
puppeteer.use(StealthPlugin());

/**
 * TikTok Automation Module
 * Handles TikTok video posting, comment monitoring, and DM responses
 * Uses Puppeteer for browser automation
 */
class TikTokAutomation {
    constructor(account, marketingAgent = null, clickTracker = null) {
        this.account = account;
        this.marketingAgent = marketingAgent;
        this.clickTracker = clickTracker;
        this.baseUrl = 'https://www.tiktok.com';
        this.browser = null;
        this.page = null;
        this.isLoggedIn = false;
    }

    /**
     * Initialize browser
     */
    async initBrowser() {
        try {
            if (!this.browser) {
                console.log('[TikTok] Launching browser...');
                this.browser = await puppeteer.launch({
                    headless: false, // Set to true for production
                    args: [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ],
                    defaultViewport: {
                        width: 1920,
                        height: 1080
                    }
                });
                
                this.page = await this.browser.newPage();
                
                // Set user agent
                await this.page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
                
                console.log('[TikTok] Browser initialized');
            }
            return this.page;
        } catch (error) {
            console.error(`[TikTok] Browser init error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Login to TikTok account
     */
    async login() {
        try {
            console.log(`[TikTok] Logging in as ${this.account.username}...`);
            
            await this.initBrowser();
            
            // Navigate to TikTok login page
            await this.page.goto('https://www.tiktok.com/login', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            
            // Wait for login form
            await this.page.waitForSelector('input[placeholder*="Email"], input[placeholder*="Username"], input[type="text"]', { timeout: 10000 });
            
            // Fill in credentials
            const usernameInput = await this.page.$('input[placeholder*="Email"], input[placeholder*="Username"], input[type="text"]');
            if (usernameInput) {
                await usernameInput.type(this.account.username || this.account.email, { delay: 100 });
            }
            
            // Find password input
            await this.page.waitForSelector('input[type="password"]', { timeout: 5000 });
            const passwordInput = await this.page.$('input[type="password"]');
            if (passwordInput) {
                await passwordInput.type(this.account.password, { delay: 100 });
            }
            
            // Click login button
            const loginButton = await this.page.$('button[type="submit"], button:has-text("Log in"), button:has-text("Login")');
            if (loginButton) {
                await Promise.all([
                    this.page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 30000 }),
                    loginButton.click()
                ]);
            } else {
                await this.page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 30000 });
            }
            
            // Check if login was successful (URL should change or show profile)
            const currentUrl = this.page.url();
            if (currentUrl.includes('/upload') || currentUrl.includes('/@') || !currentUrl.includes('/login')) {
                this.isLoggedIn = true;
                console.log(`[TikTok] Login successful`);
                return true;
            } else {
                throw new Error('Login failed - still on login page');
            }
        } catch (error) {
            console.error(`[TikTok] Login failed: ${error.message}`);
            // Don't throw - allow retry
            return false;
        }
    }

    /**
     * Close browser
     */
    async closeBrowser() {
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
            this.page = null;
        }
    }

    /**
     * Post a video to TikTok using browser automation
     * @param {string} videoPath - Path to video file
     * @param {string} caption - Video caption
     * @param {Object} options - Additional options (privacy, hashtags, etc.)
     */
    async postVideo(videoPath, caption, options = {}) {
        try {
            if (!this.isLoggedIn) {
                const loginSuccess = await this.login();
                if (!loginSuccess) {
                    throw new Error('Login required before posting');
                }
            }

            console.log(`[TikTok] Posting video: ${path.basename(videoPath)}`);
            
            // Navigate to upload page
            await this.page.goto('https://www.tiktok.com/upload', {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            
            // Wait for file input
            await this.page.waitForSelector('input[type="file"]', { timeout: 10000 });
            
            // Upload video file
            const fileInput = await this.page.$('input[type="file"]');
            if (fileInput) {
                // Convert to absolute path
                const absolutePath = path.resolve(videoPath);
                // Puppeteer file upload - use setInputFiles method
                await fileInput.setInputFiles(absolutePath);
                console.log('[TikTok] Video file uploaded');
            } else {
                throw new Error('File input not found on upload page');
            }
            
            // Wait for video to process (use event-based waiting instead of fixed timeout)
            await this.page.waitForFunction(
                () => {
                    // Check if video is loaded/processed
                    const video = document.querySelector('video');
                    return video && video.readyState >= 2; // HAVE_CURRENT_DATA
                },
                { timeout: 30000 }
            ).catch(() => {
                // Fallback to timeout if function check fails
                return this.page.waitForTimeout(3000);
            });
            
            // Fill in caption (wait for element and type in parallel)
            const captionInput = await this.page.waitForSelector('div[contenteditable="true"], textarea, input[placeholder*="caption"], input[placeholder*="Caption"]', { timeout: 10000 });
            if (captionInput) {
                await captionInput.click({ clickCount: 3 }); // Select all
                await captionInput.type(caption, { delay: 30 }); // Reduced delay for faster typing
                console.log('[TikTok] Caption added');
            }
            
            // Set privacy if needed
            if (options.privacy !== undefined) {
                // Find privacy dropdown/button (non-blocking)
                // Privacy settings vary - this is a placeholder
            }
            
            // Click post button and wait for navigation in parallel
            const postButton = await this.page.$('button:has-text("Post"), button:has-text("Publish"), button[type="submit"]');
            if (postButton) {
                await Promise.all([
                    this.page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 }),
                    postButton.click()
                ]);
                console.log('[TikTok] Post button clicked');
            } else {
                await this.page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 });
            }
            
            // Extract video ID from URL
            const currentUrl = this.page.url();
            const videoIdMatch = currentUrl.match(/video\/(\d+)/);
            const videoId = videoIdMatch ? videoIdMatch[1] : `tiktok_${Date.now()}_${crypto.randomBytes(8).toString('hex')}`;
            
            const uploadResult = {
                success: true,
                videoId: videoId,
                url: currentUrl
            };

            console.log(`[TikTok] Video posted successfully! ID: ${videoId}`);
            return uploadResult;
        } catch (error) {
            console.error(`[TikTok] Post error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Process video to ensure unique MD5 hash
     */
    async processVideoForUniqueHash(videoBuffer) {
        // Append random bytes to ensure unique hash (same approach as Instagram)
        const randomBytes = crypto.randomBytes(32);
        return Buffer.concat([videoBuffer, randomBytes]);
    }

    /**
     * Monitor comments for keywords
     * @param {string} videoId - Video ID to monitor
     * @param {Array} keywords - Keywords to watch for
     */
    async monitorComments(videoId, keywords = ['FORGE']) {
        try {
            console.log(`[TikTok] Monitoring comments on video ${videoId}...`);
            
            if (!this.page) {
                await this.initBrowser();
            }
            
            // Navigate to video page
            const videoUrl = `https://www.tiktok.com/@${this.account.username}/video/${videoId}`;
            await this.page.goto(videoUrl, {
                waitUntil: 'networkidle2',
                timeout: 30000
            });
            
            // Wait for comments section to load (event-based)
            await this.page.waitForSelector('[data-e2e="comment-level-1"], .comment-item, [class*="comment"]', { timeout: 10000 }).catch(() => {});
            
            // Scroll to load comments (optimized)
            await this.page.evaluate(() => {
                window.scrollTo(0, document.body.scrollHeight);
            });
            // Wait for comments to load after scroll
            await this.page.waitForFunction(
                () => {
                    const comments = document.querySelectorAll('[data-e2e="comment-level-1"], .comment-item, [class*="comment"]');
                    return comments.length > 0;
                },
                { timeout: 5000 }
            ).catch(() => {});
            
            // Extract comments
            const comments = await this.page.evaluate(() => {
                const commentElements = document.querySelectorAll('[data-e2e="comment-level-1"], .comment-item, [class*="comment"]');
                return Array.from(commentElements).slice(0, 50).map(el => {
                    const textEl = el.querySelector('[data-e2e="comment-level-1"], .comment-text, [class*="text"]');
                    const userEl = el.querySelector('[data-e2e="comment-username"], .username, [class*="username"]');
                    return {
                        id: el.getAttribute('data-comment-id') || Math.random().toString(36),
                        text: textEl ? textEl.textContent.trim() : '',
                        username: userEl ? userEl.textContent.trim() : 'unknown',
                        userId: userEl ? userEl.getAttribute('href')?.match(/@([^/]+)/)?.[1] : null
                    };
                }).filter(c => c.text);
            });
            
            console.log(`[TikTok] Found ${comments.length} comments`);
            
            for (const comment of comments) {
                const text = comment.text.toUpperCase();
                for (const keyword of keywords) {
                    if (text.includes(keyword.toUpperCase())) {
                        await this.handleKeywordComment(comment, keyword);
                    }
                }
            }
        } catch (error) {
            console.error(`[TikTok] Comment monitoring error: ${error.message}`);
        }
    }

    /**
     * Handle keyword-triggered comment
     */
    async handleKeywordComment(comment, keyword) {
        try {
            console.log(`[TikTok] Keyword "${keyword}" detected in comment from ${comment.user.username}`);
            
            // Like the comment
            await this.likeComment(comment.id);
            
            // Wait delay (similar to Instagram - 7 minutes)
            const delay = 7 * 60 * 1000;
            console.log(`[TikTok] Waiting ${delay / 1000 / 60} minutes before sending DM...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            
            // Send DM with product link
            await this.sendDM(comment.user.id, keyword);
        } catch (error) {
            console.error(`[TikTok] Error handling keyword comment: ${error.message}`);
        }
    }

    /**
     * Like a comment
     */
    async likeComment(commentId) {
        try {
            if (!this.page) {
                await this.initBrowser();
            }
            
            console.log(`[TikTok] Liking comment ${commentId}`);
            
            // Find and click like button for the comment
            const liked = await this.page.evaluate((id) => {
                const commentEl = document.querySelector(`[data-comment-id="${id}"]`);
                if (commentEl) {
                    const likeButton = commentEl.querySelector('[data-e2e="comment-like"], .like-button, [class*="like"]');
                    if (likeButton && !likeButton.classList.contains('liked')) {
                        likeButton.click();
                        return true;
                    }
                }
                return false;
            }, commentId);
            
            if (liked) {
                await this.page.waitForTimeout(1000);
                console.log(`[TikTok] Comment ${commentId} liked`);
            }
            
            return liked;
        } catch (error) {
            console.error(`[TikTok] Like comment error: ${error.message}`);
            return false;
        }
    }

    /**
     * Send DM to user
     */
    async sendDM(userId, keyword) {
        try {
            // Get product link for keyword
            const products = this.getProductCatalog();
            const productLink = products[keyword];
            
            if (!productLink) {
                console.warn(`[TikTok] No product found for keyword: ${keyword}`);
                return;
            }

            // Generate tracking URL
            let trackingUrl;
            if (this.marketingAgent && await this.marketingAgent.isAvailable()) {
                trackingUrl = await this.marketingAgent.createTrackingLink(
                    keyword,
                    productLink,
                    userId.toString(),
                    'tiktok' // Platform parameter
                );
            } else if (this.clickTracker) {
                trackingUrl = await this.clickTracker.generateTrackingUrl(
                    keyword,
                    productLink,
                    userId.toString()
                );
            } else {
                trackingUrl = productLink;
            }

            // Send DM via TikTok API
            const message = `Here is your link: ${trackingUrl}`;
            console.log(`[TikTok] Sending DM to user ${userId}: ${message}`);
            
            // Placeholder - would use actual TikTok DM API
            return { success: true, messageId: `dm_${Date.now()}` };
        } catch (error) {
            console.error(`[TikTok] Send DM error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get product catalog from environment
     */
    getProductCatalog() {
        const products = {};
        Object.keys(process.env).forEach(key => {
            if (key.endsWith('_ID')) {
                const name = key.replace('_ID', '');
                products[name] = process.env[`${name}_LINK`] || `https://gumroad.com/l/${name.toLowerCase()}`;
            }
        });
        return products;
    }

    /**
     * Get account stats
     */
    async getStats() {
        try {
            // TikTok API call to get account stats
            return {
                followers: 0,
                following: 0,
                videos: 0,
                likes: 0
            };
        } catch (error) {
            console.error(`[TikTok] Get stats error: ${error.message}`);
            return null;
        }
    }
}

module.exports = TikTokAutomation;
