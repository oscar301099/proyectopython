import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Inicializa la app
app = Dash(__name__)
server = app.server

# Función para obtener y procesar los datos
def get_datos():
    try:
        # Ventas
        query_ventas = """
        query {
          ventaBoletos {
            precio
            fechaVenta
          }
        }"""

        res_ventas = requests.post("http://localhost:3000/api/graphql", json={"query": query_ventas})

        if res_ventas.status_code == 200:
            ventas_data = res_ventas.json()
            if "data" in ventas_data and "ventaBoletos" in ventas_data["data"]:
                df_ventas = pd.DataFrame(ventas_data["data"]["ventaBoletos"])
                if not df_ventas.empty:
                    df_ventas["fechaVenta"] = pd.to_datetime(df_ventas["fechaVenta"])  # Sin .dt.date
                    df_ventas = df_ventas.rename(columns={"precio": "Ganancia", "fechaVenta": "Fecha"})
                    df_ventas.set_index("Fecha", inplace=True)  # Índice de tipo datetime

            else:
                df_ventas = pd.DataFrame()
        else:
            df_ventas = pd.DataFrame()

        # Gastos
        query_gastos = """
        query {
          gastos {
            monto
            fecha
          }
        }"""

        res_gastos = requests.post("http://localhost:3000/api/graphql", json={"query": query_gastos})

        if res_gastos.status_code == 200:
            gastos_data = res_gastos.json()
            if "data" in gastos_data and "gastos" in gastos_data["data"]:
                df_gastos = pd.DataFrame(gastos_data["data"]["gastos"])
                if not df_gastos.empty:
                    df_gastos["fecha"] = pd.to_datetime(df_gastos["fecha"]).dt.date
                    df_gastos = df_gastos.rename(columns={"monto": "Gasto", "fecha": "Fecha"})
            else:
                df_gastos = pd.DataFrame()
        else:
            df_gastos = pd.DataFrame()

        return df_ventas, df_gastos

    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Obtener datos iniciales
df_ganancias, df_gastos = get_datos()

# Layout
app.layout = html.Div([
    html.H1("Dashboard de Ganancias y Gastos", style={"textAlign": "center"}),
    
    html.Div([
        html.Button("Actualizar Datos", id="refresh-button", n_clicks=0),
        html.Div(id="status-message", style={"margin": "10px", "color": "blue"})
    ]),
    
    # Controles adicionales
    html.Div([
        html.Label("Tipo de visualización:"),
        dcc.Dropdown(
            id="chart-type",
            options=[
                {"label": "Gráficos separados (escalas independientes)", "value": "separate"},
                {"label": "Gráficos combinados (misma escala)", "value": "combined"},
                {"label": "Datos agregados por día", "value": "daily"},
                {"label": "Datos agregados por mes", "value": "monthly"}
            ],
            value="separate",
            style={"margin": "10px"}
        )
    ]),
    
    dcc.DatePickerRange(
        id="date-range",
        start_date=datetime(2024, 1, 1).date(),
        end_date=datetime.now().date(),
        display_format="YYYY-MM-DD"
    ) if not df_ganancias.empty or not df_gastos.empty else html.Div("No hay datos para mostrar fechas"),
    
    html.Div(id="charts-container"),
    
    # Sección de Predicciones
    html.Hr(),
    html.H2("📈 Predicciones de Ganancias y Gastos", style={"textAlign": "center", "margin": "20px"}),
    
    html.Div([
        html.Div([
            html.Label("Tipo de Modelo:"),
            dcc.Dropdown(
                id="model-type",
                options=[
                    {"label": "Regresión Lineal Simple", "value": "linear"},
                    {"label": "Regresión Polinomial (grado 2)", "value": "poly2"},
                    {"label": "Regresión Polinomial (grado 3)", "value": "poly3"},
                    {"label": "Promedio Móvil", "value": "moving_avg"}
                ],
                value="linear",
                style={"width": "100%"}
            )
        ], style={"width": "30%", "display": "inline-block", "margin": "0 10px"}),
        
        html.Div([
            html.Label("Días a Predecir:"),
            dcc.Input(
                id="prediction-days",
                type="number",
                value=30,
                min=1,
                max=365,
                style={"width": "100%"}
            )
        ], style={"width": "30%", "display": "inline-block", "margin": "0 10px"}),
        
        html.Div([
            html.Label("Período de Agregación:"),
            dcc.Dropdown(
                id="prediction-period",
                options=[
                    {"label": "Diario", "value": "D"},
                    {"label": "Semanal", "value": "W"},
                    {"label": "Mensual", "value": "M"}
                ],
                value="D",
                style={"width": "100%"}
            )
        ], style={"width": "30%", "display": "inline-block", "margin": "0 10px"})
    ], style={"margin": "20px 0"}),
    
    html.Div(id="prediction-container"),
    
    # Métricas de predicción
    html.Div(id="prediction-metrics", style={"margin": "20px 0"}),
    
    # Información de debug
    html.Div([
        html.H3("Información de Debug:"),
        html.Div(id="debug-info")
    ], style={"margin-top": "20px", "padding": "10px", "border": "1px solid #ccc"})
])

