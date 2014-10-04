"""
    beartoday

    2014.10.01 beartoday
"""

import os
from app import create_app

beartoday = create_app(os.getenv('BT_CONFIG') or 'default')
