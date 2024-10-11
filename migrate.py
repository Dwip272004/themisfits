import os
from app import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)

if __name__ == '__main__':
    migrate.init_app(app, db)
<<<<<<< HEAD
    migrate.upgrade()
=======
    migrate.upgrade()
>>>>>>> ce476617c14f7e08fc958afd74510ff9685b921a
