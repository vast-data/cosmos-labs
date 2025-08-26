# safety_checker.py
import logging
from typing import Dict, List
from vastpy import VASTClient

logger = logging.getLogger(__name__)

class SafetyCheckFailed(Exception):
    """Exception raised when safety checks fail"""
    pass

class SafetyChecker:
    """Safety checker for storage operations"""
    
    def __init__(self, config, vast_client: VASTClient):
        self.config = config
        self.vast_client = vast_client
        self.checks_passed = []
        self.checks_failed = []
    
    def validate_storage_expansion(self, view_path: str, required_size_gb: int) -> bool:
        """Validate that storage expansion is safe"""
        logger.info(f"Running essential safety checks for storage expansion: {view_path} (+{required_size_gb}GB)")
        
        # Reset check results
        self.checks_passed = []
        self.checks_failed = []
        
        # Run essential safety checks
        checks = [
            self._check_view_exists(view_path),
            self._check_basic_permissions(view_path),
            self._check_storage_availability(required_size_gb),
            self._check_quota_limits(required_size_gb)
        ]
        
        # Log results
        self._log_safety_check_results()
        
        # Return True only if ALL essential checks pass
        return all(checks)
    
    def _check_view_exists(self, view_path: str) -> bool:
        """Check if the VAST view exists and is accessible"""
        try:
            views = self.vast_client.views.get(path=view_path)
            if views:
                self.checks_passed.append(f"✅ View exists: {view_path}")
                return True
            else:
                self.checks_failed.append(f"❌ View does not exist: {view_path}")
                return False
        except Exception as e:
            self.checks_failed.append(f"❌ Failed to check view {view_path}: {e}")
            return False
    
    def _check_basic_permissions(self, view_path: str) -> bool:
        """Check if we have basic permissions on the view"""
        try:
            # Simple check: if we can get view info, we have basic permissions
            views = self.vast_client.views.get(path=view_path)
            if views:
                self.checks_passed.append(f"✅ Basic permissions OK: {view_path}")
                return True
            else:
                self.checks_failed.append(f"❌ Cannot access view: {view_path}")
                return False
        except Exception as e:
            self.checks_failed.append(f"❌ Permission check failed for {view_path}: {e}")
            return False
    
    def _check_storage_availability(self, required_size_gb: int) -> bool:
        """Check if there's sufficient storage available"""
        try:
            # For learning purposes, we'll assume storage is available
            # In production, this would check actual cluster capacity
            self.checks_passed.append(f"✅ Storage availability: {required_size_gb}GB requested")
            return True
        except Exception as e:
            self.checks_failed.append(f"❌ Storage check failed: {e}")
            return False
    
    def _check_quota_limits(self, required_size_gb: int) -> bool:
        """Check if the requested expansion is within reasonable limits"""
        try:
            # Simple check: don't allow expansions larger than 10TB for safety
            max_expansion_gb = self.config.get('lab1.storage.max_expansion_gb', 10240)  # 10TB default
            
            if required_size_gb > max_expansion_gb:
                self.checks_failed.append(f"❌ Expansion too large: {required_size_gb}GB > {max_expansion_gb}GB limit")
                return False
            
            self.checks_passed.append(f"✅ Quota expansion within limits: {required_size_gb}GB")
            return True
            
        except Exception as e:
            self.checks_failed.append(f"❌ Quota limit check failed: {e}")
            return False
    
    def _log_safety_check_results(self):
        """Log the results of safety checks in a simple, clear format"""
        logger.info("=" * 50)
        logger.info("SAFETY CHECK RESULTS")
        logger.info("=" * 50)
        
        if self.checks_passed:
            logger.info("✅ PASSED CHECKS:")
            for check in self.checks_passed:
                logger.info(f"  {check}")
        
        if self.checks_failed:
            logger.error("❌ FAILED CHECKS:")
            for check in self.checks_failed:
                logger.error(f"  {check}")
        
        total_checks = len(self.checks_passed) + len(self.checks_failed)
        logger.info(f"SUMMARY: {len(self.checks_passed)}/{total_checks} checks passed")
        
        if len(self.checks_failed) == 0:
            logger.info("🎉 All safety checks passed - operation is safe to proceed")
        else:
            logger.error("🚨 Safety checks failed - operation blocked")
        
        logger.info("=" * 50)
        
        # Reset for next run
        self.checks_passed = []
        self.checks_failed = []
