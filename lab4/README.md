# Lab 4: The Snapshot Strategy

> 📖 **Hey, remember to read the [story](STORY.md) to understand what we're doing and why!** This will help you understand the business context and challenges the Orbital Dynamics team is facing.

## 🎯 Overview

This Lab 4 solution demonstrates how to implement systematic version control for research datasets using VAST's protection policies and snapshot capabilities. We'll build a comprehensive system that automatically creates snapshots at key milestones and provides researchers with easy tools to browse, search, and restore from previous dataset versions.

**Key Features:**
- Automated protection policies with configurable schedules and retention
- Named snapshot workflows for research milestones
- User-friendly browsing and restoration tools
- Systematic version tracking and change management
- Integration with existing VAST infrastructure

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Research      │    │  Protection      │    │  VAST           │
│   Workflows     │───▶│  Policies        │───▶│  Snapshots      │
│   (Triggers)    │    │  (vastpy)        │    │  (Space-Efficient)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Named         │    │  Snapshot        │    │  Version        │
│   Snapshots     │    │  Browser         │    │  Tracking       │
│   (Manual)      │    │  (Search/Restore)│    │  (Metadata)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────┐
                    │   Researchers   │
                    │   (End Users)   │
                    └─────────────────┘
```

## 📁 Solution Structure

All solution files are located in the `lab4/` folder:

```
lab4/
├── lab4_solution.py          # Main orchestrator script
├── lab4_config.py            # Lab-specific configuration loader
├── protection_policies.py    # VAST protection policy management
├── snapshot_manager.py      # Core snapshot operations
├── snapshot_browser.py       # User interface for browsing snapshots
├── snapshot_restore.py      # Restoration and rollback tools
├── version_tracker.py       # Version tracking and metadata
├── snapshot_analytics.py    # Analytics and reporting
└── requirements.txt          # Python dependencies
```

## 🧪 Test Data

For optional data generation utilities, see the [scripts README](../scripts/README.md#test-data-generator).

**Note:** Configuration files (`config.yaml` and `secrets.yaml`) are centralized in the root directory for all labs.

## 🚀 Quick Start

### 1. Navigate to Lab 4 Directory
```bash
cd lab4
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

#### Setup Protection Policies
```bash
# Dry run (safe - shows what would be created)
python lab4_solution.py --setup-policies

# Production (creates actual protection policies)
python lab4_solution.py --setup-policies --pushtoprod
```

#### Create Named Snapshots
```bash
# Create snapshot with descriptive name
python lab4_solution.py --create-snapshot "pre-calibration-change" --view "/cosmos7/processed"

# Create snapshot for specific milestone
python lab4_solution.py --create-snapshot "post-processing-complete" --view "/cosmos7/analysis"
```

#### Browse and Restore Snapshots
```bash
# List all snapshots
python lab4_solution.py --list-snapshots

# Search snapshots by name
python lab4_solution.py --search-snapshots "calibration"

# Restore from snapshot (dry run)
python lab4_solution.py --restore-snapshot "pre-calibration-change" --view "/cosmos7/processed"

# Restore from snapshot (production)
python lab4_solution.py --restore-snapshot "pre-calibration-change" --view "/cosmos7/processed" --pushtoprod
```

#### Complete Workflow
```bash
# Run everything in sequence
python lab4_solution.py --complete --pushtoprod
```

## 🔧 Configuration

### Research-Based Retention Strategy

Our snapshot timing and retention policies are based on industry best practices and research data requirements:

#### **Industry Best Practices Applied:**
- **Grandfather-Father-Son Strategy**: Multiple retention tiers for different recovery scenarios
- **3-2-1 Backup Rule**: Multiple copies with different retention periods
- **RPO/RTO Alignment**: Snapshot frequency matches Recovery Point Objectives
- **Data Classification**: Different policies for different data types and importance levels

#### **Research Data Considerations:**
- **Reproducibility**: Extended retention for research reproducibility requirements
- **NASA Compliance**: Policies designed to meet NASA data retention standards
- **Version Control**: Systematic versioning for research data evolution
- **Collaboration**: Policies support multi-researcher workflows

#### **Retention Tiers:**
- **Hourly (3 days)**: Active work and real-time processing
- **Daily (14 days)**: Recent work and short-term recovery
- **Weekly (90 days)**: Research milestones and medium-term recovery
- **Monthly (1 year)**: Published datasets and compliance requirements
- **Yearly (5 years)**: Long-term archival and historical reference

### Main Configuration (`../config.yaml` - copy from `../config.yaml.example`)

```yaml
# Lab 4: Snapshot Strategy Settings
lab4:
  protection_policies:
    # Retention settings based on industry best practices and research data requirements
    # Following Grandfather-Father-Son strategy with research-specific considerations
    
    # Snapshot schedules (following industry best practices)
    schedules:
      # High-frequency snapshots for active work (every 6 hours, 3-day retention)
      hourly: "every 6h keep-local 3d"
      
      # Daily snapshots for recent work (daily, 2-week retention)
      daily: "every 24h keep-local 14d"
      
      # Weekly snapshots for milestones (weekly, 3-month retention)
      weekly: "every 7d keep-local 90d"
      
      # Monthly snapshots for releases (monthly, 1-year retention)
      monthly: "every 30d keep-local 365d"
      
      # Yearly snapshots for long-term archival (yearly, 5-year retention)
      yearly: "every 365d keep-local 1825d"
    
    # Policy templates based on data classification and research needs
    templates:
      # Raw data: High frequency, shorter retention (active processing)
      raw_data:
        schedule: "every 6h keep-local 3d"
        prefix: "raw-6h"
      
      # Processed data: Daily snapshots, medium retention (analysis phase)
      processed_data:
        schedule: "every 24h keep-local 14d"
        prefix: "processed-daily"
      
      # Analysis results: Weekly snapshots, longer retention (research milestones)
      analysis_results:
        schedule: "every 7d keep-local 90d"
        prefix: "analysis-weekly"
      
      # Published datasets: Monthly snapshots, long retention (publication compliance)
      published_datasets:
        schedule: "every 30d keep-local 365d"
        prefix: "published-monthly"
  
  views:
    - "/cosmos7/raw"
    - "/cosmos7/processed"
    - "/cosmos7/analysis"
    - "/cosmos7/published"
  
  snapshot_naming:
    include_timestamp: true
    include_user: true
    include_milestone: true
    max_name_length: 100
  
  restoration:
    dry_run_default: true
    backup_before_restore: true
    confirmation_required: true
```

### Secrets Configuration (`../secrets.yaml` - copy from `../secrets.yaml.example`)

```yaml
# VAST Connection Secrets
vast_password: "your_vast_password_here"
```

## ✨ Key Features

### ✅ VAST Protection Policies
- **Automated Schedules** - Daily, weekly, monthly snapshots with configurable retention
- **Space Efficiency** - Only stores differences between versions, not full copies
- **Policy Templates** - Pre-configured policies for different data types
- **Flexible Retention** - Configurable local and remote retention periods

### ✅ Named Snapshot Workflows
- **Descriptive Names** - Create snapshots with meaningful labels
- **Milestone Tracking** - Snapshots for processing milestones and calibration events
- **Metadata Tagging** - Rich metadata for easy searching and filtering
- **Manual Control** - On-demand snapshots for specific events

### ✅ User-Friendly Interface
- **Snapshot Browser** - Easy browsing of available snapshots
- **Search Capabilities** - Find snapshots by name, date, or metadata
- **Visual Timeline** - See dataset evolution over time
- **Comparison Tools** - Compare snapshots to understand changes

### ✅ Restoration Tools
- **One-Click Restoration** - Easy restoration to previous states
- **Dry-Run Mode** - Preview changes before applying
- **Selective Rollback** - Restore specific changes while preserving others
- **Batch Operations** - Restore multiple datasets simultaneously

### ✅ Version Tracking
- **Automatic Versioning** - Systematic version numbering for datasets
- **Change Logs** - Document what changed between versions
- **Audit Trails** - Complete history of all snapshot operations
- **Dependency Tracking** - Track relationships between related datasets

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
- ✅ **Snapshot Validity** - Snapshots must exist and be restorable
- ✅ **Permission Verification** - Proper access rights verified
- ✅ **Backup Validation** - Confirms backup capabilities before restoration

## 📊 Protection Policy Examples

### Daily Processing Policy
```json
{
  "name": "cosmos7-daily-processing",
  "frames": "every 24h keep-local 7d",
  "prefix": "daily-processing",
  "clone_type": "LOCAL"
}
```

### Hourly Raw Data Policy
```json
{
  "name": "cosmos7-raw-hourly",
  "frames": "every 6h keep-local 3d",
  "prefix": "raw-hourly",
  "clone_type": "LOCAL"
}
```

### Weekly Analysis Policy
```json
{
  "name": "cosmos7-analysis-weekly",
  "frames": "every 7d keep-local 30d",
  "prefix": "analysis-weekly",
  "clone_type": "LOCAL"
}
```

### Monthly Published Data Policy
```json
{
  "name": "cosmos7-published-monthly",
  "frames": "every 30d keep-local 90d",
  "prefix": "published-monthly",
  "clone_type": "LOCAL"
}
```

## 🔍 Usage Examples

### Setup Protection Policies
```bash
# Create all protection policies (dry run)
python lab4_solution.py --setup-policies

# Create specific policy template
python lab4_solution.py --create-policy raw_data --view "/cosmos7/raw"

# List existing policies
python lab4_solution.py --list-policies
```

### Create Named Snapshots
```bash
# Create snapshot before calibration change
python lab4_solution.py --create-snapshot "pre-mars-calibration-change" --view "/cosmos7/processed"

# Create snapshot after processing milestone
python lab4_solution.py --create-snapshot "post-asteroid-tracking-phase-1" --view "/cosmos7/analysis"

# Create snapshot with custom metadata
python lab4_solution.py --create-snapshot "nasa-deliverable-v1.2" --view "/cosmos7/published" --metadata "nasa_deliverable=true,version=1.2"
```

### Browse and Search Snapshots
```bash
# List all snapshots
python lab4_solution.py --list-snapshots

# Search by name pattern
python lab4_solution.py --search-snapshots "calibration"

# Search by date range
python lab4_solution.py --search-snapshots --date-range "2025-01-01" "2025-01-31"

# Show snapshot details
python lab4_solution.py --snapshot-details "pre-mars-calibration-change"
```

### Restore from Snapshots
```bash
# Restore from snapshot (dry run)
python lab4_solution.py --restore-snapshot "pre-calibration-change" --view "/cosmos7/processed"

# Restore from snapshot (production)
python lab4_solution.py --restore-snapshot "pre-calibration-change" --view "/cosmos7/processed" --pushtoprod

# Restore multiple views
python lab4_solution.py --restore-snapshot "milestone-complete" --views "/cosmos7/processed" "/cosmos7/analysis"
```

## 🧪 Testing

The solution includes comprehensive error handling and validation built into the main functionality.

### Test Script
```bash
# Test all components
python test_lab4_solution.py
```

This will verify that all components can be imported and initialized correctly.

## 🎯 Success Criteria

1. **Systematic Version Control** - All datasets have systematic version tracking using VAST protection policies
2. **Easy Recovery** - Researchers can find and restore previous versions in under 5 minutes
3. **Space Efficiency** - Snapshot storage overhead is minimal (less than 10% of original data)
4. **User-Friendly Interface** - Intuitive tools for browsing and restoring snapshots
5. **Automated Policies** - Snapshots are created automatically at key milestones
6. **NASA Compliance** - Meet data versioning and recovery requirements
7. **Research Reproducibility** - Researchers can reference specific snapshot versions in publications

## 🚨 Troubleshooting

### Common Issues

1. **Protection Policy Creation Failed**
   - Ensure VAST cluster is accessible
   - Check credentials in `secrets.yaml`
   - Verify view paths exist

2. **Snapshot Not Found**
   - Check snapshot name spelling
   - Verify snapshot exists with `--list-snapshots`
   - Ensure snapshot hasn't expired based on retention policy

3. **Restoration Failed**
   - Use dry-run mode first to preview changes
   - Check view permissions
   - Verify snapshot is restorable

4. **Permission Denied**
   - Verify user has appropriate permissions on VAST cluster
   - Check protection policy permissions
   - Ensure view access rights

### Debug Tools
```bash
# Debug protection policies
python protection_policies.py --debug

# Debug snapshot operations
python snapshot_manager.py --debug

# Test complete solution
python test_lab4_solution.py
```

## 📈 Performance

- **Efficient Snapshots** - VAST's space-efficient snapshot technology minimizes storage overhead
- **Fast Restoration** - Optimized restoration processes for quick recovery
- **Scalable Policies** - Protection policies scale with data volume
- **Batch Operations** - Efficient handling of multiple snapshot operations

## 📚 API Reference

### ProtectionPolicies
- `create_policy(name, schedule, prefix, clone_type)` - Create protection policy
- `list_policies()` - List all protection policies
- `delete_policy(policy_id)` - Delete protection policy
- `apply_policy_to_view(policy_id, view_path)` - Apply policy to view

### SnapshotManager
- `create_named_snapshot(name, view_path, metadata)` - Create named snapshot
- `list_snapshots(view_path)` - List snapshots for view
- `get_snapshot_details(snapshot_name)` - Get snapshot details
- `delete_snapshot(snapshot_name)` - Delete snapshot

### SnapshotRestore
- `restore_from_snapshot(snapshot_name, view_path, dry_run)` - Restore from snapshot
- `compare_snapshots(snapshot1, snapshot2)` - Compare snapshots
- `validate_restoration(snapshot_name, view_path)` - Validate restoration

### VersionTracker
- `track_version_change(view_path, change_description)` - Track version change
- `get_version_history(view_path)` - Get version history
- `create_change_log(snapshot1, snapshot2)` - Create change log

## 🔮 Next Steps

1. **Advanced Analytics** - Add snapshot usage analytics and optimization recommendations
2. **API Development** - Create REST API for external system integration
3. **Web Interface** - Build web-based snapshot management interface
4. **Integration** - Integrate with Lab 5 real-time systems for automated snapshots
5. **Machine Learning** - Implement intelligent snapshot scheduling based on usage patterns

## 📞 Support

If you encounter issues:

1. **Check the test script** output for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check VAST connectivity** and permissions
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a comprehensive snapshot strategy system that provides systematic version control for research datasets using VAST's protection policies and snapshot capabilities.
