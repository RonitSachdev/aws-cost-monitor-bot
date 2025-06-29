import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from botocore.exceptions import ClientError, NoCredentialsError

class AWSCostMonitor:
    """ AWS Cost monitoring and analysis with service-specific controls"""
    
    def __init__(self, aws_credentials: Dict[str, str], config):
        """Initialize AWS Cost Monitor with credentials and configuration"""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        try:
            self.cost_explorer = boto3.client(
                'ce',
                **aws_credentials
            )
            self.cloudwatch = boto3.client(
                'cloudwatch',
                **aws_credentials
            )
            self.ec2 = boto3.client('ec2', **aws_credentials)
            self.rds = boto3.client('rds', **aws_credentials)
            self.s3 = boto3.client('s3', **aws_credentials)
            self.lambda_client = boto3.client('lambda', **aws_credentials)
            
            self.logger.info("AWS Cost Explorer and service clients initialized successfully")
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise
        except Exception as e:
            self.logger.error(f"Error initializing AWS clients: {str(e)}")
            raise
    
    def get_cost_and_usage(self, 
                          days: int = 7, 
                          granularity: str = 'DAILY',
                          group_by: Optional[List[Dict]] = None,
                          filters: Optional[List[Dict]] = None) -> Dict:
        """
        Get cost and usage data from AWS Cost Explorer with  filtering
        
        Args:
            days: Number of days to look back
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: List of group by dimensions
            filters: List of filters to apply
            
        Returns:
            Dictionary containing cost data
        """
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Default group by service
            if group_by is None:
                group_by = [
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            
            # Apply configuration filters
            if filters is None:
                filters = self.config.get_cost_explorer_filters()
            
            # Get cost and usage
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=group_by,
                Filter=self._build_filter_expression(filters) if filters else None
            )
            
            return self._process_cost_data(response)
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting cost data: {str(e)}")
            raise
    
    def get_current_month_cost(self) -> Tuple[float, Dict[str, float]]:
        """Get current month's cost and breakdown by service with filtering"""
        try:
            # Get first day of current month
            now = datetime.now()
            start_of_month = now.replace(day=1).date()
            end_date = now.date()
            
            # Apply service filters
            filters = self.config.get_cost_explorer_filters()
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_of_month.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter=self._build_filter_expression(filters) if filters else None
            )
            
            total_cost = 0.0
            service_costs = {}
            
            if response['ResultsByTime']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    # Only include enabled services
                    if self.config.is_service_enabled(service_name):
                        service_costs[service_name] = cost
                        total_cost += cost
            
            return total_cost, service_costs
            
        except Exception as e:
            self.logger.error(f"Error getting current month cost: {str(e)}")
            return 0.0, {}
    
    def get_service_specific_costs(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Get detailed cost breakdown for each enabled service"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            service_details = {}
            
            for service in self.config.get_enabled_services_list():
                try:
                    # Get cost for specific service
                    response = self.cost_explorer.get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date.strftime('%Y-%m-%d'),
                            'End': end_date.strftime('%Y-%m-%d')
                        },
                        Granularity='DAILY',
                        Metrics=['BlendedCost'],
                        Filter={
                            'Dimensions': {
                                'Key': 'SERVICE',
                                'Values': [service]
                            }
                        }
                    )
                    
                    total_cost = 0.0
                    daily_costs = []
                    
                    for result in response['ResultsByTime']:
                        cost = float(result['Total']['BlendedCost']['Amount'])
                        total_cost += cost
                        daily_costs.append({
                            'date': result['TimePeriod']['Start'],
                            'cost': cost
                        })
                    
                    service_threshold = self.config.get_service_threshold(service)
                    
                    service_details[service] = {
                        'total_cost': total_cost,
                        'daily_costs': daily_costs,
                        'threshold': service_threshold,
                        'threshold_exceeded': total_cost > service_threshold,
                        'percentage_of_threshold': (total_cost / service_threshold) * 100 if service_threshold > 0 else 0
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error getting cost for service {service}: {str(e)}")
                    continue
            
            return service_details
            
        except Exception as e:
            self.logger.error(f"Error getting service-specific costs: {str(e)}")
            return {}
    
    def get_resource_level_costs(self, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by individual resources (where available)"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            resource_costs = {}
            
            # Get costs grouped by resource
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'RESOURCE_ID'
                    }
                ]
            )
            
            for result in response['ResultsByTime']:
                for group in result.get('Groups', []):
                    service_name = group['Keys'][0]
                    resource_id = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    # Check if service is enabled and resource should be monitored
                    if (self.config.is_service_enabled(service_name) and 
                        self.config.should_monitor_resource(resource_id)):
                        
                        if resource_id not in resource_costs:
                            resource_costs[resource_id] = {
                                'service': service_name,
                                'total_cost': 0.0,
                                'daily_costs': []
                            }
                        
                        resource_costs[resource_id]['total_cost'] += cost
                        resource_costs[resource_id]['daily_costs'].append({
                            'date': result['TimePeriod']['Start'],
                            'cost': cost
                        })
            
            return resource_costs
            
        except Exception as e:
            self.logger.error(f"Error getting resource-level costs: {str(e)}")
            return {}
    
    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily cost breakdown for specified number of days with filtering"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Apply configuration filters
            filters = self.config.get_cost_explorer_filters()
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                Filter=self._build_filter_expression(filters) if filters else None
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                cost = float(result['Total']['BlendedCost']['Amount'])
                daily_costs.append({
                    'date': date,
                    'cost': cost
                })
            
            return sorted(daily_costs, key=lambda x: x['date'])
            
        except Exception as e:
            self.logger.error(f"Error getting daily costs: {str(e)}")
            return []
    
    def get_cost_forecast(self, days: int = 30) -> Dict:
        """Get cost forecast for next N days"""
        if not self.config.enable_cost_forecasting:
            return {}
            
        try:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=days)
            
            # Apply configuration filters
            filters = self.config.get_cost_explorer_filters()
            
            response = self.cost_explorer.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='BLENDED_COST',
                Granularity='MONTHLY',
                Filter=self._build_filter_expression(filters) if filters else None
            )
            
            return {
                'forecasted_cost': float(response['Total']['Amount']),
                'currency': response['Total']['Unit'],
                'forecast_period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cost forecast: {str(e)}")
            return {}
    
    def check_cost_anomalies(self) -> List[Dict]:
        """ cost anomaly detection with configurable sensitivity"""
        if not self.config.enable_anomaly_detection:
            return []
            
        try:
            daily_costs = self.get_daily_costs(days=30)
            
            if len(daily_costs) < 7:
                return []
            
            # Calculate sensitivity multiplier based on configuration
            sensitivity_multipliers = {
                'low': 2.0,      # 100% increase
                'medium': 1.5,   # 50% increase  
                'high': 1.2      # 20% increase
            }
            
            multiplier = sensitivity_multipliers.get(self.config.anomaly_sensitivity, 1.5)
            
            # Calculate average of last 7 days vs previous 7 days
            recent_avg = sum(day['cost'] for day in daily_costs[-7:]) / 7
            previous_avg = sum(day['cost'] for day in daily_costs[-14:-7]) / 7
            
            anomalies = []
            
            # Check if recent average is significantly higher
            if recent_avg > previous_avg * multiplier:
                anomalies.append({
                    'type': 'cost_spike',
                    'description': f'Recent 7-day average (${recent_avg:.2f}) is {((recent_avg/previous_avg - 1) * 100):.1f}% higher than previous week',
                    'severity': 'high' if recent_avg > previous_avg * 2 else 'medium',
                    'sensitivity': self.config.anomaly_sensitivity
                })
            
            # Check for sudden daily spikes
            for i, day in enumerate(daily_costs[-7:]):
                if i > 0:
                    prev_day = daily_costs[-(8-i)]
                    if day['cost'] > prev_day['cost'] * multiplier:
                        anomalies.append({
                            'type': 'daily_spike',
                            'description': f'Cost spike on {day["date"]}: ${day["cost"]:.2f} (vs ${prev_day["cost"]:.2f} previous day)',
                            'severity': 'high',
                            'sensitivity': self.config.anomaly_sensitivity
                        })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error checking cost anomalies: {str(e)}")
            return []
    
    def get_resource_utilization(self) -> Dict:
        """Get resource utilization metrics for enabled services"""
        try:
            utilization_data = {}
            
            # EC2 Instance utilization
            if self.config.is_service_enabled('Amazon EC2'):
                try:
                    instances = self.ec2.describe_instances()
                    ec2_utilization = []
                    
                    for reservation in instances['Reservations']:
                        for instance in reservation['Instances']:
                            if self.config.should_monitor_resource(instance['InstanceId']):
                                ec2_utilization.append({
                                    'instance_id': instance['InstanceId'],
                                    'state': instance['State']['Name'],
                                    'instance_type': instance['InstanceType'],
                                    'launch_time': instance['LaunchTime'].isoformat()
                                })
                    
                    utilization_data['ec2_instances'] = ec2_utilization
                    
                except Exception as e:
                    self.logger.warning(f"Error getting EC2 utilization: {str(e)}")
            
            # RDS Instance utilization
            if self.config.is_service_enabled('Amazon RDS'):
                try:
                    rds_instances = self.rds.describe_db_instances()
                    rds_utilization = []
                    
                    for instance in rds_instances['DBInstances']:
                        if self.config.should_monitor_resource(instance['DBInstanceIdentifier']):
                            rds_utilization.append({
                                'instance_id': instance['DBInstanceIdentifier'],
                                'engine': instance['Engine'],
                                'instance_class': instance['DBInstanceClass'],
                                'status': instance['DBInstanceStatus']
                            })
                    
                    utilization_data['rds_instances'] = rds_utilization
                    
                except Exception as e:
                    self.logger.warning(f"Error getting RDS utilization: {str(e)}")
            
            # Lambda function utilization
            if self.config.is_service_enabled('AWS Lambda'):
                try:
                    functions = self.lambda_client.list_functions()
                    lambda_utilization = []
                    
                    for function in functions['Functions']:
                        if self.config.should_monitor_resource(function['FunctionName']):
                            lambda_utilization.append({
                                'function_name': function['FunctionName'],
                                'runtime': function['Runtime'],
                                'memory_size': function['MemorySize'],
                                'timeout': function['Timeout']
                            })
                    
                    utilization_data['lambda_functions'] = lambda_utilization
                    
                except Exception as e:
                    self.logger.warning(f"Error getting Lambda utilization: {str(e)}")
            
            return utilization_data
            
        except Exception as e:
            self.logger.error(f"Error getting resource utilization: {str(e)}")
            return {}
    
    def _build_filter_expression(self, filters: List[Dict]) -> Dict:
        """Build Cost Explorer filter expression from multiple filters"""
        if not filters:
            return {}
        
        if len(filters) == 1:
            return filters[0]
        
        # Combine multiple filters with AND logic
        return {
            'And': filters
        }
    
    def _process_cost_data(self, response: Dict) -> Dict:
        """Process raw cost data from AWS API with  filtering"""
        processed_data = {
            'total_cost': 0.0,
            'currency': 'USD',
            'daily_breakdown': [],
            'service_breakdown': {},
            'time_period': {
                'start': '',
                'end': ''
            }
        }
        
        try:
            # Extract time period
            if response['ResultsByTime']:
                first_result = response['ResultsByTime'][0]
                last_result = response['ResultsByTime'][-1]
                processed_data['time_period']['start'] = first_result['TimePeriod']['Start']
                processed_data['time_period']['end'] = last_result['TimePeriod']['End']
            
            # Process each time period
            for result in response['ResultsByTime']:
                time_period = result['TimePeriod']['Start']
                
                # Calculate total for this period
                period_total = float(result['Total'].get('BlendedCost', {}).get('Amount', 0))
                processed_data['total_cost'] += period_total
                
                # Get currency
                if result['Total'].get('BlendedCost', {}).get('Unit'):
                    processed_data['currency'] = result['Total']['BlendedCost']['Unit']
                
                # Daily breakdown
                processed_data['daily_breakdown'].append({
                    'date': time_period,
                    'cost': period_total
                })
                
                # Service breakdown with filtering
                for group in result.get('Groups', []):
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    service_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    # Only include enabled services
                    if self.config.is_service_enabled(service_name):
                        if service_name not in processed_data['service_breakdown']:
                            processed_data['service_breakdown'][service_name] = 0.0
                        processed_data['service_breakdown'][service_name] += service_cost
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing cost data: {str(e)}")
            return processed_data 