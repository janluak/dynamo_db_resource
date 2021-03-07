__version__ = "0.1.0"

from .dynamo_db_table import Table
from .resource import database_resource


class UpdateReturns:
    """
    contains the options for possible return values if updating an item
    """
    NONE = "NONE"
    ALL_OLD = "ALL_OLD"
    UPDATED_OLD = "UPDATED_OLD"
    ALL_NEW = "ALL_NEW"
    UPDATED_NEW = "UPDATED_NEW"
