import logging
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
from aws_cost_monitor import AWSCostMonitor
from slack_notifier import SlackNotifier

class CostMonitorBot:
    """Main AWS Cost Monitoring Bot class"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the Cost Monitor Bot"""
        self.config = Config(config_file)
        self.logger = self._setup_logging()
        
        # Initialize components
        self.aws_monitor = AWSCostMonitor(self.config.get_aws_credentials())
        self.slack_notifier = SlackNotifier(
            self.config.slack_bot_token, 
            self.config.slack_channel
        )
        
        self.logger.info(f"Cost Monitor Bot initialized for project: {self.config.project_name}")
        self.logger.info(f"Configuration: {self.config.to_dict()}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cost_monitor.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def check_costs(self) -> Dict:
        """Main cost checking function"""
        try:
            self.logger.info("Starting cost check...")
            
            # Get current cost data
            current_cost, service_breakdown = self.aws_monitor.get_current_month_cost()
            
            # Get daily costs for trend analysis
            daily_costs = self.aws_monitor.get_daily_costs(self.config.monitoring_period_days)
            
            # Check for anomalies
            anomalies = self.aws_monitor.check_cost_anomalies()
            
            # Prepare result
            result = {
                'timestamp': datetime.now().isoformat(),
                'project_name': self.config.project_name,
                'current_cost': current_cost,
                'threshold': self.config.cost_threshold,
                'currency': self.config.currency,
                'service_breakdown': service_breakdown,
                'daily_costs': daily_costs,
                'anomalies': anomalies,
                'threshold_exceeded': current_cost > self.config.cost_threshold,
                'percentage_of_threshold': (current_cost / self.config.cost_threshold) * 100
            }
            
            self.logger.info(f"Cost check completed: ${current_cost:.2f} (threshold: ${self.config.cost_threshold:.2f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during cost check: {str(e)}")
            raise
    
    def send_alert(self, cost_data: Dict) -> bool:
        """Send cost alert based on cost data"""
        try:
            # Always send if threshold exceeded, or if it's a scheduled summary
            should_alert = (
                cost_data['threshold_exceeded'] or 
                cost_data['percentage_of_threshold'] >= 80 or
                cost_data['anomalies']
            )
            
            if should_alert:
                success = self.slack_notifier.send_cost_alert(
                    project_name=cost_data['project_name'],
                    current_cost=cost_data['current_cost'],
                    threshold=cost_data['threshold'],
                    period_days=self.config.monitoring_period_days,
                    currency=cost_data['currency'],
                    cost_breakdown=cost_data['service_breakdown']
                )
                
                if success:
                    self.logger.info("Cost alert sent successfully")
                else:
                    self.logger.error("Failed to send cost alert")
                
                return success
            else:
                self.logger.info("No alert needed - costs within normal range")
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending alert: {str(e)}")
            return False
    
    def send_summary(self, cost_data: Dict) -> bool:
        """Send cost summary report"""
        try:
            success = self.slack_notifier.send_cost_summary(
                project_name=cost_data['project_name'],
                total_cost=cost_data['current_cost'],
                daily_costs=cost_data['daily_costs'],
                currency=cost_data['currency']
            )
            
            if success:
                self.logger.info("Cost summary sent successfully")
            else:
                self.logger.error("Failed to send cost summary")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending summary: {str(e)}")
            return False
    
    def run_check(self) -> bool:
        """Run a complete cost check and notification cycle"""
        try:
            # Check costs
            cost_data = self.check_costs()
            
            # Send alert if needed
            alert_success = self.send_alert(cost_data)
            
            # Log anomalies
            if cost_data['anomalies']:
                self.logger.warning(f"Cost anomalies detected: {len(cost_data['anomalies'])} anomalies")
                for anomaly in cost_data['anomalies']:
                    self.logger.warning(f"Anomaly: {anomaly['description']} (severity: {anomaly['severity']})")
            
            return alert_success
            
        except Exception as e:
            self.logger.error(f"Error in run_check: {str(e)}")
            # Send error notification to Slack
            try:
                self.slack_notifier.client.chat_postMessage(
                    channel=self.config.slack_channel,
                    text=f"🚨 AWS Cost Monitor Error for {self.config.project_name}:\n```{str(e)}```",
                    username="AWS Cost Monitor",
                    icon_emoji=":rotating_light:"
                )
            except:
                pass  # Don't fail if error notification fails
            
            return False
    
    def run_summary(self) -> bool:
        """Run cost summary report"""
        try:
            cost_data = self.check_costs()
            return self.send_summary(cost_data)
        except Exception as e:
            self.logger.error(f"Error in run_summary: {str(e)}")
            return False
    
    def test_connections(self) -> bool:
        """Test all connections and configurations"""
        try:
            self.logger.info("Testing connections...")
            
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
            
            # Send test message if both connections work
            if slack_ok and aws_ok:
                self.slack_notifier.client.chat_postMessage(
                    channel=self.config.slack_channel,
                    text=f"✅ AWS Cost Monitor test successful for *{self.config.project_name}*\nBot is ready to monitor costs!",
                    username="AWS Cost Monitor",
                    icon_emoji=":white_check_mark:"
                )
                self.logger.info("All connection tests passed")
                return True
            else:
                self.logger.error("Connection tests failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing connections: {str(e)}")
            return False
    
    def schedule_monitoring(self):
        """Schedule regular monitoring based on configuration"""
        
        # Clear any existing schedules
        schedule.clear()
        
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
            schedule.every().month.do(self.run_check)
            schedule.every().month.do(self.run_summary)
            self.logger.info("Scheduled monthly monitoring")
        
        # Always check every 6 hours for threshold breaches
        schedule.every(6).hours.do(self.run_check)
        self.logger.info("Added 6-hourly threshold checks")
    
    def start_monitoring(self):
        """Start the monitoring bot"""
        self.logger.info(f"Starting AWS Cost Monitor Bot for {self.config.project_name}")
        
        # Test connections first
        if not self.test_connections():
            self.logger.error("Connection tests failed. Please check your configuration.")
            return
        
        # Schedule monitoring
        self.schedule_monitoring()
        
        # Run initial check
        self.logger.info("Running initial cost check...")
        self.run_check()
        
        # Start the scheduler
        self.logger.info("Starting scheduler...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying 