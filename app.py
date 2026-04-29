import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consola de IDs - Gestión", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Ajuste para que los selectores no tengan tanto margen arriba */
    .stSelectbox { margin-top: -15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS MULTIPLES (GOOGLE DRIVE)
@st.cache_data(ttl=300) 
def cargar_datos():
    try:
        # Añadimos encoding='utf-8-sig' para eliminar basura invisible de Google
        # URL 1: Base principal de IDs
        url_principal = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1166538171&single=true&output=csv"
        df = pd.read_csv(url_principal, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'SUB Tipo de Spot': 'Tipo', 'ID Deteccion': 'ID'})
        
        # URL 2: Información de Canales
        url_canales = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=2126304715&single=true&output=csv"
        df_canales = pd.read_csv(url_canales, encoding='utf-8-sig')
        df_canales.columns = df_canales.columns.str.strip()
        
        # URL 3: IDs por Canal
        url_ids_canal = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1906691236&single=true&output=csv"
        df_ids_canal = pd.read_csv(url_ids_canal, encoding='utf-8-sig')
        # Forzamos todo a MAYÚSCULAS en la Hoja 3 para evitar el KeyError
        df_ids_canal.columns = df_ids_canal.columns.str.strip().str.upper()

        # Unificación Base Principal
        columnas_clave = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'Tipo']
        if all(col in df.columns for col in columnas_clave):
            df['ID'] = df.groupby(columnas_clave)['ID'].transform('first')
            df = df.drop_duplicates(subset=columnas_clave).reset_index(drop=True)
            
        if 'Estado' not in df.columns:
            df['Estado'] = 'Confiable'
        
        return df, df_canales, df_ids_canal
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, df_canales, df_ids_canal = cargar_datos()

# 3. INTERFAZ
st.title("🛠️ Consola de Gestión Centralizada")

tab_buscar, tab_nuevo, tab_canales, tab_admin = st.tabs([
    "🔍 Buscar AAEE", "📥 Nuevo ID", "📺 IDs x Canal", "🛡️ Validación Admin"
])

# ==========================================
# --- PESTAÑA 1: BUSCAR AAEE ---
# ==========================================
with tab_buscar:
    busqueda = st.text_input("Filtrar por cualquier campo (Compañía, Marca, Producto, ID...):", placeholder="Ej: Caliente...", key="search_universal")
    if busqueda and not df.empty:
        cols_filtro = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'ID']
        mascara = df[cols_filtro].astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
        resultados = df[mascara].copy()
        
        if not resultados.empty:
            st.write(f"**Resultados encontrados: {len(resultados)}**")
            html_tabla = """<style>body{margin:0;font-family:sans-serif;}table{width:100%;border-collapse:collapse;font-size:14px;}th,td{border:1px solid #E5E7EB;padding:10px;text-align:left;}th{background-color:#1E3A8A;color:#FFF;font-size:12px;}.btn-c{background:#F1F5F9;border:1px solid #CBD5E1;cursor:pointer;width:100%;font-weight:700;border-radius:4px;padding:5px;transition:0.2s;}.btn-c:hover{background:#E2E8F0;}</style>"""
            html_tabla += "<table><tr><th>Compañía</th><th>Marca</th><th>Submarca</th><th>Producto</th><th>Versión</th><th>Tipo</th><th>ID</th></tr>"
            
            res_mostrar = resultados.head(100)
            for _, f in res_mostrar.iterrows():
                id_t = str(f['ID'])
                html_tabla += f"<tr><td>{f['Compañía']}</td><td>{f['Marca']}</td><td>{f['Submarca']}</td><td>{f['Producto']}</td><td>{f['VersiOn']}</td><td>{f['Tipo']}</td><td><button class='btn-c' onclick=\"navigator.clipboard.writeText('{id_t}')\">{id_t}</button></td></tr>"
            html_tabla += "</table>"
            
            components.html(html_tabla, height=min(800, 50 + len(res_mostrar)*45), scrolling=True)
            if len(resultados) > 100:
                st.warning("⚠️ Se muestran los primeros 100 resultados.")
        else:
            st.info("No hay coincidencias.")

# ==========================================
# --- PESTAÑA 2: NUEVO ID ---
# ==========================================
with tab_nuevo:
    st.subheader("Sugerir Nuevo Registro")
    
    def selector_o_manual(label, opciones):
        opc = ["-- Seleccionar --", "INGRESAR NUEVO (MANUAL)"] + sorted(list(opciones.astype(str).unique()))
        sel = st.selectbox(f"{label}:", opc)
        if sel == "INGRESAR NUEVO (MANUAL)":
            return st.text_input(f"Escriba {label}:").upper()
        return sel

    if not df.empty:
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

