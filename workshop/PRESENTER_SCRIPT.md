# VAST SDK Workshop Presenter Script

## 🎯 Presenter Notes

This script provides detailed talking points and timing for the 2-hour VAST SDK workshop. Use this as a guide while adapting to your audience's experience level and questions.

---

## **Part 1: VAST SDK Fundamentals (30 minutes)**

### **Welcome & Introduction (5 minutes)**

**"Welcome everyone to the VAST SDK Hands-On Workshop! I'm [Your Name], and I'll be your guide through the next 2 hours as we explore VAST Data's Python SDKs."**

**"Let's start with a quick audience survey to understand your backgrounds. Please raise your hand if you:**
- **Have programmed in Python before** (wait for response)
- **Are a system administrator** (wait for response)
- **Are a DevOps engineer** (wait for response)
- **Are a data engineer or data scientist** (wait for response)
- **Have worked with VAST Data before** (wait for response)
- **Are completely new to VAST Data** (wait for response)

**"Great! Based on what I'm seeing, I'll adjust the pace accordingly. For those new to VAST Data, don't worry - we'll start with the basics and build up from there."**

**"Today we'll cover three main areas:**
1. **VAST SDK fundamentals** - The core concepts and connection patterns
2. **Hands-on examples** - Live demonstrations you'll follow along with
3. **Real-world lab scenarios** - Practical applications you can use immediately

**"Before we dive in, let's verify everyone's environment is ready. Can you all see your terminal/command line? Great! Let's do a quick connection test."**

---

### **VAST Data & SDKs Overview (15 minutes)**

**"VAST Data is a unified data platform that combines storage, database, and analytics capabilities. Think of it as your data lake, data warehouse, and data processing engine all in one system."**

**"Today we'll work with two Python SDKs:**
- **`vastpy`** - For storage management, monitoring, and infrastructure operations
- **`vastdb`** - For database operations, queries, and data analytics

**"Key concepts you'll encounter:**
- **Views** - Fundamental building blocks that serve as organized windows into your storage infrastructure, acting as logical access points that control how data is presented across different protocols (S3, NFS, SMB, block)
- **Quotas** - Storage limits and usage tracking for different users or projects
- **Databases** - Structured data storage with SQL-like query capabilities
- **Snapshots** - Point-in-time copies of your data for backup and recovery

**"Why does this matter? In today's data-driven world, you need:**
- **Unified storage** that scales from terabytes to petabytes
- **Multiple access methods** (S3, NFS, database) from the same data
- **Automated management** to handle growth and complexity
- **Real-time insights** into your data and infrastructure

**"The SDKs make all of this accessible through Python, which many of us already know and love."**

**"`vastpy` is your gateway to VAST storage management. It provides a Python interface to all the storage operations you'd normally do through the web UI or CLI."**

**"In `vastpy`, you'll work with:**
- **VASTClient** - Your main connection object
- **Clusters** - System information and capacity
- **Views, Quotas, and Snapshots** - The concepts we just discussed"

**"Basic connection pattern:"**

```python
from vastpy import VASTClient

# Create client
client = VASTClient(
    address='your-vast-cluster.com',
    user='your-username',
    password='your-password'
)

# Test connection
clusters = client.clusters.get()
if clusters:
    print("Connection successful!")
    print(f"Found {len(clusters)} cluster(s)")
else:
    print("No clusters found")
```

**"Common operations:**
- **List views** - `client.views.get()`
- **Check quotas** - `client.quotas.get()`
- **Monitor health** - `client.clusters.get()`
- **Manage snapshots** - `client.snapshots.get()`

**"Error handling is crucial in production:"**

```python
try:
    views = client.views.get()
    if not views:
        print("No views found")
    else:
        print(f"Success! Found {len(views)} views")
except Exception as e:
    print(f"Error: {e}")
    # Handle gracefully
```

**"Always use try-catch blocks and check for empty results. VAST systems can be large and complex, so defensive programming is essential."**

---

