# tools/reset_setup.py
#!/usr/bin/env python3
"""
Utility to reset setup wizard for testing
"""
import json
import os
import sys
from pathlib import Path

def main():
    print("Reset Setup Wizard")
    print("="*60)
    
    # Find config file
    config_path = Path.home() / '.workout_analyzer' / 'user_config.json'
    
    if not config_path.exists():
        print("[ERROR] Config file not found.")
        print(f"Expected at: {config_path}")
        print("\nThe config file will be created when you:")
        print("1. Run the application for the first time")
        print("2. Or complete the setup wizard")
        return 1
    
    # Backup
    backup_path = config_path.with_suffix('.json.backup')
    import shutil
    shutil.copy2(config_path, backup_path)
    print(f"[FILE] Backup created: {backup_path}")
    
    # Load and modify
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # What to reset
    print("\nWhat would you like to reset?")
    print("1. Just setup completion (show wizard again)")
    print("2. Everything (including waiver, profile, etc.)")
    print("3. Cancel")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        config['setup']['completed'] = False
        print("[OK] Setup completion reset")
    
    elif choice == '2':
        # Create fresh config
        from config.user_config import UserConfig
        fresh_config = UserConfig.DEFAULT_CONFIG.copy()
        
        # Keep any important settings?
        keep_keys = input("Keep any settings? (comma-separated keys, or 'none'): ")
        if keep_keys.lower() != 'none':
            for key in [k.strip() for k in keep_keys.split(',')]:
                if key in config:
                    fresh_config[key] = config[key]
        
        config = fresh_config
        print("[OK] Full reset complete")
    
    else:
        print("[ERROR] Cancelled")
        return 0
    
    # Save
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n[OK] Config updated: {config_path}")
    print("\nNext steps:")
    print("1. Run: python main.py")
    print("2. Setup wizard will show again")
    print(f"3. Backup available at: {backup_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())