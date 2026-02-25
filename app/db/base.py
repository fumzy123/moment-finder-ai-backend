from sqlalchemy.orm import declarative_base

# The declarative_base() function creates a master patent class.
# Every single database model we write (like Video, VideoScreenshot, CharacterMoment)
# MUST inherit from this Base class. 
#
# Why? Because when SQLAlchemy runs, it looks at this `Base` object to discover 
# all the tables we defined so it can tell Alembic how to generate our migration scripts.
Base = declarative_base()
