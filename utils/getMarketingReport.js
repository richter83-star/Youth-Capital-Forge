require('dotenv').config();
const MarketingAgent = require('./marketingAgent');

/**
 * Generate Marketing Agent V2 Report
 */
async function generateReport() {
    const marketingAgent = new MarketingAgent(process.env.MARKETING_AGENT_URL || 'http://localhost:8000');
    
    const fs = require('fs-extra');
    const path = require('path');
    
    console.log('='.repeat(60));
    console.log('📊 MARKETING AGENT V2 - PERFORMANCE REPORT');
    console.log('='.repeat(60));
    console.log('');
    
    // Check if Marketing Agent is available
    const isAvailable = await marketingAgent.isAvailable();
    if (!isAvailable) {
        console.log('⚠️  Marketing Agent V2 is not running');
        console.log(`   URL: ${marketingAgent.baseUrl}`);
        console.log('');
        console.log('📋 FALLBACK: Showing local log data...');
        console.log('-'.repeat(60));
        
        // Show local click logs
        try {
            const clicksPath = path.join(__dirname, '../logs/clicks/clicks.json');
            if (await fs.pathExists(clicksPath)) {
                const clicks = await fs.readJson(clicksPath);
                console.log(`Total Clicks Logged: ${clicks.length || 0}`);
                
                if (clicks.length > 0) {
                    // Group by product
                    const productStats = {};
                    clicks.forEach(click => {
                        const product = click.productName || click.product || 'Unknown';
                        productStats[product] = (productStats[product] || 0) + 1;
                    });
                    
                    console.log('');
                    console.log('📦 Clicks by Product:');
                    Object.entries(productStats)
                        .sort((a, b) => b[1] - a[1])
                        .forEach(([product, count]) => {
                            console.log(`  ${product}: ${count} clicks`);
                        });
                    
                    console.log('');
                    console.log('🕐 Recent Clicks (Last 10):');
                    clicks.slice(-10).reverse().forEach((click, idx) => {
                        const product = click.productName || click.product || 'Unknown';
                        const time = click.timestamp ? new Date(click.timestamp).toLocaleString() : 'N/A';
                        console.log(`  ${idx + 1}. ${product} - ${time}`);
                    });
                }
            }
        } catch (error) {
            console.log('No click logs found');
        }
        
        // Show activity logs
        try {
            const activityPath = path.join(__dirname, '../logs/activity.json');
            if (await fs.pathExists(activityPath)) {
                const activity = await fs.readJson(activityPath);
                console.log('');
                console.log(`Total Posts: ${activity.length || 0}`);
                if (activity.length > 0) {
                    console.log('');
                    console.log('Recent Posts:');
                    activity.slice(-5).forEach((post, idx) => {
                        console.log(`  ${idx + 1}. ${post.timestamp || 'N/A'} - ${post.mediaId || 'N/A'}`);
                    });
                }
            }
        } catch (error) {
            console.log('No activity logs found');
        }
        
        console.log('');
        console.log('='.repeat(60));
        console.log('🚀 TO GET FULL REPORTS:');
        console.log('='.repeat(60));
        console.log('');
        console.log('Start Marketing Agent V2:');
        console.log('  cd marketing_agent_v2');
        console.log('  docker-compose up -d');
        console.log('');
        console.log('Then run this report again:');
        console.log('  npm run report');
        console.log('');
        console.log('Or access the Admin Dashboard:');
        console.log(`  ${marketingAgent.baseUrl}/admin`);
        console.log('');
        return;
    }
    
    console.log('✅ Marketing Agent V2 is connected');
    console.log(`   URL: ${marketingAgent.baseUrl}`);
    console.log('');
    
    try {
        // Get Instagram campaign stats
        console.log('📈 INSTAGRAM CAMPAIGN STATISTICS');
        console.log('-'.repeat(60));
        const instagramStats = await marketingAgent.getCampaignStats();
        
        if (instagramStats) {
            console.log(`Campaign: ${instagramStats.campaign}`);
            console.log(`Total Links: ${instagramStats.totalLinks}`);
            console.log(`Total Clicks: ${instagramStats.totalClicks}`);
            console.log(`Bot Clicks: ${instagramStats.totalBots}`);
            console.log(`Unique Clicks: ${instagramStats.uniqueClicks}`);
            console.log(`Click-Through Rate: ${instagramStats.totalLinks > 0 ? ((instagramStats.uniqueClicks / instagramStats.totalLinks) * 100).toFixed(2) : 0}%`);
            console.log('');
            
            if (Object.keys(instagramStats.productStats).length > 0) {
                console.log('📦 PRODUCT PERFORMANCE:');
                console.log('-'.repeat(60));
                const sortedProducts = Object.entries(instagramStats.productStats)
                    .sort((a, b) => b[1] - a[1]);
                
                sortedProducts.forEach(([product, clicks]) => {
                    console.log(`  ${product}: ${clicks} clicks`);
                });
                console.log('');
            }
        } else {
            console.log('No campaign data available yet.');
            console.log('');
        }
        
        // Get all campaigns
        console.log('🎯 ALL CAMPAIGNS:');
        console.log('-'.repeat(60));
        try {
            const campaigns = await marketingAgent.getOrCreateCampaign('instagram');
            console.log(`Active Campaign: ${campaigns.name}`);
            console.log(`Status: ${campaigns.status}`);
            console.log(`Start Date: ${campaigns.start_date}`);
            console.log(`End Date: ${campaigns.end_date}`);
            console.log('');
            
            // Get campaign links
            const links = await marketingAgent.getCampaignLinks(campaigns.id);
            if (links.length > 0) {
                console.log(`📎 TRACKED LINKS (${links.length}):`);
                console.log('-'.repeat(60));
                for (const link of links.slice(0, 10)) { // Show first 10
                    const stats = await marketingAgent.getLinkStats(link.id, 30);
                    if (stats) {
                        console.log(`  ${link.short_slug}:`);
                        console.log(`    Clicks: ${stats.total_clicks} (${stats.unique_clicks} unique)`);
                        console.log(`    Bots: ${stats.total_bots}`);
                        console.log(`    Channel: ${link.channel}`);
                        console.log('');
                    }
                }
                if (links.length > 10) {
                    console.log(`  ... and ${links.length - 10} more links`);
                    console.log('');
                }
            }
        } catch (error) {
            console.log(`Error fetching campaigns: ${error.message}`);
        }
        
        // Summary
        console.log('='.repeat(60));
        console.log('📊 SUMMARY');
        console.log('='.repeat(60));
        if (instagramStats) {
            console.log(`Total Unique Clicks: ${instagramStats.uniqueClicks}`);
            console.log(`Total Links Created: ${instagramStats.totalLinks}`);
            console.log(`Average Clicks per Link: ${instagramStats.totalLinks > 0 ? (instagramStats.uniqueClicks / instagramStats.totalLinks).toFixed(2) : 0}`);
        }
        console.log('');
        console.log('💡 Access Admin Dashboard:');
        console.log(`   ${marketingAgent.baseUrl}/admin`);
        console.log('');
        
    } catch (error) {
        console.error('❌ Error generating report:', error.message);
        console.error(error.stack);
    }
}

// Run report
generateReport().catch(console.error);
