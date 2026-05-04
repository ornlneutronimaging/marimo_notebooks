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
        full_width=True,
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
def _(loaded_tiff_array, mo):

    loaded_array_for_slider = loaded_tiff_array()
    mo.stop(
        loaded_array_for_slider is None,
        mo.md("Load TIFF files to display images."),
    )

    n_images = len(loaded_array_for_slider)
    image_slider = mo.ui.slider(
        start=0,
        stop=n_images - 1,
        step=1,
        value=0,
        show_value=True,
        disabled=(n_images <= 1),
        label="Image index",
    )

    mo.vstack([
        mo.md(f"Use the slider to browse {n_images} loaded image(s)."),
        image_slider,
    ])

    return (image_slider, n_images)


@app.cell
def _(image_slider, loaded_tiff_array, mo, np, n_images):
    loaded_array_for_display = loaded_tiff_array()
    display_downsample_factor = 10
    mo.stop(
        loaded_array_for_display is None,
        mo.md("Load TIFF files to display images."),
    )

    image_index = int(image_slider.value)
    image_to_display = np.asarray(loaded_array_for_display[image_index])
    # get subset of the image to display
    image_to_display = image_to_display[::display_downsample_factor, ::display_downsample_factor]

    mo.md(f"**Displaying image {image_index + 1}/{n_images}**")
    return (display_downsample_factor, image_index, image_to_display)


@app.cell
def _(image_index, image_to_display, mo, n_images, np):
    import plotly.express as px
    import plotly.graph_objects as go

    integrate_over = mo.ui.radio(
        options=["horizontal", "vertical"],
        value="horizontal",
        label="Profile selected will be integrate over:",
    )

    image_min = float(np.min(image_to_display))
    image_max = float(np.max(image_to_display))
    fig_image = px.imshow(
        image_to_display,
        color_continuous_scale="Viridis",
        origin="upper",
        binary_string=False,
    )
    fig_image.update_traces(
        hovertemplate="x: %{x}<br>y: %{y}<br>intensity: %{z}<extra></extra>"
    )
    fig_image.update_coloraxes(
        showscale=True,
        colorbar=dict(title="Intensity"),
    )
    fig_image.update_layout(
        title=f"Loaded TIFF image {image_index + 1}/{n_images}",
        width=1200,
        height=900,
        margin=dict(l=10, r=10, t=40, b=10),
        dragmode="select",
        newselection=dict(line=dict(color="red", width=3)),
        activeselection=dict(fillcolor="rgba(255, 0, 0, 0.20)"),
    )

    # marimo selection events are emitted for scatter-like traces.
    # Add an effectively invisible point grid to capture box/lasso selections.
    h, w = image_to_display.shape[:2]
    heatmap_overlay_x_grid, heatmap_overlay_y_grid = np.meshgrid(np.arange(w), np.arange(h))
    fig_image.add_trace(
        go.Scattergl(
            x=heatmap_overlay_x_grid.ravel(),
            y=heatmap_overlay_y_grid.ravel(),
            mode="markers",
            marker=dict(size=6, opacity=0.001, color="rgba(0, 0, 0, 1)"),
            hoverinfo="skip",
            showlegend=False,
            selected=dict(marker=dict(opacity=0.001)),
            unselected=dict(marker=dict(opacity=0.001)),
        )
    )

    plot_widget = mo.ui.plotly(fig_image)

    mo.vstack([
        integrate_over,
        plot_widget,
    ])

    return (fig_image, image_max, image_min, integrate_over, plot_widget, px)


@app.cell
def _(image_max, image_min, mo, plot_widget):
    display_heatmap_button = mo.ui.run_button(
        label="Display heatmap of profile selected over full stack of images",
        full_width=True,
    )

    mo.vstack([
        display_heatmap_button,
        mo.md(f"Image intensity range: min={image_min:.3f}, max={image_max:.3f}"),
    ])

    return (display_heatmap_button,)


