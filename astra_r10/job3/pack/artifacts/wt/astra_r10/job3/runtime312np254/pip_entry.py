"""Use the copied official pip with this runtime revision's interpreter."""
import runpy
import sys
sys.path.insert(0, 'D:/a10/job3/runtime312np254/bootstrap_packages')
runpy.run_module('pip', run_name='__main__')
