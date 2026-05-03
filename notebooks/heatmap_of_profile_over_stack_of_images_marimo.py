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


if __name__ == "__main__":
    app.run()
