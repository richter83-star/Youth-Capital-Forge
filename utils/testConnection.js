require('dotenv').config();
const { IgApiClient } = require('instagram-private-api');
const fs = require('fs-extra');
const path = require('path');

/**
 * Test Instagram connection and diagnose issues
 */
async function testConnection() {
    console.log('='.repeat(60));
    console.log('🔍 INSTAGRAM CONNECTION DIAGNOSTIC');
    console.log('='.repeat(60));
    console.log('');
    
    try {
        // Check accounts.json
        console.log('1. Checking accounts.json...');
        const accountsPath = path.join(__dirname, '../accounts.json');
        if (!await fs.pathExists(accountsPath)) {
            console.log('   ❌ accounts.json NOT FOUND');
            return;
        }
        
        const accounts = await fs.readJson(accountsPath);
        if (!accounts || accounts.length === 0) {
            console.log('   ❌ No accounts in accounts.json');
            return;
        }
        
        const account = accounts[0];
        console.log(`   ✅ Found account: ${account.username}`);
        console.log(`   ✅ Password: ${account.password ? '***' : 'MISSING'}`);
        console.log('');
        
        // Check .env
        console.log('2. Checking environment variables...');
        const requiredVars = ['GUMROAD_TOKEN'];
        const missing = requiredVars.filter(v => !process.env[v]);
        if (missing.length > 0) {
            console.log(`   ⚠️  Missing: ${missing.join(', ')}`);
        } else {
            console.log('   ✅ Required env vars present');
        }
        console.log('');
        
        // Test Instagram login
        console.log('3. Testing Instagram login...');
        const ig = new IgApiClient();
        
        try {
            ig.state.generateDevice(account.username);
            console.log('   ✅ Device generated');
            
            console.log('   Attempting pre-login flow...');
            try {
                await ig.simulate.preLoginFlow();
                console.log('   ✅ Pre-login flow successful');
            } catch (e) {
                console.log(`   ⚠️  Pre-login flow warning: ${e.message}`);
            }
            
            console.log('   Attempting login...');
            await ig.account.login(account.username, account.password);
            console.log('   ✅ LOGIN SUCCESSFUL!');
            
            // Get user info
            const user = await ig.account.currentUser();
            console.log(`   ✅ Logged in as: ${user.username} (${user.full_name || 'No name'})`);
            console.log(`   ✅ User ID: ${user.pk}`);
            console.log('');
            
            // Test queue access
            console.log('4. Testing queue access...');
            const queueDir = path.join(__dirname, '../queue');
            if (await fs.pathExists(queueDir)) {
                const files = (await fs.readdir(queueDir).catch(() => [])).filter(f => f.endsWith('.mp4'));
                console.log(`   ✅ Queue directory accessible`);
                console.log(`   ✅ Found ${files.length} videos`);
                if (files.length > 0) {
                    const firstFile = path.join(queueDir, files[0]);
                    try {
                        const stats = await fs.stat(firstFile);
                        console.log(`   ✅ Can read first file: ${files[0]} (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);
                    } catch (e) {
                        console.log(`   ❌ Cannot read file: ${e.message}`);
                    }
                }
            } else {
                console.log('   ❌ Queue directory not found');
            }
            console.log('');
            
            console.log('='.repeat(60));
            console.log('✅ ALL CHECKS PASSED - Automation should work!');
            console.log('='.repeat(60));
            
        } catch (loginError) {
            console.log('');
            console.log('='.repeat(60));
            console.log('❌ LOGIN FAILED');
            console.log('='.repeat(60));
            console.log(`Error: ${loginError.message}`);
            console.log(`Stack: ${loginError.stack}`);
            console.log('');
            console.log('Possible issues:');
            console.log('  1. Wrong username/password');
            console.log('  2. Instagram 2FA enabled (needs app password)');
            console.log('  3. Account locked/suspended');
            console.log('  4. Rate limiting');
            console.log('  5. Network connectivity');
        }
        
    } catch (error) {
        console.error('❌ Diagnostic Error:', error.message);
        console.error(error.stack);
    }
}

testConnection().catch(console.error);
