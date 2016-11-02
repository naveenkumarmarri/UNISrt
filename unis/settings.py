import os
import sys
import tempfile

UNISRT_ROOT = os.path.dirname(os.path.abspath(__file__)) + os.sep
LOCAL_ROOT = tempfile.mkdtemp()
sys.path.append(os.path.dirname(os.path.dirname(UNISRT_ROOT)))