# ==========================================
# --- PESTAÑA 3: IDs x CANAL (COMPACTO Y CORREGIDO) ---
# ==========================================
with tab_canales:
    if not df_canales.empty:
        col_busqueda, col_identidad = st.columns([1, 2.8])
        
        with col_busqueda:
            st.write("**Selección de Canal**")
            # Lista de canales de la hoja 2
            lista_c = ["-- Seleccionar --"] + sorted(df_canales['CANAL'].dropna().unique().tolist())
            canal_sel = st.selectbox("Canal:", lista_c, label_visibility="collapsed")

        if canal_sel != "-- Seleccionar --":
            with col_identidad:
                # Extraer info
                info = df_canales[df_canales['CANAL'] == canal_sel].iloc[0]
                
                # Función para limpiar nulos
                def clean(val): return str(val).replace('nan', 'N/A').strip()
                
                station_id = clean(info.get('StationID'))
                tag_auto = clean(info.get('TAG DE AUTOPROMOS'))
                texto_monitor = f"{canal_sel} - {station_id} - MONITOR"
                
                # HTML COMPACTO (Ficha + Autopromo)
                html_ficha = f"""
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; margin: 0; display: flex; gap: 15px; align-items: flex-start; }}
                    .card {{
                        flex: 2;
                        display: flex; justify-content: space-between; align-items: center;
                        background: #F8FAFC; border: 2px dashed #3B82F6; border-radius: 10px;
                        padding: 12px; cursor: pointer; transition: 0.2s;
                    }}
                    .card:hover {{ background: #EFF6FF; transform: scale(1.01); }}
                    .info-txt {{ font-size: 13px; color: #1E293B; line-height: 1.4; }}
                    .logo-img img {{ max-height: 70px; max-width: 120px; }}
                    .btn-promo {{
                        flex: 1; height: 100px;
                        background: #0F172A; color: white; border: none; border-radius: 10px;
                        font-size: 13px; font-weight: bold; cursor: pointer;
                        transition: 0.2s;
                    }}
                    .btn-promo:hover {{ background: #1E293B; }}
                    .toast {{ position: fixed; bottom: 5px; right: 5px; background: #10B981; color: white; padding: 5px 10px; border-radius: 5px; font-size: 11px; display: none; }}
                </style>
                <script>
                    function cop(txt) {{
                        navigator.clipboard.writeText(txt);
                        let t = document.getElementById('t'); t.style.display='block'; t.innerHTML = '✓ Copiado: ' + txt;
                        setTimeout(()=>{{t.style.display='none'}}, 1500);
                    }}
                </script>
                <div class="card" onclick="cop('{texto_monitor}')">
                    <div class="info-txt">
                        <b>{canal_sel}</b><br>
                        Network: {clean(info.get('Network'))} | Tipo: {clean(info.get('Tipo'))}<br>
                        ID: {station_id} | Server: {clean(info.get('Server'))}<br>
                        Grilla: {clean(info.get('Grilla Web /Dish'))}
                    </div>
                    <div class="logo-img"><img src="{clean(info.get('LOGO_URL'))}" onerror="this.style.display='none'"></div>
                </div>
                <button class="btn-promo" onclick="cop('{tag_auto}')">
                    TAG AUTOPROMO:<br>{tag_auto}
                </button>
                <div id="t" class="toast"></div>
                """
                components.html(html_ficha, height=110)

            st.divider()
            st.write("### IDs de Operación")
            
            # Filtrado de IDs de la Hoja 3 (Protegido contra errores de columna)
            if not df_ids_canal.empty and 'CANAL' in df_ids_canal.columns:
                ids_c = df_ids_canal[df_ids_canal['CANAL'] == canal_sel]
                
                if not ids_c.empty:
                    hashes = ids_c['CODIGO HASH'].dropna().unique()
                    
                    for h in hashes:
                        st.markdown(f"**{h}**")
                        # AQUÍ ESTÁ LA CORRECCIÓN DEL NAMERROR QUE ARROJABA ANTES:
                        df_h = ids_c[ids_c['CODIGO HASH'] == h]
                        
                        html_ids = """<style>body{margin:0;}table{width:100%;border-collapse:collapse;font-size:13px;font-family:sans-serif;}th,td{border:1px solid #EEE;padding:8px;text-align:left;}th{background:#F8FAFC;} .btn-i{width:100%;cursor:pointer;font-weight:700;background:#FFF;border:1px solid #DDD;border-radius:4px;padding:4px; transition:0.2s;}.btn-i:hover{background:#EFF6FF; border-color:#3B82F6;}</style>"""
                        html_ids += "<table><tr><th width='20%'>Tipo</th><th width='60%'>Descripción</th><th width='20%'>ID</th></tr>"
                        
                        for _, r in df_h.iterrows():
                            v_id = str(r['ID'])
                            html_ids += f"<tr><td>{r['TIPO']}</td><td>{r['DESCRIPCION']}</td><td><button class='btn-i' onclick=\"navigator.clipboard.writeText('{v_id}')\">{v_id}</button></td></tr>"
                        html_ids += "</table>"
                        
                        # Dibujamos cada tablita
                        components.html(html_ids, height=(len(df_h)*38)+40)
                else:
                    st.info("Sin registros de IDs para este canal en la base de datos.")
            else:
                st.error("Error: No se encontró la columna 'CANAL' en la base de datos de IDs (Hoja 3).")
    else:
        st.warning("No se pudo cargar la información de los canales. Verifique los enlaces de Google Sheets.")

# ==========================================
# --- PESTAÑA 4: ADMIN ---
# ==========================================
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
                else: st.error("Credenciales incorrectas")
    else:
        st.write("Panel de Validación de Nuevos Registros")
        if not df.empty:
            alto_admin = (len(df) + 1) * 36
            st.dataframe(df[['Compañía', 'Marca', 'Producto', 'ID', 'Estado']], hide_index=True, height=min(alto_admin, 600))
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()
