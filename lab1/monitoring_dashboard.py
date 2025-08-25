# monitoring_dashboard.py
import time
import json
from datetime import datetime
from vastpy import VASTClient
from config_loader import ConfigLoader

class StorageDashboard:
    """Real-time storage monitoring dashboard"""
    
    def __init__(self):
        self.config = ConfigLoader()
        self.client = VASTClient(**self.config.get_vast_config())
        self.view_paths = [
            self.config.get('storage.raw_data_path', '/cosmos7/raw'),
            self.config.get('storage.processed_data_path', '/cosmos7/processed'),
            self.config.get('storage.temp_data_path', '/cosmos7/temp')
        ]
    
    def get_view_status(self, view_path: str) -> dict:
        """Get detailed status for a specific view"""
        try:
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
            
            size = view_details.get('size', 0)
            quota = view_details.get('quota', 0)
            
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
        if utilization >= self.config.get('quotas.critical_threshold', 85):
            return 'CRITICAL'
        elif utilization >= self.config.get('quotas.warning_threshold', 75):
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
                'NOT_FOUND': '❓'
            }.get(view_data['status'], '❓')
            
            print(f"{status_icon} {view_path}")
            
            if view_data['status'] in ['NORMAL', 'WARNING', 'CRITICAL']:
                print(f"   Utilization: {view_data['utilization']}%")
                print(f"   Size: {view_data['size_tb']} TB / {view_data['quota_tb']} TB")
                print(f"   Available: {view_data['available_tb']} TB")
            elif view_data['status'] == 'ERROR':
                print(f"   Error: {view_data.get('error', 'Unknown error')}")
            else:
                print(f"   Status: {view_data['status']}")
            
            print()
        
        print("="*80)

def main():
    """Main function for dashboard"""
    config = ConfigLoader()
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