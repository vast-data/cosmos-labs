# Lab 4: The Snapshot Strategy

## Problem Statement

As Orbital Dynamics prepares for the launch of additional satellite constellations and increased research collaboration with NASA, Dr. Alex Sterling recognizes that the current manual data versioning approach won't scale. When researchers need to roll back to previous versions of their processed datasets (like when they discover a calibration error affected a week's worth of analysis), Maya Chen's team has been manually copying entire directories and hoping they can find the right version later. This approach will become unsustainable as data volumes grow and more researchers join the team.

**The Strategic Need:** With multiple satellite constellations coming online and increased collaboration with NASA, there's no systematic way to track dataset versions or quickly revert to known-good states. Researchers will lose valuable time trying to locate previous versions of their work, and the manual backup approach is both unreliable and unscalable. NASA is demanding better data versioning and recovery capabilities, and we need to implement this before the complexity becomes overwhelming.

## Character Interactions

### Scene 1: Strategic Planning Session
*Location: Dr. Sterling's Office, 2:00 PM*

**Dr. Alex Sterling (CTO):** "Maya, I'm reviewing our data management practices for the upcoming expansion, and I'm concerned about our version control strategy. How do we handle situations where researchers need to roll back to previous versions of their datasets?"

**Maya Chen (Lead SysAdmin):** "Well, Alex, we've been using a manual approach. When someone needs a previous version, we copy the entire directory to a backup location with a timestamp. It's worked so far, but I'm worried about scaling this approach."

**Dr. Sterling:** "Exactly. With COSMOS-7 running and two more constellations coming online, plus increased NASA collaboration, this manual approach will become a bottleneck. What happens when we have 10 researchers all needing different versions simultaneously?"

**Maya:** "That's the problem. We rely on researchers to remember when they made changes, and we hope the timestamps are accurate. It's not very systematic, and it won't scale."

### Scene 2: The Solution Design
*Location: Conference Room, 10:00 AM*

**Sam Rodriguez (DevOps Engineer):** "I think I have a solution. The VAST Management System has built-in protection policies and snapshot capabilities. We can use `vastpy` to implement systematic snapshot policies that automatically capture dataset states at key milestones."

**Jordan Blake (Senior Developer):** "How would that work? Won't it consume a lot of storage space?"

**Sam:** "VAST protection policies are space-efficient. They only store the differences between versions, not full copies. We can create protection policies with schedules like:
- Daily snapshots with 7-day retention for recent work
- Weekly snapshots with 30-day retention for milestones
- Monthly snapshots with 90-day retention for major releases
- On-demand snapshots with descriptive names for specific events"

**Mac Thompson (Junior Admin):** "So instead of manually copying directories, the system automatically creates snapshots that we can browse and restore from?"

**Maya:** "Exactly. And we can create named snapshots with descriptive labels like 'pre-calibration-change' or 'post-processing-complete' so researchers can easily find what they need."

**Dr. Sterling:** "This sounds like exactly what NASA is asking for. They want systematic version control and the ability to reproduce research results from specific data states."

### Scene 3: Implementation Planning
*Location: Sam's Workspace, 3:00 PM*

**Dr. Sterling:** "Sam, this is exactly what we need. NASA is already asking about our data versioning capabilities, and we need to demonstrate this before the new satellites launch."

**Sam:** "We have a 4-month window to implement this system. That gives us time to design it properly and ensure it's robust before we're under pressure."

**Maya:** "And we can use the COSMOS-7 data as our testbed while we develop the system. That way we're ready when the new constellations come online."

**Jordan:** "This will be crucial for research reproducibility too. When we publish results, we can point to specific snapshots that contain the exact data used in our analysis."

**Mac:** "I'm excited to learn about protection policies. This seems like a much more professional approach than our current manual backups."

### Scene 4: The Technical Deep Dive
*Location: Lab 4 Development Environment, 1:00 PM*

**Sam:** "Let me show you how VAST protection policies work. We can create policies with different schedules and retention periods."

**Jordan:** "So we can have a policy that takes snapshots every 6 hours but only keeps them for 3 days, and another that takes weekly snapshots but keeps them for 3 months?"

**Sam:** "Exactly! And we can apply different policies to different views based on their importance and change frequency. For example:
- Raw data views: Daily snapshots, 7-day retention
- Processed data views: Every 4 hours, 3-day retention  
- Analysis results: Weekly snapshots, 30-day retention
- Published datasets: Monthly snapshots, 1-year retention"

**Maya:** "This gives us much more granular control than our current approach. We can optimize storage usage while ensuring we have the right level of protection for each type of data."

**Mac:** "And researchers can still create manual snapshots when they need them, right?"

**Sam:** "Absolutely. We'll build tools that let researchers create named snapshots with descriptive labels, and they can browse all available snapshots to find exactly what they need."

### Scene 5: The Business Case
*Location: Executive Conference Room, 4:00 PM*

**Dr. Sterling:** "Maya, can you walk us through the business impact of implementing this snapshot strategy?"

