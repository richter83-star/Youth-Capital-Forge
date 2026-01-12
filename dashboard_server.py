#!/usr/bin/env python3
"""
Real-Time Dashboard Server for Cash Engine
Provides web-based GUI with real-time metrics and status updates
"""

import os
import sys
import json
import sqlite3
import threading
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='dashboard',
            static_folder='dashboard/static')
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY', 'cash-engine-dashboard-secret-key-2026')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')  # 0.0.0.0 for remote access
DASHBOARD_UPDATE_INTERVAL = int(os.getenv('DASHBOARD_UPDATE_INTERVAL', '10'))  # seconds
DB_PATH = Path("./data/engine.db")

# Global database connection
db_conn = None

def get_db_connection():
    """Get database connection"""
    global db_conn
    if db_conn is None:
        if DB_PATH.exists():
            db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            db_conn.row_factory = sqlite3.Row
    return db_conn

def close_db_connection():
    """Close database connection"""
    global db_conn
    if db_conn:
        db_conn.close()
        db_conn = None

def get_revenue_data(days: int = 30) -> Dict[str, Any]:
    """Get revenue data from database"""
    conn = get_db_connection()
    if not conn:
        return {"total": 0.0, "by_source": {}, "recent": []}
    
    try:
        cursor = conn.cursor()
        
        # Total revenue
        cursor.execute('''
            SELECT SUM(amount) as total 
            FROM revenue 
            WHERE timestamp >= datetime('now', '-' || ? || ' days') AND status = 'completed'
        ''', (days,))
        total = cursor.fetchone()[0] or 0.0
        
        # Revenue by source
        cursor.execute('''
            SELECT source, SUM(amount) as total 
            FROM revenue 
            WHERE timestamp >= datetime('now', '-' || ? || ' days') AND status = 'completed'
            GROUP BY source
        ''', (days,))
        by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent transactions
        cursor.execute('''
            SELECT source, amount, currency, description, timestamp
            FROM revenue 
            WHERE status = 'completed'
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        recent = [
            {
                "source": row[0],
                "amount": row[1],
                "currency": row[2],
                "description": row[3],
                "timestamp": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "total": total,
            "by_source": by_source,
            "recent": recent
        }
    except Exception as e:
        print(f"Error getting revenue data: {e}")
        return {"total": 0.0, "by_source": {}, "recent": []}

def get_shopify_stats(days: int = 30) -> Dict[str, Any]:
    """Get Shopify-specific statistics"""
    conn = get_db_connection()
    if not conn:
        return {
            "order_count": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "currency": "USD"
        }
    
    try:
        cursor = conn.cursor()
        
        # Count Shopify orders and calculate totals
        cursor.execute('''
            SELECT COUNT(*) as order_count, 
                   SUM(amount) as total_revenue,
                   AVG(amount) as avg_order_value,
                   currency
            FROM revenue 
            WHERE source = 'shopify' 
              AND timestamp >= datetime('now', '-' || ? || ' days') 
              AND status = 'completed'
            GROUP BY currency
        ''', (days,))
        
        result = cursor.fetchone()
        if result:
            return {
                "order_count": result[0] or 0,
                "total_revenue": float(result[1] or 0.0),
                "average_order_value": float(result[2] or 0.0),
                "currency": result[3] or "USD"
            }
        else:
            return {
                "order_count": 0,
                "total_revenue": 0.0,
                "average_order_value": 0.0,
                "currency": "USD"
            }
    except Exception as e:
        print(f"Error getting Shopify stats: {e}")
        return {
            "order_count": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "currency": "USD"
        }

def get_products_data() -> Dict[str, Any]:
    """Get products data"""
    conn = get_db_connection()
    if not conn:
        return {"count": 0, "recent": []}
    
    try:
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) as count FROM products')
        count = cursor.fetchone()[0] or 0
        
        # Recent products
        cursor.execute('''
            SELECT name, price, created_date, template_id
            FROM products 
            ORDER BY created_date DESC
            LIMIT 10
        ''')
        recent = [
            {
                "name": row[0],
                "price": row[1],
                "created_date": row[2],
                "template_id": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        return {"count": count, "recent": recent}
    except Exception as e:
        print(f"Error getting products data: {e}")
        return {"count": 0, "recent": []}

def get_leads_data(days: int = 30) -> Dict[str, Any]:
    """Get leads data"""
    conn = get_db_connection()
    if not conn:
        return {"count": 0, "by_source": {}, "recent": []}
    
    try:
        cursor = conn.cursor()
        
        # Total count (leads table doesn't have timestamp, count all)
        cursor.execute('SELECT COUNT(*) as count FROM leads')
        count = cursor.fetchone()[0] or 0
        
        # By source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM leads 
            GROUP BY source
        ''')
        by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent leads (using id as proxy for recent, since no timestamp)
        cursor.execute('''
            SELECT email, source, value_score, id
            FROM leads 
            ORDER BY id DESC
            LIMIT 10
        ''')
        recent = [
            {
                "email": row[0],
                "source": row[1],
                "value_score": row[2],
                "timestamp": None  # leads table doesn't have timestamp
            }
            for row in cursor.fetchall()
        ]
        
        return {"count": count, "by_source": by_source, "recent": recent}
    except Exception as e:
        print(f"Error getting leads data: {e}")
        return {"count": 0, "by_source": {}, "recent": []}

