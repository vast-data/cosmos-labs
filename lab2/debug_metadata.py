#!/usr/bin/env python3
"""
Debug script to examine raw metadata from VAST Database
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from lab2.vast_database_manager import VASTDatabaseManager
from config_loader import ConfigLoader
import json

def debug_metadata():
    """Debug function to examine raw metadata structure"""
    print("🔍 Debug: Examining raw metadata from VAST Database")
    print("=" * 60)
    
    # Load config
    config = ConfigLoader(
        str(Path(__file__).parent.parent / "config.yaml"),
        str(Path(__file__).parent.parent / "secrets.yaml")
    )
    
    db_manager = VASTDatabaseManager(config)
    
    try:
        if not db_manager.connect():
            print("❌ Failed to connect to database")
            return
        
        print("✅ Connected to VAST Database")
        
        # Get a few records to examine
        with db_manager.connection.transaction() as tx:
            bucket = tx.bucket(db_manager.bucket_name)
            schema = bucket.schema(db_manager.schema_name)
            table = schema.table("swift_metadata")
            
            print(f"\n📊 Table: {db_manager.bucket_name}.{db_manager.schema_name}.swift_metadata")
            
            # Get first batch of data
            from vastdb.config import QueryConfig
            config_query = QueryConfig(
                num_splits=1,
                num_sub_splits=1,
                limit_rows_per_sub_split=3,  # Just get 3 records for debugging
            )
            
            reader = table.select(config=config_query)
            
            try:
                first_batch = next(reader)
                print(f"\n📋 Batch info:")
                print(f"   - Number of rows: {len(first_batch)}")
                print(f"   - Column names: {first_batch.column_names}")
                print(f"   - Schema: {first_batch.schema}")
                
                print(f"\n🔍 Raw data for first 3 records:")
                print("-" * 60)
                
                for i in range(min(3, len(first_batch))):
                    print(f"\nRecord {i+1}:")
                    print(f"  File name: {first_batch['file_name'][i].as_py() if first_batch['file_name'][i] is not None else 'None'}")
                    
                    # Show all columns and their values
                    for col_name in first_batch.column_names:
                        value = first_batch[col_name][i]
                        if value is not None:
                            py_value = value.as_py()
                            print(f"  {col_name}: {py_value} (type: {type(py_value).__name__})")
                        else:
                            print(f"  {col_name}: None")
                
                print(f"\n🔍 Column details:")
                print("-" * 60)
                for col_name in first_batch.column_names:
                    col_data = first_batch[col_name]
                    print(f"  {col_name}:")
                    print(f"    - Type: {col_data.type}")
                    print(f"    - Null count: {col_data.null_count}")
                    print(f"    - Length: {len(col_data)}")
                    if len(col_data) > 0:
                        sample_value = col_data[0]
                        print(f"    - Sample value: {sample_value.as_py() if sample_value is not None else 'None'}")
                
            except StopIteration:
                print("❌ No data found in table")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_manager.close()

if __name__ == "__main__":
    debug_metadata()
