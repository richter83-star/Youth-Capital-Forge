# Youth Capital Forge - Autonomous Cash Engine

**Version 2.0** | Fully automated revenue generation system with zero human intervention after launch.

An advanced, multi-stream revenue generation platform that automatically creates digital products, manages affiliate campaigns, generates leads, syndicates content, and optimizes performance using AI-powered analytics.

## 🚀 Features

### Core Revenue Streams

1. **Digital Product Factory**
   - AI-powered template generation using OpenAI
   - Automatic product creation from templates
   - Gumroad integration with auto-upload
   - Sales tracking and revenue recording
   - Template-based product scaling

2. **Affiliate Automation**
   - Marketing Agent V2 integration for advanced tracking
   - Automatic campaign creation for products
   - Dynamic affiliate link generation
   - Click and conversion tracking
   - Commission revenue tracking

3. **Lead Generation Bot**
   - Multi-source lead extraction (Instagram, TikTok, Twitter, Reddit)
   - Click tracking log analysis
   - Activity log parsing
   - Web scraping for public leads
   - Lead scoring and qualification

4. **Content Syndication**
   - Automatic content distribution
   - Multi-platform posting (Instagram, Twitter/X, LinkedIn)
   - Affiliate link embedding
   - Content performance tracking
   - Automated scheduling

5. **Template Optimization System** 🔬
   - **A/B Testing**: Compare template variants and determine winners
   - **Trend Analysis**: Analyze social media trends for content topics
   - **Sales Optimization**: AI-powered template improvement based on performance data

### Advanced Features

- **AI-Powered Template Generation**: Uses OpenAI to generate new product templates
- **Performance Analytics**: Comprehensive tracking of all revenue streams
- **Automated Scheduling**: Intelligent task scheduling with adaptive frequencies
- **Database Encryption**: Military-grade encryption for sensitive data
- **Marketing Agent V2**: Advanced link tracking and campaign management
- **Gumroad Integration**: Full API integration for product management and sales tracking

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for Instagram/TikTok automation)
- SQLite3 (included with Python)
- Gumroad account with API access
- OpenAI API key (for template generation - optional)
- Marketing Agent V2 (optional but recommended)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/richter83-star/Youth-Capital-Forge.git
cd Youth-Capital-Forge
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies

```bash
npm install
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Gumroad Configuration
GUMROAD_TOKEN=your_gumroad_access_token

# OpenAI (for template generation)
OPENAI_API_KEY=your_openai_api_key
TEMPLATE_GENERATION_ENABLED=true

# Marketing Agent V2
MARKETING_AGENT_URL=http://localhost:9000

# Template Optimization
AB_TEST_ENABLED=true
TREND_ANALYSIS_ENABLED=true
SALES_OPTIMIZATION_ENABLED=true

# Twitter/X API (for trend analysis)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Reddit API (for trend analysis - optional)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Auto-upload to Gumroad
AUTO_UPLOAD_TO_GUMROAD=true

# Instagram/TikTok (for automation)
IG_USERNAME=your_instagram_username
IG_PASSWORD=your_instagram_password
```

### 5. Setup Marketing Agent V2 (Optional)

```bash
cd marketing_agent_v2
docker-compose up -d
```

Or follow the [Marketing Agent V2 Deployment Guide](marketing_agent_v2/DEPLOYMENT_GUIDE.md)

## 🎯 Quick Start

### Start the Cash Engine

```bash
python start_engine.py
```

Or:

```bash
python cash_engine.py
```

### Check System Status

```bash
python check_revenue_status.py
```

## 📊 System Architecture

### Core Components

- **CashEngine**: Main orchestration engine
- **ProductFactory**: Digital product creation and management
- **TemplateGenerator**: AI-powered template generation
- **TemplateABTesting**: A/B testing for template optimization
- **TrendAnalyzer**: Social media trend analysis
- **TemplateOptimizer**: Sales-based template optimization
- **AffiliateManager**: Affiliate campaign management
- **LeadBot**: Multi-source lead generation
- **ContentSyndicator**: Content distribution automation
- **RevenueTracker**: Revenue and performance tracking
- **GumroadClient**: Gumroad API integration

### Database Schema

The system uses an encrypted SQLite database (`data/engine.db`) with the following tables:

- `revenue`: Revenue transactions
- `products`: Digital products
- `leads`: Generated leads
- `tasks`: Scheduled tasks
- `performance_metrics`: Performance analytics
- `content_performance`: Content analytics
- `campaign_performance`: Campaign analytics
- `template_ab_tests`: A/B test experiments
- `template_ab_results`: A/B test results
- `trend_analysis`: Trend data
- `template_optimization_history`: Optimization tracking

