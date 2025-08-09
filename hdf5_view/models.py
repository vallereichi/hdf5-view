"""
models
"""

from typing import Any
import reflex as rx


class HDF5_Group(rx.Base):
    """group model for hdf5 files"""
    name: str
    size: tuple[int, int]
    dataset: dict[str, Any]

class HDF5_File(rx.Base):
    """class holding information about the hdf5 file"""
    filename: str
    groups: list[HDF5_Group]
    attributes: list[str]
    metadata: dict
