# VAST SDK Workshop Outline

## 🕐 2-Hour Workshop Agenda

### **Part 1: VAST SDK Fundamentals (30 minutes)**

#### **Welcome & Introduction (5 minutes)**
- Workshop overview and learning objectives
- Participant introductions and experience levels
- Environment setup verification (see [Main README](../README.md))

#### **VAST Data & SDKs Overview (15 minutes)**
- Introduction to `vastpy` and `vastdb` SDKs
- Key concepts: views, quotas, databases, snapshots
- Real-world use cases and business value
- Basic connection and authentication
- Core concepts: clients, views, quotas, clusters
- Common operations and API patterns
- Error handling and troubleshooting

#### **Connection & Configuration (10 minutes)**
- Configuration management approach
- Setting up `config.yaml` and `secrets.yaml`
- Connection patterns and best practices
- Security considerations and credential management

### **Part 2: Hands-On Examples (25 minutes)**

#### **Core Examples (15 minutes)**
- **Example 1: System Connection** - `01_connect_to_vast.py` (3 min)
- **Example 2: Storage Views** - `02_list_views.py` (3 min)
- **Example 3: Quota Management** - `03_check_quotas.py` (3 min)
- **Example 4: System Health** - `04_monitor_health.py` (3 min)
- **Example 9: System Inventory** - `09_show_inventory.py` (3 min)

#### **Advanced Examples (10 minutes)**
- **Example 5: Snapshots** - `05_show_snapshots.py` (2 min)
- **Example 6: Chargeback Report** - `06_chargeback_report.py` (2 min)
- **Example 7: Orphaned Data Discovery** - `07_orphaned_data_discovery_catalog.py` (3 min)
- **Example 8: User Quotas** - `08_show_user_quotas.py` (3 min)

**Note:** Participants run all examples with live demonstration and hands-on practice

### **Part 3: Lab Scenarios (50 minutes)**

#### **Lab 1: Storage Monitoring & Auto-Expansion (15 minutes)**
- **Story Context:** Read Lab 1 story (3 minutes)
- **Technical Walkthrough:** Lab 1 solution (7 minutes)
  - Storage monitoring concepts
  - Quota expansion automation
  - Safety checks and dry-run modes
- **Hands-On Practice:** Run Lab 1 in dry-run mode (5 minutes)

#### **Lab 2: Metadata Infrastructure (15 minutes)**
- **Story Context:** Read Lab 2 story (3 minutes)
- **Technical Walkthrough:** Lab 2 solution (7 minutes)
  - Metadata extraction and storage
  - Database schema design
  - Search and query capabilities
- **Hands-On Practice:** Explore metadata system (5 minutes)

#### **Lab 3: Weather Data Pipeline (20 minutes)**
- **Story Context:** Read Lab 3 story (5 minutes)
- **Technical Walkthrough:** Lab 3 solution (10 minutes)
  - Weather data ingestion and processing
  - Advanced analytics and correlations
  - Health impact assessment
  - Real-time data pipeline concepts
- **Hands-On Practice:** Explore weather analytics (5 minutes)

### **Wrap-up & Next Steps (10 minutes)**

#### **Key Takeaways (5 minutes)**
- Core concepts and best practices
- Common patterns and anti-patterns
- Production considerations

#### **Q&A and Discussion (5 minutes)**
- Open questions and clarifications
- Real-world scenarios and challenges
- Next steps and resources

## 🎯 Learning Checkpoints

### **After Part 1:**
- [ ] Can connect to VAST system
- [ ] Understand basic SDK concepts
- [ ] Know configuration requirements

### **After Part 2:**
- [ ] Can run example scripts
- [ ] Understand view and quota concepts
- [ ] Can monitor system health

### **After Part 3:**
- [ ] Understand lab scenarios
- [ ] Can run labs in dry-run mode
- [ ] Know how to build data pipelines

## ⏰ Timing Notes

- **Buffer Time:** 5 minutes built into each major section
- **Flexible Sections:** Examples can be adjusted based on participant experience
- **Break Option:** 10-minute break after Part 1 if needed
- **Q&A Integration:** Questions encouraged throughout, not just at the end

## 🛠️ Required Materials

- **Laptop** with Python 3.7+ installed
- **VAST cluster access** (read-only credentials)
- **Internet connection** for documentation and resources
- **Terminal/command line** access
- **Code editor** (VS Code, PyCharm, or similar)

## 📋 Preparation Checklist

- [ ] Repository cloned and dependencies installed
- [ ] Configuration files set up
- [ ] Connection test successful
- [ ] Example scripts run successfully
- [ ] Lab 1 and Lab 2 reviewed
- [ ] Troubleshooting guide available
