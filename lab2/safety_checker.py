# lab2/safety_checker.py
import logging
from typing import Dict, List
from vastpy import VASTClient

logger = logging.getLogger(__name__)

class SafetyCheckFailed(Exception):
    """Raised when safety checks fail"""
    pass

class MetadataSafetyChecker:
    """Safety checker for metadata catalog operations"""
    
    def __init__(self, config, vast_client: VASTClient):
        """Initialize the safety checker"""
        self.config = config
        self.vast_client = vast_client
        self.checks_passed = []
        self.checks_failed = []
        
    def validate_catalog_creation(self, catalog_name: str) -> bool:
        """Validate that it's safe to create a new catalog schema"""
        try:
            logger.info(f"Running essential safety checks for catalog creation: {catalog_name}")
            
            # Run essential safety checks
            checks = [
                self._check_view_policies_exist(),
                self._check_storage_availability(),
                self._check_catalog_name_conflicts(catalog_name)
            ]
            
            # Log results
            self._log_safety_check_results()
            
            # Return success only if all essential checks pass
            if len(self.checks_failed) == 0:
                logger.info("✅ All safety checks passed - catalog creation is safe")
                return True
            else:
                logger.error(f"❌ {len(self.checks_failed)} safety checks failed - catalog creation blocked")
                return False
                
        except Exception as e:
            logger.error(f"Safety check validation failed: {e}")
            return False
    
    def validate_batch_ingest(self, directory_path: str, file_count: int) -> bool:
        """Validate that it's safe to perform batch ingest operations"""
        try:
            logger.info(f"Running essential safety checks for batch ingest: {directory_path} ({file_count} files)")
            
            # Run essential ingest safety checks
            checks = [
                self._check_directory_access(directory_path),
                self._check_file_count_limits(file_count),
                self._check_storage_impact(file_count)
            ]
            
            # Log results
            self._log_safety_check_results()
            
            # Return success only if all essential checks pass
            if len(self.checks_failed) == 0:
                logger.info("✅ All safety checks passed - batch ingest is safe")
                return True
            else:
                logger.error(f"❌ {len(self.checks_failed)} safety checks failed - batch ingest blocked")
                return False
                
        except Exception as e:
            logger.error(f"Safety check validation failed: {e}")
            return False
    
    def _check_view_policies_exist(self) -> bool:
        """Check if required view policies exist"""
        try:
            views_config = self.config.get_views_config()
            default_policy = views_config.get('default_policy')
            
            if not default_policy:
                self.checks_failed.append("❌ View policies check - no default policy configured")
                return False
            
            policies = self.vast_client.viewpolicies.get(name=default_policy)
            if policies:
                self.checks_passed.append("✅ View policies check")
                return True
            else:
                self.checks_failed.append(f"❌ View policies check - policy '{default_policy}' not found")
                return False
        except Exception as e:
            self.checks_failed.append(f"❌ View policies check - {e}")
            return False
    
    def _check_storage_availability(self) -> bool:
        """Check if there's sufficient storage for new views"""
        try:
            # For learning purposes, we'll assume storage is available
            # In production, this would check actual cluster capacity
            self.checks_passed.append("✅ Storage availability check")
            return True
        except Exception as e:
            self.checks_failed.append(f"❌ Storage availability check - {e}")
            return False
    
    def _check_catalog_name_conflicts(self, catalog_name: str) -> bool:
        """Check if catalog name conflicts with existing views"""
        try:
            # Check if views with this catalog name already exist
            existing_views = self.vast_client.views.get(path=f"/{catalog_name}")
            if existing_views:
                self.checks_failed.append(f"❌ Catalog name conflict check - views already exist for '{catalog_name}'")
                return False
            else:
                self.checks_passed.append("✅ Catalog name conflict check")
                return True
        except Exception as e:
            self.checks_failed.append(f"❌ Catalog name conflict check - {e}")
            return False
    
    def _check_directory_access(self, directory_path: str) -> bool:
        """Check if directory is accessible and safe to process"""
        try:
            import os
            if not os.path.exists(directory_path):
                self.checks_failed.append(f"❌ Directory access check - path '{directory_path}' does not exist")
                return False
            
            if not os.access(directory_path, os.R_OK):
                self.checks_failed.append(f"❌ Directory access check - no read access to '{directory_path}'")
                return False
            
            self.checks_passed.append("✅ Directory access check")
            return True
        except Exception as e:
            self.checks_failed.append(f"❌ Directory access check - {e}")
            return False
    
    def _check_file_count_limits(self, file_count: int) -> bool:
        """Check if file count is within safe limits"""
        try:
            max_files = self.config.get('lab2.safety.max_files_per_batch', 10000)
            if file_count > max_files:
                self.checks_failed.append(f"❌ File count limits check - {file_count} files exceeds limit of {max_files}")
                return False
            
            self.checks_passed.append("✅ File count limits check")
            return True
        except Exception as e:
            self.checks_failed.append(f"❌ File count limits check - {e}")
            return False
    
    def _check_storage_impact(self, file_count: int) -> bool:
        """Check estimated storage impact of batch operation"""
        try:
            # Estimate storage impact (placeholder implementation)
            estimated_size_gb = file_count * 0.001  # Assume 1MB per file on average
            max_impact_gb = self.config.get('lab2.safety.max_storage_impact_gb', 100)
            
            if estimated_size_gb > max_impact_gb:
                self.checks_failed.append(f"❌ Storage impact check - estimated {estimated_size_gb:.2f}GB exceeds limit of {max_impact_gb}GB")
                return False
            
            self.checks_passed.append("✅ Storage impact check")
            return True
        except Exception as e:
            self.checks_failed.append(f"❌ Storage impact check - {e}")
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
