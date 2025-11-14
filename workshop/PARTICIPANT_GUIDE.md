# VAST SDK Workshop Participant Guide

## 🎯 Welcome to the Workshop!

This guide will help you follow along during the 2.25-hour VAST SDK workshop. Keep this open and follow the step-by-step instructions as we explore VAST Data's Python SDKs together.

## 📋 Pre-Workshop Checklist

Before we start, make sure you have:

- [ ] **Python 3.7+** installed on your laptop
- [ ] **Terminal/command line** access
- [ ] **Code editor** (VS Code, PyCharm, or similar)
- [ ] **Internet connection** for documentation
- [ ] **VAST cluster access** (read-only credentials provided)

## 🚀 Quick Setup

**Quick start:**
1. Clone repository and install dependencies according to the [Main README](../README.md).
2. Configure VAST access in `config.yaml` and `secrets.yaml`
3. Test connection with `python examples/01_connect_to_vast.py`

**Expected output:** You should see cluster information and capacity metrics. If you see connection errors, check your configuration files.

---

## 📚 Part 1: VAST SDK Fundamentals

### **Connection Test**

**Run this command:**
```bash
cd examples
python 01_connect_to_vast.py
```

**What to look for:**
- ✅ Connection successful message
- 📊 Cluster information (ID, name, GUID)
- 💾 Capacity metrics (physical, usable, logical space)
- 📈 Data reduction ratio

**If you see errors:**
- Check your `config.yaml` and `secrets.yaml` files
- Verify network connectivity to VAST cluster
- Ensure credentials are correct

### **Configuration Understanding**

**Open your `config.yaml` file and look for:**
```yaml
vast:
  address: "https://your-vast-cluster.com"
  user: "your-username"
  ssl_verify: true
  timeout: 30
```

**Open your `secrets.yaml` file and look for:**
```yaml
vast_password: "your-password"
s3_access_key: "your-s3-access-key"
s3_secret_key: "your-s3-secret-key"
```

**Key points:**
- `config.yaml` contains non-sensitive settings
- `secrets.yaml` contains sensitive data like passwords
- Never commit `secrets.yaml` to version control
- Use environment variables for production secrets

---

## 🔧 Part 2: Hands-On Examples

### **Core Examples**
*These examples demonstrate fundamental VAST SDK operations*

### **Example 1: System Connection**

**Command:**
```bash
python 01_connect_to_vast.py
```

**What this demonstrates:**
- Basic VAST connection using `vastpy`
- System information retrieval
- Capacity and utilization metrics
- Error handling patterns

**Key code to understand:**
```python
from vastpy import VASTClient

client = VASTClient(
    user=vast_config['user'],
    password=vast_config['password'],
    address=address
)

clusters = client.clusters.get()
```

### **Example 2: Storage Views**

**Command:**
```bash
python 02_list_views.py
```

**What this demonstrates:**
- Listing all storage views
- Logical vs Physical size analysis
- View metadata extraction

**What to look for:**
- Logical Size - The amount of data written
- Physical Size - The actual storage space used
- Different view types (S3, NFS, SMB, etc.)

### **Example 3: Quota Management**

**Command:**
```bash
python 03_check_quotas.py
```

**What this demonstrates:**
- Quota configuration retrieval
- Usage vs. limit analysis
- Quota status monitoring
- Capacity planning insights

**What to look for:**
- All quota configurations
- Current usage vs. limits
- Utilization percentages
- Quotas that need attention

### **Example 4: System Health**

**Command:**
```bash
python 04_monitor_health.py
```

**What this demonstrates:**
- Cluster health monitoring
- Node status and roles
- System performance metrics
- Connectivity validation

**What to look for:**
- Cluster health status and capacity
- Individual node status (CNodes and DNodes)
- Overall system connectivity

### **Example 9: System Inventory**

**Command:**
```bash
python 09_show_inventory.py
```

**What this demonstrates:**
- Comprehensive system overview
- Views categorized by protocol (S3, NFS, SMB, Block, Database)
- Bucket names and summary statistics

