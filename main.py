"""
    beartoday

    2014.10.01 beartoday
"""

from app.tool.tools import dbg
dbg('main.py')

import os
from app import create_app

main = create_app(os.getenv('BT_CONFIG') or 'default')
