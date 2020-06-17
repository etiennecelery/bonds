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
from templates import Security

from dash.exceptions import PreventUpdate



external_stylesheets = [
 "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# df = pd.read_excel('Book1.xlsx')

seleccion = [
    ['Alimentos','Bebidas','Vitivinicola'],
    ['Comercio'],
    ['Sanitario'],
    ['Electrico','Energia'],
    ['Tecnologico','Telecomunicaciones'],
    ['Financiero'],
    ['Forestal','Industrial','Salud'],
    ['Holding'],
    ['Construccion','Minero'],
    ['Concesionaria','Inmobiliario'],
    ['Banco']
]

app.layout = html.Div([
    html.Div(
        className='container box content is-large',
        children=[
            html.H1('Cómo funciona'),
            html.P('Primero se debe seleccionar un archivo en "Seleccionar Archivo". Este archivo debe estar en el mismo formato que el de prueba, que se puede descargar a continuación.'),
            html.A('Ver archivo de prueba', href='https://drive.google.com/file/d/1kPws57K4IlDbYf5XSkuYjeEJtFQWDbNw/view?usp=sharing'),
            html.Br(),
            html.P('A continuación se pueden seleccionar distintas opciones que modificarán los gráficos que se generarán automáticamente'),
        ]
    ),
    html.Div(
        className='hero',
        children=dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Arrastra y Suelta o ',
                html.A('Seleccionar Archivo')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin-top': '10px',
                'margin-bottom': '10px'
            },
            className='container',
            multiple=False
        )
    ),
    dcc.Store(id='dataframe', data=None),
    html.Div(className='hero', children=[
        html.Div(
            id='dropdowns',
            className='container box',
            children=[
                html.Div(
                    className='columns',
                    children = [
                        html.Div(
                            className='column',
                            children=dcc.Dropdown(
                                multi=True,
                                value=None,
                                id='dropdown-emisor',
                                placeholder=f"Eliminar emisor",
                                className='column'
                            ),
                        ),
                        html.Div(
                            className='column',
                            children=dcc.Dropdown(
                                multi=True,
                                value=None,
                                id='dropdown-clasif',
                                placeholder=f"Eliminar clasificación",
                                className='column'
                            ),
                        )
                    ]
                )

            ]
            ),
        html.Div(
            className='container box',
            children=[
                html.Div(
                    className='content has-text-centered',
                    children=html.H1('Anotaciones'),
                ),
                dcc.RadioItems(
                    id='anotaciones',
                    className='level',
                    labelClassName='level-item',
                    options=[
                        {'label':x, 'value':x}
                        for x in ['Emisor','Instrumento','Desactivado']
                    ],
                    value='Emisor',
                ),]
        ),
        html.Div(
            className='container box',
            children=[
                html.Div(
                    className='content has-text-centered',
                    children=html.H1('Leyenda'),
                ),
                dcc.RadioItems(
                    id='leyenda',
                    className='level',
                    labelClassName='level-item',
                    options=[
                        {'label':x, 'value':x}
                        for x in ['Activada','Desactivada']
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

@app.callback([Output('dataframe', 'data'),
               Output('dropdown-emisor','options'),
               Output('dropdown-clasif','options'),
               Output('dropdowns','style')],
              [Input('upload-data', 'contents')])
def update_output(data):
    if data is None:
        return None, [{'label':0, 'value':0}], [{'label':0, 'value':0}], {'display':'None'}

    content_type, content_string = data.split(',')
    decoded = base64.b64decode(content_string)

    df = pd.read_excel(io.BytesIO(decoded))
    df = df[~df.Instrumento.isna()]

    def create_dd_options(col):
        options = [{'label':x, 'value':x}
            for x in df[col].sort_values().unique().tolist()]
        return options

    industria = create_dd_options('Emisor')
    clasif = create_dd_options('Clasif.')

    return (df.to_json(date_format='iso', orient='split'),
            industria, clasif, {})


@app.callback(Output('graphs','children'),
              [Input('dataframe','data'),
               Input('anotaciones','value'),
               Input('leyenda','value'),
               Input('dropdown-emisor','value'),
               Input('dropdown-clasif','value')])
def graficos_auto(data, anotaciones, leyenda, emisor_dd, clasificacion_dd):
    if data is None:
        return None

    df = pd.read_json(data, orient='split')

    if emisor_dd is not None:
        df = df[~df['Emisor'].isin(emisor_dd)].copy()

    if clasificacion_dd is not None:
        df = df[~df['Clasif.'].isin(clasificacion_dd)].copy()

    figures = list()
    for sel in seleccion:
        traces = [
            go.Scatter(
                x=df[df.Emisor==x].Durat,
                y=df[df.Emisor==x].Spread,
                mode='markers',
                marker_size=20,
                text=f"{x} / {df[df.Emisor==x]['Clasif.'].values[0]}",
                name=f"{x} / {df[df.Emisor==x]['Clasif.'].values[0]}",
            )
            for x in df[df.Sector.isin(sel)].Emisor.unique()
        ]
        if len(sel) == 0:
            title = f'Spread Bonos Sector {sel[0]}'
        else:
            title = f'Spread Bonos Sectores {" - ".join(sel)}'

        if anotaciones == 'Emisor' or anotaciones == 'Instrumento':
            annotations = [
                dict(
                    x=df[df[anotaciones]==x].Durat.values[0],
                    y=df[df[anotaciones]==x].Spread.values[0],
                    xref="x",
                    yref="y",
                    text=f"{x} / {df[df[anotaciones]==x]['Clasif.'].values[0]}",
                    showarrow=True,
                    arrowhead=0,
                    ax=0,
                    ay=-40
                )
                for x in df[df.Sector.isin(sel)][anotaciones].unique()
            ]
        else:
            annotations = None

        layout = go.Layout(
            template=Security,
            yaxis_title='Spread',
            xaxis_title='Duración',
            yaxis_zeroline=False,
            xaxis_zeroline=False,
            title=title,
            showlegend=(True if leyenda=='Activada' else False),
            annotations=annotations
        )
        fig = go.Figure(traces, layout)

        figures.append(fig)

    graphs = [
        dcc.Graph(
            figure=fig,
            id=f'graph_{i}',
            config={'displayModeBar': False,
                    'editable': True},
        )
        for i, fig in enumerate(figures)]

    return graphs

if __name__ == '__main__':
    app.run_server(debug=False, port=8059, host='0.0.0.0')
