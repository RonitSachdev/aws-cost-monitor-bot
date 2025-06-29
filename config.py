import os
import json
import yaml
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for AWS Cost Monitoring Bot"""
    
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
        self.notification_frequency = os.getenv('NOTIFICATION_FREQUENCY', 'daily')  # daily, weekly, monthly
        
        self._validate_config()
    
    def _load_config_file(self):
        """Load configuration from JSON or YAML file"""
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
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key,
            'region_name': self.aws_region
        }
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for logging/debugging"""
        return {
            'project_name': self.project_name,
            'aws_region': self.aws_region,
            'slack_channel': self.slack_channel,
            'cost_threshold': self.cost_threshold,
            'monitoring_period_days': self.monitoring_period_days,
            'currency': self.currency,
            'notification_frequency': self.notification_frequency
        } 