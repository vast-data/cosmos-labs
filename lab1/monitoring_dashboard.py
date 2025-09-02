# monitoring_dashboard.py
import time
import json
from datetime import datetime
from vastpy import VASTClient
from lab1_config import Lab1ConfigLoader

class StorageDashboard:
    """Real-time storage monitoring dashboard"""
    
    def __init__(self):
        self.config = Lab1ConfigLoader()
        vast_config = self.config.get_vast_config()
        self.client = VASTClient(
            user=vast_config['user'],
            password=vast_config.get('password'),
            address=vast_config['address'],
            token=vast_config.get('token'),
            version=vast_config.get('version', 'v1')
        )
        
        # Get view paths from the correct config structure
        view_paths = self.config.get_data_directories()
        if not view_paths:
            # Fallback to default paths if config is missing
            self.view_paths = ['/cosmos7/raw', '/cosmos7/processed', '/cosmos7/temp']
            print("⚠️  Warning: No data directories configured, using defaults")
        else:
            # Use first 3 directories from config, or all if less than 3
            self.view_paths = view_paths[:3] if len(view_paths) >= 3 else view_paths
        
        print(f"📁 Monitoring {len(self.view_paths)} view paths: {', '.join(self.view_paths)}")
    
    def get_view_status(self, view_path: str) -> dict:
        """Get detailed status for a specific view"""
        try:
            # Check if we can connect to VAST
            if not hasattr(self.client, 'views') or self.client.views is None:
                return {
                    'path': view_path,
                    'status': 'CONNECTION_ERROR',
                    'error': 'VAST client not properly initialized',
                    'utilization': 0,
                    'size': 0,
                    'quota': 0,
                    'available': 0
                }
            
            views = self.client.views.get(path=view_path)
            if not views:
                return {
                    'path': view_path,
                    'status': 'NOT_FOUND',
                    'utilization': 0,
                    'size': 0,
                    'quota': 0,
                    'available': 0
                }
            
            view = views[0]
            view_id = view['id']
            
            # Get detailed information
            view_details = self.client.views[view_id].get()
            
            # Debug: Let's see what the VAST API actually returns
            print(f"🔍 VAST API response for view {view_path}:")
            print(f"   View ID: {view_id}")
            print(f"   Available fields: {list(view_details.keys())}")
            print(f"   Raw size value: {view_details.get('size')}")
            print(f"   Raw quota value: {view_details.get('quota')}")
            print(f"   Physical capacity: {view_details.get('physical_capacity')}")
            print(f"   Logical capacity: {view_details.get('logical_capacity')}")
            
            # Try different possible field names for size and quota
            size = 0
            quota = 0
            
            # Common field names for size (try VAST-specific fields first)
            size_fields = ['logical_capacity', 'physical_capacity', 'size', 'used_size', 'used_bytes', 'bytes_used', 'storage_used']
            for field in size_fields:
                if field in view_details and view_details[field] is not None:
                    size = view_details[field]
                    print(f"   Found size in field '{field}': {size}")
                    break
            
            # Common field names for quota (try VAST-specific fields first)
            quota_fields = ['quota', 'quota_size', 'quota_bytes', 'max_size', 'max_bytes', 'storage_limit']
            for field in quota_fields:
                if field in view_details and view_details[field] is not None:
                    quota = view_details[field]
                    print(f"   Found quota in field '{field}': {quota}")
                    break
            
            # Convert to int if they're strings or floats
            try:
                size = int(float(size)) if size is not None else 0
                quota = int(float(quota)) if quota is not None else 0
            except (ValueError, TypeError):
                size = 0
                quota = 0
            
            print(f"   Final values - Size: {size} bytes, Quota: {quota} bytes")
            
            if quota > 0:
                utilization = (size / quota) * 100
                available = quota - size
            else:
                utilization = 0
                available = 0
            
            return {
                'path': view_path,
                'status': self._get_status_level(utilization),
                'utilization': round(utilization, 1),
                'size_tb': round(size / (1024**3), 2),
                'quota_tb': round(quota / (1024**3), 2),
                'available_tb': round(available / (1024**3), 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'path': view_path,
                'status': 'ERROR',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
    
    def _get_status_level(self, utilization: float) -> str:
        """Determine status level based on utilization"""
        if utilization >= self.config.get_critical_threshold():
            return 'CRITICAL'
        elif utilization >= self.config.get_alert_threshold():
            return 'WARNING'
        else:
            return 'NORMAL'
    
    def generate_dashboard_data(self) -> dict:
        """Generate complete dashboard data"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'views': {},
            'summary': {
                'total_views': len(self.view_paths),
                'critical_views': 0,
                'warning_views': 0,
                'normal_views': 0
            }
        }
        
        for view_path in self.view_paths:
            view_status = self.get_view_status(view_path)
            dashboard_data['views'][view_path] = view_status
            
            # Update summary
            if view_status['status'] == 'CRITICAL':
                dashboard_data['summary']['critical_views'] += 1
            elif view_status['status'] == 'WARNING':
                dashboard_data['summary']['warning_views'] += 1
            else:
                dashboard_data['summary']['normal_views'] += 1
        
        return dashboard_data
    
    def print_dashboard(self):
        """Print a formatted dashboard to console"""
        dashboard = self.generate_dashboard_data()
        
        print("\n" + "="*80)
        print("ORBITAL DYNAMICS - STORAGE MONITORING DASHBOARD")
        print("="*80)
        print(f"Last Updated: {dashboard['timestamp']}")
        print()
        
        # Summary
        summary = dashboard['summary']
        print(f"SUMMARY: {summary['normal_views']} Normal | {summary['warning_views']} Warning | {summary['critical_views']} Critical")
        print()
        
        # View details
        for view_path, view_data in dashboard['views'].items():
            status_icon = {
                'NORMAL': '🟢',
                'WARNING': '🟡',
                'CRITICAL': '🔴',
                'ERROR': '⚫',
                'NOT_FOUND': '❓',
                'CONNECTION_ERROR': '🔌'
            }.get(view_data['status'], '❓')
            
            print(f"{status_icon} {view_path}")
            
            if view_data['status'] in ['NORMAL', 'WARNING', 'CRITICAL']:
                print(f"   Utilization: {view_data['utilization']}%")
                print(f"   Size: {view_data['size_tb']} TB / {view_data['quota_tb']} TB")
                print(f"   Available: {view_data['available_tb']} TB")
            elif view_data['status'] in ['ERROR', 'CONNECTION_ERROR']:
                print(f"   Error: {view_data.get('error', 'Unknown error')}")
            else:
                print(f"   Status: {view_data['status']}")
            
            print()
        
        print("="*80)

def main():
    """Main function for dashboard"""
    config = Lab1ConfigLoader()
    dashboard = StorageDashboard()
    
    try:
        while True:
            dashboard.print_dashboard()
            refresh_interval = config.get('dashboard.refresh_interval_seconds', 60)
            time.sleep(refresh_interval)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")

if __name__ == "__main__":
    main() 