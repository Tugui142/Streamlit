import pandas as pd
import streamlit as st
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Sistema IoT de Riego Hidropónico - Vita Eterna SAS",
    page_icon="💧",
    layout="wide"
)

# Encabezado
st.title("💧 Sistema IoT de Monitoreo y Riego Hidropónico — Vita Eterna SAS")
st.markdown("""
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
st.subheader("📂 Cargar archivo CSV exportado de Grafana o InfluxDB")
uploaded_file = st.file_uploader("Seleccione un archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Intento de lectura robusta
        try:
            df = pd.read_csv(uploaded_file)
        except:
            df = pd.read_csv(uploaded_file, encoding="latin-1")

        st.success("Archivo cargado correctamente.")

        # ==========================================================
        # 📌 Renombrar columnas para el archivo cargado
        # ==========================================================
        rename_map = {
            "Time": "_time",
            "humidity ESP32": "humidity"
        }
        
        columns_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        
        if columns_to_rename:
            df = df.rename(columns=columns_to_rename)
            st.info(f"Columnas renombradas: {columns_to_rename}")

        # ==========================================================
        # 📌 Validación y manejo de columnas faltantes
        # ==========================================================
        required_columns = ["_time", "temperature", "humidity", "valve_state"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.warning(f"""
            El archivo no contiene todas las columnas necesarias: {', '.join(missing_columns)}.
            Se crearán con **valores por defecto** para permitir la visualización.
            """)
            
            if "temperature" in missing_columns:
                df["temperature"] = df["humidity"].mean() if "humidity" in df.columns else 25.0
                st.info(f"Columna 'temperature' creada con valor por defecto ({df['temperature'].iloc[0]:.1f}°C)")
            if "valve_state" in missing_columns:
                df["valve_state"] = 0
                st.info("Columna 'valve_state' creada con valor por defecto (0 = Cerrada)")
        
        if not all(col in df.columns for col in required_columns):
             st.error("Error grave: No se pudieron establecer las columnas esenciales. Deteniendo la ejecución.")
             st.stop()
             
        st.write("Columnas usadas en el análisis:", list(df.columns))

        # Procesar el tiempo
        df["_time"] = pd.to_datetime(df["_time"])
        df = df.set_index("_time")

        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Visualización General",
            "📊 Estadísticas",
            "🔍 Filtros por Variable",
            "🛠️ Información del Sistema"
        ])

        # -------------------------------
        # TAB 1 — VISUALIZACIÓN
        # -------------------------------
        with tab1:
            st.subheader("📈 Comportamiento de las Variables en el Tiempo")
            st.line_chart(df[["temperature", "humidity"]])
            st.subheader("🚿 Estado de la válvula (0 = cerrado, 1 = abierto)")
            st.area_chart(df["valve_state"])
            if st.checkbox("Mostrar datos crudos"):
                st.dataframe(df)

        # -------------------------------
        # TAB 2 — ESTADÍSTICAS
        # -------------------------------
        with tab2:
            st.subheader("📊 Estadísticas descriptivas")
            col1, col2, col3 = st.columns(3)
            col1.metric("🌡️ Temp Promedio (°C)", f"{df['temperature'].mean():.2f}")
            col2.metric("💧 Humedad Promedio (%)", f"{df['humidity'].mean():.2f}")
            col3.metric("🚿 % Riego Activo", f"{df['valve_state'].mean()*100:.1f}%")
            st.write("### Estadísticos completos")
            st.dataframe(df.describe())

        # -------------------------------
        # TAB 3 — FILTROS
        # -------------------------------
        with tab3:
            st.subheader("🔍 Filtrar datos por variable")
            variable = st.selectbox("Seleccione una variable", ["temperature", "humidity", "valve_state"])
            min_val = float(df[variable].min())
            max_val = float(df[variable].max())
            rango = st.slider("Rango de valores", min_val, max_val, (min_val, max_val))
            filtrado = df[(df[variable] >= rango[0]) & (df[variable] <= rango[1])]
            st.write(f"### Datos filtrados ({variable})")
            st.dataframe(filtrado)
            st.download_button("Descargar CSV filtrado", filtrado.to_csv().encode("utf-8"), "filtrado.csv", "text/csv")

        # -------------------------------
        # TAB 4 — INFORMACIÓN DEL SISTEMA
        # -------------------------------
        with tab4:
            st.subheader("🛠️ Información del sistema IoT")
            st.write("""
            **Microcontrolador:** ESP32  
            **Sensores:** DHT22 (Temperatura/Humedad)  
            **Actuador:** Servo → Válvula de riego hidropónico  
            **Base de Datos:** InfluxDB Cloud  
            **Visualización:** Grafana → Exportado a CSV  
            **Analítica:** Streamlit  
            """)
            st.write("### Objetivo del sistema")
            st.write("""
            - Controlar automáticamente el riego de un cultivo hidropónico en Vita Eterna SAS.  
            - Registrar variables ambientales para analizar el comportamiento del sistema.  
            - Detectar patrones y anticipar fallas.  
            """)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")

else:
    st.info("Por favor cargue un archivo CSV para comenzar.")
        

# Footer
st.markdown("""
---
💧 *Sistema IoT de Riego Hidropónico — Vita Eterna SAS*
""")
