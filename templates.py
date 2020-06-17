import plotly as py
import plotly.graph_objs as go

colors = {
    'blue': '#909cba',
    'red': '#e55a5a',
    'green': '#b1d366',
    'orange': '#f1b15f',
    'pastel blue' : '#264e70',
    'pastel light blue' : '#71a0a5',
    'pastel grey' : '#808b97',
    'pastel purple' : '#77628c',
    'pastel green' : '#acc6aa',
    'pastel pink' : '#ccadb8',
    'pastel orange' : '#ff9067',
    'black': '#211915',
}


security_layout = go.Layout(
    font=dict(
        family='Poppins Semibold',
        size=14,
        color=colors['black'],
    ),
    plot_bgcolor='white',
    separators = ',.',
    xaxis=dict(
        showline=True,
        tickangle=270,
        linewidth=2,
        linecolor=colors['black'],
        tickcolor=colors['black'],
        # tickmode='linear',
        ticks='outside',
        showgrid=False,
        tickfont=dict(
            family = 'Poppins',
            color = colors['black']
        ),
    ),
    yaxis=dict(
        showgrid=False,
        ticks='outside',
        showline=True,
        linewidth=2,
        linecolor=colors['black'],
    ),
    yaxis2=dict(
        showgrid=False,
        showline=True,
        ticks="outside",
        color=('rgb(144, 156, 186)'),
        titlefont=dict(
            color=('rgb(144, 156, 186)'),
        ),
        tickfont=dict(
            color=('rgb(144, 156, 186)'),
        ),
        overlaying='y',
        side='right',
        tickformat="",
        ),
    legend=dict(
        font=dict(family='Poppins'),
    ),
    autosize=True,

)

Security = go.layout.Template(
    layout=security_layout
)
Security.data.scatter = [
    go.Scatter(
        line_width=4,
        line_color=color,
        marker_color=color,
    )
    for color in list(colors.values())
]

Security.data.bar = [
    go.Bar(marker=dict(color=color))
    for color in list(colors.values())
]
