import h5py
from .models import HDF5_File

def read_hdf5(file_path: str) -> HDF5_File:
    """Load a hdf5 file and return it in a sensiible format"""
    hdf5 = HDF5_File(filename="", groups=[], attributes=[], metadata={})

    with h5py.File(file_path, 'r') as f:
        hdf5.filename = file_path.split('.')[-2].split('/')[-1]
        hdf5.groups = list(f.keys())
        hdf5.attributes = list(f.attrs.keys())
        hdf5.metadata = "TODO: extract metadata"

    return hdf5