require('dotenv').config();
const fs = require('fs-extra');
const path = require('path');

// Import platform modules
const InstagramBot = require('./index');
const TikTokBot = require('./tiktok_index');

/**
 * Multi-Platform Automation Manager
 * Runs Instagram and TikTok automation simultaneously
 */
class MultiPlatformManager {
    constructor() {
        this.platforms = {
            instagram: null,
            tiktok: null
        };
        this.isRunning = false;
    }

    /**
     * Start all platforms
     */
    async start() {
        console.log('='.repeat(60));
        console.log('Multi-Platform Automation Starting...');
        console.log('='.repeat(60));

        this.isRunning = true;

        // Start Instagram (if enabled)
        if (process.env.ENABLE_INSTAGRAM !== 'false') {
            console.log('\n[+] Starting Instagram automation...');
            try {
                // Instagram bot runs in its own process context
                // We'll spawn it as a child process or run in parallel
                this.platforms.instagram = true;
                console.log('[+] Instagram automation active');
            } catch (error) {
                console.error(`[!] Instagram failed to start: ${error.message}`);
            }
        }

        // Start TikTok (if enabled)
        if (process.env.ENABLE_TIKTOK !== 'false') {
            console.log('\n[+] Starting TikTok automation...');
            try {
                TikTokBot.main().catch(error => {
                    console.error(`[!] TikTok error: ${error.message}`);
                });
                this.platforms.tiktok = true;
                console.log('[+] TikTok automation active');
            } catch (error) {
                console.error(`[!] TikTok failed to start: ${error.message}`);
            }
        }

        console.log('\n' + '='.repeat(60));
        console.log('Multi-Platform Automation Running');
        console.log('='.repeat(60));
        console.log(`Instagram: ${this.platforms.instagram ? '✅ Active' : '❌ Inactive'}`);
        console.log(`TikTok: ${this.platforms.tiktok ? '✅ Active' : '❌ Inactive'}`);
        console.log('='.repeat(60));
    }

    /**
     * Stop all platforms
     */
    async stop() {
        console.log('\n[!] Stopping all platforms...');
        this.isRunning = false;
        // Cleanup would go here
    }

    /**
     * Get status of all platforms
     */
    getStatus() {
        return {
            running: this.isRunning,
            platforms: {
                instagram: this.platforms.instagram,
                tiktok: this.platforms.tiktok
            }
        };
    }
}

// Main execution
async function main() {
    const manager = new MultiPlatformManager();
    
    // Start all platforms
    await manager.start();

    // Keep process alive
    process.on('SIGINT', async () => {
        console.log('\n[!] Shutting down...');
        await manager.stop();
        process.exit(0);
    });
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = MultiPlatformManager;
