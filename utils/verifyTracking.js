const ClickTracker = require('./clickTracker');

/**
 * Verification script to test and display click tracking stats
 */
async function verifyTracking() {
    const tracker = new ClickTracker();
    
    console.log('='.repeat(60));
    console.log('Click-Through Tracking Verification');
    console.log('='.repeat(60));
    
    // Get statistics
    const stats = await tracker.getStats();
    console.log('\n📊 Overall Statistics:');
    console.log(`  Total Clicks: ${stats.totalClicks}`);
    console.log(`  Unique Users: ${stats.uniqueUsers}`);
    console.log(`  Total Redirects Created: ${stats.totalRedirects}`);
    console.log(`  Redirects Clicked: ${stats.clickedRedirects}`);
    
    if (Object.keys(stats.clicksByProduct).length > 0) {
        console.log('\n📈 Clicks by Product:');
        Object.entries(stats.clicksByProduct).forEach(([product, count]) => {
            console.log(`  ${product}: ${count} clicks`);
        });
    }
    
    // Get recent clicks
    const recentClicks = await tracker.getRecentClicks(10);
    if (recentClicks.length > 0) {
        console.log('\n🕐 Recent Clicks (Last 10):');
        recentClicks.forEach((click, index) => {
            console.log(`  ${index + 1}. ${click.productName} - ${new Date(click.timestamp).toLocaleString()}`);
        });
    } else {
        console.log('\n⚠️  No clicks recorded yet.');
        console.log('   Send a DM with a product keyword (e.g., "FORGE") to generate a tracking link.');
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('Tracking System Status: ✅ Active');
    console.log('='.repeat(60));
}

if (require.main === module) {
    verifyTracking().catch(console.error);
}

module.exports = { verifyTracking };
