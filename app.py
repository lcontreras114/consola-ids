import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consola de IDs - Gestión", layout="wide")

# Ocultar menú superior para más limpieza
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (GOOGLE DRIVE)
@st.cache_data(ttl=300) # Actualiza cada 5 minutos
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1166538171&single=true&output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    
    # Renombrar para visualización (Respetando que se llame ID deteccion internamente)
    df = df.rename(columns={'SUB Tipo de Spot': 'Tipo', 'ID Deteccion': 'ID'})
    
    # UNIFICACIÓN ESTRICTA: Compañía, Marca, Submarca, Producto, VersiOn y Tipo
    columnas_clave = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'Tipo']
    
    # Aseguramos que el ID sea el mismo para filas idénticas
    df['ID'] = df.groupby(columnas_clave)['ID'].transform('first')
    
    # Eliminamos duplicados para mostrar solo una fila por ID único
    df = df.drop_duplicates(subset=columnas_clave).reset_index(drop=True)
    
    if 'Estado' not in df.columns:
        df['Estado'] = 'Confiable'
        
    return df

df = cargar_datos()

# 3. INTERFAZ
st.title("🛠️ Consola de Gestión: ID Deteccion")

tab_buscar, tab_nuevo, tab_admin = st.tabs(["🔍 Buscar", "📥 Nuevo ID", "🛡️ Validación Admin"])

# --- PESTAÑA: BUSCAR ---
with tab_buscar:
    busqueda = st.text_input("Filtrar por cualquier campo (Compañía, Marca, Producto, ID...):", placeholder="Ej: Cal...")

    if busqueda:
        cols_filtro = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'ID']
        mascara = df[cols_filtro].astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        resultados = df[mascara].copy()

        if not resultados.empty:
            columnas_ver = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'Tipo', 'ID']
            st.write(f"**Resultados encontrados: {len(resultados)}**")
            
            # CÁLCULO DE ALTURA PARA QUITAR EL SCROLL INTERNO
            # Multiplicamos el número de filas por 36 píxeles (aprox la altura de una fila) + el encabezado
            alto_tabla = (len(resultados) + 1) * 36 
            
            # Mostramos la tabla configurada para que al hacer clic en el ID sea fácil de copiar
            st.dataframe(
                resultados[columnas_ver], 
                hide_index=True, 
                use_container_width=True, 
                height=alto_tabla
            )
            st.caption("💡 *Tip: Para copiar el ID, haz clic sobre el número y presiona Ctrl + C*")
        else:
            st.info("No hay coincidencias.")

# --- PESTAÑA: NUEVO ID ---
with tab_nuevo:
    st.subheader("Sugerir Nuevo Registro")
    
    def selector_o_manual(label, opciones):
        opc = ["-- Seleccionar --", "INGRESAR NUEVO (MANUAL)"] + sorted(list(opciones.astype(str).unique()))
        sel = st.selectbox(f"{label}:", opc)
        if sel == "INGRESAR NUEVO (MANUAL)":
            return st.text_input(f"Escriba {label}:").upper()
        return sel

    with st.form("form_n"):
        c1, c2 = st.columns(2)
        with c1:
            n_cia = selector_o_manual("Compañía", df['Compañía'])
            n_mar = selector_o_manual("Marca", df['Marca'])
            n_sub = selector_o_manual("Submarca", df['Submarca'])
        with c2:
            n_pro = selector_o_manual("Producto", df['Producto'])
            n_ver = st.text_input("Versión").upper()
            n_id = st.text_input("ID")
            
        if st.form_submit_button("Validar e Ingresar"):
            if n_mar and n_mar not in df['Marca'].values:
                st.warning(f"⚠️ La marca '{n_mar}' es nueva. Verifique ortografía.")
            if n_mar in df['Marca'].values and n_ver:
                vers_conocidas = df[df['Marca'] == n_mar]['VersiOn'].unique()
                if n_ver not in vers_conocidas:
                    st.error(f"🚨 La versión '{n_ver}' no coincide con registros previos de '{n_mar}'.")
            st.success("Enviado para validación.")

# --- PESTAÑA: ADMIN ---
with tab_admin:
    if 'auth' not in st.session_state: st.session_state.auth = False

    if not st.session_state.auth:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                if u == "LContreras" and p == "shanks1324":
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Error")
    else:
        st.write("Panel de Validación")
        alto_admin = (len(df) + 1) * 36
        # Limitamos la altura máxima en el panel de admin para que no sea inmensa si hay miles de datos
        st.dataframe(df[['Compañía', 'Marca', 'Producto', 'ID', 'Estado']], hide_index=True, height=min(alto_admin, 600))
        if st.button("Salir"):
            st.session_state.auth = False
            st.rerun()
