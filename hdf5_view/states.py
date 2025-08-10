"""
states
"""

import reflex as rx
from .models import HDF5_File
from .util import read_hdf5

class FileTableState(rx.State):
    """State containing all the hdf5 information."""
    hdf5_files: list[HDF5_File]
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

    def select_group(self, idx: int):
        """select a group by index from a click event"""
        self.selected_group_idx = idx

    @rx.event
    def clear_table(self):
        """clear the table"""
        self.hdf5_files = []
        self.selected_file_idx = -1
        self.selected_group_idx = -1

    @rx.event
    def clear_group_selection(self):
        """clear the group selection"""
        self.selected_group_idx = -1
