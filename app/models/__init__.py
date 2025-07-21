from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .location import Location
from .attendance import Attendance
from .cd_schedule import CDSchedule
