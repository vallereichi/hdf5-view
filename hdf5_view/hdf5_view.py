"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
import h5py

test_file = "../tests/MSSM7atQ.hdf5"

class HDF5(rx.Base):
    """class holding information about the hdf5 file"""
    filename: str
    groups: list[str]
    attributes: list[str]
    metadata: dict


def read_hdf5(file_path: str) -> HDF5:
    """Load a hdf5 file and return it in a sensiible format"""
    hdf5 = HDF5(filename="", groups=[], attributes=[], metadata={})

    with h5py.File(file_path, 'r') as f:
        hdf5.filename = file_path.split('.')[-2].split('/')[-1]
        hdf5.groups = list(f.keys())
        hdf5.attributes = list(f.attrs.keys())
        hdf5.metadata = "TODO: extract metadata"

    return hdf5



class State(rx.State):
    """State containing all the hdf5 information."""
    hdf5_files: list[HDF5]

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

    @rx.event
    def clear_table(self):
        """clear the table"""
        self.hdf5_files = []

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
            on_drop=State.handle_upload(rx.upload_files(upload_id="file_upload"))
        )
    )

def show_filename(hdf5: HDF5) -> rx.Component:
    """Display the hdf5 file information"""
    return rx.table.row(
        rx.table.cell(hdf5.filename)
    )

def table_component() -> rx.Component:
    """create a table component to display the hdf5 files"""
    return rx.cond(
        State.hdf5_files,
        rx.vstack(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Filename"),
                        ),
                    ),
                rx.table.body(
                    rx.foreach(
                        State.hdf5_files, show_filename
                    )
                ),
                width="100%",
            ),
            rx.button("clear", on_click=State.clear_table()),
            width="100%",
        ),
        rx.text("")
    )


def index() -> rx.Component:
    """Welcome Page (Index)"""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("DISPLAY HDF5!!", size="9"),
            upload_component(),
            table_component(),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
