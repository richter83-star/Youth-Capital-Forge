const http = require('http');
const ClickTracker = require('./clickTracker');

/**
 * Simple HTTP Redirect Server
 * Handles tracking URL redirects to final destination
 * 
 * Usage: node utils/redirectServer.js
 * Then access: http://localhost:3000/track/{trackingId}
 */
class RedirectServer {
    constructor(port = 3000) {
        this.port = port;
        this.tracker = new ClickTracker();
        this.server = null;
    }

    start() {
        this.server = http.createServer(async (req, res) => {
            try {
                // Parse tracking ID from URL
                const url = new URL(req.url, `http://${req.headers.host}`);
                const pathParts = url.pathname.split('/');
                
                if (pathParts[1] === 'track' && pathParts[2]) {
                    const trackingId = pathParts[2];
                    
                    // Get click data from request
                    const clickData = {
                        ip: req.headers['x-forwarded-for'] || req.connection.remoteAddress,
                        userAgent: req.headers['user-agent'],
                        referer: req.headers['referer']
                    };
                    
                    // Get redirect destination
                    const redirect = await this.tracker.getRedirect(trackingId, clickData);
                    
                    if (redirect) {
                        // Log the redirect
                        console.log(`[Redirect] ${trackingId} -> ${redirect.destinationUrl}`);
                        
                        // Send 302 redirect
                        res.writeHead(302, {
                            'Location': redirect.destinationUrl,
                            'Cache-Control': 'no-cache'
                        });
                        res.end();
                    } else {
                        // Invalid tracking ID
                        res.writeHead(404, { 'Content-Type': 'text/html' });
                        res.end('<h1>404 - Tracking link not found</h1>');
                    }
                } else if (url.pathname === '/stats') {
                    // Stats endpoint
                    const stats = await this.tracker.getStats();
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(stats, null, 2));
                } else if (url.pathname === '/recent') {
                    // Recent clicks endpoint
                    const recent = await this.tracker.getRecentClicks(20);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(recent, null, 2));
                } else {
                    // Health check
                    res.writeHead(200, { 'Content-Type': 'text/html' });
                    res.end(`
                        <h1>Click Tracking Redirect Server</h1>
                        <p>Status: ✅ Running</p>
                        <p>Endpoints:</p>
                        <ul>
                            <li><a href="/stats">/stats</a> - View statistics</li>
                            <li><a href="/recent">/recent</a> - Recent clicks</li>
                            <li>/track/{trackingId} - Redirect to destination</li>
                        </ul>
                    `);
                }
            } catch (error) {
                console.error(`[!] Server error: ${error.message}`);
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('Internal Server Error');
            }
        });

        this.server.listen(this.port, () => {
            console.log(`[Redirect Server] Running on http://localhost:${this.port}`);
            console.log(`[Redirect Server] Access stats at http://localhost:${this.port}/stats`);
        });
    }

    stop() {
        if (this.server) {
            this.server.close();
            console.log('[Redirect Server] Stopped');
        }
    }
}

if (require.main === module) {
    const server = new RedirectServer(process.env.REDIRECT_PORT || 3000);
    server.start();
    
    // Graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n[Redirect Server] Shutting down...');
        server.stop();
        process.exit(0);
    });
}

module.exports = RedirectServer;
