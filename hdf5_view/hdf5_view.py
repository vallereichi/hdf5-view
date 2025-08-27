import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import reflex as rx
from reflex_pyplot import pyplot
import h5py


class FileState(rx.State):
    """The app state."""
    uploaded_files: list[str]

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """handle file upload"""
        for file in files:
            data = await file.read()
            outfile = rx.get_upload_dir() / str(file.name)
            with outfile.open("wb") as file_object:
                file_object.write(data)
            self.uploaded_files.append(str(file.name))

    @rx.event
    def clear_files(self):
        """remove all uploaded files"""
        self.uploaded_files = []
        HDF5State.group_list = []


class HDF5State(rx.State):
    """State with loaded file structure data, e.g. groups and datasets"""
    file_name: str
    group_list: list[str]
    dataset_list: list[str]
    selected_group_idx: int = -1

    def find_groups(self, file_path: str, group: str | None = None, group_list: list[str] | None = None) -> list[str]:
        """
        recursively searching the file for all groups.

        parameters:
            file_path:  path to the hdf5 file
            group:      (optional) start the recursive search from this group. If not provided the search will start from the root group '/'
            group_list: (optional) All found groups will be appended to this list.

        returns:
            list[str]:  List containing all found groups as paths. Therefore subgroups also contain information about their location in the file structure
        """
        group_path: str = "/" if group is None else group
        group_path = group_path if group_path.startswith("/") else "/" + group_path
        group_path = group_path if group_path.endswith("/") else group_path + "/"

        group_list: list[str] = [] if group_list is None else group_list
        if group_path not in group_list: group_list.append(group_path)
        file = h5py.File(file_path, 'r')

        if isinstance(file[group_path], h5py.Group):
            initial_group: h5py.Group = file[group_path]
        else:
            raise TypeError(f"file[group] is not of type 'h5py.Group' but is '{type(file[group_path])}'")

        for key in initial_group.keys():
            if isinstance(initial_group[key], h5py.Group):
                new_group_path: str = group_path + key + "/"
                group_list.append(new_group_path)
                self.find_groups(file_path, group=new_group_path, group_list=group_list)

        file.close()

        return group_list


    def find_datasets(self, file_path: str, group: str | None = None) -> list[str]:
        """
        recursivly searching the file for all datasets

        parameters:
            file_path:      path to the hdf5 file
            group:          (optional) start the recursive search from this group. If not provided the search will start from the root group '/'

        returns:
            list[str]:      List containing all found datasets as paths so the file structure can be accessed directly
        """
        group_path: str = "/" if group is None else group
        group_list: list[str] = self.find_groups(file_path=file_path, group=group_path)
        file = h5py.File(file_path, 'r')
        dataset_list = []

        for group in group_list:
            if isinstance(file[group], h5py.Group):
                group_obj: h5py.Group = file[group]
            else:
                raise TypeError(f"'find_groups()' found an object of type '{type(file[group])}'. Please contact support")

            for dset in group_obj.keys():
                if isinstance(group_obj[dset], h5py.Dataset):
                    new_dataset_path: str = group + dset
                    dataset_list.append(new_dataset_path)
                else:
                    break

        file.close()

        return dataset_list 

    @rx.event
    def load_file(self, file_name: str):
        self.file_name = file_name
        self.group_list = self.find_groups(os.path.join(rx.get_upload_dir(), self.file_name))

    @rx.event
    def load_group(self, group_idx: int):
        group: str = self.group_list[group_idx]
        self.dataset_list = self.find_datasets(os.path.join(rx.get_upload_dir(), self.file_name), group)

    @rx.event
    def clear_group_list(self):
        self.group_list = []

    @rx.event
    def clear_dataset_list(self):
        self.dataset_list = []



class PlotState(rx.State):
    """State containing all the information about a plot"""
    parameters_to_plot: list[str] = []
    parameter_data: list[np.ndarray]

    def load_parameter_data(self, file_path):
        file: h5py.File = h5py.File(file_path, 'r')
        try:
            data: np.ndarray = file[self.parameters_to_plot[-1]][:]
        except:
            raise KeyError(f"{self.parameters_to_plot[-1]} cannot be accessed from file {file_path}")

        try:
            mask = file['MSSM']['LogLike_isvalid'][:].astype(bool)
            data = data[mask]
        except:
            pass
        self.parameter_data.append(data)

    @rx.var
    def create_plot(self) -> Figure:
        fig = plt.figure(figsize=(7,5))
        ax = fig.add_subplot(111)
        labels = []

        for data in self.parameter_data:
            counts, bins, _ = ax.hist(data, bins=50, density=True, color='rebeccapurple', linewidth=1.5, alpha=0.7, histtype='step')

            max_index = np.argmax(counts)
            max_bin_center = (bins[max_index] + bins[max_index + 1]) / 2
            label = f'max: {max_bin_center:.2f}'
            labels.append(label)

        ax.legend(labels)
        if len(self.parameters_to_plot) > 0:
            ax.text(0.05, 0.95, s="$n_{valid}$ = " + f"{len(self.parameter_data[0])}",transform=ax.transAxes, ha='left', va='top')
            ax.set_xlabel(self.parameters_to_plot[0].split('::')[-1])
        ax.set_ylabel("counts")

        plt.close(fig)
        return fig


    @rx.event
    def add_parameter(self, paramter: str, file_name: str):
        self.parameters_to_plot.append(paramter)
        self.load_parameter_data(file_path=os.path.join(rx.get_upload_dir(), file_name))

    @rx.event
    def clear_parameters(self):
        self.parameters_to_plot = []
        self.parameter_data = []