# Callback para actualizar datos
@app.callback(
    Output("status-message", "children"),
    Input("refresh-button", "n_clicks")
)
def refresh_data(n_clicks):
    if n_clicks > 0:
        global df_ganancias, df_gastos
        df_ganancias, df_gastos = get_datos()
        return f"Datos actualizados. Ganancias: {len(df_ganancias)}, Gastos: {len(df_gastos)}"
    return f"Ganancias: {len(df_ganancias)}, Gastos: {len(df_gastos)}"

# Callback principal para las gráficas
@app.callback(
    [Output("charts-container", "children"),
     Output("debug-info", "children")],
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("chart-type", "value"),
     Input("refresh-button", "n_clicks")]
)
def actualizar_graficos(start_date, end_date, chart_type, n_clicks):
    debug_info = []
    
    try:
        # Filtrar por rango de fechas
        if not df_ganancias.empty and start_date and end_date:
            df_g = df_ganancias[
                (df_ganancias["Fecha"] >= pd.to_datetime(start_date).date()) &
                (df_ganancias["Fecha"] <= pd.to_datetime(end_date).date())
            ]
        else:
            df_g = df_ganancias
            
        if not df_gastos.empty and start_date and end_date:
            df_x = df_gastos[
                (df_gastos["Fecha"] >= pd.to_datetime(start_date).date()) &
                (df_gastos["Fecha"] <= pd.to_datetime(end_date).date())
            ]
        else:
            df_x = df_gastos
        
        debug_info.append(f"Datos filtrados - Ganancias: {len(df_g)}, Gastos: {len(df_x)}")
        
        if not df_g.empty:
            debug_info.append(f"Rango ganancias: {df_g['Ganancia'].min():.2f} - {df_g['Ganancia'].max():.2f}")
        if not df_x.empty:
            debug_info.append(f"Rango gastos: {df_x['Gasto'].min():.2f} - {df_x['Gasto'].max():.2f}")
        
        # Crear gráficas según el tipo seleccionado
        if chart_type == "separate":
            charts = crear_graficos_separados(df_g, df_x, debug_info)
        elif chart_type == "combined":
            charts = crear_grafico_combinado(df_g, df_x, debug_info)
        elif chart_type == "daily":
            charts = crear_graficos_agregados(df_g, df_x, "D", debug_info)
        else:  # monthly
            charts = crear_graficos_agregados(df_g, df_x, "M", debug_info)
        
        return charts, html.Div([html.P(info) for info in debug_info])
        
    except Exception as e:
        debug_info.append(f"Error: {str(e)}")
        return html.Div("Error al crear gráficas"), html.Div([html.P(info) for info in debug_info])

