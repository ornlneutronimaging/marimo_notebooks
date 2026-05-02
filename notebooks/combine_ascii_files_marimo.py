import marimo

__generated_with = "0.15.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import datetime
    import json
    import os
    import pandas as pd
    import datetime
    import numpy as np

    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

    mo.Html("<font color=blue size=10>iBeatles config file editor</font>")

    DEBUG = True
    if DEBUG:
        initial_path = "/SNS/VENUS/IPTS-35167/shared/processed_data/jean/"
    else:
        initial_path = "/SNS/VENUS/IPTS-35167/shared/processed_data"
    return datetime, initial_path, json, mo, np, os, pd


@app.cell
def _(initial_path, mo):
    def select_normalized_ascii_file():
        normalized_ascii_file = mo.ui.file_browser(
            initial_path=initial_path,
            filetypes=[".txt"],
            multiple=False,
            label="Select axis file created by the normalization_tof notebook (<b>new_x_axis.txt</b>)"
        )
        return normalized_ascii_file
    normalized_ascii_file = select_normalized_ascii_file()
    normalized_ascii_file
    return (normalized_ascii_file,)


@app.cell
def _(initial_path, mo):
    def _():
        json_file = mo.ui.file_browser(
            initial_path=initial_path,
            filetypes=[".json"],
            multiple=False,
            label="Select json file created by the TOF binning notebook (<b>metadata.json</b>)",
        )
        return json_file

    json_file_name = _()
    json_file_name
    return (json_file_name,)


@app.cell
def _(mo, normalized_ascii_file, pd):
    # loading the normalized axis ascii file
    mo.stop(normalized_ascii_file.value == ())
    normalized_ascii_file_full_path = str(normalized_ascii_file.value[0].path)
    # load the ascii file using pandas
    normalized_ascii_file_content = pd.read_csv(normalized_ascii_file_full_path, 
                                                skiprows=1,
                                                names=["file_index", "lambda (Angstroms)", "energy (eV)"])
    print(normalized_ascii_file_content)
    return normalized_ascii_file_content, normalized_ascii_file_full_path


@app.cell
def _(json, json_file_name, mo):
    # loading the tof binned json file
    mo.stop(json_file_name.value == ())
    json_file_name_full_path = str(json_file_name.value[0].path)
    json_file_content = json.load(open(json_file_name_full_path))
    return json_file_content, json_file_name_full_path


@app.cell
def _(initial_path, mo):
    output_folder_ui = mo.ui.file_browser(
        initial_path=initial_path,
        label="Select output folder",
        multiple=False,
        selection_mode='directory'
    )
    output_folder_ui
    return (output_folder_ui,)


@app.function
def make_ascii_file(metadata=[], data=[], output_file_name="", sep=","):
    f = open(output_file_name, "w")
    for _meta in metadata:
        _line = _meta + "\n"
        f.write(_line)

    for _data in data:
        _line = str(_data) + "\n"
        f.write(_line)

    f.close()


@app.cell
def _(
    get_current_time_in_special_file_name_format,
    json_file_content,
    json_file_name_full_path,
    normalized_ascii_file_content,
    normalized_ascii_file_full_path,
    np,
    os,
    output_folder_ui,
):
    def merge_and_export_ascii(x):
        # print(f"{json_file_content =}")
        # print(f"{normalized_ascii_file_content =}")

        lambda_array = np.array(normalized_ascii_file_content['lambda (Angstroms)'])
        energy_array = np.array(normalized_ascii_file_content['energy (eV)'])

        output_folder = str(output_folder_ui.value[0].path)
        # print(f"{output_folder =}")

        current_time = get_current_time_in_special_file_name_format()
        # print(f"{current_time =}")

        # output columns
        # new file index | starting tof | ending tof | mean tof | staring lambda | ending lambda | mean lambda | starting energy | ending energy | mean energy

        for _image in json_file_content.keys():
            list_index = json_file_content[_image]['file_index']
            list_lambda = []
            list_energy = []
            for _index in list_index:
                list_energy.append(energy_array[_index])
                list_lambda.append(lambda_array[_index])

            json_file_content[_image]['energy'] = list_energy
        
        file_name = os.path.join(output_folder, f"merged_ascii_{current_time}.txt")
        metadata = [f"x-axis file from normalized data: {normalized_ascii_file_full_path}",
                    f"json file from rebinned data (via iBeatles): {json_file_name_full_path}"
                    "",
                    f"file index, starting tof, ending tof, mean tof, starting lambda, ending lambda, mean lambda, starting energy, ending energy, mean energy",
                   ]
        data = []
        list_images_sorted = list(json_file_content.keys())
        list_images_sorted.sort()
        for _index, _image in enumerate(list_images_sorted):
            tof = json_file_content[_image]['tof']
            tof_min = tof[0]
            tof_max = tof[-1]
            tof_mean = np.mean(tof)
    
            _lambda = json_file_content[_image]['lambda']
            _lambda_min = _lambda[0]
            _lambda_max = _lambda[-1]
            _lambda_mean = np.mean(_lambda)

            _energy = json_file_content[_image]['energy']
            _energy_min = np.min(_energy)
            _energy_max = np.max(_energy)
            _energy_mean = np.mean(_energy)
        
            data.append(f"{_index}, {tof_min}, {tof_max}, {tof_mean}, {_lambda_min}, {_lambda_max}, {_lambda_mean}, {_energy_min}, {_energy_max}, {_energy_mean}")

        make_ascii_file(metadata=metadata, 
                       data=data,
                       output_file_name=file_name)
        print(f"{file_name} has been created!")

    return (merge_and_export_ascii,)


@app.cell
def _(datetime):
    def get_current_time_in_special_file_name_format():
        """format the current date and time into something like  04m_07d_2022y_08h_06mn"""
        current_time = datetime.datetime.now().strftime("%mm_%dd_%Yy_%Hh_%Mmn")
        return current_time
    return (get_current_time_in_special_file_name_format,)


@app.cell
def _(
    merge_and_export_ascii,
    mo,
    normalized_ascii_file_content,
    output_folder_ui,
):
    mo.stop(output_folder_ui.value == ())

    create_config_button = mo.ui.button(label="Create combined ASCII file",
                                        on_click=lambda x: merge_and_export_ascii(x),
                                        disabled=normalized_ascii_file_content is None,
                                        full_width=True,
                                       )
    create_config_button
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
