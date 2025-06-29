import json
from typing import Dict, List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

class SlackNotifier:
    """Slack notification handler for AWS cost alerts"""
    
    def __init__(self, bot_token: str, channel: str = '#alerts'):
        self.client = WebClient(token=bot_token)
        self.channel = channel
        self.logger = logging.getLogger(__name__)
    
    def send_cost_alert(self, 
                       project_name: str,
                       current_cost: float,
                       threshold: float,
                       period_days: int,
                       currency: str = 'USD',
                       cost_breakdown: Optional[Dict] = None) -> bool:
        """Send cost alert to Slack channel"""
        
        try:
            # Determine alert level
            percentage_of_threshold = (current_cost / threshold) * 100
            
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
            
            # Add cost breakdown if provided
            if cost_breakdown and cost_breakdown:
                breakdown_text = ""
                for service, cost in sorted(cost_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
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
            
            # Add recommendations
            recommendations = self._get_recommendations(percentage_of_threshold)
            if recommendations:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Recommendations:*\n{recommendations}"
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
            
            self.logger.info(f"Cost alert sent successfully to {self.channel}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending Slack message: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack message: {str(e)}")
            return False
    
    def send_cost_summary(self, 
                         project_name: str,
                         total_cost: float,
                         daily_costs: List[Dict],
                         currency: str = 'USD') -> bool:
        """Send cost summary report to Slack"""
        
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
                        "text": f"📊 Cost Summary - {project_name}"
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
                text=f"Cost Summary for {project_name}",
                blocks=blocks,
                username="AWS Cost Monitor",
                icon_emoji=":chart_with_upwards_trend:"
            )
            
            self.logger.info(f"Cost summary sent successfully to {self.channel}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending Slack summary: {e.response['error']}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending Slack summary: {str(e)}")
            return False
    
    def _get_recommendations(self, percentage_of_threshold: float) -> str:
        """Get cost optimization recommendations based on usage"""
        
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