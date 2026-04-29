import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consola de IDs - Gestión", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS (GOOGLE DRIVE)
@st.cache_data(ttl=300) 
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1166538171&single=true&output=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    
    df = df.rename(columns={'SUB Tipo de Spot': 'Tipo', 'ID Deteccion': 'ID'})
    
    # UNIFICACIÓN ESTRICTA
    columnas_clave = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'Tipo']
    df['ID'] = df.groupby(columnas_clave)['ID'].transform('first')
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
            st.write(f"**Resultados encontrados: {len(resultados)}**")
            
            # --- TABLA HTML MEJORADA (COLORES PROFESIONALES Y SIN SCROLL) ---
            html_tabla = """
            <style>
                /* Quitamos márgenes del cuerpo para que encaje perfecto */
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                    border-radius: 8px;
                    overflow: hidden; /* Bordes redondeados */
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.05); /* Sombra sutil */
                }
                th, td {
                    border: 1px solid #E5E7EB;
                    padding: 12px 15px;
                    text-align: left;
                }
                /* Color del encabezado */
                th {
                    background-color: #1E3A8A; /* Azul Marino Corporativo */
                    color: #FFFFFF;
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 12px;
                    letter-spacing: 0.5px;
                }
                /* Filas intercaladas (Tipo Cebra) */
                tr:nth-child(even) {
                    background-color: #F9FAFB; /* Gris súper claro */
                }
                tr:nth-child(odd) {
                    background-color: #FFFFFF; /* Blanco */
                }
                /* Color al pasar el mouse por la fila */
                tr:hover {
                    background-color: #EFF6FF; /* Azul clarito */
                }
                /* Estilo del Botón de Copiar */
                .btn-copiar {
                    background-color: #F1F5F9;
                    border: 1px solid #CBD5E1;
                    color: #0F172A;
                    padding: 8px 12px;
                    text-align: center;
                    display: inline-block;
                    font-size: 13px;
                    font-weight: 700;
                    margin: 0;
                    cursor: pointer;
                    border-radius: 6px;
                    width: 100%;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }
                /* Efecto del Botón al pasar el mouse */
                .btn-copiar:hover {
                    background-color: #E2E8F0;
                    border-color: #94A3B8;
                    transform: translateY(-1px);
                }
                /* Efecto del Botón al hacer clic */
                .btn-copiar:active {
                    transform: translateY(1px);
                }
            </style>
            
            <script>
                function copiarID(texto, boton) {
                    let inputFalso = document.createElement("textarea");
                    inputFalso.value = texto;
                    document.body.appendChild(inputFalso);
                    inputFalso.select();
                    document.execCommand("copy");
                    document.body.removeChild(inputFalso);
                    
                    let textoOriginal = boton.innerHTML;
                    // Color de éxito (Verde)
                    boton.innerHTML = '¡Copiado!';
                    boton.style.backgroundColor = '#10B981';
                    boton.style.color = '#FFFFFF';
                    boton.style.borderColor = '#059669';
                    
                    setTimeout(function() {
                        boton.innerHTML = textoOriginal;
                        boton.style.backgroundColor = '#F1F5F9';
                        boton.style.color = '#0F172A';
                        boton.style.borderColor = '#CBD5E1';
                    }, 1200);
                }
            </script>
            
            <table>
                <tr>
                    <th>Compañía</th>
                    <th>Marca</th>
                    <th>Submarca</th>
                    <th>Producto</th>
                    <th>Versión</th>
                    <th>Tipo</th>
                    <th style="text-align: center;">ID Detección</th>
                </tr>
            """
            
            resultados_mostrar = resultados.head(100)
            for _, fila in resultados_mostrar.iterrows():
                id_txt = str(fila['ID'])
                html_tabla += f"""
                <tr>
                    <td>{fila['Compañía']}</td>
                    <td>{fila['Marca']}</td>
                    <td>{fila['Submarca']}</td>
                    <td>{fila['Producto']}</td>
                    <td>{fila['VersiOn']}</td>
                    <td>{fila['Tipo']}</td>
                    <td style="padding: 6px 10px;">
                        <button class="btn-copiar" onclick="copiarID('{id_txt}', this)">{id_txt}</button>
                    </td>
                </tr>
                """
            html_tabla += "</table>"
            
            if len(resultados) > 100:
                html_tabla += "<p style='color:#DC2626; font-family:sans-serif; margin-top:10px; font-weight:bold;'>⚠️ Se muestran los primeros 100 resultados para mantener el rendimiento.</p>"
            
            # --- CÁLCULO EXACTO PARA ELIMINAR EL SCROLL ---
            # 50px por el encabezado + 52px por cada fila de datos + 20px de margen extra
            alto_exacto = 50 + (len(resultados_mostrar) * 52) + 20 
            if len(resultados) > 100:
                alto_exacto += 40 # Espacio para el mensaje de advertencia
                
            # scrolling=False hace que la ventana desaparezca y el contenido se expanda
            components.html(html_tabla, height=alto_exacto, scrolling=False)

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
        st.dataframe(df[['Compañía', 'Marca', 'Producto', 'ID', 'Estado']], hide_index=True, height=min(alto_admin, 600))
        if st.button("Salir"):
            st.session_state.auth = False
            st.rerun()
