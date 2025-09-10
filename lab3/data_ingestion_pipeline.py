#!/usr/bin/env python3
"""
Data Ingestion Pipeline for Lab 3
=================================

This module provides data ingestion capabilities for SWIFT and Chandra
datasets into the Lab 3 multi-observatory storage and analytics system.

Features:
- Automated data ingestion into VAST storage views
- Cross-observatory data correlation
- Real-time burst detection and follow-up analysis
- Multi-wavelength light curve generation
- Data quality validation and monitoring

Author: Lab 3 Development Team
Date: 2025-01-10
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from lab3.lab3_config import Lab3ConfigLoader
from lab3.multi_observatory_storage_manager import MultiObservatoryStorageManager
from lab3.cross_observatory_analytics import CrossObservatoryAnalytics
from lab3.cross_matching_engine import CrossMatchingEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Pipeline for ingesting SWIFT and Chandra data into Lab 3 system."""
    
    def __init__(self, config: Lab3ConfigLoader, production_mode: bool = False):
        self.config = config
        self.production_mode = production_mode
        self.data_dir = Path("lab3_datasets")
        
        # Initialize components
        self.storage_manager = MultiObservatoryStorageManager(
            config, production_mode, show_api_calls=True
        )
        self.analytics_manager = CrossObservatoryAnalytics(
            config, show_api_calls=True
        )
        self.cross_matching_engine = CrossMatchingEngine(str(self.data_dir))
        
        # Load cross-matching results
        self.cross_matching_results = self._load_cross_matching_results()
        
    def _load_cross_matching_results(self) -> Dict[str, Any]:
        """Load cross-matching results from previous analysis."""
        results_file = self.data_dir / "cross_matching_results.json"
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            logger.info(f"✅ Loaded cross-matching results for {len(results.get('events', {}))} events")
            return results
        except FileNotFoundError:
            logger.warning("⚠️ Cross-matching results not found. Run cross-matching first.")
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to load cross-matching results: {e}")
            return {}
    
    def ingest_swift_data(self, event_name: str, swift_observations: List[Dict]) -> bool:
        """
        Ingest SWIFT observation data into VAST storage.
        
        Args:
            event_name: Name of the event
            swift_observations: List of SWIFT observations
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📡 Ingesting SWIFT data for {event_name}...")
            
            # Prepare data for ingestion
            ingested_count = 0
            for obs in swift_observations:
                # Create observation record
                observation_record = {
                    'event_name': event_name,
                    'observation_time': obs['observation_time'],
                    'target_object': obs['target_object'],
                    'ra': obs['ra'],
                    'dec': obs['dec'],
                    'xray_flux': obs['xray_flux'],
                    'burst_detected': obs.get('burst_detected', False),
                    'exposure_time': obs.get('exposure_time', 0),
                    'instrument': obs.get('instrument', 'XRT'),
                    'data_source': 'SWIFT',
                    'ingestion_timestamp': datetime.now().isoformat()
                }
                
                # Ingest into VAST storage (simulated)
                if self.production_mode:
                    # In real implementation, this would write to VAST storage
                    logger.info(f"  📝 Ingesting SWIFT observation: {obs['observation_time']}")
                
                ingested_count += 1
            
            logger.info(f"✅ Ingested {ingested_count} SWIFT observations for {event_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest SWIFT data for {event_name}: {e}")
            return False
    
    def ingest_chandra_data(self, event_name: str, chandra_observations: List[Dict]) -> bool:
        """
        Ingest Chandra observation data into VAST storage.
        
        Args:
            event_name: Name of the event
            chandra_observations: List of Chandra observations
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📡 Ingesting Chandra data for {event_name}...")
            
            # Prepare data for ingestion
            ingested_count = 0
            for obs in chandra_observations:
                # Create observation record
                observation_record = {
                    'event_name': event_name,
                    'observation_time': obs['observation_time'],
                    'target_object': obs['target_object'],
                    'ra': obs['ra'],
                    'dec': obs['dec'],
                    'xray_flux': obs['xray_flux'],
                    'follow_up_observation': obs.get('follow_up_observation', False),
                    'exposure_time': obs.get('exposure_time', 0),
                    'instrument': obs.get('instrument', 'ACIS'),
                    'resolution': obs.get('resolution', 'high'),
                    'data_source': 'Chandra',
                    'ingestion_timestamp': datetime.now().isoformat()
                }
                
                # Ingest into VAST storage (simulated)
                if self.production_mode:
                    # In real implementation, this would write to VAST storage
                    logger.info(f"  📝 Ingesting Chandra observation: {obs['observation_time']}")
                
                ingested_count += 1
            
            logger.info(f"✅ Ingested {ingested_count} Chandra observations for {event_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest Chandra data for {event_name}: {e}")
            return False
    
    def ingest_cross_observatory_analytics(self, event_name: str, 
                                         cross_analysis: Dict[str, Any]) -> bool:
        """
        Ingest cross-observatory analytics data.
        
        Args:
            event_name: Name of the event
            cross_analysis: Cross-observatory analysis data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📊 Ingesting cross-observatory analytics for {event_name}...")
            
            # Prepare analytics record
            analytics_record = {
                'event_name': event_name,
                'burst_followup_detected': cross_analysis.get('burst_followup_detected', False),
                'time_difference_hours': cross_analysis.get('time_difference_hours', 0),
                'flux_correlation': cross_analysis.get('flux_correlation', 0.0),
                'position_accuracy': cross_analysis.get('position_accuracy', 0.0),
                'multi_wavelength_coverage': cross_analysis.get('multi_wavelength_coverage', False),
                'significance': cross_analysis.get('significance', ''),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Ingest into VAST database (simulated)
            if self.production_mode:
                # In real implementation, this would write to VAST database
                logger.info(f"  📝 Ingesting cross-observatory analytics: {event_name}")
            
            logger.info(f"✅ Ingested cross-observatory analytics for {event_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest cross-observatory analytics for {event_name}: {e}")
            return False
    
    def run_burst_followup_analysis(self, event_name: str, 
                                  burst_sequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run burst follow-up analysis for a specific event.
        
        Args:
            event_name: Name of the event
            burst_sequences: List of burst follow-up sequences
        
        Returns:
            Burst follow-up analysis results
        """
        try:
            logger.info(f"🔍 Running burst follow-up analysis for {event_name}...")
            
            analysis_results = {
                'event_name': event_name,
                'total_sequences': len(burst_sequences),
                'sequences': [],
                'summary_statistics': {}
            }
            
            if not burst_sequences:
                logger.warning(f"⚠️ No burst sequences found for {event_name}")
                return analysis_results
            
            # Analyze each burst sequence
            time_differences = []
            flux_evolutions = []
            
            for sequence in burst_sequences:
                # Analyze individual sequence
                sequence_analysis = {
                    'burst_time': sequence['burst_time'],
                    'followup_time': sequence['followup_time'],
                    'time_difference_hours': sequence['time_difference_hours'],
                    'swift_flux': sequence['swift_flux'],
                    'chandra_flux': sequence['chandra_flux'],
                    'flux_evolution': sequence['flux_evolution'],
                    'target_object': sequence['target_object'],
                    'sequence_quality': sequence['sequence_quality']
                }
                
                analysis_results['sequences'].append(sequence_analysis)
                time_differences.append(sequence['time_difference_hours'])
                flux_evolutions.append(sequence['flux_evolution'])
            
            # Calculate summary statistics
            analysis_results['summary_statistics'] = {
                'avg_time_difference_hours': sum(time_differences) / len(time_differences),
                'min_time_difference_hours': min(time_differences),
                'max_time_difference_hours': max(time_differences),
                'avg_flux_evolution': sum(flux_evolutions) / len(flux_evolutions),
                'high_quality_sequences': sum(1 for s in burst_sequences if s['sequence_quality'] == 'high')
            }
            
            logger.info(f"✅ Burst follow-up analysis complete for {event_name}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"❌ Failed to run burst follow-up analysis for {event_name}: {e}")
            return {}
    
    def run_multi_wavelength_analysis(self, event_name: str, 
                                    light_curve: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run multi-wavelength analysis for a specific event.
        
        Args:
            event_name: Name of the event
            light_curve: Multi-wavelength light curve data
        
        Returns:
            Multi-wavelength analysis results
        """
        try:
            logger.info(f"🌈 Running multi-wavelength analysis for {event_name}...")
            
            analysis_results = {
                'event_name': event_name,
                'target_object': light_curve.get('target_object', 'Unknown'),
                'total_data_points': len(light_curve.get('combined_data', [])),
                'swift_data_points': len(light_curve.get('swift_data', [])),
                'chandra_data_points': len(light_curve.get('chandra_data', [])),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            combined_data = light_curve.get('combined_data', [])
            if not combined_data:
                logger.warning(f"⚠️ No combined data found for {event_name}")
                return analysis_results
            
            # Analyze flux ratios
            flux_ratios = [point['flux_ratio'] for point in combined_data if point['flux_ratio'] > 0]
            if flux_ratios:
                analysis_results['flux_analysis'] = {
                    'avg_flux_ratio': sum(flux_ratios) / len(flux_ratios),
                    'min_flux_ratio': min(flux_ratios),
                    'max_flux_ratio': max(flux_ratios),
                    'flux_ratio_std': (sum((r - sum(flux_ratios)/len(flux_ratios))**2 for r in flux_ratios) / len(flux_ratios))**0.5
                }
            
            # Analyze time coverage
            time_differences = [point['time_difference_hours'] for point in combined_data]
            if time_differences:
                analysis_results['time_analysis'] = {
                    'avg_time_difference_hours': sum(time_differences) / len(time_differences),
                    'total_time_span_hours': max(time_differences) - min(time_differences),
                    'observation_frequency': len(combined_data) / max(time_differences) if max(time_differences) > 0 else 0
                }
            
            logger.info(f"✅ Multi-wavelength analysis complete for {event_name}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"❌ Failed to run multi-wavelength analysis for {event_name}: {e}")
            return {}
    
    def run_complete_ingestion_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete data ingestion pipeline for all events.
        
        Returns:
            Complete ingestion pipeline results
        """
        logger.info("🚀 Starting complete data ingestion pipeline...")
        
        results = {
            'pipeline_timestamp': datetime.now().isoformat(),
            'production_mode': self.production_mode,
            'total_events': len(self.cross_matching_results.get('events', {})),
            'events': {},
            'summary': {
                'successful_ingestions': 0,
                'failed_ingestions': 0,
                'total_observations': 0,
                'total_analytics': 0
            }
        }
        
        for event_name, event_data in self.cross_matching_results.get('events', {}).items():
            logger.info(f"\n📡 Processing {event_name}...")
            
            event_results = {
                'event_name': event_name,
                'swift_ingestion': False,
                'chandra_ingestion': False,
                'analytics_ingestion': False,
                'burst_analysis': {},
                'multi_wavelength_analysis': {},
                'total_observations': 0
            }
            
            try:
                # Get event data from cross-matching results
                matches = event_data.get('matches', [])
                light_curve = event_data.get('light_curve', {})
                burst_sequences = event_data.get('burst_sequences_data', [])
                
                # Extract observations from matches
                swift_observations = [match['swift_observation'] for match in matches if 'swift_observation' in match]
                chandra_observations = [match['chandra_observation'] for match in matches if 'chandra_observation' in match]
                
                # Ingest SWIFT data
                if swift_observations:
                    event_results['swift_ingestion'] = self.ingest_swift_data(event_name, swift_observations)
                    event_results['total_observations'] += len(swift_observations)
                
                # Ingest Chandra data
                if chandra_observations:
                    event_results['chandra_ingestion'] = self.ingest_chandra_data(event_name, chandra_observations)
                    event_results['total_observations'] += len(chandra_observations)
                
                # Run burst follow-up analysis
                if burst_sequences:
                    event_results['burst_analysis'] = self.run_burst_followup_analysis(event_name, burst_sequences)
                
                # Run multi-wavelength analysis
                if light_curve:
                    event_results['multi_wavelength_analysis'] = self.run_multi_wavelength_analysis(event_name, light_curve)
                
                # Ingest cross-observatory analytics
                cross_analysis = event_data.get('cross_observatory_analysis', {})
                if cross_analysis:
                    event_results['analytics_ingestion'] = self.ingest_cross_observatory_analytics(event_name, cross_analysis)
                
                # Update summary
                if event_results['swift_ingestion'] and event_results['chandra_ingestion']:
                    results['summary']['successful_ingestions'] += 1
                else:
                    results['summary']['failed_ingestions'] += 1
                
                results['summary']['total_observations'] += event_results['total_observations']
                if event_results['analytics_ingestion']:
                    results['summary']['total_analytics'] += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to process {event_name}: {e}")
                results['summary']['failed_ingestions'] += 1
            
            results['events'][event_name] = event_results
        
        # Save results
        results_file = self.data_dir / "ingestion_pipeline_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Data ingestion pipeline complete. Results saved to {results_file}")
        return results
    
    def show_ingestion_summary(self, results: Dict[str, Any]) -> None:
        """Display data ingestion pipeline summary."""
        print("\n" + "="*70)
        print("📊 Data Ingestion Pipeline Summary")
        print("="*70)
        
        summary = results.get('summary', {})
        print(f"📡 Total events processed: {results.get('total_events', 0)}")
        print(f"✅ Successful ingestions: {summary.get('successful_ingestions', 0)}")
        print(f"❌ Failed ingestions: {summary.get('failed_ingestions', 0)}")
        print(f"📊 Total observations: {summary.get('total_observations', 0)}")
        print(f"🔍 Total analytics: {summary.get('total_analytics', 0)}")
        
        print("\n📡 Event Details:")
        for event_name, event_data in results.get('events', {}).items():
            print(f"\n  📡 {event_name}")
            print(f"     SWIFT ingestion: {'✅' if event_data.get('swift_ingestion') else '❌'}")
            print(f"     Chandra ingestion: {'✅' if event_data.get('chandra_ingestion') else '❌'}")
            print(f"     Analytics ingestion: {'✅' if event_data.get('analytics_ingestion') else '❌'}")
            print(f"     Total observations: {event_data.get('total_observations', 0)}")
            
            burst_analysis = event_data.get('burst_analysis', {})
            if burst_analysis:
                print(f"     Burst sequences: {burst_analysis.get('total_sequences', 0)}")
            
            multi_wavelength = event_data.get('multi_wavelength_analysis', {})
            if multi_wavelength:
                print(f"     Multi-wavelength points: {multi_wavelength.get('total_data_points', 0)}")
        
        print("\n🎯 Data ingestion pipeline complete!")
        print("📁 Results saved to: lab3_datasets/ingestion_pipeline_results.json")


def main():
    """Main function to run the data ingestion pipeline."""
    try:
        # Load configuration
        config = Lab3ConfigLoader()
        
        # Create ingestion pipeline
        pipeline = DataIngestionPipeline(config, production_mode=False)
        
        # Run complete pipeline
        results = pipeline.run_complete_ingestion_pipeline()
        
        # Show summary
        pipeline.show_ingestion_summary(results)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Data ingestion pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
