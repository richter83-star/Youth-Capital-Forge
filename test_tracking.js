const ClickTracker = require('./utils/clickTracker');

/**
 * Test script to verify click tracking and redirect functionality
 */
async function testTracking() {
    console.log('🧪 Testing Click-Through Tracking System\n');
    
    const tracker = new ClickTracker();
    
    // Test 1: Generate tracking URLs
    console.log('Test 1: Generating tracking URLs...');
    const testProducts = [
        { name: 'FORGE', url: 'https://gumroad.com/l/forge' },
        { name: 'PROMPTS', url: 'https://gumroad.com/l/prompts' }
    ];
    
    const trackingUrls = [];
    for (const product of testProducts) {
        const trackingUrl = await tracker.generateTrackingUrl(product.name, product.url, 'test_user_123');
        trackingUrls.push({ product: product.name, url: trackingUrl });
        console.log(`  ✅ Generated: ${product.name} -> ${trackingUrl}`);
    }
    
    // Test 2: Simulate clicks
    console.log('\nTest 2: Simulating clicks...');
    for (const { product, url } of trackingUrls) {
        // Extract tracking ID from URL
        const trackingId = url.split('/').pop();
        
        const redirect = await tracker.getRedirect(trackingId, {
            ip: '127.0.0.1',
            userAgent: 'Test-Agent/1.0',
            referer: 'instagram'
        });
        
        if (redirect) {
            console.log(`  ✅ Click tracked: ${product}`);
            console.log(`     Redirects to: ${redirect.destinationUrl}`);
        } else {
            console.log(`  ❌ Failed to track click for ${product}`);
        }
    }
    
    // Test 3: Get statistics
    console.log('\nTest 3: Retrieving statistics...');
    const stats = await tracker.getStats();
    console.log(`  Total Clicks: ${stats.totalClicks}`);
    console.log(`  Clicks by Product:`, stats.clicksByProduct);
    
    // Test 4: Get recent clicks
    console.log('\nTest 4: Recent clicks...');
    const recent = await tracker.getRecentClicks(5);
    recent.forEach((click, i) => {
        console.log(`  ${i + 1}. ${click.productName} at ${click.timestamp}`);
    });
    
    console.log('\n✅ All tests completed!');
    console.log('\n📝 Next Steps:');
    console.log('  1. Start redirect server: node utils/redirectServer.js');
    console.log('  2. Send a DM with product keyword (e.g., "FORGE")');
    console.log('  3. Click the tracking link to verify redirect');
    console.log('  4. Check stats: node utils/verifyTracking.js');
}

testTracking().catch(console.error);
