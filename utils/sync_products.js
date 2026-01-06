const fs = require('fs-extra');
const path = require('path');
require('dotenv').config();

const Gumroad = require('./gumroad');

/**
 * PDF Generator Placeholder Hook
 * This can be extended to use pdfkit, puppeteer, or any PDF library
 * @param {Object} product - Product data from Gumroad
 * @param {string} outputPath - Path to save PDF
 * @returns {Promise<boolean>} Success status
 */
async function generatePDFPlaceholder(product, outputPath) {
    try {
        await fs.ensureDir(path.dirname(outputPath));
        
        // Placeholder: Simple text file (replace with actual PDF generation)
        // Example: Use pdfkit, puppeteer, or pdf-lib here
        const content = `PRODUCT DELIVERY: ${product.name}
        
Access Link: ${product.short_url || product.url || 'N/A'}
Product ID: ${product.id}
Created: ${new Date().toISOString()}

This is an automated delivery placeholder.
Replace this function with your preferred PDF generation library.

Example implementations:
- pdfkit: const PDFDocument = require('pdfkit');
- puppeteer: Generate HTML and convert to PDF
- pdf-lib: Create/modify PDF documents programmatically
`;

        await fs.writeFile(outputPath, content, 'utf8');
        return true;
    } catch (error) {
        console.error(`[!] PDF Generation Error for ${product.name}: ${error.message}`);
        return false;
    }
}

/**
 * Sync products from Gumroad and update .env file
 * Autonomous-safe: Handles errors gracefully without crashing
 */
async function syncProducts() {
    try {
        // Initialize Gumroad client
        const gumroad = new Gumroad(process.env.GUMROAD_TOKEN);
        
        if (!gumroad.hasAccessToken()) {
            console.error('[!] GUMROAD_TOKEN is not set correctly in .env');
            console.error('[!] Please set GUMROAD_TOKEN=your_access_token in .env file');
            return { success: false, error: 'Missing access token' };
        }

        console.log('[*] Fetching products from Gumroad...');
        const products = await gumroad.getProducts();
        
        if (!Array.isArray(products) || products.length === 0) {
            console.warn('[!] No products found or failed to fetch products');
            return { success: false, error: 'No products found', products: [] };
        }

        console.log(`[+] Found ${products.length} product(s).`);

        // Read existing .env file
        let envContent = '';
        const envPath = path.join(__dirname, '..', '.env');
        
        try {
            envContent = await fs.readFile(envPath, 'utf8');
        } catch (error) {
            console.warn('[!] .env file not found, creating new one...');
            envContent = '';
        }
        
        const productsDir = path.join(__dirname, '..', 'products');
        await fs.ensureDir(productsDir);

        let syncedCount = 0;
        let pdfGeneratedCount = 0;

        // Process each product
        for (const product of products) {
            try {
                // Normalize product name for env key (remove special chars, collapse multiple underscores)
                const normalizedName = product.name.toUpperCase()
                    .replace(/[^A-Z0-9]/g, '_')
                    .replace(/_+/g, '_')
                    .replace(/^_|_$/g, '');
                const nameKey = normalizedName + '_ID';
                const idValue = product.id;
                
                // Update or add product ID to .env
                const regex = new RegExp(`^${nameKey}=.*`, 'm');
                if (regex.test(envContent)) {
                    envContent = envContent.replace(regex, `${nameKey}=${idValue}`);
                } else {
                    envContent += `\n${nameKey}=${idValue}`;
                }

                // Generate product link if not present
                const linkKey = nameKey.replace('_ID', '_LINK');
                const linkValue = product.short_url || product.url || `https://gumroad.com/l/${product.permalink || product.id}`;
                const linkRegex = new RegExp(`^${linkKey}=.*`, 'm');
                if (!linkRegex.test(envContent)) {
                    envContent += `\n${linkKey}=${linkValue}`;
                }

                console.log(`[i] Synced: ${product.name} -> ${idValue}`);

                // Generate PDF placeholder if missing
                const pdfName = normalizedName + '.pdf';
                const pdfPath = path.join(productsDir, pdfName);
                
                if (!(await fs.pathExists(pdfPath))) {
                    console.log(`[*] Generating PDF placeholder for: ${product.name}`);
                    const pdfSuccess = await generatePDFPlaceholder(product, pdfPath);
                    if (pdfSuccess) {
                        pdfGeneratedCount++;
                    }
                }

                syncedCount++;
            } catch (error) {
                console.error(`[!] Error processing product ${product.name}: ${error.message}`);
                // Continue with next product
            }
        }

        // Write updated .env file
        try {
            await fs.writeFile(envPath, envContent, 'utf8');
            console.log('[+] .env updated with Product IDs and Links.');
        } catch (error) {
            console.error(`[!] Error writing .env file: ${error.message}`);
            return { success: false, error: 'Failed to write .env file' };
        }

        console.log(`[+] Sync complete: ${syncedCount} products synced, ${pdfGeneratedCount} PDFs generated.`);
        
        return {
            success: true,
            productsSynced: syncedCount,
            pdfsGenerated: pdfGeneratedCount,
            products
        };
    } catch (error) {
        console.error(`[!] Fatal error syncing products: ${error.message}`);
        console.error(error.stack);
        return { success: false, error: error.message };
    }
}

// Run if executed directly
if (require.main === module) {
    syncProducts()
        .then(result => {
            if (result.success) {
                process.exit(0);
            } else {
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('[!] Unhandled error:', error);
            process.exit(1);
        });
}

module.exports = { syncProducts, generatePDFPlaceholder };
