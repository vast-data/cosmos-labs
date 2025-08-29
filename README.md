# WIP - DO NOT USE YET

# Orbital Dynamics: Hands-On Labs with VAST SDKs

## Welcome to Orbital Dynamics

*"Where complex systems find their orbit"*

Orbital Dynamics is a mid-sized space technology company that processes astronomical data and manages satellite constellation networks for research institutions, government agencies, and private space companies. They've recently landed a major NASA contract for real-time processing of deep space telescope data, which is pushing their infrastructure to new limits.

This series of hands-on labs follows the journey of the Orbital Dynamics team as they tackle real-world challenges using the VAST Management System and VAST Database. Through these labs, you'll learn how to use `vastpy` and `vastdb_sdk` to solve complex data management and processing problems in a space technology environment.

## The Team

Meet the characters who will guide you through these challenges:

- **Dr. Alex Sterling (CTO)** - Former JPL engineer who understands the domain and drives the company's technical vision
- **Maya Chen (Lead SysAdmin)** - Gaming industry veteran adapting to space-scale challenges
- **Jordan Blake (Senior Developer)** - Brilliant but sometimes gets lost in technical details
- **Sam Rodriguez (DevOps Engineer)** - The alignment specialist who bridges dev and ops
- **Mac Thompson (Junior Admin)** - Eager learner prone to educational mistakes

## Lab Overview

### [Lab 1: Proactive Satellite Data Infrastructure Planning](Lab_1_Satellite_Data_Infrastructure_Planning.md)
**Challenge:** Design and implement automated storage management before COSMOS-7 satellite launch
- Use `vastpy` to build proactive storage provisioning and quota management
- Create predictive scaling systems that anticipate data growth
- Build monitoring and alerting that prevents infrastructure crises
- Integrate with data processing pipelines for seamless operation
- **NEW:** Comprehensive safety system with dry-run/production modes

### [Lab 2: Proactive Metadata Infrastructure Planning](Lab_2_Metadata_Infrastructure_Project.md)
**Challenge:** Build a comprehensive metadata catalog system before data organization becomes unmanageable
- Use `vastpy` to create VAST views for organized data storage
- Build automated metadata extraction workflows for various file formats
- Create search and query interfaces for efficient data discovery
- Integrate metadata systems with existing data processing pipelines
- **NEW:** Comprehensive safety system with dry-run/production modes

### [Lab 3: The Multi-Mission Data Pipeline](Lab_3_Multi_Mission_Data_Pipeline.md)
**Challenge:** Orchestrate processing for three different satellite constellations
- Combine `vastpy` and `vastdb_sdk` for unified pipeline orchestration
- Build automated job management with failure handling
- Create real-time monitoring dashboards
- Support different data formats and processing requirements

### [Lab 4: The Snapshot Strategy](Lab_4_Snapshot_Strategy.md)
**Challenge:** Implement systematic version control for research datasets
- Use `vastpy` to implement automated snapshot policies
- Build named snapshot workflows for key milestones
- Create tools for browsing and restoring from snapshots
- Establish systematic version tracking and management

### [Lab 5: The Real-Time Alert System](Lab_5_Real_Time_Alert_System.md)
**Challenge:** Detect astronomical events in real-time and alert appropriate teams
- Use `vastdb_sdk` for real-time data ingestion and analysis
- Build automated detection for specific astronomical events
- Create multi-level alerting based on event type and urgency
- Develop APIs for external system integration

## Prerequisites

Before starting these labs, you should have:

- Basic Python programming experience
- Familiarity with REST APIs and JSON
- Understanding of data processing concepts
- Access to a VAST Management System cluster
- Python 3.7+ installed

## Required Tools

- **vastpy** - Python SDK for VAST Management System (storage, views, monitoring)
- **vastdb** - Python SDK for VAST Database (metadata catalog, queries)
- **Python 3.7+** - Programming language
- **Jupyter Notebook** (optional) - For interactive development
- **Git** - For version control

