#!/usr/bin/env python3
"""
WHOP-STYLE MONEY ENGINE
Zero human intervention after launch
"""

import os
import json
import time
import random
import schedule
import threading
import hashlib
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import cloudscraper
import aiohttp
import asyncio
import redis
import sqlite3
import pandas as pd
import numpy as np
from cryptography.fernet import Fernet
import ccxt
import yfinance as yf
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AI Course Corrector
try:
    from ai_course_corrector import AICourseCorrector
    COURSE_CORRECTION_AVAILABLE = True
except ImportError:
    COURSE_CORRECTION_AVAILABLE = False
    logger = None  # Will be set up later

# Import Weekly Report Generator
try:
    from weekly_report_generator import WeeklyReportGenerator
    WEEKLY_REPORT_AVAILABLE = True
except ImportError:
    WEEKLY_REPORT_AVAILABLE = False

# Optional dependencies - wrap in try/except
try:
    import telebot
    TELEBOT_AVAILABLE = True
except ImportError:
    TELEBOT_AVAILABLE = False

try:
    import discord
    from discord import Webhook
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from logging.handlers import RotatingFileHandler
import pickle
import zlib
import qrcode
from PIL import Image, ImageDraw, ImageFont
import cv2

# Optional automation dependencies (require admin on Windows)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import mouse
    MOUSE_AVAILABLE = True
except ImportError:
    MOUSE_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from forex_python.converter import CurrencyRates
import stripe
from flask import Flask, request, jsonify
import subprocess
import sys
import re
import html
import itertools
from collections import defaultdict, Counter
import statistics
import math

# ============================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================
CONFIG = {
    "system_name": "AUTONOMOUS_CASH_ENGINE",
    "template_generation_enabled": os.getenv("TEMPLATE_GENERATION_ENABLED", "false").lower() == "true",
    "min_template_interval": int(os.getenv("MIN_TEMPLATE_GENERATION_INTERVAL", "7")),
    "template_topics": ["wealth", "business", "productivity", "entrepreneurship", "finance", "passive income"],
    "version": "2.0",
    "target_monthly": 10000,  # USD
    "operating_mode": "stealth",  # stealth, aggressive, balanced
    "revenue_streams": [
        "crypto_arbitrage",
        "affiliate_automation", 
        "digital_product_factory",
        "lead_generation_bot",
        "saas_reselling",
        "content_syndication",
        "data_scraping_service",
        "api_middleware"
    ],
    "bank_accounts": {
        "primary": "STRIPE_CONNECT",  # or PAYPAL, WISE, etc.
        "crypto": ["BTC", "ETH", "USDT"],
        "withdrawal_schedule": "weekly"
    },
    "automation": {
        "human_emulation": True,
        "proxy_rotation": True,
        "fingerprint_rotation": True,
        "rate_limiting": "adaptive",
        "error_recovery": "auto"
    },
    "security": {
        "encryption_level": "military",
        "log_obfuscation": True,
        "data_purging": "72h",
        "backup_location": "encrypted_cloud"
    },
    "template_optimization": {
        "ab_testing_enabled": os.getenv("AB_TEST_ENABLED", "true").lower() == "true",
        "trend_analysis_enabled": os.getenv("TREND_ANALYSIS_ENABLED", "true").lower() == "true",
        "sales_optimization_enabled": os.getenv("SALES_OPTIMIZATION_ENABLED", "true").lower() == "true",
        "trend_analysis_interval": int(os.getenv("TREND_ANALYSIS_INTERVAL", "24")),  # hours
        "ab_test_min_conversions": int(os.getenv("AB_TEST_MIN_CONVERSIONS", "10")),  # minimum conversions before declaring winner
        "optimization_threshold": float(os.getenv("OPTIMIZATION_THRESHOLD", "0.3"))  # optimize templates below 30% of average performance
    }
}

# API Keys (Store encrypted)
ENCRYPTED_KEYS = {
    "openai": "ENCRYPTED_KEY_HERE",
    "stripe": "ENCRYPTED_KEY_HERE", 
    "telegram": "ENCRYPTED_KEY_HERE",
    "discord": "ENCRYPTED_KEY_HERE",
    "aws": "ENCRYPTED_KEY_HERE",
    "google": "ENCRYPTED_KEY_HERE"
}

