"""
User configuration management
Stores user-specific settings, preferences, and calibrated thresholds
IMPORTS ALL DEFAULTS from config.constants - NO hardcoded values!
"""
import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from config.app_constants import (
    DEFAULT_USER_CONFIG,
    get_default_thresholds,
    get_default_config
)


class UserConfig:
    """Manages user-specific configuration and preferences"""
    
    # Import defaults from constants.py - NO hardcoding!
    DEFAULT_CONFIG = DEFAULT_USER_CONFIG
    
    def __init__(self, config_dir: str = None):
        """
        Initialize user configuration
        
        Args:
            config_dir: Directory to store config file (default: ~/.workout_analyzer)
        """
        if config_dir is None:
            config_dir = os.path.join(Path.home(), '.workout_analyzer')
        
        self.config_dir = config_dir
        self.config_path = os.path.join(config_dir, 'user_config.json')
        
        # Thread safety for multi-threaded app
        self.save_lock = threading.RLock()
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Normalize threshold keys to uppercase for consistency
                loaded_config = self._normalize_threshold_keys(loaded_config)
                
                # Merge with defaults (handles new settings from updates)
                return self._merge_configs(get_default_config(), loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Creating new config with defaults")
                config = get_default_config()
                self._save_config(config)
                return config
        else:
            # First time - create default config
            config = get_default_config()
            self._save_config(config)
            return config
    
    def _normalize_threshold_keys(self, config: Dict) -> Dict:
        """
        Normalize threshold keys to UPPERCASE for consistency
        Handles old configs that might have lowercase keys
        """
        if 'thresholds' in config:
            for exercise_type in config['thresholds']:
                thresholds = config['thresholds'][exercise_type]
                
                # Map of lowercase -> UPPERCASE
                key_mapping = {
                    'standing': 'STANDING',
                    'squatting': 'SQUATTING',
                    'up': 'UP',
                    'down': 'DOWN',
                    'curled': 'CURLED',
                    'cooldown_frames': 'COOLDOWN_FRAMES',
                    'excellent': 'EXCELLENT',
                    'good': 'GOOD',
                    'calibrated': 'CALIBRATED',
                    'calibration_date': 'CALIBRATION_DATE'
                }
                
                # Convert any lowercase keys to uppercase
                normalized = {}
                for key, value in thresholds.items():
                    if key in key_mapping:
                        normalized[key_mapping[key]] = value
                    else:
                        # Already uppercase or unknown key - keep as is
                        normalized[key] = value
                
                config['thresholds'][exercise_type] = normalized
        
        return config
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults, preserving user-added keys"""
        for key, value in default.items():
            if key in loaded:
                if isinstance(value, dict) and isinstance(loaded[key], dict):
                    default[key] = self._merge_configs(value, loaded[key])
                else:
                    default[key] = loaded[key]
        # Preserve keys from loaded config that aren't in defaults
        # (e.g. cached_cameras, workout preferences, etc.)
        for key, value in loaded.items():
            if key not in default:
                default[key] = value
        return default
    
    def _save_config(self, config: Dict = None):
        """Save configuration to file"""
        with self.save_lock:
            if config is None:
                config = self.config
            
            try:
                # Create backup of existing config
                if os.path.exists(self.config_path):
                    backup_path = self.config_path + '.bak'
                    try:
                        with open(self.config_path, 'r') as src, open(backup_path, 'w') as dst:
                            dst.write(src.read())
                    except Exception:
                        pass  # Backup failed, continue anyway
                
                # Save new config
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2, default=str)
            
            except Exception as e:
                print(f"Error saving config: {e}")
    
    # ========== GETTERS ==========
    
    def get(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            category: config category
            key: setting key
            default: default value if not found (uses constants.py defaults if None)
        
        Returns:
            configuration value or default
        """
        with self.save_lock:
            if category not in self.config:
                # Try to get from DEFAULT_CONFIG
                if default is None and category in self.DEFAULT_CONFIG:
                    return self.DEFAULT_CONFIG[category].get(key)
                return default
            
            value = self.config[category].get(key)
            
            # If value not found and no explicit default, try DEFAULT_CONFIG
            if value is None and default is None:
                if category in self.DEFAULT_CONFIG:
                    return self.DEFAULT_CONFIG[category].get(key)
            
            return value if value is not None else default
    
    def get_threshold(self, exercise: str, key: str = None) -> Any:
        """
        Get exercise threshold value
        
        Args:
            exercise: 'squat', 'pushup', or 'curl'
            key: specific threshold key (optional, should be UPPERCASE)
        
        Returns:
            threshold value or dict of all thresholds
        """
        with self.save_lock:
            if exercise not in self.config['thresholds']:
                # If exercise not in user config, get default from constants
                return get_default_thresholds(exercise) if key is None else get_default_thresholds(exercise).get(key)
            
            if key is None:
                return self.config['thresholds'][exercise].copy()
            
            return self.config['thresholds'][exercise].get(key)
    
    # ========== SETTERS ==========
    
    def set(self, category: str, key: str, value: Any, save: bool = True):
        """
        Set configuration value
        
        Args:
            category: config category
            key: setting key
            value: new value
            save: save to disk immediately (default: True)
        """
        with self.save_lock:
            if category not in self.config:
                self.config[category] = {}
            
            self.config[category][key] = value
            
            if 'last_updated' in self.config[category] or category in ['profile', 'system', 'display']:
                self.config[category]['last_updated'] = datetime.now().isoformat()
            
            if save:
                self._save_config()
    
    def set_profile(self, name: str = None, height_cm: float = None, weight_kg: float = None):
        """Update user profile information"""
        with self.save_lock:
            if name is not None:
                self.config['profile']['name'] = name
            # if height_cm is not None:
            #     self.config['profile']['height_cm'] = float(height_cm)           
            self.config['profile']['last_updated'] = datetime.now().isoformat()
            self._save_config()

    def set_threshold(self, exercise: str, thresholds: Dict, mark_calibrated: bool = True):
        """
        Update exercise thresholds (called by workout engine for auto-calibration)

        Args:
            exercise: 'squat', 'pushup', or 'curl'
            thresholds: Dict with threshold values (keys should be UPPERCASE)
            mark_calibrated: Mark as calibrated
        """
        with self.save_lock:
            if exercise not in self.config['thresholds']:
                self.config['thresholds'][exercise] = get_default_thresholds(exercise)

            self.config['thresholds'][exercise].update(thresholds)

            if mark_calibrated:
                self.config['thresholds'][exercise]['CALIBRATED'] = True
                self.config['thresholds'][exercise]['CALIBRATION_DATE'] = datetime.now().isoformat()

            self._save_config()

    # ========== LEGAL / CONSENT ==========
    
    def set_legal_acceptance(self, accepted: bool, waiver_version: str):
        """Store legal waiver acceptance"""
        with self.save_lock:
            self.config['legal']['liability_waiver'] = {
                'accepted': accepted,
                'version': waiver_version,
                'accepted_at': datetime.now().isoformat()
            }
            self._save_config()
    
    def has_accepted_waiver(self, waiver_version: str) -> bool:
        """Check whether the user has accepted a specific waiver version"""
        with self.save_lock:
            waiver = self.config.get('legal', {}).get('liability_waiver', {})
            
            if not isinstance(waiver, dict):
                return False
            
            return (
                waiver.get('accepted') is True
                and waiver.get('version') == waiver_version
            )
    
    # ========== SETUP STATUS ==========
    
    def mark_setup_complete(self):
        """Mark initial setup as completed"""
        with self.save_lock:
            self.config['setup']['completed'] = True
            self.config['setup']['completion_date'] = datetime.now().isoformat()
            if not self.config['profile'].get('created_at'):
                self.config['profile']['created_at'] = datetime.now().isoformat()
            self._save_config()
    
    def is_setup_complete(self) -> bool:
        """Check if initial setup has been completed"""
        with self.save_lock:
            return self.config['setup'].get('completed', False)
    
    # ========== RESET ==========
    
    def reset_to_defaults(self, category: str = None):
        """
        Reset configuration to defaults from constants.py
        
        Args:
            category: Specific category to reset, or None for all
        """
        with self.save_lock:
            if category:
                if category in self.DEFAULT_CONFIG:
                    self.config[category] = get_default_config()[category]
            else:
                self.config = get_default_config()
            
            self._save_config()
    
    # ========== EXPORT/IMPORT ==========
    
    def export_config(self, filepath: str):
        """Export configuration to a file"""
        with self.save_lock:
            with open(filepath, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
    
    def import_config(self, filepath: str):
        """Import configuration from a file"""
        with self.save_lock:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Config file not found: {filepath}")
            
            with open(filepath, 'r') as f:
                imported = json.load(f)
            
            # Normalize threshold keys
            imported = self._normalize_threshold_keys(imported)
            
            self.config = self._merge_configs(get_default_config(), imported)
            self._save_config()