## Python Dependencies

The following Python packages are required:

- **pyyaml** - YAML configuration file parsing
- **vastpy** - VAST Management System SDK (version 0.3.17+)
- **vastdb_sdk** - VAST Database SDK for metadata catalog functionality
- **astropy** - Astronomical data processing (for Lab 2)
- **h5py** - HDF5 file format support (for Lab 2)

**Note:** vastpy 0.3.17 supports basic authentication with `user`, `password`, and `address` parameters. Advanced features like `token`, `tenant_name`, and `version` are not yet supported in this version.

## Configuration Management

This repository uses a centralized configuration approach with **strict validation**:

- **`config.yaml.example`** - Example configuration template for all labs (non-sensitive settings)
- **`secrets.yaml.example`** - Example secrets template for all labs (sensitive information)
- **`config_loader.py`** - Centralized configuration loader with lab-specific extensions
- **`config_validator.py`** - Strict validation system that prevents dangerous default values

Each lab has its own `config_loader.py` that inherits from the centralized loader and provides lab-specific configuration methods.

### **Initial Setup**

Before running any labs, you need to create your configuration files:

```bash
# Copy the example configuration files
cp config.yaml.example config.yaml
cp secrets.yaml.example secrets.yaml

# Edit the files with your specific settings
# config.yaml - Update with your environment settings
# secrets.yaml - Update with your actual credentials
```

**Note:** Never commit your actual `config.yaml` or `secrets.yaml` files to version control. Only the `.example` files are tracked.

### **Strict Validation Philosophy**

**No Default Values Allowed** - This system prevents accidental use of potentially dangerous default values that could overwrite production data. All configuration values must be explicitly defined in the YAML files.

**Fail-Fast Approach** - If any required configuration is missing, the application will fail to start with clear error messages, preventing silent failures that could lead to data corruption.

## Safety System

Both Lab 1 and Lab 2 include comprehensive **dual-mode safety systems** to prevent accidental changes to production VAST systems:

### **🛡️ Dry Run Mode (Default)**
- **No actual changes** are made to the VAST system
- **Preview operations** before execution
- **Comprehensive safety checks** run automatically
- **Estimated results** are shown for all operations
- **Perfect for testing and validation**

### **🚀 Production Mode**
- **Explicit confirmation** required (`--pushtoprod` flag)
- **Actual changes** made to VAST views, storage, and metadata
- **User must type 'YES'** to confirm production operations
- **All safety checks must pass** before any changes
- **Comprehensive logging** of all operations

### **🔍 Safety Checks Performed**

#### **Lab 1: Storage Management Safety**
- View existence and permissions validation
- Monitoring system status verification
- Quota limits and backup status checks
- Network connectivity and system health validation
- Storage expansion impact assessment

#### **Lab 2: Metadata Catalog Safety**
- VAST system health and responsiveness
- View policy validation and conflicts
- Directory access and file count limits
- Storage impact estimation and capacity checks
- Processing capacity and backup status validation

### **📋 Command Line Usage**

```bash
# DRY RUN MODE (default - no changes)
python lab1/lab1_solution.py
python lab2/lab2_solution.py

# PRODUCTION MODE (actual changes - requires confirmation)
python lab1/lab1_solution.py --pushtoprod
python lab2/lab2_solution.py --pushtoprod

# Lab-specific operations
python lab1/lab1_solution.py --setup-only      # Only create views
python lab1/lab1_solution.py --monitor-only    # Only run monitoring
python lab2/lab2_solution.py --setup-only      # Only create schema
python lab2/lab2_solution.py --ingest-only     # Only ingest data
```

### **💡 Safety Philosophy**
- **"Look before you leap"** - Always preview operations first
- **"Fail safe"** - Better to block an operation than cause damage
- **"Explicit consent"** - Production changes require user confirmation
- **"Comprehensive validation"** - Multiple layers of safety checks

## Utilities

