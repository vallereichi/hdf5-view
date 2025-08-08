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
            table_component("Filename", show_filename),      
            table_component("Group", show_group),
            table_component("Keys", show_keys),
            rx.button("clear", on_click=FileTableState.clear_table()),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
