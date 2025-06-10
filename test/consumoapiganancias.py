import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

url = "http://localhost:3000/api/graphql"

query = """
query {
  ventaBoletos {
    id
    precio
    fechaVenta
  }
}
"""

response = requests.post(url, json={'query': query})
data = response.json()

venta_boletos = data["data"]["ventaBoletos"]

# Convertimos a DataFrame
df = pd.DataFrame(venta_boletos)

# Convertimos fechaVenta a datetime
df["fechaVenta"] = pd.to_datetime(df["fechaVenta"])

# Agrupamos por fecha (sin la hora) y sumamos los precios
df_grouped = df.groupby(df["fechaVenta"].dt.date)["precio"].sum()

# Graficamos
df_grouped.plot(kind='bar', title="Ganancias por Fecha")
plt.xlabel("Fecha")
plt.ylabel("Ganancia")
plt.tight_layout()
plt.savefig("ganancias.png")
plt.show()
