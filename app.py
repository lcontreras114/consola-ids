import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consola de IDs - Gestión", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stSelectbox { margin-top: -15px; }
    </style>
    """, unsafe_allow_html=True)

# MEMORIA TEMPORAL PARA NUEVOS IDs
if 'nuevos_ids' not in st.session_state:
    st.session_state.nuevos_ids = pd.DataFrame(columns=['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'ID', 'Estado'])

# 2. CARGA DE DATOS MULTIPLES
@st.cache_data(ttl=300) 
def cargar_datos():
    try:
        url_principal = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1166538171&single=true&output=csv"
        df = pd.read_csv(url_principal, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'SUB Tipo de Spot': 'Tipo', 'ID Deteccion': 'ID'})
        
        url_canales = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=2126304715&single=true&output=csv"
        df_canales = pd.read_csv(url_canales, encoding='utf-8-sig')
        df_canales.columns = df_canales.columns.str.strip()
        
        url_ids_canal = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=1906691236&single=true&output=csv"
        df_ids_canal = pd.read_csv(url_ids_canal, encoding='utf-8-sig')
        df_ids_canal.columns = df_ids_canal.columns.str.strip().str.upper()

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
            
            html_tabla = """
            <style>
                :root { --bg: #FFFFFF; --text: #111827; --border: #E5E7EB; --th-bg: #1E3A8A; --th-text: #FFFFFF; --row-alt: #F9FAFB; --btn-bg: #F1F5F9; --btn-border: #CBD5E1; --btn-hover: #E2E8F0; --hover-resaltador: rgba(250, 204, 21, 0.35); }
                @media (prefers-color-scheme: dark) {
                    :root { --bg: #1F2937; --text: #F9FAFB; --border: #374151; --th-bg: #1E3A8A; --row-alt: #111827; --btn-bg: #374151; --btn-border: #4B5563; --btn-hover: #4B5563; --hover-resaltador: rgba(250, 204, 21, 0.2); }
                }
                body { margin: 0; font-family: sans-serif; background-color: transparent; }
                table { width: 100%; border-collapse: collapse; font-size: 14px; background-color: var(--bg); }
                th, td { border: 1px solid var(--border); padding: 10px; text-align: left; color: var(--text); transition: background-color 0.1s; }
                th { background-color: var(--th-bg); color: var(--th-text); }
                tr:nth-child(even) td { background-color: var(--row-alt); }
                tr:hover td { background-color: var(--hover-resaltador) !important; color: var(--text) !important; }
                
                .btn-c { background: var(--btn-bg); border: 1px solid var(--btn-border); color: var(--text); cursor: pointer; width: 100%; font-weight: 700; border-radius: 4px; padding: 6px; transition: 0.2s; }
                .btn-c:hover { background: var(--btn-hover); transform: scale(1.02); }
                .btn-c.copiado { background-color: #10B981 !important; color: white !important; border-color: #059669 !important; }
            </style>
            <script>
                function copiarID(texto, boton) {
                    navigator.clipboard.writeText(texto);
                    let txtOrig = boton.innerHTML;
                    boton.innerHTML = '¡Copiado!';
                    boton.classList.add('copiado');
                    setTimeout(() => { 
                        boton.innerHTML = txtOrig; 
                        boton.classList.remove('copiado'); 
                    }, 1200);
                }
            </script>
            """
            html_tabla += "<table><tr><th>Compañía</th><th>Marca</th><th>Submarca</th><th>Producto</th><th>Versión</th><th>Tipo</th><th>ID</th></tr>"
            
            for _, f in resultados.iterrows():
                id_t = str(f['ID'])
                html_tabla += f"<tr><td>{f['Compañía']}</td><td>{f['Marca']}</td><td>{f['Submarca']}</td><td>{f['Producto']}</td><td>{f['VersiOn']}</td><td>{f['Tipo']}</td><td><button class='btn-c' onclick=\"copiarID('{id_t}', this)\">{id_t}</button></td></tr>"
            html_tabla += "</table>"
            
            altura_exacta = 80 + (len(resultados) * 55)
            components.html(html_tabla, height=altura_exacta, scrolling=False)
            
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
                if n_cia and n_mar and n_id:
                    # Guardar en memoria temporal de la sesión
                    nuevo_registro = pd.DataFrame([{
                        'Compañía': n_cia, 'Marca': n_mar, 'Submarca': n_sub, 
                        'Producto': n_pro, 'VersiOn': n_ver, 'ID': n_id, 'Estado': 'Pendiente'
                    }])
                    st.session_state.nuevos_ids = pd.concat([st.session_state.nuevos_ids, nuevo_registro], ignore_index=True)
                    st.success("¡Registrado en memoria! El administrador ahora puede revisarlo en la Pestaña 4.")
                else:
                    st.error("Faltan campos obligatorios por llenar.")

# ==========================================
# --- PESTAÑA 3: IDs x CANAL ---
# ==========================================
with tab_canales:
    if not df_canales.empty:
        col_busqueda, col_identidad = st.columns([1, 3.5])
        
        with col_busqueda:
            st.write("**Selección de Canal**")
            lista_c = ["-- Seleccionar --"] + sorted(df_canales['CANAL'].dropna().unique().tolist())
            canal_sel = st.selectbox("Canal:", lista_c, label_visibility="collapsed")

        if canal_sel != "-- Seleccionar --":
            with col_identidad:
                info = df_canales[df_canales['CANAL'] == canal_sel].iloc[0]
                def clean(val): return str(val).replace('nan', 'N/A').strip()
                
                station_id = clean(info.get('StationID'))
                tag_auto = clean(info.get('TAG DE AUTOPROMOS'))
                grilla_val = clean(info.get('Grilla Web /Dish'))
                texto_monitor = f"{canal_sel} - {station_id} - MONITOR"
                
                btn_grilla_html = ""
                if grilla_val != 'N/A' and grilla_val != '':
                    if "http" in grilla_val.lower():
                        link = grilla_val
                        onclick_action = ""
                        texto_btn = "🌐 Ver Grilla Web<br><span style='font-size:10px; font-weight:normal;'>(Abrir enlace)</span>"
                    elif "carta oficial" in grilla_val.lower():
                        link = "file://192.168.148.80/Casos/MonDedicado/Programacion"
                        ruta_js = r"\\192.168.148.80\Casos\MonDedicado\Programacion".replace("\\", "\\\\")
                        onclick_action = f"onclick=\"cop_ruta(event, '{ruta_js}');\""
                        texto_btn = "📁 Carta Oficial<br><span style='font-size:10px; font-weight:normal;'>(Intenta abrir / Copia ruta)</span>"
                    else:
                        link = "https://secciones.dish.com.mx/guiadeprogramacion.html"
                        onclick_action = ""
                        texto_btn = f"📡 Grilla Dish<br><span style='font-size:11px; font-weight:normal;'>({grilla_val})</span>"

                    btn_grilla_html = f"""
                    <a href="{link}" target="_blank" class="btn-grilla" {onclick_action}>
                        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                            {texto_btn}
                        </div>
                    </a>
                    """
                
                html_ficha = f"""
                <style>
                    :root {{ --bg-card: #F8FAFC; --text: #1E293B; --btn-promo: #0F172A; --btn-text: #FFF; }}
                    @media (prefers-color-scheme: dark) {{
                        :root {{ --bg-card: #1E293B; --text: #F8FAFC; --btn-promo: #374151; }}
                    }}
                    body {{ font-family: sans-serif; margin: 0; display: flex; gap: 15px; align-items: stretch; background: transparent; width: 100%; }}
                    .card {{ flex: 2.2; display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border: 2px dashed #3B82F6; border-radius: 10px; padding: 12px; cursor: pointer; transition: 0.2s; color: var(--text); }}
                    .card:hover {{ transform: scale(1.01); border-color: #60A5FA; }}
                    .info-txt {{ font-size: 13px; line-height: 1.4; }}
                    .logo-img img {{ max-height: 70px; max-width: 120px; }}
                    .btn-grilla {{ flex: 1; background: #3B82F6; color: white; border-radius: 10px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; text-decoration: none; border: none; box-sizing: border-box; }}
                    .btn-grilla:hover {{ background: #2563EB; transform: scale(1.02); }}
                    .btn-promo {{ flex: 1; background: var(--btn-promo); color: var(--btn-text); border: none; border-radius: 10px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; }}
                    .btn-promo:hover {{ filter: brightness(1.2); transform: scale(1.02); }}
                    .toast {{ position: fixed; bottom: 5px; right: 5px; background: #10B981; color: white; padding: 8px 15px; border-radius: 5px; font-size: 12px; font-weight: bold; display: none; z-index: 1000; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);}}
                </style>
                <script>
                    function cop(txt, msg = '✓ Copiado') {{
                        navigator.clipboard.writeText(txt);
                        let t = document.getElementById('t'); t.style.display='block'; t.innerHTML = msg;
                        setTimeout(()=>{{t.style.display='none'}}, 2000);
                    }}
                    function cop_ruta(e, txt) {{
                        navigator.clipboard.writeText(txt);
                        let t = document.getElementById('t'); t.style.display='block'; t.innerHTML = '✓ Ruta copiada (Pégala en tu explorador de red)';
                        setTimeout(()=>{{t.style.display='none'}}, 3500);
                    }}
                </script>
                <div class="card" onclick="cop('{texto_monitor}')">
                    <div class="info-txt">
                        <b>{canal_sel}</b><br>
                        Network: {clean(info.get('Network'))} | Tipo: {clean(info.get('Tipo'))}<br>
                        ID: {station_id} | Server: {clean(info.get('Server'))}
                    </div>
                    <div class="logo-img"><img src="{clean(info.get('LOGO_URL'))}" onerror="this.style.display='none'"></div>
                </div>
                {btn_grilla_html}
                <button class="btn-promo" onclick="cop('{tag_auto}', '✓ Tag de Autopromo copiado')">
                    TAG AUTOPROMO:<br>{tag_auto}
                </button>
                <div id="t" class="toast"></div>
                """
                components.html(html_ficha, height=115, scrolling=False)

            st.divider()
            st.write("### IDs de Operación")
            
            if not df_ids_canal.empty and 'CANAL' in df_ids_canal.columns:
                ids_c = df_ids_canal[df_ids_canal['CANAL'] == canal_sel]
                if not ids_c.empty:
                    hashes = ids_c['CODIGO HASH'].dropna().unique()
                    for h in hashes:
                        st.markdown(f"**{h}**")
                        df_h = ids_c[ids_c['CODIGO HASH'] == h]
                        
                        html_ids = """
                        <style>
                            :root { --bg: #FFFFFF; --text: #111827; --border: #E5E7EB; --th-bg: #F8FAFC; --btn-bg: #FFF; --btn-border: #CBD5E1; --btn-hover: #EFF6FF; --hover-resaltador: rgba(250, 204, 21, 0.35); }
                            @media (prefers-color-scheme: dark) { :root { --bg: #1F2937; --text: #F9FAFB; --border: #374151; --th-bg: #111827; --btn-bg: #374151; --btn-border: #4B5563; --btn-hover: #4B5563; --hover-resaltador: rgba(250, 204, 21, 0.2); } }
                            body{margin:0; background: transparent;} 
                            table{width:100%;border-collapse:collapse;font-size:13px;font-family:sans-serif; background: var(--bg);} 
                            th,td{border:1px solid var(--border);padding:8px;text-align:left; color: var(--text); transition: background-color 0.1s;} 
                            th{background: var(--th-bg);} 
                            tr:hover td { background-color: var(--hover-resaltador) !important; color: var(--text) !important; }
                            .btn-i{width:100%;cursor:pointer;font-weight:700;background:var(--btn-bg);border:1px solid var(--btn-border); color: var(--text); border-radius:4px;padding:4px; transition:0.2s;}
                            .btn-i:hover{background:var(--btn-hover); border-color:#3B82F6; transform: scale(1.02);}
                            .btn-i.copiado { background-color: #10B981 !important; color: white !important; border-color: #059669 !important; }
                        </style>
                        <script>
                            function copiarID(texto, boton) {
                                navigator.clipboard.writeText(texto);
                                let txtOrig = boton.innerHTML;
                                boton.innerHTML = '¡Copiado!';
                                boton.classList.add('copiado');
                                setTimeout(() => { boton.innerHTML = txtOrig; boton.classList.remove('copiado'); }, 1200);
                            }
                        </script>
                        """
                        html_ids += "<table><tr><th width='20%'>Tipo</th><th width='60%'>Descripción</th><th width='20%'>ID</th></tr>"
                        
                        for _, r in df_h.iterrows():
                            v_id = str(r['ID'])
                            html_ids += f"<tr><td>{r['TIPO']}</td><td>{r['DESCRIPCION']}</td><td><button class='btn-i' onclick=\"copiarID('{v_id}', this)\">{v_id}</button></td></tr>"
                        html_ids += "</table>"
                        
                        altura_ids = 60 + (len(df_h) * 55)
                        components.html(html_ids, height=altura_ids, scrolling=False)
                else:
                    st.info("Sin registros de IDs para este canal.")
            else:
                st.error("Error: No se encontró la columna 'CANAL'.")
    else:
        st.warning("Verifique los enlaces de Google Sheets.")

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
                else: st.error("Credenciales incorrectas. Intente de nuevo.")
    else:
        st.subheader("🛡️ Panel de Validación Admin")
        
        # 1. Tabla de Nuevos Registros de la sesión actual
        st.write("### 📥 IDs Pendientes (Generados en esta sesión)")
        if not st.session_state.nuevos_ids.empty:
            st.dataframe(st.session_state.nuevos_ids, hide_index=True)
            st.info("👆 Cópialos y pégalos en tu Google Sheet (Base Madre) para hacerlos permanentes.")
        else:
            st.write("No hay IDs nuevos pendientes.")
            
        st.divider()
        
        # 2. Tabla Base Madre de Drive
        st.write("### 📚 Base Madre de IDs (Confiables en Drive)")
        if not df.empty:
            st.dataframe(df[['Compañía', 'Marca', 'Producto', 'ID', 'Estado']], hide_index=True, height=400)
            
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()
