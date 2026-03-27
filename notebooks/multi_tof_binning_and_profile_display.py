from gc import disable
from json import load

import marimo

__generated_with = "0.13.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import os

    IPTS = "IPTS-35112"
    default_roi = {'x_range': [0, 255], 'y_range': [0, 255], 'x_offset': 0, 'y_offset': 0}

    return mo, os, IPTS


@app.cell
def _(mo, os, IPTS):
    
    default_path = f"/SNS/VENUS/{IPTS}/shared/autoreduce/images/tpx1/raw/radiography/"
    entries = sorted(
        [
            d
            for d in os.listdir(default_path)
            if os.path.isdir(os.path.join(default_path, d))
        ]
    )
    folder_dropdown = mo.ui.dropdown(
        options=entries,
        label="Select a folder",
    )
    mo.vstack([
        mo.md(f"**Default starting path:** `{default_path}`"),
        folder_dropdown,
    ])
    return default_path, folder_dropdown


@app.cell
def _(mo):
    run_button = mo.ui.run_button(label="Load all data contained in the selected folder")
    run_button
    return (run_button,)


@app.cell
def _(run_button, folder_dropdown, default_path, mo, os):
    
    from tqdm import tqdm
    import tifffile
    import numpy as np
    
    def retrieve_data_filepath(full_path):
        # Placeholder for data retrieval logic
        # This function should return the file paths of the data needed for binning and profile display
        import os
        import glob
        list_folders = os.listdir(full_path)
        list_folders.sort()
        
        data_filepath_dict = {}
        for _folder in list_folders:
            list_files = glob.glob(os.path.join(full_path, _folder, "*.tif*"))
            list_files.sort()
            data_filepath_dict[_folder] = list_files
        
        return data_filepath_dict
    
    mo.stop(not run_button.value, mo.md("_Click the button to load the selected folder._"))
    selected = folder_dropdown.value
    
    if selected:
        full_path = os.path.join(default_path, selected)
        mo.md(f"**Selected folder:** {full_path}")
        all_data_filepath_dict = retrieve_data_filepath(full_path)
        # print(f"{all_data_filepath_dict=}")
        
        mo.vstack([
            mo.md(f"{len(all_data_filepath_dict)} folders found in the selected folder."),
            mo.md("**Data file paths:**"),
        ])
        
        # loading the data
        all_data_dict = {}
        all_data_integrated_dict = {}
        
        # print(f"{all_data_filepath_dict.keys()=}")
        # print(f"{len(all_data_filepath_dict.keys())=}")
                
        for index in mo.status.progress_bar(range(len(all_data_filepath_dict.keys())), 
                                            title="Loading data...",
                                            subtitle="Please wait",
                                            show_eta=True,
                                            show_rate=True):
            _key = list(all_data_filepath_dict.keys())[index]
            list_data_file = all_data_filepath_dict[_key]
            data_array = []
            for _file in tqdm(list_data_file):
                with tifffile.TiffFile(_file) as tif:
                    _image = tif.pages[0].asarray()
                    data_array.append(_image)
            all_data_dict[_key] = data_array
            all_data_integrated_dict[_key] = np.sum(data_array, axis=0)
                        
    else:
        mo.md("_No folder selected yet._")
    
    return np, all_data_dict, all_data_integrated_dict


@app.cell
def _(mo):
    # add a horizontal line
    mo.Html("<hr style='border: none; border-top: 5px solid #333; margin: 20px 0;'>")
    return


@app.cell
def _(all_data_integrated_dict, mo):
    import plotly.express as px

    keys = list(all_data_integrated_dict.keys())
    slider_folder_index = mo.ui.slider(
        start=0,
        stop=len(keys) - 1,
        step=1,
        value=0,
        disabled= (len(keys) == 1),
        show_value=True,
    )
    # slider_folder_index
    
    mo.Html(f"""
    <div style="display:flex; align-items:center; gap:10px;">
    <span style="min-width:100px;">Select folder index</span>
    {slider_folder_index}
    </div>
    """)
    
    return keys, px, slider_folder_index


@app.cell
def _(all_data_integrated_dict, keys, mo, slider_folder_index, default_roi):
    key = keys[slider_folder_index.value]
    data = all_data_integrated_dict[key]
    h, w = data.shape[:2]

    x_range = mo.ui.range_slider(start=0, stop=w - 1, value=default_roi['x_range'], label="x range")
    x_offset = mo.ui.slider(start=-(w - 1), stop=w - 1, value=default_roi['x_offset'], label="x offset")
    y_range = mo.ui.range_slider(start=0, stop=h - 1, value=default_roi['y_range'], label="y range", orientation="horizontal",)
    y_offset = mo.ui.slider(start=-(h - 1), stop=h - 1, value=default_roi['y_offset'], label="y offset", orientation='horizontal')

    mo.vstack([
        mo.md(f"**Key:** `{key}` ({slider_folder_index.value + 1}/{len(keys)})"),
        mo.md("**ROI selection:**"),
        mo.hstack([x_range, x_offset], justify="start"),
        mo.hstack([y_range, y_offset], justify="start"),
    ])
    
    return data, x_range, x_offset, y_range, y_offset


