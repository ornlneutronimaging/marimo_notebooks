import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    load_tiff_loading, set_load_tiff_loading = mo.state(False)
    return (load_tiff_loading, set_load_tiff_loading)


@app.cell
def _(mo):
    loaded_tiff_array, set_loaded_tiff_array = mo.state(None)
    return (loaded_tiff_array, set_loaded_tiff_array)


@app.cell
def _():
    import numpy as np

    return (np,)


@app.cell
def _(mo):
    instrument_dropdown = mo.ui.dropdown(
        options=["MARS", "VENUS"],
        value="MARS",
        label="Select instrument",
    )
    mo.vstack([
        mo.md("## Heatmap of Profile Over Stack of Images"),
        instrument_dropdown,
    ])
    return (instrument_dropdown,)


@app.cell
def _(instrument_dropdown, mo):
    import os
    import glob

    instrument = instrument_dropdown.value
    mo.stop(instrument is None, mo.md("**Please select an instrument above.**"))

    if instrument == "MARS":
        base_pattern = "/HFIR/CG1D/IPTS-*"
    else:
        base_pattern = "/SNS/VENUS/IPTS-*"

    ipts_folders = sorted(
        [os.path.basename(p) for p in glob.glob(base_pattern) if os.access(p, os.R_OK)],
        reverse=True,
    )

    default_ipts = "IPTS-35409" if "IPTS-35409" in ipts_folders else (ipts_folders[0] if ipts_folders else None)

    if ipts_folders:
        ipts_dropdown = mo.ui.dropdown(
            options=ipts_folders,
            value=default_ipts,
            label="Select IPTS",
        )
    else:
        ipts_dropdown = mo.ui.dropdown(
            options=["(no IPTS folders accessible)"],
            value="(no IPTS folders accessible)",
            label="Select IPTS",
        )

    mo.vstack([
        ipts_dropdown,
    ])
    return (glob, ipts_dropdown, ipts_folders, os)


@app.cell
def _(instrument_dropdown, ipts_dropdown, mo):
    ipts_selected = ipts_dropdown.value
    mo.stop(
        ipts_selected is None or ipts_selected.startswith("(no IPTS"),
        mo.md("**Please select an IPTS above.**"),
    )

    if instrument_dropdown.value == "MARS":
        default_folder_path = f"/HFIR/CG1D/{ipts_selected}/shared"
    else:
        default_folder_path = f"/SNS/VENUS/{ipts_selected}/shared"

    folder_browser = mo.ui.file_browser(
        initial_path=default_folder_path,
        label="Select folder containing TIFF files",
        multiple=False,
        selection_mode="directory",
        restrict_navigation=False,
    )
    load_all_button = mo.ui.run_button(label="Display base name of TIFF files in the selected folder")
    mo.vstack([
        mo.md(f"**Starting path:** `{default_folder_path}`"),
        mo.md("#### Display base name of TIFF files in the selected folder"),
        folder_browser,
        load_all_button,
    ])
    return (
        default_folder_path,
        folder_browser,
        ipts_selected,
        load_all_button,
    )


@app.cell
def _(
    folder_browser,
    load_all_button,
    mo,
    os,
):
    import glob as _glob
    import re

    folder = folder_browser.value[0].path if folder_browser.value else None
    mo.stop(
        folder is None,
        mo.md("**No folder selected yet.**"),
    )

    all_tiffs = sorted(
        _glob.glob(os.path.join(folder, "*.tif"))
        + _glob.glob(os.path.join(folder, "*.tiff"))
    )
    folder_status = mo.md(f"**{len(all_tiffs)} TIFF file(s) found** in `{folder}`")
    mo.stop(
        not load_all_button.value or len(all_tiffs) == 0,
        mo.vstack([
            folder_status,
            mo.md("Click the load button to use these files.") if len(all_tiffs) > 0 else mo.md("Select a different folder to continue."),
        ]),
    )

    selected_files = all_tiffs
    source = "folder"

    base_names = sorted(
        {
            re.sub(r"_[0-9]+$", "", os.path.splitext(os.path.basename(path))[0])
            for path in selected_files
        }
    )
    base_name_selector = mo.ui.multiselect(
        options=base_names,
        value=[],
        label="Select one or more TIFF base names",
        full_width=True,
    )

    mo.vstack([
        mo.md(f"**{len(selected_files)} TIFF file(s) selected** from `{folder}` (via {source})"),
        mo.md(f"**{len(base_names)} base name(s) found** (final numeric index removed)."),
        base_name_selector,
    ])
    return (base_name_selector, selected_files, source, re)


