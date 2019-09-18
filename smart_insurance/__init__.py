from flask import Flask
from smart_insurance._version import __version__

app = Flask(__name__)

import smart_insurance_routes
import cognitive
import experian
import nhtsa_gov