**What to look for:**
- All views categorized by protocol
- Bucket names for S3 and Database views
- Summary statistics across all protocols
- Clean, organized system overview

### **Advanced Examples**
*These examples demonstrate more sophisticated VAST capabilities*

### **Example 5: Snapshots**

**Command:**
```bash
python 05_show_snapshots.py
```

**What this demonstrates:**
- Snapshot listing and management
- Size analysis and creation times
- Summary statistics

**What to look for:**
- Snapshot sizes, creation times, and summary statistics

### **Example 6: Chargeback Report**

**Command:**
```bash
python 06_chargeback_report.py
```

**What this demonstrates:**
- Cost analysis and reporting
- Storage usage by root view
- Monthly cost calculations

**What to look for:**
- Top expensive views and monthly costs

### **Example 7: Orphaned Data Discovery**

**Command:**
```bash
python 07_orphaned_data_discovery_catalog.py
```

**What this demonstrates:**
- Finding orphaned data using catalog
- Efficient data cleanup identification

**What to look for:**
- Efficiently finds orphaned directories using VAST catalog
- Storage space recovery potential
- Cleanup recommendations

### **Example 8: User Quotas**

**Command:**
```bash
python 08_show_user_quotas.py --all
```

**What this demonstrates:**
- Detailed user quota information
- Usage percentages and status
- Professional formatting

**What to look for:**
- Comprehensive quota summary and individual user details


---

## 🏗️ Part 3: Lab Scenarios

### **Lab 1: Storage Monitoring & Auto-Expansion**

**First, read the story:**
```bash
cd lab1
cat STORY.md
```

**This gives you the business context - why Orbital Dynamics needs automated storage management.**

**Run the solution in dry-run mode:**
```bash
python lab1_solution.py --setup-only
```

**What this shows:**
- What infrastructure would be created
- Safety checks and validations
- Dry-run mode in action
- Configuration requirements

**Try the monitoring functionality:**
```bash
python lab1_solution.py --monitor-only
```

**What this demonstrates:**
- Storage utilization monitoring
- Quota status analysis
- Predictive scaling logic
- Safety checks before changes

**Key concepts to understand:**
- **Proactive monitoring** - Check storage before it becomes critical
- **Automated expansion** - Increase quotas based on usage patterns
- **Safety checks** - Multiple validation layers
- **Dry-run mode** - Test everything before applying changes

### **Lab 2: Metadata Infrastructure**

**First, read the story:**
```bash
cd lab2
cat STORY.md
```

**This explains why Orbital Dynamics needs a metadata catalog for their satellite data.**

**Set up the database infrastructure:**
```bash
python lab2_solution.py --setup-only
```

**What this creates:**
- Database and schema if they don't exist
- Metadata table structure
- Indexes for fast searching
- Safety checks for existing infrastructure

**Explore the search capabilities:**
```bash
python lab2_solution.py --search-only --stats
```

**What this demonstrates:**
- Metadata search and querying
- Database statistics
- Search result formatting
- Query performance

**Key concepts to understand:**
- **Metadata extraction** - Parse information from various file formats
- **Database storage** - Structured storage for fast queries
- **Search capabilities** - Find data by multiple criteria
- **S3 integration** - Link metadata to actual data files

### **Lab 3: Weather Data Pipeline**

**First, read the story:**
```bash
cd lab3
cat STORY.md
```

**This explains why Orbital Dynamics needs weather data analysis for their satellite operations.**

**Run the weather analytics demo:**
```bash
python weather_analytics_demo.py
```

**What this demonstrates:**
- Real-time weather data ingestion
- Advanced analytics and correlations
- Multi-city trend analysis
- Health impact assessment

**Key concepts to understand:**
- **Time-series data** - Weather data over time
- **Correlation analysis** - Finding relationships between variables
- **Health impact assessment** - Using data for public health
- **Scalable processing** - Handling large datasets efficiently

### **Lab 4: The Snapshot Strategy**

