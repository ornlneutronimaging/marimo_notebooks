import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    import os

    venus_path = "/SNS/VENUS"
    if os.path.isdir(venus_path):
        ipts_folders = sorted(
            [d for d in os.listdir(venus_path) if d.startswith("IPTS-")],
            reverse=True,
        )
    else:
        ipts_folders = []

    if ipts_folders:
        default_ipts = "IPTS-37493" if "IPTS-37493" in ipts_folders else None
        ipts_dropdown = mo.ui.dropdown(
            options=ipts_folders,
            value=default_ipts,
            label="Select IPTS folder",
        )
    else:
        ipts_dropdown = mo.ui.dropdown(
            options=["(no IPTS folders found)"],
            value="(no IPTS folders found)",
            label="Select IPTS folder",
        )
    ipts_dropdown
    return (ipts_dropdown, venus_path)


@app.cell
def _(ipts_dropdown, mo, venus_path):
    import os as _os

    ipts_selected = ipts_dropdown.value
    mo.stop(
        ipts_selected is None or ipts_selected == "(no IPTS folders found)",
        mo.md("**Please select an IPTS folder above.**"),
    )
    ipts_path = _os.path.join(venus_path, ipts_selected, "images", "ikonxl", "raw", "ct")
    mo.md(f"IPTS path: `{ipts_path}`")
    return (ipts_path,)


@app.cell
def _(ipts_path, mo):
    file_browser = mo.ui.file_browser(
        initial_path=ipts_path,
        filetypes=[".tiff", ".tif"],
        label="Select the 0° TIFF image",
        multiple=False,
    )
    file_browser
    return (file_browser,)


@app.cell
def _(file_browser, mo):
    mo.stop(len(file_browser.value) == 0, mo.md("**Please select the 0° TIFF image above.**"))
    selected_path_0 = file_browser.value[0].path
    mo.md(f"Selected: `{selected_path_0}`")
    return (selected_path_0,)


@app.cell
def _(ipts_path, mo):
    file_browser_180 = mo.ui.file_browser(
        initial_path=ipts_path,
        filetypes=[".tiff", ".tif"],
        label="Select the 180° TIFF image",
        multiple=False,
    )
    file_browser_180
    return (file_browser_180,)


@app.cell
def _(file_browser_180, mo):
    mo.stop(len(file_browser_180.value) == 0, mo.md("**Please select the 180° TIFF image above.**"))
    selected_path_180 = file_browser_180.value[0].path
    mo.md(f"Selected: `{selected_path_180}`")
    return (selected_path_180,)


@app.cell
def _(selected_path_0, selected_path_180):
    from skimage.transform import resize
    import tifffile as tiff
    import numpy as np
    import plotly.express as px

    img_0 = np.flipud(tiff.imread(selected_path_0))
    img_180 = np.flipud(tiff.imread(selected_path_180))

    scale_factor = 0.25

    new_shape = (int(img_0.shape[0] * scale_factor), int(img_0.shape[1] * scale_factor))
    low_res_img_0 = resize(img_0, new_shape, 
                           anti_aliasing=True,
                           preserve_range=True).astype(img_0.dtype)
    low_res_img_180 = resize(img_180, new_shape, 
                             anti_aliasing=True,
                             preserve_range=True).astype(img_180.dtype)
    low_res_img_180_flipped = np.fliplr(low_res_img_180)

    x_axis = np.linspace(0, img_0.shape[1], new_shape[1])
    y_axis = np.linspace(0, img_0.shape[0], new_shape[0])

    # Blend the two images: average of 0° and flipped 180°
    blended = (low_res_img_0.astype(np.float32) + low_res_img_180_flipped.astype(np.float32)) / 2.0
    blended_with_no_flips = (low_res_img_0.astype(np.float32) + low_res_img_180.astype(np.float32)) / 2.0

    fig = px.imshow(blended, x=x_axis, y=y_axis, color_continuous_scale="gray", binary_string=True, origin="upper")
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=True)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=True,
                      scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=900,
        width=1600,
        title_text="0° and 180° (flipped) overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    fig
    return (
        blended_with_no_flips,
        low_res_img_0,
        low_res_img_180_flipped,
        np,
        px,
        scale_factor,
        x_axis,
        y_axis,
    )


