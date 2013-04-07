import inspect
import os
import sys

DIR_TOP = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

sys.path.append(DIR_TOP)
activate_this = DIR_TOP + '/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from howmanyouts import app as application