**Maya:** "The benefits are significant:
- **Research Efficiency**: Researchers can quickly revert to previous states instead of spending hours searching for backups
- **NASA Compliance**: We'll meet their data versioning and reproducibility requirements
- **Storage Optimization**: Space-efficient snapshots instead of full directory copies
- **Operational Scalability**: Automated policies that work regardless of team size
- **Risk Mitigation**: Systematic protection against data loss and corruption"

**Sam:** "And from a technical perspective, this positions us perfectly for the upcoming expansion. When the new constellations come online, we'll already have robust data versioning in place."

**Jordan:** "This will also help with our research publications. We can reference specific snapshot versions in our papers, making our work more reproducible and credible."

**Dr. Sterling:** "Excellent. This is exactly the kind of forward-thinking infrastructure we need. Let's implement this system and make it a model for the industry."

## Technical Challenge Overview

### Primary Objectives:
1. **Implement VAST Protection Policies** - Use `vastpy` to create automated snapshot policies with configurable schedules and retention
2. **Build Named Snapshot Workflows** - Create tools for creating descriptive, searchable snapshots at key processing milestones
3. **Develop Recovery Tools** - Build interfaces for researchers to easily browse and restore from snapshots
4. **Establish Version Tracking** - Create a systematic approach to tracking dataset versions and changes

### Key Technical Components:

#### 1. Protection Policy Implementation
- Use `vastpy` to create VAST protection policies:
  - **Time-based policies:** Daily, weekly, monthly automatic captures with configurable retention
  - **Event-based policies:** Triggered by processing milestones and calibration changes
  - **Manual snapshots:** On-demand captures with descriptive names and custom retention
- Implement policy hierarchies for different data types and importance levels
- Create policy templates for common use cases

#### 2. Named Snapshot Workflows
- Build workflows for creating descriptive snapshots:
  - **Processing milestones:** "post-cosmos7-processing-complete"
  - **Calibration events:** "pre-mars-calibration-change"
  - **Research phases:** "asteroid-tracking-phase-1-complete"
  - **System events:** "pre-maintenance-window"
- Implement metadata tagging for easy searching and filtering
- Create snapshot naming conventions and validation

#### 3. Recovery and Restoration Tools
- Create user-friendly interfaces for:
  - Browsing available snapshots with descriptive names and metadata
  - Comparing snapshot contents and timestamps
  - Restoring datasets to previous states with dry-run capabilities
  - Rolling back specific changes while preserving others
- Build APIs for integration with existing research tools
- Implement batch operations for multiple dataset restoration

#### 4. Version Tracking and Management
- Implement systematic version tracking:
  - Automatic version numbering for datasets
  - Change logs documenting what changed between versions
  - Dependency tracking for related datasets
  - Audit trails for all snapshot operations
- Create tools for researchers to understand dataset evolution
- Build reporting and analytics for snapshot usage patterns

## Implementation Timeline

### Phase 1 (Months 1-2): Foundation
- Design protection policy architecture using VAST APIs
- Implement basic automated protection policies
- Create snapshot metadata and tagging system
- Build core snapshot management tools

### Phase 2 (Months 3-4): User Interface
- Build snapshot browsing and search tools
- Develop restoration and rollback capabilities
- Create integration APIs for research tools
- Implement named snapshot workflows

### Phase 3 (Months 5-6): Advanced Features
- Add version tracking and change logging
- Performance optimization and testing
- Advanced analytics and reporting
- Integration with existing lab workflows

## Success Criteria

1. **Systematic Version Control** - All datasets have systematic version tracking and recovery capabilities using VAST protection policies
2. **Easy Recovery** - Researchers can find and restore previous versions in under 5 minutes using intuitive tools
3. **Space Efficiency** - Snapshot storage overhead is minimal (less than 10% of original data) through VAST's efficient snapshot technology
4. **User-Friendly Interface** - Intuitive tools for browsing and restoring snapshots with descriptive names and metadata
5. **Automated Policies** - Snapshots are created automatically at key milestones using configurable protection policies

## Business Impact

- **Proactive Data Management** - System ready for increased data volumes and research collaboration
- **Research Reproducibility** - Researchers can easily access exact data versions used in published work
- **Operational Efficiency** - Eliminate time spent searching for previous dataset versions
- **NASA Compliance** - Meet data versioning and recovery requirements with enterprise-grade solutions
- **Competitive Advantage** - Position Orbital Dynamics as a leader in research data management
- **Storage Cost Optimization** - Efficient snapshot technology reduces storage overhead compared to manual backups

## Risk Mitigation

- **Early Testing** - Use COSMOS-7 data as testbed while developing system
- **Gradual Rollout** - Implement protection policies incrementally to validate approach
- **Performance Monitoring** - Continuous monitoring to ensure snapshot overhead remains minimal
- **User Training** - Provide training to researchers on new snapshot workflows before full deployment
- **Backup Validation** - Ensure restoration capabilities work correctly before relying on snapshots
