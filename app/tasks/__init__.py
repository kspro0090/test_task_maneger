from flask import Blueprint

bp = Blueprint('tasks', __name__)

from . import routes