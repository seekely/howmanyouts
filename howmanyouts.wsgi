import os
import sys

sys.path.append('/srv/www/howmanyouts.com/howmanyouts')

activate_this = '/srv/www/howmanyouts.com/howmanyouts/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from howmanyouts import app as application