### **Connection & Configuration (10 minutes)**

**"Let's talk about how we connect to VAST systems. We use a centralized configuration approach that's both secure and flexible."**

**"Configuration files:**
- **`config.yaml`** - Non-sensitive settings like endpoints and timeouts
- **`secrets.yaml`** - Sensitive data like passwords and API keys
- **Never commit secrets** to version control

**"Here's how we load the configuration into our scripts:"**

```python
# Load configuration
config = ConfigLoader('config.yaml', 'secrets.yaml')

# Get VAST settings
vast_address = config.get('vast.address')
vast_user = config.get('vast.user')
vast_password = config.get_secret('vast_password')
```

**"Key configuration principles:**
- **Fail-fast approach** - Missing configuration causes immediate errors
- **No dangerous defaults** - You must explicitly set every value
- **Environment-specific** - Different configs for dev, staging, production

**"Security best practices:**
- Use environment variables for secrets in production
- Rotate credentials regularly
- Use least-privilege access
- Enable SSL/TLS for all connections

**"Let's look at a real configuration example..."**

---

## **Part 2: Hands-On Examples (25 minutes)**

### **Core Examples (15 minutes)**

**"Let's work through the core examples that demonstrate fundamental VAST SDK operations. We'll cover 5 examples in 15 minutes, so about 3 minutes each."**

#### **Example 1: System Connection (3 minutes)**

**"Let's start with the basics - connecting to your VAST system."**

**"Run this command:"**
```bash
cd examples
python 01_connect_to_vast.py
```

**"This demonstrates:**
- Basic VAST connection using `vastpy`
- System information retrieval
- Capacity and utilization metrics
- Error handling patterns

**"Key things to notice:**
- Connection success and cluster details
- Capacity information (physical, usable, logical space)
- Data reduction ratios
- Usage breakdown

**"Take a moment to run this and let me know if you see any issues."**

#### **Example 2: Storage Views (3 minutes)**

**"Now let's look at your storage views - the organized windows into your storage infrastructure."**

**"Run this command:"**
```bash
python 02_list_views.py
```

**"The output shows:**
- Logical Size - The amount of data written
- Physical Size - The actual storage space used

#### **Example 3: Quota Management (3 minutes)**

**"Quotas control storage usage and prevent any single user from consuming all available space."**

**"Run this command:"**
```bash
python 03_check_quotas.py
```

**"This displays:**
- All quota configurations
- Current usage vs. limits
- Utilization percentages
- Quotas that need attention

#### **Example 4: System Health (3 minutes)**

**"Let's check the overall health of your VAST system."**

**"Run this command:"**
```bash
python 04_monitor_health.py
```

**"This provides:**
- Cluster health status and capacity
- Individual node status (CNodes and DNodes)
- Overall system connectivity

#### **Example 9: System Inventory (3 minutes)**

**"Finally, let's get a comprehensive overview of your VAST system."**

**"Run this command:"**
```bash
python 09_show_inventory.py
```

**"This shows:**
- All views categorized by protocol (S3, NFS, SMB, Block, Database)
- Bucket names for S3 and Database views
- Summary statistics across all protocols
- Clean, organized system overview

---

### **Advanced Examples (10 minutes)**

**"Now let's look at some advanced examples that demonstrate more sophisticated VAST capabilities."**

#### **Example 5: Snapshots (2 minutes)**

**"Snapshots are point-in-time copies of your data for backup and recovery."**

**"Run this command:"**
```bash
python 05_show_snapshots.py
```

**"This shows snapshot sizes, creation times, and summary statistics."**

#### **Example 6: Chargeback Report (2 minutes)**

**"Let's generate a cost analysis report to understand storage spending."**

**"Run this command:"**
```bash
python 06_chargeback_report.py
```

**"This shows top expensive views and monthly costs."**

#### **Example 7: Orphaned Data Discovery (3 minutes)**

**"Let's find orphaned data - files that exist but aren't associated with any view."**

