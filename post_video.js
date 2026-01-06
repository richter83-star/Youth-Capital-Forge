require('dotenv').config();
const { IgApiClient } = require('instagram-private-api');
const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');
const sharp = require('sharp');
const Optimizer = require('./utils/optimizer');

const ig = new IgApiClient();
const optimizer = new Optimizer(process.env.GUMROAD_TOKEN);

async function login(account) {
    ig.state.generateDevice(account.username);
    try {
        await ig.simulate.preLoginFlow();
    } catch (e) {
        console.log(`[!] Skipped preLoginFlow simulation (Expected 404)`);
    }
    await ig.account.login(account.username, account.password);
    process.nextTick(async () => {
        try { await ig.simulate.postLoginFlow(); } catch(e) {}
    });
}

async function postVideo() {
    const strategy = await optimizer.analyzeAndPivot(ig);
    const queueDir = path.join(__dirname, 'queue');
    const files = (await fs.readdir(queueDir).catch(() => [])).filter(f => f.endsWith('.mp4') && !f.includes('_processed'));

    if (files.length === 0) {
        console.log("[!] Queue empty. No videos to post.");
        return;
    }

    // Get first video from queue
    const videoName = files[0];
    const videoPath = path.join(queueDir, videoName);
    const coverPath = path.join(__dirname, `temp_cover_${Date.now()}.jpg`);
    
    console.log(`[*] Processing video: ${videoName}`);

    let coverBuffer;
    let videoBuffer;

    try {
        videoBuffer = await fs.readFile(videoPath);
        
        // Try to extract cover with ffmpeg
        try {
            console.log(`[*] Extracting cover frame...`);
            execSync(`ffmpeg -y -i "${videoPath}" -ss 00:00:01 -vframes 1 "${coverPath}" -loglevel error`);
            
            if (fs.existsSync(coverPath)) {
                coverBuffer = await sharp(coverPath)
                    .resize(1080, 1920, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 1 } })
                    .jpeg()
                    .toBuffer();
                await fs.unlink(coverPath).catch(() => {});
                console.log(`[+] Cover extracted successfully.`);
            } else {
                throw new Error("ffmpeg finished but cover file not found");
            }
        } catch (ffmpegErr) {
            console.warn(`[!] ffmpeg failed or not found, using minimal JPEG cover...`);
            // Generate minimal JPEG cover
            coverBuffer = Buffer.from([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
                0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
                0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
                0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
                0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
                0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
                0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
                0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
                0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x08, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
                0x80, 0xFF, 0xD9
            ]);
        }

        const baseCaptions = [
            "Automate your income. Check link in bio.",
            "Stop trading time for money.",
            "The digital revolution is here.",
            "30k/mo system. Comment FORGE below."
        ];
        const caption = `${baseCaptions[Math.floor(Math.random() * baseCaptions.length)]} ${strategy.activeHashtags.join(' ')}`;

        console.log(`[*] Posting Reel: ${videoName}...`);
        console.log(`[*] Caption: ${caption}`);
        
        const result = await ig.publish.video({
            video: videoBuffer,
            coverImage: coverBuffer,
            caption: caption
        });
        
        await optimizer.logActivity(result.media.id, caption);
        const processedDir = path.join(__dirname, 'logs/processed');
        await fs.ensureDir(processedDir);
        await fs.move(videoPath, path.join(processedDir, videoName));
        
        console.log(`[+] ✅ Post success! Media ID: ${result.media.id}`);
        console.log(`[+] Video moved to processed folder`);

    } catch (e) {
        console.error(`[!] Post error: ${e.message}`);
        if (e.stack) {
            console.error(`[!] Stack: ${e.stack}`);
        }
        throw e;
    }
}

async function main() {
    try {
        const accounts = await fs.readJson(path.join(__dirname, 'accounts.json'));
        const activeAccount = accounts.find(acc => acc.status === 'active') || accounts[0];
        
        console.log(`[*] Logging in as ${activeAccount.username}...`);
        await login(activeAccount);
        console.log(`[+] Login successful`);
        
        console.log(`[*] Posting video...`);
        await postVideo();
        
        console.log(`[+] Done!`);
        process.exit(0);
    } catch (error) {
        console.error(`[!] Fatal error: ${error.message}`);
        process.exit(1);
    }
}

main();
