#!/usr/bin/env python3
"""
Lab 4 Test Data Generator

This script generates realistic test data for Lab 4 snapshot strategy testing.
It creates various file types and sizes to simulate real research data workloads.
"""

import os
import random
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker
import json
import csv
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import psutil

# Initialize Faker for realistic data generation
fake = Faker()


class TestDataGenerator:
    """
    Generate test data for various lab scenarios.
    
    Creates various file types and sizes to simulate real research workloads:
    - Raw telescope data (large binary files)
    - Processed data (medium-sized files)
    - Analysis results (small structured files)
    - Published datasets (mixed content)
    """
    
    def __init__(self, lab_type: str = "lab4", max_workers: int = 8):
        """
        Initialize the data generator.
        
        Args:
            lab_type: Type of lab (lab1, lab4, etc.) to determine data structure
            max_workers: Maximum number of threads for concurrent uploads
        """
        self.lab_type = lab_type
        self.max_workers = max_workers
        
        # Thread-safe counters for progress tracking
        self._lock = threading.Lock()
        self._files_generated = 0
        self._files_uploaded = 0
        
        # Load lab-specific configuration
        self.lab_config = self._load_lab_config()
        
        # Initialize S3 client for VAST uploads
        self.s3_client = self._init_s3_client()
    
    def _increment_generated(self):
        """Thread-safe increment of generated files counter."""
        with self._lock:
            self._files_generated += 1
    
    def _increment_uploaded(self):
        """Thread-safe increment of uploaded files counter."""
        with self._lock:
            self._files_uploaded += 1
    
    def _get_progress(self):
        """Get current progress counters."""
        with self._lock:
            return self._files_generated, self._files_uploaded
    
    def _get_memory_usage(self):
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            return 0
    
    def _force_cleanup(self):
        """Force garbage collection and memory cleanup."""
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage after cleanup
        memory_mb = self._get_memory_usage()
        
        return collected, memory_mb
    
    def _check_memory_pressure(self, file_size_mb: int, thread_count: int) -> bool:
        """
        Check if we have enough memory for the operation.
        
        Args:
            file_size_mb: Size of each file in MB
            thread_count: Number of concurrent threads
            
        Returns:
            True if memory pressure is too high
        """
        try:
            # Calculate estimated memory needed
            estimated_memory = file_size_mb * thread_count * 1.5  # 1.5x for overhead
            
            # Get available memory
            available_memory = psutil.virtual_memory().available / 1024 / 1024  # MB
            
            # Check if we need more than 80% of available memory
            return estimated_memory > (available_memory * 0.8)
        except:
            return False
    
    def _load_lab_config(self) -> dict:
        """
        Load lab-specific configuration from config.yaml.
        
        Returns:
            Dict containing lab configuration
            
        Raises:
            SystemExit: If config.yaml is missing or lab configuration is not found
        """
        # Look for config.yaml in the project root
        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            print(f"❌ Error: config.yaml not found at {config_path}")
            print("Please copy config.yaml.example to config.yaml and configure it first.")
            raise SystemExit(1)
        
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                lab_config = config.get(self.lab_type)
                if not lab_config:
                    print(f"❌ Error: No configuration found for {self.lab_type} in config.yaml")
                    print(f"Available lab configurations: {list(config.keys())}")
                    raise SystemExit(1)
                return lab_config
        except Exception as e:
            print(f"❌ Error: Could not load lab configuration: {e}")
            raise SystemExit(1)
    
    def get_lab_views(self) -> list:
        """
        Get configured views for the current lab.
        
        Returns:
            List of view paths configured for this lab
        """
        if self.lab_type == "lab1":
            views_config = self.lab_config.get('views', {})
            raw_path = views_config.get('raw_data', {}).get('path')
            processed_path = views_config.get('processed_data', {}).get('path')
            
            if not raw_path or not processed_path:
                print(f"❌ Error: Missing view paths in lab1 configuration")
                print("Required: lab1.views.raw_data.path and lab1.views.processed_data.path")
                raise SystemExit(1)
                
            return [raw_path, processed_path]
            
        elif self.lab_type == "lab4":
            views_config = self.lab_config.get('views', {})
            if not views_config:
                print(f"❌ Error: Missing views configuration in lab4")
                print("Required: lab4.views dictionary")
                raise SystemExit(1)
            
            # Extract paths from the views dictionary
            view_paths = []
            for view_name, view_config in views_config.items():
                if isinstance(view_config, dict) and 'path' in view_config:
                    view_paths.append(view_config['path'])
            
            if not view_paths:
                print(f"❌ Error: No valid view paths found in lab4.views")
                print("Required: lab4.views.{view_name}.path for each view")
                raise SystemExit(1)
                
            return view_paths
        else:
            print(f"❌ Error: Unsupported lab type: {self.lab_type}")
            print("Supported lab types: lab1, lab4")
            raise SystemExit(1)
    
    def get_bucket_mapping(self) -> dict:
        """
        Get mapping of data types to S3 bucket names.
        
        Returns:
            Dict mapping data types to bucket names
        """
        if self.lab_type == "lab4":
            views_config = self.lab_config.get('views', {})
            return {
                'raw': views_config.get('raw_data', {}).get('bucket_name'),
                'processed': views_config.get('processed_data', {}).get('bucket_name'),
                'analysis': views_config.get('analysis_results', {}).get('bucket_name'),
                'published': views_config.get('published_datasets', {}).get('bucket_name')
            }
        else:
            # For lab1, use raw and processed buckets
            views_config = self.lab_config.get('views', {})
            return {
                'raw': views_config.get('raw_data', {}).get('bucket_name'),
                'processed': views_config.get('processed_data', {}).get('bucket_name')
            }
    
    def _init_s3_client(self):
        """Initialize S3 client for VAST uploads."""
        try:
            # Get S3 configuration from root config (not lab-specific)
            config_path = Path(__file__).parent.parent / "config.yaml"
            secrets_path = Path(__file__).parent.parent / "secrets.yaml"
            
            with open(config_path, 'r') as f:
                import yaml
                full_config = yaml.safe_load(f)
                s3_config = full_config.get('s3', {})
            
            if not s3_config:
                print("❌ Error: No S3 configuration found in config.yaml")
                raise SystemExit(1)
            
            # Load secrets for S3 credentials
            secrets = {}
            if secrets_path.exists():
                with open(secrets_path, 'r') as f:
                    secrets = yaml.safe_load(f) or {}
            
            # Get S3 credentials from secrets
            access_key_id = secrets.get('s3_access_key')
            secret_access_key = secrets.get('s3_secret_key')
            
            if not access_key_id or not secret_access_key:
                print("❌ Error: VAST S3 credentials not found in secrets.yaml")
                print("Required: s3_access_key and s3_secret_key")
                raise SystemExit(1)
            
            # Suppress SSL warnings if verification is disabled (like other labs)
            ssl_verify = s3_config.get('ssl_verify', s3_config.get('verify_ssl', True))
            if not ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                endpoint_url=s3_config.get('endpoint_url'),
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=s3_config.get('region', 'us-east-1'),
                use_ssl=True,
                verify=ssl_verify
            )
            
            # Test connection
            s3_client.list_buckets()
            print("✅ S3 connection successful")
            return s3_client
            
        except NoCredentialsError:
            print("❌ Error: VAST S3 credentials not found")
            print("Please configure s3_access_key_id and s3_secret_access_key in secrets.yaml")
            raise SystemExit(1)
        except ClientError as e:
            print(f"❌ Error: VAST S3 connection failed: {e}")
            raise SystemExit(1)
        except Exception as e:
            print(f"❌ Error: Could not initialize VAST S3 client: {e}")
            raise SystemExit(1)
    
    def _upload_to_s3(self, local_file_path: Path, bucket_name: str, s3_key: str) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_file_path: Path to local file
            bucket_name: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            True if upload successful
        """
        try:
            self.s3_client.upload_file(str(local_file_path), bucket_name, s3_key)
            return True
        except ClientError as e:
            print(f"❌ Error uploading {local_file_path} to s3://{bucket_name}/{s3_key}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error uploading {local_file_path}: {e}")
            return False
    
    def _upload_file_to_appropriate_bucket(self, filepath: Path, data_type: str) -> bool:
        """
        Upload a file to the appropriate S3 bucket based on data type.
        
        Args:
            filepath: Path to local file
            data_type: Type of data (raw, processed, analysis, published)
            
        Returns:
            True if upload successful
        """
        bucket_mapping = self.get_bucket_mapping()
        bucket_name = bucket_mapping.get(data_type)
        
        if not bucket_name:
            print(f"  ⚠️  No bucket configured for {data_type} data")
            return False
        
        s3_key = f"{data_type}/{filepath.name}"
        success = self._upload_to_s3(filepath, bucket_name, s3_key)
        
        if success:
            print(f"  ✅ Uploaded to s3://{bucket_name}/{s3_key}")
        else:
            print(f"  ❌ Failed to upload to S3")
        
        return success
    
    def _upload_data_directly_to_s3(self, data: bytes, filename: str, data_type: str) -> bool:
        """
        Upload data directly to S3 without creating local files.
        
        Args:
            data: Data bytes to upload
            filename: Name for the S3 object
            data_type: Type of data (raw, processed, analysis, published)
            
        Returns:
            True if upload successful
        """
        bucket_mapping = self.get_bucket_mapping()
        bucket_name = bucket_mapping.get(data_type)
        
        if not bucket_name:
            print(f"  ⚠️  No bucket configured for {data_type} data")
            return False
        
        s3_key = f"{data_type}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=data
            )
            print(f"  ✅ Uploaded to s3://{bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            print(f"  ❌ Error uploading {filename} to s3://{bucket_name}/{s3_key}: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Error uploading {filename}: {e}")
            return False
    
    def _generate_single_file(self, file_type: str, index: int, size_mb: int = None) -> str:
        """
        Generate a single file and upload to S3 (thread-safe with memory cleanup).
        
        Args:
            file_type: Type of file ('raw', 'processed', 'analysis', 'published')
            index: File index for naming
            size_mb: Size in MB (for raw/processed files)
            
        Returns:
            Filename if successful, None if failed
        """
        data = None
        try:
            # Generate unique filename with timestamp and random suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = fake.random_int(min=1000, max=9999)
            
            if file_type == 'raw':
                filename = f"telescope_data_{timestamp}_{random_suffix}_{index:03d}.dat"
                data_size = size_mb * 1024 * 1024
                data = os.urandom(data_size)
            elif file_type == 'processed':
                filename = f"processed_data_{timestamp}_{random_suffix}_{index:03d}.dat"
                header = f"PROCESSED_DATA_V1.0\nFile: {filename}\nTimestamp: {datetime.now().isoformat()}\n"
                header_bytes = header.encode('utf-8')
                remaining_size = (size_mb * 1024 * 1024) - len(header_bytes)
                data = header_bytes + os.urandom(remaining_size)
            elif file_type == 'analysis':
                file_types = ['json', 'csv', 'txt']
                file_ext = random.choice(file_types)
                filename = f"analysis_result_{timestamp}_{random_suffix}_{index:03d}.{file_ext}"
                
                if file_ext == 'json':
                    data = self._generate_json_analysis_data()
                elif file_ext == 'csv':
                    data = self._generate_csv_analysis_data()
                else:
                    data = self._generate_text_analysis_data()
            elif file_type == 'published':
                file_types = ['pdf', 'txt', 'json', 'dat']
                file_ext = random.choice(file_types)
                filename = f"published_dataset_{timestamp}_{random_suffix}_{index:03d}.{file_ext}"
                
                if file_ext == 'pdf':
                    data = self._generate_pdf_dataset_data()
                elif file_ext == 'json':
                    data = self._generate_json_dataset_data()
                elif file_ext == 'dat':
                    data = self._generate_binary_dataset_data()
                else:
                    data = self._generate_text_dataset_data()
            else:
                return None
            
            # Upload to S3
            success = self._upload_data_directly_to_s3(data, filename, file_type)
            if success:
                self._increment_uploaded()
                return filename
            return None
            
        except Exception as e:
            print(f"  ❌ Error generating {file_type} file {index}: {e}")
            return None
        finally:
            # CRITICAL: Explicit memory cleanup
            if data is not None:
                del data  # Explicitly delete the large data object
            
            # Force garbage collection for this thread
            gc.collect()
            
            self._increment_generated()

    def generate_large_files(self, count: int = 10, size_mb: int = 100) -> list:
        """
        Generate large binary files directly to S3 using threading with memory management.
        
        Args:
            count: Number of files to generate
            size_mb: Size of each file in MB
            
        Returns:
            List of generated file names (for tracking)
        """
        # Check memory pressure before starting
        if self._check_memory_pressure(size_mb, self.max_workers):
            print(f"⚠️  High memory pressure detected! Consider reducing --max-workers or file size.")
            print(f"💾 Current memory usage: {self._get_memory_usage():.1f}MB")
        
        print(f"🚀 Generating {count} raw files ({size_mb}MB each) using {self.max_workers} threads...")
        print(f"💾 Starting memory usage: {self._get_memory_usage():.1f}MB")
        
        files = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file generation tasks
            futures = [
                executor.submit(self._generate_single_file, 'raw', i, size_mb)
                for i in range(count)
            ]
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    files.append(result)
                    generated, uploaded = self._get_progress()
                    current_memory = self._get_memory_usage()
                    print(f"  ✅ Progress: {uploaded}/{generated} files uploaded (Memory: {current_memory:.1f}MB)")
        
        # Force cleanup after all files are processed
        collected, final_memory = self._force_cleanup()
        print(f"🧹 Cleanup: {collected} objects collected, Memory: {final_memory:.1f}MB")
        
        return files
    
    def generate_processed_data(self, count: int = 20, size_mb: int = 50) -> list:
        """
        Generate processed data files directly to S3 using threading with memory management.
        
        Args:
            count: Number of files to generate
            size_mb: Size of each file in MB
            
        Returns:
            List of generated file names (for tracking)
        """
        # Check memory pressure before starting
        if self._check_memory_pressure(size_mb, self.max_workers):
            print(f"⚠️  High memory pressure detected! Consider reducing --max-workers or file size.")
            print(f"💾 Current memory usage: {self._get_memory_usage():.1f}MB")
        
        print(f"🚀 Generating {count} processed files ({size_mb}MB each) using {self.max_workers} threads...")
        print(f"💾 Starting memory usage: {self._get_memory_usage():.1f}MB")
        
        files = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file generation tasks
            futures = [
                executor.submit(self._generate_single_file, 'processed', i, size_mb)
                for i in range(count)
            ]
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    files.append(result)
                    generated, uploaded = self._get_progress()
                    current_memory = self._get_memory_usage()
                    print(f"  ✅ Progress: {uploaded}/{generated} files uploaded (Memory: {current_memory:.1f}MB)")
        
        # Force cleanup after all files are processed
        collected, final_memory = self._force_cleanup()
        print(f"🧹 Cleanup: {collected} objects collected, Memory: {final_memory:.1f}MB")
        
        return files
    
    def generate_analysis_results(self, count: int = 30) -> list:
        """
        Generate analysis result files directly to S3 using threading with memory management.
        
        Args:
            count: Number of files to generate
            
        Returns:
            List of generated file names (for tracking)
        """
        print(f"🚀 Generating {count} analysis files using {self.max_workers} threads...")
        print(f"💾 Starting memory usage: {self._get_memory_usage():.1f}MB")
        
        files = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file generation tasks
            futures = [
                executor.submit(self._generate_single_file, 'analysis', i)
                for i in range(count)
            ]
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    files.append(result)
                    generated, uploaded = self._get_progress()
                    current_memory = self._get_memory_usage()
                    print(f"  ✅ Progress: {uploaded}/{generated} files uploaded (Memory: {current_memory:.1f}MB)")
        
        # Force cleanup after all files are processed
        collected, final_memory = self._force_cleanup()
        print(f"🧹 Cleanup: {collected} objects collected, Memory: {final_memory:.1f}MB")
        
        return files
    
    def generate_published_datasets(self, count: int = 15) -> list:
        """
        Generate published dataset files directly to S3 using threading with memory management.
        
        Args:
            count: Number of files to generate
            
        Returns:
            List of generated file names (for tracking)
        """
        print(f"🚀 Generating {count} published files using {self.max_workers} threads...")
        print(f"💾 Starting memory usage: {self._get_memory_usage():.1f}MB")
        
        files = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file generation tasks
            futures = [
                executor.submit(self._generate_single_file, 'published', i)
                for i in range(count)
            ]
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                if result:
                    files.append(result)
                    generated, uploaded = self._get_progress()
                    current_memory = self._get_memory_usage()
                    print(f"  ✅ Progress: {uploaded}/{generated} files uploaded (Memory: {current_memory:.1f}MB)")
        
        # Force cleanup after all files are processed
        collected, final_memory = self._force_cleanup()
        print(f"🧹 Cleanup: {collected} objects collected, Memory: {final_memory:.1f}MB")
        
        return files
    
    def _generate_json_analysis_data(self) -> bytes:
        """Generate JSON analysis data in memory."""
        data = {
            "analysis_id": fake.uuid4(),
            "timestamp": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
            "telescope": fake.random_element(elements=('COSMOS-7', 'HUBBLE', 'JAMES_WEBB')),
            "target": fake.random_element(elements=('M31', 'M87', 'NGC_1234', 'PSR_J0007+7303')),
            "exposure_time": fake.random_int(min=100, max=3600),
            "magnitude": round(fake.random.uniform(10.0, 25.0), 2),
            "coordinates": {
                "ra": round(fake.random.uniform(0, 360), 6),
                "dec": round(fake.random.uniform(-90, 90), 6)
            },
            "data_quality": fake.random_element(elements=('EXCELLENT', 'GOOD', 'FAIR', 'POOR')),
            "processing_version": f"v{fake.random_int(min=1, max=5)}.{fake.random_int(min=0, max=9)}",
            "results": {
                "detected_objects": fake.random_int(min=0, max=100),
                "signal_to_noise": round(fake.random.uniform(1.0, 100.0), 2),
                "background_level": round(fake.random.uniform(0.1, 10.0), 3)
            }
        }
        return json.dumps(data, indent=2).encode('utf-8')
    
    def _generate_csv_analysis_data(self) -> bytes:
        """Generate CSV analysis data in memory."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['timestamp', 'object_id', 'magnitude', 'ra', 'dec', 'quality'])
        
        for _ in range(fake.random_int(min=10, max=100)):
            writer.writerow([
                fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                fake.uuid4()[:8],
                round(fake.random.uniform(10.0, 25.0), 2),
                round(fake.random.uniform(0, 360), 6),
                round(fake.random.uniform(-90, 90), 6),
                fake.random_element(elements=('EXCELLENT', 'GOOD', 'FAIR', 'POOR'))
            ])
        
        return output.getvalue().encode('utf-8')
    
    def _generate_text_analysis_data(self) -> bytes:
        """Generate text analysis data in memory."""
        content = f"Analysis Report\n"
        content += f"Generated: {datetime.now().isoformat()}\n"
        content += f"Analysis ID: {fake.uuid4()}\n"
        content += f"Telescope: {fake.random_element(elements=('COSMOS-7', 'HUBBLE', 'JAMES_WEBB'))}\n"
        content += f"Target: {fake.random_element(elements=('M31', 'M87', 'NGC_1234'))}\n\n"
        content += f"Summary:\n"
        content += f"{fake.paragraph(nb_sentences=5)}\n\n"
        content += f"Results:\n"
        content += f"- Detected objects: {fake.random_int(min=0, max=100)}\n"
        content += f"- Signal to noise ratio: {round(fake.random.uniform(1.0, 100.0), 2)}\n"
        content += f"- Data quality: {fake.random_element(elements=('EXCELLENT', 'GOOD', 'FAIR', 'POOR'))}\n"
        
        return content.encode('utf-8')
    
    def _generate_json_dataset_data(self) -> bytes:
        """Generate JSON dataset data in memory."""
        dataset = {
            "dataset_id": fake.uuid4(),
            "title": fake.sentence(nb_words=6),
            "authors": [fake.name() for _ in range(fake.random_int(min=1, max=5))],
            "publication_date": fake.date_between(start_date='-2y', end_date='now').isoformat(),
            "telescope": fake.random_element(elements=('COSMOS-7', 'HUBBLE', 'JAMES_WEBB')),
            "wavelength": fake.random_element(elements=('optical', 'infrared', 'radio', 'x-ray')),
            "target_objects": [fake.random_element(elements=('M31', 'M87', 'NGC_1234', 'PSR_J0007+7303')) for _ in range(fake.random_int(min=1, max=10))],
            "data_size_gb": round(fake.random.uniform(0.1, 100.0), 2),
            "observations": fake.random_int(min=10, max=1000),
            "keywords": [fake.word() for _ in range(fake.random_int(min=3, max=10))],
            "license": fake.random_element(elements=('MIT', 'Apache-2.0', 'CC-BY-4.0', 'Proprietary')),
            "doi": f"10.1000/{fake.random_int(min=100000, max=999999)}"
        }
        return json.dumps(dataset, indent=2).encode('utf-8')
    
    def _generate_pdf_dataset_data(self) -> bytes:
        """Generate PDF-like dataset data in memory."""
        content = f"%PDF-1.4\n"
        content += f"1 0 obj\n"
        content += f"<<\n"
        content += f"/Type /Catalog\n"
        content += f"/Pages 2 0 R\n"
        content += f">>\n"
        content += f"endobj\n\n"
        content += f"2 0 obj\n"
        content += f"<<\n"
        content += f"/Type /Pages\n"
        content += f"/Kids [3 0 R]\n"
        content += f"/Count 1\n"
        content += f">>\n"
        content += f"endobj\n\n"
        content += f"3 0 obj\n"
        content += f"<<\n"
        content += f"/Type /Page\n"
        content += f"/Parent 2 0 R\n"
        content += f"/MediaBox [0 0 612 792]\n"
        content += f"/Contents 4 0 R\n"
        content += f">>\n"
        content += f"endobj\n\n"
        content += f"4 0 obj\n"
        content += f"<<\n"
        content += f"/Length 44\n"
        content += f">>\n"
        content += f"stream\n"
        content += f"BT\n"
        content += f"/F1 12 Tf\n"
        content += f"72 720 Td\n"
        content += f"(Dataset: {fake.sentence(nb_words=4)}) Tj\n"
        content += f"ET\n"
        content += f"endstream\n"
        content += f"endobj\n"
        content += f"xref\n"
        content += f"0 5\n"
        content += f"0000000000 65535 f \n"
        content += f"0000000009 00000 n \n"
        content += f"0000000058 00000 n \n"
        content += f"0000000115 00000 n \n"
        content += f"0000000204 00000 n \n"
        content += f"trailer\n"
        content += f"<<\n"
        content += f"/Size 5\n"
        content += f"/Root 1 0 R\n"
        content += f">>\n"
        content += f"startxref\n"
        content += f"298\n"
        content += f"%%EOF\n"
        return content.encode('utf-8')
    
    def _generate_binary_dataset_data(self) -> bytes:
        """Generate binary dataset data in memory."""
        size_mb = fake.random_int(min=1, max=10)
        header = f"BINARY_DATASET_V1.0\nSize: {size_mb}MB\nTimestamp: {datetime.now().isoformat()}\n"
        header_bytes = header.encode('utf-8')
        
        # Fill with random binary data
        remaining_size = (size_mb * 1024 * 1024) - len(header_bytes)
        return header_bytes + os.urandom(remaining_size)
    
    def _generate_text_dataset_data(self) -> bytes:
        """Generate text dataset data in memory."""
        content = f"Dataset: {fake.sentence(nb_words=4)}\n"
        content += f"Generated: {datetime.now().isoformat()}\n"
        content += f"Description: {fake.paragraph(nb_sentences=3)}\n\n"
        content += f"Data Points:\n"
        for i in range(fake.random_int(min=20, max=100)):
            content += f"{i:03d}: {fake.random.uniform(0, 100):.6f}\n"
        
        return content.encode('utf-8')
    
    
    def generate_all_data(self, 
                         raw_files: int = 10,
                         processed_files: int = 20,
                         analysis_files: int = 30,
                         published_files: int = 15,
                         raw_size_mb: int = 100,
                         processed_size_mb: int = 50):
        """
        Generate all types of test data.
        
        Args:
            raw_files: Number of raw data files to generate
            processed_files: Number of processed data files to generate
            analysis_files: Number of analysis result files to generate
            published_files: Number of published dataset files to generate
            raw_size_mb: Size of raw data files in MB
            processed_size_mb: Size of processed data files in MB
        """
        print("🚀 Starting test data generation...")
        print(f"⚡ Using {self.max_workers} threads for concurrent uploads")
        
        # Generate different types of data
        raw_files_list = self.generate_large_files(raw_files, raw_size_mb)
        processed_files_list = self.generate_processed_data(processed_files, processed_size_mb)
        analysis_files_list = self.generate_analysis_results(analysis_files)
        published_files_list = self.generate_published_datasets(published_files)
        
        print(f"\n✅ Data generation complete!")
        print(f"📊 Generated {len(raw_files_list)} raw files")
        print(f"📊 Generated {len(processed_files_list)} processed files")
        print(f"📊 Generated {len(analysis_files_list)} analysis files")
        print(f"📊 Generated {len(published_files_list)} published files")
        print(f"📁 Total files: {len(raw_files_list) + len(processed_files_list) + len(analysis_files_list) + len(published_files_list)}")
    


