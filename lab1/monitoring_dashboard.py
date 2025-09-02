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
        # Build VAST client parameters dynamically based on what's available
        # vastpy constructs URLs as https://{address}/... so we need to strip protocol
        address = vast_config['address']
        if address.startswith('https://'):
            address = address[8:]  # Remove 'https://' prefix
        elif address.startswith('http://'):
            address = address[7:]   # Remove 'http://' prefix
        
        client_params = {
            'user': vast_config['user'],
            'password': vast_config['password'],
            'address': address
        }
        
        # Add optional parameters only if they exist and are supported
        if vast_config.get('token'):
            client_params['token'] = vast_config['token']
        if vast_config.get('version'):
            client_params['version'] = vast_config['version']
        
        try:
            self.client = VASTClient(**client_params)
        except TypeError as e:
            # Handle unsupported parameters gracefully
            if "tenant_name" in str(e):
                print("⚠️  tenant_name parameter not supported in this vastpy version, retrying without it")
                # Remove tenant_name and retry
                if 'tenant_name' in client_params:
                    del client_params['tenant_name']
                self.client = VASTClient(**client_params)
            else:
                # Re-raise other TypeError exceptions
                raise
        
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
            
            # Get detailed information from view
            view_details = self.client.views[view_id].get()
            
            # Get quota information from quotas endpoint
            quotas = self.client.quotas.get(path=view_path)
            
            # Debug: Let's see what the VAST API actually returns
            print(f"🔍 VAST API response for view {view_path}:")
            print(f"   View ID: {view_id}")
            print(f"   Available fields: {list(view_details.keys())}")
            print(f"   Physical capacity: {view_details.get('physical_capacity')}")
            print(f"   Logical capacity: {view_details.get('logical_capacity')}")
            
            # Get size from view details
            size = view_details.get('logical_capacity', 0)
            print(f"   Found size in field 'logical_capacity': {size}")
            
            # Get quota information
            soft_limit = 0
            hard_limit = 0
            if quotas:
                quota_info = quotas[0]
                soft_limit = quota_info.get('soft_limit', 0)
                hard_limit = quota_info.get('hard_limit', 0)
                used_capacity = quota_info.get('used_capacity', 0)
                print(f"   Quota info: used={used_capacity}, soft_limit={soft_limit}, hard_limit={hard_limit}")
                # Use the quota's used capacity if available, otherwise use view's logical capacity
                if used_capacity > 0:
                    size = used_capacity
            else:
                print(f"   No quota found for path: {view_path}")
            
            # Convert to int if they're strings or floats
            try:
                size = int(float(size)) if size is not None else 0
                soft_limit = int(float(soft_limit)) if soft_limit is not None else 0
                hard_limit = int(float(hard_limit)) if hard_limit is not None else 0
            except (ValueError, TypeError):
                size = 0
                soft_limit = 0
                hard_limit = 0
            
            print(f"   Final values - Size: {size} bytes, Soft Limit: {soft_limit} bytes, Hard Limit: {hard_limit} bytes")
            
            # Use soft limit for utilization calculation if available, otherwise hard limit
            quota_for_calc = soft_limit if soft_limit > 0 else hard_limit
            if quota_for_calc > 0:
                utilization = (size / quota_for_calc) * 100
                available = quota_for_calc - size
            else:
                utilization = 0
                available = 0
            
            return {
                'path': view_path,
                'status': self._get_status_level(utilization),
                'utilization': round(utilization, 1),
                'size_tb': round(size / (1000**3), 2),
                'soft_limit_tb': round(soft_limit / (1000**3), 2),
                'hard_limit_tb': round(hard_limit / (1000**3), 2),
                'quota_tb': round(quota_for_calc / (1000**3), 2),  # The limit used for calculation
                'available_tb': round(available / (1000**3), 2),
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
                print(f"   Size: {view_data['size_tb']} TB")
                
                # Show quota limits
                if view_data['soft_limit_tb'] > 0 or view_data['hard_limit_tb'] > 0:
                    if view_data['soft_limit_tb'] > 0 and view_data['hard_limit_tb'] > 0:
                        print(f"   Soft Limit: {view_data['soft_limit_tb']} TB")
                        print(f"   Hard Limit: {view_data['hard_limit_tb']} TB")
                    elif view_data['soft_limit_tb'] > 0:
                        print(f"   Soft Limit: {view_data['soft_limit_tb']} TB")
                    elif view_data['hard_limit_tb'] > 0:
                        print(f"   Hard Limit: {view_data['hard_limit_tb']} TB")
                    
                    print(f"   Available: {view_data['available_tb']} TB")
                else:
                    print(f"   No quota set")
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