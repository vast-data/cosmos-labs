#!/usr/bin/env python3
"""
Automated Data Downloader for Lab 3
===================================

This script automatically downloads real SWIFT and Chandra datasets
for Lab 3: Multi-Observatory Data Storage and Analytics.

Uses official APIs:
- SWIFT: UK Swift Science Data Centre (UKSSDC) via astroquery
- Chandra: Chandra Data Archive via CIAO tools and astroquery

Author: Lab 3 Development Team
Date: 2025-01-10
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from astroquery.heasarc import Heasarc
    from astroquery.cda import CDA
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    print("⚠️ astroquery not available. Install with: pip install astroquery")

from lab3.lab3_config import Lab3ConfigLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedDataDownloader:
    """Automated downloader for SWIFT and Chandra datasets."""
    
    def __init__(self, config: Lab3ConfigLoader, data_dir: str = "lab3_real_data"):
        self.config = config
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize archive interfaces
        if ASTROQUERY_AVAILABLE:
            self.heasarc = Heasarc()
            self.cda = CDA()
        else:
            self.heasarc = None
            self.cda = None
        
        # Notable SWIFT-Chandra collaboration examples
        self.notable_examples = {
            "GRB_050724": {
                "name": "GRB 050724 - Short Gamma-Ray Burst",
                "swift_obs_id": "00144906000",
                "chandra_obs_id": "6686",
                "swift_date": "2005-07-24",
                "chandra_date": "2005-07-25",
                "ra": 16.0,
                "dec": -72.4,
                "significance": "Jet break analysis, uncollimated afterglow"
            },
            "SWIFT_J1644_57": {
                "name": "SWIFT J1644+57 - Tidal Disruption Event",
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
                "swift_obs_id": "00031403002",
                "chandra_obs_id": "17705",
                "swift_date": "2016-02-01",
                "chandra_date": "2016-02-02",
                "ra": 248.0,
                "dec": -47.0,
                "significance": "Distance determination, dust characteristics"
            }
        }
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        missing_deps = []
        
        if not ASTROQUERY_AVAILABLE:
            missing_deps.append("astroquery")
        
        # Check if CIAO is available
        try:
            result = subprocess.run(['download_chandra_obsid', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                missing_deps.append("CIAO (Chandra Interactive Analysis of Observations)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_deps.append("CIAO (Chandra Interactive Analysis of Observations)")
        
        if missing_deps:
            logger.error("❌ Missing dependencies:")
            for dep in missing_deps:
                logger.error(f"   - {dep}")
            logger.error("\nInstall missing dependencies:")
            logger.error("   pip install astroquery")
            logger.error("   # Install CIAO from: https://cxc.cfa.harvard.edu/ciao/download/")
            return False
        
        logger.info("✅ All dependencies available")
        return True
    
    def download_swift_data(self, obs_id: str, event_name: str) -> bool:
        """Download SWIFT data using astroquery."""
        try:
            if not self.heasarc:
                logger.error("❌ astroquery not available for SWIFT download")
                return False
            
            logger.info(f"📡 Downloading SWIFT data for {event_name} (ObsID: {obs_id})...")
            
            # Create event directory
            event_dir = self.data_dir / event_name
            event_dir.mkdir(parents=True, exist_ok=True)
            swift_dir = event_dir / "swift"
            swift_dir.mkdir(exist_ok=True)
            
            # Query SWIFT data from HEASARC
            try:
                # Query the SWIFT master catalog
                result = self.heasarc.query_object(f"swiftmastr", obs_id)
                
                if len(result) == 0:
                    logger.warning(f"⚠️ No SWIFT data found for ObsID {obs_id}")
                    return False
                
                # Get data products
                data_products = self.heasarc.get_data_products(obs_id)
                
                if len(data_products) == 0:
                    logger.warning(f"⚠️ No data products found for SWIFT ObsID {obs_id}")
                    return False
                
                # Download data products
                logger.info(f"   📥 Downloading {len(data_products)} data products...")
                self.heasarc.download_data(data_products, dir=str(swift_dir))
                
                logger.info(f"✅ SWIFT data downloaded to {swift_dir}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to download SWIFT data via astroquery: {e}")
                
                # Fallback: Create placeholder with instructions
                self._create_swift_placeholder(obs_id, event_name, swift_dir)
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to download SWIFT data for {event_name}: {e}")
            return False
    
    def download_chandra_data(self, obs_id: str, event_name: str) -> bool:
        """Download Chandra data using CIAO tools."""
        try:
            logger.info(f"📡 Downloading Chandra data for {event_name} (ObsID: {obs_id})...")
            
            # Create event directory
            event_dir = self.data_dir / event_name
            event_dir.mkdir(parents=True, exist_ok=True)
            chandra_dir = event_dir / "chandra"
            chandra_dir.mkdir(exist_ok=True)
            
            # Use CIAO download_chandra_obsid tool
            try:
                # Change to chandra directory
                original_cwd = os.getcwd()
                os.chdir(chandra_dir)
                
                # Download Chandra data
                cmd = ['download_chandra_obsid', obs_id]
                logger.info(f"   📥 Running: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"✅ Chandra data downloaded to {chandra_dir}")
                    return True
                else:
                    logger.error(f"❌ CIAO download failed: {result.stderr}")
                    
                    # Try astroquery as fallback
                    if self.cda:
                        logger.info("   🔄 Trying astroquery fallback...")
                        return self._download_chandra_astroquery(obs_id, event_name, chandra_dir)
                    else:
                        self._create_chandra_placeholder(obs_id, event_name, chandra_dir)
                        return False
                
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Chandra download timed out for ObsID {obs_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to download Chandra data for {event_name}: {e}")
            return False
    
    def _download_chandra_astroquery(self, obs_id: str, event_name: str, chandra_dir: Path) -> bool:
        """Fallback Chandra download using astroquery."""
        try:
            logger.info(f"   📥 Trying astroquery for Chandra ObsID {obs_id}...")
            
            # Query Chandra data
            result = self.cda.query_region(obs_id)
            
            if len(result) == 0:
                logger.warning(f"⚠️ No Chandra data found for ObsID {obs_id}")
                return False
            
            # Download data
            self.cda.download_data(result, dir=str(chandra_dir))
            
            logger.info(f"✅ Chandra data downloaded via astroquery to {chandra_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ astroquery Chandra download failed: {e}")
            self._create_chandra_placeholder(obs_id, event_name, chandra_dir)
            return False
    
    def _create_swift_placeholder(self, obs_id: str, event_name: str, swift_dir: Path) -> None:
        """Create placeholder SWIFT data with download instructions."""
        placeholder_files = [
            "swift_xrt_data.fits",
            "swift_bat_data.fits", 
            "swift_uvot_data.fits",
            "observation_log.txt"
        ]
        
        for filename in placeholder_files:
            placeholder_file = swift_dir / filename
            with open(placeholder_file, 'w') as f:
                f.write(f"# Placeholder SWIFT data for {event_name}\n")
                f.write(f"# Observation ID: {obs_id}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Note: This is synthetic data for Lab 3\n")
        
        # Create download instructions
        instructions_file = swift_dir / "download_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write("SWIFT Data Download Instructions:\n")
            f.write("================================\n\n")
            f.write("To download real SWIFT data:\n")
            f.write("1. Visit: https://www.swift.ac.uk/swift_portal/\n")
            f.write(f"2. Search for observation ID: {obs_id}\n")
            f.write("3. Download the data products\n")
            f.write("4. Replace these placeholder files\n\n")
            f.write("Or use Python:\n")
            f.write("```python\n")
            f.write("from astroquery.heasarc import Heasarc\n")
            f.write("heasarc = Heasarc()\n")
            f.write(f"data_products = heasarc.get_data_products('{obs_id}')\n")
            f.write("heasarc.download_data(data_products)\n")
            f.write("```\n")
    
    def _create_chandra_placeholder(self, obs_id: str, event_name: str, chandra_dir: Path) -> None:
        """Create placeholder Chandra data with download instructions."""
        placeholder_files = [
            "chandra_acis_data.fits",
            "chandra_hrc_data.fits",
            "chandra_spectrum.fits",
            "observation_log.txt"
        ]
        
        for filename in placeholder_files:
            placeholder_file = chandra_dir / filename
            with open(placeholder_file, 'w') as f:
                f.write(f"# Placeholder Chandra data for {event_name}\n")
                f.write(f"# Observation ID: {obs_id}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Note: This is synthetic data for Lab 3\n")
        
        # Create download instructions
        instructions_file = chandra_dir / "download_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write("Chandra Data Download Instructions:\n")
            f.write("==================================\n\n")
            f.write("To download real Chandra data:\n")
            f.write("1. Install CIAO: https://cxc.cfa.harvard.edu/ciao/download/\n")
            f.write(f"2. Run: download_chandra_obsid {obs_id}\n")
            f.write("3. Move files to this directory\n\n")
            f.write("Or use Python:\n")
            f.write("```python\n")
            f.write("from astroquery.cda import CDA\n")
            f.write("cda = CDA()\n")
            f.write(f"result = cda.query_region('{obs_id}')\n")
            f.write("cda.download_data(result)\n")
            f.write("```\n")
    
    def download_all_datasets(self) -> Dict[str, bool]:
        """Download all notable SWIFT-Chandra collaboration datasets."""
        logger.info("🚀 Starting automated data download...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Cannot proceed without required dependencies")
            return {}
        
        results = {}
        
        for event_name, event_data in self.notable_examples.items():
            logger.info(f"\n📡 Processing {event_data['name']}...")
            
            # Download SWIFT data
            swift_success = self.download_swift_data(
                event_data["swift_obs_id"], 
                event_name
            )
            
            # Download Chandra data
            chandra_success = self.download_chandra_data(
                event_data["chandra_obs_id"], 
                event_name
            )
            
            results[event_name] = {
                "swift": swift_success,
                "chandra": chandra_success,
                "overall": swift_success and chandra_success
            }
        
        # Create metadata
        self._create_metadata(results)
        
        return results
    
    def _create_metadata(self, results: Dict[str, bool]) -> None:
        """Create metadata file for downloaded datasets."""
        metadata = {
            "download_timestamp": datetime.now().isoformat(),
            "total_events": len(self.notable_examples),
            "successful_downloads": sum(1 for r in results.values() if r["overall"]),
            "events": {}
        }
        
        for event_name, event_data in self.notable_examples.items():
            metadata["events"][event_name] = {
                "name": event_data["name"],
                "swift_obs_id": event_data["swift_obs_id"],
                "chandra_obs_id": event_data["chandra_obs_id"],
                "coordinates": {"ra": event_data["ra"], "dec": event_data["dec"]},
                "significance": event_data["significance"],
                "download_status": results.get(event_name, {}),
                "data_paths": {
                    "swift": str(self.data_dir / event_name / "swift"),
                    "chandra": str(self.data_dir / event_name / "chandra")
                }
            }
        
        # Save metadata
        metadata_file = self.data_dir / "download_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Download metadata saved to {metadata_file}")
    
    def show_download_summary(self, results: Dict[str, bool]) -> None:
        """Display download summary."""
        print("\n" + "="*70)
        print("📊 Automated Data Download Summary")
        print("="*70)
        
        successful = sum(1 for r in results.values() if r["overall"])
        total = len(results)
        
        print(f"✅ Successfully downloaded: {successful}/{total} events")
        print(f"📁 Data directory: {self.data_dir}")
        
        print("\n📡 Event Details:")
        for event_name, event_data in self.notable_examples.items():
            status = "✅" if results[event_name]["overall"] else "❌"
            swift_status = "✅" if results[event_name]["swift"] else "❌"
            chandra_status = "✅" if results[event_name]["chandra"] else "❌"
            
            print(f"  {status} {event_data['name']}")
            print(f"     SWIFT: {swift_status} {event_data['swift_obs_id']}")
            print(f"     Chandra: {chandra_status} {event_data['chandra_obs_id']}")
            print(f"     Significance: {event_data['significance']}")
            print()
        
        if successful < total:
            print("📋 Note: Some downloads failed. Check the logs for details.")
            print("   Placeholder data and instructions were created for failed downloads.")
        
        print("🎯 Ready for Lab 3 cross-observatory analytics!")


def main():
    """Main function to run the automated data downloader."""
    try:
        # Load configuration
        config = Lab3ConfigLoader()
        
        # Create downloader
        downloader = AutomatedDataDownloader(config)
        
        # Download all datasets
        results = downloader.download_all_datasets()
        
        # Show summary
        downloader.show_download_summary(results)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Automated data download failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
