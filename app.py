from flask import Flask, render_template, jsonify, request
import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# Función para obtener datos (la misma que tenías)
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
                    df_ventas["fechaVenta"] = pd.to_datetime(df_ventas["fechaVenta"])
                    df_ventas = df_ventas.rename(columns={"precio": "Ganancia", "fechaVenta": "Fecha"})
                    df_ventas.set_index("Fecha", inplace=True)
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

# Función para procesar datos para Chart.js
def process_data_for_chart(df_g, df_x, chart_type, start_date=None, end_date=None):
    # Filtrar por fechas si se especifican
    if start_date and end_date:
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        
        if not df_g.empty:
            df_g = df_g[(df_g.index.date >= start_date) & (df_g.index.date <= end_date)]
        if not df_x.empty:
            df_x = df_x[(df_x['Fecha'] >= start_date) & (df_x['Fecha'] <= end_date)]
    
    # Procesar según el tipo de gráfico
    if chart_type == 'daily':
        if not df_g.empty:
            df_g = df_g.groupby(df_g.index.date).sum()
        if not df_x.empty:
            df_x = df_x.groupby('Fecha').sum()
    elif chart_type == 'monthly':
        if not df_g.empty:
            df_g = df_g.groupby(pd.Grouper(freq='M')).sum()
            df_g.index = df_g.index.strftime('%Y-%m')
        if not df_x.empty:
            df_x = df_x.groupby(pd.Grouper(key='Fecha', freq='M')).sum()
            df_x.index = df_x.index.strftime('%Y-%m')
    
    # Preparar datos para Chart.js
    chart_data = {
        'ganancias': {
            'labels': [],
            'data': []
        },
        'gastos': {
            'labels': [],
            'data': []
        }
    }
    
    if not df_g.empty:
        if chart_type == 'monthly':
            chart_data['ganancias']['labels'] = df_g.index.tolist()
        else:
            chart_data['ganancias']['labels'] = [str(date) for date in df_g.index]
        chart_data['ganancias']['data'] = df_g['Ganancia'].tolist()
    
    if not df_x.empty:
        if chart_type == 'monthly':
            chart_data['gastos']['labels'] = df_x.index.tolist()
        else:
            chart_data['gastos']['labels'] = [str(date) for date in df_x.index]
        chart_data['gastos']['data'] = df_x['Gasto'].tolist()
    
    return chart_data

# Función para predicciones (similar a la original pero adaptada)
def make_predictions(df_g, df_x, model_type, prediction_days, prediction_period):
    try:
        # Agregar por período
        df_g_agg = df_g.groupby(pd.Grouper(freq=prediction_period)).sum().reset_index()
        df_x_agg = df_x.groupby(pd.Grouper(key="Fecha", freq=prediction_period)).sum().reset_index()
        
        df_g_agg = df_g_agg.dropna()
        df_x_agg = df_x_agg.dropna()
        
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
                return y_pred, None, None
            
            else:
                return np.zeros(dias), None, None
        
        y_pred_ganancias, r2_g, mae_g = modelo_prediccion(df_g_agg, "Ganancia", model_type, prediction_days)
        y_pred_gastos, r2_x, mae_x = modelo_prediccion(df_x_agg, "Gasto", model_type, prediction_days)
        
        # Crear fechas de predicción
        last_date = df_g_agg["Fecha"].max() if not df_g_agg.empty else datetime.now()
        fechas_pred = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=prediction_days, freq=prediction_period)
        
        # Preparar datos para el gráfico
        prediction_data = {
            'ganancias': {
                'real': {
                    'labels': df_g_agg["Fecha"].dt.strftime('%Y-%m-%d').tolist(),
                    'data': df_g_agg["Ganancia"].tolist()
                },
                'predicted': {
                    'labels': fechas_pred.strftime('%Y-%m-%d').tolist(),
                    'data': y_pred_ganancias.tolist()
                }
            },
            'gastos': {
                'real': {
                    'labels': df_x_agg["Fecha"].dt.strftime('%Y-%m-%d').tolist(),
                    'data': df_x_agg["Gasto"].tolist()
                },
                'predicted': {
                    'labels': fechas_pred.strftime('%Y-%m-%d').tolist(),
                    'data': y_pred_gastos.tolist()
                }
            },
            'metrics': {
                'ganancias': {
                    'r2': r2_g,
                    'mae': mae_g
                },
                'gastos': {
                    'r2': r2_x,
                    'mae': mae_x
                }
            }
        }
        
        return prediction_data
    
    except Exception as e:
        print(f"Error en predicción: {e}")
        return None

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    chart_type = request.args.get('chart_type', 'separate')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    df_g, df_x = get_datos()
    chart_data = process_data_for_chart(df_g, df_x, chart_type, start_date, end_date)
    
    return jsonify(chart_data)

@app.route('/get_predictions', methods=['GET'])
def get_predictions():
    model_type = request.args.get('model_type', 'linear')
    prediction_days = int(request.args.get('prediction_days', 30))
    prediction_period = request.args.get('prediction_period', 'D')
    
    df_g, df_x = get_datos()
    prediction_data = make_predictions(df_g, df_x, model_type, prediction_days, prediction_period)
    
    return jsonify(prediction_data)

if __name__ == '__main__':
    app.run(debug=True)