- **`test_login.py`** - Test script to verify VAST VMS connectivity and authentication
- **`test_config_validation.py`** - Test script to verify configuration validation system

## Installation

1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd lab-guides-2
   ```

2. **Install Python dependencies**
   ```bash
   # Install all dependencies (recommended)
   pip install -r requirements.txt
   
   # Or use the helper script
   python3 install_dependencies.py
   
   # Or install individually
   pip install pyyaml      # YAML configuration parsing
   pip install vastpy      # VAST Management System SDK
   pip install vastdb      # VAST Database SDK for metadata catalog
   ```

3. **Verify installation**
   ```bash
   # Test basic imports
   python3 lab1/test_basic_imports.py
   
   # Or test individually
   python -c "import yaml; print('pyyaml installed successfully')"
   python -c "import vastpy; print('vastpy installed successfully')"
   python -c "import vastdb; print('vastdb installed successfully')"
   ```

4. **Configure your environment**
   ```bash
   # Copy the example configuration files
   cp config.yaml.example config.yaml
   cp secrets.yaml.example secrets.yaml
   
   # Edit the files with your specific settings
   # config.yaml - Update with your environment settings
   # secrets.yaml - Update with your actual VAST credentials
   ```

## Lab Structure

Each lab follows a consistent structure:

1. **Problem Statement** - The business challenge and strategic planning needs
2. **Technical Challenge Overview** - Detailed objectives and requirements
3. **Implementation Guide** - Step-by-step technical instructions
4. **Success Criteria** - Measurable outcomes for each lab
5. **Business Impact** - Real-world benefits and outcomes

## Learning Objectives

By completing these labs, you will learn to:

- **Plan Proactively** - Design infrastructure that anticipates future needs rather than reacting to crises
- **Automate Infrastructure Management** - Use `vastpy` to programmatically manage storage, quotas, and monitoring
- **Build Data Catalogs** - Use `vastpy` to create organized storage structures and metadata systems
- **Orchestrate Data Pipelines** - Combine both SDKs for unified data processing workflows
- **Implement Version Control** - Use snapshots for systematic data versioning and recovery
- **Create Real-Time Systems** - Build event detection and alerting systems for time-critical operations

## Business Context

These labs are designed to mirror real-world challenges faced by organizations dealing with:

- **Proactive Infrastructure Planning** - Building systems before they're needed rather than during crises
- **High-Volume Data Processing** - Managing petabytes of incoming data
- **Multi-Source Data Integration** - Combining data from different sources and formats
- **Real-Time Requirements** - Processing and alerting on time-sensitive events
- **Compliance and Auditing** - Meeting regulatory and contractual requirements
- **Operational Efficiency** - Automating manual processes to scale operations

## Getting Started

1. **Choose Your Lab** - Start with Lab 1 if you're new to VAST SDKs, or jump to any lab that interests you
2. **Set Up Your Environment** - Ensure you have access to a VAST cluster and the required SDKs
3. **Follow the Story** - Read through the character interactions to understand the business context
4. **Implement the Solution** - Work through the technical challenges step by step
5. **Validate Results** - Use the success criteria to verify your implementation

## Support and Resources

- **VAST Documentation** - [https://vastdata.com/docs](https://vastdata.com/docs)
- **vastpy GitHub** - [https://github.com/vast-data/vastpy](https://github.com/vast-data/vastpy)
- **vastdb_sdk GitHub** - [https://github.com/vast-data/vastdb_sdk](https://github.com/vast-data/vastdb_sdk)
- **Community Support** - Join the VAST community for additional help and examples

## Contributing

These labs are designed to be educational and practical. If you find issues or have suggestions for improvements, please contribute by:

- Reporting bugs or unclear instructions
- Suggesting additional scenarios or challenges
- Improving code examples or explanations
- Adding new labs or expanding existing ones

---

*"In space exploration, preparation is everything. We build our data organization systems to handle the scale we expect, not the scale we hope to manage."* - Dr. Alex Sterling
