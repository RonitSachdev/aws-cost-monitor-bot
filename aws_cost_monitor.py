import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from botocore.exceptions import ClientError, NoCredentialsError

class AWSCostMonitor:
    """AWS Cost monitoring and analysis"""
    
    def __init__(self, aws_credentials: Dict[str, str]):
        """Initialize AWS Cost Monitor with credentials"""
        self.logger = logging.getLogger(__name__)
        
        try:
            self.cost_explorer = boto3.client(
                'ce',
                **aws_credentials
            )
            self.cloudwatch = boto3.client(
                'cloudwatch',
                **aws_credentials
            )
            self.logger.info("AWS Cost Explorer client initialized successfully")
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise
        except Exception as e:
            self.logger.error(f"Error initializing AWS clients: {str(e)}")
            raise
    
    def get_cost_and_usage(self, 
                          days: int = 7, 
                          granularity: str = 'DAILY',
                          group_by: Optional[List[Dict]] = None) -> Dict:
        """
        Get cost and usage data from AWS Cost Explorer
        
        Args:
            days: Number of days to look back
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: List of group by dimensions
            
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
            
            # Get cost and usage
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UnblendedCost', 'UsageQuantity'],
                GroupBy=group_by
            )
            
            return self._process_cost_data(response)
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting cost data: {str(e)}")
            raise
    
    def get_current_month_cost(self) -> Tuple[float, Dict[str, float]]:
        """Get current month's cost and breakdown by service"""
        try:
            # Get first day of current month
            now = datetime.now()
            start_of_month = now.replace(day=1).date()
            end_date = now.date()
            
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
                ]
            )
            
            total_cost = 0.0
            service_costs = {}
            
            if response['ResultsByTime']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    service_costs[service_name] = cost
                    total_cost += cost
            
            return total_cost, service_costs
            
        except Exception as e:
            self.logger.error(f"Error getting current month cost: {str(e)}")
            return 0.0, {}
    
    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily cost breakdown for specified number of days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
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
        try:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=days)
            
            response = self.cost_explorer.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='BLENDED_COST',
                Granularity='MONTHLY'
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
        """Check for cost anomalies using AWS Cost Anomaly Detection"""
        try:
            # This requires Cost Anomaly Detection to be set up
            # For now, we'll implement a simple threshold-based anomaly detection
            daily_costs = self.get_daily_costs(days=30)
            
            if len(daily_costs) < 7:
                return []
            
            # Calculate average of last 7 days vs previous 7 days
            recent_avg = sum(day['cost'] for day in daily_costs[-7:]) / 7
            previous_avg = sum(day['cost'] for day in daily_costs[-14:-7]) / 7
            
            anomalies = []
            
            # Check if recent average is significantly higher
            if recent_avg > previous_avg * 1.5:  # 50% increase
                anomalies.append({
                    'type': 'cost_spike',
                    'description': f'Recent 7-day average (${recent_avg:.2f}) is {((recent_avg/previous_avg - 1) * 100):.1f}% higher than previous week',
                    'severity': 'high' if recent_avg > previous_avg * 2 else 'medium'
                })
            
            # Check for sudden daily spikes
            for i, day in enumerate(daily_costs[-7:]):
                if i > 0:
                    prev_day = daily_costs[-(8-i)]
                    if day['cost'] > prev_day['cost'] * 2:  # 100% increase
                        anomalies.append({
                            'type': 'daily_spike',
                            'description': f'Cost spike on {day["date"]}: ${day["cost"]:.2f} (vs ${prev_day["cost"]:.2f} previous day)',
                            'severity': 'high'
                        })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error checking cost anomalies: {str(e)}")
            return []
    
    def _process_cost_data(self, response: Dict) -> Dict:
        """Process raw cost data from AWS API"""
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
                
                # Service breakdown
                for group in result.get('Groups', []):
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    service_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service_name not in processed_data['service_breakdown']:
                        processed_data['service_breakdown'][service_name] = 0.0
                    processed_data['service_breakdown'][service_name] += service_cost
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing cost data: {str(e)}")
            return processed_data
    
    def get_resource_utilization(self) -> Dict:
        """Get basic resource utilization metrics"""
        try:
            # Get EC2 instance utilization
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            # This is a simplified version - in a real implementation,
            # you'd want to get actual instance IDs and check their utilization
            
            return {
                'ec2_utilization': 'Feature requires specific instance monitoring setup',
                'rds_utilization': 'Feature requires specific RDS monitoring setup',
                'note': 'Implement specific resource monitoring based on your AWS resources'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting resource utilization: {str(e)}")
            return {} 