@app.cell
def _(display_heatmap_button, mo, plot_widget):
    mo.stop(
        not display_heatmap_button.value,
        mo.md("Click the button to display the selected region corners."),
    )

    selection_value = plot_widget.value

    x_values = []
    y_values = []

    def add_xy(xs, ys):
        if not xs or not ys:
            return
        x_values.extend(float(x) for x in xs)
        y_values.extend(float(y) for y in ys)

    points = plot_widget.points
    if isinstance(points, list):
        selected_points_x_values = [p.get("x") for p in points if isinstance(p, dict) and p.get("x") is not None]
        selected_points_y_values = [p.get("y") for p in points if isinstance(p, dict) and p.get("y") is not None]
        add_xy(selected_points_x_values, selected_points_y_values)

    selection_range = plot_widget.ranges
    if isinstance(selection_range, dict):
        xr = selection_range.get("x")
        yr = selection_range.get("y")
        if isinstance(xr, (list, tuple)) and len(xr) >= 2 and isinstance(yr, (list, tuple)) and len(yr) >= 2:
            add_xy([xr[0], xr[1]], [yr[0], yr[1]])

    if isinstance(selection_value, dict):
        lasso_points = selection_value.get("lassoPoints")
        if isinstance(lasso_points, dict):
            lasso_x_values = lasso_points.get("x")
            lasso_y_values = lasso_points.get("y")
            if isinstance(lasso_x_values, (list, tuple)) and isinstance(lasso_y_values, (list, tuple)):
                add_xy(lasso_x_values, lasso_y_values)

        # Some plotly payloads expose selected coordinates directly.
        selection_x_values = selection_value.get("x")
        selection_y_values = selection_value.get("y")
        if isinstance(selection_x_values, (list, tuple)) and isinstance(selection_y_values, (list, tuple)):
            add_xy(selection_x_values, selection_y_values)

        # Support bounding-box style payloads if present.
        x0 = selection_value.get("x0")
        x1 = selection_value.get("x1")
        y0 = selection_value.get("y0")
        y1 = selection_value.get("y1")
        if None not in (x0, x1, y0, y1):
            add_xy([x0, x1], [y0, y1])

    elif isinstance(selection_value, list):
        xs = [p.get("x") for p in selection_value if isinstance(p, dict) and p.get("x") is not None]
        ys = [p.get("y") for p in selection_value if isinstance(p, dict) and p.get("y") is not None]
        add_xy(xs, ys)

    print(f"Extracted x values: {x_values}")
    print(f"Extracted y values: {y_values}")

    if not x_values or not y_values:
        mo.vstack([
            mo.md("### Selected region corners"),
            mo.md("No valid region selection detected. Please use box selection on the heatmap first."),
        ])
        x_min = x_max = y_min = y_max = None
        
    else:
        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = max(y_values)
        mo.vstack([
            mo.md("### Selected region corners"),
            mo.md(f"Top-left: (x={x_min:.2f}, y={y_min:.2f})"),
            mo.md(f"Top-right: (x={x_max:.2f}, y={y_min:.2f})"),
            mo.md(f"Bottom-left: (x={x_min:.2f}, y={y_max:.2f})"),
            mo.md(f"Bottom-right: (x={x_max:.2f}, y={y_max:.2f})"),
        ])

    return (selection_value, x_min, x_max, y_min, y_max)

