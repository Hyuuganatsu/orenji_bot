import json
import os
from typing import Dict, Set, Callable, Any
from functools import wraps
from loguru import logger
from graia.ariadne.model import Group

class ModuleConfigManager:
    """Manages module enable/disable configuration per group"""
    
    def __init__(self, config_file: str = "module_config.json"):
        self.config_file = config_file
        self.config: Dict[str, Dict[str, bool]] = {}
        self.admin_groups: Set[str] = set()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = data.get('module_config', {})
                    self.admin_groups = set(data.get('admin_groups', []))
        except Exception as e:
            logger.error(f"Failed to load module config: {e}")
            self.config = {}
            self.admin_groups = set()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            data = {
                'module_config': self.config,
                'admin_groups': list(self.admin_groups)
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save module config: {e}")
    
    def is_admin_group(self, group_id: str) -> bool:
        """Check if a group is an admin group"""
        return group_id in self.admin_groups
    
    def add_admin_group(self, group_id: str):
        """Add a group to admin groups"""
        self.admin_groups.add(group_id)
        self.save_config()
    
    def remove_admin_group(self, group_id: str):
        """Remove a group from admin groups"""
        self.admin_groups.discard(group_id)
        if group_id in self.config:
            del self.config[group_id]
        self.save_config()
    
    def is_module_enabled(self, group_id: str, module_name: str) -> bool:
        """Check if a module is enabled for a group. Default is True."""
        if group_id not in self.config:
            return True
        return self.config[group_id].get(module_name, True)
    
    def set_module_status(self, group_id: str, module_name: str, enabled: bool):
        """Set module enable/disable status for a group"""
        if group_id not in self.config:
            self.config[group_id] = {}
        self.config[group_id][module_name] = enabled
        self.save_config()
    
    def get_group_config(self, group_id: str) -> Dict[str, bool]:
        """Get all module configurations for a group"""
        return self.config.get(group_id, {})
    
    def get_all_groups(self) -> Set[str]:
        """Get all configured groups"""
        return set(self.config.keys())

# Global instance
module_config_manager = ModuleConfigManager()

def check_module_enabled(module_name: str):
    """Decorator to check if a module is enabled for the group before executing"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract group from args and kwargs - should be in the function signature
            group = None
            
            # Check args first
            for arg in args:
                if isinstance(arg, Group):
                    group = arg
                    break
            
            # If not found in args, check kwargs
            if group is None:
                for value in kwargs.values():
                    if isinstance(value, Group):
                        group = value
                        break
            
            # If no group found, allow execution (might be friend message or other)
            if group is None:
                return await func(*args, **kwargs)
            
            group_id = str(group.id)
            # Check if module is enabled for this group
            if not module_config_manager.is_module_enabled(group_id, module_name):
                logger.debug(f"Module {module_name} is disabled for group {group_id}, skipping execution")
                return None
            
            # Module is enabled, proceed with execution
            return await func(*args, **kwargs)
        return wrapper
    return decorator