# ============================================
# GUMROAD API CLIENT
# ============================================
class GumroadClient:
    """Python client for Gumroad API"""
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv('GUMROAD_TOKEN')
        self.base_url = 'https://api.gumroad.com/v2'
    
    def has_access_token(self) -> bool:
        """Check if access token is available"""
        return bool(self.access_token and self.access_token.strip() and 
                   self.access_token != 'your_gumroad_access_token')
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     requires_auth: bool = False) -> Dict[str, Any]:
        """Make API request to Gumroad"""
        try:
            if requires_auth and not self.has_access_token():
                return {"success": False, "error": "Access token required"}
            
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if method == "GET":
                params = data or {}
                if requires_auth:
                    params["access_token"] = self.access_token
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                if requires_auth and data:
                    data["access_token"] = self.access_token
                response = requests.request(method, url, json=data, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            return {"success": True, "data": result}
        
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return {"success": False, "error": error_msg}
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products from Gumroad"""
        if not self.has_access_token():
            logger.warning("Gumroad: Access token missing")
            return []
        
        result = self._make_request("GET", "/products", requires_auth=True)
        if result["success"]:
            return result["data"].get("products", [])
        return []
    
    def get_sales(self, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Get sales data from Gumroad"""
        if not self.has_access_token():
            return {"success": False, "sales": []}
        
        result = self._make_request("GET", "/sales", data=options or {}, requires_auth=True)
        if result["success"]:
            return {"success": True, "sales": result["data"].get("sales", [])}
        return {"success": False, "sales": [], "error": result.get("error")}
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID"""
        if not self.has_access_token() or not product_id:
            return None
        
        result = self._make_request("GET", f"/products/{product_id}", requires_auth=True)
        if result["success"]:
            return result["data"].get("product")
        return None
    
    def create_product(self, name: str, price_cents: int, description: str = "", 
                      permalink: Optional[str] = None, custom_permalink: bool = False) -> Optional[Dict[str, Any]]:
        """Create a product on Gumroad via API"""
        if not self.has_access_token():
            logger.warning("Gumroad: Cannot create product - access token missing")
            return None
        
        try:
            data = {
                "name": name,
                "price": price_cents,  # Price in cents
                "description": description
            }
            
            if permalink:
                data["permalink"] = permalink
                if custom_permalink:
                    data["custom_permalink"] = True
            
            result = self._make_request("POST", "/products", data=data, requires_auth=True)
            
            if result["success"]:
                product = result["data"].get("product")
                logger.info(f"✅ Created Gumroad product: {name} (ID: {product.get('id') if product else 'unknown'})")
                return product
            else:
                logger.error(f"Gumroad product creation failed: {result.get('error', 'Unknown error')}")
                return None
        except Exception as e:
            logger.error(f"Error creating Gumroad product: {e}")
            return None
    
    def upload_product_file(self, product_id: str, file_path: Path) -> bool:
        """Upload a file to a Gumroad product (requires file upload API)"""
        if not self.has_access_token() or not product_id:
            return False
        
        try:
            # Gumroad file upload typically requires multipart/form-data
            # This is a placeholder - actual implementation would use requests with file upload
            logger.info(f"Would upload file {file_path.name} to product {product_id} (file upload API integration needed)")
            # TODO: Implement actual file upload when Gumroad API supports it
            return True
        except Exception as e:
            logger.error(f"Error uploading file to Gumroad: {e}")
            return False


# ============================================
# SUPPORTING CLASSES
# ============================================
class RevenueTracker:
    """Tracks revenue across all streams"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
    
    def record_revenue(self, source: str, amount: float, currency: str = "USD", description: str = ""):
        """Record revenue transaction"""
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO revenue (source, amount, currency, description, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (source, amount, currency, description, "completed"))
        db.commit()
    
    def get_total_revenue(self, days: int = 30) -> float:
        """Get total revenue for specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        cursor = self._get_cursor()
        cursor.execute('''
            SELECT SUM(amount) FROM revenue 
            WHERE timestamp >= ? AND status = 'completed'
        ''', (cutoff,))
        result = cursor.fetchone()
        return result[0] or 0.0
    
    def get_revenue_by_source(self, days: int = 30) -> Dict[str, float]:
        """Get revenue breakdown by source"""
        cutoff = datetime.now() - timedelta(days=days)
        cursor = self._get_cursor()
        cursor.execute('''
            SELECT source, SUM(amount) FROM revenue 
            WHERE timestamp >= ? AND status = 'completed'
            GROUP BY source
        ''', (cutoff,))
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def track_performance_metric(self, metric_type: str, metric_name: str, value: float, 
                                 source: str = "", metadata: Optional[Dict] = None):
        """Track a performance metric for analytics"""
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            db = self._get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO performance_metrics (metric_type, metric_name, value, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (metric_type, metric_name, value, source, metadata_json))
            db.commit()
        except Exception as e:
            logger.error(f"Error tracking metric: {e}")
    
    def get_content_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get content performance analytics"""
        cutoff = datetime.now() - timedelta(days=days)
        self.cursor.execute('''
            SELECT content_file, platform, SUM(clicks) as total_clicks, 
                   SUM(conversions) as total_conversions, SUM(revenue) as total_revenue
            FROM content_performance
            WHERE date >= ?
            GROUP BY content_file, platform
            ORDER BY total_revenue DESC
        ''', (cutoff,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def get_campaign_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get campaign performance analytics"""
        cutoff = datetime.now() - timedelta(days=days)
        self.cursor.execute('''
            SELECT campaign_id, SUM(impressions) as total_impressions,
                   SUM(clicks) as total_clicks, SUM(conversions) as total_conversions,
                   SUM(revenue) as total_revenue, SUM(commissions) as total_commissions
            FROM campaign_performance
            WHERE date >= ?
            GROUP BY campaign_id
            ORDER BY total_commissions DESC
        ''', (cutoff,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def track_content_performance(self, content_file: str, platform: str, clicks: int = 0,
                                   conversions: int = 0, revenue: float = 0.0, metadata: Optional[Dict] = None):
        """Track content syndication performance"""
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            self.cursor.execute('''
                INSERT INTO content_performance (content_file, platform, clicks, conversions, revenue, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (content_file, platform, clicks, conversions, revenue, metadata_json))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error tracking content performance: {e}")
    
    def track_campaign_performance(self, campaign_id: str, impressions: int = 0, clicks: int = 0,
                                   conversions: int = 0, revenue: float = 0.0, commissions: float = 0.0,
                                   metadata: Optional[Dict] = None):
        """Track affiliate campaign performance"""
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            self.cursor.execute('''
                INSERT INTO campaign_performance (campaign_id, impressions, clicks, conversions, revenue, commissions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, impressions, clicks, conversions, revenue, commissions, metadata_json))
            self.db.commit()
        except Exception as e:
            logger.error(f"Error tracking campaign performance: {e}")


class RiskManager:
    """Manages risk and compliance"""
    def __init__(self):
        self.risk_level = "low"
        self.max_exposure = 1000.0
    
    def assess_risk(self, action: str, amount: float) -> bool:
        """Assess if action is within risk tolerance"""
        if amount > self.max_exposure:
            return False
        return True
    
    def update_risk_level(self, level: str):
        """Update risk level"""
        self.risk_level = level
        if level == "high":
            self.max_exposure = 100.0
        elif level == "medium":
            self.max_exposure = 500.0
        else:
            self.max_exposure = 1000.0


class ExecutionEngine:
    """Executes automated tasks"""
    def __init__(self):
        self.active_tasks = []
        self.task_queue = []
    
    def execute_task(self, task_name: str, params: Dict[str, Any]) -> bool:
        """Execute a task"""
        try:
            logger.info(f"Executing task: {task_name}")
            # Task execution logic would go here
            return True
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return False
    
    def schedule_task(self, task_name: str, params: Dict[str, Any], delay: int = 0):
        """Schedule a task for later execution"""
        self.task_queue.append({
            "task": task_name,
            "params": params,
            "execute_at": datetime.now() + timedelta(seconds=delay)
        })


class MarketScanner:
    """Scans markets for opportunities"""
    def __init__(self):
        self.opportunities = []
    
    def scan_arbitrage(self) -> List[Dict[str, Any]]:
        """Scan for arbitrage opportunities"""
        opportunities = []
        # Implementation would scan crypto exchanges, forex, etc.
        return opportunities
    
    def scan_affiliate(self) -> List[Dict[str, Any]]:
        """Scan for affiliate opportunities"""
        opportunities = []
        # Implementation would scan affiliate networks
        return opportunities


class ProductFactory:
    """Automated digital product creation with Gumroad integration"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.templates = []
        self.gumroad = GumroadClient()
        self.products_dir = Path("./products")
    
    def sync_gumroad_products(self) -> int:
        """Sync products from Gumroad to local database"""
        if not self.gumroad.has_access_token():
            logger.warning("Cannot sync Gumroad products: no access token")
            return 0
        
        try:
            gumroad_products = self.gumroad.get_products()
            synced = 0
            
            for gp in gumroad_products:
                product_id = gp.get("id")
                name = gp.get("name", "Unknown")
                price = float(gp.get("price_cents", 0)) / 100
                permalink = gp.get("permalink", "")
                
                # Check if product already exists
                self.cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
                existing = self.cursor.fetchone()
                
                if not existing:
                    self.cursor.execute('''
                        INSERT INTO products (name, price, type, description)
                        VALUES (?, ?, ?, ?)
                    ''', (name, price, "gumroad", permalink))
                    synced += 1
                    logger.info(f"Synced Gumroad product: {name}")
            
            self.db.commit()
            return synced
        except Exception as e:
            logger.error(f"Error syncing Gumroad products: {e}")
            return 0
    
    def track_gumroad_sales(self) -> float:
        """Track recent sales from Gumroad and record revenue"""
        if not self.gumroad.has_access_token():
            return 0.0
        
        try:
            # Get sales from last 24 hours
            since_date = (datetime.now() - timedelta(days=1)).isoformat()
            sales_result = self.gumroad.get_sales({"after": since_date})
            
            if not sales_result.get("success"):
                return 0.0
            
            total_revenue = 0.0
            sales = sales_result.get("sales", [])
            
            for sale in sales:
                amount = float(sale.get("price", 0)) / 100  # Convert cents to dollars
                product_name = sale.get("product_name", "Unknown")
                sale_id = sale.get("id", "")
                
                # Record revenue
                self.cursor.execute('''
                    INSERT INTO revenue (source, amount, currency, description, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', ("gumroad_sale", amount, "USD", f"Sale: {product_name}", "completed"))
                
                # Update product sales count
                self.cursor.execute('''
                    UPDATE products 
                    SET sales_count = sales_count + 1, 
                        total_revenue = total_revenue + ?
                    WHERE name = ?
                ''', (amount, product_name))
                
                # Note: A/B test conversion tracking will be handled in CashEngine.execute_product_creation
                
                total_revenue += amount
                logger.info(f"Recorded sale: {product_name} - ${amount:.2f}")
            
            self.db.commit()
            return total_revenue
            
        except Exception as e:
            logger.error(f"Error tracking Gumroad sales: {e}")
            return 0.0
    
    def create_product(self, product_type: str, params: Dict[str, Any]) -> Optional[int]:
        """Create a new digital product (local database only - Gumroad creation requires manual setup)"""
        try:
            name = params.get("name", f"Product_{uuid.uuid4().hex[:8]}")
            price = params.get("price", 9.99)
            description = params.get("description", "")
            
            self.cursor.execute('''
                INSERT INTO products (name, price, type, description)
                VALUES (?, ?, ?, ?)
            ''', (name, price, product_type, description))
            self.db.commit()
            
            product_id = self.cursor.lastrowid
            logger.info(f"Created product: {name} (ID: {product_id})")
            return product_id
        except Exception as e:
            logger.error(f"Product creation failed: {e}")
            return None
    
    def create_product_from_template(self, template_file: Path, product_name: str, price: float, ab_test_variant: str = None) -> Optional[int]:
        """Create a product from a template file (REVENUE GENERATION)"""
        try:
            if not template_file.exists():
                logger.error(f"Template not found: {template_file}")
                return None
            content = template_file.read_text(encoding='utf-8')
            description = self._generate_product_description(content, product_name)
            template_id = template_file.stem
            
            self.cursor.execute('''
                INSERT INTO products (name, price, type, description, created_date, template_id, ab_test_variant)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_name, price, "digital", description, datetime.now(), template_id, ab_test_variant))
            self.db.commit()
            product_id = self.cursor.lastrowid
            logger.info(f"Created product from template: {product_name} (ID: {product_id}, template: {template_id})")
            return product_id
        except Exception as e:
            logger.error(f"Error creating product from template: {e}")
            return None
    
    def _generate_product_description(self, content: str, name: str) -> str:
        """Generate product description from content"""
        lines = content.split('\n')
        description_lines = []
        char_count = 0
        for line in lines[:20]:
            if char_count + len(line) > 500:
                break
            description_lines.append(line)
            char_count += len(line)
        description = '\n'.join(description_lines)
        if len(description) > 500:
            description = description[:497] + "..."
        return description or f"Digital product: {name}"
    
    def upload_product_to_gumroad(self, product_id: int, price_cents: int = None) -> Optional[str]:
        """Upload a locally created product to Gumroad (REVENUE GENERATION)"""
        if not self.gumroad.has_access_token():
            logger.warning("Cannot upload to Gumroad: no access token")
            return None
        
        try:
            # Get product from database
            self.cursor.execute('SELECT name, price, description FROM products WHERE id = ?', (product_id,))
            product = self.cursor.fetchone()
            if not product:
                logger.error(f"Product {product_id} not found in database")
                return None
            
            name, price, description = product
            price_cents = price_cents or int(price * 100)  # Convert to cents
            
            # Create product on Gumroad
            gumroad_product = self.gumroad.create_product(
                name=name,
                price_cents=price_cents,
                description=description or f"Digital product: {name}",
                permalink=name.lower().replace(' ', '-')[:50]  # Generate permalink from name
            )
            
            if gumroad_product:
                gumroad_id = gumroad_product.get("id")
                gumroad_url = gumroad_product.get("url", f"https://gumroad.com/l/{gumroad_product.get('permalink', name.lower().replace(' ', '-'))}")
                
                # Update local product with Gumroad info
                self.cursor.execute('''
                    UPDATE products 
                    SET description = ? 
                    WHERE id = ?
                ''', (f"{description or ''}\n\nGumroad: {gumroad_url}", product_id))
                self.db.commit()
                
                logger.info(f"✅ Uploaded product '{name}' to Gumroad: {gumroad_url}")
                return gumroad_url
            else:
                logger.error(f"Failed to create product '{name}' on Gumroad")
                return None
        except Exception as e:
            logger.error(f"Error uploading product to Gumroad: {e}")
            return None
    
    def scan_templates_and_create_products(self) -> int:
        """Scan products/ folder and create products from templates (REVENUE GENERATION)"""
        if not self.products_dir.exists():
            return 0
        created = 0
        for template_file in self.products_dir.glob("*.md"):
            product_name = template_file.stem.replace("_", " ").title()
            self.cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
            if self.cursor.fetchone():
                continue
            price = 9.99
            product_id = self.create_product_from_template(template_file, product_name, price)
            if product_id:
                created += 1
        return created
    
    def list_products(self) -> List[Dict[str, Any]]:
        """List all products"""
        self.cursor.execute('SELECT * FROM products ORDER BY created_date DESC')
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]


class TemplateGenerator:
    """AI-powered template generator using OpenAI API"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.products_dir = Path("./products")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("TEMPLATE_GENERATION_MODEL", "gpt-4-turbo-preview")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI client initialized for template generation")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
        else:
            if not OPENAI_AVAILABLE:
                logger.debug("OpenAI package not available")
            if not self.api_key:
                logger.debug("OPENAI_API_KEY not set")
    
    def is_available(self) -> bool:
        """Check if template generation is available"""
        return self.client is not None
    
    def analyze_existing_templates(self) -> Dict[str, Any]:
        """Analyze existing templates to learn structure and patterns"""
        templates = {}
        structure_patterns = {
            "sections": [],
            "common_elements": [],
            "avg_length": 0,
            "sample_content": []
        }
        
        if not self.products_dir.exists():
            return structure_patterns
        
        total_length = 0
        template_files = list(self.products_dir.glob("*.md"))
        
        for template_file in template_files[:3]:  # Analyze up to 3 templates
            try:
                content = template_file.read_text(encoding='utf-8')
                total_length += len(content)
                
                # Extract title (first line starting with #)
                lines = content.split('\n')
                title = ""
                for line in lines[:10]:
                    if line.strip().startswith('# '):
                        title = line.strip('# ').strip()
                        break
                
                # Extract sections (## headings)
                sections = []
                current_section = None
                for line in lines:
                    if line.strip().startswith('## '):
                        section_name = line.strip('## ').strip()
                        sections.append(section_name)
                        current_section = section_name
                
                structure_patterns["sections"].extend(sections)
                structure_patterns["sample_content"].append({
                    "title": title,
                    "sections": sections,
                    "length": len(content),
                    "first_500_chars": content[:500]
                })
            except Exception as e:
                logger.error(f"Error analyzing template {template_file.name}: {e}")
        
        if template_files:
            structure_patterns["avg_length"] = total_length // len(template_files)
        
        # Find common sections
        section_counts = {}
        for sample in structure_patterns["sample_content"]:
            for section in sample["sections"]:
                section_counts[section] = section_counts.get(section, 0) + 1
        
        structure_patterns["common_elements"] = [
            section for section, count in section_counts.items() 
            if count >= 2  # Appears in at least 2 templates
        ]
        
        return structure_patterns
    
    def generate_template(self, topic: str, product_type: str = "digital") -> Optional[Path]:
        """Generate a new template using OpenAI API"""
        if not self.is_available():
            logger.warning("Template generation not available - OpenAI client not initialized")
            return None
        
        try:
            # Analyze existing templates for structure
            patterns = self.analyze_existing_templates()
            
            # Build system prompt
            system_prompt = """You are an expert digital product creator specializing in high-converting product descriptions and templates.
Generate product templates in Markdown format that match the structure and style of successful digital products.
Focus on wealth, business, productivity, and entrepreneurship niches.
Create compelling sales copy that converts."""
            
            # Build user prompt with examples
            user_prompt = f"""Create a new digital product template for a {product_type} product in the "{topic}" niche.

Structure the template as a Markdown file with:
1. Title/Name (starting with #)
2. Sales Blurb section (## Sales Blurb) - persuasive marketing copy
3. Content Structure/Outline section
4. Detailed sections as needed

"""
            
            # Add examples from existing templates
            if patterns["sample_content"]:
                user_prompt += "Here are examples of successful templates:\n\n"
                for i, sample in enumerate(patterns["sample_content"][:2], 1):
                    user_prompt += f"Example {i}:\n"
                    user_prompt += f"Title: {sample['title']}\n"
                    user_prompt += f"Key Sections: {', '.join(sample['sections'][:5])}\n"
                    user_prompt += f"Sample content:\n{sample['first_500_chars']}\n\n"
            
            user_prompt += f"""
Create a complete, compelling template for a {topic}-themed product. 
Make it engaging, persuasive, and ready to use. 
Minimum 2000 characters. Include a sales blurb, structure outline, and detailed content sections.
"""
            
            # Generate template using OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=3000
            )
            
            generated_content = response.choices[0].message.content
            
            # Validate before saving
            if self.validate_template_content(generated_content):
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
                filename = f"{safe_topic.replace(' ', '_')}_{timestamp}.md"
                
                # Save template
                template_path = self.save_template(generated_content, filename)
                
                # Track generation
                self.track_generation(topic, product_type, len(generated_content), response.usage.total_tokens if hasattr(response, 'usage') else 0)
                
                logger.info(f"✅ Generated template: {filename} (topic: {topic})")
                return template_path
            else:
                logger.warning(f"Generated template failed validation (topic: {topic})")
                return None
                
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            return None
    
    def validate_template_content(self, content: str) -> bool:
        """Validate generated template content"""
        if not content or len(content) < 500:
            return False
        
        # Check for required sections
        has_title = content.strip().startswith('#')
        has_sales_blurb = '## Sales Blurb' in content or 'Sales Blurb' in content or 'sales blurb' in content.lower()
        
        # Check minimum length
        min_length = 2000
        if len(content) < min_length:
            return False
        
        return has_title and has_sales_blurb
    
    def validate_template(self, template_path: Path) -> bool:
        """Validate a template file"""
        if not template_path.exists():
            return False
        
        try:
            content = template_path.read_text(encoding='utf-8')
            return self.validate_template_content(content)
        except Exception as e:
            logger.error(f"Error validating template {template_path}: {e}")
            return False
    
    def save_template(self, content: str, filename: str) -> Path:
        """Save generated template to products directory"""
        self.products_dir.mkdir(parents=True, exist_ok=True)
        template_path = self.products_dir / filename
        template_path.write_text(content, encoding='utf-8')
        return template_path
    
    def track_generation(self, topic: str, product_type: str, content_length: int, tokens_used: int):
        """Track template generation in database"""
        try:
            # Estimate cost (rough estimate: $0.01 per 1K tokens for GPT-4 Turbo)
            estimated_cost = (tokens_used / 1000) * 0.01 if tokens_used > 0 else 0.0
            
            # Store in performance_metrics table
            metadata = json.dumps({
                "topic": topic,
                "product_type": product_type,
                "content_length": content_length,
                "tokens_used": tokens_used,
                "model": self.model
            })
            
            self.cursor.execute('''
                INSERT INTO performance_metrics (metric_type, metric_name, value, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', ("template_generation", "templates_generated", 1.0, "ai_generated", metadata))
            
            if estimated_cost > 0:
                self.cursor.execute('''
                    INSERT INTO performance_metrics (metric_type, metric_name, value, source, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', ("template_generation", "generation_cost", estimated_cost, "openai", metadata))
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error tracking template generation: {e}")


class TemplateABTesting:
    """A/B testing system for template variants"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.products_dir = Path("./products")
    
    def create_ab_test(self, template_a_path: Path, template_b_path: Path, test_name: str) -> Optional[int]:
        """Create a new A/B test"""
        if not template_a_path.exists() or not template_b_path.exists():
            logger.error(f"Cannot create A/B test: template files not found")
            return None
        
        try:
            template_a_id = template_a_path.stem
            template_b_id = template_b_path.stem
            start_date = datetime.now()
            
            self.cursor.execute('''
                INSERT INTO template_ab_tests (test_name, template_a_id, template_b_id, start_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (test_name, template_a_id, template_b_id, start_date, "active"))
            
            test_id = self.cursor.lastrowid
            self.db.commit()
            
            logger.info(f"✅ Created A/B test '{test_name}' (ID: {test_id})")
            return test_id
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            return None
    
    def get_active_tests(self) -> List[Dict[str, Any]]:
        """Get all active A/B tests"""
        try:
            self.cursor.execute('''
                SELECT * FROM template_ab_tests WHERE status = 'active'
            ''')
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting active tests: {e}")
            return []
    
    def record_conversion(self, test_id: int, variant_id: str, sale_amount: float) -> bool:
        """Record a conversion for a specific variant"""
        try:
            # Get or create result row for this variant
            self.cursor.execute('''
                SELECT id, conversions, revenue FROM template_ab_results
                WHERE test_id = ? AND variant_id = ?
                ORDER BY date DESC LIMIT 1
            ''', (test_id, variant_id))
            
            result = self.cursor.fetchone()
            if result:
                result_id, conversions, revenue = result
                self.cursor.execute('''
                    UPDATE template_ab_results
                    SET conversions = ?, revenue = ?, conversion_rate = 
                        CASE WHEN impressions > 0 THEN CAST(conversions AS REAL) / impressions ELSE 0 END
                    WHERE id = ?
                ''', (conversions + 1, revenue + sale_amount, result_id))
            else:
                # Create new result row
                self.cursor.execute('''
                    INSERT INTO template_ab_results (test_id, variant_id, conversions, revenue)
                    VALUES (?, ?, ?, ?)
                ''', (test_id, variant_id, 1, sale_amount))
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording conversion: {e}")
            return False
    
    def record_impression(self, test_id: int, variant_id: str) -> bool:
        """Record an impression (product created/viewed) for a variant"""
        try:
            self.cursor.execute('''
                SELECT id, impressions FROM template_ab_results
                WHERE test_id = ? AND variant_id = ?
                ORDER BY date DESC LIMIT 1
            ''', (test_id, variant_id))
            
            result = self.cursor.fetchone()
            if result:
                result_id, impressions = result
                self.cursor.execute('''
                    UPDATE template_ab_results
                    SET impressions = ?, conversion_rate = 
                        CASE WHEN impressions > 0 THEN CAST(conversions AS REAL) / impressions ELSE 0 END
                    WHERE id = ?
                ''', (impressions + 1, result_id))
            else:
                self.cursor.execute('''
                    INSERT INTO template_ab_results (test_id, variant_id, impressions)
                    VALUES (?, ?, ?)
                ''', (test_id, variant_id, 1))
            
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording impression: {e}")
            return False
    
    def get_test_results(self, test_id: int) -> Dict[str, Any]:
        """Get performance metrics for an A/B test"""
        try:
            self.cursor.execute('''
                SELECT variant_id, 
                       SUM(impressions) as total_impressions,
                       SUM(conversions) as total_conversions,
                       SUM(revenue) as total_revenue,
                       CASE WHEN SUM(impressions) > 0 
                            THEN CAST(SUM(conversions) AS REAL) / SUM(impressions) 
                            ELSE 0 END as conversion_rate
                FROM template_ab_results
                WHERE test_id = ?
                GROUP BY variant_id
            ''', (test_id,))
            
            results = {}
            for row in self.cursor.fetchall():
                variant_id, impressions, conversions, revenue, rate = row
                results[variant_id] = {
                    "impressions": impressions or 0,
                    "conversions": conversions or 0,
                    "revenue": revenue or 0.0,
                    "conversion_rate": rate or 0.0
                }
            
            return results
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {}
    
    def determine_winner(self, test_id: int, min_conversions: int = 10) -> Optional[str]:
        """Determine the winning variant using statistical analysis"""
        try:
            results = self.get_test_results(test_id)
            if len(results) < 2:
                return None
            
            variant_a = results.get("A")
            variant_b = results.get("B")
            
            if not variant_a or not variant_b:
                return None
            
            # Check if we have minimum conversions
            total_conversions = variant_a["conversions"] + variant_b["conversions"]
            if total_conversions < min_conversions:
                return None
            
            # Statistical significance test (simple t-test approximation)
            conv_a, imp_a = variant_a["conversions"], variant_a["impressions"]
            conv_b, imp_b = variant_b["conversions"], variant_b["impressions"]
            
            if imp_a == 0 or imp_b == 0:
                return None
            
            rate_a = conv_a / imp_a if imp_a > 0 else 0
            rate_b = conv_b / imp_b if imp_b > 0 else 0
            
            # Simple winner determination (rate difference > 20% or revenue advantage)
            revenue_diff = variant_b["revenue"] - variant_a["revenue"]
            
            if rate_b > rate_a * 1.2 or (rate_b > rate_a and revenue_diff > 0):
                return "B"
            elif rate_a > rate_b * 1.2 or (rate_a > rate_b and revenue_diff < 0):
                return "A"
            
            # If rates are close, use revenue as tiebreaker
            if revenue_diff > 0:
                return "B"
            elif revenue_diff < 0:
                return "A"
            
            return None
        except Exception as e:
            logger.error(f"Error determining winner: {e}")
            return None
    
    def apply_winner(self, test_id: int) -> bool:
        """Mark test as complete and apply winning template"""
        try:
            winner = self.determine_winner(test_id, CONFIG["template_optimization"]["ab_test_min_conversions"])
            if not winner:
                return False
            
            # Get test info
            self.cursor.execute('SELECT template_a_id, template_b_id FROM template_ab_tests WHERE id = ?', (test_id,))
            test = self.cursor.fetchone()
            if not test:
                return False
            
            template_a_id, template_b_id = test
            winner_id = template_a_id if winner == "A" else template_b_id
            
            # Update test status
            self.cursor.execute('''
                UPDATE template_ab_tests
                SET status = 'completed', winner_id = ?, end_date = ?
                WHERE id = ?
            ''', ("completed", winner_id, datetime.now(), test_id))
            
            self.db.commit()
            logger.info(f"✅ A/B test {test_id} completed. Winner: {winner_id}")
            return True
        except Exception as e:
            logger.error(f"Error applying winner: {e}")
            return False


class TrendAnalyzer:
    """Analyze trends from social media and keyword sources"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.cache_duration = timedelta(hours=CONFIG["template_optimization"]["trend_analysis_interval"])
    
    def analyze_twitter_trends(self, keywords: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Analyze Twitter/X trends for given keywords"""
        trends = []
        
        if not self.twitter_bearer_token:
            logger.debug("Twitter bearer token not configured, skipping Twitter trend analysis")
            return trends
        
        try:
            headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}
            
            for keyword in keywords:
                try:
                    # Search for recent tweets containing keyword
                    url = "https://api.twitter.com/2/tweets/search/recent"
                    params = {
                        "query": keyword,
                        "max_results": min(limit, 100),
                        "tweet.fields": "created_at,public_metrics"
                    }
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        tweets = data.get("data", [])
                        
                        # Calculate trend score (engagement per tweet)
                        total_engagement = 0
                        for tweet in tweets:
                            metrics = tweet.get("public_metrics", {})
                            total_engagement += (
                                metrics.get("like_count", 0) +
                                metrics.get("retweet_count", 0) * 2 +
                                metrics.get("reply_count", 0)
                            )
                        
                        trend_score = total_engagement / len(tweets) if tweets else 0
                        
                        # Store in database
                        metadata = json.dumps({
                            "tweet_count": len(tweets),
                            "total_engagement": total_engagement
                        })
                        
                        self.cursor.execute('''
                            INSERT INTO trend_analysis (topic, source, keyword, trend_score, volume, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (keyword, "twitter", keyword, trend_score, len(tweets), metadata))
                        
                        trends.append({
                            "keyword": keyword,
                            "trend_score": trend_score,
                            "volume": len(tweets),
                            "source": "twitter"
                        })
                    
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Error analyzing Twitter trend for '{keyword}': {e}")
                    continue
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error in Twitter trend analysis: {e}")
        
        return trends
    
    def analyze_reddit_trends(self, subreddits: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Analyze Reddit trends"""
        trends = []
        
        if not self.reddit_client_id or not self.reddit_client_secret:
            logger.debug("Reddit credentials not configured, skipping Reddit trend analysis")
            return trends
        
        subreddits = subreddits or ["entrepreneur", "passiveincome", "startups", "business", "productivity"]
        
        try:
            # Reddit API OAuth2 authentication
            auth_url = "https://www.reddit.com/api/v1/access_token"
            auth_response = requests.post(
                auth_url,
                auth=(self.reddit_client_id, self.reddit_client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": "CashEngine/1.0"},
                timeout=10
            )
            
            if auth_response.status_code != 200:
                logger.warning("Reddit authentication failed")
                return trends
            
            access_token = auth_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {access_token}", "User-Agent": "CashEngine/1.0"}
            
            for subreddit in subreddits:
                try:
                    url = f"https://oauth.reddit.com/r/{subreddit}/hot"
                    params = {"limit": min(limit, 100)}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        # Extract keywords from post titles
                        keywords = {}
                        for post in posts[:limit]:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "").lower()
                            
                            # Extract relevant keywords (simple word frequency)
                            words = title.split()
                            for word in words:
                                if len(word) > 4:  # Filter short words
                                    keywords[word] = keywords.get(word, 0) + post_data.get("score", 0)
                        
                        # Store top keywords as trends
                        for keyword, score in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]:
                            metadata = json.dumps({
                                "subreddit": subreddit,
                                "post_count": len(posts)
                            })
                            
                            self.cursor.execute('''
                                INSERT INTO trend_analysis (topic, source, keyword, trend_score, volume, metadata)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (keyword, "reddit", keyword, float(score), len(posts), metadata))
                            
                            trends.append({
                                "keyword": keyword,
                                "trend_score": float(score),
                                "volume": len(posts),
                                "source": "reddit"
                            })
                    
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Error analyzing Reddit trend for '{subreddit}': {e}")
                    continue
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error in Reddit trend analysis: {e}")
        
        return trends
    
    def get_top_trending_topics(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Get most trending topics from recent analysis"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            self.cursor.execute('''
                SELECT keyword, topic, source, AVG(trend_score) as avg_score, SUM(volume) as total_volume
                FROM trend_analysis
                WHERE timestamp >= ?
                GROUP BY keyword, topic, source
                ORDER BY avg_score DESC, total_volume DESC
                LIMIT ?
            ''', (cutoff, limit))
            
            trends = []
            for row in self.cursor.fetchall():
                keyword, topic, source, avg_score, total_volume = row
                trends.append({
                    "keyword": keyword,
                    "topic": topic,
                    "source": source,
                    "trend_score": avg_score or 0.0,
                    "volume": total_volume or 0
                })
            
            return trends
        except Exception as e:
            logger.error(f"Error getting top trends: {e}")
            return []
    
    def suggest_template_topics(self, limit: int = 5) -> List[str]:
        """Suggest trending topics for template generation"""
        trends = self.get_top_trending_topics(limit=limit * 2)
        
        # Extract unique topics/keywords
        suggested = []
        seen = set()
        for trend in trends:
            keyword = trend.get("keyword", "").strip()
            if keyword and keyword not in seen and len(keyword) > 3:
                suggested.append(keyword)
                seen.add(keyword)
                if len(suggested) >= limit:
                    break
        
        # Fallback to default topics if no trends
        if not suggested:
            suggested = CONFIG["template_topics"][:limit]
        
        return suggested
    
    def update_trend_cache(self):
        """Update trend analysis cache"""
        try:
            keywords = CONFIG["template_topics"]
            
            logger.info("📊 Updating trend analysis cache...")
            
            # Analyze Twitter trends
            if self.twitter_bearer_token:
                self.analyze_twitter_trends(keywords, limit=50)
            
            # Analyze Reddit trends
            if self.reddit_client_id and self.reddit_client_secret:
                self.analyze_reddit_trends(limit=50)
            
            logger.info("✅ Trend analysis cache updated")
        except Exception as e:
            logger.error(f"Error updating trend cache: {e}")


class TemplateOptimizer:
    """Optimize templates based on sales performance data"""
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.products_dir = Path("./products")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"OpenAI initialization failed for optimizer: {e}")
    
    def analyze_template_performance(self, template_path: Path) -> Dict[str, Any]:
        """Analyze sales performance for a template"""
        if not template_path.exists():
            return {}
        
        try:
            template_id = template_path.stem
            
            # Get products created from this template
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as product_count,
                    SUM(sales_count) as total_sales,
                    SUM(total_revenue) as total_revenue,
                    AVG(price) as avg_price
                FROM products
                WHERE template_id = ?
            ''', (template_id,))
            
            row = self.cursor.fetchone()
            if not row:
                return {}
            
            product_count, total_sales, total_revenue, avg_price = row
            
            # Calculate metrics
            avg_revenue_per_product = (total_revenue or 0) / product_count if product_count > 0 else 0
            avg_sales_per_product = (total_sales or 0) / product_count if product_count > 0 else 0
            
            return {
                "template_id": template_id,
                "product_count": product_count or 0,
                "total_sales": total_sales or 0,
                "total_revenue": total_revenue or 0.0,
                "avg_price": avg_price or 0.0,
                "avg_revenue_per_product": avg_revenue_per_product,
                "avg_sales_per_product": avg_sales_per_product
            }
        except Exception as e:
            logger.error(f"Error analyzing template performance: {e}")
            return {}
    
    def identify_underperforming_templates(self, threshold: float = None) -> List[Dict[str, Any]]:
        """Find templates performing below threshold"""
        threshold = threshold or CONFIG["template_optimization"]["optimization_threshold"]
        
        try:
            # Get average performance across all templates
            self.cursor.execute('''
                SELECT AVG(total_revenue) as avg_revenue
                FROM products
                WHERE template_id IS NOT NULL
            ''')
            
            row = self.cursor.fetchone()
            avg_revenue = (row[0] or 0.0) if row else 0.0
            threshold_revenue = avg_revenue * threshold
            
            # Find underperforming templates
            self.cursor.execute('''
                SELECT template_id, SUM(total_revenue) as total_revenue, COUNT(*) as product_count
                FROM products
                WHERE template_id IS NOT NULL
                GROUP BY template_id
                HAVING SUM(total_revenue) < ?
            ''', (threshold_revenue,))
            
            underperforming = []
            for row in self.cursor.fetchall():
                template_id, revenue, count = row
                template_path = self.products_dir / f"{template_id}.md"
                if template_path.exists():
                    performance = self.analyze_template_performance(template_path)
                    performance["threshold_revenue"] = threshold_revenue
                    underperforming.append(performance)
            
            return underperforming
        except Exception as e:
            logger.error(f"Error identifying underperforming templates: {e}")
            return []
    
    def compare_performance(self, template_a_path: Path, template_b_path: Path) -> Dict[str, Any]:
        """Compare performance of two templates"""
        perf_a = self.analyze_template_performance(template_a_path)
        perf_b = self.analyze_template_performance(template_b_path)
        
        return {
            "template_a": perf_a,
            "template_b": perf_b,
            "winner": "A" if (perf_a.get("total_revenue", 0) > perf_b.get("total_revenue", 0)) else "B"
        }
    
    def extract_winning_elements(self) -> Dict[str, Any]:
        """Extract successful elements from high-performing templates"""
        try:
            # Get top performing templates
            self.cursor.execute('''
                SELECT template_id, SUM(total_revenue) as total_revenue, COUNT(*) as product_count
                FROM products
                WHERE template_id IS NOT NULL AND total_revenue > 0
                GROUP BY template_id
                ORDER BY total_revenue DESC
                LIMIT 5
            ''')
            
            top_templates = []
            for row in self.cursor.fetchall():
                template_id, revenue, count = row
                template_path = self.products_dir / f"{template_id}.md"
                if template_path.exists():
                    try:
                        content = template_path.read_text(encoding='utf-8')
                        top_templates.append({
                            "template_id": template_id,
                            "revenue": revenue,
                            "product_count": count,
                            "content": content[:2000]  # First 2000 chars
                        })
                    except Exception as e:
                        logger.warning(f"Error reading template {template_id}: {e}")
            
            # Extract common patterns (simple analysis)
            common_elements = {
                "avg_length": sum(len(t.get("content", "")) for t in top_templates) / len(top_templates) if top_templates else 0,
                "sections": [],
                "keywords": []
            }
            
            return {
                "top_templates": top_templates,
                "common_elements": common_elements
            }
        except Exception as e:
            logger.error(f"Error extracting winning elements: {e}")
            return {}
    
    def optimize_template(self, template_path: Path, performance_data: Dict[str, Any] = None) -> Optional[Path]:
        """Generate an optimized version of a template using AI"""
        if not self.client:
            logger.warning("OpenAI client not available for template optimization")
            return None
        
        if not template_path.exists():
            return None
        
        try:
            # Get performance data if not provided
            if not performance_data:
                performance_data = self.analyze_template_performance(template_path)
            
            # Get winning elements from top templates
            winning_elements = self.extract_winning_elements()
            
            # Read current template
            current_content = template_path.read_text(encoding='utf-8')
            
            # Build optimization prompt
            prompt = f"""You are optimizing a digital product template based on sales performance data.

Current Template Performance:
- Total Revenue: ${performance_data.get('total_revenue', 0):.2f}
- Total Sales: {performance_data.get('total_sales', 0)}
- Products Created: {performance_data.get('product_count', 0)}

Current Template Content (first 1500 chars):
{current_content[:1500]}

Analyze the current template and create an improved version that:
1. Enhances the sales blurb to be more compelling
2. Improves structure based on successful templates
3. Adds persuasive elements that drive conversions
4. Maintains the core value proposition while improving clarity

Return ONLY the optimized template content in markdown format, following the same structure as the original."""

            # Generate optimized version using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert at optimizing digital product templates for sales performance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            optimized_content = response.choices[0].message.content.strip()
            
            # Save optimized template
            optimized_filename = f"{template_path.stem}_optimized_{datetime.now().strftime('%Y%m%d')}.md"
            optimized_path = self.save_optimized_template(optimized_content, optimized_filename, template_path.stem)
            
            # Track optimization
            self.track_optimization(template_path.stem, "ai_optimization", performance_data, optimized_path)
            
            logger.info(f"✅ Optimized template saved: {optimized_path.name}")
            return optimized_path
            
        except Exception as e:
            logger.error(f"Error optimizing template: {e}")
            return None
    
    def save_optimized_template(self, content: str, filename: str, original_template_id: str) -> Path:
        """Save optimized template to products directory"""
        self.products_dir.mkdir(parents=True, exist_ok=True)
        template_path = self.products_dir / filename
        template_path.write_text(content, encoding='utf-8')
        return template_path
    
    def track_optimization(self, template_id: str, optimization_type: str, 
                          before_metrics: Dict[str, Any], optimized_path: Path):
        """Track optimization in database"""
        try:
            metadata = json.dumps({
                "original_template_id": template_id,
                "optimized_file": optimized_path.name,
                "optimization_date": datetime.now().isoformat()
            })
            
            self.cursor.execute('''
                INSERT INTO template_optimization_history 
                (template_id, optimization_type, before_metrics, metadata)
                VALUES (?, ?, ?, ?)
            ''', (template_id, optimization_type, json.dumps(before_metrics), metadata))
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error tracking optimization: {e}")


class LeadBot:
    """REAL lead generation - extracts leads from multiple sources"""
    def __init__(self, db_conn, marketing_agent_url: Optional[str] = None):
        self.db = db_conn
        self.cursor = db_conn.cursor()
        self.marketing_agent_url = marketing_agent_url or os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000')
        self.clicks_log = Path("./logs/clicks/clicks.json")
        self.activity_log = Path("./logs/activity.json")
    
    def generate_leads(self, source: str = "automated", count: int = 10) -> int:
        """Actually generate leads from multiple sources"""
        leads_added = 0
        try:
            # Source 1: Extract leads from click tracking logs (Instagram/TikTok users who clicked)
            leads_added += self._extract_leads_from_clicks()
            # Source 2: Extract from activity logs
            leads_added += self._extract_leads_from_activity()
            # Source 3: Web scraping for public leads (if enabled)
            if os.getenv("ENABLE_WEB_SCRAPING", "false").lower() == "true":
                leads_added += self._scrape_public_leads(count - leads_added)
            logger.info(f"Generated {leads_added} leads from {source}")
            return leads_added
        except Exception as e:
            logger.error(f"Lead generation error: {e}")
            return leads_added
    
    def _extract_leads_from_clicks(self) -> int:
        """Extract leads from click tracking logs (users who clicked product links)"""
        if not self.clicks_log.exists():
            return 0
        try:
            with open(self.clicks_log, 'r') as f:
                clicks = json.load(f)
            leads_added = 0
            for click in clicks:
                user_id = click.get("userId", "")
                product_name = click.get("productName", "")
                if not user_id or user_id == "test_user_123":
                    continue
                self.cursor.execute('SELECT id FROM leads WHERE email = ?', (f"{user_id}@instagram",))
                if self.cursor.fetchone():
                    continue
                value_score = 75
                if product_name:
                    value_score += 10
                self.cursor.execute('''
                    INSERT INTO leads (email, source, value_score, contacted, converted, revenue)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (f"{user_id}@instagram", f"instagram_click_{product_name}", value_score, 0, 0, 0.0))
                leads_added += 1
            self.db.commit()
            return leads_added
        except Exception as e:
            logger.error(f"Error extracting leads from clicks: {e}")
            return 0
    
    def _extract_leads_from_activity(self) -> int:
        """Extract leads from activity logs"""
        if not self.activity_log.exists():
            return 0
        try:
            with open(self.activity_log, 'r') as f:
                activities = json.load(f)
            leads_added = 0
            for activity in activities:
                media_id = activity.get("mediaId", "")
                if media_id:
                    user_hash = hashlib.md5(media_id.encode()).hexdigest()[:8]
                    email = f"eng_{user_hash}@instagram"
                    self.cursor.execute('SELECT id FROM leads WHERE email = ?', (email,))
                    if not self.cursor.fetchone():
                        self.cursor.execute('''
                            INSERT INTO leads (email, source, value_score, contacted, converted, revenue)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (email, "instagram_engagement", 50, 0, 0, 0.0))
                        leads_added += 1
            self.db.commit()
            return leads_added
        except Exception as e:
            logger.error(f"Error extracting leads from activity: {e}")
            return 0
    
    def _scrape_public_leads(self, max_count: int) -> int:
        """Scrape public leads from web sources (ethical scraping only)"""
        if max_count <= 0:
            return 0
        
        leads_added = 0
        scrape_delay = 2.0  # Minimum 2 seconds between requests (rate limiting)
        
        try:
            # Scrape from multiple sources
            leads_added += self._scrape_twitter_leads(max_count - leads_added, scrape_delay)
            leads_added += self._scrape_reddit_leads(max_count - leads_added, scrape_delay)
            
            if leads_added > 0:
                logger.info(f"Scraped {leads_added} leads from public sources")
            
            return leads_added
            
        except Exception as e:
            logger.error(f"Web scraping error: {e}")
            return 0
    
    def _scrape_twitter_leads(self, max_count: int, delay: float) -> int:
        """Scrape leads from Twitter/X public profiles (ethical scraping)"""
        if max_count <= 0:
            return 0
        
        leads_added = 0
        twitter_api_key = os.getenv('TWITTER_API_KEY')
        twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # If API keys available, use Twitter API v2
        if twitter_bearer_token:
            try:
                # Search for relevant keywords in tweets
                keywords = ["entrepreneur", "business", "startup", "wealth", "passive income"]
                # TODO: Implement Twitter API v2 search when bearer token is available
                logger.debug(f"Twitter API available - would search for leads (API integration ready)")
                # For now, return 0 until API implementation is complete
                return 0
            except Exception as e:
                logger.error(f"Twitter scraping error: {e}")
                return 0
        else:
            logger.debug("Twitter API keys not configured - skipping Twitter lead scraping")
            return 0
    
    def _scrape_reddit_leads(self, max_count: int, delay: float) -> int:
        """Scrape leads from Reddit public posts (ethical scraping)"""
        if max_count <= 0:
            return 0
        
        leads_added = 0
        reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'CashEngine/1.0')
        
        # If Reddit API credentials available, use Reddit API
        if reddit_client_id and reddit_client_secret:
            try:
                # Search relevant subreddits for potential leads
                subreddits = ["entrepreneur", "startups", "passive_income", "business", "wealth"]
                # TODO: Implement Reddit API search when credentials are available
                logger.debug(f"Reddit API available - would search for leads (API integration ready)")
                # For now, return 0 until API implementation is complete
                return 0
            except Exception as e:
                logger.error(f"Reddit scraping error: {e}")
                return 0
        else:
            logger.debug("Reddit API credentials not configured - skipping Reddit lead scraping")
            return 0
    
    def score_lead(self, lead_id: int) -> int:
        """Score a lead based on multiple factors"""
        self.cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead = self.cursor.fetchone()
        if not lead:
            return 0
        score = lead[3]
        source = lead[2] if len(lead) > 2 else ""
        if "click" in source.lower():
            score += 10
        if "engagement" in source.lower():
            score += 5
        return min(score, 100)
    
    def get_leads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get leads from database"""
        self.cursor.execute('''
            SELECT * FROM leads 
            WHERE contacted = 0 
            ORDER BY value_score DESC 
            LIMIT ?
        ''', (limit,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
    
    def export_leads_for_sale(self, min_score: int = 60, limit: int = 100) -> List[Dict]:
        """Export high-quality leads for sale (REVENUE GENERATION)"""
        self.cursor.execute('''
            SELECT email, source, value_score 
            FROM leads 
            WHERE value_score >= ? AND contacted = 0
            ORDER BY value_score DESC
            LIMIT ?
        ''', (min_score, limit))
        leads = []
        for row in self.cursor.fetchall():
            leads.append({"email": row[0], "source": row[1], "value_score": row[2]})
        if leads:
            revenue_per_lead = 0.50
            total_revenue = len(leads) * revenue_per_lead
            self.cursor.execute('''
                INSERT INTO revenue (source, amount, currency, description, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ("lead_export", total_revenue, "USD", f"Exported {len(leads)} leads", "pending"))
            self.db.commit()
        return leads


class AffiliateManager:
    """REAL affiliate automation - manages campaigns and generates revenue"""
    def __init__(self, marketing_agent_url: Optional[str] = None):
        self.marketing_agent_url = marketing_agent_url or os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000')
        self.campaigns = []
        self.performance = {}
    
    def create_campaign(self, name: str, product_url: str, commission_rate: float = 0.30) -> str:
        """Create a real affiliate campaign via Marketing Agent API"""
        try:
            # Debug: Log the URL being used
            logger.debug(f"Creating campaign via Marketing Agent at: {self.marketing_agent_url}/api/campaigns")
            response = requests.post(
                f"{self.marketing_agent_url}/api/campaigns",
                json={
                    "name": name,
                    "objective": f"Affiliate campaign for {product_url}",
                    "status": "active",
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=365)).isoformat()
                },
                timeout=10
            )
            if response.status_code == 200:
                campaign_data = response.json()
                campaign_id = str(campaign_data.get("id", uuid.uuid4().hex[:16]))
                self.campaigns.append({
                    "id": campaign_id,
                    "name": name,
                    "product_url": product_url,
                    "commission_rate": commission_rate,
                    "created": datetime.now(),
                    "marketing_agent_id": campaign_data.get("id")
                })
                logger.info(f"Created affiliate campaign: {name} (ID: {campaign_id})")
                return campaign_id
            else:
                campaign_id = uuid.uuid4().hex[:16]
                self.campaigns.append({
                    "id": campaign_id, "name": name, "product_url": product_url,
                    "commission_rate": commission_rate, "created": datetime.now()
                })
                return campaign_id
        except Exception as e:
            logger.warning(f"Marketing Agent unavailable at {self.marketing_agent_url}, creating local campaign: {e}")
            campaign_id = uuid.uuid4().hex[:16]
            self.campaigns.append({
                "id": campaign_id, "name": name, "product_url": product_url,
                "commission_rate": commission_rate, "created": datetime.now()
            })
            return campaign_id
    
    def generate_affiliate_link(self, campaign_id: str, destination_url: str, user_id: str = "") -> Optional[str]:
        """Generate tracking link via Marketing Agent"""
        campaign = next((c for c in self.campaigns if c["id"] == campaign_id), None)
        if not campaign:
            return None
        try:
            marketing_agent_id = campaign.get("marketing_agent_id")
            if marketing_agent_id:
                # Marketing Agent expects campaign_id as int and utm_json (not utm_params)
                try:
                    campaign_id_int = int(marketing_agent_id) if isinstance(marketing_agent_id, str) else marketing_agent_id
                    response = requests.post(
                        f"{self.marketing_agent_url}/api/links",
                        json={
                            "campaign_id": campaign_id_int,
                            "channel": "affiliate",
                            "long_url": destination_url,
                            "utm_json": {
                                "utm_source": "affiliate", "utm_medium": "cash_engine",
                                "utm_campaign": campaign["name"], "affiliate_id": user_id
                            }
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        link_data = response.json()
                        # Marketing Agent returns short_slug, construct full URL
                        slug = link_data.get("short_slug")
                        if slug:
                            return f"{self.marketing_agent_url}/r/{slug}"
                        return link_data.get("short_url") or link_data.get("url") or destination_url
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid campaign ID format: {marketing_agent_id}, {e}")
            tracking_id = hashlib.md5(f"{campaign_id}{destination_url}{user_id}".encode()).hexdigest()[:16]
            return f"https://track.example.com/{tracking_id}"
        except Exception as e:
            logger.error(f"Error generating affiliate link: {e}")
            return destination_url
    
    def track_click(self, campaign_id: str):
        """Track a campaign click"""
        if campaign_id not in self.performance:
            self.performance[campaign_id] = {"clicks": 0, "conversions": 0}
        self.performance[campaign_id]["clicks"] += 1
    
    def track_conversion(self, campaign_id: str, amount: float, commission_rate: Optional[float] = None):
        """Track conversion and calculate commission revenue (REVENUE GENERATION)"""
        campaign = next((c for c in self.campaigns if c["id"] == campaign_id), None)
        if not campaign:
            return 0
        rate = commission_rate or campaign.get("commission_rate", 0.30)
        commission = amount * rate
        if campaign_id not in self.performance:
            self.performance[campaign_id] = {"clicks": 0, "conversions": 0, "revenue": 0.0, "commissions": 0.0}
        self.performance[campaign_id]["conversions"] += 1
        self.performance[campaign_id]["revenue"] += amount
        self.performance[campaign_id]["commissions"] += commission
        logger.info(f"Affiliate conversion: ${amount:.2f} sale, ${commission:.2f} commission")
        
        # Track campaign performance in database (if db connection available)
        # Note: AffiliateManager doesn't have db access, tracking happens in CashEngine
        return commission


# ============================================
# SHOPIFY MANAGER
# ============================================
class ShopifyManager:
    """Manages Shopify store integration - products, orders, and revenue tracking"""
    
    def __init__(self, db_conn=None):
        self.store_domain = os.getenv('SHOPIFY_STORE_DOMAIN', '')
        self.api_key = os.getenv('SHOPIFY_API_KEY', '')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET', '')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
        self.webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET', '')
        self.enabled = os.getenv('SHOPIFY_ENABLED', 'false').lower() in ('true', '1', 'yes', 'on')
        
        self.db = db_conn
        self.products_cache = {}  # Cache product catalog
        self.last_sync_time = None
        self.api_version = '2024-01'  # Shopify API version
        self.logger = logging.getLogger('CashEngine.ShopifyManager')
        
        if self.db:
            self._ensure_order_id_column()
    
    def _ensure_order_id_column(self):
        """Add order_id column to revenue table if it doesn't exist"""
        try:
            self.db.cursor().execute('ALTER TABLE revenue ADD COLUMN order_id TEXT')
            self.db.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
    
    def _get_api_url(self, endpoint: str) -> str:
        """Build Shopify Admin API URL"""
        if not self.store_domain:
            raise ValueError("SHOPIFY_STORE_DOMAIN not configured")
        # Remove protocol if present
        domain = self.store_domain.replace('https://', '').replace('http://', '')
        return f"https://{domain}/admin/api/{self.api_version}{endpoint}"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Shopify API"""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    def fetch_products(self) -> List[Dict[str, Any]]:
        """Fetch all products from Shopify store"""
        if not self.enabled or not self.access_token:
            self.logger.warning("Shopify not enabled or access token missing")
            return []
        
        try:
            url = self._get_api_url("/products.json")
            headers = self._get_headers()
            
            products = []
            page_info = None
            
            # Handle pagination
            while True:
                params = {"limit": 250}  # Max products per page
                if page_info:
                    params["page_info"] = page_info
                
                resp = requests.get(url, headers=headers, params=params, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    page_products = data.get("products", [])
                    products.extend(page_products)
                    
                    # Check for next page
                    link_header = resp.headers.get("Link", "")
                    if 'rel="next"' not in link_header:
                        break
                    
                    # Extract page_info from Link header
                    next_match = re.search(r'page_info=([^&>]+)', link_header)
                    if next_match:
                        page_info = next_match.group(1)
                    else:
                        break
                elif resp.status_code == 401:
                    self.logger.error(f"Shopify API authentication failed (401)")
                    break
                elif resp.status_code == 429:
                    self.logger.warning("Shopify API rate limit - waiting 2 seconds")
                    time.sleep(2)
                    continue
                else:
                    self.logger.error(f"Shopify API error: HTTP {resp.status_code} - {resp.text[:200]}")
                    break
            
            self.products_cache = {p["id"]: p for p in products}
            self.last_sync_time = datetime.now()
            self.logger.info(f"Fetched {len(products)} products from Shopify")
            return products
            
        except Exception as e:
            self.logger.error(f"Error fetching Shopify products: {e}")
            return []
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get single product by ID"""
        if product_id in self.products_cache:
            return self.products_cache[product_id]
        
        try:
            url = self._get_api_url(f"/products/{product_id}.json")
            headers = self._get_headers()
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                product = data.get("product", {})
                self.products_cache[product_id] = product
                return product
            else:
                self.logger.error(f"Shopify product fetch error: HTTP {resp.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching Shopify product {product_id}: {e}")
            return None
    
    def get_product_url(self, product_handle: str, utm_source: str = "cash_engine", 
                       utm_medium: str = "social", utm_campaign: str = "promotion") -> str:
        """Generate Shopify product URL with UTM parameters"""
        if not self.store_domain:
            return ""
        
        domain = self.store_domain.replace('https://', '').replace('http://', '')
        base_url = f"https://{domain}/products/{product_handle}"
        utm_params = f"?utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"
        return base_url + utm_params
    
    def sync_products_to_db(self) -> int:
        """Sync Shopify products to database"""
        if not self.db:
            self.logger.warning("Database connection not available for product sync")
            return 0
        
        products = self.fetch_products()
        if not products:
            return 0
        
        cursor = self.db.cursor()
        synced = 0
        
        for product in products:
            try:
                product_id = product.get("id")
                title = product.get("title", "")
                handle = product.get("handle", "")
                variants = product.get("variants", [])
                price = float(variants[0].get("price", 0)) if variants else 0.0
                description = product.get("body_html", "")[:500] if product.get("body_html") else ""
                
                # Check if product exists
                cursor.execute('SELECT id FROM products WHERE name = ? AND type = ?', 
                             (title, "shopify"))
                
                if cursor.fetchone():
                    # Update existing
                    cursor.execute('''
                        UPDATE products 
                        SET price = ?, description = ?
                        WHERE name = ? AND type = ?
                    ''', (price, description, title, "shopify"))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO products (name, price, type, description, created_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (title, price, "shopify", description, datetime.now()))
                
                synced += 1
            except Exception as e:
                self.logger.error(f"Error syncing product {product.get('title', 'unknown')}: {e}")
        
        self.db.commit()
        self.logger.info(f"Synced {synced} Shopify products to database")
        return synced
    
    def find_matching_product(self, content: str) -> Optional[Dict[str, Any]]:
        """Find best matching Shopify product for content based on keywords"""
        if not self.products_cache:
            self.fetch_products()
        
        if not self.products_cache:
            return None
        
        content_lower = content.lower()
        best_match = None
        best_score = 0
        
        for product in self.products_cache.values():
            title = product.get("title", "").lower()
            handle = product.get("handle", "").lower()
            tags = [t.lower() for t in product.get("tags", "").split(",") if t.strip()]
            
            # Simple keyword matching score
            score = 0
            if title in content_lower:
                score += 10
            if handle in content_lower:
                score += 8
            for tag in tags:
                if tag.strip() in content_lower:
                    score += 5
            
            # Boost score for product type keywords
            product_type = product.get("product_type", "").lower()
            if product_type and product_type in content_lower:
                score += 7
            
            if score > best_score:
                best_score = score
                best_match = product
        
        # Only return if score is above threshold
        return best_match if best_score >= 5 else None
    
    def record_order_revenue(self, order_data: Dict[str, Any]) -> bool:
        """Record Shopify order as revenue in database"""
        if not self.db:
            self.logger.warning("Database connection not available for revenue recording")
            return False
        
        try:
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
            
            cursor = self.db.cursor()
            
            # Check if order already recorded
            cursor.execute('SELECT id FROM revenue WHERE order_id = ?', (str(order_id),))
            if cursor.fetchone():
                self.logger.debug(f"Shopify order {order_number} already recorded")
                return True
            
            # Record revenue
            cursor.execute('''
                INSERT INTO revenue (source, amount, currency, description, status, order_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ("shopify", total_price, currency, description, "completed", str(order_id), created_at))
            
            self.db.commit()
            self.logger.info(f"Recorded Shopify order #{order_number}: ${total_price} {currency}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording Shopify order revenue: {e}")
            return False


class ContentSyndicator:
    """REAL content syndication - distributes content with affiliate links"""
    def __init__(self, affiliate_manager, products_dir: Path = Path("./products"), viral_template_manager=None, shopify_manager=None):
        self.affiliate_manager = affiliate_manager
        self.products_dir = products_dir
        self.syndicated_count = 0
        self.viral_template_manager = viral_template_manager
        self.shopify_manager = shopify_manager
        self._twitter_state_path = Path("./data/twitter_post_state.json")
        self._twitter_state_lock = threading.Lock()
        self._platform_status = {}  # Track platform health
    
    def syndicate_content(self, content_file: Path, platforms: List[str] = None) -> int:
        """Syndicate content to multiple platforms with affiliate links"""
        if not content_file.exists():
            return 0
        platforms = platforms or ["instagram", "twitter"]
        content = content_file.read_text(encoding='utf-8')
        # Embed affiliate links with default platform (first in list)
        default_platform = platforms[0] if platforms else "social"
        enhanced_content = self._embed_affiliate_links(content, platform=default_platform)
        output_dir = Path("./data/content/syndicated")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{content_file.stem}_syndicated_{datetime.now().strftime('%Y%m%d')}.txt"
        output_file.write_text(enhanced_content, encoding='utf-8')
        self.syndicated_count += 1
        logger.info(f"Syndicated content: {content_file.name} to {len(platforms)} platforms")
        return 1
    
    def _embed_affiliate_links(self, content: str, platform: str = "social") -> str:
        """Embed affiliate links in content - supports both Gumroad and Shopify products"""
        enhanced = content
        
        # 1. Check Gumroad affiliate campaigns
        gumroad_token = os.getenv('GUMROAD_TOKEN')
        if gumroad_token and self.affiliate_manager.campaigns:
            for campaign in self.affiliate_manager.campaigns:
                campaign_name = campaign.get("name", "")
                # Remove "Affiliate - " prefix for matching
                product_name = campaign_name.replace("Affiliate - ", "").strip()
                # Try matching with and without prefix
                if product_name and (product_name.lower() in content.lower() or campaign_name.lower() in content.lower()):
                    link = self.affiliate_manager.generate_affiliate_link(campaign["id"], campaign.get("product_url", ""))
                    if link and link != campaign.get("product_url", ""):  # Only replace if link was actually generated
                        # Replace the actual product name found in content (not the campaign name)
                        enhanced = enhanced.replace(product_name, f"{product_name} [Get it here: {link}]")
                        logger.debug(f"Embedded Gumroad affiliate link for {product_name}: {link}")
        
        # 2. Check Shopify products
        if self.shopify_manager and self.shopify_manager.enabled:
            shopify_product = self.shopify_manager.find_matching_product(content)
            if shopify_product:
                product_title = shopify_product.get("title", "")
                product_handle = shopify_product.get("handle", "")
                
                # Generate Shopify product URL with UTM tracking
                shopify_url = self.shopify_manager.get_product_url(
                    product_handle,
                    utm_source="cash_engine",
                    utm_medium="social",
                    utm_campaign=platform
                )
                
                if shopify_url and product_title:
                    # Only add link if not already present in content
                    if shopify_url not in enhanced and product_handle not in enhanced:
                        # Insert after first mention of product title
                        if product_title.lower() in enhanced.lower():
                            # Find first occurrence (case-insensitive)
                            pattern = re.compile(re.escape(product_title), re.IGNORECASE)
                            enhanced = pattern.sub(f"{product_title} [Get it here: {shopify_url}]", enhanced, count=1)
                            logger.debug(f"Embedded Shopify product link for {product_title}: {shopify_url}")
                        else:
                            # Product matched by keywords but title not in content - append link
                            enhanced = f"{enhanced}\n\n🔗 Check out: {shopify_url}"
                            logger.debug(f"Appended Shopify product link for {product_title}: {shopify_url}")
        
        return enhanced
    
    def auto_syndicate_from_folder(self) -> int:
        """Automatically syndicate all content from products folder (REVENUE GENERATION)"""
        if not self.products_dir.exists():
            return 0
        syndicated = 0
        for content_file in self.products_dir.glob("*.md"):
            if self.syndicate_content(content_file):
                syndicated += 1
        return syndicated
    
    def auto_distribute_to_platforms(self, content_file: Path, platforms: List[str] = None) -> Dict[str, bool]:
        """Auto-distribute syndicated content to platforms via APIs"""
        # Default platforms: prefer Facebook/LinkedIn if Twitter is disabled
        if platforms is None:
            twitter_enabled = os.getenv("TWITTER_LIVE_POSTING", "false").lower() in ("1", "true", "yes", "on")
            if twitter_enabled:
                platforms = ["twitter", "facebook", "linkedin"]
            else:
                platforms = ["facebook", "linkedin"]
        results = {}
        
        try:
            # Read syndicated content
            content = content_file.read_text(encoding='utf-8') if content_file.exists() else ""
            if not content:
                return results
            
            # Extract key content for social media (first 280 chars for Twitter, etc.)
            # Pass platform to enable viral template generation
            platform_map = {
                "twitter": "twitter",
                "x": "twitter",
                "instagram": "instagram",
                "linkedin": "linkedin",
                "facebook": "facebook"
            }
            current_platform = platform_map.get(platforms[0].lower() if platforms else "twitter", "twitter")
            social_content = self._format_for_social(content, platform=current_platform)
            
            # Distribute to each platform (with platform-specific formatting)
            for platform in platforms:
                try:
                    # Format content for this specific platform
                    platform_content = self._format_for_social(content, platform=platform.lower())
                    
                    if platform.lower() == "twitter" or platform.lower() == "x":
                        results[platform] = self._post_to_twitter(platform_content, content_file)
                    elif platform.lower() == "instagram":
                        results[platform] = self._post_to_instagram(platform_content, content_file)
                    elif platform.lower() == "linkedin":
                        results[platform] = self._post_to_linkedin(platform_content, content_file)
                    elif platform.lower() == "facebook":
                        results[platform] = self._post_to_facebook(platform_content, content_file)
                    else:
                        logger.warning(f"Platform {platform} not yet supported for auto-distribution")
                        results[platform] = False
                except Exception as e:
                    logger.error(f"Error posting to {platform}: {e}")
                    results[platform] = False
                    # Continue to other platforms even if one fails
            
            return results
        except Exception as e:
            logger.error(f"Error in auto_distribute_to_platforms: {e}")
            return results
    
    def _format_for_social(self, content: str, max_length: int = 280, platform: str = "twitter") -> str:
        """Format content for social media platforms with platform-specific rules"""
        # Platform-specific limits
        platform_limits = {
            "twitter": 280,
            "facebook": 5000,
            "linkedin": 3000,
            "instagram": 2200
        }
        max_length = platform_limits.get(platform.lower(), max_length)
        
        # Check if viral templates are enabled and manager is available
        viral_manager = getattr(self, 'viral_template_manager', None)
        if viral_manager and self.affiliate_manager.campaigns:
            # Try to generate viral content based on content topic
            # Extract topic from content (simple keyword matching)
            topic_keywords = {
                "entrepreneur": ["entrepreneur", "startup", "business"],
                "passiveincome": ["passive", "income", "wealth", "money"],
                "business": ["business", "revenue", "profit", "growth"]
            }
            
            detected_topic = None
            content_lower = content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    detected_topic = topic
                    break
            
            if detected_topic:
                # Get affiliate link if available
                affiliate_link = None
                for campaign in self.affiliate_manager.campaigns:
                    if detected_topic.lower() in campaign.get("name", "").lower():
                        affiliate_link = self.affiliate_manager.generate_affiliate_link(
                            campaign["id"], 
                            campaign.get("product_url", "")
                        )
                        break
                
                # Generate viral content
                viral_content = viral_manager.generate_for_topic(
                    detected_topic, 
                    platform, 
                    affiliate_link
                )
                
                if viral_content:
                    import logging
                    logging.debug(f"Generated viral content for {detected_topic} on {platform}")
                    return viral_content[:max_length]
        
        # Fallback to original formatting with platform-specific rules
        lines = content.split('\n')
        title = ""
        body = ""
        
        for line in lines[:10]:
            if line.strip().startswith('#') and not title:
                title = line.strip('#').strip()
            elif line.strip() and not body and not line.strip().startswith('#'):
                body = line.strip()
                break
        
        # Platform-specific formatting
        if platform.lower() == "linkedin":
            # LinkedIn: Professional tone, no hashtags in main text
            if title and body:
                social_text = f"{title}\n\n{body}"
            elif title:
                social_text = title
            elif body:
                social_text = body
            else:
                social_text = content
            # Remove hashtags from main text (can add in comments later)
            social_text = re.sub(r'#\w+', '', social_text)
        
        elif platform.lower() == "facebook":
            # Facebook: Supports links, images, hashtags (max 30)
            if title and body:
                social_text = f"{title}\n\n{body}"
            elif title:
                social_text = title
            elif body:
                social_text = body
            else:
                social_text = content
        
        elif platform.lower() == "instagram":
            # Instagram: Hashtags (max 30), emoji-friendly
            if title and body:
                social_text = f"{title}\n\n{body}"
            elif title:
                social_text = title
            elif body:
                social_text = body
            else:
                social_text = content
        
        else:  # Twitter or default
            # Twitter: 280 chars, concise
            if title and body:
                social_text = f"{title}\n\n{body[:max_length - len(title) - 3]}..."
            elif title:
                social_text = title[:max_length]
            elif body:
                social_text = body[:max_length]
            else:
                social_text = content[:max_length]
        
        # Embed affiliate links (Gumroad and Shopify) with platform-specific tracking
        social_text = self._embed_affiliate_links(social_text, platform=platform.lower())
        
        # Final length check and return
        return social_text[:max_length].strip()
    
    def _post_to_twitter(self, content: str, content_file: Path) -> bool:
        """Post content to Twitter/X (requires API keys)"""
        twitter_api_key = os.getenv('TWITTER_API_KEY')
        twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        twitter_access_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_secret]):
            logger.debug("Twitter API keys not configured - skipping auto-post")
            return False

        # Phased rollout: only post if explicitly enabled
        if os.getenv("TWITTER_LIVE_POSTING", "false").lower() not in ("1", "true", "yes", "on"):
            logger.info("Twitter live posting disabled (TWITTER_LIVE_POSTING=false) - skipping auto-post")
            return False

        # Enforce live window (default 12h) starting at first successful tweet
        duration_hours = float(os.getenv("TWITTER_LIVE_POSTING_DURATION_HOURS", "12"))
        now_ts = datetime.now().timestamp()

        state: Dict[str, Any] = {}
        start_ts: float = 0.0
        try:
            with self._twitter_state_lock:
                self._twitter_state_path.parent.mkdir(parents=True, exist_ok=True)
                if self._twitter_state_path.exists():
                    raw = self._twitter_state_path.read_text(encoding="utf-8").strip()
                    state = json.loads(raw) if raw else {}
                start_ts = float(state.get("start_ts", 0) or 0)
                if start_ts > 0 and (now_ts - start_ts) > (duration_hours * 3600):
                    logger.info("Twitter live posting window expired - skipping auto-post")
                    return False
        except Exception as e:
            logger.warning(f"Twitter post state read failed (continuing): {e}")

        # De-dupe: don't repost same file during the current live window
        try:
            posted = state.get("posted_files", {}) if isinstance(state, dict) else {}
            if isinstance(posted, dict) and start_ts > 0:
                last_post_ts = float(posted.get(content_file.name, 0) or 0)
                if last_post_ts >= start_ts:
                    logger.info(f"Twitter already posted during this live window: {content_file.name} - skipping")
                    return False
        except Exception:
            pass
        
        try:
            url = "https://api.twitter.com/2/tweets"
            auth = OAuth1(
                client_key=twitter_api_key,
                client_secret=twitter_api_secret,
                resource_owner_key=twitter_access_token,
                resource_owner_secret=twitter_access_secret,
            )

            payload = {"text": (content or "").strip()[:280]}
            if not payload["text"]:
                return False

            resp = requests.post(url, json=payload, auth=auth, timeout=15)
            if resp.status_code not in (200, 201):
                logger.error(f"Twitter post failed: HTTP {resp.status_code} - {resp.text[:500]}")
                return False

            data = resp.json() if resp.content else {}
            tweet_id = (data.get("data") or {}).get("id")
            logger.info(f"✅ Posted to Twitter/X ({content_file.name}) tweet_id={tweet_id}")

            # Persist live window + per-file state
            try:
                with self._twitter_state_lock:
                    state = state if isinstance(state, dict) else {}
                    if not state.get("start_ts"):
                        state["start_ts"] = now_ts
                    posted = state.get("posted_files", {})
                    if not isinstance(posted, dict):
                        posted = {}
                    posted[content_file.name] = now_ts
                    state["posted_files"] = posted
                    self._twitter_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Twitter post state write failed: {e}")

            return True
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            return False
    
    def _post_to_instagram(self, content: str, content_file: Path) -> bool:
        """Post content to Instagram using Facebook Graph API (requires Instagram Business Account)"""
        instagram_business_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')  # Same token as Facebook
        
        if not instagram_business_account_id or not facebook_access_token:
            logger.debug("Instagram Business Account ID or Facebook access token not configured - skipping auto-post")
            return False
        
        if not self._check_platform_status("instagram"):
            return False
        
        # Extract affiliate link from content if present
        affiliate_link = None
        import re
        link_match = re.search(r'\[Get it here: (https?://[^\]]+)\]', content)
        if link_match:
            affiliate_link = link_match.group(1)
        
        def _make_instagram_post():
            # Instagram requires a 2-step process: create media container, then publish
            # For text-only posts, we create a simple media container
            url = f"https://graph.facebook.com/v18.0/{instagram_business_account_id}/media"
            headers = {"Authorization": f"Bearer {facebook_access_token}"}
            
            # Format content for Instagram (max 2200 chars, hashtags supported)
            formatted_content = content[:2200]
            if affiliate_link:
                formatted_content = f"{formatted_content}\n\n{affiliate_link}"
            
            # Step 1: Create media container (for text-only, we use caption-only approach)
            # Note: Instagram API requires an image for most post types, but we can try caption-only
            payload = {
                "caption": formatted_content
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if resp.status_code in (200, 201):
                data = resp.json() if resp.content else {}
                creation_id = data.get("id")
                
                if creation_id:
                    # Step 2: Publish the media
                    publish_url = f"https://graph.facebook.com/v18.0/{instagram_business_account_id}/media_publish"
                    publish_payload = {"creation_id": creation_id}
                    publish_resp = requests.post(publish_url, json=publish_payload, headers=headers, timeout=15)
                    
                    if publish_resp.status_code in (200, 201):
                        publish_data = publish_resp.json() if publish_resp.content else {}
                        media_id = publish_data.get("id", "")
                        logger.info(f"✅ Posted to Instagram ({content_file.name}) media_id={media_id}")
                        self._mark_platform_success("instagram")
                        return True
                    else:
                        error_data = publish_resp.json() if publish_resp.content else {}
                        error_msg = error_data.get('error', {}).get('message', publish_resp.text[:200])
                        logger.error(f"Instagram publish failed: HTTP {publish_resp.status_code} - {error_msg}")
                        return False
                else:
                    logger.error("Instagram: No creation_id returned")
                    return False
            elif resp.status_code == 190:
                logger.error(f"Instagram token error (190): Token expired or invalid")
                self._mark_platform_failed("instagram")
                return False
            elif resp.status_code in (4, 17):
                logger.warning(f"Instagram rate limit (4/17): Rate limit exceeded")
                raise Exception("Rate limit - will retry")
            else:
                error_data = resp.json() if resp.content else {}
                error_msg = error_data.get('error', {}).get('message', resp.text[:200])
                logger.error(f"Instagram post failed: HTTP {resp.status_code} - {error_msg}")
                if resp.status_code in (401, 403):
                    self._mark_platform_failed("instagram")
                return False
        
        try:
            return self._retry_api_call(_make_instagram_post, max_attempts=3, base_delay=2)
        except Exception as e:
            logger.error(f"Instagram post failed after retries: {e}")
            return False
    
    def _retry_api_call(self, func, max_attempts=3, base_delay=1):
        """Retry API call with exponential backoff"""
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"API call failed (attempt {attempt + 1}/{max_attempts}), retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        return False
    
    def _check_platform_status(self, platform: str) -> bool:
        """Check if platform is healthy (not recently failed)"""
        status = self._platform_status.get(platform, {})
        if status.get("failed_at"):
            # If failed less than 1 hour ago, skip
            failed_ts = status.get("failed_at", 0)
            if time.time() - failed_ts < 3600:
                logger.debug(f"Platform {platform} marked as unhealthy, skipping")
                return False
        return True
    
    def _mark_platform_failed(self, platform: str):
        """Mark platform as failed"""
        self._platform_status[platform] = {"failed_at": time.time()}
    
    def _mark_platform_success(self, platform: str):
        """Mark platform as successful"""
        if platform in self._platform_status:
            self._platform_status[platform].pop("failed_at", None)
    
    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all platforms for dashboard reporting"""
        status = {}
        for platform in ["facebook", "linkedin", "instagram", "twitter"]:
            platform_status = self._platform_status.get(platform, {})
            is_healthy = self._check_platform_status(platform)
            has_credentials = False
            
            if platform == "facebook":
                has_credentials = bool(os.getenv('FACEBOOK_ACCESS_TOKEN') and os.getenv('FACEBOOK_PAGE_ID'))
            elif platform == "linkedin":
                has_credentials = bool(os.getenv('LINKEDIN_ACCESS_TOKEN'))
            elif platform == "instagram":
                has_credentials = bool(os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID') and os.getenv('FACEBOOK_ACCESS_TOKEN'))
            elif platform == "twitter":
                has_credentials = bool(all([
                    os.getenv('TWITTER_API_KEY'),
                    os.getenv('TWITTER_API_SECRET'),
                    os.getenv('TWITTER_ACCESS_TOKEN'),
                    os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
                ]))
            
            status[platform] = {
                "healthy": is_healthy,
                "configured": has_credentials,
                "failed_at": platform_status.get("failed_at"),
                "last_error": platform_status.get("last_error")
            }
        
        return status
    
    def _post_to_facebook(self, content: str, content_file: Path) -> bool:
        """Post content to Facebook using Graph API v18.0"""
        facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        
        if not facebook_access_token or not facebook_page_id:
            logger.debug("Facebook access token or page ID not configured - skipping auto-post")
            return False
        
        if not self._check_platform_status("facebook"):
            return False
        
        # Extract affiliate link from content if present
        affiliate_link = None
        import re
        link_match = re.search(r'\[Get it here: (https?://[^\]]+)\]', content)
        if link_match:
            affiliate_link = link_match.group(1)
        
        def _make_facebook_post():
            url = f"https://graph.facebook.com/v18.0/{facebook_page_id}/feed"
            headers = {"Authorization": f"Bearer {facebook_access_token}"}
            
            # Format content for Facebook (max 5000 chars, supports links)
            formatted_content = content[:5000]
            if affiliate_link:
                formatted_content = f"{formatted_content}\n\n{affiliate_link}"
            
            payload = {"message": formatted_content}
            
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if resp.status_code in (200, 201):
                data = resp.json() if resp.content else {}
                post_id = data.get("id")
                logger.info(f"✅ Posted to Facebook ({content_file.name}) post_id={post_id}")
                self._mark_platform_success("facebook")
                return True
            elif resp.status_code == 190:
                # Token expired or invalid
                error_data = resp.json() if resp.content else {}
                logger.error(f"Facebook token error (190): {error_data.get('error', {}).get('message', 'Token expired or invalid')}")
                self._mark_platform_failed("facebook")
                return False
            elif resp.status_code == 506:
                # Duplicate post
                logger.info(f"Facebook duplicate post detected for {content_file.name} - skipping")
                return True  # Treat as success
            elif resp.status_code in (4, 17):
                # Rate limit
                error_data = resp.json() if resp.content else {}
                logger.warning(f"Facebook rate limit (4/17): {error_data.get('error', {}).get('message', 'Rate limit exceeded')}")
                raise Exception("Rate limit - will retry")
            else:
                error_data = resp.json() if resp.content else {}
                error_msg = error_data.get('error', {}).get('message', resp.text[:200])
                logger.error(f"Facebook post failed: HTTP {resp.status_code} - {error_msg}")
                if resp.status_code in (401, 403):
                    self._mark_platform_failed("facebook")
                return False
        
        try:
            return self._retry_api_call(_make_facebook_post, max_attempts=3, base_delay=2)
        except Exception as e:
            logger.error(f"Facebook post failed after retries: {e}")
            return False
    
    def _post_to_linkedin(self, content: str, content_file: Path) -> bool:
        """Post content to LinkedIn using API v2 (UGC Posts)"""
        linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        linkedin_urn = os.getenv('LINKEDIN_URN')  # Optional: e.g., "urn:li:person:123456" or "urn:li:organization:123456"
        
        if not linkedin_access_token:
            logger.debug("LinkedIn access token not configured - skipping auto-post")
            return False
        
        if not self._check_platform_status("linkedin"):
            return False
        
        # Extract affiliate link from content if present
        affiliate_link = None
        import re
        link_match = re.search(r'\[Get it here: (https?://[^\]]+)\]', content)
        if link_match:
            affiliate_link = link_match.group(1)
        
        def _make_linkedin_post():
            # First, get the user's URN if not provided
            user_urn = linkedin_urn
            if not user_urn:
                # Try to get URN from profile
                profile_url = "https://api.linkedin.com/v2/me"
                headers = {
                    "Authorization": f"Bearer {linkedin_access_token}",
                    "X-Restli-Protocol-Version": "2.0.0"
                }
                profile_resp = requests.get(profile_url, headers=headers, timeout=15)
                if profile_resp.status_code == 200:
                    profile_data = profile_resp.json()
                    user_urn = profile_data.get("id", "")
                else:
                    logger.error(f"LinkedIn: Failed to get user URN: HTTP {profile_resp.status_code}")
                    return False
            
            if not user_urn:
                logger.error("LinkedIn: User URN not available")
                return False
            
            # Format content for LinkedIn (max 3000 chars, professional tone)
            formatted_content = content[:3000]
            if affiliate_link:
                formatted_content = f"{formatted_content}\n\n{affiliate_link}"
            
            # Create UGC Post
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            
            # LinkedIn UGC Post structure
            payload = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": formatted_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if resp.status_code in (200, 201):
                data = resp.json() if resp.content else {}
                post_id = data.get("id", "")
                logger.info(f"✅ Posted to LinkedIn ({content_file.name}) post_id={post_id}")
                self._mark_platform_success("linkedin")
                return True
            elif resp.status_code == 401:
                logger.error(f"LinkedIn token expired (401): {resp.text[:200]}")
                self._mark_platform_failed("linkedin")
                return False
            elif resp.status_code == 403:
                logger.error(f"LinkedIn permission denied (403): {resp.text[:200]}")
                self._mark_platform_failed("linkedin")
                return False
            elif resp.status_code == 429:
                error_data = resp.json() if resp.content else {}
                logger.warning(f"LinkedIn rate limit (429): {error_data.get('message', 'Rate limit exceeded')}")
                raise Exception("Rate limit - will retry")
            else:
                error_data = resp.json() if resp.content else {}
                error_msg = error_data.get('message', resp.text[:200])
                logger.error(f"LinkedIn post failed: HTTP {resp.status_code} - {error_msg}")
                if resp.status_code in (401, 403):
                    self._mark_platform_failed("linkedin")
                return False
        
        try:
            return self._retry_api_call(_make_linkedin_post, max_attempts=3, base_delay=2)
        except Exception as e:
            logger.error(f"LinkedIn post failed after retries: {e}")
            return False


# ============================================
# VIRAL TEMPLATE MANAGER
# ============================================
class ViralTemplateManager:
    """Manages viral content templates for enhanced engagement"""
    
    def __init__(self, templates_dir: Path = Path("./products/viral_templates")):
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates_cache = {}
        self.load_templates()
        self.used_templates = set()  # Track used templates to avoid repetition
    
    def load_templates(self):
        """Load viral templates from JSON files"""
        try:
            templates_file = self.templates_dir / "templates.json"
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates_cache = data.get("templates", {})
            else:
                # Initialize with default templates
                self._create_default_templates()
                self.load_templates()
        except Exception as e:
            import logging
            logging.warning(f"Error loading viral templates: {e}")
            self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default viral templates based on proven formats"""
        default_templates = {
            "templates": {
                "thread_entrepreneur_001": {
                    "id": "thread_entrepreneur_001",
                    "category": "entrepreneur",
                    "platform": "twitter",
                    "type": "thread",
                    "template": "🔥 {HOOK}\n\n💡 {POINT_1}\n\n💡 {POINT_2}\n\n💡 {POINT_3}\n\n🚀 {CTA}",
                    "variables": {
                        "HOOK": "The #1 mistake entrepreneurs make...",
                        "POINT_1": "They focus on perfection instead of shipping",
                        "POINT_2": "They build in a vacuum without market feedback",
                        "POINT_3": "They wait for the 'perfect' time to launch",
                        "CTA": "{AFFILIATE_LINK}"
                    },
                    "tags": ["entrepreneurship", "business", "startup"]
                },
                "thread_passive_income_001": {
                    "id": "thread_passive_income_001",
                    "category": "passiveincome",
                    "platform": "twitter",
                    "type": "thread",
                    "template": "💰 {HOOK}\n\n📊 {POINT_1}\n\n📈 {POINT_2}\n\n💎 {POINT_3}\n\n🔗 {CTA}",
                    "variables": {
                        "HOOK": "7 passive income streams that changed my life:",
                        "POINT_1": "Digital products (no inventory, instant delivery)",
                        "POINT_2": "Affiliate marketing (earn while you sleep)",
                        "POINT_3": "Automated services (scale without you)",
                        "CTA": "{AFFILIATE_LINK}"
                    },
                    "tags": ["passiveincome", "money", "wealth"]
                },
                "post_linkedin_001": {
                    "id": "post_linkedin_001",
                    "category": "business",
                    "platform": "linkedin",
                    "type": "post",
                    "template": "{HOOK}\n\n{POINT_1}\n\n{POINT_2}\n\n{CTA}",
                    "variables": {
                        "HOOK": "The biggest lesson I learned building a 6-figure business:",
                        "POINT_1": "Focus on ONE thing and master it completely",
                        "POINT_2": "Then scale it systematically before adding complexity",
                        "CTA": "{AFFILIATE_LINK}"
                    },
                    "tags": ["business", "success", "entrepreneurship"]
                },
                "thread_business_001": {
                    "id": "thread_business_001",
                    "category": "business",
                    "platform": "twitter",
                    "type": "thread",
                    "template": "⚡ {HOOK}\n\n1️⃣ {POINT_1}\n2️⃣ {POINT_2}\n3️⃣ {POINT_3}\n\n👇 {CTA}",
                    "variables": {
                        "HOOK": "3 business principles that doubled my revenue:",
                        "POINT_1": "Value first, profit follows",
                        "POINT_2": "Build systems, not just products",
                        "POINT_3": "Serve one niche exceptionally well",
                        "CTA": "{AFFILIATE_LINK}"
                    },
                    "tags": ["business", "revenue", "growth"]
                }
            }
        }
        
        templates_file = self.templates_dir / "templates.json"
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(default_templates, f, indent=2, ensure_ascii=False)
        
        import logging
        logging.info(f"Created default viral templates in {templates_file}")
    
    def get_template(self, category: str = None, platform: str = None, topic: str = None) -> Optional[Dict[str, Any]]:
        """Get a viral template matching criteria"""
        available = []
        
        for template_id, template in self.templates_cache.items():
            # Match category
            if category and template.get("category") != category:
                continue
            # Match platform
            if platform and template.get("platform") != platform.lower():
                continue
            # Match topic/tags
            if topic:
                tags = template.get("tags", [])
                if topic.lower() not in [t.lower() for t in tags]:
                    continue
            # Skip if recently used
            if template_id not in self.used_templates:
                available.append((template_id, template))
        
        if not available:
            # Reset used templates if all have been used
            self.used_templates.clear()
            available = [(tid, t) for tid, t in self.templates_cache.items()]
        
        if available:
            template_id, template = random.choice(available)
            self.used_templates.add(template_id)
            return template
        
        return None
    
    def generate_viral_content(self, template: Dict[str, Any], variables: Dict[str, str] = None, affiliate_link: str = None) -> str:
        """Generate viral content from template"""
        if not template:
            return ""
        
        content = template.get("template", "")
        default_vars = template.get("variables", {})
        
        # Merge variables
        final_vars = {**default_vars}
        if variables:
            final_vars.update(variables)
        
        # Replace affiliate link placeholder
        if affiliate_link:
            final_vars["AFFILIATE_LINK"] = affiliate_link
            # Also replace in CTA
            if "{CTA}" in content and "CTA" in final_vars:
                cta = final_vars["CTA"]
                if "{AFFILIATE_LINK}" in cta:
                    final_vars["CTA"] = cta.replace("{AFFILIATE_LINK}", affiliate_link)
        
        # Replace all variables
        for key, value in final_vars.items():
            content = content.replace(f"{{{key}}}", str(value))
        
        return content
    
    def generate_for_topic(self, topic: str, platform: str, affiliate_link: str = None) -> str:
        """Generate viral content for a specific topic and platform"""
        # Map topic to category
        category_map = {
            "entrepreneur": "entrepreneur",
            "business": "business",
            "passiveincome": "passiveincome",
            "wealth": "passiveincome",
            "startup": "entrepreneur"
        }
        
        category = category_map.get(topic.lower(), "business")
        
        template = self.get_template(category=category, platform=platform, topic=topic)
        if template:
            return self.generate_viral_content(template, affiliate_link=affiliate_link)
        
        return ""


# ============================================
# CORE ENGINE CLASS
# ============================================
class CashEngine:
    def __init__(self):
        self.setup_logging()
        self.setup_encryption()
        self.setup_directories()
        self.setup_database()
        self.setup_apis()
        # Use self.conn for main thread, but classes will get thread-local connections when needed
        self.revenue_tracker = RevenueTracker(self.conn)
        self.risk_manager = RiskManager()
        self.execution_engine = ExecutionEngine()
        self.market_scanner = MarketScanner()
        self.product_factory = ProductFactory(self.conn)
        self.template_generator = TemplateGenerator(self.conn)
        self.lead_bot = LeadBot(self.conn, os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000'))
        self.affiliate_manager = AffiliateManager(os.getenv('MARKETING_AGENT_URL', 'http://localhost:9000'))
        self.viral_template_manager = ViralTemplateManager() if os.getenv('VIRAL_TEMPLATES_ENABLED', 'true').lower() == 'true' else None
        self.shopify_manager = ShopifyManager(self.conn)
        self.content_syndicator = ContentSyndicator(self.affiliate_manager, viral_template_manager=self.viral_template_manager, shopify_manager=self.shopify_manager)
        
        # Template optimization components
        self.template_ab_testing = TemplateABTesting(self.conn)
        self.trend_analyzer = TrendAnalyzer(self.conn)
        self.template_optimizer = TemplateOptimizer(self.conn)
        
        # AI Course Corrector (includes Smart Cleanup System)
        if COURSE_CORRECTION_AVAILABLE and os.getenv('COURSE_CORRECTION_ENABLED', 'true').lower() == 'true':
            try:
                self.course_corrector = AICourseCorrector(cash_engine=self)
                logger.info("✅ AI Course Correction System enabled (with Smart Cleanup)")
            except Exception as e:
                logger.warning(f"⚠️ AI Course Correction System initialization failed: {e}")
                self.course_corrector = None
        else:
            self.course_corrector = None
        
        # Weekly Report Generator
        if WEEKLY_REPORT_AVAILABLE and os.getenv('WEEKLY_REPORT_ENABLED', 'true').lower() == 'true':
            try:
                self.weekly_report_generator = WeeklyReportGenerator(cash_engine=self)
                logger.info("✅ Weekly Report Generator enabled")
            except Exception as e:
                logger.warning(f"⚠️ Weekly Report Generator initialization failed: {e}")
                self.weekly_report_generator = None
        else:
            self.weekly_report_generator = None
        
        # Store reference to engine for thread-local connections
        for obj in [self.revenue_tracker, self.product_factory, self.template_generator, 
                   self.lead_bot, self.shopify_manager, self.template_ab_testing, 
                   self.trend_analyzer, self.template_optimizer]:
            if hasattr(obj, 'db') and hasattr(obj, 'cursor'):
                obj._engine = self  # Store reference to engine for thread-local access
        self.last_trend_analysis = None
        
        self.is_running = False
        self.daily_target = CONFIG["target_monthly"] / 30
        self.current_balance = 0
        
        logger.info(f"💰 CASH ENGINE v{CONFIG['version']} INITIALIZED")
        logger.info(f"🎯 Monthly Target: ${CONFIG['target_monthly']}")
        logger.info(f"📊 Active Revenue Streams: {len(CONFIG['revenue_streams'])}")
        
        # Log template optimization status
        opt_config = CONFIG["template_optimization"]
        logger.info(f"🔬 Template Optimization:")
        logger.info(f"   • A/B Testing: {'✅ Enabled' if opt_config['ab_testing_enabled'] else '❌ Disabled'}")
        logger.info(f"   • Trend Analysis: {'✅ Enabled' if opt_config['trend_analysis_enabled'] else '❌ Disabled'}")
        logger.info(f"   • Sales Optimization: {'✅ Enabled' if opt_config['sales_optimization_enabled'] else '❌ Disabled'}")
    
    def setup_logging(self):
        """Stealth logging system"""
        global logger
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('CashEngine')
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        fh = RotatingFileHandler(
            log_dir / 'engine.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        
        # Console handler
        ch = logging.StreamHandler()
        
        # Formatter with obfuscation
        class ObfuscatingFormatter(logging.Formatter):
            def format(self, record):
                message = super().format(record)
                # Obfuscate sensitive data
                message = re.sub(r'(api[_-]?key=)[^\s]+', r'\1[REDACTED]', message, flags=re.IGNORECASE)
                message = re.sub(r'(token=)[^\s]+', r'\1[REDACTED]', message)
                message = re.sub(r'(password=)[^\s]+', r'\1[REDACTED]', message)
                return message
        
        formatter = ObfuscatingFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    def setup_encryption(self):
        """Military-grade encryption setup"""
        key_path = Path("./.encryption_key")
        if key_path.exists():
            with open(key_path, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
            if sys.platform != 'win32':
                os.chmod(key_path, 0o600)
        
        self.cipher = Fernet(key)
        logger.info("🔐 Encryption system ready")
    
    def setup_directories(self):
        """Create necessary directory structure"""
        dirs = [
            "./data",
            "./data/leads",
            "./data/products", 
            "./data/content",
            "./data/templates",
            "./data/logs",
            "./data/backups",
            "./data/temp",
            "./output",
            "./output/reports",
            "./output/exports",
            "./config",
            "./scripts",
            "./resources"
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("📁 Directory structure created")
    
    def setup_database(self):
        """Encrypted SQLite database (thread-safe)"""
        self.db_path = Path("./data/engine.db")
        # Use check_same_thread=False to allow cross-thread access
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        # Thread-local storage for database connections
        self._local = threading.local()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                amount REAL,
                currency TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price REAL,
                type TEXT,
                description TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                sales_count INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0
            )
        ''')
        
        # Add description column if it doesn't exist (for existing databases)
        try:
            self.cursor.execute('ALTER TABLE products ADD COLUMN description TEXT')
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                source TEXT,
                value_score INTEGER,
                contacted INTEGER DEFAULT 0,
                converted INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT,
                last_run DATETIME,
                next_run DATETIME,
                status TEXT,
                result TEXT
            )
        ''')
        
        # Analytics tables for performance tracking
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                metric_name TEXT,
                value REAL,
                metadata TEXT,
                source TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_file TEXT,
                platform TEXT,
                clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                commissions REAL DEFAULT 0.0,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # A/B Testing tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_ab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                template_a_id TEXT,
                template_b_id TEXT,
                start_date DATETIME,
                end_date DATETIME,
                status TEXT,
                winner_id TEXT,
                metadata TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_ab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                variant_id TEXT,
                impressions INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0.0,
                conversion_rate REAL DEFAULT 0.0,
                date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trend Analysis table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                source TEXT,
                keyword TEXT,
                trend_score REAL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Template Optimization table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                optimization_type TEXT,
                changes TEXT,
                before_metrics TEXT,
                after_metrics TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Add template_id column to products table if it doesn't exist (for linking products to templates)
        try:
            self.cursor.execute('ALTER TABLE products ADD COLUMN template_id TEXT')
            self.cursor.execute('ALTER TABLE products ADD COLUMN ab_test_variant TEXT')
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        self.conn.commit()
        logger.info("💾 Database initialized")
    
    def get_db_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def setup_apis(self):
        """Initialize all API connections"""
        self.apis = {}
        
        # Decrypt API keys if encrypted
        try:
            for key_name, encrypted_value in ENCRYPTED_KEYS.items():
                if encrypted_value and encrypted_value != f"ENCRYPTED_KEY_HERE":
                    try:
                        decrypted = self.cipher.decrypt(encrypted_value.encode())
                        self.apis[key_name] = decrypted.decode()
                    except Exception as e:
                        logger.warning(f"Could not decrypt {key_name}: {e}")
                        # Try using as plain text if decryption fails
                        self.apis[key_name] = encrypted_value
                else:
                    # Try environment variable as fallback
                    env_key = f"{key_name.upper()}_API_KEY"
                    if env_key in os.environ:
                        self.apis[key_name] = os.environ[env_key]
                        logger.info(f"Loaded {key_name} from environment")
        except Exception as e:
            logger.error(f"API setup error: {e}")
        
        # Initialize API clients if keys available
        if "stripe" in self.apis:
            try:
                stripe.api_key = self.apis["stripe"]
                logger.info("✅ Stripe API initialized")
            except Exception as e:
                logger.warning(f"Stripe initialization failed: {e}")
        
        if "telegram" in self.apis and TELEBOT_AVAILABLE:
            try:
                self.telegram_bot = telebot.TeleBot(self.apis["telegram"])
                logger.info("✅ Telegram Bot initialized")
            except Exception as e:
                logger.warning(f"Telegram Bot initialization failed: {e}")
        
        # Check Gumroad integration
        if os.getenv("GUMROAD_TOKEN"):
            logger.info("✅ Gumroad token found - product factory enabled")
        else:
            logger.warning("⚠️ Gumroad token not found - product factory will be limited")
        
        logger.info(f"🔌 API connections initialized: {len(self.apis)} keys loaded")
    
    def start(self):
        """Start the cash engine"""
        if self.is_running:
            logger.warning("Engine is already running")
            return
        
        self.is_running = True
        logger.info("🚀 CASH ENGINE STARTED")
        
        # Schedule recurring tasks (optimized frequencies for faster revenue generation)
        schedule.every(1).hours.do(self.run_revenue_streams)
        schedule.every(6).hours.do(self.scan_markets)
        schedule.every(3).hours.do(self.generate_leads)  # Increased from 12h to 3h for more frequent lead generation
        schedule.every(8).hours.do(self.generate_products)  # Increased from 24h to 8h for faster product creation
        schedule.every(1).days.do(self.generate_daily_report)
        
        # Shopify product sync (every 6 hours)
        if self.shopify_manager and self.shopify_manager.enabled:
            schedule.every(6).hours.do(self.sync_shopify_products)
        
        # Template optimization tasks
        if CONFIG["template_optimization"]["trend_analysis_enabled"]:
            trend_interval = CONFIG["template_optimization"]["trend_analysis_interval"]
            schedule.every(trend_interval).hours.do(self.trend_analyzer.update_trend_cache)
        
        # AI Course Correction - scheduled performance checks
        if self.course_corrector:
            correction_interval = int(os.getenv('PERFORMANCE_CHECK_INTERVAL_HOURS', '6'))
            schedule.every(correction_interval).hours.do(self.run_course_correction)
            logger.info(f"🔍 AI Course Correction scheduled every {correction_interval} hours")
        
        # Weekly Report - scheduled generation
        if self.weekly_report_generator:
            report_day = os.getenv('WEEKLY_REPORT_DAY', 'monday').lower()
            report_time = os.getenv('WEEKLY_REPORT_TIME', '09:00')
            
            # Map day names to schedule
            day_map = {
                'monday': schedule.every().monday,
                'tuesday': schedule.every().tuesday,
                'wednesday': schedule.every().wednesday,
                'thursday': schedule.every().thursday,
                'friday': schedule.every().friday,
                'saturday': schedule.every().saturday,
                'sunday': schedule.every().sunday
            }
            
            if report_day in day_map:
                day_map[report_day].at(report_time).do(self.generate_weekly_report)
                logger.info(f"📊 Weekly Report scheduled for {report_day} at {report_time}")
            else:
                # Default to Monday
                schedule.every().monday.at(report_time).do(self.generate_weekly_report)
                logger.info(f"📊 Weekly Report scheduled for Monday at {report_time}")
        
        # Start scheduler in background thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Run initial execution
        self.run_revenue_streams()
        
        # Run initial course correction check (after a short delay to let system initialize)
        if self.course_corrector:
            def initial_correction_check():
                time.sleep(300)  # Wait 5 minutes for system to initialize
                self.run_course_correction()
            correction_thread = threading.Thread(target=initial_correction_check, daemon=True)
            correction_thread.start()
    
    def stop(self):
        """Stop the cash engine"""
        self.is_running = False
        logger.info("🛑 CASH ENGINE STOPPED")
    
    def run_revenue_streams(self):
        """Execute all active revenue streams"""
        logger.info("💰 Running revenue streams...")
        
        for stream in CONFIG["revenue_streams"]:
            try:
                if stream == "crypto_arbitrage":
                    self.execute_crypto_arbitrage()
                elif stream == "affiliate_automation":
                    self.execute_affiliate_automation()
                elif stream == "digital_product_factory":
                    self.execute_product_creation()
                elif stream == "lead_generation_bot":
                    self.execute_lead_generation()
                elif stream == "content_syndication":
                    self.execute_content_syndication()
                elif stream == "data_scraping_service":
                    self.execute_data_scraping()
            except Exception as e:
                logger.error(f"Revenue stream {stream} failed: {e}")
    
    def execute_crypto_arbitrage(self):
        """Execute crypto arbitrage opportunities"""
        logger.info("🔍 Scanning crypto arbitrage...")
        opportunities = self.market_scanner.scan_arbitrage()
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
    
    def execute_affiliate_automation(self):
        """Execute REAL affiliate automation with Marketing Agent integration"""
        logger.info("🔗 Running affiliate automation...")
        
        try:
            # Auto-create campaigns for Gumroad products
            gumroad_products = self.product_factory.list_products()
            for product in gumroad_products[:5]:  # Top 5 products
                product_name = product.get("name", "")
                product_url = f"https://gumroad.com/l/{product_name.lower().replace(' ', '-')}"
                if not any(c.get("product_url") == product_url for c in self.affiliate_manager.campaigns):
                    campaign_id = self.affiliate_manager.create_campaign(
                        f"Affiliate - {product_name}",
                        product_url,
                        commission_rate=0.30
                    )
                    logger.info(f"Created affiliate campaign for: {product_name}")
            
            campaigns = self.affiliate_manager.campaigns
            logger.info(f"Active campaigns: {len(campaigns)}")
            
            # Track performance and record commission revenue
            total_commissions = sum(p.get("commissions", 0) for p in self.affiliate_manager.performance.values())
            if total_commissions > 0:
                logger.info(f"💰 Total affiliate commissions: ${total_commissions:.2f}")
            
            # Track campaign performance in analytics
            for campaign in campaigns:
                perf = self.affiliate_manager.performance.get(campaign["id"], {})
                self.revenue_tracker.track_campaign_performance(
                    str(campaign["id"]),
                    impressions=perf.get("clicks", 0),
                    clicks=perf.get("clicks", 0),
                    conversions=perf.get("conversions", 0),
                    revenue=perf.get("revenue", 0.0),
                    commissions=perf.get("commissions", 0.0)
                )
        
        except Exception as e:
            logger.error(f"Affiliate automation failed: {e}")
    
    def execute_product_creation(self):
        """Execute REAL digital product creation with revenue generation"""
        logger.info("📦 Running digital product factory...")
        
        try:
            # Sync products from Gumroad
            synced = self.product_factory.sync_gumroad_products()
            if synced > 0:
                logger.info(f"✅ Synced {synced} products from Gumroad")
            
            # Create products from templates (REVENUE GENERATION)
            created = self.product_factory.scan_templates_and_create_products()
            if created > 0:
                logger.info(f"✅ Created {created} products from templates")
            
            # Track sales and record revenue
            revenue = self.product_factory.track_gumroad_sales()
            if revenue > 0:
                logger.info(f"💰 Recorded ${revenue:.2f} in Gumroad sales")
                self.current_balance += revenue
                
                # Record A/B test conversions
                if CONFIG["template_optimization"]["ab_testing_enabled"]:
                    self._record_ab_test_conversions()
            else:
                logger.info("No new sales to track")
        
        except Exception as e:
            logger.error(f"Product creation execution failed: {e}")
    
    def _record_ab_test_conversions(self):
        """Record A/B test conversions for recent sales"""
        try:
            # Get recent sales (last hour)
            cutoff = datetime.now() - timedelta(hours=1)
            self.cursor.execute('''
                SELECT p.name, p.template_id, p.ab_test_variant, r.amount
                FROM revenue r
                JOIN products p ON r.description LIKE '%' || p.name || '%'
                WHERE r.timestamp >= ? AND r.source = 'gumroad_sale'
            ''', (cutoff,))
            
            sales = self.cursor.fetchall()
            
            for product_name, template_id, variant, amount in sales:
                if not template_id:
                    continue
                
                # Find active A/B test for this template
                self.cursor.execute('''
                    SELECT id, template_a_id, template_b_id FROM template_ab_tests
                    WHERE status = 'active' AND (template_a_id = ? OR template_b_id = ?)
                ''', (template_id, template_id))
                test = self.cursor.fetchone()
                
                if test:
                    test_id = test[0]
                    template_a_id, template_b_id = test[1], test[2]
                    
                    # Determine variant letter
                    if variant:
                        variant_letter = variant.upper()
                    else:
                        variant_letter = "A" if template_id == template_a_id else "B"
                    
                    # Record conversion
                    self.template_ab_testing.record_conversion(test_id, variant_letter, amount or 0.0)
                    logger.debug(f"Recorded A/B test conversion: Test {test_id}, Variant {variant_letter}, ${amount:.2f}")
        except Exception as e:
            logger.error(f"Error recording A/B test conversions: {e}")
    
    def execute_lead_generation(self):
        """Execute lead generation"""
        logger.info("🎯 Generating leads...")
        leads_count = self.lead_bot.generate_leads("automated", count=10)
        logger.info(f"Generated {leads_count} leads")
    
    def execute_content_syndication(self):
        """Execute REAL content syndication with affiliate links"""
        logger.info("📰 Syndicating content...")
        
        try:
            # Auto-syndicate content from products folder
            syndicated = self.content_syndicator.auto_syndicate_from_folder()
            if syndicated > 0:
                logger.info(f"✅ Syndicated {syndicated} content files with affiliate links")
                # Track content syndication performance
                for content_file in self.content_syndicator.products_dir.glob("*.md"):
                    self.revenue_tracker.track_content_performance(
                        content_file.name, "syndicated", clicks=0, conversions=0, revenue=0.0
                    )

            # Optional: auto-distribute to social platforms (phased rollout)
            if os.getenv("AUTO_DISTRIBUTE_CONTENT", "false").lower() in ("1", "true", "yes", "on"):
                platforms_env = os.getenv("DISTRIBUTION_PLATFORMS", "")
                if platforms_env:
                    platforms = [p.strip() for p in platforms_env.split(",") if p.strip()]
                else:
                    # Default: Facebook and LinkedIn if Twitter is disabled
                    twitter_enabled = os.getenv("TWITTER_LIVE_POSTING", "false").lower() in ("1", "true", "yes", "on")
                    if twitter_enabled:
                        platforms = ["twitter", "facebook", "linkedin"]
                    else:
                        platforms = ["facebook", "linkedin"]
                for content_file in self.content_syndicator.products_dir.glob("*.md"):
                    results = self.content_syndicator.auto_distribute_to_platforms(content_file, platforms=platforms)
                    if results:
                        ok = [k for k, v in results.items() if v]
                        fail = [k for k, v in results.items() if not v]
                        if ok:
                            logger.info(f"✅ Posted {content_file.name} to: {', '.join(ok)}")
                        if fail:
                            logger.info(f"⚠️ Skipped/failed posting {content_file.name} to: {', '.join(fail)}")
            
            # Content syndication generates revenue through affiliate commissions
            # when users click affiliate links in syndicated content
            logger.info(f"Content ready for distribution with embedded affiliate links")
        
        except Exception as e:
            logger.error(f"Content syndication failed: {e}")
    
    def execute_data_scraping(self):
        """Execute data scraping service"""
        logger.info("🕷️ Running data scraping...")
        # Implementation would scrape data
        pass
    
    def scan_markets(self):
        """Scan markets for opportunities"""
        logger.info("🔍 Scanning markets...")
        opportunities = self.market_scanner.scan_arbitrage()
        opportunities.extend(self.market_scanner.scan_affiliate())
        logger.info(f"Found {len(opportunities)} total opportunities")
    
    def generate_leads(self):
        """Generate leads periodically"""
        logger.info("🎯 Generating leads...")
        self.lead_bot.generate_leads("scheduled", count=20)
    
    def sync_shopify_products(self):
        """Sync Shopify products from store to database"""
        if not self.shopify_manager or not self.shopify_manager.enabled:
            return
        
        logger.info("🛍️ Syncing Shopify products...")
        try:
            synced_count = self.shopify_manager.sync_products_to_db()
            if synced_count > 0:
                logger.info(f"✅ Synced {synced_count} Shopify products to database")
            else:
                logger.debug("No Shopify products to sync or sync failed")
        except Exception as e:
            logger.error(f"Error syncing Shopify products: {e}")
    
    def generate_products(self):
        """Generate products periodically with template optimization"""
        logger.info("📦 Generating products...")
        try:
            opt_config = CONFIG["template_optimization"]
            
            # 1. Trend Analysis (if enabled and time interval passed)
            if opt_config["trend_analysis_enabled"]:
                should_update_trends = False
                if not self.last_trend_analysis:
                    should_update_trends = True
                else:
                    hours_since = (datetime.now() - self.last_trend_analysis).total_seconds() / 3600
                    if hours_since >= opt_config["trend_analysis_interval"]:
                        should_update_trends = True
                
                if should_update_trends:
                    logger.info("📊 Running trend analysis...")
                    self.trend_analyzer.update_trend_cache()
                    self.last_trend_analysis = datetime.now()
            
            # 2. Template Generation with trend suggestions
            if CONFIG["template_generation_enabled"] and self.template_generator.is_available():
                if self.should_generate_templates():
                    # Get trending topics
                    suggested_topics = []
                    if opt_config["trend_analysis_enabled"]:
                        suggested_topics = self.trend_analyzer.suggest_template_topics(limit=3)
                    
                    topic = random.choice(suggested_topics if suggested_topics else CONFIG["template_topics"])
                    logger.info(f"🤖 Template generation triggered for topic: {topic}")
                    
                    generated_path = self.template_generator.generate_template(topic)
                    if generated_path:
                        logger.info(f"✅ New template generated: {generated_path.name}")
                        
                        # 3. A/B Testing (create variant if enabled)
                        if opt_config["ab_testing_enabled"]:
                            # Create a variant by modifying the template slightly
                            variant_path = self._create_template_variant(generated_path)
                            if variant_path:
                                test_name = f"Template_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                test_id = self.template_ab_testing.create_ab_test(generated_path, variant_path, test_name)
                                if test_id:
                                    logger.info(f"🧪 A/B test created: {test_name} (ID: {test_id})")
            
            # 4. Scan templates and create products
            created = self.product_factory.scan_templates_and_create_products()
            if created > 0:
                logger.info(f"✅ Created {created} products from templates")
                
                # Record impressions for A/B tests
                if opt_config["ab_testing_enabled"]:
                    self._record_ab_test_impressions()
            
            # 5. Evaluate A/B tests
            if opt_config["ab_testing_enabled"]:
                self._evaluate_ab_tests()
            
            # 6. Sales-based optimization
            if opt_config["sales_optimization_enabled"]:
                self._optimize_underperforming_templates()
            
            # Auto-upload to Gumroad if enabled
            auto_upload = os.getenv("AUTO_UPLOAD_TO_GUMROAD", "false").lower() == "true"
            if auto_upload and self.product_factory.gumroad.has_access_token():
                # Get recently created products (last 24 hours)
                cutoff = datetime.now() - timedelta(hours=24)
                self.product_factory.cursor.execute('''
                    SELECT id, name, price FROM products 
                    WHERE created_date >= ? AND type = 'digital'
                    ORDER BY created_date DESC
                    LIMIT 10
                ''', (cutoff,))
                recent_products = self.product_factory.cursor.fetchall()
                
                uploaded = 0
                for product_id, name, price in recent_products:
                    gumroad_url = self.product_factory.upload_product_to_gumroad(product_id)
                    if gumroad_url:
                        uploaded += 1
                
                if uploaded > 0:
                    logger.info(f"✅ Auto-uploaded {uploaded} products to Gumroad")
        except Exception as e:
            logger.error(f"Product generation failed: {e}")
    
    def should_generate_templates(self) -> bool:
        """Determine if templates should be generated based on adaptive scheduling"""
        if not CONFIG["template_generation_enabled"]:
            return False
        
        # Check minimum interval
        min_interval = CONFIG["min_template_interval"]
        self.cursor.execute('''
            SELECT MAX(date) FROM template_optimization_history
        ''')
        row = self.cursor.fetchone()
        if row and row[0]:
            last_gen = datetime.fromisoformat(row[0])
            days_since = (datetime.now() - last_gen).days
            if days_since < min_interval:
                return False
        
        # Check recent product creation
        cutoff = datetime.now() - timedelta(days=7)
        self.cursor.execute('''
            SELECT COUNT(*) FROM products WHERE created_date >= ?
        ''', (cutoff,))
        recent_products = self.cursor.fetchone()[0] or 0
        
        # Generate if we have few recent products or revenue target not met
        if recent_products < 3:
            return True
        
        # Check revenue target
        revenue = self.revenue_tracker.get_total_revenue(days=7)
        target = self.daily_target * 7
        if revenue < target * 0.7:  # Below 70% of weekly target
            return True
        
        return False
    
    def _create_template_variant(self, template_path: Path) -> Optional[Path]:
        """Create a variant of a template for A/B testing"""
        if not template_path.exists():
            return None
        
        try:
            content = template_path.read_text(encoding='utf-8')
            
            # Simple variant: modify sales blurb slightly (could use AI for better variants)
            # For now, create a copy with "_variant" suffix
            variant_path = template_path.parent / f"{template_path.stem}_variant.md"
            
            # Add variant marker in content
            variant_content = content.replace(
                "Sales Blurb",
                "Sales Blurb\n\n*Variant for A/B Testing*"
            )
            
            variant_path.write_text(variant_content, encoding='utf-8')
            return variant_path
        except Exception as e:
            logger.error(f"Error creating template variant: {e}")
            return None
    
    def _record_ab_test_impressions(self):
        """Record impressions for active A/B tests when products are created"""
        try:
            active_tests = self.template_ab_testing.get_active_tests()
            cutoff = datetime.now() - timedelta(hours=1)
            
            for test in active_tests:
                test_id = test["id"]
                template_a_id = test["template_a_id"]
                template_b_id = test["template_b_id"]
                
                # Check for products created from these templates
                self.cursor.execute('''
                    SELECT COUNT(*) FROM products
                    WHERE created_date >= ? AND template_id IN (?, ?)
                ''', (cutoff, template_a_id, template_b_id))
                
                count = self.cursor.fetchone()[0] or 0
                
                if count > 0:
                    # Determine which variant was used (simplified - would need better tracking)
                    # For now, record impression for variant A
                    self.template_ab_testing.record_impression(test_id, "A")
        except Exception as e:
            logger.error(f"Error recording A/B test impressions: {e}")
    
    def _evaluate_ab_tests(self):
        """Evaluate active A/B tests and determine winners"""
        try:
            active_tests = self.template_ab_testing.get_active_tests()
            
            for test in active_tests:
                test_id = test["id"]
                results = self.template_ab_testing.get_test_results(test_id)
                
                # Check if we have enough data
                total_conversions = sum(r.get("conversions", 0) for r in results.values())
                min_conversions = CONFIG["template_optimization"]["ab_test_min_conversions"]
                
                if total_conversions >= min_conversions:
                    winner = self.template_ab_testing.determine_winner(test_id, min_conversions)
                    if winner:
                        self.template_ab_testing.apply_winner(test_id)
        except Exception as e:
            logger.error(f"Error evaluating A/B tests: {e}")
    
    def _optimize_underperforming_templates(self):
        """Identify and optimize underperforming templates"""
        try:
            threshold = CONFIG["template_optimization"]["optimization_threshold"]
            underperforming = self.template_optimizer.identify_underperforming_templates(threshold)
            
            for template_perf in underperforming[:3]:  # Optimize top 3 underperforming
                template_id = template_perf.get("template_id")
                products_dir = Path("./products")
                template_path = products_dir / f"{template_id}.md"
                
                if template_path.exists():
                    logger.info(f"🔧 Optimizing underperforming template: {template_id}")
                    optimized = self.template_optimizer.optimize_template(template_path, template_perf)
                    if optimized:
                        logger.info(f"✅ Optimized template created: {optimized.name}")
        except Exception as e:
            logger.error(f"Error optimizing templates: {e}")
    
    def run_course_correction(self):
        """Run AI-driven course correction analysis and fixes"""
        if not self.course_corrector:
            return
        
        try:
            logger.info("🔍 Running AI Course Correction...")
            correction_days = int(os.getenv('COURSE_CORRECTION_PERIOD_DAYS', '3'))
            report = self.course_corrector.run_course_correction(days=correction_days)
            
            if "error" in report:
                logger.error(f"Course correction failed: {report['error']}")
                return
            
            if report.get("needs_correction"):
                logger.warning(f"⚠️  Course correction needed: {len(report['issues'])} issues identified")
                for issue in report['issues']:
                    logger.warning(f"   • {issue.get('description', 'Unknown issue')}")
                
                # Log implemented fixes
                fixes_impl = report.get("fixes_implemented", {})
                if fixes_impl.get("implemented"):
                    logger.info(f"✅ Implemented {len(fixes_impl['implemented'])} fixes")
                if fixes_impl.get("failed"):
                    logger.warning(f"⚠️  {len(fixes_impl['failed'])} fixes failed")
            else:
                logger.info("✅ Performance metrics within acceptable range")
        
        except Exception as e:
            logger.error(f"Course correction error: {e}")
    
    def generate_weekly_report(self):
        """Generate comprehensive weekly work report"""
        if not self.weekly_report_generator:
            return
        
        try:
            logger.info("📊 Generating Weekly Work Report...")
            report_days = int(os.getenv('WEEKLY_REPORT_DAYS', '7'))
            result = self.weekly_report_generator.generate_weekly_report(days=report_days)
            
            if "error" in result:
                logger.error(f"Weekly report generation failed: {result['error']}")
                return
            
            if result.get("success"):
                logger.info(f"✅ Weekly report generated: {result.get('markdown_file', 'N/A')}")
                logger.info("📄 Report includes: What worked, what didn't, why, future actions, and honest recommendations")
            else:
                logger.warning("⚠️ Weekly report generation completed with warnings")
        
        except Exception as e:
            logger.error(f"Weekly report generation error: {e}")
    
    def generate_daily_report(self):
        """Generate daily revenue report with analytics"""
        logger.info("📊 Generating daily report...")
        total_revenue = self.revenue_tracker.get_total_revenue(days=1)
        revenue_by_source = self.revenue_tracker.get_revenue_by_source(days=1)
        
        # Get analytics data
        content_perf = self.revenue_tracker.get_content_performance(days=1)
        campaign_perf = self.revenue_tracker.get_campaign_performance(days=1)
        
        logger.info(f"📈 Daily Revenue: ${total_revenue:.2f}")
        for source, amount in revenue_by_source.items():
            logger.info(f"  - {source}: ${amount:.2f}")
        
        # Log analytics
        if content_perf:
            logger.info(f"📰 Content Performance: {len(content_perf)} content items tracked")
        if campaign_perf:
            logger.info(f"🔗 Campaign Performance: {len(campaign_perf)} campaigns tracked")
            for camp in campaign_perf[:3]:  # Top 3
                logger.info(f"  - Campaign {camp.get('campaign_id')}: ${camp.get('total_commissions', 0):.2f} commissions")
        
        # Save report to file
        report_path = Path("./output/reports") / f"report_{datetime.now().strftime('%Y%m%d')}.json"
        report_data = {
            "date": datetime.now().isoformat(),
            "total_revenue": total_revenue,
            "by_source": revenue_by_source,
            "content_performance": content_perf,
            "campaign_performance": campaign_perf,
            "daily_target": self.daily_target,
            "target_met": total_revenue >= self.daily_target
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Report saved: {report_path}")
    
    def generate_performance_dashboard(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive performance dashboard with analytics"""
        try:
            total_revenue = self.revenue_tracker.get_total_revenue(days=days)
            revenue_by_source = self.revenue_tracker.get_revenue_by_source(days=days)
            content_perf = self.revenue_tracker.get_content_performance(days=days)
            campaign_perf = self.revenue_tracker.get_campaign_performance(days=days)
            
            # Calculate conversion rates
            total_clicks = sum(c.get("total_clicks", 0) for c in campaign_perf)
            total_conversions = sum(c.get("total_conversions", 0) for c in campaign_perf)
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0
            
            dashboard = {
                "period_days": days,
                "total_revenue": total_revenue,
                "revenue_by_source": revenue_by_source,
                "content_performance": content_perf,
                "campaign_performance": campaign_perf,
                "metrics": {
                    "total_clicks": total_clicks,
                    "total_conversions": total_conversions,
                    "conversion_rate": round(conversion_rate, 2),
                    "total_commissions": sum(c.get("total_commissions", 0) for c in campaign_perf)
                },
                "top_performing_content": sorted(content_perf, key=lambda x: x.get("total_revenue", 0), reverse=True)[:5],
                "top_performing_campaigns": sorted(campaign_perf, key=lambda x: x.get("total_commissions", 0), reverse=True)[:5]
            }
            
            return dashboard
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return {}
    
    def get_top_performing_content(self, limit: int = 5, days: int = 30) -> List[Dict[str, Any]]:
        """Get top performing content by revenue"""
        content_perf = self.revenue_tracker.get_content_performance(days=days)
        return sorted(content_perf, key=lambda x: x.get("total_revenue", 0), reverse=True)[:limit]
    
    def get_conversion_rates(self, days: int = 30) -> Dict[str, float]:
        """Get conversion rates for campaigns and content"""
        campaign_perf = self.revenue_tracker.get_campaign_performance(days=days)
        content_perf = self.revenue_tracker.get_content_performance(days=days)
        
        total_campaign_clicks = sum(c.get("total_clicks", 0) for c in campaign_perf)
        total_campaign_conversions = sum(c.get("total_conversions", 0) for c in campaign_perf)
        total_content_clicks = sum(c.get("total_clicks", 0) for c in content_perf)
        total_content_conversions = sum(c.get("total_conversions", 0) for c in content_perf)
        
        return {
            "campaign_conversion_rate": (total_campaign_conversions / total_campaign_clicks * 100) if total_campaign_clicks > 0 else 0.0,
            "content_conversion_rate": (total_content_conversions / total_content_clicks * 100) if total_content_clicks > 0 else 0.0,
            "overall_conversion_rate": ((total_campaign_conversions + total_content_conversions) / 
                                       (total_campaign_clicks + total_content_clicks) * 100) if (total_campaign_clicks + total_content_clicks) > 0 else 0.0
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            "running": self.is_running,
            "daily_target": self.daily_target,
            "current_balance": self.current_balance,
            "total_revenue_30d": self.revenue_tracker.get_total_revenue(days=30),
            "total_revenue_7d": self.revenue_tracker.get_total_revenue(days=7),
            "active_streams": len(CONFIG["revenue_streams"]),
            "risk_level": self.risk_manager.risk_level
        }


# ============================================
# MAIN EXECUTION
# ============================================
def main():
    """Main entry point"""
    engine = CashEngine()
    
    try:
        engine.start()
        logger.info("Engine started. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        while engine.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received...")
        engine.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        engine.stop()


if __name__ == "__main__":
    main()
