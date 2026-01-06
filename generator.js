const fs = require('fs-extra');
const path = require('path');
const https = require('https');
const http = require('http');
require('dotenv').config();

// Wealth & Hustle video prompts for Reels (9:16 vertical format)
const WEALTH_PROMPTS = [
  'Cinematic shot of a luxury watch in a dark office, 4k, 9:16',
  'POV of driving a supercar through Dubai at night, neon lights, 9:16',
  'Aerial view of a private jet on a runway at sunset, cinematic, 9:16',
  'Close-up of hundred dollar bills being counted, luxury desk, 9:16',
  'POV walking into a penthouse with city skyline view, modern, 9:16',
  'Luxury yacht cruising in crystal blue waters, drone shot, 9:16',
  'Time-lapse of a city skyline at night, financial district, 9:16',
  'Close-up of a gold Rolex on a marble surface, elegant lighting, 9:16',
  'POV of a private helicopter flying over mountains, cinematic, 9:16',
  'Luxury sports car parked in front of a modern mansion, 9:16',
  'Stack of gold bars on a black surface, dramatic lighting, 9:16',
  'POV entering a high-end casino, neon lights, Las Vegas, 9:16',
  'Aerial view of a private island with white sand beaches, 9:16',
  'Luxury watch collection displayed in a glass case, 9:16',
  'POV of a private jet interior, leather seats, luxury, 9:16',
];

/**
 * Downloads a file from a URL to a local path
 */
async function downloadFile(url, filePath) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    
    const request = protocol.get(url, (response) => {
      // Handle redirects
      if (response.statusCode === 301 || response.statusCode === 302) {
        return downloadFile(response.headers.location, filePath)
          .then(resolve)
          .catch(reject);
      }
      
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode} ${response.statusMessage}`));
        return;
      }

      const fileStream = fs.createWriteStream(filePath);
      response.pipe(fileStream);

      fileStream.on('finish', () => {
        fileStream.close();
        console.log(`[Download] Saved: ${path.basename(filePath)}`);
        resolve(filePath);
      });

      fileStream.on('error', (err) => {
        fs.unlink(filePath, () => {}); // Delete the file on error
        reject(err);
      });
    });

    request.on('error', reject);
  });
}

/**
 * Generates a timestamped filename
 */
function getTimestampedFilename(prefix = 'reel', extension = 'mp4') {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hour = String(now.getHours()).padStart(2, '0');
  const minute = String(now.getMinutes()).padStart(2, '0');
  const second = String(now.getSeconds()).padStart(2, '0');
  
  // Format: reel_20231226_143052.mp4
  return `${prefix}_${year}${month}${day}_${hour}${minute}${second}.${extension}`;
}

/**
 * Main generation function
 * This uses MCP tools via remote workbench
 */
async function generateReel(prompt, sessionId = 'generator_session') {
  const queuePath = path.join(__dirname, 'queue');
  
  // Ensure queue directory exists
  await fs.ensureDir(queuePath);
  
  console.log(`\n[Generator] Starting generation for prompt:`);
  console.log(`  "${prompt}"`);
  
  // This will be executed via MCP remote workbench
  // The actual implementation will be in the workbench code
  return {
    prompt,
    sessionId,
    queuePath,
  };
}

/**
 * Main execution - shows example and instructions
 */
async function main() {
  const queuePath = path.join(__dirname, 'queue');
  
  // Ensure queue directory exists
  await fs.ensureDir(queuePath);
  
  console.log('='.repeat(60));
  console.log('Wealth & Hustle Reel Generator');
  console.log('='.repeat(60));
  console.log(`Total prompts available: ${WEALTH_PROMPTS.length}`);
  console.log(`Queue directory: ${queuePath}\n`);

  // Show example prompt
  const examplePrompt = WEALTH_PROMPTS[0];
  console.log('Example prompt that will be used:');
  console.log(`  "${examplePrompt}"\n`);

  console.log('Workflow:');
  console.log('  1. GEMINI_GENERATE_VIDEOS - Create video from prompt');
  console.log('  2. GEMINI_WAIT_FOR_VIDEO - Wait for completion and get URL');
  console.log('  3. Download video to queue folder with timestamped name');
  console.log('  4. GEMINI_GENERATE_IMAGE - Create matching 9:16 cover image');
  console.log('\nNote: This script requires MCP tool integration.');
  console.log('The actual generation will be executed via MCP remote workbench.\n');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  WEALTH_PROMPTS,
  generateReel,
  downloadFile,
  getTimestampedFilename,
};
