#!/usr/bin/env python3

import os
import sys
import json
import threading
from datetime import datetime
from flask import Flask, jsonify
from typing import Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from sportmonks_client import SportmonksClient

class HealthChecker:
    """Simple health check service for monitoring application status"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.config = get_config()
        self.last_check = None
        self.health_status = {
            'status': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Setup routes
        self.app.route('/health')(self.health_check)
        self.app.route('/status')(self.detailed_status)
        
    def health_check(self) -> Dict[str, Any]:
        """Basic health check endpoint"""
        try:
            # Run health checks
            self._run_health_checks()
            
            # Return simple status
            if self.health_status['checks'].get('overall', False):
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat()
                }), 503
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def detailed_status(self) -> Dict[str, Any]:
        """Detailed status endpoint with all checks"""
        try:
            self._run_health_checks()
            return jsonify(self.health_status), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def _run_health_checks(self):
        """Run all health checks and update status"""
        checks = {}
        
        # Check configuration
        try:
            config = get_config()
            checks['config'] = True
        except Exception as e:
            checks['config'] = False
            checks['config_error'] = str(e)
        
        # Check API connectivity (basic)
        try:
            client = SportmonksClient()
            # Simple API test - just check if we can create client
            checks['api_client'] = True
        except Exception as e:
            checks['api_client'] = False
            checks['api_error'] = str(e)
        
        # Check file system access
        try:
            # Test log file access
            log_path = getattr(self.config, 'LOG_FILE', 'latecorners.log')
            with open(log_path, 'a') as f:
                f.write(f"# Health check {datetime.now().isoformat()}\n")
            checks['filesystem'] = True
        except Exception as e:
            checks['filesystem'] = False
            checks['filesystem_error'] = str(e)
        
        # Overall health
        checks['overall'] = all([
            checks.get('config', False),
            checks.get('api_client', False),
            checks.get('filesystem', False)
        ])
        
        # Update status
        self.health_status = {
            'status': 'healthy' if checks['overall'] else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'uptime_seconds': self._get_uptime()
        }
        
        self.last_check = datetime.now()
    
    def _get_uptime(self) -> float:
        """Get application uptime in seconds"""
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()
        return (datetime.now() - self.start_time).total_seconds()
    
    def run_server(self, host='0.0.0.0', port=8080, debug=False):
        """Run the health check server"""
        self.start_time = datetime.now()
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def start_health_server_thread(port=8080):
    """Start health check server in a background thread"""
    health_checker = HealthChecker()
    server_thread = threading.Thread(
        target=health_checker.run_server,
        kwargs={'port': port, 'debug': False},
        daemon=True
    )
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    # Run standalone health check server
    health_checker = HealthChecker()
    health_checker.run_server(port=8080, debug=True) 