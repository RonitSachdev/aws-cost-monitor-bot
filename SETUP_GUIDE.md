# 🚀 Quick Setup Guide

## ✅ Installation Complete!

Your AWS Cost Monitoring Bot is ready to use! All tests passed successfully.

## 📋 Next Steps

### 1. AWS Setup (5 minutes)

1. **Go to AWS IAM Console**
   - Navigate to https://console.aws.amazon.com/iam/
   - Create a new user for the bot

2. **Set Permissions**
   - Attach policy: `AWSBillingReadOnlyAccess`
   - Or create custom policy with these permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "ce:GetCostAndUsage",
                   "ce:GetDimensionValues",
                   "ce:GetCostForecast"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

3. **Create Access Keys**
   - Go to "Security credentials" tab
   - Create new access key
   - Save the Access Key ID and Secret Access Key

### 2. Slack Setup (3 minutes)

1. **Create Slack App**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name it "AWS Cost Monitor"

2. **Add Permissions**
   - Go to "OAuth & Permissions"
   - Add Bot Token Scopes:
     - `chat:write`
     - `chat:write.public`

3. **Install to Workspace**
   - Click "Install to Workspace"
   - Copy the Bot User OAuth Token (starts with `xoxb-`)

4. **Invite to Channel**
   - In Slack: `/invite @AWS Cost Monitor` in your desired channel

### 3. Configure Bot

Edit your `.env` file:
```bash
# Replace with your actual values
AWS_ACCESS_KEY_ID=your_real_access_key
AWS_SECRET_ACCESS_KEY=your_real_secret_key
SLACK_BOT_TOKEN=xoxb-your-real-bot-token
SLACK_CHANNEL=#your-channel
COST_THRESHOLD=500.0
PROJECT_NAME=My Production Project
```

### 4. Test & Run

```bash
# Test connections
python main.py --test

# Run once
python main.py --check-once

# Start monitoring
python main.py --daemon
```

## 🎯 You're Done!

Your bot will now:
- 🔍 Monitor AWS costs every 6 hours
- 📊 Send daily summaries  
- 🚨 Alert when thresholds are exceeded
- 📈 Detect cost anomalies
- 💡 Provide optimization recommendations

## 🔧 For Multiple Projects

Create separate config files:
```bash
# Project 1
python main.py --config production.yaml --daemon

# Project 2  
python main.py --config staging.yaml --daemon
```

## 🆘 Need Help?

- Check the logs: `cost_monitor.log`
- All modules tested: ✅
- Error handling working: ✅
- Ready for production: ✅

**Happy cost monitoring!** 🎉 