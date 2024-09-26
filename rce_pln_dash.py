import webbrowser
from datetime import date
from threading import Timer

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
from dash import Dash, html, dcc, callback, Output, Input

port = 8050
url = lambda business_date: f'https://api.raporty.pse.pl/api/rce-pln?$filter=business_date eq \'{business_date}\''
Y_AXIS_MIN_VAL = -500
Y_AXIS_MAX_VAL = 1500


def get_prices(business_date: str = '2024-09-26'):
    response = requests.get(url(business_date)).json()
    df = pd.DataFrame.from_dict(response.get('value'))
    if df.empty:
        return pd.DataFrame()
    df = df[['udtczas_oreb', 'rce_pln']]
    df = df[::4]  # every 4th row
    df['udtczas_oreb'] = df['udtczas_oreb'].str.split(' - ').str[0]  # from '00:00 - 00:15' get '00:00'
    df = df.rename(columns={'udtczas_oreb': 'start_hour', 'rce_pln': 'price'})
    return df


def prepare_prices_chart(business_date):
    prices_df = get_prices(business_date)
    if prices_df.empty:
        fig = go.Figure()
        fig.update_layout(
            {
                "yaxis": {
                    'range': (Y_AXIS_MIN_VAL, Y_AXIS_MAX_VAL)
                },
                "annotations": [
                    {
                        "text": "No data for selected date",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 28
                        }
                    }
                ]
            }
        )
        return fig
    else:
        fig = px.line(prices_df, x="start_hour", y="price", title="RCE_PLN", markers=True)
        fig.update_layout(
            {
                "yaxis": {
                    'range': (Y_AXIS_MIN_VAL, Y_AXIS_MAX_VAL)
                }
            }
        )
        return fig


@callback(
    Output('price-chart', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_output(date_value):
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%Y-%m-%d')
        print(f'Preparing chart for {date_string}.')
        output_fig = prepare_prices_chart(date_string)
        return output_fig


def open_browser():
    webbrowser.open_new(f"http://localhost:{port}")


app = Dash(__name__)
today = date.today()
app.layout = html.Div([
    dcc.DatePickerSingle(
        id='my-date-picker-single',
        date=date(today.year, today.month, today.day)
    ),
    dcc.Loading(
        [dcc.Graph(id='price-chart')],
        overlay_style={"visibility": "visible", "opacity": .5, "backgroundColor": "white"},
    )
])

if __name__ == '__main__':
    Timer(1, open_browser).start();
    app.run_server(debug=True, port=port)
