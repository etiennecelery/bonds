import base64
import datetime
import io
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
from plotly.io import write_image

from graficos_bonos_templates import Security

external_stylesheets = [
        "https://cdn.jsdelivr.net/npm/bulma@0.9/css/bulma.min.css",
        "https://fonts.googleapis.com/css?family=Poppins",
        ]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
# df = pd.read_excel('prueba.xlsx')

ranking_clasificaciones = {'AAA':100,'AA+':95,'AA':90,'AA-':85,'A+':80,'A':75,
    'A-':70,'BBB+':65,'BBB':60,'BBB-':55,'BB+':50,'BB':45,'BB-':40,'B+':35,
    'B':30,'B-':25,'CCC+':20,'CCC':15,'CCC-':10,'D+':3,'D':2,'D-':1}

seleccion = [
    ['Alimentos', 'Bebidas', 'Vitivinicola'],
    ['Comercio'],
    ['Sanitario'],
    ['Electrico', 'Energia'],
    ['Telecomunicaciones', 'Tecnologico'],
    ['Financiero'],
    ['Forestal', 'Industrial'],
    ['Holding'],
    ['Construccion', 'Minero'],
    ['Concesionaria', 'Inmobiliario', 'Infraestructura'],
    ['Salud', 'Educación', 'Transporte'],
    ['Factoring', 'Leasing', 'Securitizadora'],
    ['Entretenimiento']
]

layout = html.Div(
    className='hero-body',
    children=[
    html.Div(
        className='container box content',
        children=[
            html.H1('Guía de uso'),
            html.P('Primero se debe seleccionar un archivo en "Seleccionar Archivo". Este archivo debe estar en el mismo formato que el de prueba, que se puede descargar a continuación. El archivo puede tener más columnas que el de prueba pero siempre debe incluir las siguientes columnas con el mismo nombre: Emisor, Instrumento, Sector, Clasif., Spread, Durat .'),
            html.P('Actualización: Ahora se pueden utilizar archivos descargados directamente desde Risk America'),
            html.A('Ver archivo de prueba', href='https://github.com/etiennecelery/bonds/raw/master/prueba.xlsx'),
            html.Br(),
            html.P('A continuación se pueden seleccionar distintas opciones que modificarán los gráficos que se generarán automáticamente'),
        ]
    ),
    html.Div(
        className='container',
        children=dcc.Upload(
            id='upload-data',
            children=html.Div(
                className="content has-text-centered p-3",
                children=[
                    'Arrastra y Suelta o ',
                    html.A('Seleccionar Archivo')
                ],
                style={
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                },
            ),
            className='content',
            multiple=False
        )
    ),
    dcc.Store(id='dataframe', data=None),
    html.Div(className='container', children=[
        html.Div(
            id='dropdowns',
            className='box',
            children=[
                html.Div(
                    className='columns',
                    children=[
                        html.Div(
                            className='column',
                            children=dcc.Dropdown(
                                multi=True,
                                value=None,
                                id='dropdown-emisor',
                                placeholder="Eliminar emisor",
                                className='column'
                            ),
                        ),
                        html.Div(
                            className='column',
                            children=dcc.Dropdown(
                                multi=True,
                                value=None,
                                id='dropdown-clasif',
                                placeholder="Eliminar clasificación",
                                className='column'
                            ),
                        )
                    ]
                )

            ]
            ),
        html.Div(
            className='box',
            children=[
                html.Div(
                    className='content has-text-centered',
                    children=html.H1('Anotaciones'),
                ),
                dcc.RadioItems(
                    id='anotaciones',
                    labelClassName='level-item',
                    className='level',
                    options=[
                        {'label': x, 'value': x}
                        for x in ['Instrumento', 'Emisor', 'Desactivado']
                    ],
                    value='Instrumento',
                ),
                html.Div(
                    className='content has-text-centered',
                    children=html.H1('Orientación'),
                ),
                dcc.RadioItems(
                    id='orientacion',
                    labelClassName='level-item',
                    className='level',
                    options=[{'label': x, 'value': x} for x in [90, 45, 0]],
                    value=90,
                ),
            ]
        ),
        html.Div(
            className='box',
            children=[
                html.Div(
                    className='content has-text-centered',
                    children=html.H1('Leyenda'),
                ),
                dcc.RadioItems(
                    id='leyenda',
                    labelClassName='level-item',
                    className='level',
                    options=[
                        {'label': x, 'value': x}
                        for x in ['Activada', 'Desactivada']
                    ],
                    value='Activada',
                ),
            ]
        ),
        dcc.Loading(
            children=html.Div(id='graphs', className='container'),
            color='#8dec6e',
            className='container',
        ),
    ])
])