# Callback para predicciones
@app.callback(
    [Output("prediction-container", "children"),
     Output("prediction-metrics", "children")],
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("model-type", "value"),
     Input("prediction-days", "value"),
     Input("prediction-period", "value"),
     Input("refresh-button", "n_clicks")]
)
def predecir_datos(start_date, end_date, model_type, prediction_days, prediction_period, n_clicks):
    try:
        # Filtrar datos según fecha
        df_g = df_ganancias.copy()
        df_x = df_gastos.copy()
        if not df_g.empty and start_date and end_date:
            df_g = df_g[(df_g["Fecha"] >= pd.to_datetime(start_date).date()) & (df_g["Fecha"] <= pd.to_datetime(end_date).date())]
        if not df_x.empty and start_date and end_date:
            df_x = df_x[(df_x["Fecha"] >= pd.to_datetime(start_date).date()) & (df_x["Fecha"] <= pd.to_datetime(end_date).date())]
        
        if df_g.empty or df_x.empty:
            return html.Div("No hay datos suficientes para hacer predicciones."), ""
        
        # Agregar por período
        df_g_agg = df_g.groupby(pd.Grouper(key="Fecha", freq=prediction_period)).sum().reset_index()
        df_x_agg = df_x.groupby(pd.Grouper(key="Fecha", freq=prediction_period)).sum().reset_index()
        
        # Ajustar fechas para modelos
        df_g_agg = df_g_agg.dropna()
        df_x_agg = df_x_agg.dropna()
        
        # Función para predecir
        def modelo_prediccion(df, col, modelo, dias):
            df = df.reset_index(drop=True)
            df["Dia"] = np.arange(len(df))
            X = df["Dia"].values.reshape(-1, 1)
            y = df[col].values
            
            if modelo == "linear":
                reg = LinearRegression()
                reg.fit(X, y)
                X_pred = np.arange(len(df), len(df) + dias).reshape(-1, 1)
                y_pred = reg.predict(X_pred)
                r2 = r2_score(y, reg.predict(X))
                mae = mean_absolute_error(y, reg.predict(X))
                return y_pred, r2, mae
            
            elif modelo.startswith("poly"):
                grado = int(modelo[-1])
                poly = PolynomialFeatures(degree=grado)
                X_poly = poly.fit_transform(X)
                reg = LinearRegression()
                reg.fit(X_poly, y)
                X_pred = np.arange(len(df), len(df) + dias).reshape(-1, 1)
                X_pred_poly = poly.transform(X_pred)
                y_pred = reg.predict(X_pred_poly)
                r2 = r2_score(y, reg.predict(X_poly))
                mae = mean_absolute_error(y, reg.predict(X_poly))
                return y_pred, r2, mae
            
            elif modelo == "moving_avg":
                window = min(5, len(y))
                y_pred = np.full(dias, np.mean(y[-window:]))
                # No aplica métricas para moving avg
                return y_pred, None, None
            
            else:
                return np.zeros(dias), None, None
        
        y_pred_ganancias, r2_g, mae_g = modelo_prediccion(df_g_agg, "Ganancia", model_type, prediction_days)
        y_pred_gastos, r2_x, mae_x = modelo_prediccion(df_x_agg, "Gasto", model_type, prediction_days)
        
        # Crear DataFrame para predicciones
        fechas_pred = pd.date_range(start=df_g_agg["Fecha"].max() + pd.Timedelta(days=1), periods=prediction_days, freq=prediction_period)
        df_pred_ganancias = pd.DataFrame({"Fecha": fechas_pred, "Ganancia Predicha": y_pred_ganancias})
        df_pred_gastos = pd.DataFrame({"Fecha": fechas_pred, "Gasto Predicho": y_pred_gastos})
        
        # Gráfica combinada de predicción
        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(x=df_g_agg["Fecha"], y=df_g_agg["Ganancia"], mode="lines+markers", name="Ganancia Real"))
        fig_pred.add_trace(go.Scatter(x=df_pred_ganancias["Fecha"], y=df_pred_ganancias["Ganancia Predicha"], mode="lines+markers", name="Ganancia Predicha"))
        fig_pred.add_trace(go.Scatter(x=df_x_agg["Fecha"], y=df_x_agg["Gasto"], mode="lines+markers", name="Gasto Real"))
        fig_pred.add_trace(go.Scatter(x=df_pred_gastos["Fecha"], y=df_pred_gastos["Gasto Predicho"], mode="lines+markers", name="Gasto Predicho"))
        fig_pred.update_layout(title="Predicción de Ganancias y Gastos", xaxis_title="Fecha", yaxis_title="Monto", height=500)
        
        # Métricas de desempeño
        metrics_text = []
        if r2_g is not None and mae_g is not None:
            metrics_text.append(f"Ganancias - R²: {r2_g:.3f}, MAE: {mae_g:.2f}")
        if r2_x is not None and mae_x is not None:
            metrics_text.append(f"Gastos - R²: {r2_x:.3f}, MAE: {mae_x:.2f}")
        if model_type == "moving_avg":
            metrics_text.append("Promedio móvil: métricas no aplicables.")
        
        metrics_div = html.Div([html.P(text) for text in metrics_text])
        
        return dcc.Graph(figure=fig_pred), metrics_div
    
    except Exception as e:
        return html.Div(f"Error en predicción: {e}"), ""

