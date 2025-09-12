from logging import PlaceHolder
import os
import re
import numpy as np
import numexpr as ne
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
        HDF5State.dataset_list = []


class HDF5State(rx.State):
    """State with loaded file structure data, e.g. groups and datasets"""
    file_name: str
    group_list: list[str]
    dataset_list: list[str]
    filtered_datasets: list[str]

    @rx.event
    def clear(self):
        self.file_name = ""
        self.group_list = []
        self.dataset_list = []

    def filter_datasets(self, search_key: str):
        if search_key == "":
            self.filtered_datasets = self.dataset_list
            return
        pattern = re.compile(search_key)
        tmp = [dset for dset in self.dataset_list if pattern.search(dset)]
        self.filtered_datasets = tmp


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
        self.filtered_datasets = self.dataset_list

    @rx.event
    def clear_group_list(self):
        self.group_list = []

    @rx.event
    def clear_dataset_list(self):
        self.dataset_list = []




class PlotState(rx.State):
    """State containing all the information about a plot"""
    file_name_list: list[str] = []
    parameters_to_plot: list[str] = []
    parameter_data: list[np.ndarray]
    index_list: list[int] = [0]
    base_filter: list[bool]
    filter_condition: str = ""


    @rx.var
    def enumerated_parameters(self) -> list[tuple[int, str]]:
        return list(enumerate(self.parameters_to_plot))


    @rx.event
    def filter_data(self, index: int, filter_condition: str, dataset_list: list[str]):
        """filter a dataset for a given condition"""

        print(filter_condition)

        print(index)

        parameter_name = [dset for dset in dataset_list if dset.split('/')[-1] in filter_condition] # TODO: check for multiple occurances
        if not parameter_name:
            raise ValueError("could not find the dataset provided by the filter")

        parameter_name = parameter_name[0]

        file: h5py.File = h5py.File(os.path.join(rx.get_upload_dir(), self.file_name_list[index]))
        filter_data = file[parameter_name][:]

        safe_filter_condition = filter_condition.replace(parameter_name.split('/')[-1], 'x')

        # apply the condition to the filter data and use it as a mask
        mask = ne.evaluate(safe_filter_condition, local_dict={'x': filter_data})
        if self.parameter_data[index].shape != filter_data.shape:
            # reset filters by reloading original data
            self.load_parameter_data(os.path.join(rx.get_upload_dir(), self.file_name_list[index]), index=index)

        self.parameter_data[index] = self.parameter_data[index][mask]


    def load_parameter_data(self, file_path, index: int = -1):
        file: h5py.File = h5py.File(file_path, 'r')
        try:
            data: np.ndarray = file[self.parameters_to_plot[index]][:]
        except:
            raise KeyError(f"{self.parameters_to_plot[index]} cannot be accessed from file {file_path}")

        self.base_filter = [True] * len(data)
        try:
            self.base_filter = list(file['MSSM']['LogLike_isvalid'][:].astype(bool))
            data = data[self.base_filter]
        except:
            pass

        # try:
        #     self.base_filter = list(file['MSSM']["SP_m_W"][:] != -1)
        #     data = data[self.base_filter]
        # except:
        #     pass


        if index != -1:
            self.parameter_data[index] = data
        else:
            self.parameter_data.append(data)

    @rx.var
    def create_plot(self) -> Figure:
        fig = plt.figure(figsize=(7,5))
        ax = fig.add_subplot(111)
        labels = []
        colors = ["rebeccapurple", "teal", "firebrick"]


        if len(self.parameters_to_plot) > 0:
            for idx in self.index_list:
                counts, bins, _ = ax.hist(self.parameter_data[idx], bins=50, density=True, color=colors[idx], linewidth=1.5, alpha=0.7, histtype='step')

                max_index = np.argmax(counts)
                max_bin_center = (bins[max_index] + bins[max_index + 1]) / 2
                label = f'data_length={len(self.parameter_data[idx])}'
                labels.append(label)
                ax.set_xlabel(self.parameters_to_plot[idx].split('::')[-1])

            ax.legend(labels)
            # ax.text(0.05, 0.95, s="$n_{valid}$ = " + f"{len(self.parameter_data[0])}",transform=ax.transAxes, ha='left', va='top')
        ax.set_ylabel("counts")

        plt.close(fig)
        return fig


    @rx.event
    def add_parameter(self, parameter: str, file_name: str):
        self.parameters_to_plot.append(parameter)
        self.file_name_list.append(file_name)
        self.load_parameter_data(file_path=os.path.join(rx.get_upload_dir(), file_name))

    @rx.event
    def show_parameter(self, index: int):
        if index not in self.index_list:
            self.index_list.append(index)

    @rx.event
    def hide_parameter(self, index: int):
        if index in self.index_list:
            del self.index_list[index]
        if not self.index_list:
            self.index_list = [0]

    @rx.event
    def clear_parameters(self):
        self.parameters_to_plot = []
        self.parameter_data = []
        self.index_list = [0]


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
                rx.input(placeholder="search ..", on_change=lambda search_key: HDF5State.filter_datasets(search_key)),
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
                        HDF5State.filtered_datasets,
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
                    rx.icon_button("arrow_big_left", on_click=HDF5State.clear()),
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



def filter_form(index: int) -> rx.Component:
    return rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Dataset;Condition (e.g. error == 1)",
                        width="85%",
                        value=PlotState.filter_condition,
                        on_change=lambda value: PlotState.set_filter_condition(value),
                    ),
                    rx.dialog.close(
                        rx.button(
                            "Submit",
                            type="submit"
                        )
                    ),
                ),
                on_submit=lambda index=index: PlotState.filter_data(index, PlotState.filter_condition, HDF5State.dataset_list),
                reset_on_submit=False,
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
                    PlotState.enumerated_parameters,
                    lambda parameter_tuple: rx.table.row(
                        rx.table.cell(
                            rx.hstack(
                                parameter_tuple[1],
                                rx.hstack(
                                    rx.dialog.root(
                                        rx.dialog.trigger(
                                            rx.button(
                                                "+ add filter",
                                            )
                                        ),
                                        rx.dialog.content(
                                            filter_form(index=parameter_tuple[0])
                                        ),
                                    ),
                                    # rx.button(
                                    #     "+ add filter",
                                    #     on_click=PlotState.filter_data(index, "(GM2_Delta_gmuon != -1) & (GM2_Delta_gmuon < 2.35e-10)", HDF5State.dataset_list)
                                    # ),
                                    rx.cond(
                                        PlotState.index_list.contains(parameter_tuple[0]),
                                        rx.button(
                                            "hide",
                                            on_click=PlotState.hide_parameter(parameter_tuple[0]),
                                        ),
                                        rx.button(
                                            "show",
                                            on_click=PlotState.show_parameter(parameter_tuple[0]),
                                        )
                                    ),
                                ),
                                justify="between",
                                align="center",
                            )
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
            rx.hstack(
                pyplot(
                    PlotState.create_plot
                ),
                rx.vstack(
                    rx.button(
                        "+ add parameter",
                        on_click=rx.redirect("/hdf5")
                    ),
                    rx.button(
                        "+ add scan",
                    ),
                )
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