app.layout = layout

@app.callback([Output('dataframe', 'data'),
               Output('dropdown-emisor', 'options'),
               Output('dropdown-clasif', 'options'),
               Output('dropdowns', 'style')],
              [Input('upload-data', 'contents')])
def update_output(data):
    if data is None:
        return (None, [{'label': 0, 'value': 0}],
                [{'label': 0, 'value': 0}], {'display': 'None'})

    content_type, content_string = data.split(',')
    decoded = base64.b64decode(content_string)

    df = pd.read_excel(io.BytesIO(decoded))
    df = df.rename(columns={'Dur': 'Durat', 'Riesgo': 'Clasif.', 'Nemo': 'Instrumento'})
    df = df[~df.Instrumento.isna()]

    def create_dd_options(col):
        options = [{'label': x, 'value': x}
                   for x in df[col].sort_values().unique()]
        return options

    industria = create_dd_options('Emisor')
    clasif = create_dd_options('Clasif.')
    df['ranking'] = df['Clasif.'].map(ranking_clasificaciones)
    df = df.sort_values(by='ranking', ascending=False)

    return (df.to_json(date_format='iso', orient='split'),
            industria, clasif, {})

@app.callback(Output('graphs', 'children'),
              [Input('dataframe', 'data'),
               Input('anotaciones', 'value'),
               Input('orientacion', 'value'),
               Input('leyenda', 'value'),
               Input('dropdown-emisor', 'value'),
               Input('dropdown-clasif', 'value')])
