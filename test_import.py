import importlib
import sys
import traceback

sys.path.insert(0, '.')
module_name= 'main'

try:
    module= importlib.import_module(module_name)
    print(f"{module_name}.py imported successfully")
except Exception as e:
    traceback.print_exc()
