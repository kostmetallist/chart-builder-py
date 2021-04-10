import numpy as np
import plotly.graph_objects as go

DEFAULT_COLOR = '#ED823D'


def compose_scatter_plot(x_values, y_values):

    assert x_values.size == y_values.size
    size = x_values.size

    return go.Figure(data=go.Scattergl(
        x = x_values,
        y = y_values,
        mode='markers',
        marker={
            'color': DEFAULT_COLOR,
            'colorscale': 'Viridis',
            'line_width': 0,
            'size': 2,
        }
    ))
