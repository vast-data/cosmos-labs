# Lab 1: Storage Monitoring & Auto-Expansion

> 📖 **Hey, remember to read the [story](STORY.md) to understand what we're doing and why!** This will help you understand the business context and challenges the Orbital Dynamics team is facing.

## 🎯 Overview

This solution demonstrates how to use `vastpy` to monitor existing storage infrastructure and automatically expand quotas when needed. We'll build a system that monitors storage utilization across multiple views and provides proactive quota expansion with comprehensive safety checks to prevent storage crises.

**Key Features:**
- Automated storage provisioning and quota management
- Real-time monitoring with configurable intervals
- Pipeline integration with safety checks
- Centralized configuration management

## 🏗️ Solution Structure

All solution files are located in the `lab1/` folder:

```
lab1/
├── lab1_solution.py          # Main storage automation script
├── lab1_config.py            # Lab-specific configuration loader (inherits from centralized config)
├── monitoring_dashboard.py   # Real-time monitoring dashboard
└── requirements.txt          # Python dependencies
```

**Note:** Configuration files (`config.yaml` and `secrets.yaml`) are now centralized in the root directory for all labs.

## 🚀 Quick Start

### 1. Navigate to Lab 1 Directory
```bash
cd lab1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Test Data (Optional)
```bash
# Generate test data for Lab 1 (storage testing)
python ../scripts/generate_test_data.py --lab-type lab1 --raw-files 20 --raw-size-mb 500

# Generate large files to test auto-expansion
python ../scripts/generate_test_data.py --lab-type lab1 --raw-files 50 --raw-size-mb 1000
```

### 4. Configure the Solution
```bash
# Copy the example configuration files (if you haven't already)
cp ../config.yaml.example ../config.yaml
cp ../secrets.yaml.example ../secrets.yaml

# Edit configuration files in the root directory
# ../config.yaml - Main configuration for all labs
# ../secrets.yaml - Sensitive data (passwords, API keys)
```

### 5. Run the Solution
```bash
# DRY RUN MODE (default - safe, no changes made)
python lab1_solution.py

# PRODUCTION MODE (actual changes will be made)
python lab1_solution.py --pushtoprod

# Setup only (check if views exist, then exit)
python lab1_solution.py --setup-only

# Monitor only (skip setup, start monitoring)
python lab1_solution.py --monitor-only

# In another terminal, run the dashboard
python monitoring_dashboard.py
```

## 🔧 Configuration

### Main Configuration (`../config.yaml` - copy from `../config.yaml.example`)

The main configuration file contains all non-sensitive settings:

```yaml
# VAST Connection Settings
vast:
  user: admin
  address: "your-vast-cluster.example.com"

# Data directories
data:
  directories:
    - "/your-tenant/raw"      # Raw data storage
    - "/your-tenant/processed" # Processed data storage

# Lab 1: Storage Automation Settings
lab1:
  storage:
    auto_provision_threshold: 75  # Percentage at which to auto-provision
    expansion_factor: 1.5         # How much to expand by
    max_expansion_gb: 10000       # Maximum expansion in GB
  
  monitoring:
    alert_threshold: 80           # Percentage at which to alert
    critical_threshold: 90        # Percentage at which to take immediate action

# Monitoring settings
monitoring:
  enabled: true
  interval_seconds: 300  # 5 minutes between monitoring cycles
