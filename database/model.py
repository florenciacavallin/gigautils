# The model file defines the SQLAlchemy Declarative base object
# which is used by models throughout our system to define tables.
import abc

from sqlalchemy.orm import declarative_base, DeclarativeMeta

Base = declarative_base()


class ABCBase(abc.ABCMeta, DeclarativeMeta):
    """
    The ABCBase class combines the metaclass of SqlAlchemy ORM Base and the ABCMeta
    This allows abstract SqlAlchemy classes
    """
    pass
