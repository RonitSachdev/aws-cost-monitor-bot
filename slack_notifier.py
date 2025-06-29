import json
from typing import Dict, List, Optional, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

class SlackNotifier:
    """ Slack notification handler for AWS cost alerts with service-specific controls"""
    
    def __init__(self, bot_token: str, channel: str = '#alerts', config=None):
        self.client = WebClient(token=bot_token)
        self.channel = channel
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_cost_alert(self, 
                       project_name: str,
                       current_cost: float,
                       threshold: float,
                       period_days: int,
                       currency: str = 'USD',
                       cost_breakdown: Optional[Dict] = None,
                       service_details: Optional[Dict] = None,
                       resource_costs: Optional[Dict] = None,
                       anomalies: Optional[List[Dict]] = None) -> bool:
        """Send  cost alert to Slack channel with service-specific details"""
        
        try:
            # Determine alert level based on configuration
            percentage_of_threshold = (current_cost / threshold) * 100
            
            if self.config:
                alert_levels = self.config.alert_levels
                if percentage_of_threshold >= alert_levels['critical']:
                    alert_level = "🚨 CRITICAL"
                    color = "#FF0000"
                elif percentage_of_threshold >= alert_levels['warning']:
                    alert_level = "⚠️ WARNING"
                    color = "#FF9900"
                elif percentage_of_threshold >= alert_levels['info']:
                    alert_level = "ℹ️ INFO"
                    color = "#36A64F"
                else:
                    alert_level = "✅ NORMAL"
                    color = "#00FF00"
            else:
                # Fallback to original logic
                if percentage_of_threshold >= 100:
                    alert_level = "🚨 CRITICAL"
                    color = "#FF0000"
                elif percentage_of_threshold >= 80:
                    alert_level = "⚠️ WARNING"
                    color = "#FF9900"
                else:
                    alert_level = "ℹ️ INFO"
                    color = "#36A64F"
            
            # Create main message
            message = f"{alert_level}: AWS Cost Alert for *{project_name}*"
            
            # Create detailed blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"AWS Cost Monitor - {project_name}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Cost:*\n{currency} {current_cost:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Threshold:*\n{currency} {threshold:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Period:*\n{period_days} days"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Percentage:*\n{percentage_of_threshold:.1f}%"
                        }
                    ]
                }
            ]
            
            # Add service-specific breakdown if enabled and available
            if (self.config and self.config.enable_detailed_breakdown and 
                service_details and self.config.max_services_in_alert > 0):
                
                # Sort services by cost and get top ones
                sorted_services = sorted(
                    service_details.items(), 
                    key=lambda x: x[1]['total_cost'], 
                    reverse=True
                )[:self.config.max_services_in_alert]
                
                if sorted_services:
                    service_text = ""
                    for service_name, service_data in sorted_services:
                        cost = service_data['total_cost']
                        service_threshold = service_data['threshold']
                        percentage = service_data['percentage_of_threshold']
                        
                        # Add emoji based on threshold status
                        if percentage >= 100:
                            emoji = "🔴"
                        elif percentage >= 80:
                            emoji = "🟡"
                        else:
                            emoji = "🟢"
                        
                        service_text += f"{emoji} *{service_name}*: {currency} {cost:.2f} ({percentage:.1f}%)\n"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Service Breakdown (Top {len(sorted_services)}):*\n{service_text}"
                        }
                    })
            
            # Add cost breakdown if provided (fallback to original logic)
            elif cost_breakdown and cost_breakdown:
                breakdown_text = ""
                max_services = self.config.max_services_in_alert if self.config else 10
                
                for service, cost in sorted(cost_breakdown.items(), key=lambda x: x[1], reverse=True)[:max_services]:
                    if cost > 0:
                        breakdown_text += f"• {service}: {currency} {cost:.2f}\n"
                
                if breakdown_text:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Top Services by Cost:*\n{breakdown_text}"
                        }
                    })
            
            # Add resource-level costs if available
            if resource_costs and self.config and self.config.enable_detailed_breakdown:
                # Get top expensive resources
                sorted_resources = sorted(
                    resource_costs.items(),
                    key=lambda x: x[1]['total_cost'],
                    reverse=True
                )[:5]  # Top 5 resources
                
                if sorted_resources:
                    resource_text = ""
                    for resource_id, resource_data in sorted_resources:
                        cost = resource_data['total_cost']
                        service = resource_data['service']
                        resource_text += f"• *{resource_id}* ({service}): {currency} {cost:.2f}\n"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Top Expensive Resources:*\n{resource_text}"
                        }
                    })
            
            # Add anomalies if detected
            if anomalies:
                anomaly_text = ""
                for anomaly in anomalies:
                    severity_emoji = "🔴" if anomaly['severity'] == 'high' else "🟡"
                    anomaly_text += f"{severity_emoji} {anomaly['description']}\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🚨 Cost Anomalies Detected:*\n{anomaly_text}"
                    }
                })
            
            # Add recommendations
            recommendations = self._get_recommendations(percentage_of_threshold, service_details, resource_costs)
            if recommendations:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💡 Recommendations:*\n{recommendations}"
                    }
                })
            
            # Send message
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                blocks=blocks,
                username="AWS Cost Monitor",
                icon_emoji=":moneybag:"
            )
            
            self.logger.info(f" cost alert sent successfully to {self.channel}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending Slack message: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack message: {str(e)}")
            return False
    
    def send_service_specific_alert(self, 
                                   project_name: str,
                                   service_name: str,
                                   service_data: Dict[str, Any],
                                   currency: str = 'USD') -> bool:
        """Send service-specific cost alert"""
        
        try:
            cost = service_data['total_cost']
            threshold = service_data['threshold']
            percentage = service_data['percentage_of_threshold']
            
            # Determine alert level
            if percentage >= 100:
                alert_level = "🚨 CRITICAL"
                color = "#FF0000"
            elif percentage >= 80:
                alert_level = "⚠️ WARNING"
                color = "#FF9900"
            else:
                alert_level = "ℹ️ INFO"
                color = "#36A64F"
            
            message = f"{alert_level}: Service Cost Alert - *{service_name}* in {project_name}"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Service Cost Alert - {service_name}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Service:*\n{service_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Project:*\n{project_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Cost:*\n{currency} {cost:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Threshold:*\n{currency} {threshold:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Percentage:*\n{percentage:.1f}%"
                        }
                    ]
                }
            ]
            
            # Add daily trend if available
            if service_data.get('daily_costs'):
                daily_costs = service_data['daily_costs']
                if len(daily_costs) >= 2:
                    recent_avg = sum(day['cost'] for day in daily_costs[-7:]) / min(7, len(daily_costs))
                    previous_avg = sum(day['cost'] for day in daily_costs[-14:-7]) / min(7, len(daily_costs[-14:-7])) if len(daily_costs) >= 14 else recent_avg
                    
                    trend = ((recent_avg - previous_avg) / previous_avg) * 100 if previous_avg > 0 else 0
                    trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Trend Analysis:*\n{trend_emoji} {trend:+.1f}% vs previous period"
                        }
                    })
            
            # Add service-specific recommendations
            service_recommendations = self._get_service_recommendations(service_name, percentage)
            if service_recommendations:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💡 {service_name} Recommendations:*\n{service_recommendations}"
                    }
                })
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                blocks=blocks,
                username="AWS Cost Monitor",
                icon_emoji=":gear:"
            )
            
            self.logger.info(f"Service-specific alert sent for {service_name}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending service alert: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending service alert: {str(e)}")
            return False
    
    def send_cost_summary(self, 
                         project_name: str,
                         total_cost: float,
                         daily_costs: List[Dict],
                         currency: str = 'USD',
                         service_details: Optional[Dict] = None,
                         forecast_data: Optional[Dict] = None,
                         utilization_data: Optional[Dict] = None) -> bool:
        """Send  cost summary report to Slack"""
        
        try:
            # Calculate trends
            if len(daily_costs) >= 2:
                trend = daily_costs[-1]['cost'] - daily_costs[-2]['cost']
                trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                trend_text = f"{trend_emoji} {currency} {abs(trend):.2f} vs. yesterday"
            else:
                trend_text = "No trend data available"
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊  Cost Summary - {project_name}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Cost:*\n{currency} {total_cost:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Daily Trend:*\n{trend_text}"
                        }
                    ]
                }
            ]
            
            # Add cost forecast if available
            if forecast_data and self.config and self.config.enable_cost_forecasting:
                forecast_cost = forecast_data.get('forecasted_cost', 0)
                forecast_days = forecast_data.get('forecast_period_days', 30)
                
                blocks.append({
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Forecast ({forecast_days} days):*\n{currency} {forecast_cost:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Forecast vs Current:*\n{((forecast_cost/total_cost - 1) * 100):+.1f}%"
                        }
                    ]
                })
            
            # Add service breakdown if available
            if service_details and self.config and self.config.enable_detailed_breakdown:
                # Get top 5 services by cost
                sorted_services = sorted(
                    service_details.items(),
                    key=lambda x: x[1]['total_cost'],
                    reverse=True
                )[:5]
                
                if sorted_services:
                    service_text = ""
                    for service_name, service_data in sorted_services:
                        cost = service_data['total_cost']
                        percentage = service_data['percentage_of_threshold']
                        service_text += f"• {service_name}: {currency} {cost:.2f} ({percentage:.1f}%)\n"
                    
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Top Services by Cost:*\n{service_text}"
                        }
                    })
            
            # Add resource utilization if available
            if utilization_data:
                utilization_text = ""
                for service_type, resources in utilization_data.items():
                    if resources:
                        count = len(resources)
                        utilization_text += f"• {service_type}: {count} resources\n"
                
                if utilization_text:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Resource Utilization:*\n{utilization_text}"
                        }
                    })
            
            # Add daily breakdown
            if daily_costs:
                daily_text = ""
                for day_data in daily_costs[-7:]:  # Last 7 days
                    daily_text += f"• {day_data['date']}: {currency} {day_data['cost']:.2f}\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Daily Costs (Last 7 days):*\n{daily_text}"
                    }
                })
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=f" Cost Summary for {project_name}",
                blocks=blocks,
                username="AWS Cost Monitor",
                icon_emoji=":chart_with_upwards_trend:"
            )
            
            self.logger.info(f" cost summary sent successfully to {self.channel}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending Slack summary: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack summary: {str(e)}")
            return False
    
    def _get_recommendations(self, percentage_of_threshold: float, 
                           service_details: Optional[Dict] = None,
                           resource_costs: Optional[Dict] = None) -> str:
        """Get  cost optimization recommendations"""
        
        recommendations = []
        
        if percentage_of_threshold >= 100:
            recommendations.extend([
                "• Immediately review high-cost services",
                "• Consider stopping non-essential resources",
                "• Set up billing alerts for real-time monitoring"
            ])
        elif percentage_of_threshold >= 80:
            recommendations.extend([
                "• Review resource utilization",
                "• Consider rightsizing instances",
                "• Enable cost optimization recommendations"
            ])
        else:
            recommendations.extend([
                "• Costs are within normal range",
                "• Consider setting up Reserved Instances for predictable workloads",
                "• Review and optimize storage costs"
            ])
        
        # Add service-specific recommendations
        if service_details:
            high_cost_services = [
                service for service, data in service_details.items()
                if data['percentage_of_threshold'] > 80
            ]
            
            if high_cost_services:
                recommendations.append(f"• Focus on optimizing: {', '.join(high_cost_services[:3])}")
        
        # Add resource-specific recommendations
        if resource_costs:
            expensive_resources = sorted(
                resource_costs.items(),
                key=lambda x: x[1]['total_cost'],
                reverse=True
            )[:3]
            
            if expensive_resources:
                resource_names = [r[0] for r in expensive_resources]
                recommendations.append(f"• Review expensive resources: {', '.join(resource_names)}")
        
        return "\n".join(recommendations)
    
    def _get_service_recommendations(self, service_name: str, percentage: float) -> str:
        """Get service-specific recommendations"""
        
        service_recommendations = {
            'Amazon EC2': [
                "• Check for unused instances",
                "• Consider Spot Instances for non-critical workloads",
                "• Right-size instance types",
                "• Use Reserved Instances for predictable workloads"
            ],
            'Amazon RDS': [
                "• Review database instance sizes",
                "• Consider Multi-AZ only for critical databases",
                "• Use Reserved Instances for production databases",
                "• Check for unused read replicas"
            ],
            'Amazon S3': [
                "• Review storage classes (move to cheaper tiers)",
                "• Check for unused buckets",
                "• Enable lifecycle policies",
                "• Review access patterns"
            ],
            'AWS Lambda': [
                "• Optimize function memory allocation",
                "• Review function execution time",
                "• Check for unused functions",
                "• Consider provisioned concurrency for consistent workloads"
            ],
            'Amazon CloudFront': [
                "• Review cache hit ratios",
                "• Optimize cache settings",
                "• Consider regional edge caches",
                "• Review origin costs"
            ]
        }
        
        recommendations = service_recommendations.get(service_name, [
            "• Review service usage patterns",
            "• Check for unused resources",
            "• Consider cost optimization options",
            "• Monitor usage trends"
        ])
        
        if percentage > 100:
            recommendations.insert(0, "🚨 **IMMEDIATE ACTION REQUIRED** - Service exceeds threshold!")
        elif percentage > 80:
            recommendations.insert(0, "⚠️ **WARNING** - Service approaching threshold")
        
        return "\n".join(recommendations)
    
    def test_connection(self) -> bool:
        """Test Slack connection"""
        try:
            response = self.client.auth_test()
            self.logger.info(f"Slack connection successful. Bot user: {response['user']}")
            return True
        except SlackApiError as e:
            self.logger.error(f"Slack connection failed: {e.response['error']}")
            return False 