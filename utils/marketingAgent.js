const axios = require('axios');

/**
 * Marketing Agent V2 API Client
 * Integrates with the Python FastAPI marketing agent for advanced link tracking
 */
class MarketingAgent {
    constructor(baseUrl = process.env.MARKETING_AGENT_URL || 'http://localhost:9000') {
        this.baseUrl = baseUrl;
        this.apiUrl = `${baseUrl}/api`;
    }

    /**
     * Check if the marketing agent is available
     */
    async isAvailable() {
        try {
            const response = await axios.get(`${this.baseUrl}/healthz`, { timeout: 5000 });
            return response.data.status === 'healthy';
        } catch (error) {
            console.error(`[Marketing Agent] Health check failed: ${error.message}`);
            return false;
        }
    }

    /**
     * Get or create a campaign for a platform
     * @param {string} platform - Platform name (instagram, tiktok, etc.)
     */
    async getOrCreateCampaign(platform = 'instagram') {
        try {
            const platformName = platform.charAt(0).toUpperCase() + platform.slice(1);
            
            // Try to find existing campaign
            const campaigns = await axios.get(`${this.apiUrl}/campaigns`);
            const existingCampaign = campaigns.data.find(
                c => c.name.toLowerCase().includes(platform.toLowerCase()) && c.status === 'active'
            );

            if (existingCampaign) {
                return existingCampaign;
            }

            // Create new campaign
            const now = new Date();
            const endDate = new Date(now);
            endDate.setFullYear(endDate.getFullYear() + 1);

            const newCampaign = await axios.post(`${this.apiUrl}/campaigns`, {
                name: `${platformName} Automation`,
                objective: `Track clicks from ${platformName} DMs and posts`,
                start_date: now.toISOString(),
                end_date: endDate.toISOString(),
                status: 'active'
            });

            return newCampaign.data;
        } catch (error) {
            console.error(`[!] Marketing Agent Error (getOrCreateCampaign): ${error.message}`);
            throw error;
        }
    }

    /**
     * Get or create a campaign for Instagram (backward compatibility)
     */
    async getOrCreateInstagramCampaign() {
        return this.getOrCreateCampaign('instagram');
    }

    /**
     * Create a tracked link for a product
     * @param {string} productName - Product name
     * @param {string} destinationUrl - Final Gumroad URL
     * @param {string} userId - User ID (optional)
     * @param {string} platform - Platform name (instagram, tiktok, etc.)
     * @returns {Promise<string>} Short tracking URL
     */
    async createTrackingLink(productName, destinationUrl, userId = null, platform = 'instagram') {
        try {
            // Get or create campaign for platform
            const campaign = await this.getOrCreateCampaign(platform);

            // Create tracked link
            const link = await axios.post(`${this.apiUrl}/links`, {
                campaign_id: campaign.id,
                channel: `${platform}_dm`,
                long_url: destinationUrl,
                utm_json: {
                    utm_source: platform,
                    utm_medium: 'dm',
                    utm_campaign: productName.toLowerCase().replace(/\s+/g, '_'),
                    utm_content: userId || 'unknown'
                }
            });

            // Generate short URL
            const shortUrl = `${this.baseUrl}/r/${link.data.short_slug}`;
            
            console.log(`[Marketing Agent] Created ${platform} tracking link for ${productName}: ${link.data.short_slug}`);
            return shortUrl;
        } catch (error) {
            console.error(`[!] Marketing Agent Error (createTrackingLink): ${error.message}`);
            throw error;
        }
    }

    /**
     * Get link statistics
     * @param {number} linkId - Link ID
     * @param {number} days - Number of days to look back
     * @returns {Promise<Object>} Statistics
     */
    async getLinkStats(linkId, days = 30) {
        try {
            const response = await axios.get(`${this.apiUrl}/links/${linkId}/stats?days=${days}`);
            return response.data;
        } catch (error) {
            console.error(`[!] Marketing Agent Error (getLinkStats): ${error.message}`);
            return null;
        }
    }

    /**
     * Get all links for a campaign
     * @param {number} campaignId - Campaign ID
     * @returns {Promise<Array>} List of links
     */
    async getCampaignLinks(campaignId) {
        try {
            const response = await axios.get(`${this.apiUrl}/links?campaign_id=${campaignId}`);
            return response.data;
        } catch (error) {
            console.error(`[!] Marketing Agent Error (getCampaignLinks): ${error.message}`);
            return [];
        }
    }

    /**
     * Get overall campaign statistics
     * @returns {Promise<Object>} Campaign stats
     */
    async getCampaignStats() {
        try {
            const campaign = await this.getOrCreateInstagramCampaign();
            const links = await this.getCampaignLinks(campaign.id);

            let totalClicks = 0;
            let totalBots = 0;
            const productStats = {};

            for (const link of links) {
                const stats = await this.getLinkStats(link.id, 30);
                if (stats) {
                    totalClicks += stats.total_clicks;
                    totalBots += stats.total_bots;
                    
                    const productName = link.utm_json?.utm_campaign || 'unknown';
                    productStats[productName] = (productStats[productName] || 0) + stats.total_clicks;
                }
            }

            return {
                campaign: campaign.name,
                totalLinks: links.length,
                totalClicks,
                totalBots,
                uniqueClicks: totalClicks - totalBots,
                productStats
            };
        } catch (error) {
            console.error(`[!] Marketing Agent Error (getCampaignStats): ${error.message}`);
            return null;
        }
    }
}

module.exports = MarketingAgent;
