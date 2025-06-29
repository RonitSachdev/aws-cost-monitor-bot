# AWS Cost Monitoring Bot
A comprehensive, AWS cost monitoring solution that tracks your AWS spending with **granular service-specific controls**, **resource-level filtering**, and intelligent alerts to Slack. Perfect for keeping your AWS costs under control across multiple projects with **unprecedented flexibility**.

## Features

### **Service-Specific Controls**
- **Enable/Disable Services**: Monitor only the services you care about
- **Service-Specific Thresholds**: Set different cost limits for each AWS service
- **Granular Filtering**: Exclude specific services from monitoring
- **Resource ARN Filtering**: Monitor specific resources or exclude unwanted ones
- **Tag-Based Filtering**: Filter costs by AWS resource tags

### **Advanced Cost Analysis**
- **Service-Level Breakdown**: Detailed cost analysis per AWS service
- **Resource-Level Costs**: Track costs of individual resources (EC2, RDS, Lambda, etc.)
- **Configurable Anomaly Detection**: Low, medium, or high sensitivity
- **Cost Forecasting**: Predict future costs with configurable timeframes
- ** Trend Analysis**: Advanced cost trend detection and reporting

### **Intelligent Alerting System**
- **Multi-Level Alerts**: Critical, Warning, Info, and Normal levels
- **Service-Specific Alerts**: Individual alerts for each service
- **Resource-Level Alerts**: Alerts for expensive individual resources
- **Anomaly Alerts**: Automatic detection of unusual spending patterns
- **Actionable Recommendations**: Service-specific optimization suggestions

### **Enterprise Configuration**
- **Flexible Scheduling**: Configurable check intervals (1-24 hours)
- **Weekend Controls**: Enable/disable monitoring on weekends
- **Timezone Support**: Configure monitoring for your timezone
- **Debug Mode**:  logging and troubleshooting
- **Multiple Deployment Options**: CLI, Docker, Cron, Systemd

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd aws-cost-monitoring-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. AWS Setup

1. **Create IAM User** with the following permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "ce:GetCostAndUsage",
                   "ce:GetDimensionValues",
                   "ce:GetReservationCoverage",
                   "ce:GetReservationPurchaseRecommendation",
                   "ce:GetReservationUtilization",
                   "ce:GetUsageReport",
                   "ce:DescribeCostCategoryDefinition",
                   "ce:GetRightsizingRecommendation",
                   "ce:GetSavingsPlansUtilization",
                   "ce:GetCostForecast",
                   "ec2:DescribeInstances",
                   "rds:DescribeDBInstances",
                   "lambda:ListFunctions",
                   "s3:ListBuckets"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

2. **Save AWS credentials** (access key ID and secret access key)

### 3. Slack Setup

1. **Create a Slack App**:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Enter app name and select workspace

2. **Configure Bot Token Scopes**:
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write`
     - `chat:write.public`
     - `files:write`

3. **Install App to Workspace**:
   - Click "Install to Workspace"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

4. **Invite Bot to Channel**:
   ```
   /invite @YourBotName
   ```

### 4.  Configuration

Copy the  environment file and configure:

```bash
cp env..example .env
```

Edit `.env` with your credentials and preferences:

```bash
# Basic Configuration
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_CHANNEL=#aws-alerts

#  Service Controls
ENABLED_SERVICES=all
DISABLED_SERVICES=Amazon Glacier,AWS Data Transfer
SERVICE_THRESHOLDS={"Amazon EC2": 500.0, "Amazon RDS": 200.0, "Amazon S3": 100.0}

# Resource Filtering
RESOURCE_ARNS=
EXCLUDED_ARNS=arn:aws:ec2:us-east-1:123456789012:instance/i-test123
TAG_FILTERS={"Environment": "production", "Project": "myapp"}

# Advanced Monitoring
ENABLE_ANOMALY_DETECTION=true
ANOMALY_SENSITIVITY=medium
ENABLE_COST_FORECASTING=true
FORECAST_DAYS=30

# Alert Configuration
ALERT_CRITICAL_PERCENT=100.0
ALERT_WARNING_PERCENT=80.0
ALERT_INFO_PERCENT=50.0
ENABLE_DETAILED_BREAKDOWN=true
MAX_SERVICES_IN_ALERT=10

# Scheduling
CHECK_INTERVAL_HOURS=6
ENABLE_WEEKEND_MONITORING=true
TIMEZONE=UTC
```

### 5. Test and Run

```bash
# Test  connections
python main.py --test

# Run  cost check
python main.py --check-once

# Send  summary
python main.py --summary

# Start  monitoring
python main.py --daemon
```

##  Usage Examples

### Basic Usage
```bash
# Run once and exit
python main.py

# Test  connections
python main.py --test

