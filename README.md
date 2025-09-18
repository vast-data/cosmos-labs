# Orbital Dynamics: Hands-On Labs with VAST SDKs

## Welcome to Orbital Dynamics

*"Where complex systems find their orbit"*

Orbital Dynamics is a mid-sized space technology company that processes astronomical data and manages satellite constellation networks for research institutions, government agencies, and private space companies. They've recently landed a major NASA contract for real-time processing of deep space telescope data, which is pushing their infrastructure to new limits.

This series of hands-on labs follows the journey of the Orbital Dynamics team as they tackle real-world challenges using the VAST Management System and VAST Database. Through these labs, you'll learn how to use `vastpy` and `vastdb` to solve complex data management and processing problems in a space technology environment.

## ⚠️ Important Disclaimer

**This repository contains educational code and examples only. All code, scripts, and configurations are provided for learning and demonstration purposes. They are NOT intended for production use and should NOT be deployed in production environments without proper review, testing, and modification.**

- **Educational Purpose Only** - These labs are designed to teach VAST SDK concepts
- **Review Before Use** - Always review and test any code before using it in your environment

## The Team

Meet the characters who will guide you through these challenges:

- **Dr. Alex Sterling (CTO)** - Former JPL engineer who understands the domain and drives the company's technical vision
- **Maya Chen (Lead SysAdmin)** - Gaming industry veteran adapting to space-scale challenges
- **Jordan Blake (Senior Developer)** - Brilliant but sometimes gets lost in technical details
- **Sam Rodriguez (DevOps Engineer)** - The alignment specialist who bridges dev and ops
- **Mac Thompson (Junior Admin)** - Eager learner prone to educational mistakes

## Lab Overview

### [Lab 1: Storage Monitoring & Auto-Expansion](Lab_1_Satellite_Data_Infrastructure_Planning.md)
**Challenge:** Monitor existing storage infrastructure and automatically expand quotas when needed
- Use `vastpy` to monitor storage utilization across multiple views
- Build automated quota expansion with comprehensive safety checks
- Create basic predictive scaling systems that prevent storage crises
- Implement real-time monitoring and alerting for storage health
- **Focus:** Monitoring existing infrastructure, not creating new views

### [Lab 2: Metadata Database & Search System](Lab_2_Metadata_Infrastructure_Project.md)
**Challenge:** Build a comprehensive metadata database system for efficient data discovery and management
- Use `vastdb` to create and manage VAST databases
- Build automated metadata extraction workflows for various file formats (FITS, JSON, etc.)
- Create powerful search interfaces with wildcard and date range support
- **Focus:** Metadata management and search capabilities

### [Lab 3: Weather Data Pipeline & Analytics](lab3/README.md)
**Challenge:** Build a complete weather data pipeline with advanced analytics and health impact assessment
- Download weather and air quality data from Open-Meteo API for global cities
- Store and manage large-scale weather datasets in VAST Database using `vastdb`
- Perform advanced correlation analysis between weather patterns and air quality metrics
- Detect dangerous pollution episodes and health risk situations using WHO guidelines
- Analyze long-term trends and seasonal patterns across multiple cities
- **Focus:** Real-time data ingestion, scalable storage, and advanced analytics

## Upcoming labs

### [Lab 4: The Snapshot Strategy](Lab_4_Snapshot_Strategy.md)
**Challenge:** Implement systematic version control for research datasets
- Use `vastpy` to implement automated snapshot policies
- Build named snapshot workflows for key milestones
- Create tools for browsing and restoring from snapshots
- Establish systematic version tracking and management

### [Lab 5: The Real-Time Alert System](Lab_5_Real_Time_Alert_System.md)
**Challenge:** Detect astronomical events in real-time and alert appropriate teams
- Use `vastdb` for real-time data ingestion and analysis
- Build automated detection for specific astronomical events
- Create multi-level alerting based on event type and urgency
- Develop APIs for external system integration

### [Lab 6: Pipeline Storage Integration](lab6/README.md)
**Challenge:** Integrate storage validation and management with data processing pipelines
- Build pre-processing storage availability checks
- Create interactive storage expansion for processing workflows
- Integrate storage validation with processing scripts
- Provide seamless storage management for data processing jobs

## Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/vast-data/cosmos-labs
   cd cosmos-labs
   ```

2. **Install Python dependencies**
   ```bash
   # Install all dependencies (recommended)
   pip install -r requirements.txt
   
   # Or use the helper script for guided installation
   python3 install_dependencies.py
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

## Prerequisites

- **Python 3.7+** with basic programming experience
- **VAST Management System cluster** access
- **Git** for version control
- **vastpy** and **vastdb** SDKs (installed via requirements.txt)

## Configuration Management

This repository uses a centralized configuration approach with **strict validation**:

- **`config.yaml.example`** - Example configuration template for all labs (non-sensitive settings)
- **`secrets.yaml.example`** - Example secrets template for all labs (sensitive information)
- **`config_loader.py`** - Centralized configuration loader with lab-specific extensions
- **`config_validator.py`** - Strict validation system that prevents dangerous default values

Each lab has its own `config_loader.py` that inherits from the centralized loader and provides lab-specific configuration methods.

### **Initial Setup**

After installing the dependencies (see Installation section above), you need to create your configuration files:

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

All labs include comprehensive **dual-mode safety systems** to prevent accidental changes to production VAST systems:

- **🛡️ Dry Run Mode (Default)** - Preview operations without making changes
- **🚀 Production Mode** - Requires explicit confirmation (`--pushtoprod` flag)
- **🔍 Comprehensive Safety Checks** - Multiple validation layers before any changes

See individual lab READMEs for detailed safety information and command-line usage.

## Utilities

- **`test_login.py`** - Test script to verify VAST VMS connectivity and authentication
- **`test_config_validation.py`** - Test script to verify configuration validation system


## Lab Structure

Each lab follows a consistent structure:

1. **Problem Statement** - The business challenge and strategic planning needs
2. **Technical Challenge Overview** - Detailed objectives and requirements
3. **Implementation Guide** - Step-by-step technical instructions
4. **Success Criteria** - Measurable outcomes for each lab
5. **Business Impact** - Real-world benefits and outcomes

## Learning Objectives

By completing these labs, you will learn to:

- **Monitor Infrastructure Proactively** - Use `vastpy` to monitor storage utilization and prevent crises
- **Automate Quota Management** - Build intelligent quota expansion with comprehensive safety checks
- **Build Metadata Catalogs** - Use `vastdb` to create searchable metadata systems for data discovery
- **Implement Advanced Search** - Create powerful search interfaces with wildcards and date ranges
- **Build Data Ingestion Pipelines** - Create robust systems for downloading and storing large-scale datasets
- **Perform Advanced Analytics** - Use `vastdb` for correlation analysis and pattern detection in time-series data
- **Analyze Long-Term Trends** - Process and analyze multi-year datasets for historical pattern recognition
- **Orchestrate Data Pipelines** - Combine both SDKs for unified data processing workflows
- **Implement Version Control** - Use snapshots for systematic data versioning and recovery
- **Create Real-Time Systems** - Build event detection and alerting systems for time-critical operations
- **Integrate Pipeline Storage** - Build storage validation and management for data processing workflows

## Business Context

These labs are designed to mirror real-world challenges faced by organizations dealing with:

- **Proactive Infrastructure Monitoring** - Monitoring existing systems to prevent crises rather than reacting to them
- **Intelligent Quota Management** - Automatically expanding storage before it becomes critical
- **Metadata-Driven Data Discovery** - Building searchable catalogs for efficient data management
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

- **VAST Documentation** - [https://support.vastdata.com/s/](https://support.vastdata.com/s/)
- **vastpy GitHub** - [https://github.com/vast-data/vastpy](https://github.com/vast-data/vastpy)
- **vastdb GitHub** - [https://github.com/vast-data/vastdb_sdk](https://github.com/vast-data/vastdb_sdk)
- **Community Support** - Join the VAST community for additional help and examples

## Contributing

These labs are designed to be educational and practical. If you find issues or have suggestions for improvements, please contribute by:

- Reporting bugs or unclear instructions
- Suggesting additional scenarios or challenges
- Improving code examples or explanations
- Adding new labs or expanding existing ones

---

*"In space exploration, preparation is everything. We build our data organization systems to handle the scale we expect, not the scale we hope to manage."* - Dr. Alex Sterling