**First, read the story:**
```bash
cd lab4
cat STORY.md
```

**This explains why Orbital Dynamics needs systematic version control for their research datasets as they scale operations and collaborate with NASA.**

**Set up protection policies:**
```bash
python lab4_solution.py --setup-policies
```

**What this creates:**
- Automated protection policies with different schedules
- Configurable retention periods for different snapshot types
- Space-efficient snapshot infrastructure
- Safety checks for existing policies

**Create and browse snapshots:**
```bash
python lab4_solution.py --create-snapshot "test-milestone" --protected-path "test_snapshot"
python lab4_solution.py --list-available-snapshots --protected-path "test_snapshot"
python lab4_solution.py --browse-snapshot "test-milestone" --protected-path "test_snapshot"
```

**What this demonstrates:**
- Named snapshot creation with descriptive labels
- Snapshot browsing and exploration
- Version tracking and change management
- Restoration capabilities

**Key concepts to understand:**
- **Space-efficient snapshots** - VAST only stores differences, not full copies
- **Automated policies** - Set schedules and retention, system handles the rest
- **Named snapshots** - Create milestones with descriptive labels
- **Easy restoration** - Rollback to previous states quickly and safely
- **Research reproducibility** - Link published results to specific data versions

---

## 🎯 Key Learning Points

### **Connection Patterns**
```python
# Standard connection pattern
from vastpy import VASTClient

client = VASTClient(
    user=config.get('vast.user'),
    password=config.get_secret('vast_password'),
    address=config.get('vast.address')
)
```

### **Error Handling**
```python
try:
    result = client.views.get()
    if not result:
        print("No data found")
except Exception as e:
    print(f"Error: {e}")
    # Handle gracefully
```

### **Safety Practices**
- Always use dry-run mode for testing
- Implement comprehensive error handling
- Validate before making changes
- Monitor proactively

### **Common Operations**
- **List views:** `client.views.get()`
- **Check quotas:** `client.quotas.get()`
- **Monitor health:** `client.clusters.get()`
- **Database queries:** `vastdb.connect()`

---

## 🛠️ Troubleshooting

### **Connection Issues**
- Verify `config.yaml` and `secrets.yaml` exist
- Check VAST cluster is accessible
- Ensure credentials are correct
- Try `ssl_verify: false` for testing

### **Import Errors**
- Make sure you're in the right directory
- Verify `pip install -r requirements.txt` completed
- Check Python path includes the root directory

### **No Data Found**
- Some examples may show "No data found" in empty systems
- This is normal for new or test environments
- Examples still demonstrate the API calls

### **Database Connection Issues**
- Check endpoint points to database VIP (not VMS)
- Verify S3 credentials are correct
- Try `ssl_verify: false` for testing
- Contact VAST administrator for correct endpoint

---

## 📞 Getting Help

### **During the Workshop**
- Ask questions during designated Q&A periods
- Use the troubleshooting guide
- Check the example scripts for reference
- Ask your neighbor for help

### **After the Workshop**
- Review the documentation in each lab directory
- Try running the examples in your own environment
- Build your own solutions using these as templates
- Join the VAST community for ongoing support

### **Resources**
- **VAST Documentation:** https://support.vastdata.com/s/
- **vastpy GitHub:** https://github.com/vast-data/vastpy
- **vastdb GitHub:** https://github.com/vast-data/vastdb_sdk
- **Community Support:** https://community.vastdata.com

---

## 🎉 Next Steps

After the workshop, consider:

1. **Try the examples** in your own environment
2. **Run the labs** in dry-run mode to understand the patterns
3. **Build your own solutions** using these as templates
4. **Explore advanced features** like snapshots and analytics
5. **Join the VAST community** for ongoing support and examples

**Remember:** The best way to learn VAST SDKs is by doing. Start with the examples, then build your own solutions using the patterns you've learned today.

---

*"In space exploration, preparation is everything. We build our data organization systems to handle the scale we expect, not the scale we hope to manage."* - Dr. Alex Sterling
