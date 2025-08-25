import os
import reflex as rx
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

    @rx.event
    def load_file(self, file_name: str):
        self.file_name = file_name
        self.group_list = self.find_groups(os.path.join(rx.get_upload_dir(), self.file_name))

def upload_component() -> rx.Component:
    """Input field for file selection and 'drag&drop' area"""
    return rx.vstack(
        rx.upload(
            rx.button("upload"),
            id="file_upload",
            border="2px dashed #ccc",
            border_radius="1em",
            justify="center",
            width="69vw",
            padding="2em",
            on_drop=FileState.handle_upload(rx.upload_files(upload_id="file_upload"))
        )
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
            rx.cond(
                HDF5State.file_name,
                rx.text(HDF5State.file_name),
                rx.text("please select a file to view its contents")
            ),
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
                    lambda group: rx.table.row(
                        rx.table.cell(
                            group,
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
        ),
        spacing="5",
        padding_top="5rem",
        justify="start",
        min_height="85vh",

    )


app = rx.App()
app.add_page(index)
app.add_page(hdf5)