def get_content_performance(days: int = 30) -> List[Dict[str, Any]]:
    """Get content performance data"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content_file, platform, 
                   SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions,
                   SUM(revenue) as total_revenue
            FROM content_performance
            WHERE date >= datetime('now', '-' || ? || ' days')
            GROUP BY content_file, platform
            ORDER BY total_revenue DESC
        ''', (days,))
        
        return [
            {
                "content_file": row[0],
                "platform": row[1],
                "clicks": row[2] or 0,
                "conversions": row[3] or 0,
                "revenue": row[4] or 0.0
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error getting content performance: {e}")
        return []

def get_campaign_performance(days: int = 30) -> List[Dict[str, Any]]:
    """Get campaign performance data"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT campaign_id, 
                   SUM(impressions) as total_impressions,
                   SUM(clicks) as total_clicks,
                   SUM(conversions) as total_conversions,
                   SUM(revenue) as total_revenue,
                   SUM(commissions) as total_commissions
            FROM campaign_performance
            WHERE date >= datetime('now', '-' || ? || ' days')
            GROUP BY campaign_id
            ORDER BY total_commissions DESC
        ''', (days,))
        
        return [
            {
                "campaign_id": row[0],
                "impressions": row[1] or 0,
                "clicks": row[2] or 0,
                "conversions": row[3] or 0,
                "revenue": row[4] or 0.0,
                "commissions": row[5] or 0.0
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error getting campaign performance: {e}")
        return []

def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    status = {
        "engine_running": False,
        "last_activity": None,
        "api_status": {},
        "database_status": False,
        "revenue_streams": []
    }
    
    # Check if engine is running (check for recent log activity)
    log_path = Path("./logs/engine.log")
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    # Extract timestamp from log
                    if 'INFO' in last_line or 'ERROR' in last_line:
                        status["engine_running"] = True
                        # Try to extract timestamp
                        parts = last_line.split(' - ')
                        if len(parts) > 0:
                            status["last_activity"] = parts[0]
        except Exception:
            pass
    
    # Check database
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            status["database_status"] = True
        except Exception:
            status["database_status"] = False
    
    # Check API connections
    gumroad_token = os.getenv('GUMROAD_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    marketing_agent_url = os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000')
    shopify_enabled = os.getenv('SHOPIFY_ENABLED', 'false').lower() in ('true', '1', 'yes', 'on')
    shopify_access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    
    status["api_status"] = {
        "gumroad": bool(gumroad_token),
        "openai": bool(openai_key),
        "marketing_agent": bool(marketing_agent_url),
        "shopify": shopify_enabled and bool(shopify_access_token)
    }
    
    # Revenue streams
    revenue_streams = [
        "digital_product_factory",
        "affiliate_automation",
        "lead_generation_bot",
        "content_syndication"
    ]
    if shopify_enabled:
        revenue_streams.append("shopify_integration")
    status["revenue_streams"] = [{"name": s, "status": "active"} for s in revenue_streams]
    
    return status

def get_ab_tests() -> List[Dict[str, Any]]:
    """Get active A/B tests"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, test_name, status, start_date
            FROM template_ab_tests
            WHERE status = 'active'
        ''')
        
        return [
            {
                "id": row[0],
                "test_name": row[1],
                "status": row[2],
                "created_date": row[3]  # Using start_date as created_date
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error getting A/B tests: {e}")
        return []

def get_trend_analysis(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent trend analysis"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT topic, source, trend_score, volume, timestamp
            FROM trend_analysis
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        return [
            {
                "topic": row[0],
                "source": row[1],
                "trend_score": row[2] or 0.0,
                "volume": row[3] or 0,
                "timestamp": row[4]
            }
            for row in cursor.fetchall()
        ]
    except Exception as e:
        print(f"Error getting trend analysis: {e}")
        return []

def get_dashboard_data() -> Dict[str, Any]:
    """Get complete dashboard data"""
    return {
        "timestamp": datetime.now().isoformat(),
        "revenue": {
            "today": get_revenue_data(1),
            "week": get_revenue_data(7),
            "month": get_revenue_data(30)
        },
        "shopify": {
            "today": get_shopify_stats(1),
            "week": get_shopify_stats(7),
            "month": get_shopify_stats(30)
        },
        "products": get_products_data(),
        "leads": get_leads_data(30),
        "content_performance": get_content_performance(30),
        "campaign_performance": get_campaign_performance(30),
        "system_status": get_system_status(),
        "ab_tests": get_ab_tests(),
        "trends": get_trend_analysis(10)
    }

# Flask Routes
@app.route('/')
def index():
    """Serve dashboard page"""
    return render_template('index.html')

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for full dashboard data"""
    return jsonify(get_dashboard_data())

@app.route('/api/revenue')
def api_revenue():
    """API endpoint for revenue data"""
    days = int(request.args.get('days', 30))
    return jsonify(get_revenue_data(days))

@app.route('/api/performance')
def api_performance():
    """API endpoint for performance metrics"""
    days = int(request.args.get('days', 30))
    return jsonify({
        "content": get_content_performance(days),
        "campaigns": get_campaign_performance(days)
    })

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(get_system_status())

@app.route('/api/shopify')
def api_shopify():
    """API endpoint for Shopify statistics"""
    days = int(request.args.get('days', 30))
    return jsonify(get_shopify_stats(days))

@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/webhooks/shopify/orders', methods=['POST'])
def shopify_webhook():
    """Shopify order webhook endpoint for real-time revenue tracking"""
    webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET', '')
    shopify_enabled = os.getenv('SHOPIFY_ENABLED', 'false').lower() in ('true', '1', 'yes', 'on')
    
    if not shopify_enabled:
        return jsonify({"error": "Shopify integration not enabled"}), 403
    
    # Verify webhook signature
    if webhook_secret:
        signature = request.headers.get('X-Shopify-Hmac-Sha256', '')
        calculated_signature = base64.b64encode(
            hmac.new(
                webhook_secret.encode('utf-8'),
                request.data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        if not hmac.compare_digest(calculated_signature, signature):
            print(f"⚠️ Shopify webhook signature verification failed")
            return jsonify({"error": "Invalid webhook signature"}), 401
    
    try:
        order_data = request.get_json()
        
        if not order_data:
            return jsonify({"error": "No order data received"}), 400
        
        # Extract order information
        total_price = float(order_data.get("total_price", 0))
        order_number = order_data.get("order_number", "")
        order_id = order_data.get("id", "")
        created_at = order_data.get("created_at", datetime.now().isoformat())
        currency = order_data.get("currency", "USD")
        
        # Extract product names from line items
        line_items = order_data.get("line_items", [])
        product_names = [item.get("title", "") for item in line_items]
        description = f"Shopify Order #{order_number}: {', '.join(product_names[:3])}"
        if len(product_names) > 3:
            description += f" and {len(product_names) - 3} more"
        
        # Record revenue in database
        conn = get_db_connection()
        if not conn:
            print("⚠️ Database connection not available for Shopify webhook")
            return jsonify({"error": "Database unavailable"}), 500
        
        try:
            # Ensure order_id column exists
            cursor = conn.cursor()
            try:
                cursor.execute('ALTER TABLE revenue ADD COLUMN order_id TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass
            
            # Check if order already recorded (deduplication)
            cursor.execute('SELECT id FROM revenue WHERE order_id = ?', (str(order_id),))
            if cursor.fetchone():
                print(f"ℹ️ Shopify order #{order_number} already recorded (duplicate webhook)")
                return jsonify({"status": "duplicate", "order_number": order_number}), 200
            
            # Record revenue
            cursor.execute('''
                INSERT INTO revenue (source, amount, currency, description, status, order_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ("shopify", total_price, currency, description, "completed", str(order_id), created_at))
            
            conn.commit()
            
            print(f"✅ Recorded Shopify order #{order_number}: ${total_price} {currency}")
            
            # Emit real-time update to connected clients
            socketio.emit('shopify_order', {
                "order_number": order_number,
                "amount": total_price,
                "currency": currency,
                "products": product_names[:5]  # First 5 products
            })
            
            return jsonify({
                "status": "success",
                "order_number": order_number,
                "amount": total_price,
                "currency": currency
            }), 200
            
        except Exception as db_error:
            conn.rollback()
            print(f"❌ Database error recording Shopify order: {db_error}")
            return jsonify({"error": "Database error"}), 500
            
    except Exception as e:
        print(f"❌ Error processing Shopify webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Cash Engine Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    data = get_dashboard_data()
    emit('dashboard_update', data)

def emit_periodic_updates():
    """Emit periodic dashboard updates"""
    while True:
        try:
            data = get_dashboard_data()
            socketio.emit('dashboard_update', data)
        except Exception as e:
            print(f"Error emitting update: {e}")
        time.sleep(DASHBOARD_UPDATE_INTERVAL)

# Start periodic update thread
update_thread = threading.Thread(target=emit_periodic_updates, daemon=True)
update_thread.start()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Cash Engine Dashboard Server")
    print("=" * 60)
    print(f"📊 Dashboard URL: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"🔄 Update Interval: {DASHBOARD_UPDATE_INTERVAL} seconds")
    print(f"🌐 Remote Access: {'Enabled' if DASHBOARD_HOST == '0.0.0.0' else 'Local only'}")
    print("=" * 60)
    
    try:
        socketio.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard server...")
        close_db_connection()
        sys.exit(0)
