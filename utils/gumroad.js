const axios = require('axios');

/**
 * Enhanced Gumroad API Client
 * Centralized class for all Gumroad API interactions
 * Autonomous-safe with comprehensive error handling
 */
class Gumroad {
    constructor(accessToken = null) {
        this.accessToken = accessToken || null;
        this.baseUrl = 'https://api.gumroad.com/v2';
    }

    /**
     * Check if access token is valid
     * @returns {boolean}
     */
    hasAccessToken() {
        return !!this.accessToken && this.accessToken !== 'your_gumroad_access_token' && this.accessToken.trim() !== '';
    }

    /**
     * Make authenticated API request
     * @private
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request data
     * @param {boolean} requiresAuth - Whether auth token is required
     * @returns {Promise<Object>}
     */
    async _makeRequest(method, endpoint, data = null, requiresAuth = false) {
        try {
            if (requiresAuth && !this.hasAccessToken()) {
                throw new Error('Access token required for this operation');
            }

            const config = {
                method,
                url: `${this.baseUrl}${endpoint}`,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                if (method === 'GET') {
                    config.params = { ...data, ...(requiresAuth ? { access_token: this.accessToken } : {}) };
                } else {
                    config.data = data;
                }
            } else if (requiresAuth && method === 'GET') {
                config.params = { access_token: this.accessToken };
            }

            const response = await axios(config);
            return { success: true, data: response.data };
        } catch (error) {
            const errorMessage = error.response?.data?.message || error.message || 'Unknown error';
            const statusCode = error.response?.status || null;
            
            console.error(`[!] Gumroad API Error (${endpoint}): ${errorMessage}${statusCode ? ` [${statusCode}]` : ''}`);
            
            return {
                success: false,
                error: errorMessage,
                statusCode,
                data: error.response?.data || null
            };
        }
    }

    /**
     * Verify a license key for a specific product
     * @param {string} productId - The product's ID or permalink
     * @param {string} licenseKey - The license key to verify
     * @param {boolean} incrementUses - Whether to increment usage count
     * @returns {Promise<Object>} Verification result
     */
    async verifyLicense(productId, licenseKey, incrementUses = true) {
        if (!productId || !licenseKey) {
            return { success: false, error: 'Product ID and license key are required' };
        }

        const result = await this._makeRequest('POST', '/licenses/verify', {
            product_id: productId,
            license_key: licenseKey,
            increment_uses_count: incrementUses
        }, false);

        if (!result.success) {
            return { success: false, message: result.error, uses: 0, purchase: null };
        }

        return {
            success: result.data.success || false,
            uses: result.data.uses || 0,
            purchase: result.data.purchase || null,
            message: result.data.message || null
        };
    }

    /**
     * Get all products from Gumroad
     * @returns {Promise<Array>} Array of products
     */
    async getProducts() {
        if (!this.hasAccessToken()) {
            console.warn('[!] Gumroad: Access token missing, returning empty products array');
            return [];
        }

        const result = await this._makeRequest('GET', '/products', null, true);

        if (!result.success) {
            console.error(`[!] Failed to fetch products: ${result.error}`);
            return [];
        }

        // Return products array, defaulting to empty array if not present
        return result.data?.products || [];
    }

    /**
     * Get sales data from Gumroad
     * @param {Object} options - Query options (page, after, before, etc.)
     * @returns {Promise<Object>} Sales data
     */
    async getSales(options = {}) {
        if (!this.hasAccessToken()) {
            console.warn('[!] Gumroad: Access token missing, returning empty sales');
            return { success: false, sales: [] };
        }

        const result = await this._makeRequest('GET', '/sales', options, true);

        if (!result.success) {
            return { success: false, sales: [], error: result.error };
        }

        return {
            success: result.data.success !== false,
            sales: result.data.sales || [],
            ...result.data
        };
    }

    /**
     * Get a specific product by ID
     * @param {string} productId - Product ID
     * @returns {Promise<Object|null>} Product data or null
     */
    async getProduct(productId) {
        if (!this.hasAccessToken()) {
            console.warn('[!] Gumroad: Access token missing');
            return null;
        }

        if (!productId) {
            return null;
        }

        const result = await this._makeRequest('GET', `/products/${productId}`, null, true);

        if (!result.success) {
            return null;
        }

        return result.data.product || null;
    }
}

module.exports = Gumroad;
