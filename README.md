# AWS Cost Monitoring Bot 🤖💰

A comprehensive, reusable AWS cost monitoring solution that tracks your AWS spending and sends intelligent alerts to Slack. Perfect for keeping your AWS costs under control across multiple projects.

## ✨ Features

- **Real-time Cost Monitoring**: Track AWS costs using AWS Cost Explorer API
- **Intelligent Alerts**: Smart notifications based on thresholds and anomalies
- **Slack Integration**: Rich, formatted notifications with cost breakdowns
- **Multi-Project Support**: Easily reusable across different AWS projects
- **Anomaly Detection**: Automatically detect unusual spending patterns
- **Flexible Scheduling**: Daily, weekly, or monthly monitoring options
- **Service Breakdown**: Detailed cost analysis by AWS service
- **Trend Analysis**: Track cost trends over time
- **Easy Configuration**: Environment variables or config files

## 🚀 Quick Start

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
                   "ce:GetCostForecast"
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

### 4. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_DEFAULT_REGION=us-east-1

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_CHANNEL=#aws-alerts

# Cost Monitoring Settings
COST_THRESHOLD=500.0
MONITORING_PERIOD_DAYS=30
CURRENCY=USD

# Project Settings
PROJECT_NAME=My Production Environment
NOTIFICATION_FREQUENCY=daily
```

### 5. Test and Run

```bash
# Test connections
python main.py --test

# Run a single check
python main.py --check-once

# Send cost summary
python main.py --summary

# Start continuous monitoring
python main.py --daemon
```

## 📖 Usage Examples

### Basic Usage
```bash
# Run once and exit
python main.py

# Test all connections
python main.py --test

# Run in background (daemon mode)
python main.py --daemon
```

### Advanced Configuration

#### Using Config Files

Create `config.yaml`:
```yaml
project_name: "Production Web App"
cost_threshold: 1000.0
monitoring_period_days: 7
notification_frequency: "daily"
slack_channel: "#production-alerts"
currency: "USD"
```

Run with config file:
```bash
python main.py --config config.yaml --daemon
```

#### Multiple Projects

For different projects, create separate config files:

```bash
# E-commerce project
python main.py --config configs/ecommerce.yaml --daemon

# Analytics project  
python main.py --config configs/analytics.yaml --daemon
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | - | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | - | ✅ |
| `AWS_DEFAULT_REGION` | AWS Region | `us-east-1` | ❌ |
| `SLACK_BOT_TOKEN` | Slack Bot Token | - | ✅ |
| `SLACK_CHANNEL` | Slack Channel | `#alerts` | ❌ |
| `COST_THRESHOLD` | Cost alert threshold | `100.0` | ❌ |
| `MONITORING_PERIOD_DAYS` | Days to analyze | `7` | ❌ |
| `CURRENCY` | Currency code | `USD` | ❌ |
| `PROJECT_NAME` | Project identifier | `AWS Project` | ❌ |
| `NOTIFICATION_FREQUENCY` | Alert frequency | `daily` | ❌ |

### Notification Frequencies

- **`daily`**: Checks at 9 AM and 6 PM, plus 6-hourly threshold checks
- **`weekly`**: Checks every Monday morning
- **`monthly`**: Checks once per month
- **Custom**: Use config files for custom scheduling

## 📊 Alert Types

### 🚨 Critical Alerts
- Cost exceeds 100% of threshold
- Severe cost anomalies detected

### ⚠️ Warning Alerts  
- Cost exceeds 80% of threshold
- Moderate cost increases detected

### ℹ️ Info Alerts
- Regular cost summaries
- Normal cost reports

## 🎯 Example Slack Notifications

The bot sends rich, formatted Slack messages including:

- **Current vs. threshold costs**
- **Top services by cost**
- **Daily/weekly trends**
- **Actionable recommendations**
- **Anomaly alerts**

## 🔄 Scheduling Options

### Cron Integration
```bash
# Add to crontab for hourly checks
0 * * * * /usr/bin/python3 /path/to/main.py --check-once

# Daily summary at 8 AM
0 8 * * * /usr/bin/python3 /path/to/main.py --summary
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "--daemon"]
```

### Systemd Service
```ini
[Unit]
Description=AWS Cost Monitor
After=network.target

[Service]
Type=simple
User=aws-monitor
WorkingDirectory=/opt/aws-cost-monitor
ExecStart=/usr/bin/python3 main.py --daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🛠️ Development

### Project Structure
```
aws-cost-monitoring-bot/
├── main.py                 # Entry point
├── cost_monitor_bot.py     # Main bot logic
├── aws_cost_monitor.py     # AWS Cost Explorer integration
├── slack_notifier.py       # Slack messaging
├── config.py              # Configuration management
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md             # Documentation
```

### Adding New Features

1. **Custom Metrics**: Extend `AWSCostMonitor` class
2. **New Alert Types**: Modify `SlackNotifier` class  
3. **Additional Scheduling**: Update `CostMonitorBot.schedule_monitoring()`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**AWS Permission Denied**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Cost Explorer permissions
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-02 --granularity DAILY --metrics BlendedCost
```

**Slack Bot Not Responding**
- Verify bot token starts with `xoxb-`
- Ensure bot is invited to the channel
- Check bot permissions include `chat:write`

**No Cost Data**
- AWS Cost Explorer requires 24-48 hours for data availability
- Ensure your AWS account has actual usage/costs

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

- 📧 **Email**: [your-email@domain.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📖 **Documentation**: [Project Wiki](https://github.com/your-repo/wiki)

---

**Made with ❤️ for better AWS cost management** 