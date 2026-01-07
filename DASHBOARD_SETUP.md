# Dashboard Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install Flask Flask-SocketIO python-socketio
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Start Dashboard Server

```bash
python dashboard_server.py
```

### 3. Access Dashboard

- **Local**: http://localhost:5000
- **Remote**: http://YOUR_IP:5000

## Configuration

Dashboard configuration is in `.env`:

```env
DASHBOARD_ENABLED=true
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0  # 0.0.0.0 for remote access, 127.0.0.1 for local only
DASHBOARD_UPDATE_INTERVAL=10  # seconds
```

## Features

- Real-time updates every 10 seconds via WebSocket
- Revenue metrics (today/week/month)
- Performance analytics
- System status monitoring
- Content and campaign performance tables
- Activity feed
- Responsive design (works on mobile)

## Troubleshooting

### Dashboard not loading
- Check if database exists at `./data/engine.db`
- Check if Cash Engine is running
- Check logs for errors

### No data showing
- Verify database has data
- Check database connection
- Verify tables exist

### WebSocket connection issues
- Check firewall settings
- Verify Flask-SocketIO is installed
- Check browser console for errors
