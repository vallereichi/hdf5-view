"""
helper functions to extract data from hdf5 files
"""

import h5py
import pandas as pd
from .models import HDF5_File, HDF5_Group


def read_hdf5(file_path: str) -> HDF5_File:
    """Load a hdf5 file and return it in a sensiible format"""
    hdf5 = HDF5_File(filename="", groups=[], attributes=[], metadata={})

    def extract_datasets(file: h5py.File) -> list[HDF5_Group]:
        """extract datasets/groups from the hdf5 file"""
        groups = []
        for _, group in enumerate(file.keys()):
            data_dict = {}
            for key in file[group].keys():
                data_dict[key] = file[group][key][:]
            dataframe = pd.DataFrame(data=data_dict)
            groups.append(HDF5_Group(name=str(group), size=dataframe.shape, dataset=data_dict))
        return groups

    with h5py.File(file_path, 'r') as f:
        hdf5.filename = file_path.split('.')[-2].split('/')[-1]
        hdf5.attributes = list(f.attrs.keys())
        hdf5.metadata = "TODO: extract metadata"

        hdf5.groups = extract_datasets(f)
    return hdf5
