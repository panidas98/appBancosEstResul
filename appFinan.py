import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression

#Nuevo cargue...

# Función para cargar el CSV desde Google Drive
@st.cache_data
def load_data():
    url = 'https://raw.githubusercontent.com/panidas98/appBancosEstResul/main/consolidadoFinal.xlsx'
    data = pd.read_excel(url)
    # Convertir las columnas de fecha
    data['Mes'] = data['Mes'].apply(lambda x: f'{int(x):02d}')  # Asegurar que el mes sea de dos dígitos
    data['Fecha'] = pd.to_datetime(data['Año'].astype(str) + '-' + data['Mes'] + '-01')
    return data

# Cargar los datos
data = load_data()

# Título del dashboard
st.title('Analisis de Rentabilidad de Bancos en Colombia')

# Configuración de la barra lateral (sidebar)
st.sidebar.header("Filtros")

# Filtros interactivos en la barra lateral
# Filtro por bancos (selección múltiple)
bancos = data['Banco'].unique()
selected_bancos = st.sidebar.multiselect('Selecciona los bancos', bancos, default=bancos[0])

# Filtro por índice de rentabilidad (rango)
min_indice, max_indice = data['indiceRentabilidad'].min(), data['indiceRentabilidad'].max()
indice_rentabilidad = st.sidebar.slider(
    'Selecciona el rango de índice de rentabilidad',
    min_value=float(min_indice), max_value=float(max_indice),
    value=(min_indice, max_indice)
)

# Filtro por bancos (selección múltiple)
anio = data['Año'].unique()
selected_anios = st.sidebar.multiselect('Selecciona los años', anio, default=[anio[0],anio[1],anio[2],anio[3],anio[4],anio[5]])

# Filtrar datos según las selecciones
filtered_data = data[
    (data['Banco'].isin(selected_bancos)) &
    (data['indiceRentabilidad'] >= indice_rentabilidad[0]) &
    (data['indiceRentabilidad'] <= indice_rentabilidad[1]) &
    (data['Año'].isin(selected_anios))
]

# Configurar el layout de las gráficas
st.subheader('Visualización de Datos Filtrados')

# Gráfica de barras: Ingresos y Gastos por Banco y Mes
fig1 = go.Figure()

# Colores para cada banco
color_palette = px.colors.qualitative.G10
bancos_unicos = filtered_data['Banco'].unique()
color_map = {banco: color_palette[i % len(color_palette)] for i, banco in enumerate(bancos_unicos)}

fig1 = go.Figure()

# Agregar trazos para cada banco, tanto para ingresos como para gastos
for banco in bancos_unicos:
    # Filtrar datos del banco actual
    banco_data = filtered_data[filtered_data['Banco'] == banco]

    # Barra para ingresos de cada banco
    fig1.add_trace(go.Bar(
        x=banco_data['Fecha'],
        y=banco_data['Valor_Ingreso'],
        name=f'Ingresos - {banco}',
        marker_color=color_map[banco],
        hovertemplate='Banco: %{customdata}<br>Ingresos: %{y:.2f}M<extra></extra>',
        customdata=[banco] * len(banco_data)
    ))

    # Barra para gastos de cada banco
    fig1.add_trace(go.Bar(
        x=banco_data['Fecha'],
        y=-banco_data['Valor_Gasto'],  # Invertir el valor para que las barras queden abajo
        name=f'Gastos - {banco}',
        marker_color=color_map[banco],
        hovertemplate='Banco: %{customdata}<br>Gastos: -%{y:.2f}M<extra></extra>',
        customdata=[banco] * len(banco_data)
    ))

# Configuración de la gráfica
fig1.update_layout(
    title='Ingresos y Gastos por Banco y Mes',
    xaxis_title='Fecha',
    yaxis_title='Valor en miles de pesos',
    barmode='group',  # Agrupar las barras por banco dentro de cada mes
    template='plotly_white',
    legend_title='Tipo de Valor y Banco'
)

st.plotly_chart(fig1, use_container_width=True)

# Gráfica de líneas: Beneficio Neto y Capital Neto por Banco y Mes
fig2 = go.Figure()

for banco in selected_bancos:
    banco_data = filtered_data[filtered_data['Banco'] == banco]
    fig2.add_trace(go.Scatter(
        x=banco_data['Fecha'],
        y=banco_data['Beneficio Neto'],
        mode='lines',
        name=f'{banco} - Beneficio Neto'
    ))
    fig2.add_trace(go.Scatter(
        x=banco_data['Fecha'],
        y=banco_data['Capital Neto'],
        mode='lines',
        name=f'{banco} - Capital Neto'
    ))

fig2.update_layout(
    title='Beneficio Neto y Capital Neto por Banco y Mes',
    xaxis_title='Mes',
    yaxis_title='Valor en millones',
    template='plotly_dark'
)
st.plotly_chart(fig2, use_container_width=True)

# Gráfica de líneas: Índice de Rentabilidad por Banco y Mes
fig3 = px.line(
    filtered_data,
    x='Fecha',
    y='indiceRentabilidad',
    color='Banco',
    title='Índice de Rentabilidad por Banco y Mes'
)

# Ajustar regresión lineal por cada banco
for banco in filtered_data['Banco'].unique():
    # Filtrar datos para el banco actual
    banco_data = filtered_data[filtered_data['Banco'] == banco]
    banco_data = banco_data.sort_values('Fecha')
    
    # Convertir fechas a números para el modelo
    X = np.array((banco_data['Fecha'] - banco_data['Fecha'].min()).dt.days).reshape(-1, 1)
    y = banco_data['indiceRentabilidad'].values.reshape(-1, 1)
    
    # Ajustar el modelo de regresión lineal
    reg = LinearRegression()
    reg.fit(X, y)
    y_pred = reg.predict(X)
    
    # Agregar la línea de regresión al gráfico
    fig3.add_trace(
        go.Scatter(
            x=banco_data['Fecha'],
            y=y_pred.flatten(),
            mode='lines',
            name=f'{banco} - Regresión',
            line=dict(dash='dash')  # Línea discontinua para diferenciar
        )
    )