def main():
    """Main entry point for the data generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for various lab scenarios")
    parser.add_argument("--lab-type", default="lab4", choices=["lab1", "lab4"], 
                       help="Type of lab (lab1 for storage testing, lab4 for snapshot testing)")
    parser.add_argument("--raw-files", type=int, default=10, help="Number of raw data files")
    parser.add_argument("--processed-files", type=int, default=20, help="Number of processed data files")
    parser.add_argument("--analysis-files", type=int, default=30, help="Number of analysis files")
    parser.add_argument("--published-files", type=int, default=15, help="Number of published files")
    parser.add_argument("--raw-size-mb", type=int, default=100, help="Size of raw files in MB")
    parser.add_argument("--processed-size-mb", type=int, default=50, help="Size of processed files in MB")
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum number of threads for concurrent uploads")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.lab_type, args.max_workers)
    
    # Show lab-specific information
    lab_views = generator.get_lab_views()
    print(f"🎯 Generating test data for {args.lab_type.upper()}")
    print(f"⚡ Threading: {args.max_workers} concurrent workers")
    print(f"🔗 Configured VAST views:")
    for view in lab_views:
        print(f"   - {view}")
    
    # Show bucket mapping - this MUST execute
    print("DEBUG_START: Bucket mapping section", flush=True)
    try:
        bucket_mapping = generator.get_bucket_mapping()
        print(f"🪣 Configured S3 buckets:", flush=True)
        if not bucket_mapping:
            print(f"   ⚠️  No bucket mapping found!", flush=True)
        else:
            for data_type, bucket_name in sorted(bucket_mapping.items()):
                if bucket_name:
                    print(f"   - {data_type}: {bucket_name}", flush=True)
                else:
                    print(f"   - {data_type}: ❌ NOT CONFIGURED (bucket_name missing in config)", flush=True)
    except Exception as e:
        import traceback
        print(f"⚠️  Error retrieving bucket mapping: {e}", flush=True)
        traceback.print_exc()
    print("DEBUG_END: Bucket mapping section", flush=True)
    print()
    
    generator.generate_all_data(
        raw_files=args.raw_files,
        processed_files=args.processed_files,
        analysis_files=args.analysis_files,
        published_files=args.published_files,
        raw_size_mb=args.raw_size_mb,
        processed_size_mb=args.processed_size_mb
    )


if __name__ == "__main__":
    main()
