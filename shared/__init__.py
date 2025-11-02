# Shared modules for Enterprise Code Archaeologist

from .data_lake_interface import (
    DataLakeInterface,
    DataLakeEntry,
    DataType,
    DataLakeError,
    NotFoundError,
    ValidationError
)

from .disk_data_lake import DiskDataLake

__all__ = [
    "DataLakeInterface",
    "DataLakeEntry", 
    "DataType",
    "DataLakeError",
    "NotFoundError",
    "ValidationError",
    "DiskDataLake"
]