def upload_component() -> rx.Component:
    """Input field for file selection and 'drag&drop' area"""
    return rx.vstack(
        rx.upload(
            rx.button("upload"),
            id="file_upload",
            border="2px dashed #ccc",
            border_radius="1em",
            justify="center",
            width="100%",
            padding="2em",
            on_drop=FileState.handle_upload(rx.upload_files(upload_id="file_upload"))
        ),
        width="100%",
    )

def display_files() -> rx.Component:
    return rx.cond(
        FileState.uploaded_files,
        rx.vstack(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("uploaded files")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        FileState.uploaded_files,
                        lambda file: rx.table.row(
                            rx.table.cell(file, on_click=rx.redirect("/hdf5")),
                            on_click=HDF5State.load_file(file),
                            style={
                                "border": "2px solid transparent",
                                "cursor": "pointer"
                            },
                            _hover={
                                "background": "#222",
                                "border-radius": "0.5em",
                                "cursor": "pointer"
                            },
                        )
                    )
                ),
                width="100%",
            ),
            rx.button(
                "clear",
                on_click=FileState.clear_files()
            ),
            width="100%",
        ),
        rx.text("no uploaded files")
    )

def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Display HDF5!"),
            upload_component(),
            display_files(),
            spacing="5",
            padding_top="5rem",
            justify="start",
            min_height="85vh",
        ),
    )

def display_group_table() -> rx.Component:
    return rx.cond(
        HDF5State.group_list,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Groups")
                )
            ),
            rx.table.body(
                rx.foreach(
                    HDF5State.group_list,
                    lambda group, index: rx.table.row(
                        rx.table.cell(
                            group,
                            on_click=HDF5State.load_group(index)
                        ),
                        style={
                            "border": "2px solid transparent",
                            "cursor": "pointer"
                        },
                        _hover={
                            "background": "#222",
                            "border-radius": "0.5em",
                            "cursor": "pointer"
                        },
                    )
                )
            ),
            width="100%"
        )
    )


def display_dataset_table() -> rx.Component:
     return rx.cond(
        HDF5State.dataset_list,
        rx.vstack(
            rx.hstack(
                rx.input(placeholder="search .."), #add search functionality here
                rx.button("clear", on_click=HDF5State.clear_dataset_list()),
                justify="between",
                width="100%"
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Datasets")
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        HDF5State.dataset_list,
                        lambda dset, index: rx.table.row(
                            rx.table.cell(
                                dset,
                                on_click=PlotState.add_parameter(dset, HDF5State.file_name)
                            ),
                            on_click=rx.redirect("/plot"),
                            style={
                                "border": "2px solid transparent",
                                "cursor": "pointer"
                            },
                            _hover={
                                "background": "#222",
                                "border-radius": "0.5em",
                                "cursor": "pointer"
                            },
                        )
                    )
                ),
                width="100%",
                max_height="50vh",
                overflow="auto",
            ),
            padding="1em",
            border="3px solid #ccc",
            border_radius="1em",
            width="100%"
        )
    )




def hdf5() -> rx.Component:
    # hdf5 page (view file structure)
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                rx.link(
                    rx.icon_button("arrow_big_left"),
                    href="/", position="top-left",
                    ),
                rx.heading("Back")
            ),
            rx.heading(HDF5State.file_name),
            display_group_table(),
            display_dataset_table(),
        ),
        spacing="5",
        padding_top="5rem",
        justify="start",
        min_height="85vh",

    )






def display_parameter_table() -> rx.Component:
    return rx.cond(
        PlotState.parameters_to_plot,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Parameters")
                )
            ),
            rx.table.body(
                rx.foreach(
                    PlotState.parameters_to_plot,
                    lambda parameter: rx.table.row(
                        rx.table.cell(
                            parameter,
                        )
                    )
                )
            ),
            width="100%",
        ),
        rx.text("nothing to see here")
    )





def display_plot() -> rx.Component:
    return rx.cond(
        PlotState.parameters_to_plot,
        rx.card(
            pyplot(
                PlotState.create_plot
            ),
            width="100%",
        )
    )




def plot() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                rx.link(
                        rx.icon_button("arrow_big_left"),
                        on_click=PlotState.clear_parameters(),
                        href="/hdf5", position="top-left",
                    ),
                rx.heading("Back")
            ),
            display_parameter_table(),
            display_plot(),
            padding_top="1.5em",
            spacing="9",
            justify="start",
            min_height="85vh",
            max_height="85vh",

        )
    )


app = rx.App()
app.add_page(index)
app.add_page(hdf5)
app.add_page(plot)

