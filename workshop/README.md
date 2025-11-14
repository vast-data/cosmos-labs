# VAST SDK Hands-On Workshop

## 🎯 Workshop Overview

This 2.25-hour hands-on workshop introduces participants to VAST Data's Python SDKs (`vastpy` and `vastdb`) through practical examples and real-world lab scenarios. Participants will learn to connect to VAST systems, manage storage infrastructure, and build data processing pipelines.

## 📁 Workshop Materials

- **[Workshop Outline](WORKSHOP_OUTLINE.md)** - Detailed 2.25-hour agenda with timing
- **[Presenter Script](PRESENTER_SCRIPT.md)** - Complete speaking notes and talking points
- **[Participant Guide](PARTICIPANT_GUIDE.md)** - Step-by-step instructions for attendees
- **[Main README](../README.md)** - Complete installation and setup guide
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 Learning Objectives

By the end of this workshop, participants will be able to:

1. **Connect to VAST Systems** - Use `vastpy` to establish connections and retrieve system information
2. **Monitor Storage Infrastructure** - Check quotas, view utilization, and monitor system health
3. **Manage Storage Views** - List, analyze, and understand storage view configurations
4. **Work with VAST Database** - Connect using `vastdb` and perform basic database operations
5. **Build Data Pipelines** - Create automated workflows for data processing and management
6. **Implement Snapshot Strategies** - Use protection policies and snapshots for version control and data recovery
7. **Implement Safety Practices** - Use dry-run modes and safety checks in production environments

## 🏗️ Workshop Structure

### **Part 1: VAST SDK Fundamentals (30 minutes)**
- Introduction to VAST Data and SDKs
- Connection setup and configuration
- Basic `vastpy` operations
- Introduction to `vastdb`

### **Part 2: Hands-On Examples (25 minutes)**
- Live demonstration of key examples
- Interactive exercises with participants
- Q&A and troubleshooting

### **Part 3: Lab Scenarios (65 minutes)**
- Walkthrough of Lab 1 (Storage Monitoring)
- Walkthrough of Lab 2 (Metadata Management)
- Walkthrough of Lab 3 (Weather Data Pipeline)
- Walkthrough of Lab 4 (Snapshot Strategy)
- Hands-on practice with read-only access

## 🛠️ Prerequisites

- **Python 3.7+** with basic programming experience
- **VAST cluster access** (read-only for participants)
- **Git** for cloning the repository
- **Basic terminal/command line** familiarity

## 📋 Pre-Workshop Setup

1. **Clone the repository**
2. **Install dependencies** (`pip install -r requirements.txt`)
3. **Configure access** (using provided configuration templates)
4. **Test connectivity** (using example scripts)

## 🎓 Target Audience

- **System Administrators** managing VAST infrastructure
- **Data Engineers** building data processing pipelines
- **Developers** integrating VAST systems into applications
- **DevOps Engineers** automating storage operations
- **Data Scientists** working with large-scale datasets

## 👨‍🏫 Instructor Guidance

### **Pre-Workshop Preparation**
- **Test all examples** in your environment before the workshop
- **Review participant backgrounds** and adjust pace accordingly
- **Prepare backup plans** for common technical issues
- **Set up test VAST cluster** if possible for hands-on practice
- **Review troubleshooting guide** for quick problem resolution

### **During the Workshop**
- **Start with audience survey** to gauge experience levels
- **Encourage questions** throughout, not just at the end
- **Use dry-run mode** for all lab demonstrations
- **Have backup examples** ready if participants finish early
- **Monitor participant progress** and adjust timing as needed

### **Common Challenges**
- **Connection issues** - Have troubleshooting steps ready
- **Different experience levels** - Pair beginners with experienced participants
- **Technical problems** - Use the troubleshooting guide and have backup plans
- **Time management** - Be flexible with timing, focus on learning over strict schedule

## 📞 Support

For questions or issues during the workshop:
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Ask questions during designated Q&A periods
- Use the provided example scripts for reference

---

*"The best way to learn VAST SDKs is by doing. This workshop provides hands-on experience with real-world scenarios that you'll encounter in production environments."*
