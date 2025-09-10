#!/usr/bin/env python3
"""
Cross-Matching Engine for SWIFT-Chandra Datasets
===============================================

This module provides cross-matching capabilities to find overlapping
observations between SWIFT and Chandra datasets for Lab 3.

Features:
- Position-based cross-matching using angular separation
- Time-based correlation for burst follow-up analysis
- Flux correlation analysis
- Multi-wavelength light curve generation
- Data quality cross-validation

Author: Lab 3 Development Team
Date: 2025-01-10
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.coordinates import match_coordinates_sky, search_around_sky

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossMatchingEngine:
    """Engine for cross-matching SWIFT and Chandra observations."""
    
    def __init__(self, data_dir: str = "lab3_datasets"):
        self.data_dir = Path(data_dir)
        self.metadata_file = self.data_dir / "dataset_metadata.json"
        self.cross_match_results = {}
        
    def load_dataset_metadata(self) -> Dict[str, Any]:
        """Load dataset metadata from JSON file."""
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.info(f"✅ Loaded metadata for {len(metadata['events'])} events")
            return metadata
        except FileNotFoundError:
            logger.error(f"❌ Metadata file not found: {self.metadata_file}")
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to load metadata: {e}")
            return {}
    
    def load_synthetic_data(self, event_name: str) -> Optional[Dict[str, Any]]:
        """Load synthetic data for a specific event."""
        synthetic_file = self.data_dir / f"{event_name}_synthetic.json"
        try:
            with open(synthetic_file, 'r') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded synthetic data for {event_name}")
            return data
        except FileNotFoundError:
            logger.error(f"❌ Synthetic data not found for {event_name}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to load synthetic data for {event_name}: {e}")
            return None
    
    def cross_match_by_position(self, swift_obs: List[Dict], chandra_obs: List[Dict], 
                              max_separation: float = 1.0) -> List[Dict[str, Any]]:
        """
        Cross-match observations by celestial coordinates.
        
        Args:
            swift_obs: List of SWIFT observations
            chandra_obs: List of Chandra observations
            max_separation: Maximum angular separation in arcseconds
        
        Returns:
            List of cross-matched observation pairs
        """
        matches = []
        
        # Convert to SkyCoord objects
        swift_coords = SkyCoord(
            ra=[obs['ra'] for obs in swift_obs] * u.deg,
            dec=[obs['dec'] for obs in swift_obs] * u.deg
        )
        
        chandra_coords = SkyCoord(
            ra=[obs['ra'] for obs in chandra_obs] * u.deg,
            dec=[obs['dec'] for obs in chandra_obs] * u.deg
        )
        
        # Find matches within max_separation
        idx_swift, idx_chandra, d2d, d3d = search_around_sky(
            swift_coords, chandra_coords, max_separation * u.arcsec
        )
        
        for i, (swift_idx, chandra_idx) in enumerate(zip(idx_swift, idx_chandra)):
            match = {
                'swift_observation': swift_obs[swift_idx],
                'chandra_observation': chandra_obs[chandra_idx],
                'angular_separation_arcsec': d2d[i].arcsec,
                'match_quality': 'high' if d2d[i].arcsec < 0.5 else 'medium',
                'cross_match_type': 'position'
            }
            matches.append(match)
        
        logger.info(f"✅ Found {len(matches)} position-based matches")
        return matches
    
    def cross_match_by_time(self, swift_obs: List[Dict], chandra_obs: List[Dict],
                          max_time_diff_hours: float = 168.0) -> List[Dict[str, Any]]:
        """
        Cross-match observations by time for burst follow-up analysis.
        
        Args:
            swift_obs: List of SWIFT observations
            chandra_obs: List of Chandra observations
            max_time_diff_hours: Maximum time difference in hours (default: 7 days)
        
        Returns:
            List of time-based cross-matched observation pairs
        """
        matches = []
        
        for swift_obs_item in swift_obs:
            swift_time = datetime.fromisoformat(swift_obs_item['observation_time'])
            
            for chandra_obs_item in chandra_obs:
                chandra_time = datetime.fromisoformat(chandra_obs_item['observation_time'])
                time_diff = chandra_time - swift_time
                time_diff_hours = time_diff.total_seconds() / 3600
                
                # Check if Chandra observation is after SWIFT and within time window
                if 0 < time_diff_hours <= max_time_diff_hours:
                    match = {
                        'swift_observation': swift_obs_item,
                        'chandra_observation': chandra_obs_item,
                        'time_difference_hours': time_diff_hours,
                        'time_difference_days': time_diff_hours / 24,
                        'match_quality': 'high' if time_diff_hours < 24 else 'medium',
                        'cross_match_type': 'burst_followup'
                    }
                    matches.append(match)
        
        logger.info(f"✅ Found {len(matches)} time-based matches")
        return matches
    
    def analyze_flux_correlation(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze flux correlation between SWIFT and Chandra observations.
        
        Args:
            matches: List of cross-matched observation pairs
        
        Returns:
            Flux correlation analysis results
        """
        if not matches:
            return {'correlation': 0.0, 'r_squared': 0.0, 'sample_size': 0}
        
        swift_fluxes = []
        chandra_fluxes = []
        
        for match in matches:
            swift_obs = match['swift_observation']
            chandra_obs = match['chandra_observation']
            
            swift_fluxes.append(swift_obs.get('xray_flux', 0))
            chandra_fluxes.append(chandra_obs.get('xray_flux', 0))
        
        # Calculate correlation
        correlation_matrix = np.corrcoef(swift_fluxes, chandra_fluxes)
        correlation = correlation_matrix[0, 1] if not np.isnan(correlation_matrix[0, 1]) else 0.0
        
        # Calculate R-squared
        r_squared = correlation ** 2
        
        analysis = {
            'correlation': float(correlation),
            'r_squared': float(r_squared),
            'sample_size': len(matches),
            'swift_flux_mean': float(np.mean(swift_fluxes)),
            'chandra_flux_mean': float(np.mean(chandra_fluxes)),
            'flux_ratio_mean': float(np.mean([c/s if s > 0 else 0 for s, c in zip(swift_fluxes, chandra_fluxes)]))
        }
        
        logger.info(f"✅ Flux correlation analysis: r={correlation:.3f}, R²={r_squared:.3f}")
        return analysis
    
    def generate_multi_wavelength_light_curve(self, matches: List[Dict[str, Any]], 
                                           target_object: str) -> Dict[str, Any]:
        """
        Generate multi-wavelength light curve from cross-matched observations.
        
        Args:
            matches: List of cross-matched observation pairs
            target_object: Target object name
        
        Returns:
            Multi-wavelength light curve data
        """
        light_curve_data = {
            'target_object': target_object,
            'swift_data': [],
            'chandra_data': [],
            'combined_data': []
        }
        
        for match in matches:
            swift_obs = match['swift_observation']
            chandra_obs = match['chandra_observation']
            
            # SWIFT data point
            swift_point = {
                'time': swift_obs['observation_time'],
                'flux': swift_obs.get('xray_flux', 0),
                'instrument': 'SWIFT-XRT',
                'exposure_time': swift_obs.get('exposure_time', 0)
            }
            light_curve_data['swift_data'].append(swift_point)
            
            # Chandra data point
            chandra_point = {
                'time': chandra_obs['observation_time'],
                'flux': chandra_obs.get('xray_flux', 0),
                'instrument': 'Chandra-ACIS',
                'exposure_time': chandra_obs.get('exposure_time', 0)
            }
            light_curve_data['chandra_data'].append(chandra_point)
            
            # Combined data point
            combined_point = {
                'time': chandra_obs['observation_time'],
                'swift_flux': swift_obs.get('xray_flux', 0),
                'chandra_flux': chandra_obs.get('xray_flux', 0),
                'flux_ratio': chandra_obs.get('xray_flux', 0) / swift_obs.get('xray_flux', 1),
                'time_difference_hours': match.get('time_difference_hours', 0)
            }
            light_curve_data['combined_data'].append(combined_point)
        
        # Sort by time
        light_curve_data['swift_data'].sort(key=lambda x: x['time'])
        light_curve_data['chandra_data'].sort(key=lambda x: x['time'])
        light_curve_data['combined_data'].sort(key=lambda x: x['time'])
        
        logger.info(f"✅ Generated multi-wavelength light curve for {target_object}")
        return light_curve_data
    
    def detect_burst_followup_sequences(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect burst follow-up sequences from cross-matched observations.
        
        Args:
            matches: List of cross-matched observation pairs
        
        Returns:
            List of burst follow-up sequences
        """
        sequences = []
        
        for match in matches:
            swift_obs = match['swift_observation']
            chandra_obs = match['chandra_observation']
            
            # Check if this is a burst follow-up sequence
            if (swift_obs.get('burst_detected', False) and 
                chandra_obs.get('follow_up_observation', False)):
                
                sequence = {
                    'burst_time': swift_obs['observation_time'],
                    'followup_time': chandra_obs['observation_time'],
                    'time_difference_hours': match.get('time_difference_hours', 0),
                    'swift_flux': swift_obs.get('xray_flux', 0),
                    'chandra_flux': chandra_obs.get('xray_flux', 0),
                    'flux_evolution': chandra_obs.get('xray_flux', 0) / swift_obs.get('xray_flux', 1),
                    'target_object': swift_obs.get('target_object', 'Unknown'),
                    'sequence_quality': match.get('match_quality', 'unknown')
                }
                sequences.append(sequence)
        
        logger.info(f"✅ Detected {len(sequences)} burst follow-up sequences")
        return sequences
    
    def run_comprehensive_cross_matching(self) -> Dict[str, Any]:
        """
        Run comprehensive cross-matching analysis for all events.
        
        Returns:
            Comprehensive cross-matching results
        """
        logger.info("🚀 Starting comprehensive cross-matching analysis...")
        
        # Load metadata
        metadata = self.load_dataset_metadata()
        if not metadata:
            return {}
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_events': len(metadata['events']),
            'events': {}
        }
        
        for event_name, event_info in metadata['events'].items():
            logger.info(f"📡 Processing {event_info['name']}...")
            
            # Load synthetic data
            synthetic_data = self.load_synthetic_data(event_name)
            if not synthetic_data:
                continue
            
            swift_obs = synthetic_data.get('swift_observations', [])
            chandra_obs = synthetic_data.get('chandra_observations', [])
            
            # Position-based cross-matching
            position_matches = self.cross_match_by_position(swift_obs, chandra_obs)
            
            # Time-based cross-matching
            time_matches = self.cross_match_by_time(swift_obs, chandra_obs)
            
            # Combine matches
            all_matches = position_matches + time_matches
            
            # Analyze flux correlation
            flux_analysis = self.analyze_flux_correlation(all_matches)
            
            # Generate multi-wavelength light curve
            light_curve = self.generate_multi_wavelength_light_curve(
                all_matches, 
                event_info['name']
            )
            
            # Detect burst follow-up sequences
            burst_sequences = self.detect_burst_followup_sequences(all_matches)
            
            # Store results
            results['events'][event_name] = {
                'event_info': event_info,
                'position_matches': len(position_matches),
                'time_matches': len(time_matches),
                'total_matches': len(all_matches),
                'flux_analysis': flux_analysis,
                'light_curve_points': len(light_curve['combined_data']),
                'burst_sequences': len(burst_sequences),
                'matches': all_matches,
                'light_curve': light_curve,
                'burst_sequences_data': burst_sequences
            }
        
        # Save results
        results_file = self.data_dir / "cross_matching_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Cross-matching analysis complete. Results saved to {results_file}")
        return results
    
    def show_cross_matching_summary(self, results: Dict[str, Any]) -> None:
        """Display cross-matching analysis summary."""
        print("\n" + "="*70)
        print("📊 SWIFT-Chandra Cross-Matching Analysis Summary")
        print("="*70)
        
        total_events = results.get('total_events', 0)
        print(f"📡 Total events analyzed: {total_events}")
        
        print("\n🔍 Event Details:")
        for event_name, event_data in results.get('events', {}).items():
            event_info = event_data['event_info']
            print(f"\n  📡 {event_info['name']}")
            print(f"     Position matches: {event_data['position_matches']}")
            print(f"     Time matches: {event_data['time_matches']}")
            print(f"     Total matches: {event_data['total_matches']}")
            print(f"     Flux correlation: {event_data['flux_analysis']['correlation']:.3f}")
            print(f"     Light curve points: {event_data['light_curve_points']}")
            print(f"     Burst sequences: {event_data['burst_sequences']}")
        
        print("\n🎯 Cross-matching analysis complete!")
        print("📁 Results saved to: lab3_datasets/cross_matching_results.json")


def main():
    """Main function to run cross-matching analysis."""
    try:
        # Create cross-matching engine
        engine = CrossMatchingEngine()
        
        # Run comprehensive analysis
        results = engine.run_comprehensive_cross_matching()
        
        # Show summary
        engine.show_cross_matching_summary(results)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Cross-matching analysis failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