@app.cell
def _(low_res_img_0, low_res_img_180_flipped, np, px, scale_factor):
    from skimage.registration import phase_cross_correlation

    # Sub-pixel phase cross-correlation between 0° and horizontally-flipped 180°
    # upsample_factor=100 gives 1/100 pixel accuracy
    shift, error, _ = phase_cross_correlation(
        low_res_img_0.astype(np.float64),
        low_res_img_180_flipped.astype(np.float64),
        upsample_factor=100,
    )

    # COR = image_center + horizontal_shift / 2  (in low-res pixel coords)
    cor_low_res = low_res_img_0.shape[1] / 2 + shift[1] / 2
    # Scale back to original image coordinates
    cor_original = cor_low_res / scale_factor

    tilt_shift_low_res = shift[0]
    tilt_shift_original = tilt_shift_low_res / scale_factor

    # print(f"Horizontal shift (low-res px): {shift[1]:.3f}")
    # print(f"Vertical shift   (low-res px): {shift[0]:.3f}")
    # print(f"Center of rotation (original px): {cor_original:.2f}")
    # print(f"Tilt shift         (original px): {tilt_shift_original:.2f}")

    # Visual comparison
    from plotly.subplots import make_subplots

    diff = low_res_img_0 - low_res_img_180_flipped

    fig1 = make_subplots(rows=1, cols=3, subplot_titles=("0°", "180° flipped", "Difference"))
    fig1.add_trace(px.imshow(low_res_img_0, color_continuous_scale="gray", binary_string=True).data[0], row=1, col=1)
    fig1.add_trace(px.imshow(low_res_img_180_flipped, color_continuous_scale="gray", binary_string=True).data[0], row=1, col=2)
    fig1.add_trace(px.imshow(diff, color_continuous_scale="RdBu", binary_string=True).data[0], row=1, col=3)
    fig1.update_yaxes(scaleanchor="x", scaleratio=1, col=1)
    fig1.update_yaxes(scaleanchor="x2", scaleratio=1, col=2)
    fig1.update_yaxes(scaleanchor="x3", scaleratio=1, col=3)
    fig1.update_xaxes(matches="x")
    fig1.update_yaxes(matches="y")
    fig1.update_layout(height=400, width=1200, coloraxis_showscale=False)
    fig1
    return cor_original, tilt_shift_original


@app.cell
def _(
    blended_with_no_flips,
    cor_original,
    np,
    px,
    tilt_shift_original,
    x_axis,
    y_axis,
):
    import plotly.graph_objects as go

    img_height = y_axis[-1]
    img_width = x_axis[-1]

    tilt_angle_deg = np.degrees(np.arctan2(tilt_shift_original, img_height))

    fig2 = px.imshow(blended_with_no_flips, x=x_axis, y=y_axis, color_continuous_scale="gray", binary_string=True, origin="upper")
    # Vertical COR line
    fig2.add_vline(
        x=cor_original, line_color="red", line_width=2,
        annotation_text=f"COR = {cor_original:.1f} px",
        annotation_position="top left",
        annotation_font_color="red",
    )
    # Tilt line: starts at COR at the bottom, offset by tilt_shift at the top
    tilt_top_x = cor_original + tilt_shift_original
    fig2.add_trace(go.Scatter(
        x=[cor_original, tilt_top_x],
        y=[img_height, 0],
        mode="lines",
        line=dict(color="cyan", width=2, dash="dash"),
        name=f"Tilt = {tilt_angle_deg:.3f}°",
        showlegend=True,
    ))
    # Tilt angle annotation on the right side of the dashed line, at COR text level
    fig2.add_annotation(
        x=tilt_top_x + img_width * 0.01,
        y=0,
        text=f"Tilt = {tilt_angle_deg:.3f}°",
        showarrow=False,
        font=dict(color="blue", size=14),
        xanchor="left",
        yanchor="bottom",
        yref="y domain",
    )
    fig2.update_xaxes(showgrid=False, zeroline=False, showticklabels=True)
    fig2.update_yaxes(showgrid=False, zeroline=False, showticklabels=True,
                      scaleanchor="x", scaleratio=1)
    fig2.update_layout(
        height=900,
        width=1600,
        title_text="0° and 180° overlay with Center of Rotation",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    fig2
    return


if __name__ == "__main__":
    app.run()
