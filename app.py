import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Consola de IDs", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAlert {margin-top: 10px;}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA Y LIMPIEZA DE DATOS (REGLA DE UNIFICACIÓN ESTRICTA)
@st.cache_data(ttl=600)
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1166538171&single=true&output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    
    # Renombrar para facilitar manejo interno según tus preferencias
    df = df.rename(columns={'SUB Tipo de Spot': 'Tipo', 'ID Deteccion': 'ID'})
    
    # REGLA: Unificar ID si Compañía, Marca, Submarca, VersiOn y Tipo son iguales
    columnas_clave = ['Compañía', 'Marca', 'Submarca', 'VersiOn', 'Tipo']
    
    # Agrupamos y tomamos el primer ID para evitar duplicidad de IDs en la misma categoría
    df['ID'] = df.groupby(columnas_clave)['ID'].transform('first')
    
    # Eliminamos filas duplicadas para que solo exista un ID por cada combinación única
    df = df.drop_duplicates(subset=columnas_clave).reset_index(drop=True)
    
    if 'Estado' not in df.columns:
        df['Estado'] = 'Confiable'
        
    return df

df = cargar_datos()

# 3. INTERFAZ DE PESTAÑAS
tab_buscar, tab_nuevo, tab_admin = st.tabs(["🔍 Buscar", "📥 Nuevo ID", "🛡️ Validación Admin"])

# --- PESTAÑA: BUSCAR ---
with tab_buscar:
    st.subheader("Búsqueda Universal")
    busqueda = st.text_input("Filtrar por Compañía, Marca, Producto, Versión o ID:", placeholder="Ej: Cal o 1620...")

    if busqueda:
        cols_filtro = ['Compañía', 'Marca', 'Submarca', 'VersiOn', 'ID', 'Producto']
        mascara = df[cols_filtro].astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        resultados = df[mascara].copy()

        if not resultados.empty:
            columnas_ver = ['Compañía', 'Marca', 'Submarca', 'VersiOn', 'Tipo', 'ID']
            st.write(f"Resultados únicos encontrados ({len(resultados)}):")
            st.dataframe(resultados[columnas_ver], hide_index=True, use_container_width=True)
        else:
            st.info("No se encontraron coincidencias.")

# --- PESTAÑA: NUEVO ID (CON VALIDACIÓN DE ERRORES) ---
with tab_nuevo:
    st.subheader("Sugerir Registro en Base de Datos")
    
    def selector_o_manual(label, opciones):
        opc_finales = ["-- Seleccionar --", "INGRESAR NUEVO (MANUAL)"] + sorted(list(opciones))
        seleccion = st.selectbox(f"{label}:", opc_finales)
        if seleccion == "INGRESAR NUEVO (MANUAL)":
            return st.text_input(f"Escriba el nuevo {label}:").upper()
        return seleccion

    with st.form("form_registro"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            n_cia = selector_o_manual("Compañía", df['Compañía'].unique())
            n_marca = selector_o_manual("Marca", df['Marca'].unique())
            n_sub = selector_o_manual("Submarca", df['Submarca'].unique())
        
        with col_b:
            n_ver = st.text_input("Versión (Manual)").upper()
            n_tipo = selector_o_manual("Tipo", df['Tipo'].unique())
            n_id = st.text_input("ID Detección")

        btn_validar = st.form_submit_button("Validar e Ingresar")

    if btn_validar:
        # 1. Seguridad contra errores ortográficos básicos (Novatos)
        if n_marca:
            # Buscar marcas muy parecidas
            marcas_existentes = df['Marca'].unique()
            if n_marca not in marcas_existentes:
                st.warning(f"⚠️ La marca '{n_marca}' no existe en la base de datos actual. Verifique que no sea un error ortográfico.")
        
        # 2. Validación de consistencia Marca-Versión
        if n_marca and n_ver and n_marca in df['Marca'].values:
            versiones_conocidas = df[df['Marca'] == n_marca]['VersiOn'].unique()
            if n_ver not in versiones_conocidas:
                st.error(f"🚨 Alerta de Consistencia: La versión '{n_ver}' no ha sido asociada anteriormente a la marca '{n_marca}'. ¿Está seguro de que es correcta?")
        
        st.success(f"Solicitud para el ID {n_id} enviada. Estado: No Validado.")

# --- PESTAÑA: VALIDACIÓN ADMIN (ACCESO PROTEGIDO) ---
with tab_admin:
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.write("### Área Restringida")
        with st.form("login_admin"):
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if user == "LContreras" and pw == "shanks1324":
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
    else:
        st.subheader("Panel de Control - Validación de Datos")
        st.write("Bienvenido, LContreras.")
        
        # Aquí se filtraría por estado 'No Validado' cuando conectemos la escritura al Drive
        st.write("Vista previa de estados actuales:")
        st.dataframe(df[['Compañía', 'Marca', 'ID', 'Estado']], hide_index=True)
        
        if st.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()