# Run in background (daemon mode)
python main.py --daemon
```

### Service-Specific Configuration

#### Monitor Only Specific Services
```bash
# Monitor only compute and database services
ENABLED_SERVICES="Amazon EC2,Amazon RDS,Amazon ECS" python main.py --daemon

# Exclude expensive services
DISABLED_SERVICES="Amazon SageMaker,Amazon EMR,Amazon Redshift" python main.py --daemon
```

#### Service-Specific Thresholds
```bash
# Set different thresholds for each service
SERVICE_THRESHOLDS='{"Amazon EC2": 500.0, "Amazon RDS": 200.0, "Amazon S3": 50.0}' python main.py --daemon
```

### Resource-Level Filtering

#### Monitor Specific Resources
```bash
# Monitor only specific EC2 instances
RESOURCE_ARNS="arn:aws:ec2:us-east-1:123456789012:instance/i-prod1,arn:aws:ec2:us-east-1:123456789012:instance/i-prod2" python main.py --daemon

# Exclude test resources
EXCLUDED_ARNS="arn:aws:ec2:us-east-1:123456789012:instance/i-test*" python main.py --daemon
```

#### Tag-Based Filtering
```bash
# Monitor only production resources
TAG_FILTERS='{"Environment": "production"}' python main.py --daemon

# Monitor specific project resources
TAG_FILTERS='{"Project": "myapp", "Environment": "prod"}' python main.py --daemon
```

### Advanced Configuration Files

#### Using  YAML Config
Create `production.yaml`:
```yaml
project_name: "Production Environment"
cost_threshold: 1000.0
enabled_services: "Amazon EC2,Amazon RDS,Amazon S3,AWS Lambda"
service_thresholds:
  "Amazon EC2": 500.0
  "Amazon RDS": 200.0
  "Amazon S3": 100.0
  "AWS Lambda": 50.0
tag_filters:
  Environment: "production"
check_interval_hours: 2
enable_anomaly_detection: true
anomaly_sensitivity: "high"
```

Run with config file:
```bash
python main.py --config production.yaml --daemon
```

#### Multiple Environment Setup
```bash
# Production environment
python main.py --config configs/production.yaml --daemon

# Staging environment  
python main.py --config configs/staging.yaml --daemon

# Development environment
python main.py --config configs/development.yaml --daemon
```

## 🔧  Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | - | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | - | ✅ |
| `AWS_DEFAULT_REGION` | AWS Region | `us-east-1` | ❌ |
| `SLACK_BOT_TOKEN` | Slack Bot Token | - | ✅ |
| `SLACK_CHANNEL` | Slack Channel | `#alerts` | ❌ |
| `COST_THRESHOLD` | Global cost alert threshold | `100.0` | ❌ |
| `MONITORING_PERIOD_DAYS` | Days to analyze | `7` | ❌ |
| `CURRENCY` | Currency code | `USD` | ❌ |
| `PROJECT_NAME` | Project identifier | `AWS Project` | ❌ |
| `NOTIFICATION_FREQUENCY` | Alert frequency | `daily` | ❌ |

### Service-Specific Controls

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLED_SERVICES` | Services to monitor | `all` |
| `DISABLED_SERVICES` | Services to exclude | `` |
| `SERVICE_THRESHOLDS` | Service-specific thresholds | `{}` |

### Resource Filtering

| Variable | Description | Default |
|----------|-------------|---------|
| `RESOURCE_ARNS` | Specific ARNs to monitor | `` |
| `EXCLUDED_ARNS` | ARNs to exclude | `` |
| `TAG_FILTERS` | Tag-based filtering | `{}` |

### Advanced Monitoring

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_ANOMALY_DETECTION` | Enable anomaly detection | `true` |
| `ANOMALY_SENSITIVITY` | Detection sensitivity | `medium` |
| `ENABLE_COST_FORECASTING` | Enable cost forecasting | `true` |
| `FORECAST_DAYS` | Days to forecast | `30` |

### Alert Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ALERT_CRITICAL_PERCENT` | Critical alert threshold | `100.0` |
| `ALERT_WARNING_PERCENT` | Warning alert threshold | `80.0` |
| `ALERT_INFO_PERCENT` | Info alert threshold | `50.0` |
| `ENABLE_DETAILED_BREAKDOWN` | Enable detailed alerts | `true` |
| `MAX_SERVICES_IN_ALERT` | Max services in alert | `10` |

### Scheduling

| Variable | Description | Default |
|----------|-------------|---------|
| `CHECK_INTERVAL_HOURS` | Check interval | `6` |
| `ENABLE_WEEKEND_MONITORING` | Weekend monitoring | `true` |
| `TIMEZONE` | Timezone | `UTC` |

##  Alert Types

### 🚨 Critical Alerts
- Cost exceeds 100% of threshold
- Service-specific threshold exceeded
- Severe cost anomalies detected
- Resource-level cost spikes