@app.cell
def _(base_name_selector, load_tiff_loading, mo, os, selected_files, re):

    selected_base_names = set(base_name_selector.value)
    filtered_files = [
        path
        for path in selected_files
        if re.sub(r"_[0-9]+$", "", os.path.splitext(os.path.basename(path))[0]) in selected_base_names
    ]

    is_loading = load_tiff_loading()

    load_tiff_button = mo.ui.run_button(
        label="Loading TIFF ..." if is_loading else "Load TIFF",
        disabled=(len(selected_base_names) == 0 or is_loading),
    )

    mo.stop(
        len(selected_base_names) == 0,
        mo.vstack([
            mo.md("Select one or more base names to see how many TIFF files will be used."),
            load_tiff_button,
        ]),
    )

    mo.vstack([
        mo.md(
            f"**{len(filtered_files)} TIFF file(s) will be used** for {len(selected_base_names)} selected base name(s)."
        ),
        load_tiff_button,
    ])
    return (filtered_files, load_tiff_button, selected_base_names)


@app.cell
def _(
    filtered_files,
    load_tiff_button,
    mo,
    np,
    set_load_tiff_loading,
    set_loaded_tiff_array,
):
    from tifffile import imread

    mo.stop(
        not load_tiff_button.value,
        mo.md("Click **Load TIFF** to load the selected TIFF files into a NumPy array."),
    )
    mo.stop(
        len(filtered_files) == 0,
        mo.md("No TIFF files match the selected base name(s)."),
    )

    set_load_tiff_loading(True)
    try:
        loaded_images = []
        for path in mo.status.progress_bar(
            filtered_files,
            title="Loading TIFF ...",
            subtitle=f"{len(filtered_files)} file(s)",
            completion_title="TIFF loading complete",
            show_rate=False,
        ):
            loaded_images.append(imread(path))
        image_shapes = {img.shape for img in loaded_images}

        if len(image_shapes) == 1:
            tiff_array = np.stack(loaded_images, axis=0)
            status_message = (
                f"**Loaded TIFF array shape:** `{tiff_array.shape}` "
                f"(dtype: `{tiff_array.dtype}`)"
            )
        else:
            # Keep heterogeneous image sizes without data loss.
            tiff_array = np.array(loaded_images, dtype=object)
            status_message = (
                f"**Loaded {len(loaded_images)} TIFF images with varying shapes** "
                "into an object-dtype NumPy array."
            )
        set_loaded_tiff_array(tiff_array)
    finally:
        set_load_tiff_loading(False)

    mo.md(status_message)
    return


@app.cell
def _(loaded_tiff_array, mo, np):

    loaded_array = loaded_tiff_array()
    mo.stop(
        loaded_array is None,
        mo.md("Load TIFF files to display the first image."),
    )

    n_images = len(loaded_array)
    image_index = 0
    image_to_display = np.asarray(loaded_array[image_index])
    # get subset of the image to display
    image_to_display = image_to_display[::2, ::2]  # Downsample by a factor of 2

    mo.md(f"**Displaying first image (1/{n_images})**")

    return (image_index, image_to_display)


@app.cell
def _(image_index, image_to_display, mo, np):
    import plotly.express as px

    image_min = float(np.min(image_to_display))
    image_max = float(np.max(image_to_display))
    fig_image = px.imshow(
        image_to_display,
        color_continuous_scale="gray",
        origin="upper",
        binary_string=True,
    )
    fig_image.update_layout(
        title=f"Loaded TIFF image index: {image_index}",
        margin=dict(l=10, r=10, t=40, b=10),
    )

    mo.vstack([
        mo.ui.plotly(fig_image),
        mo.md(f"Image intensity range: min={image_min:.3f}, max={image_max:.3f}"),
    ])

    return (fig_image,)


if __name__ == "__main__":
    app.run()
