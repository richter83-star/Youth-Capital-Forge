#!/usr/bin/env python3
"""
Start the Cash Engine and ensure it's running
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cash_engine import CashEngine
    import logging
    
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("🚀 STARTING CASH ENGINE")
    print("=" * 60)
    
    engine = CashEngine()
    engine.start()
    
    print("\n✅ Cash Engine started successfully!")
    print("📊 Revenue streams are now active")
    print("💰 Monitoring for revenue generation...")
    print("\nPress Ctrl+C to stop the engine")
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping Cash Engine...")
        engine.stop()
        print("✅ Cash Engine stopped")
        
except Exception as e:
    print(f"\n❌ Error starting Cash Engine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
