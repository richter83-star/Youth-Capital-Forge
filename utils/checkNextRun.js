require('dotenv').config();
const fs = require('fs-extra');
const path = require('path');

/**
 * Check when the next post is scheduled
 */
async function checkNextRun() {
    console.log('='.repeat(60));
    console.log('📅 NEXT POST SCHEDULE CHECK');
    console.log('='.repeat(60));
    console.log('');
    
    try {
        // Get last post
        const activityPath = path.join(__dirname, '../logs/activity.json');
        let lastPost = null;
        let lastPostTime = null;
        
        if (await fs.pathExists(activityPath)) {
            const activity = await fs.readJson(activityPath);
            if (activity.length > 0) {
                lastPost = activity[activity.length - 1];
                lastPostTime = new Date(lastPost.timestamp);
            }
        }
        
        // Get current interval
        const statePath = path.join(__dirname, '../logs/state.json');
        let currentInterval = 4 * 60 * 60 * 1000; // Default 4 hours
        if (await fs.pathExists(statePath)) {
            const state = await fs.readJson(statePath);
            currentInterval = state.currentInterval || currentInterval;
        }
        
        // Enforce minimum 4-hour interval
        const minInterval = 4 * 60 * 60 * 1000;
        const actualInterval = Math.max(currentInterval, minInterval);
        const intervalHours = actualInterval / (60 * 60 * 1000);
        
        const now = new Date();
        
        console.log('📊 Current Status:');
        console.log('-'.repeat(60));
        
        if (lastPost) {
            console.log(`Last Post: ${lastPostTime.toLocaleString()}`);
            console.log(`Media ID: ${lastPost.mediaId}`);
            console.log(`Caption: ${lastPost.caption.substring(0, 50)}...`);
            console.log('');
            
            const hoursSinceLastPost = (now - lastPostTime) / (60 * 60 * 1000);
            console.log(`Time Since Last Post: ${hoursSinceLastPost.toFixed(2)} hours`);
            console.log('');
            
            // Calculate next post time
            const nextPostTime = new Date(lastPostTime.getTime() + actualInterval);
            const hoursUntilNext = (nextPostTime - now) / (60 * 60 * 1000);
            
            console.log('⏰ Next Post Schedule:');
            console.log('-'.repeat(60));
            console.log(`Interval: ${intervalHours.toFixed(2)} hours (minimum 4 hours)`);
            console.log(`Scheduled Time: ${nextPostTime.toLocaleString()}`);
            
            if (hoursUntilNext <= 0) {
                console.log(`Status: ⚠️  OVERDUE by ${Math.abs(hoursUntilNext).toFixed(2)} hours`);
                console.log('');
                console.log('🚨 The automation should post IMMEDIATELY on next run!');
            } else {
                console.log(`Status: ✅ Scheduled in ${hoursUntilNext.toFixed(2)} hours`);
                const minutesUntil = hoursUntilNext * 60;
                if (minutesUntil < 60) {
                    console.log(`         (${Math.round(minutesUntil)} minutes)`);
                } else {
                    const hours = Math.floor(hoursUntilNext);
                    const minutes = Math.round((hoursUntilNext - hours) * 60);
                    console.log(`         (${hours}h ${minutes}m)`);
                }
            }
        } else {
            console.log('No previous posts found.');
            console.log('');
            console.log('⏰ Next Post Schedule:');
            console.log('-'.repeat(60));
            console.log('Status: ✅ Will post IMMEDIATELY on next run');
            console.log(`Interval: ${intervalHours.toFixed(2)} hours (minimum 4 hours)`);
        }
        
        console.log('');
        console.log('📋 Queue Status:');
        console.log('-'.repeat(60));
        const queueDir = path.join(__dirname, '../queue');
        if (await fs.pathExists(queueDir)) {
            const files = (await fs.readdir(queueDir).catch(() => [])).filter(f => f.endsWith('.mp4'));
            console.log(`Videos in queue: ${files.length}`);
            if (files.length > 0) {
                console.log('');
                console.log('Available videos:');
                files.slice(0, 5).forEach((file, idx) => {
                    console.log(`  ${idx + 1}. ${file}`);
                });
                if (files.length > 5) {
                    console.log(`  ... and ${files.length - 5} more`);
                }
            } else {
                console.log('⚠️  Queue is empty - no videos to post');
            }
        } else {
            console.log('⚠️  Queue directory not found');
        }
        
        console.log('');
        console.log('💡 Note:');
        console.log('   - Posts happen every 4 hours minimum');
        console.log('   - Duplicate videos are automatically skipped');
        console.log('   - If overdue, next post will be immediate');
        console.log('');
        
    } catch (error) {
        console.error('❌ Error checking schedule:', error.message);
    }
}

checkNextRun().catch(console.error);
