#!/usr/bin/env python3
"""
 AWS Cost Monitoring Bot - Main Entry Point
A comprehensive, enterprise-grade AWS cost monitoring solution with service-specific controls,
resource filtering, and intelligent alerts to Slack.
"""

import argparse
import sys
import logging
from cost_monitor_bot import CostMonitorBot

def setup_logging(debug: bool = False):
    """Setup  logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cost_monitor.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """ main entry point with comprehensive argument parsing"""
    parser = argparse.ArgumentParser(
        description=' AWS Cost Monitoring Bot - Enterprise-grade cost monitoring with service-specific controls',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
 Features:
  Service-Specific Controls: Enable/disable services, set service-specific thresholds
  Resource Filtering: Monitor specific ARNs, exclude unwanted resources
  Intelligent Alerts: Multi-level alerts with service-specific recommendations
  Advanced Configuration: YAML config files, environment variables, flexible scheduling

Examples:
  # Test  connections
  python main.py --test

  # Run with service-specific configuration
  python main.py --config production.yaml --daemon

  # Monitor only specific services
  ENABLED_SERVICES="Amazon EC2,Amazon RDS" python main.py --daemon

  # Set service-specific thresholds
  SERVICE_THRESHOLDS='{"Amazon EC2": 500.0}' python main.py --check-once

  # Resource filtering
  RESOURCE_ARNS="arn:aws:ec2:us-east-1:123456789012:instance/i-prod*" python main.py --daemon

  #  debugging
  DEBUG_MODE=true python main.py --test
        """
    )
    
    #  action arguments
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Test  connections (AWS, Slack, service configuration)'
    )
    
    parser.add_argument(
        '--check-once', 
        action='store_true',
        help='Run  cost check once and exit'
    )
    
    parser.add_argument(
        '--summary', 
        action='store_true',
        help='Send  cost summary report'
    )
    
    parser.add_argument(
        '--daemon', 
        action='store_true',
        help='Start  monitoring in daemon mode'
    )
    
    #  configuration arguments
    parser.add_argument(
        '--config', 
        type=str,
        help='Path to  YAML/JSON configuration file'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable  debug mode with detailed logging'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=' AWS Cost Monitor Bot v2.0.0'
    )
    
    #  service-specific arguments
    parser.add_argument(
        '--services', 
        type=str,
        help='Comma-separated list of AWS services to monitor (overrides config)'
    )
    
    parser.add_argument(
        '--exclude-services', 
        type=str,
        help='Comma-separated list of AWS services to exclude (overrides config)'
    )
    
    parser.add_argument(
        '--threshold', 
        type=float,
        help='Global cost threshold (overrides config)'
    )
    
    parser.add_argument(
        '--service-thresholds', 
        type=str,
        help='JSON string of service-specific thresholds (overrides config)'
    )
    
    #  resource filtering arguments
    parser.add_argument(
        '--resource-arns', 
        type=str,
        help='Comma-separated list of resource ARNs to monitor (overrides config)'
    )
    
    parser.add_argument(
        '--exclude-arns', 
        type=str,
        help='Comma-separated list of resource ARNs to exclude (overrides config)'
    )
    
    parser.add_argument(
        '--tag-filters', 
        type=str,
        help='JSON string of tag filters (overrides config)'
    )
    
    #  monitoring arguments
    parser.add_argument(
        '--anomaly-detection', 
        choices=['true', 'false'],
        help='Enable/disable anomaly detection (overrides config)'
    )
    
    parser.add_argument(
        '--anomaly-sensitivity', 
        choices=['low', 'medium', 'high'],
        help='Anomaly detection sensitivity (overrides config)'
    )
    
    parser.add_argument(
        '--cost-forecasting', 
        choices=['true', 'false'],
        help='Enable/disable cost forecasting (overrides config)'
    )
    
    parser.add_argument(
        '--forecast-days', 
        type=int,
        help='Number of days to forecast (overrides config)'
    )
    
    #  scheduling arguments
    parser.add_argument(
        '--check-interval', 
        type=int,
        help='Check interval in hours (overrides config)'
    )
    
    parser.add_argument(
        '--weekend-monitoring', 
        choices=['true', 'false'],
        help='Enable/disable weekend monitoring (overrides config)'
    )
    
    #  alert arguments
    parser.add_argument(
        '--alert-levels', 
        type=str,
        help='JSON string of alert level percentages (overrides config)'
    )
    
    parser.add_argument(
        '--detailed-breakdown', 
        choices=['true', 'false'],
        help='Enable/disable detailed breakdown in alerts (overrides config)'
    )
    
    parser.add_argument(
        '--max-services', 
        type=int,
        help='Maximum services to show in alerts (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Setup  logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    #  argument validation
    if not any([args.test, args.check_once, args.summary, args.daemon]):
        logger.error("No action specified. Use --help for available options.")
        parser.print_help()
        sys.exit(1)
    
    try:
        # Initialize  bot with configuration
        logger.info("Initializing  AWS Cost Monitor Bot...")
        bot = CostMonitorBot(args.config)
        
        # Override configuration with command line arguments
        if args.services:
            bot.config.enabled_services = [s.strip() for s in args.services.split(',')]
            logger.info(f"Overriding enabled services: {bot.config.enabled_services}")
        
        if args.exclude_services:
            bot.config.disabled_services = [s.strip() for s in args.exclude_services.split(',')]
            logger.info(f"Overriding disabled services: {bot.config.disabled_services}")
        
        if args.threshold:
            bot.config.cost_threshold = args.threshold
            logger.info(f"Overriding cost threshold: ${args.threshold}")
        
        if args.service_thresholds:
            import json
            bot.config.service_thresholds = json.loads(args.service_thresholds)
            logger.info(f"Overriding service thresholds: {bot.config.service_thresholds}")
        
        if args.resource_arns:
            bot.config.resource_arns = [arn.strip() for arn in args.resource_arns.split(',')]
            logger.info(f"Overriding resource ARNs: {bot.config.resource_arns}")
        
        if args.exclude_arns:
            bot.config.excluded_arns = [arn.strip() for arn in args.exclude_arns.split(',')]
            logger.info(f"Overriding excluded ARNs: {bot.config.excluded_arns}")
        
        if args.tag_filters:
            import json
            bot.config.tag_filters = json.loads(args.tag_filters)
            logger.info(f"Overriding tag filters: {bot.config.tag_filters}")
        
        if args.anomaly_detection:
            bot.config.enable_anomaly_detection = args.anomaly_detection.lower() == 'true'
            logger.info(f"Overriding anomaly detection: {bot.config.enable_anomaly_detection}")
        
        if args.anomaly_sensitivity:
            bot.config.anomaly_sensitivity = args.anomaly_sensitivity
            logger.info(f"Overriding anomaly sensitivity: {bot.config.anomaly_sensitivity}")
        
        if args.cost_forecasting:
            bot.config.enable_cost_forecasting = args.cost_forecasting.lower() == 'true'
            logger.info(f"Overriding cost forecasting: {bot.config.enable_cost_forecasting}")
        
        if args.forecast_days:
            bot.config.forecast_days = args.forecast_days
            logger.info(f"Overriding forecast days: {bot.config.forecast_days}")
        
        if args.check_interval:
            bot.config.check_interval_hours = args.check_interval
            logger.info(f"Overriding check interval: {bot.config.check_interval_hours} hours")
        
        if args.weekend_monitoring:
            bot.config.enable_weekend_monitoring = args.weekend_monitoring.lower() == 'true'
            logger.info(f"Overriding weekend monitoring: {bot.config.enable_weekend_monitoring}")
        
        if args.alert_levels:
            import json
            alert_levels = json.loads(args.alert_levels)
            bot.config.alert_levels.update(alert_levels)
            logger.info(f"Overriding alert levels: {bot.config.alert_levels}")
        
        if args.detailed_breakdown:
            bot.config.enable_detailed_breakdown = args.detailed_breakdown.lower() == 'true'
            logger.info(f"Overriding detailed breakdown: {bot.config.enable_detailed_breakdown}")
        
        if args.max_services:
            bot.config.max_services_in_alert = args.max_services
            logger.info(f"Overriding max services in alert: {bot.config.max_services_in_alert}")
        
        # Log  configuration summary
        logger.info(" Configuration Summary:")
        logger.info(f"  Project: {bot.config.project_name}")
        logger.info(f"  Enabled Services: {len(bot.config.get_enabled_services_list())} services")
        logger.info(f"  Disabled Services: {len(bot.config.disabled_services)} services")
        logger.info(f"  Service Thresholds: {len(bot.config.service_thresholds)} configured")
        logger.info(f"  Resource ARNs: {len(bot.config.resource_arns)} included, {len(bot.config.excluded_arns)} excluded")
        logger.info(f"  Tag Filters: {len(bot.config.tag_filters)} configured")
        logger.info(f"  Anomaly Detection: {bot.config.enable_anomaly_detection} ({bot.config.anomaly_sensitivity})")
        logger.info(f"  Cost Forecasting: {bot.config.enable_cost_forecasting} ({bot.config.forecast_days} days)")
        logger.info(f"  Check Interval: {bot.config.check_interval_hours} hours")
        logger.info(f"  Weekend Monitoring: {bot.config.enable_weekend_monitoring}")
        logger.info(f"  Detailed Breakdown: {bot.config.enable_detailed_breakdown}")
        logger.info(f"  Max Services in Alert: {bot.config.max_services_in_alert}")
        
        # Execute requested action
        if args.test:
            logger.info("Running  connection tests...")
            success = bot.test_connections()
            if success:
                logger.info("All  connection tests passed!")
                sys.exit(0)
            else:
                logger.error(" connection tests failed!")
                sys.exit(1)
        
        elif args.check_once:
            logger.info("Running  cost check...")
            try:
                cost_data = bot.check_costs()
                logger.info(f" cost check completed: ${cost_data['current_cost']:.2f}")
                
                # Send alert if needed
                alert_sent = bot.send_alert(cost_data)
                if alert_sent:
                    logger.info(" alert sent successfully")
                else:
                    logger.info("No alert needed - costs within normal range")
                
                # Log  details
                if cost_data['service_details']:
                    logger.info(f"Service details: {len(cost_data['service_details'])} services analyzed")
                
                if cost_data['resource_costs']:
                    logger.info(f"Resource costs: {len(cost_data['resource_costs'])} resources tracked")
                
                if cost_data['anomalies']:
                    logger.warning(f"Anomalies detected: {len(cost_data['anomalies'])}")
                
                sys.exit(0)
            except Exception as e:
                logger.error(f" cost check failed: {str(e)}")
                sys.exit(1)
        
        elif args.summary:
            logger.info("Sending  cost summary...")
            try:
                cost_data = bot.check_costs()
                success = bot.send_summary(cost_data)
                if success:
                    logger.info(" cost summary sent successfully")
                    sys.exit(0)
                else:
                    logger.error("Failed to send  cost summary")
                    sys.exit(1)
            except Exception as e:
                logger.error(f" summary failed: {str(e)}")
                sys.exit(1)
        
        elif args.daemon:
            logger.info("Starting  monitoring daemon...")
            try:
                bot.start_monitoring()
            except KeyboardInterrupt:
                logger.info(" monitoring stopped by user")
                sys.exit(0)
            except Exception as e:
                logger.error(f" monitoring failed: {str(e)}")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f" bot initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 