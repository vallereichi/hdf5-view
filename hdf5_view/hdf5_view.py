"""
Entry point
"""

import reflex as rx
from .states import FileTableState
from .components import upload_component, table_component
from .components import show_filename, show_group, show_keys



def index() -> rx.Component:
    """Welcome Page (Index)"""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("DISPLAY HDF5!!", size="9"),
            upload_component(),
            rx.cond(
                FileTableState.hdf5_files,
                rx.vstack(
                    table_component(["Files"], show_filename),
                    rx.button("clear", on_click=FileTableState.clear_table()),
                    width="100%"
                )
            ),
            spacing="5",
            justify="start",
            padding_top="10em",
            min_height="85vh",
        ),
    )


def hdf5() -> rx.Component:
    """display the conten of the selected hdf5 file"""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.hstack(
                rx.link(rx.icon_button("arrow_big_left"), href="/", position="top-left"),
                rx.cond(
                    FileTableState.selected_file_idx >= 0,
                    rx.heading(FileTableState.hdf5_files[FileTableState.selected_file_idx].filename),
                    rx.heading("No file selected")
                )
            ),
            rx.vstack(

                rx.cond(
                    FileTableState.selected_file_idx >= 0,
                    table_component(["Group", ""], show_group),

                ),
                rx.cond(
                    FileTableState.selected_group_idx >= 0,
                    rx.vstack(
                        rx.hstack(
                            rx.input(placeholder="search ..", on_change=lambda value: FileTableState.search_key(value)),
                            rx.button("clear", on_click=lambda: FileTableState.clear_group_selection())
                        ),
                        table_component(
                            ["Keys"],
                            show_keys,
                            max_height="50vh",
                            overflow="auto",
                        ),
                        padding="1em",
                        border="3px solid #ccc",
                        border_radius="1em",
                        width="100%"
                    ),
                    rx.text(""),
                ),
                width="100%",
            ),
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
