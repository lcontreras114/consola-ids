import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import re

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Consola de IDs - Gestión", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
    .stSelectbox { margin-top: -15px; }
    .stTextInput { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. SISTEMA DE AUTENTICACIÓN (LOGIN STATE)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.rol = ""

# MEMORIA TEMPORAL PARA NUEVOS IDs
if 'df_live' not in st.session_state:
    st.session_state.df_live = None
if 'nuevos_ids' not in st.session_state:
    st.session_state.nuevos_ids = pd.DataFrame(columns=['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'ID', 'Estado', 'Tipo'])

# 3. CARGA DE DATOS MULTIPLES (Ahora con Carga de Usuarios)
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

        url_usuarios = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=447315811&single=true&output=csv" 
        try:
            df_usuarios = pd.read_csv(url_usuarios, encoding='utf-8-sig')
            df_usuarios.columns = df_usuarios.columns.str.strip().str.upper()
        except:
            df_usuarios = pd.DataFrame(columns=['USUARIO', 'CONTRASEÑA', 'RANGO'])
            st.error("⚠️ Faltó actualizar el enlace CSV de la hoja USUARIOS.")

        # NUEVA HOJA: CARGA DE USUARIOS
        url_carga = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJNg51LW2DbTBSEOOSPOTHR0dc4xCF1lTZqLq_z_R9LkfMHO7CzyrI45eGhbApkyGtcBwX4ibmRtZd/pub?gid=2019399218&single=true&output=csv"
        try:
            df_carga = pd.read_csv(url_carga, encoding='utf-8-sig')
            df_carga.columns = df_carga.columns.str.strip().str.upper()
        except:
            df_carga = pd.DataFrame(columns=['USUARIO', 'CANAL'])

        columnas_clave = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'Tipo']
        if all(col in df.columns for col in columnas_clave):
            df['ID'] = df.groupby(columnas_clave)['ID'].transform('first')
            df = df.drop_duplicates(subset=columnas_clave).reset_index(drop=True)
            
        if 'Estado' not in df.columns:
            df['Estado'] = 'Confiable'
        
        return df, df_canales, df_ids_canal, df_usuarios, df_carga
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_base, df_canales, df_ids_canal, df_usuarios, df_carga = cargar_datos()

if st.session_state.df_live is None and not df_base.empty:
    st.session_state.df_live = df_base.copy()

df = st.session_state.df_live if st.session_state.df_live is not None else df_base

# ==========================================
# 4. PANTALLA DE LOGIN GLOBAL
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c_izq, c_centro, c_der = st.columns([1, 1.5, 1])
    
    with c_centro:
        st.title("🔐 Consola de Gestión")
        st.write("Por favor, inicia sesión para continuar.")
        
        with st.form("form_login"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Entrar", type="primary")
            
            if btn_login:
                if not df_usuarios.empty and 'USUARIO' in df_usuarios.columns and 'CONTRASEÑA' in df_usuarios.columns:
                    usuario_valido = df_usuarios[(df_usuarios['USUARIO'].astype(str) == user) & (df_usuarios['CONTRASEÑA'].astype(str) == pwd)]
                    
                    if not usuario_valido.empty:
                        rango_usuario = str(usuario_valido.iloc[0]['RANGO']).lower().strip()
                        if rango_usuario in ['adm', 'regular', 'capa']:
                            st.session_state.logged_in = True
                            st.session_state.username = user
                            st.session_state.rol = rango_usuario
                            st.rerun()
                        else:
                            st.error("El rango de este usuario no es válido. Comuníquese con soporte.")
                    else:
                        if user == "LContreras" and pwd == "shanks1324":
                            st.session_state.logged_in = True
                            st.session_state.username = "LContreras"
                            st.session_state.rol = "adm"
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                else:
                    if user == "LContreras" and pwd == "shanks1324":
                        st.session_state.logged_in = True
                        st.session_state.username = "LContreras"
                        st.session_state.rol = "adm"
                        st.rerun()
                    else:
                        st.error("Base de datos de usuarios no configurada. Usa la cuenta maestra.")
    st.stop()

# ==========================================
# 5. CONSOLA PRINCIPAL
# ==========================================

col_titulo, col_logout = st.columns([4, 1])
with col_titulo:
    st.title("🛠️ Consola de Gestión Centralizada")
with col_logout:
    st.markdown(f"<div style='text-align: right; color:#3B82F6; font-weight:bold; margin-top:10px;'>👤 {st.session_state.username} ({st.session_state.rol.upper()})</div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.rol = ""
        st.rerun()

rol_actual = st.session_state.rol
pestanas_visibles = ["🔍 Buscar AAEE"]

if rol_actual in ["regular", "adm"]:
    pestanas_visibles.append("📥 Nuevo ID")
    
pestanas_visibles.append("📺 IDs x Canal")

if rol_actual == "adm":
    pestanas_visibles.append("🛡️ Validación Admin")

tabs = st.tabs(pestanas_visibles)
idx_tab = 0

# --- PESTAÑA 1: BUSCAR AAEE ---
with tabs[idx_tab]:
    col_main, col_hist = st.columns([3.5, 1.2])
    
    with col_main:
        busqueda = st.text_input("🔍 Buscar (Compañía, Marca, Producto, ID...):", placeholder="Ej: Caliente...", key="search_universal")
        
        if busqueda and not df.empty:
            cols_filtro = ['Compañía', 'Marca', 'Submarca', 'Producto', 'VersiOn', 'ID']
            mascara = df[cols_filtro].astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            resultados = df[mascara].copy()
            
            if not resultados.empty:
                st.markdown(f"<div style='color: #3B82F6; font-weight: bold; margin-bottom: 10px;'>Resultados encontrados: {len(resultados)}</div>", unsafe_allow_html=True)
                
                html_tabla = """
                <style>
                    :root { --bg: #FFFFFF; --text: #111827; --border: #E5E7EB; --th-bg: #1E3A8A; --th-text: #FFFFFF; --row-alt: #F9FAFB; --btn-bg: #F1F5F9; --btn-border: #CBD5E1; --btn-hover: #E2E8F0; --hover-resaltador: rgba(250, 204, 21, 0.35); }
                    @media (prefers-color-scheme: dark) { :root { --bg: #1F2937; --text: #F9FAFB; --border: #374151; --th-bg: #1E3A8A; --row-alt: #111827; --btn-bg: #374151; --btn-border: #4B5563; --btn-hover: #4B5563; --hover-resaltador: rgba(250, 204, 21, 0.2); } }
                    body { margin: 0; font-family: sans-serif; background-color: transparent; }
                    table { width: 100%; border-collapse: collapse; font-size: 14px; background-color: var(--bg); }
                    th, td { border: 1px solid var(--border); padding: 10px; text-align: left; color: var(--text); transition: background-color 0.1s; }
                    th { background-color: var(--th-bg); color: var(--th-text); text-align: center; }
                    tr:nth-child(even) td { background-color: var(--row-alt); }
                    tr:hover td { background-color: var(--hover-resaltador) !important; color: var(--text) !important; }
                    
                    .btn-c { background: var(--btn-bg); border: 1px solid var(--btn-border); color: var(--text); cursor: pointer; width: 100%; font-weight: 700; border-radius: 4px; padding: 6px; transition: 0.2s; }
                    .btn-c:hover { background: var(--btn-hover); transform: scale(1.02); }
                    .btn-c.copiado { background-color: #10B981 !important; color: white !important; border-color: #059669 !important; }
                    
                    .btn-c.warn { background-color: #FEF08A; border-color: #EAB308; color: #854D0E; }
                    .btn-c.warn:hover { background-color: #FDE047; }
                    @media (prefers-color-scheme: dark) {
                        .btn-c.warn { background-color: #713F12; border-color: #A16207; color: #FEF08A; }
                        .btn-c.warn:hover { background-color: #854D0E; }
                    }
                </style>
                <script>
                    function copiarID(id, desc, version, tipo, boton) {
                        navigator.clipboard.writeText(id);
                        let txtOrig = boton.innerHTML;
                        boton.innerHTML = '¡Copiado!';
                        boton.classList.add('copiado');
                        setTimeout(() => { boton.innerHTML = txtOrig; boton.classList.remove('copiado'); }, 1200);
                        
                        let historial = JSON.parse(localStorage.getItem('aaee_history') || '[]');
                        historial = historial.filter(item => item.id !== id); 
                        historial.unshift({id: id, desc: desc, version: version, tipo: tipo}); 
                        if (historial.length > 20) historial.pop(); 
                        localStorage.setItem('aaee_history', JSON.stringify(historial));
                    }
                </script>
                """
                
                html_tabla += "<table><tr><th width='5%'>Est.</th><th>Compañía</th><th>Marca</th><th>Submarca</th><th>Producto</th><th>Versión</th><th>Tipo</th><th>ID</th></tr>"
                
                for _, f in resultados.iterrows():
                    id_t = str(f['ID'])
                    estado = str(f.get('Estado', 'Confiable'))
                    
                    if estado == 'NO VALIDADO':
                        luz = "<div style='text-align:center; font-size:16px;' title='No Validado'>🟡</div>"
                        clase_btn = "btn-c warn"
                    else:
                        luz = "<div style='text-align:center; font-size:16px;' title='Validado'>🟢</div>"
                        clase_btn = "btn-c"
                        
                    limpiar = lambda x: str(x).replace('nan','N/A').replace("'","\\'").replace('"', '\\"').upper()
                    
                    desc_texto = f"{limpiar(f['Marca'])} | {limpiar(f['Submarca'])} | {limpiar(f['Producto'])}"
                    version_texto = limpiar(f['VersiOn'])
                    tipo_texto = limpiar(f['Tipo'])
                    
                    html_tabla += f"<tr><td>{luz}</td><td>{f['Compañía']}</td><td>{f['Marca']}</td><td>{f['Submarca']}</td><td>{f['Producto']}</td><td>{f['VersiOn']}</td><td>{f['Tipo']}</td><td><button class='{clase_btn}' onclick=\"copiarID('{id_t}', '{desc_texto}', '{version_texto}', '{tipo_texto}', this)\">{id_t}</button></td></tr>"
                
                html_tabla += "</table>"
                components.html(html_tabla, height=60 + (len(resultados) * 55), scrolling=False)
            else:
                st.info("No hay coincidencias en la base de datos.")

    with col_hist:
        html_historial = """
        <style>
            :root { --bg: #FFFFFF; --text: #111827; --border: #E5E7EB; --btn-bg: #F8FAFC; --btn-hover: #EFF6FF; }
            @media (prefers-color-scheme: dark) { :root { --bg: #1F2937; --text: #F9FAFB; --border: #374151; --btn-bg: #111827; --btn-hover: #374151; } }
            body { margin: 0; font-family: sans-serif; background-color: transparent; }
            .history-container { background: var(--bg); border: 2px solid var(--border); border-radius: 10px; padding: 12px; height: 85vh; max-height: 900px; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .history-container::-webkit-scrollbar { width: 6px; }
            .history-container::-webkit-scrollbar-track { background: transparent; }
            .history-container::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }
            .hist-title { font-size: 14px; font-weight: bold; color: var(--text); margin-bottom: 10px; border-bottom: 2px solid var(--border); padding-bottom: 6px; position: sticky; top: 0; background: var(--bg); z-index: 10;}
            
            .btn-hist { display: block; width: 100%; background: var(--btn-bg); border: 1px solid var(--border); padding: 8px 6px; margin-bottom: 6px; border-radius: 6px; cursor: pointer; color: var(--text); transition: 0.2s; overflow: hidden; }
            .btn-hist:hover { border-color: #3B82F6; background: var(--btn-hover); transform: translateY(-2px); box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
            .btn-hist.copiado { background-color: #10B981 !important; color: white !important; border-color: #059669 !important; }
            
            .hist-desc { font-size: 10.5px; color: var(--text); font-weight: 700; text-align: center; padding-bottom: 4px; border-bottom: 1px solid #CBD5E1; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
            .hist-version { font-size: 11.5px; color: var(--text); font-weight: 800; text-align: center; padding-bottom: 4px; border-bottom: 1px solid #CBD5E1; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
            .hist-tipo { font-size: 12.5px; font-weight: 900; color: #3B82F6; letter-spacing: 0.5px; text-transform: uppercase; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
            
            @media (prefers-color-scheme: dark) { 
                .hist-desc, .hist-version { border-bottom-color: #4B5563; }
                .hist-tipo { color: #60A5FA; } 
            }
            .hist-empty { font-size: 12px; color: #94A3B8; text-align: center; padding: 20px 5px; line-height: 1.4;}
        </style>
        <div class='history-container'><div class='hist-title'>🕒 Historial (Clic para copiar)</div><div id='hist-list'></div></div>
        <script>
            let currentHistStr = "";
            function renderizarHistorial() {
                let str = localStorage.getItem('aaee_history') || '[]';
                if (str === currentHistStr) return; 
                currentHistStr = str;
                let historial = JSON.parse(str);
                let contenedor = document.getElementById('hist-list');
                if (historial.length === 0) { contenedor.innerHTML = "<div class='hist-empty'>Copia un ID en tu búsqueda y aparecerá aquí automáticamente.</div>"; return; }
                
                let html = "";
                historial.forEach(item => { 
                    let versionTxt = item.version ? item.version : '-';
                    let tipoTxt = item.tipo ? item.tipo : '-';

                    html += `<button class="btn-hist" onclick="copiarDesdeHistorial('${item.id}', this)" title="${item.desc} | ${versionTxt} | ${tipoTxt}">
                                <div class="hist-desc">${item.desc}</div>
                                <div class="hist-version">${versionTxt}</div>
                                <div class="hist-tipo">${tipoTxt}</div>
                             </button>`; 
                });
                contenedor.innerHTML = html;
            }
            function copiarDesdeHistorial(id, boton) {
                navigator.clipboard.writeText(id); 
                boton.classList.add('copiado');
                setTimeout(() => { boton.classList.remove('copiado'); }, 1200);
            }
            window.onload = renderizarHistorial; setInterval(renderizarHistorial, 800); 
        </script>
        """
        components.html(html_historial, height=950, scrolling=False)
idx_tab += 1

# --- PESTAÑA 2: NUEVO ID ---
if rol_actual in ["regular", "adm"]:
    with tabs[idx_tab]:
        st.subheader("Sugerir Nuevo Registro")
        
        def aplicar_reglas_marca(texto):
            if not texto: return ""
            t = str(texto).upper()
            t = t.replace("&", "Y")
            t = t.replace("'", "").replace("´", "").replace("`", "")
            t = re.sub(r'[^A-Z0-9\-\s]', '', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t

        def selector_o_manual(label, opciones, sufijo_key):
            opc = ["-- Seleccionar --", "INGRESAR NUEVO (MANUAL)"] + sorted(list(opciones.astype(str).unique()))
            sel = st.selectbox(f"{label}:", opc, key=f"sel_{sufijo_key}")
            if sel == "INGRESAR NUEVO (MANUAL)":
                return st.text_input(f"Escriba {label}:", key=f"txt_{sufijo_key}").upper()
            return sel if sel != "-- Seleccionar --" else ""

        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                n_cia = selector_o_manual("Compañía", df['Compañía'], "cia")
                n_mar = selector_o_manual("Marca", df['Marca'], "mar")
                n_mar_sugerida = aplicar_reglas_marca(n_mar)
                n_sub = selector_o_manual("Submarca", df['Submarca'], "sub")
                
            with c2:
                n_pro = selector_o_manual("Producto", df['Producto'], "pro")
                n_ver = st.text_input("Versión (Se auto-completa con la marca)", value=n_mar_sugerida).upper()
                n_id = st.text_input("ID Detección")
                n_tipo = selector_o_manual("Tipo de Spot", df['Tipo'], "tipo")
                
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ingresar y mandar a Validación", type="primary"):
                if n_cia and n_mar and n_id:
                    nuevo_registro = pd.DataFrame([{
                        'Compañía': n_cia, 'Marca': n_mar, 'Submarca': n_sub, 
                        'Producto': n_pro, 'VersiOn': n_ver, 'Tipo': n_tipo, 
                        'ID': n_id, 'Estado': 'NO VALIDADO'
                    }])
                    st.session_state.df_live = pd.concat([nuevo_registro, st.session_state.df_live], ignore_index=True)
                    st.session_state.nuevos_ids = pd.concat([st.session_state.nuevos_ids, nuevo_registro], ignore_index=True)
                    st.success("¡Ingresado correctamente! Aparecerá con luz amarilla hasta ser validado por un Administrador.")
                else:
                    st.error("⚠️ Compañía, Marca e ID son campos obligatorios.")
    idx_tab += 1

# --- PESTAÑA 3: IDs x CANAL ---
with tabs[idx_tab]:
    if not df_canales.empty:
        
        # Función para encapsular y renderizar cualquier canal (cargado o buscado)
        def renderizar_canal(canal_sel):
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

                btn_grilla_html = f"""<a href="{link}" target="_blank" class="btn-grilla" {onclick_action}><div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">{texto_btn}</div></a>"""
            
            # Identificador único para el JS para evitar conflictos si se abren múltiples canales
            uid = re.sub(r'\W+', '', canal_sel)
            
            html_ficha = f"""
            <style>
                :root {{ --bg-card: #F8FAFC; --text: #1E293B; --btn-promo: #0F172A; --btn-text: #FFF; }}
                @media (prefers-color-scheme: dark) {{ :root {{ --bg-card: #1E293B; --text: #F8FAFC; --btn-promo: #374151; }} }}
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
                function cop_{uid}(txt, msg = '✓ Copiado') {{ navigator.clipboard.writeText(txt); let t = document.getElementById('t_{uid}'); t.style.display='block'; t.innerHTML = msg; setTimeout(()=>{{t.style.display='none'}}, 2000); }}
                function cop_ruta(e, txt) {{ navigator.clipboard.writeText(txt); let t = document.getElementById('t_{uid}'); t.style.display='block'; t.innerHTML = '✓ Ruta copiada (Pégala en tu explorador de red)'; setTimeout(()=>{{t.style.display='none'}}, 3500); }}
            </script>
            <div class="card" onclick="cop_{uid}('{texto_monitor}')">
                <div class="info-txt"><b>{canal_sel}</b><br>Network: {clean(info.get('Network'))} | Tipo: {clean(info.get('Tipo'))}<br>ID: {station_id} | Server: {clean(info.get('Server'))}</div>
                <div class="logo-img"><img src="{clean(info.get('LOGO_URL'))}" onerror="this.style.display='none'"></div>
            </div>
            {btn_grilla_html}
            <button class="btn-promo" onclick="cop_{uid}('{tag_auto}', '✓ Tag de Autopromo copiado')">TAG AUTOPROMO:<br>{tag_auto}</button>
            <div id="t_{uid}" class="toast"></div>
            """
            components.html(html_ficha, height=115, scrolling=False)

            if not df_ids_canal.empty and 'CANAL' in df_ids_canal.columns:
                ids_c = df_ids_canal[df_ids_canal['CANAL'] == canal_sel]
                if not ids_c.empty:
                    # El menú desplegable (Expander)
                    with st.expander(f"📂 Ver IDs de Operación - {canal_sel}"):
                        hashes = ids_c['CODIGO HASH'].dropna().unique()
                        for h in hashes:
                            st.markdown(f"**{h}**")
                            df_h = ids_c[ids_c['CODIGO HASH'] == h]
                            
                            html_ids = """
                            <style>
                                :root { --bg: #FFFFFF; --text: #111827; --border: #E5E7EB; --th-bg: #F8FAFC; --btn-bg: #FFF; --btn-border: #CBD5E1; --btn-hover: #EFF6FF; --hover-resaltador: rgba(250, 204, 21, 0.35); }
                                @media (prefers-color-scheme: dark) { :root { --bg: #1F2937; --text: #F9FAFB; --border: #374151; --th-bg: #111827; --btn-bg: #374151; --btn-border: #4B5563; --btn-hover: #4B5563; --hover-resaltador: rgba(250, 204, 21, 0.2); } }
                                body{margin:0; background: transparent;} table{width:100%;border-collapse:collapse;font-size:13px;font-family:sans-serif; background: var(--bg);} th,td{border:1px solid var(--border);padding:8px;text-align:left; color: var(--text); transition: background-color 0.1s;} th{background: var(--th-bg);} tr:hover td { background-color: var(--hover-resaltador) !important; color: var(--text) !important; }
                                .btn-i{width:100%;cursor:pointer;font-weight:700;background:var(--btn-bg);border:1px solid var(--btn-border); color: var(--text); border-radius:4px;padding:4px; transition:0.2s;} .btn-i:hover{background:var(--btn-hover); border-color:#3B82F6; transform: scale(1.02);} .btn-i.copiado { background-color: #10B981 !important; color: white !important; border-color: #059669 !important; }
                            </style>
                            <script>function copiarID(texto, boton) { navigator.clipboard.writeText(texto); let txtOrig = boton.innerHTML; boton.innerHTML = '¡Copiado!'; boton.classList.add('copiado'); setTimeout(() => { boton.innerHTML = txtOrig; boton.classList.remove('copiado'); }, 1200); }</script>
                            """
                            html_ids += "<table><tr><th width='20%'>Tipo</th><th width='60%'>Descripción</th><th width='20%'>ID</th></tr>"
                            for _, r in df_h.iterrows():
                                v_id = str(r['ID'])
                                html_ids += f"<tr><td>{r['TIPO']}</td><td>{r['DESCRIPCION']}</td><td><button class='btn-i' onclick=\"copiarID('{v_id}', this)\">{v_id}</button></td></tr>"
                            html_ids += "</table>"
                            components.html(html_ids, height=60 + (len(df_h) * 55), scrolling=False)
                else:
                    st.info(f"Sin registros de IDs de operación para el canal {canal_sel}.")
        
        # 1. CARGA AUTOMÁTICA DEL USUARIO LOGUEADO
        if not df_carga.empty and 'USUARIO' in df_carga.columns and 'CANAL' in df_carga.columns:
            usuario_actual = st.session_state.username.strip().upper()
            carga_user = df_carga[df_carga['USUARIO'].astype(str).str.strip().str.upper() == usuario_actual]
            canales_usuario = carga_user['CANAL'].dropna().unique().tolist()
            
            # Validamos que los canales existan en nuestra base de datos
            canales_validos = [c for c in canales_usuario if c in df_canales['CANAL'].values]

            if canales_validos:
                st.write(f"### 📋 Tus Canales Asignados ({len(canales_validos)})")
                for c in canales_validos:
                    renderizar_canal(c)
                    st.markdown("<br>", unsafe_allow_html=True)
                st.divider()

        # 2. BUSCADOR MANUAL PARA OTROS CANALES
        st.write("### 🔍 Buscar Canal Manualmente")
        lista_c = ["-- Seleccionar --"] + sorted(df_canales['CANAL'].dropna().unique().tolist())
        canal_sel = st.selectbox("Canal:", lista_c, label_visibility="collapsed")

        if canal_sel != "-- Seleccionar --":
            renderizar_canal(canal_sel)
            
idx_tab += 1

# --- PESTAÑA 4: ADMIN ---
if rol_actual == "adm":
    with tabs[idx_tab]:
        st.subheader("🛡️ Panel de Validación Admin")
        
        st.write("### 📥 Bandeja de Pendientes (Luz Amarilla)")
        if not st.session_state.nuevos_ids.empty:
            st.info("Revisa los IDs ingresados hoy. Al hacer clic en 'Validar', cambiarán a luz verde en el buscador general.")
            
            for idx, row in st.session_state.nuevos_ids.iterrows():
                c1, c2 = st.columns([5, 1])
                c1.warning(f"🟡 **Marca:** {row['Marca']} | **Versión:** {row['VersiOn']} | **ID:** `{row['ID']}`")
                
                if c2.button("Validar ✅", key=f"apr_{idx}", use_container_width=True):
                    st.session_state.df_live.loc[st.session_state.df_live['ID'] == row['ID'], 'Estado'] = 'Confiable'
                    st.session_state.nuevos_ids = st.session_state.nuevos_ids.drop(idx)
                    st.rerun()
        else:
            st.success("Todo limpio. No hay IDs pendientes por validar en esta sesión.")
            
        st.divider()
        st.write("### 📚 Base Madre de IDs (Confiables en Drive)")
        if not df_base.empty:
            st.dataframe(df_base[['Compañía', 'Marca', 'Producto', 'ID', 'Estado']], hide_index=True, height=400)
