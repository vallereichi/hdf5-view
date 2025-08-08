import reflex as rx
from .components import upload_component, table_component
from .components import show_filename



def index() -> rx.Component:
    """Welcome Page (Index)"""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("DISPLAY HDF5!!", size="9"),
            upload_component(),
            table_component(show_filename),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
