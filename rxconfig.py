import reflex as rx

config = rx.Config(
    app_name="hdf5_view",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)