**"Run this command:"**
```bash
python 07_orphaned_data_discovery_catalog.py
```

**"This efficiently finds orphaned directories using VAST catalog."**

#### **Example 8: User Quotas (3 minutes)**

**"Let's examine detailed user quota information with professional formatting."**

**"Run this command:"**
```bash
python 08_show_user_quotas.py --all
```

**"This displays comprehensive quota summary and individual user details."**

---

## **Part 3: Lab Scenarios (50 minutes)**

### **Lab 1: Storage Monitoring & Auto-Expansion (15 minutes)**

**"Now let's dive into real-world scenarios. Lab 1 focuses on storage monitoring and automated quota expansion."**

**"First, let's understand the business context. Read the story in `lab1/STORY.md` - this gives you the 'why' behind what we're building."**

**"The story shows how Orbital Dynamics, a space technology company, needs to monitor their storage infrastructure and automatically expand quotas before they run out of space. This prevents data processing delays and keeps their NASA contract on track."**

**"Key concepts in Lab 1:**
- **Proactive monitoring** - Check storage before it becomes critical
- **Automated expansion** - Increase quotas based on usage patterns
- **Safety checks** - Multiple validation layers before making changes
- **Dry-run mode** - Test everything before applying changes

**"Let's look at the technical implementation:"**

```bash
cd lab1
python lab1_solution.py --setup-only
```

**"This shows you what would be created without actually making changes. Notice the safety features:**
- **Dry-run by default** - No changes unless you explicitly use `--pushtoprod`
- **Confirmation prompts** - Requires 'YES' confirmation for production changes
- **Validation checks** - Tests connections and existing infrastructure

**"The solution includes:**
- **Storage monitoring** - Regular checks of quota utilization
- **Predictive scaling** - Expand quotas before they're full
- **Pipeline integration** - Works with data processing workflows
- **Centralized configuration** - Uses the same config system as examples

**"Try running it in dry-run mode to see what it would do:"**

```bash
python lab1_solution.py --monitor-only
```

**"This demonstrates how you can build automated storage management that prevents crises rather than reacting to them."**

---

### **Lab 2: Metadata Infrastructure (15 minutes)**

**"Lab 2 tackles a different challenge - building a comprehensive metadata system for data discovery and management."**

**"Read the story in `lab2/STORY.md` to understand the business context. Orbital Dynamics needs to catalog their satellite data so researchers can find and use it efficiently."**

**"The challenge:**
- **Massive data volumes** - Petabytes of satellite observations
- **Multiple data formats** - FITS files, lightcurves, JSON metadata
- **Complex search requirements** - Find data by mission, date, target, quality
- **Real-time processing** - Catalog data as it arrives

**"Technical approach:**
- **VAST Database** - Store metadata in structured format
- **Automated extraction** - Parse metadata from various file formats
- **Powerful search** - Query metadata with complex criteria
- **S3 integration** - Link metadata to actual data files

**"Let's explore the solution:"**

```bash
cd lab2
python lab2_solution.py --setup-only
```

**"This creates the database infrastructure needed for metadata storage. Notice how it:**
- **Checks existing infrastructure** - Won't overwrite existing databases
- **Creates structured schema** - Optimized for search and querying
- **Handles errors gracefully** - Continues even if some operations fail

**"The metadata schema includes:**
- **File information** - Path, size, format, checksum
- **Mission data** - Satellite, instrument, target, timestamp
- **Processing status** - Raw, processed, archived
- **Search optimization** - Indexed fields for fast queries

**"Try the search capabilities:"**

```bash
python lab2_solution.py --search-only --stats
```

**"This demonstrates how you can build searchable data catalogs that make petabytes of data discoverable and usable."**

---

### **Lab 3: Weather Data Pipeline (20 minutes)**

**"Lab 3 shows how to build complete data processing pipelines with VAST Database for real-world analytics."**

**"First, let's understand the business context. Read the story in `lab3/STORY.md` - this explains why Orbital Dynamics is expanding into weather data analytics for health risk assessment and environmental monitoring."**

