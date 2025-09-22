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
        
        # Get view paths from the lab1.views configuration
        views_config = self.config.get('lab1.views', {})
        if not views_config:
            # Fallback to default paths if config is missing
            self.view_paths = ['/cosmos7/raw', '/cosmos7/processed']
            print("⚠️  Warning: No lab1.views configured, using defaults")
        else:
            # Extract paths from the views configuration
            self.view_paths = []
            for view_name, view_config in views_config.items():
                if 'path' in view_config:
                    self.view_paths.append(view_config['path'])
        
        # Get refresh interval from config
        self.refresh_interval = self.config.get('lab1.monitoring.refresh_interval_seconds', 30)
        
        # Initialize Rich console
        self.console = Console()
        
        print(f"📁 Monitoring {len(self.view_paths)} view paths: {', '.join(self.view_paths)}")
        print(f"🔄 Auto-refresh every {self.refresh_interval} seconds")
    
    def format_storage_size(self, bytes_value: int) -> str:
        """Format storage size with appropriate unit (MB, GB, TB, PB)"""
        if bytes_value == 0:
            return "0 B"
        
        # Convert to appropriate unit
        if bytes_value >= 1000**5:  # PB
            return f"{bytes_value / (1000**5):.2f} PB"
        elif bytes_value >= 1000**4:  # TB
            return f"{bytes_value / (1000**4):.2f} TB"
        elif bytes_value >= 1000**3:  # GB
            return f"{bytes_value / (1000**3):.2f} GB"
        elif bytes_value >= 1000**2:  # MB
            return f"{bytes_value / (1000**2):.2f} MB"
        else:  # KB or bytes
            return f"{bytes_value / 1000:.2f} KB"
    
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
            
            # Get quota information first
            soft_limit = 0
            hard_limit = 0
            size = 0
            
            if quotas:
                quota_info = quotas[0]
                soft_limit = quota_info.get('soft_limit', 0)
                hard_limit = quota_info.get('hard_limit', 0)
                used_capacity = quota_info.get('used_capacity', 0)
                # Use the quota's used capacity for size (this is what utilization is based on)
                size = used_capacity
            else:
                print(f"   No quota found for path: {view_path}")
                # Fallback to view's logical capacity if no quota
                size = view_details.get('logical_capacity', 0)
            
            # Convert to int if they're strings or floats
            try:
                size = int(float(size)) if size is not None else 0
                soft_limit = int(float(soft_limit)) if soft_limit is not None else 0
                hard_limit = int(float(hard_limit)) if hard_limit is not None else 0
            except (ValueError, TypeError):
                size = 0
                soft_limit = 0
                hard_limit = 0
            
            # Use hard limit for utilization calculation (actual storage capacity)
            quota_for_calc = hard_limit if hard_limit > 0 else soft_limit
            if quota_for_calc > 0:
                utilization = (size / quota_for_calc) * 100
                # Available should be based on hard limit (actual storage limit)
                available_limit = hard_limit if hard_limit > 0 else soft_limit
                available = available_limit - size
            else:
                utilization = 0
                available = 0
            
            return {
                'path': view_path,
                'status': self._get_status_level(utilization),
                'utilization': round(utilization, 1),
                'size_formatted': self.format_storage_size(size),
                'soft_limit_formatted': self.format_storage_size(soft_limit),
                'hard_limit_formatted': self.format_storage_size(hard_limit),
                'available_formatted': self.format_storage_size(available),
                'size_bytes': size,  # Raw values for comparison
                'soft_limit_bytes': soft_limit,
                'hard_limit_bytes': hard_limit,
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
                # Check if soft limit is exceeded
                size_bytes = view_data.get('size_bytes', 0)
                soft_limit_bytes = view_data.get('soft_limit_bytes', 0)
                soft_limit_exceeded = soft_limit_bytes > 0 and size_bytes > soft_limit_bytes
                
                # Add warning indicator if soft limit exceeded
                utilization_text = f"{view_data['utilization']}%"
                if soft_limit_exceeded:
                    utilization_text += " ⚠️"
                
                size_text = view_data['size_formatted']
                soft_limit_text = view_data['soft_limit_formatted'] if view_data['soft_limit_formatted'] != "0 B" else "N/A"
                hard_limit_text = view_data['hard_limit_formatted'] if view_data['hard_limit_formatted'] != "0 B" else "N/A"
                available_text = view_data['available_formatted']
                
                # Color utilization based on level
                critical_threshold = self.config.get_critical_threshold()
                alert_threshold = self.config.get_alert_threshold()
                if view_data['utilization'] >= critical_threshold:
                    utilization_style = "bold red"
                elif view_data['utilization'] >= alert_threshold:
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
        while True:
            # Clear screen and display dashboard
            dashboard.console.clear()
            dashboard.console.print(dashboard.create_rich_dashboard())
            time.sleep(dashboard.refresh_interval)
    except KeyboardInterrupt:
        dashboard.console.print("\n[bold red]Dashboard stopped by user[/bold red]")

if __name__ == "__main__":
    main() 