# Funciones auxiliares para gráficos

def crear_graficos_separados(df_ganancias, df_gastos, debug_info):
    children = []
    if not df_ganancias.empty:
        fig_g = px.line(df_ganancias, x="Fecha", y="Ganancia", title="Ganancias")
        children.append(dcc.Graph(figure=fig_g))
    else:
        children.append(html.Div("No hay datos de ganancias."))
    
    if not df_gastos.empty:
        fig_x = px.line(df_gastos, x="Fecha", y="Gasto", title="Gastos")
        children.append(dcc.Graph(figure=fig_x))
    else:
        children.append(html.Div("No hay datos de gastos."))
    
    return children

def crear_grafico_combinado(df_ganancias, df_gastos, debug_info):
    fig = go.Figure()
    if not df_ganancias.empty:
        fig.add_trace(go.Scatter(x=df_ganancias["Fecha"], y=df_ganancias["Ganancia"], mode="lines+markers", name="Ganancia"))
    if not df_gastos.empty:
        fig.add_trace(go.Scatter(x=df_gastos["Fecha"], y=df_gastos["Gasto"], mode="lines+markers", name="Gasto"))
    
    fig.update_layout(title="Ganancias y Gastos Combinados", xaxis_title="Fecha", yaxis_title="Monto")
    return [dcc.Graph(figure=fig)]

def crear_graficos_agregados(df_ganancias, df_gastos, freq, debug_info):
    children = []
    if not df_ganancias.empty:
        df_g = df_ganancias.groupby(pd.Grouper(key="Fecha", freq=freq)).sum().reset_index()
        fig_g = px.line(df_g, x="Fecha", y="Ganancia", title=f"Ganancias Agregadas ({freq})")
        children.append(dcc.Graph(figure=fig_g))
    else:
        children.append(html.Div("No hay datos de ganancias para agregación."))
    
    if not df_gastos.empty:
        df_x = df_gastos.groupby(pd.Grouper(key="Fecha", freq=freq)).sum().reset_index()
        fig_x = px.line(df_x, x="Fecha", y="Gasto", title=f"Gastos Agregados ({freq})")
        children.append(dcc.Graph(figure=fig_x))
    else:
        children.append(html.Div("No hay datos de gastos para agregación."))
    
    return children

# Ejecutar la app
if __name__ == "__main__":
    app.run(debug=True)

