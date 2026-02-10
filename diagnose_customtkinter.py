import sys
import os
import subprocess

print("🔍 DIAGNOSING CUSTOMTKINTER ISSUES")
print("="*60)

# 1. Check Python and environment
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Executable: {sys.executable}")

# 2. Check if we're in a venv
if hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix:
    print("✅ Running in virtual environment")
else:
    print("⚠️  NOT in virtual environment")

# 3. Check CustomTkinter installation
print("\n📦 CHECKING CUSTOMTKINTER INSTALLATION:")
try:
    import customtkinter
    print(f"✅ CustomTkinter version: {customtkinter.__version__}")
    print(f"   Location: {customtkinter.__file__}")
except ImportError as e:
    print(f"❌ CustomTkinter import failed: {e}")
    sys.exit(1)

# 4. Check Tkinter (required by CustomTkinter)
print("\n🎨 CHECKING TKINTER (REQUIRED FOR CUSTOMTKINTER):")
try:
    import tkinter as tk
    root = tk.Tk()
    root.destroy()
    print("✅ Tkinter works")
except Exception as e:
    print(f"❌ Tkinter error: {e}")
    print("\n💡 On macOS, you might need to install tkinter:")
    print("   brew install python-tk")

# 5. Check dependencies
print("\n📋 CHECKING DEPENDENCIES:")
deps = ['darkdetect', 'packaging']
for dep in deps:
    try:
        module = __import__(dep)
        print(f"✅ {dep}: found")
    except ImportError as e:
        print(f"❌ {dep}: missing - {e}")

# 6. Test basic CustomTkinter functionality
print("\n🧪 TESTING BASIC CUSTOMTKINTER FUNCTIONALITY:")
try:
    import customtkinter as ctk
    
    # Test 1: Can we create a simple window?
    test_window = ctk.CTk()
    test_window.geometry("300x100")
    test_window.title("Test")
    
    # Test 2: Can we create a label?
    label = ctk.CTkLabel(test_window, text="CustomTkinter Test")
    label.pack(pady=20)
    
    # Test 3: Can we create a button?
    button = ctk.CTkButton(test_window, text="Close", command=test_window.destroy)
    button.pack()
    
    print("✅ Basic CustomTkinter elements work")
    print("   Window will appear briefly...")
    
    # Show briefly then close
    test_window.after(1000, test_window.destroy)
    test_window.mainloop()
    
except Exception as e:
    print(f"❌ CustomTkinter test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("💡 If tests fail above, fix those issues first.")
