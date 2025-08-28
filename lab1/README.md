# Lab 1: The Satellite Data Deluge Automation

## Overview

This solution demonstrates how to use `vastpy` to automate storage provisioning, quota management, and monitoring for Orbital Dynamics' satellite data processing pipeline. We'll build a system that automatically scales storage resources and provides proactive alerts before Jordan's processing pipeline hits quota limits.

## Files

- **`lab1_solution.py`** - Main storage automation script
- **`lab1_config.py`** - Lab-specific configuration loader (inherits from centralized config)
- **`pipeline_integration.py`** - Integration script for Jordan's processing pipeline
- **`monitoring_dashboard.py`** - Real-time monitoring dashboard
- **`test_solution.py`** - Unit tests for the solution
- **`requirements.txt`** - Python dependencies

**Note:** Configuration files are centralized in the root directory. Copy `../config.yaml.example` to `../config.yaml` and `../secrets.yaml.example` to `../secrets.yaml`, then edit them with your settings.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Solution

```bash
# Copy and edit configuration files
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Edit config.yaml to match your environment
# Edit secrets.yaml with your actual credentials
```

### 3. Run the Solution

```bash
# DRY RUN MODE (default - safe, no changes made)
python lab1_solution.py

# PRODUCTION MODE (actual changes will be made)
python lab1_solution.py --pushtoprod

# Setup only (create views, then exit)
python lab1_solution.py --setup-only

# Monitor only (skip setup, start monitoring)
python lab1_solution.py --monitor-only

# In another terminal, run the dashboard
python monitoring_dashboard.py

# Test pipeline integration
python pipeline_integration.py 5.0  # Check for 5TB availability
```

## Configuration

### Main Configuration (`config.yaml`)

The main configuration file contains all non-sensitive settings:

```yaml
# VAST Connection Settings
vast:
  user: admin
  password: ""  # Set via environment variable VAST_PASSWORD
  address: "localhost"
  token: ""  # Optional for Vast 5.3+

# Storage Paths
storage:
  raw_data_path: "/cosmos7/raw"
  processed_data_path: "/cosmos7/processed"
  temp_data_path: "/cosmos7/temp"

# Quota Management
quotas:
  warning_threshold: 75  # Alert at 75% utilization
  critical_threshold: 85  # Auto-provision at 85% utilization
  auto_expand_size_tb: 10  # Expand by 10TB when needed
```

### Secrets Configuration (`secrets.yaml`)

The secrets file contains sensitive data and should not be committed to version control:

```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"
vast_token: "your_vast_api_token_here"

# Alerting Secrets
slack_webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
pagerduty_api_key: "your_pagerduty_api_key_here"
```

## Features

### ✅ Automated Storage Provisioning
- Automatically expands quotas when utilization exceeds 85%
- Configurable expansion size (default: 10TB)
- Supports multiple storage views (raw, processed, temp)

### ✅ Real-time Monitoring
- Continuous monitoring with configurable intervals
- Status levels: Normal (🟢) vs Needs Expansion (🔴)
- Simple 2-tier system for easy understanding

### ✅ Pipeline Integration
- Pre-flight storage availability checks
- Automatic space requirement validation
- Integration with Jordan's processing pipeline

### ✅ Alerting System
- Simple alerting for storage expansion needs
- Console-based notifications (easy to understand)
- Ready for integration with email, Slack, etc.

### ✅ Configuration Management
- YAML-based configuration
- Environment variable overrides
- Separate secrets management
- Validation and error handling

### ✅ Safety System
- **Dual-Mode Operation**: Dry-run (default) vs Production mode
- **Comprehensive Safety Checks**: Views, permissions, monitoring, quotas
- **Production Confirmation**: Requires explicit confirmation for actual changes
- **Audit Logging**: All operations logged with mode information

## Safety System

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
- ✅ **Quota Limits** - Expansion requests within 10TB limit (configurable)

## Usage Examples

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

### Pipeline Integration

```python
# In Jordan's processing script
from pipeline_integration import PipelineStorageChecker
from lab1_config import Lab1ConfigLoader

def run_processing_pipeline(processing_type: str = "default"):
    # Load configuration
    config = ConfigLoader()
    
    # Get space requirement for this processing type
    space_requirements = config.get('pipeline.space_requirements', {})
    required_space = space_requirements.get(processing_type, space_requirements.get('default', 1.0))
    
    # Check storage before starting
    checker = PipelineStorageChecker()
    
    if not checker.check_storage_availability(required_space):
        print(f"ERROR: Insufficient storage space for {processing_type} processing")
        return False
    
    # Proceed with processing
    print(f"Starting {processing_type} processing pipeline...")
    # ... processing logic ...
    
    return True

# Usage examples:
run_processing_pipeline("cosmos7_processing")  # Uses 5.0 TB requirement
run_processing_pipeline("mars_rover_processing")  # Uses 3.0 TB requirement
run_processing_pipeline()  # Uses default 1.0 TB requirement
```

### Testing

```bash
# Run unit tests
python test_solution.py
```

## Architecture

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

## Success Criteria

1. **Zero Manual Intervention** - Storage provisioning happens automatically without human intervention
2. **Predictive Scaling** - System anticipates storage needs based on data ingestion patterns
3. **Pipeline Resilience** - Jordan's processing pipeline never fails due to storage constraints
4. **Real-time Visibility** - Maya's team has complete visibility into storage utilization and provisioning status
5. **NASA SLA Compliance** - Meet all data processing deadlines without storage-related delays

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Ensure `config.yaml` exists in the current directory
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

## Next Steps

1. **Integrate with Alerting Systems** - Connect to email, Slack, or PagerDuty for notifications
2. **Add Machine Learning** - Implement predictive scaling based on historical usage patterns
3. **Expand Monitoring** - Add monitoring for other resources (CPU, memory, network)
4. **Create Web Dashboard** - Build a web-based dashboard for better visualization
5. **Add Backup and Recovery** - Implement automated backup and disaster recovery procedures

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify configuration settings
3. Test VAST connectivity manually
4. Review the test cases in `test_solution.py` 