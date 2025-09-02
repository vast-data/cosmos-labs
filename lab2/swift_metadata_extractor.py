#!/usr/bin/env python3
"""
Swift Metadata Extractor for Lab 2
Extracts metadata from Swift satellite data files and integrates with VAST Database
"""

import logging
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import gzip
import re

logger = logging.getLogger(__name__)

class SwiftMetadataExtractor:
    """Extracts metadata from Swift satellite data files"""
    
    def __init__(self, config):
        """Initialize the metadata extractor"""
        self.config = config
        self.supported_formats = ['.fits', '.gz', '.txt', '.json', '.lc']
        
    def extract_metadata_from_file(self, file_path: str, dataset_name: str = None) -> Optional[Dict[str, Any]]:
        """Extract metadata from a Swift data file"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"❌ File not found: {file_path}")
                return None
            
            # Get basic file information
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            file_format = self._get_file_format(file_path)
            
            # Debug: log file size extraction
            logger.info(f"📁 File: {file_path.name} | Size: {file_size} bytes | Format: {file_format}")
            
            # Basic metadata that all files have
            metadata = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size_bytes': file_size,
                'file_format': file_format,
                'dataset_name': dataset_name or self._extract_dataset_name(file_path),
                'ingestion_timestamp': datetime.now().isoformat(),
                'metadata_version': '1.0',
                'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
            
            # Extract format-specific metadata
            if file_format in ['.fits', '.lc']:
                # Both .fits and .lc files are FITS format (lightcurves are FITS tables)
                metadata.update(self._extract_fits_metadata(file_path))
            elif file_format == '.gz':
                metadata.update(self._extract_swift_lightcurve_metadata(file_path))
            elif file_format == '.json':
                metadata.update(self._extract_json_metadata(file_path))
            else:
                # For other formats, use basic filename parsing
                metadata.update(self._extract_basic_metadata(file_path))
            
            # Add checksum
            metadata['checksum'] = self._calculate_checksum(file_path)
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed for {file_path}: {e}")
            return None
    
    def _get_file_format(self, file_path: Path) -> str:
        """Determine the file format"""
        # Check for compressed files first
        if file_path.suffix == '.gz':
            # Look at the original file extension
            stem = file_path.stem
            if stem.endswith('.fits'):
                return '.fits'
            elif stem.endswith('.lc'):
                return '.lc'
            else:
                return '.gz'
        
        return file_path.suffix.lower()
    
    def _extract_dataset_name(self, file_path: Path) -> str:
        """Extract dataset name from file path"""
        # Extract dataset name from path structure
        # Example: /path/to/swift_datasets/batsources_survey_north/file.fits
        path_parts = file_path.parts
        
        # Look for 'swift_datasets' in the path
        try:
            swift_index = path_parts.index('swift_datasets')
            if swift_index + 1 < len(path_parts):
                return path_parts[swift_index + 1]
        except ValueError:
            pass
        
        # Fallback: use parent directory name
        return file_path.parent.name
    
    def _extract_fits_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from FITS files"""
        try:
            from astropy.io import fits
            
            with fits.open(file_path) as hdul:
                header = hdul[0].header
                
                return {
                    'mission_id': header.get('MISSION', 'SWIFT'),
                    'satellite_name': header.get('TELESCOP', 'SWIFT'),
                    'instrument_type': header.get('INSTRUME', 'BAT'),
                    'observation_timestamp': header.get('DATE-OBS', 'unknown'),
                    'target_object': header.get('OBJECT', 'unknown'),
                    'processing_status': 'raw'
                }
                
        except ImportError:
            logger.warning("⚠️  astropy not available, using basic FITS parsing")
            return self._extract_basic_fits_metadata(file_path)
        except Exception as e:
            logger.error(f"❌ FITS metadata extraction failed: {e}")
            return self._get_default_metadata()
    
    def _extract_basic_fits_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Basic FITS metadata extraction without astropy"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 2880 bytes (FITS header block)
                header_block = f.read(2880)
                
                # Parse header cards (80 characters each)
                header_cards = [header_block[i:i+80] for i in range(0, len(header_block), 80)]
                
                metadata = self._get_default_metadata()
                
                for card in header_cards:
                    card_str = card.decode('ascii', errors='ignore').strip()
                    if '=' in card_str:
                        key, value = card_str.split('=', 1)
                        key = key.strip()
                        value = value.split('/')[0].strip().strip("'")
                        
                        if key == 'MISSION':
                            metadata['mission_id'] = value
                        elif key == 'TELESCOP':
                            metadata['satellite_name'] = value
                        elif key == 'INSTRUME':
                            metadata['instrument_type'] = value
                        elif key == 'DATE-OBS':
                            metadata['observation_timestamp'] = value
                        elif key == 'OBJECT':
                            metadata['target_object'] = value
                
                return metadata
                
        except Exception as e:
            logger.error(f"❌ Basic FITS parsing failed: {e}")
            return self._get_default_metadata()
    
    def _extract_swift_lightcurve_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from Swift lightcurve files"""
        try:
            # Try to read the file content
            if file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)  # Read first 1000 characters
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)
            
            metadata = self._get_default_metadata()
            
            # Extract Swift-specific information from filename
            filename = file_path.name
            
            # Parse Swift BAT filename pattern
            # Example: swbj0001_0m9012_c_s157.lc.gz
            # Format: swbjXXXX_XXXXXXX_XXXX_XXXX.extension
            pattern = r'swbj(\d{4})_([a-z0-9]+)_([a-z0-9]+)_([a-z0-9]+)\.([a-z0-9]+)'
            match = re.match(pattern, filename)
            
            if match:
                metadata.update({
                    'mission_id': 'SWIFT',
                    'satellite_name': 'SWIFT',
                    'instrument_type': 'BAT',
                    'target_object': f"BAT_{match.group(1)}",  # BAT source number
                    'processing_status': 'raw'
                })
                
                # Try to extract timestamp from content
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
                if timestamp_match:
                    metadata['observation_timestamp'] = timestamp_match.group(1)
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Swift lightcurve metadata extraction failed: {e}")
            return self._get_default_metadata()
    
    def _extract_json_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                metadata = self._get_default_metadata()
                
                # Map common JSON fields to our schema
                field_mapping = {
                    'mission_id': 'mission_id',
                    'satellite': 'satellite_name',
                    'instrument': 'instrument_type',
                    'target': 'target_object',
                    'status': 'processing_status',
                    'date_obs': 'observation_timestamp'
                }
                
                for json_key, schema_key in field_mapping.items():
                    if json_key in data:
                        metadata[schema_key] = data[json_key]
                
                return metadata
                
        except Exception as e:
            logger.error(f"❌ JSON metadata extraction failed: {e}")
            return self._get_default_metadata()
    
    def _extract_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata from filename patterns"""
        filename = file_path.name
        
        metadata = self._get_default_metadata()
        
        # Try to extract information from filename
        # Look for common astronomical filename patterns
        
        # Pattern 1: MISSION_TARGET_DATE_TIME.ext
        # Example: COSMOS7_MARS_20241201_143022.fits
        pattern1 = r'([A-Z0-9]+)_([A-Z0-9]+)_(\d{8})_(\d{6})'
        match1 = re.match(pattern1, filename)
        
        if match1:
            metadata.update({
                'mission_id': match1.group(1),
                'target_object': match1.group(2),
                'observation_timestamp': f"{match1.group(3)[:4]}-{match1.group(3)[4:6]}-{match1.group(3)[6:8]}"
            })
            return metadata
        
        # Pattern 2: Swift BAT pattern (already handled above, but fallback)
        pattern2 = r'swbj(\d{4})_([a-z0-9]+)_([a-z0-9]+)_([a-z0-9]+)'
        match2 = re.match(pattern2, filename)
        
        if match2:
            metadata.update({
                'mission_id': 'SWIFT',
                'satellite_name': 'SWIFT',
                'instrument_type': 'BAT',
                'target_object': f"BAT_{match2.group(1)}"
            })
            return metadata
        
        # Pattern 3: Generic astronomical pattern
        # Look for any recognizable patterns
        if 'swift' in filename.lower() or 'bat' in filename.lower():
            metadata.update({
                'mission_id': 'SWIFT',
                'satellite_name': 'SWIFT',
                'instrument_type': 'BAT'
            })
        
        return metadata
    
    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata for files that can't be parsed"""
        return {
            'mission_id': 'unknown',
            'satellite_name': 'unknown',
            'instrument_type': 'unknown',
            'observation_timestamp': 'unknown',
            'target_object': 'unknown',
            'processing_status': 'raw'
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to calculate checksum: {e}")
            return "unknown"
    
    def extract_metadata_from_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """Extract metadata from all files in a dataset directory"""
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists() or not dataset_path.is_dir():
            logger.error(f"❌ Dataset directory not found: {dataset_path}")
            return []
        
        logger.info(f"🔍 Extracting metadata from dataset: {dataset_path.name}")
        
        metadata_list = []
        file_count = 0
        
        # Find all files in the dataset
        for file_path in dataset_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                
                # Extract metadata from file
                metadata = self.extract_metadata_from_file(file_path, dataset_path.name)
                if metadata:
                    metadata_list.append(metadata)
                
                # Progress logging
                if file_count % 10 == 0:
                    logger.info(f"📊 Processed {file_count} files, extracted {len(metadata_list)} metadata records")
        
        logger.info(f"✅ Completed metadata extraction: {len(metadata_list)}/{file_count} files processed")
        return metadata_list
