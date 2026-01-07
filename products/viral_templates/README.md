# Viral Templates Directory

This directory contains viral content templates extracted from ViralSky.ai and other proven sources.

## Structure

- `templates.json` - Main template storage file
- `facebook_blueprint/` - Facebook Influencer Blueprint templates (to be added)

## Adding Templates from Facebook Influencer Blueprint

1. Access your ViralSky Ultra plan dashboard
2. Open Facebook Influencer Blueprint
3. Extract key templates and strategies
4. Add to `templates.json` with this format:

```json
{
  "templates": {
    "post_facebook_blueprint_001": {
      "id": "post_facebook_blueprint_001",
      "category": "business",
      "platform": "facebook",
      "type": "post",
      "template": "Template structure here",
      "variables": {
        "HOOK": "Default hook",
        "CTA": "{AFFILIATE_LINK}"
      },
      "tags": ["business", "engagement"]
    }
  }
}
```

## Current Templates

- ✅ 4 default templates (Twitter, LinkedIn)
- ✅ 2 Facebook templates (added)
- ⚠️ Facebook Blueprint templates (to be extracted)

## Usage

Templates are automatically loaded by `ViralTemplateManager` and used during content syndication.
