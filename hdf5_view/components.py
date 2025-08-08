import reflex as rx
from .states import FileTableState
from .models import HDF5_File
from typing import Callable


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
            on_drop=FileTableState.handle_upload(rx.upload_files(upload_id="file_upload"))
        )
    )



def show_filename() -> rx.Component:
    """Display the hdf5 file information"""
    return rx.foreach(
        FileTableState.hdf5_files,
        lambda hdf5: rx.table.row(
           rx.table.cell(hdf5.filename)
        )
    )

def table_component(show_item: Callable) -> rx.Component:
    """create a table component to display the various item attributes. Here an item can be any model which is defined elsewhere"""

    return rx.vstack(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Filename"),
                        ),
                    ),
                rx.table.body(
                    show_item()
                ),
                width="100%",
            ),
            rx.button("clear", on_click=FileTableState.clear_table()),
            width="100%",
        )