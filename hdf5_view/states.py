"""
states
"""

import re
import reflex as rx
from .models import HDF5_File, HDF5_Group
from .util import read_hdf5

class FileTableState(rx.State):
    """State containing all the hdf5 information."""
    hdf5_files: list[HDF5_File]
    groups: list[HDF5_Group]
    filtered_keys: list[str]
    search_value: str
    selected_file_idx: int = -1
    selected_group_idx: int = -1

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """handle file upload"""
        for file in files:
            data = await file.read()
            outfile = rx.get_upload_dir() / file.name

            # save the file
            with outfile.open("wb") as file_object:
                file_object.write(data)

            self.hdf5_files.append(read_hdf5(str(outfile)))

    def select_file(self, idx: int):
        """select a file by index from a click event"""
        self.selected_file_idx = idx
        self.groups = self.hdf5_files[idx].groups

    def select_group(self, idx: int):
        """select a group by index from a click event"""
        self.selected_group_idx = idx
        self.filtered_keys = list(self.groups[idx].dataset.keys())

    @rx.event
    def search_key(self, value: str):
        """update the filtered keys according to the search value"""
        self.search_value = value
        if not value:
            self.filtered_keys = list(self.groups[self.selected_group_idx].dataset.keys())
        else:
            pattern = re.compile(value, re.IGNORECASE)
            self.filtered_keys = [
                key for key in self.groups[self.selected_group_idx].dataset.keys()
                if pattern.search(key)
            ]



    @rx.event
    def clear_table(self):
        """clear the table"""
        self.hdf5_files = []
        self.groups = []
        self.filtered_keys = []
        self.selected_file_idx = -1
        self.selected_group_idx = -1

    @rx.event
    def clear_group_selection(self):
        """clear the group selection"""
        self.selected_group_idx = -1
        self.filtered_keys = []
