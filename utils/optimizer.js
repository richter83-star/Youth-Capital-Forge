const fs = require('fs-extra');
const path = require('path');
const Gumroad = require('./gumroad');

const LOG_FILE = path.join(__dirname, '../logs/activity.json');
const STATE_FILE = path.join(__dirname, '../logs/state.json');

class Optimizer {
    constructor(gumroadToken) {
        this.gumroad = new Gumroad(gumroadToken);
        this.minInterval = 2 * 60 * 60 * 1000; // 2 hours
        this.maxInterval = 12 * 60 * 60 * 1000; // 12 hours
    }

    async getStats() {
        const salesData = await this.gumroad.getSales();
        const activity = await fs.readJson(LOG_FILE).catch(() => []);
        
        return {
            salesCount: (salesData && salesData.sales) ? salesData.sales.length : 0,
            postCount: activity.length,
            lastPost: activity[activity.length - 1]
        };
    }

    /**
     * Decisions on whether to pivot
     * Returns an object with recommended settings
     */
    async analyzeAndPivot(igClient) {
        console.log("[*] Optimizer: Analyzing ROI...");
        
        const state = await fs.readJson(STATE_FILE).catch(() => ({
            currentInterval: 4 * 60 * 60 * 1000,
            activeHashtags: ["#wealth", "#ai", "#success"],
            performanceHistory: []
        }));

        const stats = await this.getStats();
        
        // Pivot Logic:
        // if postCount > 3 and sales are still 0, move the interval up (slow down) to preserve accounts
        // and rotate hashtags to find new audience.
        if (stats.postCount > 3 && stats.salesCount === 0) {
            console.log("[!] LOW ROI DETECTED. Pivoting strategy...");
            state.currentInterval = Math.min(state.currentInterval + (1 * 60 * 60 * 1000), this.maxInterval);
            state.activeHashtags = this.rotateHashtags(state.activeHashtags);
        } else if (stats.salesCount > 0) {
            console.log("[+] POSITIVE ROI. Scaling up carefully.");
            state.currentInterval = Math.max(state.currentInterval - (30 * 60 * 1000), this.minInterval);
        }

        await fs.writeJson(STATE_FILE, state, { spaces: 2 });
        return state;
    }

    rotateHashtags(current) {
        const buckets = [
            ["#fintech", "#ecommerce", "#dropshipping"],
            ["#nocode", "#automation", "#builders"],
            ["#career", "#growth", "#productivity"],
            ["#wealth", "#ai", "#success"]
        ];
        const nextIdx = (buckets.findIndex(b => b[0] === current[0]) + 1) % buckets.length;
        return buckets[nextIdx];
    }

    async logActivity(mediaId, caption) {
        const activity = await fs.readJson(LOG_FILE).catch(() => []);
        activity.push({
            timestamp: new Date().toISOString(),
            mediaId,
            caption
        });
        // Keep only last 20 entries to save space
        if (activity.length > 20) activity.shift();
        await fs.ensureDir(path.dirname(LOG_FILE));
        await fs.writeJson(LOG_FILE, activity);
    }
}

module.exports = Optimizer;