@app.cell
def _(
    display_downsample_factor,
    display_heatmap_button,
    integrate_over,
    loaded_tiff_array,
    mo,
    np,
    px,
    x_min,
    x_max,
    y_min,
    y_max,
):
    fig_profile_heatmap = None
    heat_map_of_profile_array = None

    loaded_stack = loaded_tiff_array()
    mo.stop(
        not display_heatmap_button.value,
        mo.md("Click the button to display the profile heatmap over the full stack."),
    )

    mo.stop(
        None in (x_min, x_max, y_min, y_max),
        mo.md("Select a region on the heatmap to enable the button for displaying the profile heatmap."),
    )

    mo.stop(
        loaded_stack is None,
        mo.md("Load TIFF files before displaying the profile heatmap."),
    )

    full_resolution_x_min = int(np.floor(x_min * display_downsample_factor))
    full_resolution_x_max = int(np.ceil((x_max + 1) * display_downsample_factor))
    full_resolution_y_min = int(np.floor(y_min * display_downsample_factor))
    full_resolution_y_max = int(np.ceil((y_max + 1) * display_downsample_factor))

    heat_map_of_profile = []
    for image_frame in loaded_stack:
        image_array = np.asarray(image_frame)
        selected_region = image_array[
            full_resolution_y_min:full_resolution_y_max,
            full_resolution_x_min:full_resolution_x_max,
        ]
        mo.stop(
            selected_region.size == 0,
            mo.md("The selected region is empty after mapping to the full-resolution stack."),
        )

        if integrate_over.value == "horizontal":
            profile = np.mean(selected_region, axis=0)
        else:
            profile = np.mean(selected_region, axis=1)
        heat_map_of_profile.append(profile)

    heat_map_of_profile_array = np.vstack(heat_map_of_profile)
    heat_map_of_profile_display = heat_map_of_profile_array.T
    fig_profile_heatmap = px.imshow(
        heat_map_of_profile_display,
        color_continuous_scale="Viridis",
        origin="upper",
        aspect="auto",
    )
    fig_profile_heatmap.update_coloraxes(
        showscale=True,
        colorbar=dict(title="Mean intensity"),
    )
    fig_profile_heatmap.update_layout(
        title="Heatmap of selected profile over full stack of images",
        xaxis_title="Image index",
        yaxis_title="Pixel index along profile",
        width=1200,
        height=900,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    mo.vstack([
        mo.md(
            f"Selected full-resolution region: x=[{full_resolution_x_min}, {full_resolution_x_max - 1}], "
            f"y=[{full_resolution_y_min}, {full_resolution_y_max - 1}]"
        ),
        mo.ui.plotly(fig_profile_heatmap),
    ])
    
    return (fig_profile_heatmap, heat_map_of_profile_array)


@app.cell
def _(mo):
    export_heatmap_ascii_button = mo.ui.run_button(
        label="Export heatmap as ASCII file",
        full_width=True,
    )

    return (export_heatmap_ascii_button,)


@app.cell
def _(export_heatmap_ascii_button, heat_map_of_profile_array, mo):
    mo.stop(
        heat_map_of_profile_array is None,
        mo.md("Display the profile heatmap to enable ASCII export."),
    )

    mo.vstack([
        export_heatmap_ascii_button,
    ])
    return


@app.cell
def _(export_heatmap_ascii_button, folder_browser, heat_map_of_profile_array, mo):
    export_heatmap_folder_browser = None

    mo.stop(
        heat_map_of_profile_array is None,
        mo.md("Display the profile heatmap to enable ASCII export."),
    )

    mo.stop(
        not export_heatmap_ascii_button.value,
        mo.md("Click the export button to choose an output folder for the ASCII file."),
    )

    initial_export_path = folder_browser.value[0].path if folder_browser.value else "."
    export_heatmap_folder_browser = mo.ui.file_browser(
        initial_path=initial_export_path,
        label="Select output folder for ASCII heatmap export",
        multiple=False,
        selection_mode="directory",
        restrict_navigation=False,
    )

    mo.vstack([
        mo.md("### Export Heatmap as ASCII"),
        export_heatmap_folder_browser,
    ])

    return (export_heatmap_folder_browser,)


@app.cell
def _(export_heatmap_folder_browser, heat_map_of_profile_array, mo, np, os):
    from datetime import datetime

    mo.stop(
        export_heatmap_folder_browser is None or not export_heatmap_folder_browser.value,
        mo.md("Select an output folder to create the ASCII heatmap file."),
    )

    output_folder = export_heatmap_folder_browser.value[0].path
    timestamp_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_ascii_path = os.path.join(output_folder, f"heatmap_{timestamp_string}.txt")

    np.savetxt(output_ascii_path, heat_map_of_profile_array, fmt="%.10g")

    mo.md(f"ASCII heatmap exported to `{output_ascii_path}`")
    return (output_ascii_path,)


if __name__ == "__main__":
    app.run()