**"The challenge:**
- **Massive data volumes** - Weather data for multiple cities over time
- **Real-time processing** - Analyze data as it arrives
- **Complex analytics** - Correlate weather patterns with air quality
- **Health impact assessment** - Detect dangerous pollution episodes

**"Technical approach:**
- **Weather data ingestion** - Download from Open-Meteo API
- **VAST Database storage** - Scalable time-series data storage
- **Advanced analytics** - Correlation analysis and trend detection
- **Health monitoring** - WHO guidelines for air quality assessment

**"Let's explore the solution:"**

```bash
cd lab3
python weather_analytics_demo.py
```

**"This demonstrates:**
- **Real-time data ingestion** - Process weather data as it arrives
- **Advanced analytics** - Complex queries and correlations
- **Multi-city analysis** - Compare patterns across locations
- **Health applications** - Real-world impact of data analysis

**"Key concepts to understand:**
- **Time-series data** - Weather data over time
- **Correlation analysis** - Finding relationships between variables
- **Health impact assessment** - Using data for public health
- **Scalable processing** - Handling large datasets efficiently

**"This shows how VAST Database makes complex analytics accessible through SQL while handling the scale and performance requirements of real-time data processing."**

---

## **Wrap-up & Next Steps (10 minutes)**

### **Key Takeaways (5 minutes)**

**"Let's recap what we've covered today:"**

**"Core concepts:**
- **VAST SDKs** provide Python access to storage and database operations
- **Configuration management** ensures security and flexibility
- **Safety practices** prevent accidents in production environments
- **Real-world applications** solve actual business problems

**"Best practices:**
- **Always use dry-run mode** for testing and validation
- **Implement comprehensive error handling** for production reliability
- **Monitor proactively** rather than reacting to problems
- **Design for scale** from the beginning

**"Common patterns:**
- **Connection → Operation → Validation** - Standard workflow
- **Configuration → Secrets → Client** - Standard setup
- **Dry-run → Test → Production** - Standard deployment

**"Anti-patterns to avoid:**
- **Hardcoded credentials** - Use configuration files
- **No error handling** - Always catch and handle exceptions
- **No validation** - Test before making changes
- **No monitoring** - You can't manage what you don't measure

---

### **Q&A and Discussion (5 minutes)**

**"Now let's open it up for questions and discussion:"**

**"Common questions I expect:**
- **'How do I handle SSL certificate issues?'** - Use `ssl_verify: false` for testing, proper certificates for production
- **'What's the difference between vastpy and vastdb?'** - vastpy for storage management, vastdb for data analytics and database management
- **'How do I scale this to production?'** - Start with dry-run mode, add monitoring, implement proper error handling
- **'Can I use this with other tools?'** - Yes, VAST integrates with many data science and analytics tools

**"Real-world scenarios:**
- **'We have 100TB of data to migrate'** - Use the examples as templates, implement batch processing
- **'We need real-time monitoring'** - Build on Lab 1, add alerting and dashboards
- **'We want to catalog our research data'** - Use Lab 2 as a starting point, customize for your data types

**"Next steps:**
- **Try the examples** in your own environment
- **Run the labs** in dry-run mode to understand the patterns
- **Build your own solutions** using these as templates
- **[Join the VAST community](https://community.vastdata.com)** for ongoing discussions and examples

**"Thank you for participating! I hope you found this workshop valuable and feel confident using VAST SDKs in your own projects."**

---

## 🎯 Presenter Tips

### **Before the Workshop:**
- Test all examples in your environment
- Have backup plans for common issues
- Prepare real-world examples from your experience

### **During the Workshop:**
- Encourage questions throughout
- Adapt timing based on participant experience
- Use real-world analogies and examples
- Emphasize safety and best practices

### **After the Workshop:**
- Provide contact information for follow-up questions
- Share additional resources and documentation
- Collect feedback for future improvements
- Offer to review participant implementations
