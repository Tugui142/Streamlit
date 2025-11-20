import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np

# Configuración de la página (Adaptado al sistema hidropónico)
st.set_page_config(
    page_title="Sistema IoT de Riego Hidropónico - Vita Eterna SAS",
    page_icon="💧",
    layout="wide"
)

# Custom CSS (Copiado del ejemplo de Gas)
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f8f9fa; /* Fondo claro */
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    /* Estilo para los títulos de las secciones */
    h3 {
        color: #0077b6; /* Un color azul para el agua/riego */
    }
    </style>
""", unsafe_allow_html=True)

# Título y descripción (Restaurado a Hydroponics)
st.title("💧 Sistema IoT de Monitoreo y Riego Hidropónico — Vita Eterna SAS")
st.markdown("""
    ### 🪴 Cultivo Hidropónico Medellín
    Este sistema permite analizar datos capturados por un ESP32 en el cultivo hidropónico de **Vita Eterna SAS**,
    incluyendo **temperatura**, **humedad** y **estado de la válvula de riego**.
    Los datos provienen de *InfluxDB → Grafana → CSV*.
""")

# Ubicación del sensor (Vita Eterna SAS)
vitaeterna_location = pd.DataFrame({
    'lat': [6.2108673],
    'lon': [-75.5709709]
})

st.subheader("📍 Ubicación del sistema en Vita Eterna SAS")
st.map(vitaeterna_location, zoom=18)

# Cargador de archivo
uploaded_file = st.file_uploader("📂 Cargar archivo CSV exportado de Grafana o InfluxDB", type=["csv"])

if uploaded_file is not None:
    try:
        # Load and process data
        try:
            df = pd.read_csv(uploaded_file, header=0) 
        except:
            df = pd.read_csv(uploaded_file, encoding="latin-1", header=0)

        st.success("Archivo cargado correctamente. Iniciando análisis del sistema hidropónico.")

        # ==========================================================
        # 📌 Lógica de Renombrado Robustos para CSV de Grafana (Join by time)
        # ==========================================================
        
        # El patrón de nombre largo para las columnas de Grafana (Join by time)
        GRAFANA_COMPLEX_NAME = '{device="ESP32", name="sensor_data"}'
        
        rename_map = {
            # Time column
            "Time": "_time", "time": "_time", "timeStamp": "_time", "result_time": "_time", 
            
            # Nombres del archivo "join by time"
            f"humidity {GRAFANA_COMPLEX_NAME}": 'humidity',
            f"temperature {GRAFANA_COMPLEX_NAME}": 'temperature',
            f"valve_state {GRAFANA_COMPLEX_NAME}": 'valve_state',
            
            # Nombres de exportaciones simples
            "humidity ESP32": "humidity", "temperature ESP32": "temperature", "valve_state ESP32": "valve_state",
            "humidity": "humidity", "temperature": "temperature", "valve_state": "valve_state",
        }
        
        columns_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        
        if columns_to_rename:
            df = df.rename(columns=columns_to_rename)
            st.info(f"Columnas renombradas: {columns_to_rename}")

        # ==========================================================
        # 📌 Validación y Procesamiento
        # ==========================================================
        required_columns = ["_time", "temperature", "humidity", "valve_state"]
        
        if "_time" not in df.columns:
            st.error("❌ La columna de tiempo ('_time') no se pudo identificar. Deteniendo la ejecución.")
            st.stop()
            
        df["_time"] = pd.to_datetime(df["_time"])
        df = df.set_index("_time")
        
        # Conversión a tipos numéricos y manejo de valores faltantes (usando media o 0 para la válvula)
        for col in ["temperature", "humidity", "valve_state"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif col == "valve_state":
                df[col] = 0
                st.warning(f"Columna '{col}' faltante. Creada con valor por defecto (0).")
            elif col == "temperature":
                df[col] = df["humidity"].mean() if "humidity" in df.columns else 25.0
                st.warning(f"Columna '{col}' faltante. Creada con valor por defecto ({df[col].iloc[0]:.1f}°C).")
            elif col == "humidity":
                df[col] = 50.0
                st.warning(f"Columna '{col}' faltante. Creada con valor por defecto (50.0%).")

        df["valve_state"] = df["valve_state"].fillna(0).astype(int, errors='ignore')

        st.write("Columnas usadas en el análisis:", list(df.columns))

        # Tabs (Adaptado del ejemplo de Gas)
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Visualización General", "📊 Estadísticas y Metas", "🔍 Filtros por Variable", "🏠 Información del Sistema"])

        # -------------------------------
        # TAB 1 — VISUALIZACIÓN
        # -------------------------------
        with tab1:
            st.subheader('📈 Comportamiento de las Variables en el Tiempo')
            
            # Métricas (Adaptado a las variables del sistema hidropónico)
            col1, col2, col3, col4 = st.columns(4)
            
            temp_avg = df['temperature'].mean()
            hum_avg = df['humidity'].mean()
            valve_mean = df['valve_state'].mean()
            
            # Condición para la Temperatura
            col1.metric("🌡️ Temp Promedio (°C)", f"{temp_avg:.2f}")
            if temp_avg > 30:
                 col1.error("🚨 Temp Promedio Alta (>30°C)")
            else:
                 col1.success("✅ Temp Promedio Normal")

            # Condición para la Humedad
            col2.metric("💧 Humedad Promedio (%)", f"{hum_avg:.2f}")
            if hum_avg < 40:
                col2.warning("⚠️ Humedad Baja (<40%)")
            else:
                col2.success("✅ Humedad Normal")

            # Métrica de Válvula
            col3.metric("🚿 % Riego Activo", f"{valve_mean*100:.1f}%")

            # Rango de Tiempo
            time_diff = df.index.max() - df.index.min()
            col4.metric("⏱️ Período Analizado", f"{time_diff}")

            st.markdown("---")
            
            # Gráficas de las tres variables
            st.subheader("🌡️ Temperatura y Humedad")
            st.line_chart(df[["temperature", "humidity"]].dropna())
            
            st.subheader("🚿 Estado de la Válvula (0=Cerrado, 1=Abierto)")
            st.area_chart(df["valve_state"])

            # Raw data display with toggle
            if st.checkbox('Mostrar datos crudos'):
                st.write(df)

        # -------------------------------
        # TAB 2 — ESTADÍSTICAS Y METAS
        # -------------------------------
        with tab2:
            st.subheader('📊 Estadísticas Descriptivas y Metas del Cultivo')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Resumen Estadístico por Variable")
                st.dataframe(df[["temperature", "humidity", "valve_state"]].describe())
            
            with col2:
                st.write("#### Metas de Riego Hidropónico")
                
                # Metas de Humedad y Temperatura
                st.metric("Metas de Humedad", "40% - 60%", 
                          delta=f"{hum_avg:.2f}% (Promedio actual)", delta_color="off")
                st.metric("Metas de Temperatura", "20°C - 28°C",
                          delta=f"{temp_avg:.2f}°C (Promedio actual)", delta_color="off")
                
                # Alerta si hay valores atípicos
                if df['temperature'].std() > 5 or df['humidity'].std() > 10:
                    st.warning("⚠️ Alta Varianza Detectada: Posible inestabilidad en el ambiente.")
                else:
                    st.info("✅ Varianza Normal. Ambiente Estable.")


        # -------------------------------
        # TAB 3 — FILTROS
        # -------------------------------
        with tab3:
            st.subheader('🔍 Filtrar y Analizar Datos')
            
            # Selector de variable para el filtro
            variable = st.selectbox("Seleccione la variable a filtrar", ["temperature", "humidity", "valve_state"])
            
            valid_data = df[variable].dropna()
            
            if valid_data.empty:
                st.warning(f"La columna '{variable}' no contiene datos numéricos válidos.")
                min_val, max_val = 0.0, 1.0
            else:
                min_val = float(valid_data.min())
                max_val = float(valid_data.max())
                
                # Manejo de slider cuando min_val == max_val
                if min_val == max_val:
                    if variable == "valve_state":
                         min_val = -0.1
                         max_val = 1.1
                    else:
                        epsilon = 0.1 
                        min_val = max_val - epsilon
                        max_val = max_val + epsilon

            # Slider de rango de valores
            rango = st.slider(f"Rango de valores de {variable}", min_val, max_val, (min_val, max_val))
                
            filtrado = df[(df[variable] >= rango[0]) & (df[variable] <= rango[1])].dropna(subset=[variable])
            
            st.write(f"### Datos filtrados ({variable})")
            st.dataframe(filtrado)
            
            # Botón de descarga
            csv = filtrado.to_csv().encode('utf-8')
            st.download_button(
                label=f"Descargar CSV Filtrado ({variable})",
                data=csv,
                file_name=f'riego_filtrado_{variable}.csv',
                mime='text/csv',
                key="download_filtrado_button"
            )


        # -------------------------------
        # TAB 4 — INFORMACIÓN DEL SISTEMA
        # -------------------------------
        with tab4:
            st.subheader("🏠 Información del sistema IoT de Riego")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📍 Contacto y Equipo")
                st.write("*Vita Eterna SAS*")
                st.write("- 📞 Teléfono: +57 (4) 555-6789")
                st.write("- 📧 Email: info@vitaeterna.com")
                st.write("- 🏠 Ubicación: Medellín - El Poblado")
                
                st.write("### 🧑‍🔬 Responsables")
                st.write("- Ingeniero a Cargo: Sofía Bermúdez")
                st.write("- Técnico de Mantenimiento: Juan Pérez")
            
            with col2:
                st.write("### 💧 Especificaciones Técnicas")
                st.write("- *Microcontrolador:* ESP32")
                st.write("- *Sensores:* DHT22 (Temperatura/Humedad)")
                st.write("- *Actuador:* Servo → Válvula de riego")
                st.write("- *Base de Datos:* InfluxDB Cloud")
                st.write("- *Lógica de Riego:* Si Humedad < 30%, Válvula = Abierta (180°)")
                
                st.write("### 📋 Protocolo de Operación")
                st.write("1. Monitoreo continuo de Temp/Hum. cada 5 segundos.")
                st.write("2. Riego automático activado si la humedad cae por debajo del umbral.")
                st.write("3. Si la temperatura supera 30°C, revisar el sistema de ventilación.")

    except Exception as e:
        st.error(f'Error al procesar el archivo: {str(e)}')
        st.info('Asegúrese de que el archivo CSV contenga las columnas de tiempo, temperatura, humedad y estado de la válvula.')
else:
    st.info('''
    💡 *Instrucciones:* 
    - Cargue un archivo CSV (exportado de Grafana) con los datos del sensor de su cultivo hidropónico.
    ''')

# Footer
st.markdown("""
---
💧 *Sistema IoT de Riego Hidropónico — Vita Eterna SAS*
""")