def graficos_auto(data, anotaciones, orientacion, leyenda, emisor_dd, clasificacion_dd):
    if data is None:
        return None

    df = pd.read_json(data, orient='split')

    if emisor_dd is not None:
        df = df[~df['Emisor'].isin(emisor_dd)].copy()

    if clasificacion_dd is not None:
        df = df[~df['Clasif.'].isin(clasificacion_dd)].copy()

    figures = list()
    markers = [
        'circle', 'square', 'diamond', 'cross', 'x', 'triangle-up',
        'triangle-down', 'triangle-left', 'triangle-right', 'triangle-ne',
        'triangle-se']

    for sel in seleccion:
        traces = list()
        for ind, marker in zip(sel, markers):
            for x in df[df.Sector==ind].Emisor.unique():
                trace = go.Scatter(
                    x=df[df.Emisor == x].Durat,
                    y=df[df.Emisor == x].Spread,
                    mode='markers',
                    marker_size=15,
                    marker_symbol=marker,
                    text=f"{x} / {df[df.Emisor==x]['Clasif.'].values[0]}",
                    name=f"{x} / {df[df.Emisor==x]['Clasif.'].values[0]}",
                )
                traces.append(trace)

        if len(sel) == 0:
            title = f'<b>Spread Bonos Sector {sel[0]}<b>'
        elif len(sel) > 0:
            title = f'<b>Spread Bonos Sectores {" - ".join(sel)}<b>'

        if anotaciones == 'Emisor' or anotaciones == 'Instrumento':
            annotations = [
                dict(
                    x=df[df[anotaciones] == x].Durat.values[-1],
                    y=df[df[anotaciones] == x].Spread.values[-1],
                    xref="x",
                    yref="y",
                    text=x,
                    showarrow=True,
                    arrowhead=0,
                    ax=0,
                    ay=-60,
                    textangle=-1*orientacion,
                )
                for x in df[df.Sector.isin(sel)][anotaciones].unique()
            ]
        else:
            annotations = None

        layout = go.Layout(
            template=Security,
            yaxis_zeroline=False,
            yaxis_title="",
            xaxis_title="",
            xaxis_zeroline=False,
            title=title,
            showlegend=(True if leyenda == 'Activada' else False),
            annotations=annotations,
            legend=dict(
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=-0.35
            ),
        )
        fig = go.Figure(traces, layout)
        fig.add_annotation(
            x=0.008,
            y=0.5,
            xref="paper",
            yref="paper",
            text='Spread',
            font_size=16,
            showarrow=False,
            textangle=-90,
        )
        fig.add_annotation(
            x=0.5,
            y=0.007,
            xref="paper",
            yref="paper",
            text='Duración',
            font_size=16,
            showarrow=False,
            textangle=0,
        )
        figures.append(fig)

    for clasif in ['AA', 'A']:
        clasif_todas = [clasif, clasif+'-', clasif+'+']
        if len(df[df['Clasif.'].isin(clasif_todas)]) > 0:
            traces = [
                go.Scatter(
                    x=df[df.Emisor == x].Durat,
                    y=df[df.Emisor == x].Spread,
                    mode='markers',
                    marker_size=15,
                    text=f"{x} / {df[df.Emisor == x]['Clasif.'].values[0]}",
                    name=f"{x} / {df[df.Emisor == x]['Clasif.'].values[0]}",
                )
                for x in df[df['Clasif.'].isin(clasif_todas)].Emisor.unique()
            ]
            annotations = [
                dict(
                    x=df[df[anotaciones] == x].Durat.values[-1],
                    y=df[df[anotaciones] == x].Spread.values[-1],
                    xref="x",
                    yref="y",
                    text=x,
                    showarrow=True,
                    arrowhead=0,
                    ax=0,
                    ay=-60,
                    textangle=-1*orientacion,
                )
                for x in df[df['Clasif.'].isin(clasif_todas)][anotaciones].unique()
            ]
            layout = go.Layout(
                template=Security,
                yaxis_title='',
                xaxis_title='',
                yaxis_zeroline=False,
                xaxis_zeroline=False,
                title=f"<b>Spread Bonos {clasif}<b>",
                showlegend=(True if leyenda == 'Activada' else False),
                annotations=annotations,
                legend=dict(
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=-0.35
                ),
            )
            fig = go.Figure(traces, layout)
            fig.add_annotation(
                x=0.008,
                y=0.5,
                xref="paper",
                yref="paper",
                text='Spread',
                font_size=16,
                showarrow=False,
                textangle=-90,
            )
            fig.add_annotation(
                x=0.5,
                y=0.007,
                xref="paper",
                yref="paper",
                text='Duración',
                font_size=16,
                showarrow=False,
                textangle=0,
            )
            figures.append(fig)

    for clasif in df['Clasif.'].unique():
        traces = [
            go.Scatter(
                x=df[df.Emisor == x].Durat,
                y=df[df.Emisor == x].Spread,
                mode='markers',
                marker_size=15,
                text=f"{x} / {df[df.Emisor == x]['Clasif.'].values[0]}",
                name=f"{x} / {df[df.Emisor == x]['Clasif.'].values[0]}",
            )
            for x in df[df['Clasif.'] == clasif].Emisor.unique()
        ]
        annotations = [
            dict(
                x=df[df[anotaciones] == x].Durat.values[-1],
                y=df[df[anotaciones] == x].Spread.values[-1],
                xref="x",
                yref="y",
                text=x,
                showarrow=True,
                arrowhead=0,
                ax=0,
                ay=-60,
                textangle=-1*orientacion,
            )
            for x in df[df['Clasif.'] == clasif][anotaciones].unique()
        ]
        layout = go.Layout(
            template=Security,
            yaxis_title='',
            xaxis_title='',
            yaxis_zeroline=False,
            xaxis_zeroline=False,
            title=f"<b>Spread Bonos {clasif}<b>",
            showlegend=(True if leyenda == 'Activada' else False),
            annotations=annotations,
            legend=dict(
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=-0.35
            ),
        )
        fig = go.Figure(traces, layout)
        fig.add_annotation(
            x=0.008,
            y=0.5,
            xref="paper",
            yref="paper",
            text='Spread',
            font_size=16,
            showarrow=False,
            textangle=-90,
        )
        fig.add_annotation(
            x=0.5,
            y=0.007,
            xref="paper",
            yref="paper",
            text='Duración',
            font_size=16,
            showarrow=False,
            textangle=0,
        )
        figures.append(fig)

    graphs = [
        html.Div(
            className='container has-text-right',
            children=[
                dcc.Graph(
                    figure=fig,
                    id=f'graph-{i}',
                    config={'displayModeBar': False,
                            'editable': True},
                ),
                html.A(
                    download=f'grafico_{i}.jpg',
                    href=None,
                    id=f'download-href-{i}',
                    children=[html.Button("Descargar Gráfico", className='button')],
                )
            ]
        )
        for i, fig in enumerate(figures)
    ]
    return graphs


for i in range(22):
    @app.callback(
        Output(f'download-href-{i}', 'href'),
        [Input(f'graph-{i}', 'relayoutData')],
         [State(f'graph-{i}', 'figure'),
          State(f'graph-{i}', 'id')]
    )
    def download(relayout_data, fig, id):
        if fig:
            fmt = "jpg"
            filename = "application/downloads/%s.%s" % (id, fmt)
            write_image(fig, filename, format=fmt, engine='kaleido', width=1100, height=500, scale=5)
            return f'/download/{id}.jpg'
        else:
            return None

if __name__ == '__main__':
    app.run_server(debug=True)
