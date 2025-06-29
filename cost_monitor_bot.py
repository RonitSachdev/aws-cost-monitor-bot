import logging
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import Config
from aws_cost_monitor import AWSCostMonitor
from slack_notifier import SlackNotifier

class CostMonitorBot:
    """Enhanced AWS Cost Monitoring Bot with service-specific controls and resource filtering"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the Enhanced Cost Monitor Bot"""
        self.config = Config(config_file)
        self.logger = self._setup_logging()
        
        # Initialize components with enhanced configuration
        self.aws_monitor = AWSCostMonitor(self.config.get_aws_credentials(), self.config)
        self.slack_notifier = SlackNotifier(
            self.config.slack_bot_token or '', 
            self.config.slack_channel,
            self.config
        )
        
        self.logger.info(f"Enhanced Cost Monitor Bot initialized for project: {self.config.project_name}")
        self.logger.info(f"Configuration: {self.config.to_dict()}")
        
        # Log enabled services
        enabled_services = self.config.get_enabled_services_list()
        self.logger.info(f"Monitoring {len(enabled_services)} services: {', '.join(enabled_services[:5])}{'...' if len(enabled_services) > 5 else ''}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup enhanced logging configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cost_monitor.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def check_costs(self) -> Dict:
        """Enhanced cost checking function with service-specific analysis"""
        try:
            self.logger.info("Starting enhanced cost check...")
            
            # Get current cost data with filtering
            current_cost, service_breakdown = self.aws_monitor.get_current_month_cost()
            
            # Get daily costs for trend analysis
            daily_costs = self.aws_monitor.get_daily_costs(self.config.monitoring_period_days)
            
            # Get service-specific details
            service_details = self.aws_monitor.get_service_specific_costs(self.config.monitoring_period_days)
            
            # Get resource-level costs
            resource_costs = self.aws_monitor.get_resource_level_costs(7)
            
            # Check for anomalies with configurable sensitivity
            anomalies = self.aws_monitor.check_cost_anomalies()
            
            # Get cost forecast if enabled
            forecast_data = self.aws_monitor.get_cost_forecast(self.config.forecast_days)
            
            # Get resource utilization
            utilization_data = self.aws_monitor.get_resource_utilization()
            
            # Prepare enhanced result
            result = {
                'timestamp': datetime.now().isoformat(),
                'project_name': self.config.project_name,
                'current_cost': current_cost,
                'threshold': self.config.cost_threshold,
                'currency': self.config.currency,
                'service_breakdown': service_breakdown,
                'service_details': service_details,
                'resource_costs': resource_costs,
                'daily_costs': daily_costs,
                'anomalies': anomalies,
                'forecast_data': forecast_data,
                'utilization_data': utilization_data,
                'threshold_exceeded': current_cost > self.config.cost_threshold,
                'percentage_of_threshold': (current_cost / self.config.cost_threshold) * 100,
                'enabled_services_count': len(self.config.get_enabled_services_list()),
                'monitoring_config': {
                    'anomaly_detection': self.config.enable_anomaly_detection,
                    'cost_forecasting': self.config.enable_cost_forecasting,
                    'detailed_breakdown': self.config.enable_detailed_breakdown
                }
            }
            
            self.logger.info(f"Enhanced cost check completed: ${current_cost:.2f} (threshold: ${self.config.cost_threshold:.2f})")
            self.logger.info(f"Monitoring {len(service_details)} services, {len(resource_costs)} resources")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during enhanced cost check: {str(e)}")
            raise
    
    def check_service_specific_costs(self) -> List[Dict]:
        """Check costs for individual services and send alerts if needed"""
        try:
            self.logger.info("Checking service-specific costs...")
            
            service_alerts = []
            service_details = self.aws_monitor.get_service_specific_costs(self.config.monitoring_period_days)
            
            for service_name, service_data in service_details.items():
                # Check if service exceeds its threshold
                if service_data['threshold_exceeded'] or service_data['percentage_of_threshold'] >= 80:
                    alert_info = {
                        'service_name': service_name,
                        'service_data': service_data,
                        'should_alert': True
                    }
                    service_alerts.append(alert_info)
                    
                    # Send service-specific alert
                    self.slack_notifier.send_service_specific_alert(
                        project_name=self.config.project_name,
                        service_name=service_name,
                        service_data=service_data,
                        currency=self.config.currency
                    )
            
            self.logger.info(f"Service-specific check completed: {len(service_alerts)} alerts sent")
            return service_alerts
            
        except Exception as e:
            self.logger.error(f"Error checking service-specific costs: {str(e)}")
            return []
    
    def send_alert(self, cost_data: Dict) -> bool:
        """Send enhanced cost alert based on cost data"""
        try:
            # Enhanced alert conditions
            should_alert = (
                cost_data['threshold_exceeded'] or 
                cost_data['percentage_of_threshold'] >= self.config.alert_levels['warning'] or
                cost_data['anomalies'] or
                any(service['threshold_exceeded'] for service in cost_data['service_details'].values())
            )
            
            if should_alert:
                success = self.slack_notifier.send_cost_alert(
                    project_name=cost_data['project_name'],
                    current_cost=cost_data['current_cost'],
                    threshold=cost_data['threshold'],
                    period_days=self.config.monitoring_period_days,
                    currency=cost_data['currency'],
                    cost_breakdown=cost_data['service_breakdown'],
                    service_details=cost_data['service_details'],
                    resource_costs=cost_data['resource_costs'],
                    anomalies=cost_data['anomalies']
                )
                
                if success:
                    self.logger.info("Enhanced cost alert sent successfully")
                else:
                    self.logger.error("Failed to send enhanced cost alert")
                
                return success
            else:
                self.logger.info("No alert needed - costs within normal range")
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending enhanced alert: {str(e)}")
            return False
    
    def send_summary(self, cost_data: Dict) -> bool:
        """Send enhanced cost summary report"""
        try:
            success = self.slack_notifier.send_cost_summary(
                project_name=cost_data['project_name'],
                total_cost=cost_data['current_cost'],
                daily_costs=cost_data['daily_costs'],
                currency=cost_data['currency'],
                service_details=cost_data['service_details'],
                forecast_data=cost_data['forecast_data'],
                utilization_data=cost_data['utilization_data']
            )
            
            if success:
                self.logger.info("Enhanced cost summary sent successfully")
            else:
                self.logger.error("Failed to send enhanced cost summary")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending enhanced summary: {str(e)}")
            return False
    
    def run_check(self) -> bool:
        """Run a complete enhanced cost check and notification cycle"""
        try:
            # Check if we should run on weekends
            if not self.config.enable_weekend_monitoring:
                current_day = datetime.now().strftime('%A')
                if current_day in ['Saturday', 'Sunday']:
                    self.logger.info(f"Skipping weekend monitoring (current day: {current_day})")
                    return True
            
            # Check costs
            cost_data = self.check_costs()
            
            # Check service-specific costs
            service_alerts = self.check_service_specific_costs()
            
            # Send main alert if needed
            alert_success = self.send_alert(cost_data)
            
            # Log anomalies
            if cost_data['anomalies']:
                self.logger.warning(f"Cost anomalies detected: {len(cost_data['anomalies'])} anomalies")
                for anomaly in cost_data['anomalies']:
                    self.logger.warning(f"Anomaly: {anomaly['description']} (severity: {anomaly['severity']}, sensitivity: {anomaly.get('sensitivity', 'unknown')})")
            
            # Log service alerts
            if service_alerts:
                self.logger.info(f"Service-specific alerts sent: {len(service_alerts)} services")
                for alert in service_alerts:
                    service_name = alert['service_name']
                    percentage = alert['service_data']['percentage_of_threshold']
                    self.logger.info(f"Service alert: {service_name} at {percentage:.1f}% of threshold")
            
            return alert_success
            
        except Exception as e:
            self.logger.error(f"Error in enhanced run_check: {str(e)}")
            # Send error notification to Slack
            try:
                self.slack_notifier.client.chat_postMessage(
                    channel=self.config.slack_channel,
                    text=f"AWS Cost Monitor Error for {self.config.project_name}:\n```{str(e)}```",
                    username="AWS Cost Monitor",
                    icon_emoji=":rotating_light:"
                )
            except:
                pass  # Don't fail if error notification fails
            
            return False
    
    def run_summary(self) -> bool:
        """Run enhanced cost summary report"""
        try:
            cost_data = self.check_costs()
            return self.send_summary(cost_data)
        except Exception as e:
            self.logger.error(f"Error in enhanced run_summary: {str(e)}")
            return False
    
    def test_connections(self) -> bool:
        """Test all connections and configurations with enhanced validation"""
        try:
            self.logger.info("Testing enhanced connections...")
            
            # Test Slack connection
            slack_ok = self.slack_notifier.test_connection()
            
            # Test AWS connection by getting a small amount of data
            try:
                self.aws_monitor.get_daily_costs(days=1)
                aws_ok = True
                self.logger.info("AWS connection test successful")
            except Exception as e:
                aws_ok = False
                self.logger.error(f"AWS connection test failed: {str(e)}")
            
            # Test service-specific functionality
            try:
                enabled_services = self.config.get_enabled_services_list()
                self.logger.info(f"Service configuration test: {len(enabled_services)} services enabled")
                
                # Test resource filtering
                test_arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
                should_monitor = self.config.should_monitor_resource(test_arn)
                self.logger.info(f"Resource filtering test: {should_monitor}")
                
                service_specific_ok = True
            except Exception as e:
                service_specific_ok = False
                self.logger.error(f"Service-specific configuration test failed: {str(e)}")
            
            # Send test message if all connections work
            if slack_ok and aws_ok and service_specific_ok:
                config_summary = f"""
Enhanced Configuration:
• Project: {self.config.project_name}
• Services: {len(self.config.get_enabled_services_list())} enabled
• Anomaly Detection: {'Enabled' if self.config.enable_anomaly_detection else 'Disabled'}
• Cost Forecasting: {'Enabled' if self.config.enable_cost_forecasting else 'Disabled'}
• Detailed Breakdown: {'Enabled' if self.config.enable_detailed_breakdown else 'Disabled'}
• Check Interval: {self.config.check_interval_hours} hours
                """.strip()
                
                self.slack_notifier.client.chat_postMessage(
                    channel=self.config.slack_channel,
                    text=f"Enhanced AWS Cost Monitor test successful for *{self.config.project_name}*\n{config_summary}",
                    username="AWS Cost Monitor",
                    icon_emoji=":white_check_mark:"
                )
                self.logger.info("All enhanced connection tests passed")
                return True
            else:
                self.logger.error("Enhanced connection tests failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing enhanced connections: {str(e)}")
            return False
    
    def schedule_monitoring(self):
        """Schedule enhanced monitoring based on configuration"""
        
        # Clear any existing schedules
        schedule.clear()
        
        # Set check interval based on configuration
        check_interval = self.config.check_interval_hours
        
        if self.config.notification_frequency == 'daily':
            schedule.every().day.at("09:00").do(self.run_check)
            schedule.every().day.at("18:00").do(self.run_check)
            schedule.every().monday.at("08:00").do(self.run_summary)
            self.logger.info("Scheduled daily monitoring at 9:00 AM and 6:00 PM")
            
        elif self.config.notification_frequency == 'weekly':
            schedule.every().monday.at("09:00").do(self.run_check)
            schedule.every().monday.at("09:30").do(self.run_summary)
            self.logger.info("Scheduled weekly monitoring on Mondays at 9:00 AM")
            
        elif self.config.notification_frequency == 'monthly':
            # Use first day of month instead of .month
            schedule.every().day.at("09:00").do(self._monthly_check)
            self.logger.info("Scheduled monthly monitoring")
        
        # Always check at configured interval for threshold breaches
        schedule.every(check_interval).hours.do(self.run_check)
        self.logger.info(f"Added {check_interval}-hourly threshold checks")
        
        # Add service-specific monitoring if enabled
        if self.config.enable_detailed_breakdown:
            schedule.every(check_interval).hours.do(self.check_service_specific_costs)
            self.logger.info(f"Added {check_interval}-hourly service-specific checks")
    
    def _monthly_check(self):
        """Helper function for monthly checks"""
        current_day = datetime.now().day
        if current_day == 1:  # First day of month
            self.run_check()
            self.run_summary()
    
    def start_monitoring(self):
        """Start the enhanced monitoring bot"""
        self.logger.info(f"Starting Enhanced AWS Cost Monitor Bot for {self.config.project_name}")
        
        # Test connections first
        if not self.test_connections():
            self.logger.error("Enhanced connection tests failed. Please check your configuration.")
            return
        
        # Schedule monitoring
        self.schedule_monitoring()
        
        # Run initial check
        self.logger.info("Running initial enhanced cost check...")
        self.run_check()
        
        # Start the scheduler
        self.logger.info("Starting enhanced scheduler...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Enhanced monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in enhanced monitoring loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying 