# Lab 4: The Snapshot Strategy

> 📖 **Hey, remember to read the [story](STORY.md) to understand what we're doing and why!** This will help you understand the business context and challenges the Orbital Dynamics team is facing.

## 🎯 Overview

This Lab 4 solution demonstrates how to implement systematic version control for research datasets using VAST's protection policies and snapshot capabilities. We'll build a comprehensive system that automatically creates snapshots at key milestones and provides researchers with easy tools to browse, search, and restore from previous dataset versions.

## Build our Infrastructure: Code Lab Server Access
The VAST Data Labs gives our entire community remote access to our data infrastructure platform for hands-on exploration and testing. The lab environment is a practical way to get familiar with VAST systems, try out different configurations, and build automation workflows - all without needing your own hardware setup.

If you do not have access to a VAST cluster, complete this lab using our data infrastructure platform, [join our Community to get Code Lab Server access](https://community.vastdata.com/t/official-vast-data-labs-user-guide/1774#p-2216-infrastructure-automation-with-python-and-the-vast-api-3).

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
├── snapshot_manager.py       # Core snapshot operations
├── snapshot_restore.py      # Restoration and rollback tools
├── protection_policies.py   # VAST protection policy management
├── lab4_config.py           # Lab-specific configuration loader
├── README.md                # This documentation
└── requirements.txt         # Python dependencies
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
# Copy and edit configuration files
cp ../config.yaml.example ../config.yaml
cp ../secrets.yaml.example ../secrets.yaml
# Edit ../config.yaml and ../secrets.yaml as needed
```

### 4. Quick Commands

```bash
# Setup protection policies
python lab4_solution.py --setup-policies --pushtoprod

# Create snapshots
python lab4_solution.py --create-snapshot "pre-calibration-change" --protected-path "processed"

# List and browse snapshots
python lab4_solution.py --list-available-snapshots --protected-path "processed"
python lab4_solution.py --browse-snapshot "pre-calibration-change" --protected-path "processed"

# Restore from snapshot
python lab4_solution.py --restore-snapshot "pre-calibration-change" --protected-path "processed" --pushtoprod

# Test safely (use test_snapshot protected path)
python lab4_solution.py --create-snapshot "test-snapshot" --protected-path "test_snapshot" --pushtoprod
python lab4_solution.py --restore-snapshot "test-snapshot" --protected-path "test_snapshot" --pushtoprod
```

## 🔧 Configuration

The solution uses industry best practices for snapshot retention:

- **6-hour snapshots**: Active work (3-day retention)
- **Daily snapshots**: Recent work (2-week retention)  
- **Weekly snapshots**: Milestones (3-month retention)
- **Monthly snapshots**: Releases (1-year retention)
- **Yearly snapshots**: Long-term archival (5-year retention)

Configuration files are in the root directory: `../config.yaml` and `../secrets.yaml`

## 🛡️ Safety System

The system runs in **dry-run mode by default** (safe, no changes made). Use `--pushtoprod` flag to make actual changes to your VAST system.

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
- `restore_from_snapshot(snapshot_name, protected_path_name, dry_run)` - Restore from snapshot
- `list_available_snapshots(protected_path_name)` - List snapshots available for restoration
- `browse_snapshot(snapshot_name, protected_path_name)` - Browse files in snapshot
- `get_snapshot_stats(snapshot_name, protected_path_name)` - Get snapshot statistics

## 📞 Support

If you encounter issues:

1. **Check the test script** output for specific errors
2. **Verify configuration** in config.yaml and secrets.yaml
3. **Check VAST connectivity** and permissions
4. **Review logs** for detailed error messages

---

**🎉 Congratulations!** You now have a comprehensive snapshot strategy system that provides systematic version control for research datasets using VAST's protection policies and snapshot capabilities.