```

### Secrets Configuration (`../secrets.yaml` - copy from `../secrets.yaml.example`)

The secrets file contains sensitive data and should not be committed to version control:

```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"
```

## ✨ Key Features

### ✅ Automated Storage Provisioning
- Automatically expands quotas when utilization exceeds configured thresholds
- Configurable expansion size based on data ingestion patterns
- Supports multiple storage views (raw, processed, temp)

### ✅ Real-time Monitoring
- Continuous monitoring with configurable intervals
- Status levels: Normal (🟢), Warning (🟡), Critical (🔴)
- Real-time dashboard with utilization metrics

### ✅ Pipeline Integration
- Pre-flight storage availability checks
- Automatic space requirement validation
- Integration with Jordan's processing pipeline

### ✅ Configuration Management
- Centralized YAML-based configuration with environment variable overrides
- Separate secrets management for security
- Strict validation to prevent dangerous default values

### ✅ Alerting System
- Simple alerting for storage expansion needs
- Console-based notifications (easy to understand)
- Ready for integration with email, Slack, etc.

## 🛡️ Safety System

### **Dual-Mode Operation**

The system operates in two modes to ensure production safety:

#### **Dry Run Mode (Default)**
- ✅ **Always Safe** - No actual changes made to your VAST system
- ✅ **Safety Checks** - All operations validated before execution
- ✅ **Preview Mode** - Shows exactly what would happen
- ✅ **Testing Friendly** - Perfect for validating configuration

#### **Production Mode**
- 🚨 **Requires Flag** - Must use `--pushtoprod` flag
- 🚨 **Confirmation Required** - User must type 'yes' to confirm
- 🚨 **Actual Changes** - Makes real changes to your VAST system
- 🚨 **Audit Trail** - All operations logged for compliance

### **Safety Checks**

Before any operation, the system validates these essential safety requirements:
- ✅ **View Existence** - Target views must exist and be accessible
- ✅ **Basic Permissions** - Proper access rights verified  
- ✅ **Storage Availability** - Sufficient space for expansion
- ✅ **Quota Limits** - Expansion requests within configured limits

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   COSMOS-7      │    │   Raw Data      │    │  Processing     │
│   Telescope     │───▶│   Views         │───▶│   Pipeline      │
│   Feed          │    │   (vastpy)      │    │   (Jordan)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │  Processed      │    │   Automation    │
│   & Alerting    │◀───│  Data Views     │◀───│   Scripts       │
│   (vastpy)      │    │  (vastpy)       │    │   (vastpy)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔍 Usage Examples

### Basic Monitoring
```bash
# Start automated monitoring (DRY RUN - safe)
python lab1_solution.py
```

### Dashboard View
```bash
# View real-time dashboard
python monitoring_dashboard.py
```

## 🧪 Safety Checks

The solution includes comprehensive monitoring and safety checks built into the main functionality.

## 🎯 Success Criteria

1. **Zero Manual Intervention** - Storage monitoring and quota expansion happens automatically without human intervention
2. **Predictive Scaling** - System anticipates storage needs based on data ingestion patterns
3. **Pipeline Resilience** - Jordan's processing pipeline never fails due to storage constraints
4. **Real-time Visibility** - Maya's team has complete visibility into storage utilization and quota expansion status
5. **NASA SLA Compliance** - Meet all data processing deadlines without storage-related delays

## 🚨 Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Ensure `config.yaml` exists in the root directory
   - Check file permissions

2. **VAST Connection Failed**
   - Verify VAST cluster is accessible
   - Check credentials in `secrets.yaml` or environment variables
   - Ensure network connectivity

3. **Permission Denied**
   - Verify user has appropriate permissions on VAST cluster
   - Check view creation and modification permissions

### Logs

The solution provides detailed logging at INFO level. Check the console output for:
- Storage utilization updates
- Quota expansion events
- Alert notifications
- Error messages

## 🔮 Next Steps

1. **Integrate with Alerting Systems** - Connect to email, Slack, or PagerDuty for notifications
2. **Add Machine Learning** - Implement predictive scaling based on historical usage patterns
3. **Expand Monitoring** - Add monitoring for other resources (CPU, memory, network)
4. **Create Web Dashboard** - Build a web-based dashboard for better visualization
5. **Add Backup and Recovery** - Implement automated backup and disaster recovery procedures

## 🆘 Support

For issues or questions:
1. Check the logs for error messages
2. Verify configuration settings
3. Test VAST connectivity manually
4. Check the monitoring dashboard for system status