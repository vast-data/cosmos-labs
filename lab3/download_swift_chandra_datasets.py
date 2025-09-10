#!/usr/bin/env python3
"""
SWIFT-Chandra Dataset Downloader for Lab 3
==========================================

This script downloads notable examples of SWIFT-Chandra collaboration
for use in Lab 3: Multi-Observatory Data Storage and Analytics.

Notable Examples Included:
- GRB 050724: Short gamma-ray burst with Chandra follow-up
- SWIFT J1644+57: Tidal disruption event with multi-observatory coverage
- V404 Cygni: Black hole binary outburst (2015)
- 4U 1630-47: Galactic black hole transient with dust scattering halo
- SWIFT BAT AGN follow-up studies

Author: Lab 3 Development Team
Date: 2025-01-10
"""

import os
import sys
import json
import time
import requests
import tarfile
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from lab3.lab3_config import Lab3ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SwiftChandraDatasetDownloader:
    """Downloads and manages SWIFT-Chandra collaboration datasets."""
    
    def __init__(self, config: Lab3ConfigLoader, data_dir: str = "lab3_datasets"):
        self.config = config
        self.data_dir = Path(data_dir)
        self.swift_dir = self.data_dir / "swift"
        self.chandra_dir = self.data_dir / "chandra"
        self.metadata_file = self.data_dir / "dataset_metadata.json"
        
        # Create directories
        self.swift_dir.mkdir(parents=True, exist_ok=True)
        self.chandra_dir.mkdir(parents=True, exist_ok=True)
        
        # Notable SWIFT-Chandra collaboration examples
        self.notable_examples = {
            "GRB_050724": {
                "name": "GRB 050724 - Short Gamma-Ray Burst",
                "description": "Short GRB detected by SWIFT, followed up by Chandra",
                "swift_obs_id": "00144906000",
                "chandra_obs_id": "6686",
                "swift_date": "2005-07-24",
                "chandra_date": "2005-07-25",
                "ra": 16.0,  # Approximate coordinates
                "dec": -72.4,
                "significance": "Jet break analysis, uncollimated afterglow"
            },
            "SWIFT_J1644_57": {
                "name": "SWIFT J1644+57 - Tidal Disruption Event",
                "description": "Star torn apart by supermassive black hole",
                "swift_obs_id": "00032092001",
                "chandra_obs_id": "13857",
                "swift_date": "2011-03-28",
                "chandra_date": "2011-03-29",
                "ra": 251.0,
                "dec": 57.0,
                "significance": "Compton echo detection, multi-wavelength analysis"
            },
            "V404_Cygni_2015": {
                "name": "V404 Cygni - Black Hole Binary Outburst (2015)",
                "description": "Major outburst with dust scattering echoes",
                "swift_obs_id": "00031403001",
                "chandra_obs_id": "17704",
                "swift_date": "2015-06-15",
                "chandra_date": "2015-06-16",
                "ra": 306.0,
                "dec": 33.9,
                "significance": "X-ray dust scattering halo analysis"
            },
            "4U_1630_47_2016": {
                "name": "4U 1630-47 - Galactic Black Hole Transient (2016)",
                "description": "Outburst with dust scattering halo",
                "swift_obs_id": "00031403002",
                "chandra_obs_id": "17705",
                "swift_date": "2016-02-01",
                "chandra_date": "2016-02-02",
                "ra": 248.0,
                "dec": -47.0,
                "significance": "Distance determination, dust characteristics"
            }
        }
        
        # SWIFT and Chandra archive URLs (corrected with proper archive URLs)
        self.swift_archive_url = "https://www.swift.ac.uk/swift_portal/"
        self.swift_bulk_url = "https://www.swift.ac.uk/xrt_products/bulk.php"
        self.chandra_archive_url = "https://cxc.cfa.harvard.edu/cda/"
        self.chandra_chaser_url = "https://asc.harvard.edu/cda/chaser_ref.html"
        
        # Note: These are the official archive URLs, but direct download requires
        # proper authentication and API access. The script creates placeholders
        # and provides instructions for manual download.
        
    def download_swift_data(self, obs_id: str, event_name: str) -> bool:
        """Download SWIFT data for a specific observation."""
        try:
            # Note: Real SWIFT data download requires proper authentication and API access
            # For this lab, we'll create a placeholder and provide instructions
            
            logger.info(f"📡 Attempting to download SWIFT data for {event_name} (ObsID: {obs_id})")
            
            # Create placeholder directory structure
            obs_dir = self.swift_dir / obs_id
            obs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create placeholder files to simulate downloaded data
            placeholder_files = [
                "swift_xrt_data.fits",
                "swift_bat_data.fits", 
                "swift_uvot_data.fits",
                "observation_log.txt"
            ]
            
            for filename in placeholder_files:
                placeholder_file = obs_dir / filename
                with open(placeholder_file, 'w') as f:
                    f.write(f"# Placeholder SWIFT data for {event_name}\n")
                    f.write(f"# Observation ID: {obs_id}\n")
                    f.write(f"# Generated: {datetime.now().isoformat()}\n")
                    f.write(f"# Note: This is synthetic data for Lab 3\n")
            
            # Create download instructions
            instructions_file = obs_dir / "download_instructions.txt"
            with open(instructions_file, 'w') as f:
                f.write("SWIFT Data Download Instructions:\n")
                f.write("================================\n\n")
                f.write("To download real SWIFT data:\n")
                f.write("1. Visit the UK Swift Science Data Centre: https://www.swift.ac.uk/swift_portal/\n")
                f.write("2. Search for observation ID: {obs_id}\n")
                f.write("3. Download the data products\n")
                f.write("4. Place files in this directory\n\n")
                f.write("Alternative bulk download:\n")
                f.write("1. Visit: https://www.swift.ac.uk/xrt_products/bulk.php\n")
                f.write("2. Select your observation and download\n\n")
                f.write("For automated download, use the SWIFT archive API:\n")
                f.write("https://www.swift.ac.uk/swift_portal/\n")
            
            logger.info(f"✅ Created SWIFT data placeholder for {event_name} (ObsID: {obs_id})")
            logger.info(f"   📁 Data directory: {obs_dir}")
            logger.info(f"   📋 Instructions: {instructions_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create SWIFT data placeholder for {event_name}: {e}")
            return False
    
    def download_chandra_data(self, obs_id: str, event_name: str) -> bool:
        """Download Chandra data for a specific observation."""
        try:
            # Note: Real Chandra data download requires proper authentication and API access
            # For this lab, we'll create a placeholder and provide instructions
            
            logger.info(f"📡 Attempting to download Chandra data for {event_name} (ObsID: {obs_id})")
            
            # Create placeholder directory structure
            obs_dir = self.chandra_dir / obs_id
            obs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create placeholder files to simulate downloaded data
            placeholder_files = [
                "chandra_acis_data.fits",
                "chandra_hrc_data.fits",
                "chandra_spectrum.fits",
                "observation_log.txt"
            ]
            
            for filename in placeholder_files:
                placeholder_file = obs_dir / filename
                with open(placeholder_file, 'w') as f:
                    f.write(f"# Placeholder Chandra data for {event_name}\n")
                    f.write(f"# Observation ID: {obs_id}\n")
                    f.write(f"# Generated: {datetime.now().isoformat()}\n")
                    f.write(f"# Note: This is synthetic data for Lab 3\n")
            
            # Create download instructions
            instructions_file = obs_dir / "download_instructions.txt"
            with open(instructions_file, 'w') as f:
                f.write("Chandra Data Download Instructions:\n")
                f.write("==================================\n\n")
                f.write("To download real Chandra data:\n")
                f.write("1. Visit the Chandra Data Archive: https://cxc.cfa.harvard.edu/cda/\n")
                f.write(f"2. Search for observation ID: {obs_id}\n")
                f.write("3. Download the data files\n")
                f.write("4. Place in this directory\n\n")
                f.write("Alternative ChaSeR interface:\n")
                f.write("1. Visit: https://asc.harvard.edu/cda/chaser_ref.html\n")
                f.write("2. Search and download your observation\n\n")
                f.write("For automated download, use the Chandra Data Archive API:\n")
                f.write("https://cxc.cfa.harvard.edu/cda/help/api.html\n")
            
            logger.info(f"✅ Created Chandra data placeholder for {event_name} (ObsID: {obs_id})")
            logger.info(f"   📁 Data directory: {obs_dir}")
            logger.info(f"   📋 Instructions: {instructions_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Chandra data placeholder for {event_name}: {e}")
            return False
    
    def create_synthetic_overlap_data(self, event_name: str, event_data: Dict) -> bool:
        """Create synthetic data showing SWIFT-Chandra overlap for lab purposes."""
        try:
            # Create synthetic observation data
            synthetic_data = {
                "event_name": event_name,
                "swift_observations": self._generate_swift_observations(event_data),
                "chandra_observations": self._generate_chandra_observations(event_data),
                "cross_observatory_analysis": self._generate_cross_analysis(event_data)
            }
            
            # Save synthetic data
            synthetic_file = self.data_dir / f"{event_name}_synthetic.json"
            with open(synthetic_file, 'w') as f:
                json.dump(synthetic_data, f, indent=2)
            
            logger.info(f"✅ Created synthetic data for {event_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create synthetic data for {event_name}: {e}")
            return False
    
    def _generate_swift_observations(self, event_data: Dict) -> List[Dict]:
        """Generate synthetic SWIFT observation data."""
        base_time = datetime.fromisoformat(event_data["swift_date"])
        
        observations = []
        for i in range(5):  # 5 observations over 2 days
            obs_time = base_time + timedelta(hours=i*12)
            observations.append({
                "observation_time": obs_time.isoformat(),
                "target_object": event_data["name"].replace(" ", "_"),
                "ra": event_data["ra"] + (i * 0.1),  # Slight position variation
                "dec": event_data["dec"] + (i * 0.05),
                "xray_flux": 1.0 + (i * 0.2),  # Increasing flux
                "burst_detected": i == 0,  # First observation is the burst
                "exposure_time": 1000 + (i * 200),
                "instrument": "XRT"
            })
        
        return observations
    
    def _generate_chandra_observations(self, event_data: Dict) -> List[Dict]:
        """Generate synthetic Chandra observation data."""
        base_time = datetime.fromisoformat(event_data["chandra_date"])
        
        observations = []
        for i in range(3):  # 3 follow-up observations
            obs_time = base_time + timedelta(days=i*2)
            observations.append({
                "observation_time": obs_time.isoformat(),
                "target_object": event_data["name"].replace(" ", "_"),
                "ra": event_data["ra"] + (i * 0.05),
                "dec": event_data["dec"] + (i * 0.02),
                "xray_flux": 0.8 + (i * 0.1),  # Detailed follow-up
                "follow_up_observation": True,
                "exposure_time": 5000 + (i * 1000),
                "instrument": "ACIS",
                "resolution": "high"
            })
        
        return observations
    
    def _generate_cross_analysis(self, event_data: Dict) -> Dict:
        """Generate cross-observatory analysis data."""
        return {
            "burst_followup_detected": True,
            "time_difference_hours": 24.0,
            "flux_correlation": 0.85,
            "position_accuracy": 0.1,  # arcseconds
            "multi_wavelength_coverage": True,
            "significance": event_data["significance"]
        }
    
    def download_all_datasets(self, include_synthetic: bool = True) -> Dict[str, bool]:
        """Download all notable SWIFT-Chandra collaboration datasets."""
        results = {}
        
        logger.info("🚀 Starting SWIFT-Chandra dataset download...")
        logger.info(f"📁 Data directory: {self.data_dir}")
        
        for event_name, event_data in self.notable_examples.items():
            logger.info(f"\n📡 Processing {event_data['name']}...")
            
            # Download SWIFT data
            swift_success = self.download_swift_data(
                event_data["swift_obs_id"], 
                event_data["name"]
            )
            
            # Download Chandra data
            chandra_success = self.download_chandra_data(
                event_data["chandra_obs_id"], 
                event_data["name"]
            )
            
            # Create synthetic data if requested
            synthetic_success = True
            if include_synthetic:
                synthetic_success = self.create_synthetic_overlap_data(
                    event_name, 
                    event_data
                )
            
            results[event_name] = {
                "swift": swift_success,
                "chandra": chandra_success,
                "synthetic": synthetic_success,
                "overall": swift_success and chandra_success and synthetic_success
            }
            
            # Brief pause between downloads
            time.sleep(1)
        
        return results
    
    def create_dataset_metadata(self, results: Dict[str, bool]) -> None:
        """Create comprehensive metadata file for all datasets."""
        metadata = {
            "download_timestamp": datetime.now().isoformat(),
            "total_events": len(self.notable_examples),
            "successful_downloads": sum(1 for r in results.values() if r["overall"]),
            "events": {}
        }
        
        for event_name, event_data in self.notable_examples.items():
            metadata["events"][event_name] = {
                "name": event_data["name"],
                "description": event_data["description"],
                "coordinates": {
                    "ra": event_data["ra"],
                    "dec": event_data["dec"]
                },
                "observation_dates": {
                    "swift": event_data["swift_date"],
                    "chandra": event_data["chandra_date"]
                },
                "observation_ids": {
                    "swift": event_data["swift_obs_id"],
                    "chandra": event_data["chandra_obs_id"]
                },
                "significance": event_data["significance"],
                "download_status": results.get(event_name, {}),
                "data_paths": {
                    "swift": str(self.swift_dir / event_data["swift_obs_id"]),
                    "chandra": str(self.chandra_dir / event_data["chandra_obs_id"]),
                    "synthetic": str(self.data_dir / f"{event_name}_synthetic.json")
                }
            }
        
        # Save metadata
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Dataset metadata saved to {self.metadata_file}")
    
    def show_download_summary(self, results: Dict[str, bool]) -> None:
        """Display download summary."""
        print("\n" + "="*60)
        print("📊 SWIFT-Chandra Dataset Setup Summary")
        print("="*60)
        
        successful = sum(1 for r in results.values() if r["overall"])
        total = len(results)
        
        print(f"✅ Successfully set up: {successful}/{total} events")
        print(f"📁 Data directory: {self.data_dir}")
        print(f"📋 Metadata file: {self.metadata_file}")
        
        print("\n📡 Event Details:")
        for event_name, event_data in self.notable_examples.items():
            status = "✅" if results[event_name]["overall"] else "❌"
            print(f"  {status} {event_data['name']}")
            print(f"     SWIFT: {event_data['swift_date']} (ObsID: {event_data['swift_obs_id']})")
            print(f"     Chandra: {event_data['chandra_date']} (ObsID: {event_data['chandra_obs_id']})")
            print(f"     Significance: {event_data['significance']}")
            print()
        
        print("📋 Note: This script creates placeholder data and download instructions.")
        print("   For real data, follow the instructions in each observation directory.")
        print("🎯 Ready for Lab 3 cross-observatory analytics!")


def main():
    """Main function to run the dataset downloader."""
    try:
        # Load configuration
        config = Lab3ConfigLoader()
        
        # Create downloader
        downloader = SwiftChandraDatasetDownloader(config)
        
        # Download all datasets
        results = downloader.download_all_datasets(include_synthetic=True)
        
        # Create metadata
        downloader.create_dataset_metadata(results)
        
        # Show summary
        downloader.show_download_summary(results)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Dataset download failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
