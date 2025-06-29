#!/usr/bin/env python3
"""
AWS Cost Monitoring Bot
A reusable cost monitoring solution for AWS projects with Slack notifications.
"""

import argparse
import sys
import os
from cost_monitor_bot import CostMonitorBot

def main():
    parser = argparse.ArgumentParser(
        description="AWS Cost Monitoring Bot - Monitor AWS costs and send Slack notifications"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (JSON or YAML)'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test connections and configuration'
    )
    
    parser.add_argument(
        '--check-once', '-o',
        action='store_true',
        help='Run cost check once and exit'
    )
    
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='Send cost summary report and exit'
    )
    
    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Run in daemon mode (continuous monitoring)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize the bot
        print("🤖 Initializing AWS Cost Monitor Bot...")
        bot = CostMonitorBot(config_file=args.config)
        
        if args.test:
            print("🔍 Testing connections...")
            success = bot.test_connections()
            if success:
                print("✅ All tests passed!")
                sys.exit(0)
            else:
                print("❌ Tests failed!")
                sys.exit(1)
        
        elif args.check_once:
            print("💰 Running single cost check...")
            success = bot.run_check()
            if success:
                print("✅ Cost check completed successfully!")
                sys.exit(0)
            else:
                print("❌ Cost check failed!")
                sys.exit(1)
        
        elif args.summary:
            print("📊 Sending cost summary...")
            success = bot.run_summary()
            if success:
                print("✅ Cost summary sent successfully!")
                sys.exit(0)
            else:
                print("❌ Failed to send cost summary!")
                sys.exit(1)
        
        elif args.daemon:
            print("🔄 Starting continuous monitoring...")
            bot.start_monitoring()
        
        else:
            # Default behavior - show help and run once
            parser.print_help()
            print("\n" + "="*50)
            print("Running single cost check by default...")
            success = bot.run_check()
            if success:
                print("✅ Cost check completed successfully!")
                print("\nTo start continuous monitoring, use: python main.py --daemon")
            else:
                print("❌ Cost check failed!")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 