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
    
    def __init__(self, output_dir: str = "test_data", lab_type: str = "lab4"):
        """
        Initialize the data generator.
        
        Args:
            output_dir: Directory to generate test data in
            lab_type: Type of lab (lab1, lab4, etc.) to determine data structure
        """
        self.output_dir = Path(output_dir)
        self.lab_type = lab_type
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different data types
        self.raw_dir = self.output_dir / "raw"
        self.processed_dir = self.output_dir / "processed"
        self.analysis_dir = self.output_dir / "analysis"
        self.published_dir = self.output_dir / "published"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.analysis_dir, self.published_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Load lab-specific configuration if available
        self.lab_config = self._load_lab_config()
        
        # Initialize S3 client for VAST uploads
        self.s3_client = self._init_s3_client()
    
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
                'analysis': views_config.get('analysis_data', {}).get('bucket_name'),
                'published': views_config.get('published_data', {}).get('bucket_name')
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
            ssl_verify = s3_config.get('ssl_verify', True)
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
    
    def generate_large_files(self, count: int = 10, size_mb: int = 100) -> list:
        """
        Generate large binary files using dd or elbencho.
        
        Args:
            count: Number of files to generate
            size_mb: Size of each file in MB
            
        Returns:
            List of generated file paths
        """
        files = []
        
        for i in range(count):
            filename = f"telescope_data_{i:03d}.dat"
            filepath = self.raw_dir / filename
            
            # Try elbencho first, fall back to dd
            try:
                # Use elbencho for efficient large file generation
                cmd = [
                    "elbencho", "--create", "--size", f"{size_mb}M",
                    "--file", str(filepath), "--threads", "1"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fall back to dd if elbencho is not available
                cmd = [
                    "dd", "if=/dev/urandom", f"of={filepath}",
                    "bs=1M", f"count={size_mb}", "status=none"
                ]
                subprocess.run(cmd, check=True)
            
            files.append(filepath)
            print(f"Generated large file: {filepath} ({size_mb}MB)")
            
            # Upload to S3
            self._upload_file_to_appropriate_bucket(filepath, 'raw')
        
        return files
    
    def generate_processed_data(self, count: int = 20, size_mb: int = 50) -> list:
        """
        Generate processed data files (medium-sized files).
        
        Args:
            count: Number of files to generate
            size_mb: Size of each file in MB
            
        Returns:
            List of generated file paths
        """
        files = []
        
        for i in range(count):
            filename = f"processed_data_{i:03d}.dat"
            filepath = self.processed_dir / filename
            
            # Generate file with some structure (header + random data)
            with open(filepath, 'wb') as f:
                # Write a simple header
                header = f"PROCESSED_DATA_V1.0\nFile: {filename}\nTimestamp: {datetime.now().isoformat()}\n"
                f.write(header.encode('utf-8'))
                
                # Fill rest with random data
                remaining_size = (size_mb * 1024 * 1024) - len(header)
                f.write(os.urandom(remaining_size))
            
            files.append(filepath)
            print(f"Generated processed file: {filepath} ({size_mb}MB)")
            
            # Upload to S3
            self._upload_file_to_appropriate_bucket(filepath, 'processed')
        
        return files
    
    def generate_analysis_results(self, count: int = 30) -> list:
        """
        Generate analysis result files (small structured files).
        
        Args:
            count: Number of files to generate
            
        Returns:
            List of generated file paths
        """
        files = []
        
        for i in range(count):
            # Generate different types of analysis files
            file_types = ['json', 'csv', 'txt']
            file_type = random.choice(file_types)
            filename = f"analysis_result_{i:03d}.{file_type}"
            filepath = self.analysis_dir / filename
            
            if file_type == 'json':
                self._generate_json_analysis(filepath)
            elif file_type == 'csv':
                self._generate_csv_analysis(filepath)
            else:
                self._generate_text_analysis(filepath)
            
            files.append(filepath)
            print(f"Generated analysis file: {filepath}")
            
            # Upload to S3
            self._upload_file_to_appropriate_bucket(filepath, 'analysis')
        
        return files
    
    def generate_published_datasets(self, count: int = 15) -> list:
        """
        Generate published dataset files (mixed content).
        
        Args:
            count: Number of files to generate
            
        Returns:
            List of generated file paths
        """
        files = []
        
        for i in range(count):
            # Generate different types of published data
            file_types = ['pdf', 'txt', 'json', 'dat']
            file_type = random.choice(file_types)
            filename = f"published_dataset_{i:03d}.{file_type}"
            filepath = self.published_dir / filename
            
            if file_type == 'pdf':
                self._generate_pdf_dataset(filepath)
            elif file_type == 'json':
                self._generate_json_dataset(filepath)
            elif file_type == 'dat':
                self._generate_binary_dataset(filepath)
            else:
                self._generate_text_dataset(filepath)
            
            files.append(filepath)
            print(f"Generated published file: {filepath}")
            
            # Upload to S3
            self._upload_file_to_appropriate_bucket(filepath, 'published')
        
        return files
    
    def _generate_json_analysis(self, filepath: Path):
        """Generate JSON analysis file."""
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
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_csv_analysis(self, filepath: Path):
        """Generate CSV analysis file."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
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
    
    def _generate_text_analysis(self, filepath: Path):
        """Generate text analysis file."""
        with open(filepath, 'w') as f:
            f.write(f"Analysis Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Analysis ID: {fake.uuid4()}\n")
            f.write(f"Telescope: {fake.random_element(elements=('COSMOS-7', 'HUBBLE', 'JAMES_WEBB'))}\n")
            f.write(f"Target: {fake.random_element(elements=('M31', 'M87', 'NGC_1234'))}\n\n")
            f.write(f"Summary:\n")
            f.write(f"{fake.paragraph(nb_sentences=5)}\n\n")
            f.write(f"Results:\n")
            f.write(f"- Detected objects: {fake.random_int(min=0, max=100)}\n")
            f.write(f"- Signal to noise ratio: {round(fake.random.uniform(1.0, 100.0), 2)}\n")
            f.write(f"- Data quality: {fake.random_element(elements=('EXCELLENT', 'GOOD', 'FAIR', 'POOR'))}\n")
    
    def _generate_json_dataset(self, filepath: Path):
        """Generate JSON dataset file."""
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
        
        with open(filepath, 'w') as f:
            json.dump(dataset, f, indent=2)
    
    def _generate_pdf_dataset(self, filepath: Path):
        """Generate a simple PDF-like file (text file with PDF-like content)."""
        with open(filepath, 'w') as f:
            f.write(f"%PDF-1.4\n")
            f.write(f"1 0 obj\n")
            f.write(f"<<\n")
            f.write(f"/Type /Catalog\n")
            f.write(f"/Pages 2 0 R\n")
            f.write(f">>\n")
            f.write(f"endobj\n\n")
            f.write(f"2 0 obj\n")
            f.write(f"<<\n")
            f.write(f"/Type /Pages\n")
            f.write(f"/Kids [3 0 R]\n")
            f.write(f"/Count 1\n")
            f.write(f">>\n")
            f.write(f"endobj\n\n")
            f.write(f"3 0 obj\n")
            f.write(f"<<\n")
            f.write(f"/Type /Page\n")
            f.write(f"/Parent 2 0 R\n")
            f.write(f"/MediaBox [0 0 612 792]\n")
            f.write(f"/Contents 4 0 R\n")
            f.write(f">>\n")
            f.write(f"endobj\n\n")
            f.write(f"4 0 obj\n")
            f.write(f"<<\n")
            f.write(f"/Length 44\n")
            f.write(f">>\n")
            f.write(f"stream\n")
            f.write(f"BT\n")
            f.write(f"/F1 12 Tf\n")
            f.write(f"72 720 Td\n")
            f.write(f"(Dataset: {fake.sentence(nb_words=4)}) Tj\n")
            f.write(f"ET\n")
            f.write(f"endstream\n")
            f.write(f"endobj\n")
            f.write(f"xref\n")
            f.write(f"0 5\n")
            f.write(f"0000000000 65535 f \n")
            f.write(f"0000000009 00000 n \n")
            f.write(f"0000000058 00000 n \n")
            f.write(f"0000000115 00000 n \n")
            f.write(f"0000000204 00000 n \n")
            f.write(f"trailer\n")
            f.write(f"<<\n")
            f.write(f"/Size 5\n")
            f.write(f"/Root 1 0 R\n")
            f.write(f">>\n")
            f.write(f"startxref\n")
            f.write(f"298\n")
            f.write(f"%%EOF\n")
    
    def _generate_binary_dataset(self, filepath: Path):
        """Generate binary dataset file."""
        size_mb = fake.random_int(min=1, max=10)
        with open(filepath, 'wb') as f:
            # Write a simple header
            header = f"BINARY_DATASET_V1.0\nSize: {size_mb}MB\nTimestamp: {datetime.now().isoformat()}\n"
            f.write(header.encode('utf-8'))
            
            # Fill with random binary data
            remaining_size = (size_mb * 1024 * 1024) - len(header)
            f.write(os.urandom(remaining_size))
    
    def _generate_text_dataset(self, filepath: Path):
        """Generate text dataset file."""
        with open(filepath, 'w') as f:
            f.write(f"Dataset: {fake.sentence(nb_words=4)}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Description: {fake.paragraph(nb_sentences=3)}\n\n")
            f.write(f"Data Points:\n")
            for i in range(fake.random_int(min=20, max=100)):
                f.write(f"{i:03d}: {fake.random.uniform(0, 100):.6f}\n")
    
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
        print("🚀 Starting Lab 4 test data generation...")
        print(f"📁 Output directory: {self.output_dir}")
        
        # Generate different types of data
        raw_files_list = self.generate_large_files(raw_files, raw_size_mb)
        processed_files_list = self.generate_processed_data(processed_files, processed_size_mb)
        analysis_files_list = self.generate_analysis_results(analysis_files)
        published_files_list = self.generate_published_datasets(published_files)
        
        # Create a summary file
        self._create_summary_file(raw_files_list, processed_files_list, 
                                analysis_files_list, published_files_list)
        
        print(f"\n✅ Data generation complete!")
        print(f"📊 Generated {len(raw_files_list)} raw files")
        print(f"📊 Generated {len(processed_files_list)} processed files")
        print(f"📊 Generated {len(analysis_files_list)} analysis files")
        print(f"📊 Generated {len(published_files_list)} published files")
        print(f"📁 Total files: {len(raw_files_list) + len(processed_files_list) + len(analysis_files_list) + len(published_files_list)}")
    
    def _create_summary_file(self, raw_files, processed_files, analysis_files, published_files):
        """Create a summary file with generation details."""
        summary_path = self.output_dir / "generation_summary.txt"
        
        with open(summary_path, 'w') as f:
            f.write(f"{self.lab_type.upper()} Test Data Generation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Lab type: {self.lab_type}\n")
            f.write(f"Output directory: {self.output_dir}\n\n")
            
            f.write("File counts:\n")
            f.write(f"- Raw data files: {len(raw_files)}\n")
            f.write(f"- Processed data files: {len(processed_files)}\n")
            f.write(f"- Analysis result files: {len(analysis_files)}\n")
            f.write(f"- Published dataset files: {len(published_files)}\n")
            f.write(f"- Total files: {len(raw_files) + len(processed_files) + len(analysis_files) + len(published_files)}\n\n")
            
            f.write("Directory structure:\n")
            f.write(f"- {self.raw_dir}/\n")
            f.write(f"- {self.processed_dir}/\n")
            f.write(f"- {self.analysis_dir}/\n")
            f.write(f"- {self.published_dir}/\n\n")
            
            # Add lab-specific usage instructions
            lab_views = self.get_lab_views()
            f.write("Configured VAST views for this lab:\n")
            for view in lab_views:
                f.write(f"- {view}\n")
            f.write("\n")
            
            f.write("Next steps:\n")
            if self.lab_type == "lab1":
                f.write("1. Upload these files to your VAST views\n")
                f.write("2. Run lab1_solution.py to test storage monitoring\n")
                f.write("3. Test auto-expansion when views fill up\n")
            elif self.lab_type == "lab4":
                f.write("1. Upload these files to your VAST views\n")
                f.write("2. Set up protection policies using lab4_solution.py\n")
                f.write("3. Test snapshot creation and restoration\n")
            else:
                f.write("1. Upload these files to your VAST views\n")
                f.write("2. Use with your lab-specific testing\n")
        
        print(f"📄 Summary file created: {summary_path}")


def main():
    """Main entry point for the data generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for various lab scenarios")
    parser.add_argument("--output-dir", default="test_data", help="Output directory for test data")
    parser.add_argument("--lab-type", default="lab4", choices=["lab1", "lab4"], 
                       help="Type of lab (lab1 for storage testing, lab4 for snapshot testing)")
    parser.add_argument("--raw-files", type=int, default=10, help="Number of raw data files")
    parser.add_argument("--processed-files", type=int, default=20, help="Number of processed data files")
    parser.add_argument("--analysis-files", type=int, default=30, help="Number of analysis files")
    parser.add_argument("--published-files", type=int, default=15, help="Number of published files")
    parser.add_argument("--raw-size-mb", type=int, default=100, help="Size of raw files in MB")
    parser.add_argument("--processed-size-mb", type=int, default=50, help="Size of processed files in MB")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir, args.lab_type)
    
    # Show lab-specific information
    lab_views = generator.get_lab_views()
    print(f"🎯 Generating test data for {args.lab_type.upper()}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"🔗 Configured VAST views:")
    for view in lab_views:
        print(f"   - {view}")
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
