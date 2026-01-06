const MarketingAgent = require('./marketingAgent');

/**
 * Check Marketing Agent status and display stats
 */
async function checkMarketingAgent() {
    const agent = new MarketingAgent(process.env.MARKETING_AGENT_URL || 'http://localhost:9000');
    
    console.log('='.repeat(60));
    console.log('Marketing Agent V2 Status Check');
    console.log('='.repeat(60));
    
    const isAvailable = await agent.isAvailable();
    
    if (!isAvailable) {
        console.log('\n❌ Marketing Agent V2 is NOT available');
        console.log('   Make sure the service is running:');
        console.log('   cd marketing_agent_v2 && docker-compose up -d');
        console.log('   Or: cd marketing_agent_v2 && make up');
        return;
    }
    
    console.log('\n✅ Marketing Agent V2 is available');
    
    try {
        const stats = await agent.getCampaignStats();
        if (stats) {
            console.log('\n📊 Campaign Statistics:');
            console.log(`   Campaign: ${stats.campaign}`);
            console.log(`   Total Links: ${stats.totalLinks}`);
            console.log(`   Total Clicks: ${stats.totalClicks}`);
            console.log(`   Bot Clicks: ${stats.totalBots}`);
            console.log(`   Unique Clicks: ${stats.uniqueClicks}`);
            
            if (Object.keys(stats.productStats).length > 0) {
                console.log('\n📈 Clicks by Product:');
                Object.entries(stats.productStats).forEach(([product, clicks]) => {
                    console.log(`   ${product}: ${clicks} clicks`);
                });
            }
        }
    } catch (error) {
        console.log(`\n⚠️  Could not fetch stats: ${error.message}`);
    }
    
    console.log('\n' + '='.repeat(60));
}

if (require.main === module) {
    require('dotenv').config();
    checkMarketingAgent().catch(console.error);
}

module.exports = { checkMarketingAgent };
