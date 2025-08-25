# Lab 1 Solution: The Satellite Data Infrastructure Planning

## Overview

This solution demonstrates how to use `vastpy` to automate storage provisioning, quota management, and monitoring for Orbital Dynamics' satellite data processing pipeline. The complete implementation is organized in the `lab1/` folder.

## Solution Structure

All solution files are located in the `lab1/` folder:

```
lab1/
├── lab1_solution.py          # Main storage automation script
├── config_loader.py          # Lab-specific configuration loader (inherits from centralized config)
├── pipeline_integration.py   # Jordan's pipeline integration
├── monitoring_dashboard.py   # Real-time monitoring dashboard
├── test_solution.py          # Unit tests
└── requirements.txt          # Python dependencies
```

**Note:** Configuration files (`config.yaml` and `secrets.yaml`) are now centralized in the root directory for all labs.

## Quick Start

### 1. Navigate to Lab 1 Directory
```bash
cd lab1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Solution
```bash
# Copy the example configuration files (if you haven't already)
cp ../config.yaml.example ../config.yaml
cp ../secrets.yaml.example ../secrets.yaml

# Edit configuration files in the root directory
# ../config.yaml - Main configuration for all labs
# ../secrets.yaml - Sensitive data (passwords, API keys)
```

### 4. Run the Solution
```bash
# Start automated monitoring
python lab1_solution.py

# In another terminal, view the dashboard
python monitoring_dashboard.py

# Test pipeline integration
python pipeline_integration.py 5.0
```

## Key Features

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

## Configuration

### Main Configuration (`../config.yaml` - copy from `../config.yaml.example`)
```yaml
# Lab 1 specific settings
lab1:
  storage:
    auto_provision_threshold: 75  # Percentage at which to auto-provision
    expansion_factor: 1.5         # How much to expand by
    max_expansion_gb: 10000       # Maximum expansion in GB
  
  monitoring:
    alert_threshold: 80           # Percentage at which to alert
    critical_threshold: 90        # Percentage at which to take immediate action

# VAST Connection Settings
vast:
  user: admin
  address: "localhost"

# Data directories
data:
  directories:
    - "/cosmos7/raw"
    - "/cosmos7/processed"
    - "/cosmos7/temp"

# Monitoring settings
monitoring:
  enabled: true
  interval_seconds: 300  # 5 minutes between monitoring cycles
```

### Secrets Configuration (`../secrets.yaml` - copy from `../secrets.yaml.example`)
```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"

# Note: vastpy 0.3.17 only supports basic authentication
# vast_token: ""  # Not supported in vastpy 0.3.17
# vast_tenant_name: ""  # Not supported in vastpy 0.3.17
# vast_api_version: "v1"  # Not supported in vastpy 0.3.17
```

## Implementation Details

### Storage Automation Logic
The solution implements proactive storage management by:
1. **Monitoring Usage Patterns** - Tracks data ingestion rates and storage utilization
2. **Predictive Scaling** - Automatically provisions additional storage before hitting limits
3. **Pipeline Integration** - Ensures Jordan's processing pipeline has guaranteed access to resources
4. **Real-time Alerts** - Provides early warning when approaching capacity thresholds

### VAST Integration
Uses `vastpy` to:
- Create and manage storage views for different data types
- Monitor storage utilization in real-time
- Automatically expand quotas when needed
- Integrate with existing monitoring and alerting systems

## Testing

Run the comprehensive test suite to verify all functionality:

```bash
python test_solution.py
```

## Success Metrics

- **Proactive Infrastructure** - Storage provisioning happens automatically before it's needed
- **Predictive Scaling** - System anticipates storage needs based on data ingestion patterns
- **Pipeline Reliability** - Jordan's processing pipeline has guaranteed access to storage resources
- **Real-time Visibility** - Complete visibility into storage utilization and provisioning status
- **NASA SLA Readiness** - Infrastructure ready to meet all data processing deadlines from day one