### ⚠️ Warning Alerts  
- Cost exceeds 80% of threshold
- Service approaching threshold
- Moderate cost increases detected
- Anomaly detection warnings

### ℹ️ Info Alerts
- Regular cost summaries
- Service-specific reports
- Resource utilization updates
- Cost forecasting insights

### ✅ Normal Alerts
- Costs within normal range
- Positive cost trends
- Optimization opportunities

## 🎯  Slack Notifications

The bot sends rich, actionable Slack messages including:

- **Service-Specific Breakdowns**: Individual service costs and thresholds
- **Resource-Level Details**: Top expensive resources with costs
- **Anomaly Alerts**: Detected unusual spending patterns
- **Cost Forecasting**: Predicted future costs and trends
- **Service Recommendations**: Specific optimization suggestions per service
- **Resource Utilization**: Current resource usage statistics
- **Trend Analysis**: Cost trends with visual indicators

##  Scheduling Options

### Flexible Intervals
```bash
# Check every 2 hours
CHECK_INTERVAL_HOURS=2 python main.py --daemon

# Check every 12 hours
CHECK_INTERVAL_HOURS=12 python main.py --daemon

# Check every hour (high-frequency monitoring)
CHECK_INTERVAL_HOURS=1 python main.py --daemon
```

### Weekend Controls
```bash
# Disable weekend monitoring
ENABLE_WEEKEND_MONITORING=false python main.py --daemon

# Enable weekend monitoring (default)
ENABLE_WEEKEND_MONITORING=true python main.py --daemon
```

### Cron Integration
```bash
# Add to crontab for custom scheduling
0 */2 * * * /usr/bin/python3 /path/to/main.py --check-once  # Every 2 hours
0 8 * * 1 /usr/bin/python3 /path/to/main.py --summary      # Weekly summary
0 9 1 * * /usr/bin/python3 /path/to/main.py --summary      # Monthly summary
```

## 🐳  Docker Deployment

### Docker Compose with  Config
```yaml
version: '3.8'

services:
  aws-cost-monitor:
    build: .
    container_name: aws-cost-monitor
    restart: unless-stopped
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SLACK_CHANNEL=${SLACK_CHANNEL:-#aws-alerts}
      - COST_THRESHOLD=${COST_THRESHOLD:-100.0}
      - ENABLED_SERVICES=${ENABLED_SERVICES:-all}
      - DISABLED_SERVICES=${DISABLED_SERVICES:-}
      - SERVICE_THRESHOLDS=${SERVICE_THRESHOLDS:-{}}
      - ENABLE_ANOMALY_DETECTION=${ENABLE_ANOMALY_DETECTION:-true}
      - ANOMALY_SENSITIVITY=${ANOMALY_SENSITIVITY:-medium}
      - CHECK_INTERVAL_HOURS=${CHECK_INTERVAL_HOURS:-6}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    command: ["python", "main.py", "--daemon"]
```

### Multi-Environment Docker Setup
```bash
# Production
docker-compose -f docker-compose.prod.yml up -d

# Staging
docker-compose -f docker-compose.staging.yml up -d

# Development
docker-compose -f docker-compose.dev.yml up -d
```

##  Development

### Project Structure
```
aws-cost-monitoring-bot/
├── main.py                     # Entry point
├── cost_monitor_bot.py         #  bot logic
├── aws_cost_monitor.py         #  AWS integration
├── slack_notifier.py           #  Slack messaging
├── config.py                   #  configuration
├── requirements.txt            # Dependencies
├── env..example        #  environment template
├── config..example.yaml #  YAML config
├── README.md                   # Documentation
└── SETUP_GUIDE.md             # Setup instructions
```

### Adding New Features

1. **Custom Service Monitoring**: Extend `Config.get_enabled_services_list()`
2. **New Alert Types**: Modify `SlackNotifier.send_service_specific_alert()`
3. **Additional Resource Types**: Extend `AWSCostMonitor.get_resource_utilization()`
4. **Custom Scheduling**: Update `CostMonitorBot.schedule_monitoring()`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

**Service-Specific Configuration Errors**
```bash
# Verify service names
python -c "from config import Config; c = Config(); print(c.get_enabled_services_list())"

# Test service filtering
python -c "from config import Config; c = Config(); print(c.is_service_enabled('Amazon EC2'))"
```

**Resource Filtering Issues**
```bash
# Test ARN filtering
python -c "from config import Config; c = Config(); print(c.should_monitor_resource('arn:aws:ec2:us-east-1:123456789012:instance/i-test123'))"

# Test tag filtering
python -c "from config import Config; c = Config(); print(c.get_cost_explorer_filters())"
```

** Debug Mode**
```bash
# Enable debug logging
DEBUG_MODE=true LOG_LEVEL=DEBUG python main.py --test
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

- **Email**: [ronitsachdev007@gmail.com]
---
