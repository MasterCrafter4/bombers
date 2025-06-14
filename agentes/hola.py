import pandas as pd
import matplotlib.pyplot as plt

# Leer archivo CSV
df = pd.read_csv('archivo.csv')

# Contar cuántas partidas hay por cada tipo de resultado
conteo_resultados = df['result'].value_counts()

# Mostrar la gráfica de barras
conteo_resultados.plot(kind='bar', color=['green', 'red'], title='Cantidad de partidas por resultado')
plt.xlabel('Resultado')
plt.ylabel('Número de partidas')
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