st.plotly_chart(fig3, use_container_width=True)

# Crear la figura para mostrar la serie de tiempo histórica y la predicción
fig4 = go.Figure()

# Iterar sobre cada banco seleccionado y aplicar el modelo SARIMA
for banco in selected_bancos:
    # Filtrar datos para el banco actual
    banco_data = filtered_data[filtered_data['Banco'] == banco].set_index("Fecha")

    # Verificar si hay suficientes datos para el modelo
    if len(banco_data) >= 12:  # Asegúrate de tener al menos un año de datos
        # Entrenar el modelo SARIMA para el banco actual
        modelo_sarima = SARIMAX(
            banco_data['indiceRentabilidad'],
            order=(1, 1, 1),    # p, d, q
            seasonal_order=(1, 2, 1, 12)  # P, D, Q, s=12 (estacionalidad anual)
        )
        
        modelo_sarima_entrenado = modelo_sarima.fit(disp=False)  # Entrenar el modelo SARIMA

        # Obtener la última fecha y agregar un mes para empezar la predicción en enero del siguiente año
        fecha_maxima = banco_data.index.max()
        fecha_inicio_pred = pd.to_datetime(f'{fecha_maxima.year + 1}-01-01')

        # Predicción para los próximos 12 meses
        prediccion = modelo_sarima_entrenado.forecast(steps=12)
        
        # Crear un índice de fechas para las predicciones
        fechas_pred = pd.date_range(start=fecha_inicio_pred, periods=12, freq='M')

        # Añadir los datos históricos al gráfico
        fig4.add_trace(go.Scatter(
            x=banco_data.index,
            y=banco_data['indiceRentabilidad'],
            mode='lines',
            name=f'{banco} - Rentabilidad Histórica'
        ))

        # Añadir la predicción al gráfico
        fig4.add_trace(go.Scatter(
            x=fechas_pred,
            y=prediccion,
            mode='lines+markers',
            name=f'{banco} - Predicción (SARIMA)'
        ))

# Configuración del gráfico de series de tiempo
fig4.update_layout(
    title='Predicción del Índice de Rentabilidad por Banco y Mes',
    xaxis_title='Fecha',
    yaxis_title='Índice de Rentabilidad',
    template='plotly_white'
)
st.plotly_chart(fig4, use_container_width=True)

# Función para clasificar la correlación
def clasificar_correlacion(cor):
    if cor >= 0.8:
        return "Muy fuerte"
    elif cor >= 0.6:
        return "Fuerte"
    elif cor >= 0.4:
        return "Moderada"
    elif cor >= 0.2:
        return "Débil"
    else:
        return "Muy débil"

# Calcular la correlación general entre Beneficio Neto y Capital Neto
correlacion_general = filtered_data[['Beneficio Neto', 'Capital Neto']].corr().iloc[0, 1]

# Crear la figura para el gráfico de dispersión y la tarjeta de correlación
fig6 = make_subplots(
    rows=2, cols=1,  # Ahora son 2 filas
    row_heights=[0.7, 0.3],  # Ajustar la altura de las filas
    subplot_titles=['Relación entre Beneficio Neto y Capital Neto', 'Correlación General'],
    specs=[[{"type": "scatter"}], [{"type": "indicator"}]]  # Especificar los tipos de gráficos en las filas correspondientes
)

# Añadir los puntos del gráfico de dispersión
fig6.add_trace(go.Scatter(
    x=filtered_data['Beneficio Neto'],
    y=filtered_data['Capital Neto'],
    mode='markers',
    name='Beneficio Neto vs Capital Neto',
    marker=dict(color=px.colors.qualitative.G10[0], size=8),
    hovertemplate='Beneficio Neto: %{x:.2f}<br>Capital Neto: %{y:.2f}<extra></extra>'
), row=1, col=1)

# Añadir el scorecard con la correlación general
fuerza_correlacion = clasificar_correlacion(correlacion_general)

fig6.add_trace(go.Indicator(
    mode="number+gauge+delta",
    value=correlacion_general,
    title={'text': f'Correlación General<br><span style="font-size: 14px;">{fuerza_correlacion}</span>'},
    domain={'x': [0, 1], 'y': [0, 1]},  # Ajuste para el indicador
    number={'font': {'size': 24}, 'suffix': ""},
    gauge={'shape': "bullet", 'axis': {'range': [-1, 1]}, 'steps': [
        {'range': [-1, -0.5], 'color': "red"},
        {'range': [-0.5, 0], 'color': "orange"},
        {'range': [0, 0.5], 'color': "yellow"},
        {'range': [0.5, 1], 'color': "green"}
    ]},
    delta={'reference': 0, 'relative': True}
), row=2, col=1)

# Configuración de la disposición de la figura
fig6.update_layout(
    title='Relación entre Beneficio Neto y Capital Neto',
    xaxis_title='Beneficio Neto',
    yaxis_title='Capital Neto',
    template='plotly_white',
    showlegend=False,
    height=800,  # Aumentar la altura para que haya espacio suficiente
    title_x=0.5  # Centrar el título
)

# Mostrar el gráfico de dispersión y el scorecard con la correlación general
st.plotly_chart(fig6, use_container_width=True)