@app.cell
def _(x_range, x_offset, y_range, y_offset, default_roi):
    default_roi['x_range'] = x_range.value
    default_roi['y_range'] = y_range.value
    default_roi['x_offset'] = x_offset.value
    default_roi['y_offset'] = y_offset.value


@app.cell
def _(data, np, mo, px, x_range, x_offset, y_range, y_offset, slider_folder_index, all_data_dict, keys):
    import plotly.graph_objects as go

    h2, w2 = data.shape[:2]
    x0 = max(0, min(x_range.value[0] + x_offset.value, w2 - 1))
    x1 = max(0, min(x_range.value[1] + x_offset.value, w2 - 1))
    y0 = max(0, min(y_range.value[0] + y_offset.value, h2 - 1))
    y1 = max(0, min(y_range.value[1] + y_offset.value, h2 - 1))

    # calculate the profile along the tof direction of the box selected
    data_selected = all_data_dict[keys[slider_folder_index.value]]
    profile = []
    for _data in data_selected:
        profile.append(np.mean(_data[y0:y1, x0:x1]))
    
    fig_image = px.imshow(data)
    fig_image.update_layout(coloraxis_showscale=True)

    fig_image.add_shape(
        type="rect",
        x0=x0, x1=x1,
        y0=y0, y1=y1,
        line=dict(color="red", width=2),
    )

    # fig_profile = px.scatter(x=list(range(len(profile))), y=profile)
    # fig_profile.update_layout(
    #     xaxis_title="TOF index",
    #     yaxis_title="Mean intensity",
    #     title="Mean counts of the selected ROI along the TOF direction",
    # )

    mo.vstack([
        mo.md(
            f"**ROI:** x=[{x0}, {x1}], "
            f"y=[{y0}, {y1}]"
        ),
        mo.vstack([mo.ui.plotly(fig_image)]),
    ])
    
    return profile


@app.cell
def _(profile, np, px, mo, tof_table):
    
    fig_profile = px.scatter(x=list(range(len(profile))), y=profile)
    fig_profile.update_layout(
        xaxis_title="TOF index",
        yaxis_title="Mean intensity",
        title="Mean counts of the selected ROI along the TOF direction",
    )
    
    index_to_use = np.arange(5)
    list_keys = [f"use_{i}" for i in index_to_use]
    for my_key in list_keys:
        _use_it = tof_table.value[my_key]
        if _use_it:
            left_tof_index = tof_table.value[f"left_tof_{my_key.split('_')[-1]}"]
            right_tof_index = tof_table.value[f"right_tof_{my_key.split('_')[-1]}"]

            # display a vertical span on the profile plot to indicate the selected TOF range
            fig_profile.add_vrect(
                x0=left_tof_index, x1=right_tof_index,
                fillcolor="green", opacity=0.3, line_width=0,
            )

    mo.vstack([
        mo.vstack([mo.ui.plotly(fig_profile)]),
    ])
    
    return
    

@app.cell
def _(mo, all_data_integrated_dict):
    mo.stop(not all_data_integrated_dict)
     
    num_rows = 5
    tof_table = mo.ui.dictionary({
        f"use_{i}": mo.ui.checkbox(label="") for i in range(num_rows)
    } | {
        f"left_tof_{i}": mo.ui.number(label="", start=0, stop=100000, value=0) for i in range(num_rows)
    } | {
        f"right_tof_{i}": mo.ui.number(label="", start=0, stop=100000, value=0) for i in range(num_rows)
    })

    header = mo.hstack([
        mo.md("**Use**"),
        mo.md("**Left TOF index**"),
        mo.md("**Right TOF index**"),
    ], widths=[1, 2, 2])

    rows = [
        mo.hstack([
            tof_table.elements[f"use_{i}"],
            tof_table.elements[f"left_tof_{i}"],
            tof_table.elements[f"right_tof_{i}"],
        ], widths=[1, 2, 2])
        for i in range(num_rows)
    ]

    mo.vstack([
        mo.md("**TOF Binning Ranges:**"),
        header,
        *rows,
    ])
    return (tof_table,)


@app.cell
def _(mo, all_data_integrated_dict):
    # display this only if data have been loaded
    mo.stop(not all_data_integrated_dict)
    
    # add a horizontal line
    mo.Html("<hr style='border: none; border-top: 5px solid #333; margin: 20px 0;'>")
    return















if __name__ == "__main__":
    app.run()
