"""
components
"""

from typing import Callable
import reflex as rx
from .states import FileTableState


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

def show_group() -> rx.Component:
    """display the group name in a table cell"""

    return rx.cond(
        FileTableState.hdf5_files,
        rx.foreach(
            FileTableState.hdf5_files[0].groups,
            lambda group: rx.table.row(
                rx.table.cell(group.name),
                rx.table.cell(f"shape: {group.size[0]} x {group.size[1]}", text_align="end")
            ),
        ),
        rx.text("")
    )

def show_keys() -> rx.Component:
    """display the keys of a group"""
    return rx.cond(
        FileTableState.hdf5_files,
        rx.foreach(
            FileTableState.hdf5_files[0].groups[0].dataset.keys(),
            lambda key: rx.table.row(
                rx.table.cell(key)
            )
        ),
        rx.text("")
    )

def table_component(header: str, show_item: Callable) -> rx.Component:
    """create a table component to display the various item attributes. Here an item can be any model which is defined elsewhere"""

    return rx.vstack(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell(header),
                        ),
                    ),
                rx.table.body(
                    show_item()
                ),
                width="100%",
            ),
            width="100%",
    )
