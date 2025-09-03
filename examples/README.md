# VAST SDK Examples

This folder contains 7 simple examples demonstrating key vastpy concepts, which are then built upon in the labs.

## 🚀 Quick Start

All examples use the centralized configuration system via `examples_config.py`. Make sure you have:

1. **Configuration files** in the root directory:
   - `config.yaml` (copied from `config.yaml.example`)
   - `secrets.yaml` (copied from `secrets.yaml.example`)

2. **Dependencies installed**:
   ```bash
   pip install vastpy pyyaml
   ```

## 📋 Examples Overview

### 1. [Connect to VAST](01_connect_to_vast.py)
**Purpose:** Basic connection test and system information
- ✅ Establishes connection to VAST Management System
- ✅ Displays system version and cluster information
- ✅ Perfect first example to verify setup

**Run:** `python 01_connect_to_vast.py`

### 2. [List Storage Views](02_list_views.py)
**Purpose:** Show all available storage views and their status
- ✅ Lists all storage views in the system
- ✅ Shows size and utilization for each view
- ✅ Color-coded status (🟢🟡🔴) based on utilization

**Run:** `python 02_list_views.py`

### 3. [Check Quota Status](03_check_quotas.py)
**Purpose:** Display quota information and utilization
- ✅ Shows all quota configurations
- ✅ Displays current usage vs. limits
- ✅ Highlights quotas that need attention

**Run:** `python 03_check_quotas.py`

### 4. [Monitor VAST System Health](04_monitor_health.py)
**Purpose:** Check cluster health, node status, and system performance
- ✅ Cluster health status and capacity
- ✅ Individual node status and roles
- ✅ Performance metrics (IOPS, throughput, latency)
- ✅ Active alerts and system status

**Run:** `python 04_monitor_health.py`

### 5. [Simple Quota Expansion](05_expand_quota.py)
**Purpose:** Demonstrate quota expansion (with safety)
- ✅ Finds quotas that need expansion (>70% utilization)
- ✅ Calculates proposed expansion (adds 1TB)
- ✅ **DRY RUN by default** - no actual changes
- ✅ Production mode available with `--production` flag

**Run:** 
- `python 05_expand_quota.py` (dry run)
- `python 05_expand_quota.py --production` (actual changes)

### 6. [Show Snapshots](06_show_snapshots.py)
**Purpose:** Display snapshot information and management
- ✅ Shows oldest and latest snapshots
- ✅ Displays snapshot sizes and creation times
- ✅ Provides summary statistics
- ✅ Shows all snapshots in table format (if ≤10 snapshots)

**Run:** `python 06_show_snapshots.py`

### 7. [Chargeback Report](07_chargeback_report.py)
**Purpose:** Generate cost analysis for storage usage
- ✅ Shows top 5 most expensive root views (e.g., /jonas, /benny)
- ✅ Calculates costs at $42/TB/month for views with enabled quotas
- ✅ Displays storage usage and monthly costs per root view
- ✅ Provides summary statistics and cost breakdown

**Run:** `python 07_chargeback_report.py`

## ⚠️ Safety Notes

- **All examples are safe by default** - No destructive operations
- **Example 5 has production mode** - Only use with `--production` flag
- **Uses centralized config** - Same credentials as the main labs
- **Educational purpose only** - Not for production use without review

## 🔧 Troubleshooting

### **Connection Issues:**
- Verify `config.yaml` and `secrets.yaml` exist
- Check VAST Management System is accessible
- Ensure credentials are correct

### **Import Errors:**
- Make sure you're running from the examples directory
- Verify vastpy is installed: `pip install vastpy`
- Check Python path includes the root directory

### **No Data:**
- Some examples may show "No data found" if the system is empty
- This is normal for new or test environments
- Examples will still demonstrate the API calls