## 🔄 Automated Workflows

### Product Generation Cycle (Every 8 hours)

1. Trend analysis (if enabled)
2. Template generation (if conditions met)
3. A/B test variant creation
4. Product creation from templates
5. Auto-upload to Gumroad (if enabled)
6. A/B test evaluation
7. Template optimization (if needed)

### Revenue Stream Execution (Every 1 hour)

1. Digital product factory
2. Affiliate automation
3. Lead generation
4. Content syndication
5. Sales tracking

### Daily Tasks

- Daily revenue reports
- Performance analytics
- Trend cache updates

## 📈 Revenue Generation Flow

```
Templates → Products → Content Distribution → Traffic → 
Affiliate Links → Gumroad Sales → Revenue Tracking → 
Performance Analysis → Optimization → Improved Templates
```

## 🔬 Template Optimization

### A/B Testing

- Automatically creates template variants
- Tracks impressions and conversions
- Determines winners statistically
- Applies winning templates

### Trend Analysis

- Analyzes Twitter/X trends
- Monitors Reddit discussions
- Suggests trending topics
- Updates cache periodically

### Sales Optimization

- Identifies underperforming templates
- Analyzes sales performance
- Generates optimized versions using AI
- Tracks optimization effectiveness

## 📝 Configuration

Edit `cash_engine.py` to customize:

```python
CONFIG = {
    "target_monthly": 10000,  # Monthly revenue target
    "operating_mode": "stealth",  # stealth, aggressive, balanced
    "template_optimization": {
        "ab_testing_enabled": True,
        "trend_analysis_enabled": True,
        "sales_optimization_enabled": True,
        "trend_analysis_interval": 24,  # hours
        "ab_test_min_conversions": 10,
        "optimization_threshold": 0.3
    }
}
```

## 📊 Monitoring

### Logs

- Main log: `logs/engine.log`
- Activity log: `logs/activity.json`
- Click tracking: `logs/clicks/clicks.json`

### Status Check

```bash
python check_revenue_status.py
```

### Database Queries

```python
# Check revenue
SELECT SUM(amount) FROM revenue WHERE status = 'completed';

# Check products
SELECT * FROM products ORDER BY created_date DESC;

# Check A/B test results
SELECT * FROM template_ab_results;
```

## 🛡️ Security

- Military-grade encryption for sensitive data
- Log obfuscation for API keys and tokens
- Secure database storage
- Environment variable protection
- Automatic data purging (configurable)

## 🔧 Troubleshooting

### Engine Not Starting

1. Check environment variables are set
2. Verify database is accessible
3. Review `logs/engine.log` for errors
4. Run `python check_revenue_status.py`

### No Revenue Tracking

1. Verify Gumroad API token is valid
2. Check products are published on Gumroad
3. Ensure Marketing Agent is running (if used)
4. Review sales in Gumroad dashboard

### Template Generation Not Working

1. Verify OpenAI API key is set
2. Check `TEMPLATE_GENERATION_ENABLED=true`
3. Ensure sufficient OpenAI credits
4. Review template generation logs

## 📚 Documentation

- [Revenue Generation Plan](REVENUE_GENERATION_PLAN.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Marketing Agent V2 Guide](marketing_agent_v2/README.md)
- [Revenue Status Report](REVENUE_STATUS_REPORT.md)

## 🤝 Contributing

This is a private repository. For issues or questions, please contact the repository owner.

## ⚠️ Disclaimer

- Use responsibly and in compliance with all platform Terms of Service
- Instagram/TikTok automation may require frequent updates
- Always respect rate limits and platform policies
- Revenue generation depends on market conditions and traffic

## 📄 License

Private repository - All rights reserved

## 🎯 Roadmap

- [ ] Multi-variant A/B testing (A/B/C/D)
- [ ] Machine learning models for optimization
- [ ] Real-time trend monitoring
- [ ] Cross-platform trend aggregation
- [ ] Advanced analytics dashboard
- [ ] Webhook integrations
- [ ] Multi-currency support

## 📞 Support

For issues or questions:
1. Check `logs/engine.log` for errors
2. Run `python check_revenue_status.py` for diagnostics
3. Review documentation files
4. Check GitHub issues (if enabled)

---

**Built with ❤️ for automated revenue generation**

*Version 2.0 - Autonomous Cash Engine*
