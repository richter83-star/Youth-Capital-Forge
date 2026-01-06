const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');

/**
 * Click-through Tracker for Instagram DM Links
 * Tracks clicks and redirects to final destination
 */
class ClickTracker {
    constructor() {
        this.trackingDir = path.join(__dirname, '..', 'logs', 'clicks');
        this.trackingFile = path.join(this.trackingDir, 'clicks.json');
        this.redirectsFile = path.join(this.trackingDir, 'redirects.json');
        this.init();
    }

    async init() {
        await fs.ensureDir(this.trackingDir);
        
        // Initialize tracking files if they don't exist or are invalid
        try {
            if (!(await fs.pathExists(this.trackingFile))) {
                await fs.writeJson(this.trackingFile, []);
            } else {
                // Validate existing file
                await fs.readJson(this.trackingFile);
            }
        } catch (error) {
            await fs.writeJson(this.trackingFile, []);
        }
        
        try {
            if (!(await fs.pathExists(this.redirectsFile))) {
                await fs.writeJson(this.redirectsFile, {});
            } else {
                // Validate existing file
                await fs.readJson(this.redirectsFile);
            }
        } catch (error) {
            await fs.writeJson(this.redirectsFile, {});
        }
    }

    /**
     * Generate a tracking URL for a product link
     * @param {string} productName - Product name/trigger
     * @param {string} destinationUrl - Final Gumroad URL
     * @param {string} userId - Instagram user ID (optional)
     * @returns {Promise<string>} Tracking URL
     */
    async generateTrackingUrl(productName, destinationUrl, userId = null) {
        const trackingId = crypto.randomBytes(16).toString('hex');
        const timestamp = Date.now();
        
        // Store redirect mapping (await to ensure it's saved)
        await this.storeRedirect(trackingId, {
            productName,
            destinationUrl,
            userId,
            timestamp,
            clicked: false
        });

        // Generate tracking URL
        // Use localhost for testing, or set REDIRECT_DOMAIN in .env for production
        const domain = process.env.REDIRECT_DOMAIN || 'http://localhost:3000';
        const trackingUrl = `${domain}/track/${trackingId}`;
        
        console.log(`[Tracker] Generated tracking URL for ${productName}: ${trackingId}`);
        return trackingUrl;
    }

    /**
     * Store redirect mapping
     * @private
     */
    async storeRedirect(trackingId, data) {
        try {
            let redirects = {};
            try {
                redirects = await fs.readJson(this.redirectsFile);
            } catch (error) {
                // File doesn't exist or is invalid, start fresh
                redirects = {};
            }
            redirects[trackingId] = data;
            await fs.writeJson(this.redirectsFile, redirects);
        } catch (error) {
            console.error(`[!] Error storing redirect: ${error.message}`);
        }
    }

    /**
     * Get redirect destination and log click
     * @param {string} trackingId - Tracking ID from URL
     * @param {Object} clickData - Additional click metadata (IP, user-agent, etc.)
     * @returns {Object|null} Redirect data with destination URL
     */
    async getRedirect(trackingId, clickData = {}) {
        try {
            const redirects = await fs.readJson(this.redirectsFile);
            const redirect = redirects[trackingId];

            if (!redirect) {
                console.warn(`[Tracker] Invalid tracking ID: ${trackingId}`);
                return null;
            }

            // Log the click
            await this.logClick(trackingId, redirect, clickData);

            // Mark as clicked
            redirect.clicked = true;
            redirect.clickedAt = new Date().toISOString();
            redirects[trackingId] = redirect;
            await fs.writeJson(this.redirectsFile, redirects);

            return {
                destinationUrl: redirect.destinationUrl,
                productName: redirect.productName,
                timestamp: redirect.timestamp
            };
        } catch (error) {
            console.error(`[!] Error getting redirect: ${error.message}`);
            return null;
        }
    }

    /**
     * Log a click event
     * @private
     */
    async logClick(trackingId, redirect, clickData) {
        try {
            const clicks = await fs.readJson(this.trackingFile);
            clicks.push({
                trackingId,
                productName: redirect.productName,
                destinationUrl: redirect.destinationUrl,
                userId: redirect.userId,
                timestamp: new Date().toISOString(),
                clickData: {
                    ip: clickData.ip || 'unknown',
                    userAgent: clickData.userAgent || 'unknown',
                    referer: clickData.referer || 'instagram'
                }
            });

            // Keep only last 1000 clicks to prevent file bloat
            if (clicks.length > 1000) {
                clicks.shift();
            }

            await fs.writeJson(this.trackingFile, clicks);
            console.log(`[Tracker] Click logged: ${redirect.productName} (ID: ${trackingId})`);
        } catch (error) {
            console.error(`[!] Error logging click: ${error.message}`);
        }
    }

    /**
     * Get click statistics
     * @param {string} productName - Optional product name filter
     * @returns {Object} Statistics
     */
    async getStats(productName = null) {
        try {
            const clicks = await fs.readJson(this.trackingFile);
            const redirects = await fs.readJson(this.redirectsFile);

            let filteredClicks = clicks;
            if (productName) {
                filteredClicks = clicks.filter(c => c.productName === productName);
            }

            const totalClicks = filteredClicks.length;
            const uniqueUsers = new Set(filteredClicks.map(c => c.userId).filter(Boolean)).size;
            const clicksByProduct = {};

            filteredClicks.forEach(click => {
                clicksByProduct[click.productName] = (clicksByProduct[click.productName] || 0) + 1;
            });

            return {
                totalClicks,
                uniqueUsers,
                clicksByProduct,
                totalRedirects: Object.keys(redirects).length,
                clickedRedirects: Object.values(redirects).filter(r => r.clicked).length
            };
        } catch (error) {
            console.error(`[!] Error getting stats: ${error.message}`);
            return { totalClicks: 0, uniqueUsers: 0, clicksByProduct: {} };
        }
    }

    /**
     * Get recent clicks
     * @param {number} limit - Number of recent clicks to return
     * @returns {Array} Recent clicks
     */
    async getRecentClicks(limit = 10) {
        try {
            const clicks = await fs.readJson(this.trackingFile);
            return clicks.slice(-limit).reverse();
        } catch (error) {
            console.error(`[!] Error getting recent clicks: ${error.message}`);
            return [];
        }
    }
}

module.exports = ClickTracker;
