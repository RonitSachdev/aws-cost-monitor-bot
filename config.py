import os
import json
import yaml
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

load_dotenv()

class Config:
    """ configuration management for AWS Cost Monitoring Bot"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config_data = {}
        
        if config_file:
            self._load_config_file()
        
        # AWS Configuration
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Slack Configuration
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#alerts')
        
        # Cost Monitoring Configuration
        self.cost_threshold = float(os.getenv('COST_THRESHOLD', '100.0'))
        self.monitoring_period_days = int(os.getenv('MONITORING_PERIOD_DAYS', '7'))
        self.currency = os.getenv('CURRENCY', 'USD')
        
        # Project Configuration
        self.project_name = os.getenv('PROJECT_NAME', 'AWS Project')
        self.notification_frequency = os.getenv('NOTIFICATION_FREQUENCY', 'daily')
        
        #  Service-Specific Configuration
        self.enabled_services = self._parse_list(os.getenv('ENABLED_SERVICES', 'all'))
        self.disabled_services = self._parse_list(os.getenv('DISABLED_SERVICES', ''))
        self.service_thresholds = self._parse_service_thresholds(os.getenv('SERVICE_THRESHOLDS', '{}'))
        
        # Resource ARN Configuration
        self.resource_arns = self._parse_list(os.getenv('RESOURCE_ARNS', ''))
        self.excluded_arns = self._parse_list(os.getenv('EXCLUDED_ARNS', ''))
        self.tag_filters = self._parse_tag_filters(os.getenv('TAG_FILTERS', '{}'))
        
        # Advanced Monitoring Options
        self.enable_anomaly_detection = os.getenv('ENABLE_ANOMALY_DETECTION', 'true').lower() == 'true'
        self.anomaly_sensitivity = os.getenv('ANOMALY_SENSITIVITY', 'medium')  # low, medium, high
        self.enable_cost_forecasting = os.getenv('ENABLE_COST_FORECASTING', 'true').lower() == 'true'
        self.forecast_days = int(os.getenv('FORECAST_DAYS', '30'))
        
        # Alert Configuration
        self.alert_levels = self._parse_alert_levels()
        self.enable_detailed_breakdown = os.getenv('ENABLE_DETAILED_BREAKDOWN', 'true').lower() == 'true'
        self.max_services_in_alert = int(os.getenv('MAX_SERVICES_IN_ALERT', '10'))
        
        # Scheduling Configuration
        self.check_interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', '6'))
        self.enable_weekend_monitoring = os.getenv('ENABLE_WEEKEND_MONITORING', 'true').lower() == 'true'
        self.timezone = os.getenv('TIMEZONE', 'UTC')
        
        # Debug and Logging
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        self._validate_config()
    
    def _load_config_file(self):
        """Load configuration from JSON or YAML file"""
        if not self.config_file:
            return
            
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith('.json'):
                    self.config_data = json.load(f)
                elif self.config_file.endswith(('.yml', '.yaml')):
                    self.config_data = yaml.safe_load(f)
                else:
                    raise ValueError("Config file must be JSON or YAML format")
                    
            # Override environment variables with config file values
            for key, value in self.config_data.items():
                if hasattr(self, key.lower()):
                    setattr(self, key.lower(), value)
                    
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found. Using environment variables.")
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def _parse_list(self, value: Optional[str]) -> List[str]:
        """Parse comma-separated string into list"""
        if not value or value.strip() == '':
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _parse_service_thresholds(self, value: Optional[str]) -> Dict[str, float]:
        """Parse service-specific thresholds"""
        try:
            if value and value.startswith('{') and value.endswith('}'):
                return json.loads(value)
            return {}
        except:
            return {}
    
    def _parse_tag_filters(self, value: Optional[str]) -> Dict[str, str]:
        """Parse tag filters for resource filtering"""
        try:
            if value and value.startswith('{') and value.endswith('}'):
                return json.loads(value)
            return {}
        except:
            return {}
    
    def _parse_alert_levels(self) -> Dict[str, float]:
        """Parse alert level thresholds"""
        return {
            'critical': float(os.getenv('ALERT_CRITICAL_PERCENT', '100.0')),
            'warning': float(os.getenv('ALERT_WARNING_PERCENT', '80.0')),
            'info': float(os.getenv('ALERT_INFO_PERCENT', '50.0'))
        }
    
    def _validate_config(self):
        """Validate required configuration parameters"""
        required_params = [
            ('slack_bot_token', 'SLACK_BOT_TOKEN'),
            ('aws_access_key_id', 'AWS_ACCESS_KEY_ID'),
            ('aws_secret_access_key', 'AWS_SECRET_ACCESS_KEY')
        ]
        
        missing_params = []
        for param, env_var in required_params:
            if not getattr(self, param):
                missing_params.append(env_var)
        
        if missing_params:
            raise ValueError(f"Missing required configuration parameters: {', '.join(missing_params)}")
    
    def get_aws_credentials(self) -> Dict[str, str]:
        """Get AWS credentials dictionary"""
        return {
            'aws_access_key_id': self.aws_access_key_id or '',
            'aws_secret_access_key': self.aws_secret_access_key or '',
            'region_name': self.aws_region
        }
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a specific service is enabled for monitoring"""
        # If disabled_services contains the service, it's disabled
        if service_name.lower() in [s.lower() for s in self.disabled_services]:
            return False
        
        # If enabled_services is 'all' or contains the service, it's enabled
        if 'all' in [s.lower() for s in self.enabled_services]:
            return True
        
        return service_name.lower() in [s.lower() for s in self.enabled_services]
    
    def get_service_threshold(self, service_name: str) -> float:
        """Get threshold for a specific service, fallback to global threshold"""
        return self.service_thresholds.get(service_name.lower(), self.cost_threshold)
    
    def get_enabled_services_list(self) -> List[str]:
        """Get list of enabled services for monitoring"""
        if 'all' in [s.lower() for s in self.enabled_services]:
            # Return common AWS services, excluding disabled ones
            common_services = [
                'Amazon EC2', 'Amazon RDS', 'Amazon S3', 'Amazon CloudFront',
                'AWS Lambda', 'Amazon DynamoDB', 'Amazon ECS', 'Amazon EKS',
                'Amazon ElastiCache', 'Amazon Redshift', 'Amazon EMR',
                'Amazon SageMaker', 'Amazon API Gateway', 'Amazon CloudWatch',
                'Amazon Route 53', 'AWS Data Transfer', 'Amazon VPC',
                'Amazon Elastic Load Balancing', 'Amazon EBS', 'Amazon Glacier'
            ]
            return [s for s in common_services if self.is_service_enabled(s)]
        else:
            return self.enabled_services
    
    def should_monitor_resource(self, resource_arn: str) -> bool:
        """Check if a specific resource should be monitored based on ARN filters"""
        # If excluded_arns contains the ARN, exclude it
        for excluded_arn in self.excluded_arns:
            if excluded_arn in resource_arn:
                return False
        
        # If resource_arns is empty, monitor all (except excluded)
        if not self.resource_arns:
            return True
        
        # If resource_arns contains the ARN, include it
        for included_arn in self.resource_arns:
            if included_arn in resource_arn:
                return True
        
        return False
    
    def get_cost_explorer_filters(self) -> List[Dict]:
        """Get filters for Cost Explorer API calls"""
        filters = []
        
        # Add service filters
        if self.enabled_services and 'all' not in [s.lower() for s in self.enabled_services]:
            filters.append({
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': self.get_enabled_services_list()
                }
            })
        
        # Add tag filters
        for tag_key, tag_value in self.tag_filters.items():
            filters.append({
                'Tags': {
                    'Key': tag_key,
                    'Values': [tag_value] if isinstance(tag_value, str) else tag_value
                }
            })
        
        return filters
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for logging/debugging"""
        return {
            'project_name': self.project_name,
            'aws_region': self.aws_region,
            'slack_channel': self.slack_channel,
            'cost_threshold': self.cost_threshold,
            'monitoring_period_days': self.monitoring_period_days,
            'currency': self.currency,
            'notification_frequency': self.notification_frequency,
            'enabled_services': self.enabled_services,
            'disabled_services': self.disabled_services,
            'service_thresholds': self.service_thresholds,
            'resource_arns': self.resource_arns,
            'excluded_arns': self.excluded_arns,
            'tag_filters': self.tag_filters,
            'enable_anomaly_detection': self.enable_anomaly_detection,
            'anomaly_sensitivity': self.anomaly_sensitivity,
            'enable_cost_forecasting': self.enable_cost_forecasting,
            'forecast_days': self.forecast_days,
            'alert_levels': self.alert_levels,
            'check_interval_hours': self.check_interval_hours,
            'debug_mode': self.debug_mode
        } 