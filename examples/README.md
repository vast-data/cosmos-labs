# VAST SDK Examples

This folder contains 8 simple examples demonstrating key vastpy concepts, which are then built upon in the labs.

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
- ✅ Individual node status and roles (CNodes and DNodes)
- ✅ Overall system status and connectivity
- ✅ Clean, focused health monitoring without unnecessary alerts

**Run:** `python 04_monitor_health.py`

### 5. [Show Snapshots](05_show_snapshots.py)
**Purpose:** Display snapshot information and management
- ✅ Shows oldest and latest snapshots
- ✅ Displays snapshot sizes and creation times
- ✅ Provides summary statistics
- ✅ Shows all snapshots in table format (if ≤10 snapshots)

**Run:** `python 05_show_snapshots.py`

### 6. [Chargeback Report](06_chargeback_report.py)
**Purpose:** Generate cost analysis for storage usage
- ✅ Shows top 5 most expensive root views (e.g., /jonas, /benny)
- ✅ Calculates costs at $42/TB/month for views with enabled quotas
- ✅ Displays storage usage and monthly costs per root view
- ✅ Provides summary statistics and cost breakdown

**Run:** `python 06_chargeback_report.py`

### 7. [Orphaned Data Discovery](07_orphaned_data_discovery.py)
**Purpose:** Efficiently find orphaned data using catalog-based approach
- ✅ Gets all directory paths from VAST using vastdb catalog
- ✅ Compares against current view paths to find orphaned directories
- ✅ Provides complete coverage of all orphaned data (not just from deleted views)
- ✅ Much more efficient than event-based approaches
- ✅ Skips VAST internal directories and shows progress indicators
- ✅ Groups results by top-level folders with detailed breakdown

**Run:** `python 07_orphaned_data_discovery.py`

### 8. [Show User Quotas](08_show_user_quotas.py)
**Purpose:** Display detailed user quota information with nice formatting
- ✅ Shows comprehensive quota summary with capacity and inode usage
- ✅ Displays individual user quotas in a formatted table
- ✅ Human-readable sizes (KB, MB, GB, TB) and usage percentages
- ✅ Shows quota status, alarms, and last update information
- ✅ Clean, professional output perfect for monitoring and reporting
- ✅ Command-line support for any quota ID
- ✅ --all option to show summary list of all quotas with color-coded status

**Run:** 
- `python 08_show_user_quotas.py --all` (show all quotas summary)
- `python 08_show_user_quotas.py 114` (show specific quota details)
- `python 08_show_user_quotas.py 114 --json` (raw JSON output)

### 9. [VAST Storage and Database Inventory](09_list_available_buckets.py)
**Purpose:** Analyze your VAST system to show storage inventory and database statistics
- ✅ Shows all VAST views categorized by protocol (S3, NFS, SMB, BLOCK, DATABASE)
- ✅ Displays summary statistics: total views, counts by protocol type
- ✅ Analyzes database-enabled views and shows actual data statistics
- ✅ Counts tables and rows in your accessible databases
- ✅ Provides helpful error messages for common connection issues
- ✅ Uses native VAST tools (vastpy, vastdb) for accurate analysis

**Run:** `python 09_list_available_buckets.py`

## ⚠️ Safety Notes

- **All examples are safe by default** - No destructive operations
- **All examples are read-only** - No changes made to VAST systems
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
