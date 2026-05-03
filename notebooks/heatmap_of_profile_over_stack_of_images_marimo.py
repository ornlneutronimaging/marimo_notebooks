import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


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
    load_all_button = mo.ui.run_button(label="Load all TIFFs from folder")
    mo.vstack([
        mo.md(f"**Starting path:** `{default_folder_path}`"),
        mo.md("#### Load TIFFs from a folder"),
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

    mo.md(f"**{len(selected_files)} TIFF file(s) selected** from `{folder}` (via {source})")
    return (selected_files, source)


if __name__ == "__main__":
    app.run()
