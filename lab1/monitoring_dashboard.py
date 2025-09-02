# monitoring_dashboard.py
import time
import json
from datetime import datetime
from vastpy import VASTClient
from lab1_config import Lab1ConfigLoader
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

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
        
        # Get refresh interval from config
        self.refresh_interval = self.config.get('monitoring.refresh_interval_seconds', 30)
        
        # Initialize Rich console
        self.console = Console()
        
        print(f"📁 Monitoring {len(self.view_paths)} view paths: {', '.join(self.view_paths)}")
        print(f"🔄 Auto-refresh every {self.refresh_interval} seconds")
    
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
            
            # Get size from view details
            size = view_details.get('logical_capacity', 0)
            
            # Get quota information
            soft_limit = 0
            hard_limit = 0
            if quotas:
                quota_info = quotas[0]
                soft_limit = quota_info.get('soft_limit', 0)
                hard_limit = quota_info.get('hard_limit', 0)
                used_capacity = quota_info.get('used_capacity', 0)
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
                'size_tb': round(size / (1000**4), 2),
                'soft_limit_tb': round(soft_limit / (1000**4), 2),
                'hard_limit_tb': round(hard_limit / (1000**4), 2),
                'quota_tb': round(quota_for_calc / (1000**4), 2),  # The limit used for calculation
                'available_tb': round(available / (1000**4), 2),
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
    
    def create_rich_dashboard(self):
        """Create a Rich-formatted dashboard"""
        dashboard = self.generate_dashboard_data()
        
        # Create main table
        table = Table(title="ORBITAL DYNAMICS - STORAGE MONITORING DASHBOARD", 
                     title_style="bold blue", 
                     show_header=True, 
                     header_style="bold magenta")
        
        # Add columns
        table.add_column("Path", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Utilization", justify="right", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Soft Limit", justify="right")
        table.add_column("Hard Limit", justify="right")
        table.add_column("Available", justify="right")
        
        # Add rows
        for view_path, view_data in dashboard['views'].items():
            status_icon = {
                'NORMAL': '🟢',
                'WARNING': '🟡',
                'CRITICAL': '🔴',
                'ERROR': '⚫',
                'NOT_FOUND': '❓',
                'CONNECTION_ERROR': '🔌'
            }.get(view_data['status'], '❓')
            
            if view_data['status'] in ['NORMAL', 'WARNING', 'CRITICAL']:
                utilization_text = f"{view_data['utilization']}%"
                size_text = f"{view_data['size_tb']} TB"
                soft_limit_text = f"{view_data['soft_limit_tb']} TB" if view_data['soft_limit_tb'] > 0 else "N/A"
                hard_limit_text = f"{view_data['hard_limit_tb']} TB" if view_data['hard_limit_tb'] > 0 else "N/A"
                available_text = f"{view_data['available_tb']} TB"
                
                # Color utilization based on level
                if view_data['utilization'] >= 90:
                    utilization_style = "bold red"
                elif view_data['utilization'] >= 75:
                    utilization_style = "bold yellow"
                else:
                    utilization_style = "green"
                
                table.add_row(
                    view_path,
                    status_icon,
                    Text(utilization_text, style=utilization_style),
                    size_text,
                    soft_limit_text,
                    hard_limit_text,
                    available_text
                )
            else:
                error_text = view_data.get('error', view_data['status'])
                table.add_row(
                    view_path,
                    status_icon,
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    Text(error_text, style="red")
                )
        
        # Create summary panel
        summary = dashboard['summary']
        summary_text = f"Normal: {summary['normal_views']} | Warning: {summary['warning_views']} | Critical: {summary['critical_views']}"
        summary_panel = Panel(summary_text, title="Summary", border_style="green")
        
        # Create timestamp panel
        timestamp_text = f"Last Updated: {dashboard['timestamp']}"
        timestamp_panel = Panel(timestamp_text, border_style="blue")
        
        # Combine everything using Rich's Group
        return Panel(
            Group(summary_panel, table, timestamp_panel),
            border_style="bright_blue"
        )

def main():
    """Main function for dashboard"""
    config = Lab1ConfigLoader()
    dashboard = StorageDashboard()
    
    try:
        # Use Rich Live display for auto-refresh
        with Live(dashboard.create_rich_dashboard(), refresh_per_second=1, console=dashboard.console) as live:
            while True:
                live.update(dashboard.create_rich_dashboard())
                time.sleep(dashboard.refresh_interval)
    except KeyboardInterrupt:
        dashboard.console.print("\n[bold red]Dashboard stopped by user[/bold red]")

if __name__ == "__main__":
    main() 