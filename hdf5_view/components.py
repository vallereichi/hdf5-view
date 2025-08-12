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
        lambda hdf5, index: rx.table.row(
            rx.table.cell(
                rx.link(
                    hdf5.filename,
                    href="/hdf5/"
                ),
            ),
            on_click=lambda: FileTableState.select_file(index),
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

def show_group() -> rx.Component:
    """display the group name in a table cell"""

    return rx.cond(
        FileTableState.groups,
        rx.foreach(
            FileTableState.groups,
            lambda group, index: rx.table.row(
                rx.table.cell(group.name),
                rx.table.cell(f"{group.size[1]} x {group.size[0]}", text_align="end"),
                on_click=lambda: FileTableState.select_group(index),
                style={
                            "border": "2px solid transparent",
                            "cursor": "pointer"
                    },
                _hover={
                        "background": "#222",
                        "border-radius": "0.5em",
                        "cursor": "pointer"
                }
            ),
        ),
        rx.text("")
    )

def show_keys() -> rx.Component:
    """display the keys of a group"""
    return rx.cond(
        FileTableState.filtered_keys,
        rx.foreach(
                FileTableState.filtered_keys,
                lambda key: rx.table.row(
                    rx.table.cell(
                        key,
                        style={
                            "border": "2px solid transparent",
                            "cursor": "pointer",
                            "width": "100%"
                        },
                        _hover={
                            "background": "#222",
                            "border-radius": "0.5em",
                            "cursor": "pointer"
                        }
                    )
                )
            ),
        rx.text("")
    )


def table_component(headers: list[str], show_item: Callable, **kwargs) -> rx.Component:
    """create a table component to display the various item attributes. Here an item can be any model which is defined elsewhere"""

    return rx.vstack(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            headers,
                            lambda header: rx.table.column_header_cell(header)
                        )
                    )
                ),
                rx.table.body(
                    show_item()
                ),
                width="100%",
            ),
            width="100%",
            **kwargs
    )
