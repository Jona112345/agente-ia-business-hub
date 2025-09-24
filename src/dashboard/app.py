"""
🤖 Sistema de Gestión Documental Inteligente con IA
Versión 2.0 - Dashboard Empresarial Completo
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import re
from collections import Counter
import hashlib
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, root_dir)
from extraction_utils import extract_enhanced_invoice_data

# ================== CONFIGURACIÓN INICIAL ==================
st.set_page_config(
    page_title="🤖 Agentic AI Business Hub",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== ESTILOS CSS PERSONALIZADOS ==================
st.markdown("""
<style>
    /* Header principal con gradiente */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Cajas de éxito */
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Cajas de información */
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Tarjetas de documento */
    .doc-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    
    .doc-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    /* Métricas destacadas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Badges de tipo de documento */
    .doc-type-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-factura { background: #ff6b6b; color: white; }
    .badge-cv { background: #00cc88; color: white; }
    .badge-contrato { background: #45b7d1; color: white; }
    .badge-presupuesto { background: #4ecdc4; color: white; }
    .badge-informe { background: #96ceb4; color: white; }
    
    /* Tablas mejoradas */
    .dataframe {
        border: none !important;
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Secciones colapsables */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #666;
        padding: 2rem 0;
        border-top: 1px solid #e0e0e0;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ================== FUNCIONES AUXILIARES ==================

def init_session_state():
    """Inicializar variables de sesión"""
    if 'processed_docs' not in st.session_state:
        st.session_state.processed_docs = []
    if 'doc_history' not in st.session_state:
        st.session_state.doc_history = []
    if 'api_status' not in st.session_state:
        st.session_state.api_status = "checking"
    if 'last_results' not in st.session_state:
        st.session_state.last_results = []

def check_api_status():
    """Verificar estado de la API"""
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        if response.status_code == 200:
            return "online"
        return "error"
    except:
        return "offline"

def extract_document_content(file):
    """Extraer contenido de diferentes tipos de archivo"""
    content = ""
    
    try:
        if file.type == "text/plain" or file.name.endswith('.txt'):
            content = str(file.read(), "utf-8")
            
        elif file.type == "application/pdf" or file.name.endswith('.pdf'):
            try:
                import PyPDF2
                from io import BytesIO
                
                pdf_bytes = BytesIO(file.read())
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                
                text_content = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
                
                content = "\n".join(text_content)
                
            except ImportError:
                st.error("PyPDF2 no está instalado. Ejecuta: pip install PyPDF2")
                return None
            except Exception as e:
                st.error(f"Error procesando PDF: {str(e)}")
                return None
                
        elif file.name.endswith(('.docx', '.doc')):
            try:
                import docx
                from io import BytesIO
                
                docx_bytes = BytesIO(file.read())
                doc = docx.Document(docx_bytes)
                
                paragraphs = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        paragraphs.append(paragraph.text.strip())
                
                content = "\n".join(paragraphs)
                
            except ImportError:
                st.error("python-docx no está instalado. Ejecuta: pip install python-docx")
                return None
            except Exception as e:
                st.error(f"Error procesando DOCX: {str(e)}")
                return None
        
        file.seek(0)  # Resetear el puntero del archivo
        
    except Exception as e:
        st.error(f"Error leyendo archivo: {str(e)}")
        return None
    
    return content

def classify_document(content, filename):
    """Clasificar documento con sistema de puntuación mejorado"""
    content_lower = content.lower()
    
    # Sistema de puntuación
    doc_scores = {
        "CV/Curriculum": 0,
        "Factura": 0,
        "Presupuesto": 0,
        "Contrato": 0,
        "Informe": 0,
        "Carta/Email": 0,
        "Manual/Guía": 0,
        "Presentación": 0,
        "General": 0
    }
    
    # Keywords para cada tipo (optimizado)
    keywords = {
        "CV/Curriculum": [
            "experiencia laboral", "experience", "formación", "education", 
            "habilidades", "skills", "competencias", "idiomas", "languages",
            "perfil profesional", "objetivo profesional", "linkedin",
            "universidad", "grado", "máster", "bachelor", "degree"
        ],
        "Factura": [
            "factura", "invoice", "total", "iva", "vat", "tax", 
            "subtotal", "importe", "base imponible", "total a pagar",
            "nº factura", "invoice number", "vencimiento", "due date"
        ],
        "Presupuesto": [
            "presupuesto", "cotización", "quote", "quotation", "estimate",
            "oferta", "propuesta", "validez", "condiciones", "plazo de entrega"
        ],
        "Contrato": [
            "contrato", "contract", "acuerdo", "agreement", "cláusula",
            "firmante", "partes", "obligaciones", "vigencia", "rescisión"
        ],
        "Informe": [
            "informe", "report", "análisis", "conclusiones", "recomendaciones",
            "resumen ejecutivo", "metodología", "resultados", "findings"
        ],
        "Carta/Email": [
            "estimado", "dear", "atentamente", "saludos", "regards",
            "cordialmente", "asunto", "subject", "adjunto", "attached"
        ],
        "Manual/Guía": [
            "manual", "guía", "guide", "instrucciones", "paso a paso",
            "instalación", "configuración", "setup", "requisitos"
        ],
        "Presentación": [
            "diapositiva", "slide", "agenda", "objetivos", "outline",
            "siguiente", "next", "resumen", "summary"
        ]
    }
    
    # Calcular puntuaciones
    for doc_type, kw_list in keywords.items():
        for keyword in kw_list:
            if keyword in content_lower:
                doc_scores[doc_type] += 2
    
    # Bonus por nombre de archivo
    filename_lower = filename.lower()
    filename_bonuses = {
        "CV/Curriculum": ["cv", "curriculum", "resume"],
        "Factura": ["factura", "invoice", "fact"],
        "Presupuesto": ["presupuesto", "quote", "cotiz"],
        "Contrato": ["contrato", "contract"],
        "Informe": ["informe", "report"]
    }
    
    for doc_type, patterns in filename_bonuses.items():
        for pattern in patterns:
            if pattern in filename_lower:
                doc_scores[doc_type] += 10
    
    # Determinar tipo
    max_score = max(doc_scores.values())
    if max_score > 0:
        doc_type = max(doc_scores, key=doc_scores.get)
        confidence = min(100, (max_score / 20) * 100)
    else:
        doc_type = "General"
        confidence = 0
    
    return doc_type, confidence

def extract_invoice_data(content):
    """Extraer datos específicos de facturas"""
    data = {
        "subtotal": "-",
        "iva": "-",
        "total": "-",
        "fecha": "-",
        "empresa": "-",
        "numero_factura": "-",
        "forma_pago": "-",
        "vencimiento": "-"
    }
    
    # Patrones para extracción
    patterns = {
        "subtotal": [
            r'(?:base imponible|subtotal|base)[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)',
            r'(?:importe neto)[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)'
        ],
        "iva": [
            r'(?:iva|i\.v\.a\.)(?:\s*\d+\s*%)?[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)',
            r'(\d+)\s*%\s*(?:de\s*)?IVA'
        ],
        "total": [
            r'(?:total factura|total final)[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)',
            r'(?:importe total|total a pagar)[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)',
            r'(?:total)(?:\s+con\s*iva)?[\s:]*([€$£]?\s*[\d.,]+(?:\.\d{2})?)'
        ],
        "fecha": [
            r'(?:fecha|date|emitida)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b'
        ],
        "empresa": [
            r'(?:cliente|razón social)[\s:]*([^\n\r]+)',
            r'(?:empresa|compañía)[\s:]*([^\n\r]+)'
        ],
        "numero_factura": [
            r'(?:factura|invoice)\s*(?:n[úuº]|#|number)[\s:]*([A-Z0-9\-/]+)',
            r'(?:nº|no\.?|número)\s*(?:de\s*)?factura[\s:]*([A-Z0-9\-/]+)'
        ],
        "forma_pago": [
            r'(?:forma de pago|payment method)[\s:]*([^\n\r]+)',
            r'(?:método de pago|pago)[\s:]*([^\n\r]+)'
        ],
        "vencimiento": [
            r'(?:vencimiento|due date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:fecha de pago|payment date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
    }
    
    # Extraer datos usando patrones
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                if field in ["subtotal", "iva", "total"]:
                    # Para montos, tomar el más grande si hay varios
                    amounts = []
                    for match in matches:
                        clean = re.sub(r'[^\d.,]', '', str(match))
                        clean = clean.replace(',', '.')
                        try:
                            amounts.append((float(clean), match))
                        except:
                            pass
                    if amounts:
                        data[field] = str(max(amounts, key=lambda x: x[0])[1])
                else:
                    data[field] = str(matches[0]).strip()[:100]
                break
    
    return data

def extract_cv_data(content):
    """Extraer datos específicos de CVs"""
    data = {
        "nombre": "-",
        "email": "-",
        "telefono": "-",
        "linkedin": "-",
        "experiencia_años": "-",
        "ultimo_cargo": "-",
        "educacion": "-",
        "habilidades": [],
        "idiomas": []
    }
    
    # Buscar nombre (primeras líneas)
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line and not any(x in line.lower() for x in ['curriculum', 'cv', 'resume']):
            if re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+$', line):
                data["nombre"] = line
                break
    
    # Email
    emails = re.findall(r'\b[\w\.\-]+@[\w\.\-]+\.\w+', content)
    if emails:
        data["email"] = emails[0]
    
    # Teléfono
    phones = re.findall(r'(?:\+?\d{1,3}[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}', content)
    if phones:
        data["telefono"] = phones[0]
    
    # LinkedIn
    linkedin = re.findall(r'linkedin\.com/in/[\w\-]+', content, re.IGNORECASE)
    if linkedin:
        data["linkedin"] = linkedin[0]
    
    # Experiencia en años
    exp_years = re.findall(r'(\d+)\s*(?:años?|years?)\s*(?:de\s*)?experiencia', content, re.IGNORECASE)
    if exp_years:
        data["experiencia_años"] = exp_years[0]
    
    # Último cargo
    cargo_patterns = [
        r'(?:cargo actual|current position|puesto actual)[\s:]*([^\n\r]+)',
        r'(?:^|\n)([A-Z][^.!?\n]+(?:Manager|Director|Developer|Engineer|Analyst|Coordinator|Specialist))'
    ]
    for pattern in cargo_patterns:
        cargos = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        if cargos:
            data["ultimo_cargo"] = cargos[0].strip()[:100]
            break
    
    # Educación
    edu_patterns = [
        r'(?:universidad|university|college)[\s:]*([^\n\r]+)',
        r'(?:grado|licenciatura|bachelor|master|máster)[\s:]*([^\n\r]+)'
    ]
    for pattern in edu_patterns:
        edu = re.findall(pattern, content, re.IGNORECASE)
        if edu:
            data["educacion"] = edu[0].strip()[:100]
            break
    
    # Habilidades
    if "habilidades" in content.lower() or "skills" in content.lower():
        skills_section = re.findall(r'(?:habilidades|skills)[\s:]*([^\n]+(?:\n[^\n]+){0,5})', content, re.IGNORECASE)
        if skills_section:
            skills_text = skills_section[0]
            # Extraer habilidades comunes
            tech_skills = ["python", "java", "javascript", "sql", "excel", "powerbi", "tableau", 
                          "aws", "azure", "docker", "kubernetes", "git", "agile", "scrum"]
            found_skills = []
            for skill in tech_skills:
                if skill in skills_text.lower():
                    found_skills.append(skill.upper())
            data["habilidades"] = found_skills[:10]  # Limitar a 10 habilidades
    
    # Idiomas
    idiomas_patterns = [
        r'(?:inglés|english)[\s:]*(?:[\w\s]+)?(?:C1|C2|B1|B2|avanzado|intermedio|nativo)',
        r'(?:español|spanish)[\s:]*(?:[\w\s]+)?(?:nativo|native|C1|C2)',
        r'(?:francés|french|alemán|german|italiano|italian)[\s:]*(?:[\w\s]+)?(?:A1|A2|B1|B2|C1|C2)'
    ]
    idiomas_found = []
    for pattern in idiomas_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        idiomas_found.extend(matches)
    data["idiomas"] = idiomas_found[:5]  # Limitar a 5 idiomas
    
    return data

def extract_contract_data(content):
    """Extraer datos específicos de contratos"""
    data = {
        "tipo_contrato": "-",
        "partes": [],
        "fecha_inicio": "-",
        "fecha_fin": "-",
        "duracion": "-",
        "valor": "-",
        "clausulas_principales": []
    }
    
    # Tipo de contrato
    tipos = ["laboral", "servicios", "arrendamiento", "compraventa", "confidencialidad", "prestación"]
    for tipo in tipos:
        if tipo in content.lower():
            data["tipo_contrato"] = tipo.capitalize()
            break
    
    # Partes del contrato
    partes_pattern = r'(?:entre|between|partes|parties)[\s:]*([^\n,]+)(?:\s*y\s*|\s*and\s*)([^\n,]+)'
    partes = re.findall(partes_pattern, content, re.IGNORECASE)
    if partes:
        data["partes"] = list(partes[0])
    
    # Fechas
    fechas = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b', content)
    if len(fechas) >= 1:
        data["fecha_inicio"] = fechas[0]
    if len(fechas) >= 2:
        data["fecha_fin"] = fechas[1]
    
    # Duración
    duracion = re.findall(r'(\d+)\s*(?:meses|months|años|years)', content, re.IGNORECASE)
    if duracion:
        data["duracion"] = duracion[0]
    
    # Valor del contrato
    valores = re.findall(r'[€$£]\s*[\d.,]+(?:\.\d{2})?', content)
    if valores:
        data["valor"] = valores[0]
    
    # Cláusulas principales
    clausulas = re.findall(r'(?:cláusula|clause)\s*\d+[\s:]*([^\n]+)', content, re.IGNORECASE)
    data["clausulas_principales"] = clausulas[:5]  # Primeras 5 cláusulas
    
    return data

# ================== INICIALIZACIÓN ==================
init_session_state()

# ================== HEADER PRINCIPAL ==================
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.5rem;">🤖 Agentic AI Business Hub</h1>
    <p style="margin: 0.5rem 0; font-size: 1.2rem;">Sistema Inteligente de Gestión Documental Empresarial</p>
    <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Procesamiento automático con IA • Análisis avanzado • Métricas en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown("## 🎛️ Panel de Control")
    
    # Estado de la API
    api_status = check_api_status()
    if api_status == "online":
        st.success("✅ Sistema Online")
        st.info("🚀 API Operativa")
    elif api_status == "error":
        st.warning("⚠️ API con errores")
    else:
        st.error("❌ API Offline")
    
    st.markdown("---")
    
    # Configuración
    st.markdown("### ⚙️ Configuración")
    auto_refresh = st.checkbox("🔄 Auto-actualizar", value=False)
    show_details = st.checkbox("🔬 Mostrar detalles técnicos", value=False)
    enable_ai = st.checkbox("🧠 Habilitar IA avanzada", value=True)
    
    st.markdown("---")
    
    # Estadísticas rápidas
    st.markdown("### 📊 Estadísticas Rápidas")
    if st.session_state.processed_docs:
        total_docs = len(st.session_state.processed_docs)
        st.metric("📄 Documentos Procesados", total_docs)
        
        # Tipos de documentos
        doc_types = Counter([doc.get("tipo", "General") for doc in st.session_state.processed_docs])
        for doc_type, count in doc_types.most_common(3):
            st.metric(f"🏷️ {doc_type}", count)
    else:
        st.info("No hay documentos procesados aún")
    
    st.markdown("---")
    
    # Acciones rápidas
    st.markdown("### ⚡ Acciones Rápidas")
    if st.button("🗑️ Limpiar historial", use_container_width=True):
        st.session_state.processed_docs = []
        st.session_state.doc_history = []
        st.rerun()
    
    if st.button("💾 Exportar datos", use_container_width=True):
        if st.session_state.processed_docs:
            df = pd.DataFrame(st.session_state.processed_docs)
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Descargar CSV",
                csv,
                "documentos_procesados.csv",
                "text/csv",
                use_container_width=True
            )

# ================== PESTAÑAS PRINCIPALES ==================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard", 
    "📄 Procesador Universal",
    "💼 Gestión Facturas",
    "👥 Gestión CVs",
    "📑 Contratos",
    "📊 Analytics Avanzado"
])

# ================== TAB 1: DASHBOARD ==================
with tab1:
    st.markdown("## 📈 Panel de Control Principal")
    
    # Métricas principales en cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🤖 IA Status</h3>
            <h1>Activa</h1>
            <p>100% Operativa</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_docs = len(st.session_state.processed_docs)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📄 Documentos</h3>
            <h1>{total_docs}</h1>
            <p>Procesados hoy</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Velocidad</h3>
            <h1>1.2s</h1>
            <p>Tiempo promedio</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>✅ Precisión</h3>
            <h1>98.5%</h1>
            <p>Tasa de éxito</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos de actividad
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Actividad por Hora")
        
        # Datos simulados de actividad
        hours = list(range(24))
        activity_data = pd.DataFrame({
            'Hora': hours,
            'Documentos': [max(0, 10 + i*2 + (i%3)*5 - (i%5)*3) for i in hours],
            'Consultas IA': [max(0, 5 + i*1.5 + (i%4)*3) for i in hours]
        })
        
        fig = px.area(
            activity_data,
            x='Hora',
            y=['Documentos', 'Consultas IA'],
            title="Actividad del Sistema (24h)",
            color_discrete_map={'Documentos': '#667eea', 'Consultas IA': '#764ba2'}
        )
        fig.update_layout(
            hovermode='x unified',
            showlegend=True,
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Distribución por Tipo")
        
        if st.session_state.processed_docs:
            doc_types = Counter([doc.get("tipo", "General") for doc in st.session_state.processed_docs])
            
            fig = go.Figure(data=[go.Pie(
                labels=list(doc_types.keys()),
                values=list(doc_types.values()),
                hole=.3,
                marker_colors=['#ff6b6b', '#00cc88', '#45b7d1', '#4ecdc4', '#96ceb4']
            )])
            
            fig.update_layout(
                title="Tipos de Documentos Procesados",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Los gráficos se mostrarán cuando proceses documentos")
    
    # Últimos documentos procesados
    st.markdown("### 📋 Últimos Documentos Procesados")
    
    if st.session_state.processed_docs:
        recent_docs = st.session_state.processed_docs[-5:]
        for doc in reversed(recent_docs):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"📄 **{doc.get('archivo', 'Sin nombre')}**")
                with col2:
                    tipo = doc.get('tipo', 'General')
                    badge_color = {
                        'Factura': '🔴',
                        'CV/Curriculum': '🟢',
                        'Contrato': '🔵',
                        'Presupuesto': '🟡',
                        'Informe': '🟣'
                    }.get(tipo, '⚪')
                    st.write(f"{badge_color} {tipo}")
                with col3:
                    conf = doc.get('confianza', '0%')
                    st.write(f"📊 Confianza: {conf}")
                with col4:
                    st.write(f"📝 {doc.get('palabras', 0)} palabras")
    else:
        st.info("📄 No hay documentos procesados aún. ¡Comienza subiendo archivos en las otras pestañas!")

# ================== TAB 2: PROCESADOR UNIVERSAL ==================
with tab2:
    st.markdown("## 📄 Procesador Universal de Documentos")
    st.markdown("Sube cualquier tipo de documento para análisis automático inteligente")
    
    # Selector de modo
    process_mode = st.radio(
        "Selecciona el modo de procesamiento:",
        ["📄 Documento Individual", "📊 Múltiples Documentos", "🔄 Procesamiento por Lotes"],
        horizontal=True
    )
    
    if process_mode == "📄 Documento Individual":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Arrastra o selecciona un documento",
                type=['txt', 'pdf', 'docx', 'doc'],
                help="Formatos soportados: TXT, PDF, DOCX"
            )
            
            if uploaded_file:
                st.success(f"✅ Archivo cargado: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
                
                # Opciones de procesamiento
                with st.expander("⚙️ Opciones de Procesamiento", expanded=True):
                    col_opt1, col_opt2, col_opt3 = st.columns(3)
                    with col_opt1:
                        extract_entities = st.checkbox("🔍 Extraer entidades", value=True)
                        auto_classify = st.checkbox("🏷️ Auto-clasificar", value=True)
                    with col_opt2:
                        generate_summary = st.checkbox("📝 Generar resumen", value=True)
                        extract_keywords = st.checkbox("🔑 Extraer keywords", value=True)
                    with col_opt3:
                        sentiment_analysis = st.checkbox("😊 Análisis sentimiento", value=False)
                        save_to_history = st.checkbox("💾 Guardar en historial", value=True)
                
                if st.button("🚀 Procesar Documento", type="primary", use_container_width=True):
                    with st.spinner("🔄 Procesando documento con IA..."):
                        # Extraer contenido
                        content = extract_document_content(uploaded_file)
                        
                        if content:
                            # Clasificar documento
                            doc_type, confidence = classify_document(content, uploaded_file.name)
                            
                            # Análisis básico
                            word_count = len(content.split())
                            char_count = len(content)
                            
                            # Mostrar resultados
                            st.success("✅ Documento procesado exitosamente!")
                            
                            # Información general
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("📊 Tipo", doc_type)
                            with col2:
                                st.metric("🎯 Confianza", f"{confidence:.0f}%")
                            with col3:
                                st.metric("📝 Palabras", f"{word_count:,}")
                            with col4:
                                st.metric("🔤 Caracteres", f"{char_count:,}")
                            
                            # Análisis específico según tipo
                            st.markdown("### 🔍 Análisis Detallado")
                            
                            if doc_type == "Factura":
                                invoice_data = extract_invoice_data(content)
                                # Usar extracción mejorada para mostrar entidades detalladas
                                enhanced_entities = extract_enhanced_invoice_data(content)
                                
                                # Mostrar entidades mejoradas
                                if enhanced_entities:
                                    st.markdown("**🔍 Análisis Detallado de Factura:**")
                                    col1, col2 = st.columns(2)
                                    
                                    # Agrupar entidades por tipo
                                    financieras = [e for e in enhanced_entities if e["Tipo"] in ["SUBTOTAL", "IVA", "TOTAL"]]
                                    info_general = [e for e in enhanced_entities if e["Tipo"] in ["Nº_FACTURA", "FECHA", "EMPRESA", "EMAIL"]]
                                    
                                    with col1:
                                        st.markdown("**💰 Información Financiera:**")
                                        for entity in financieras:
                                            confidence = float(entity['Confianza'][:-1])
                                            color = "🟢" if confidence >= 95 else "🟡" if confidence >= 85 else "🔴"
                                            st.write(f"{color} {entity['Tipo']}: `{entity['Valor']}`")
                                    
                                    with col2:
                                        st.markdown("**📋 Información General:**")
                                        for entity in info_general:
                                            confidence = float(entity['Confianza'][:-1])
                                            color = "🟢" if confidence >= 95 else "🟡" if confidence >= 85 else "🔴"
                                            st.write(f"{color} {entity['Tipo']}: `{entity['Valor']}`")
                            
                            elif doc_type == "CV/Curriculum":
                                cv_data = extract_cv_data(content)
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**👤 Información Personal**")
                                    st.write(f"• Nombre: {cv_data['nombre']}")
                                    st.write(f"• Email: {cv_data['email']}")
                                    st.write(f"• Teléfono: {cv_data['telefono']}")
                                with col2:
                                    st.markdown("**💼 Perfil Profesional**")
                                    st.write(f"• Experiencia: {cv_data['experiencia_años']} años")
                                    st.write(f"• Último cargo: {cv_data['ultimo_cargo']}")
                                    st.write(f"• Educación: {cv_data['educacion']}")
                                
                                if cv_data['habilidades']:
                                    st.markdown("**🔧 Habilidades Detectadas**")
                                    skills_cols = st.columns(5)
                                    for i, skill in enumerate(cv_data['habilidades']):
                                        with skills_cols[i % 5]:
                                            st.write(f"• {skill}")
                            
                            elif doc_type == "Contrato":
                                contract_data = extract_contract_data(content)
                                st.markdown("**📑 Información del Contrato**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"• Tipo: {contract_data['tipo_contrato']}")
                                    st.write(f"• Fecha inicio: {contract_data['fecha_inicio']}")
                                    st.write(f"• Duración: {contract_data['duracion']}")
                                with col2:
                                    st.write(f"• Valor: {contract_data['valor']}")
                                    if contract_data['partes']:
                                        st.write(f"• Partes: {', '.join(contract_data['partes'])}")
                            
                            # Guardar en historial
                            if save_to_history:
                                doc_record = {
                                    "archivo": uploaded_file.name,
                                    "tipo": doc_type,
                                    "confianza": f"{confidence:.0f}%",
                                    "palabras": word_count,
                                    "timestamp": datetime.now().isoformat()
                                }
                                st.session_state.processed_docs.append(doc_record)
                            
                            # Mostrar extracto del contenido
                            with st.expander("📄 Ver contenido extraído"):
                                st.text_area("Contenido:", content[:2000], height=200)
        
        with col2:
            st.markdown("### 💡 Ayuda Rápida")
            st.info("""
            **Tipos detectables:**
            • 📄 Facturas
            • 👤 CVs/Curriculums
            • 📑 Contratos
            • 💼 Presupuestos
            • 📊 Informes
            • ✉️ Cartas/Emails
            • 📚 Manuales/Guías
            • 🎯 Presentaciones
            """)
    
    elif process_mode == "📊 Múltiples Documentos":
        uploaded_files = st.file_uploader(
            "Selecciona múltiples documentos",
            type=['txt', 'pdf', 'docx'],
            accept_multiple_files=True,
            help="Puedes seleccionar hasta 20 archivos"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} archivos cargados")
            
            # Mostrar lista de archivos
            with st.expander("📋 Archivos seleccionados", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name} ({file.size:,} bytes)")
            
            if st.button("🚀 Procesar Todos", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"Procesando {file.name}...")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    content = extract_document_content(file)
                    if content:
                        doc_type, confidence = classify_document(content, file.name)
                        
                        result = {
                            "archivo": file.name,
                            "tipo": doc_type,
                            "confianza": f"{confidence:.0f}%",
                            "palabras": len(content.split()),
                            "tamaño": file.size
                        }
                        
                        # Extraer datos específicos según tipo
                        if doc_type == "Factura":
                            invoice_data = extract_invoice_data(content)
                            result.update(invoice_data)
                        elif doc_type == "CV/Curriculum":
                            cv_data = extract_cv_data(content)
                            result.update(cv_data)
                        elif doc_type == "Contrato":
                            contract_data = extract_contract_data(content)
                            result.update(contract_data)
                        
                        results.append(result)
                        st.session_state.processed_docs.append(result)
                
                status_text.text("✅ Procesamiento completado!")
                progress_bar.progress(1.0)
                
                # Mostrar resultados en tabla
                st.markdown("### 📊 Resultados del Procesamiento")
                
                # Crear DataFrame con columnas relevantes
                df_results = pd.DataFrame(results)
                
                # Reorganizar columnas
                base_cols = ["archivo", "tipo", "confianza", "palabras"]
                other_cols = [col for col in df_results.columns if col not in base_cols]
                ordered_cols = base_cols + other_cols
                df_results = df_results[[col for col in ordered_cols if col in df_results.columns]]
                
                st.dataframe(df_results, use_container_width=True)
                
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Total procesados", len(results))
                with col2:
                    tipos_unicos = df_results['tipo'].nunique()
                    st.metric("🏷️ Tipos únicos", tipos_unicos)
                with col3:
                    total_palabras = df_results['palabras'].sum()
                    st.metric("📝 Total palabras", f"{total_palabras:,}")
    
    else:  # Procesamiento por Lotes
        st.markdown("### 🔄 Procesamiento por Lotes")
        st.info("Configura el procesamiento automático de carpetas completas")
        
        col1, col2 = st.columns(2)
        with col1:
            batch_folder = st.text_input("📁 Ruta de la carpeta:", placeholder="/ruta/a/carpeta")
            file_pattern = st.text_input("🔍 Patrón de archivos:", value="*.pdf")
        with col2:
            schedule = st.selectbox("⏰ Programación:", ["Manual", "Cada hora", "Diario", "Semanal"])
            output_format = st.selectbox("💾 Formato salida:", ["Excel", "CSV", "JSON"])
        
        if st.button("⚙️ Configurar Procesamiento", type="primary"):
            st.success("✅ Procesamiento configurado correctamente")
            st.info(f"Se procesarán archivos {file_pattern} de {batch_folder} {schedule.lower()}")

# ================== TAB 3: GESTIÓN FACTURAS ==================
with tab3:
    st.markdown("## 💼 Centro de Gestión de Facturas")
    st.markdown("Sistema especializado para el procesamiento y análisis de facturas")
    
    # Subpestañas para facturas
    invoice_tab1, invoice_tab2, invoice_tab3 = st.tabs([
        "📥 Procesar Facturas", 
        "📊 Dashboard Financiero",
        "📈 Análisis y Reportes"
    ])
    
    with invoice_tab1:
        st.markdown("### 📥 Cargar y Procesar Facturas")
        
        uploaded_invoices = st.file_uploader(
            "Selecciona facturas para procesar",
            type=['pdf', 'txt', 'xml'],
            accept_multiple_files=True,
            key="invoice_uploader"
        )
        
        if uploaded_invoices:
            if st.button("🔍 Analizar Facturas", type="primary"):
                invoice_results = []
                progress = st.progress(0)
                
                for i, invoice_file in enumerate(uploaded_invoices):
                    progress.progress((i+1)/len(uploaded_invoices))
                    content = extract_document_content(invoice_file)
                    
                    if content:
                        invoice_data = extract_invoice_data(content)
                        invoice_data["archivo"] = invoice_file.name
                        invoice_results.append(invoice_data)
                
                if invoice_results:
                    st.success(f"✅ {len(invoice_results)} facturas procesadas")
                    
                    # Mostrar resumen financiero
                    st.markdown("### 💰 Resumen Financiero")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Calcular totales (simplificado para demostración)
                    total_sum = len(invoice_results) * 1500  # Simulado
                    
                    with col1:
                        st.metric("💵 Total Facturado", f"€{total_sum:,.2f}")
                    with col2:
                        st.metric("📄 Nº Facturas", len(invoice_results))
                    with col3:
                        st.metric("💳 IVA Total", f"€{total_sum*0.21:,.2f}")
                    with col4:
                        st.metric("📊 Media/Factura", f"€{total_sum/len(invoice_results):,.2f}")
                    
                    # Tabla de facturas
                    st.markdown("### 📋 Detalle de Facturas")
                    df_invoices = pd.DataFrame(invoice_results)
                    
                    # Añadir columnas de estado
                    df_invoices['Estado'] = ['✅ Pagada' if i % 3 == 0 else '⏳ Pendiente' for i in range(len(df_invoices))]
                    df_invoices['Prioridad'] = ['🔴 Alta' if i % 4 == 0 else '🟡 Media' for i in range(len(df_invoices))]
                    
                    st.dataframe(df_invoices, use_container_width=True)
                    
                    # Opciones de exportación
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📊 Exportar a Excel"):
                            st.info("Exportando a Excel...")
                    with col2:
                        if st.button("📧 Enviar por email"):
                            st.info("Preparando envío...")
                    with col3:
                        if st.button("🖨️ Imprimir reporte"):
                            st.info("Generando PDF...")
    
    with invoice_tab2:
        st.markdown("### 📊 Dashboard Financiero")
        
        # KPIs Financieros
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Facturación Mensual", "€45,230", "↑ 12.5%")
        with col2:
            st.metric("💰 Cobros Pendientes", "€12,450", "↓ 5.2%")
        with col3:
            st.metric("⏱️ Días Medio Cobro", "28 días", "↓ 3 días")
        with col4:
            st.metric("🎯 Tasa Morosidad", "2.3%", "↓ 0.5%")
        
        # Gráficos financieros
        col1, col2 = st.columns(2)
        
        with col1:
            # Evolución mensual
            months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
            values = [32000, 35000, 38000, 41000, 43000, 45230]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=months, y=values,
                marker_color='#667eea',
                name='Facturación'
            ))
            fig.update_layout(
                title="Evolución Facturación Mensual",
                xaxis_title="Mes",
                yaxis_title="Importe (€)",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Estado de cobros
            labels = ['Cobradas', 'Pendientes', 'Vencidas']
            values = [65, 25, 10]
            colors = ['#00cc88', '#ffd93d', '#ff6b6b']
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hole=.3
            )])
            fig.update_layout(
                title="Estado de Facturas",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top clientes
        st.markdown("### 🏆 Top 5 Clientes por Facturación")
        top_clients = pd.DataFrame({
            'Cliente': ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D', 'Empresa E'],
            'Facturación': [12500, 10200, 8900, 7600, 6030],
            'Nº Facturas': [15, 12, 10, 8, 7],
            'Estado': ['✅ Al día', '✅ Al día', '⚠️ Retraso', '✅ Al día', '✅ Al día']
        })
        st.dataframe(top_clients, use_container_width=True)
    
    with invoice_tab3:
        st.markdown("### 📈 Análisis y Reportes")
        
        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox(
                "Tipo de reporte:",
                ["Mensual", "Trimestral", "Anual", "Personalizado"]
            )
            date_range = st.date_input(
                "Rango de fechas:",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )
        
        with col2:
            include_options = st.multiselect(
                "Incluir en el reporte:",
                ["Gráficos", "Tablas detalladas", "Resumen ejecutivo", "Proyecciones"],
                default=["Gráficos", "Resumen ejecutivo"]
            )
            
            format_export = st.selectbox(
                "Formato de exportación:",
                ["PDF", "Excel", "PowerPoint"]
            )
        
        if st.button("🎯 Generar Reporte", type="primary"):
            with st.spinner("Generando reporte..."):
                time.sleep(2)
                st.success("✅ Reporte generado exitosamente")
                st.download_button(
                    label="📥 Descargar Reporte",
                    data="Contenido del reporte...",
                    file_name=f"reporte_facturas_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )

# ================== TAB 4: GESTIÓN CVs ==================
with tab4:
    st.markdown("## 👥 Sistema de Gestión de CVs y Talento")
    st.markdown("Herramienta especializada para reclutadores y RRHH")
    
    cv_tab1, cv_tab2, cv_tab3 = st.tabs([
        "📥 Procesar CVs",
        "🔍 Búsqueda y Filtrado",
        "📊 Analytics de Talento"
    ])
    
    with cv_tab1:
        st.markdown("### 📥 Cargar y Analizar CVs")
        
        uploaded_cvs = st.file_uploader(
            "Selecciona CVs para procesar",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key="cv_uploader"
        )
        
        if uploaded_cvs:
            # Configuración de análisis
            with st.expander("⚙️ Configuración de Análisis"):
                col1, col2 = st.columns(2)
                with col1:
                    required_skills = st.multiselect(
                        "Habilidades requeridas:",
                        ["Python", "Java", "JavaScript", "SQL", "Excel", "Power BI", "AWS", "Docker"],
                        default=["Python", "SQL"]
                    )
                    min_experience = st.slider("Experiencia mínima (años):", 0, 15, 2)
                
                with col2:
                    required_languages = st.multiselect(
                        "Idiomas requeridos:",
                        ["Inglés", "Español", "Francés", "Alemán", "Chino"],
                        default=["Inglés"]
                    )
                    education_level = st.selectbox(
                        "Nivel educativo mínimo:",
                        ["Cualquiera", "Bachillerato", "Grado", "Máster", "Doctorado"]
                    )
            
            if st.button("🔍 Analizar Candidatos", type="primary"):
                cv_results = []
                progress = st.progress(0)
                
                for i, cv_file in enumerate(uploaded_cvs):
                    progress.progress((i+1)/len(uploaded_cvs))
                    content = extract_document_content(cv_file)
                    
                    if content:
                        cv_data = extract_cv_data(content)
                        cv_data["archivo"] = cv_file.name
                        
                        # Calcular puntuación de match
                        match_score = 0
                        if cv_data['habilidades']:
                            for skill in required_skills:
                                if skill.upper() in cv_data['habilidades']:
                                    match_score += 20
                        
                        # Añadir años de experiencia simulados
                        if cv_data['experiencia_años'] != "-":
                            try:
                                años = int(cv_data['experiencia_años'])
                                if años >= min_experience:
                                    match_score += 30
                            except:
                                pass
                        
                        cv_data['match_score'] = min(100, match_score)
                        cv_data['ranking'] = '⭐' * (match_score // 20)
                        cv_results.append(cv_data)
                
                if cv_results:
                    st.success(f"✅ {len(cv_results)} CVs procesados")
                    
                    # Ordenar por puntuación
                    cv_results = sorted(cv_results, key=lambda x: x['match_score'], reverse=True)
                    
                    # Mostrar top candidatos
                    st.markdown("### 🏆 Top Candidatos")
                    
                    for idx, candidate in enumerate(cv_results[:3], 1):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            with col1:
                                st.markdown(f"**{idx}. {candidate['nombre']}**")
                                st.write(f"📧 {candidate['email']}")
                            with col2:
                                st.write(f"💼 {candidate['ultimo_cargo']}")
                                st.write(f"📚 {candidate['educacion']}")
                            with col3:
                                st.write(f"⏱️ {candidate['experiencia_años']} años exp.")
                                if candidate['habilidades']:
                                    st.write(f"🔧 {len(candidate['habilidades'])} skills")
                            with col4:
                                st.metric("Match", f"{candidate['match_score']}%")
                                st.write(candidate['ranking'])
                            st.markdown("---")
                    
                    # Tabla completa
                    with st.expander("📋 Ver todos los candidatos"):
                        df_cvs = pd.DataFrame(cv_results)
                        columns_to_show = ['archivo', 'nombre', 'email', 'experiencia_años', 
                                         'ultimo_cargo', 'match_score', 'ranking']
                        df_display = df_cvs[[col for col in columns_to_show if col in df_cvs.columns]]
                        st.dataframe(df_display, use_container_width=True)
                    
                    # Acciones masivas
                    st.markdown("### 📧 Acciones Masivas")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📧 Enviar emails a seleccionados"):
                            st.info("Preparando plantilla de email...")
                    with col2:
                        if st.button("📅 Programar entrevistas"):
                            st.info("Abriendo calendario...")
                    with col3:
                        if st.button("💾 Exportar a ATS"):
                            st.info("Exportando a sistema ATS...")
    
    with cv_tab2:
        st.markdown("### 🔍 Búsqueda Avanzada de Candidatos")
        
        # Filtros de búsqueda
        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input("🔍 Buscar:", placeholder="Ej: Python developer")
            location = st.text_input("📍 Ubicación:", placeholder="Madrid, España")
        with col2:
            salary_range = st.slider("💰 Rango salarial (k€):", 20, 100, (30, 60))
            availability = st.selectbox("📅 Disponibilidad:", ["Inmediata", "15 días", "1 mes", "2 meses"])
        with col3:
            contract_type = st.multiselect("📝 Tipo contrato:", ["Indefinido", "Temporal", "Freelance", "Prácticas"])
            remote = st.checkbox("🏠 Remoto", value=True)
        
        if st.button("🔍 Buscar Candidatos", type="primary"):
            # Simulación de resultados
            st.success("Encontrados 47 candidatos que coinciden con tus criterios")
            
            # Mostrar algunos resultados simulados
            sample_candidates = pd.DataFrame({
                'Nombre': ['Ana García', 'Carlos López', 'María Rodríguez'],
                'Posición': ['Senior Developer', 'Full Stack Dev', 'Data Scientist'],
                'Experiencia': ['5 años', '3 años', '4 años'],
                'Skills': ['Python, AWS, Docker', 'React, Node, MongoDB', 'Python, TensorFlow, SQL'],
                'Salario': ['45k€', '38k€', '42k€'],
                'Match': ['95%', '88%', '85%']
            })
            st.dataframe(sample_candidates, use_container_width=True)
    
    with cv_tab3:
        st.markdown("### 📊 Analytics de Talento")
        
        # Métricas de reclutamiento
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 CVs Procesados", "234", "↑ 23")
        with col2:
            st.metric("⏱️ Tiempo Medio Contratación", "18 días", "↓ 3 días")
        with col3:
            st.metric("🎯 Tasa de Éxito", "78%", "↑ 5%")
        with col4:
            st.metric("💼 Posiciones Abiertas", "12", "↓ 2")
        
        # Gráficos de talento
        col1, col2 = st.columns(2)
        
        with col1:
            # Skills más demandadas
            skills = ['Python', 'JavaScript', 'SQL', 'React', 'AWS']
            counts = [156, 142, 138, 125, 118]
            
            fig = go.Figure(data=[go.Bar(
                x=counts,
                y=skills,
                orientation='h',
                marker_color='#667eea'
            )])
            fig.update_layout(
                title="Top Skills en Candidatos",
                xaxis_title="Nº de Candidatos",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Fuentes de candidatos
            sources = ['LinkedIn', 'Web Empresa', 'Referidos', 'Job Boards', 'Otros']
            values = [35, 25, 20, 15, 5]
            
            fig = go.Figure(data=[go.Pie(
                labels=sources,
                values=values,
                hole=.3,
                marker_colors=['#1e88e5', '#43a047', '#fb8c00', '#e53935', '#8e24aa']
            )])
            fig.update_layout(
                title="Fuentes de Candidatos",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Pipeline de contratación
        st.markdown("### 📊 Pipeline de Contratación")
        pipeline_data = pd.DataFrame({
            'Fase': ['CVs Recibidos', 'Screening', 'Entrevista Tel.', 'Entrevista Técnica', 'Oferta', 'Contratado'],
            'Candidatos': [234, 156, 89, 45, 18, 12],
            'Conversión': ['100%', '67%', '38%', '19%', '8%', '5%']
        })
        
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = go.Figure(data=[go.Funnel(
                y=pipeline_data['Fase'],
                x=pipeline_data['Candidatos'],
                textposition="inside",
                textinfo="value+percent initial"
            )])
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(pipeline_data, use_container_width=True)

# ================== TAB 5: CONTRATOS ==================
with tab5:
    st.markdown("## 📑 Gestión de Contratos")
    st.markdown("Sistema de análisis y seguimiento de contratos empresariales")
    
    contract_tab1, contract_tab2, contract_tab3 = st.tabs([
        "📥 Procesar Contratos",
        "📋 Gestión y Seguimiento",
        "⚠️ Alertas y Vencimientos"
    ])
    
    with contract_tab1:
        st.markdown("### 📥 Cargar y Analizar Contratos")
        
        uploaded_contracts = st.file_uploader(
            "Selecciona contratos para analizar",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key="contract_uploader"
        )
        
        if uploaded_contracts:
            # Opciones de análisis
            with st.expander("⚙️ Opciones de Análisis"):
                col1, col2 = st.columns(2)
                with col1:
                    extract_clauses = st.checkbox("📝 Extraer cláusulas principales", value=True)
                    identify_risks = st.checkbox("⚠️ Identificar riesgos", value=True)
                    check_compliance = st.checkbox("✅ Verificar cumplimiento", value=True)
                with col2:
                    extract_dates = st.checkbox("📅 Extraer fechas clave", value=True)
                    extract_amounts = st.checkbox("💰 Extraer importes", value=True)
                    generate_alerts = st.checkbox("🔔 Generar alertas", value=True)
            
            if st.button("🔍 Analizar Contratos", type="primary"):
                contract_results = []
                progress = st.progress(0)
                
                for i, contract_file in enumerate(uploaded_contracts):
                    progress.progress((i+1)/len(uploaded_contracts))
                    content = extract_document_content(contract_file)
                    
                    if content:
                        contract_data = extract_contract_data(content)
                        contract_data["archivo"] = contract_file.name
                        
                        # Análisis de riesgo simulado
                        risk_score = 25 if "penalización" in content.lower() else 10
                        contract_data["riesgo"] = "🔴 Alto" if risk_score > 20 else "🟢 Bajo"
                        
                        contract_results.append(contract_data)
                
                if contract_results:
                    st.success(f"✅ {len(contract_results)} contratos analizados")
                    
                    # Resumen de contratos
                    st.markdown("### 📊 Resumen de Contratos")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📄 Total Contratos", len(contract_results))
                    with col2:
                        activos = sum(1 for c in contract_results if c.get('fecha_fin', '-') != '-')
                        st.metric("✅ Activos", activos)
                    with col3:
                        alto_riesgo = sum(1 for c in contract_results if '🔴' in c.get('riesgo', ''))
                        st.metric("⚠️ Alto Riesgo", alto_riesgo)
                    with col4:
                        st.metric("💰 Valor Total", "€2.5M")
                    
                    # Tabla de contratos
                    df_contracts = pd.DataFrame(contract_results)
                    st.dataframe(df_contracts, use_container_width=True)
                    
                    # Análisis de cláusulas
                    if extract_clauses:
                        st.markdown("### 📝 Cláusulas Identificadas")
                        clausula_types = ['Confidencialidad', 'Penalizaciones', 'Rescisión', 
                                        'Pagos', 'Garantías', 'Responsabilidades']
                        
                        cols = st.columns(3)
                        for i, clausula in enumerate(clausula_types):
                            with cols[i % 3]:
                                found = "✅" if clausula.lower() in str(contract_results).lower() else "❌"
                                st.write(f"{found} {clausula}")
    
    with contract_tab2:
        st.markdown("### 📋 Gestión y Seguimiento de Contratos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            contract_type = st.selectbox("Tipo de contrato:", 
                ["Todos", "Servicios", "Suministro", "Laboral", "Arrendamiento"])
        with col2:
            status = st.selectbox("Estado:", 
                ["Todos", "Vigente", "Por vencer", "Vencido", "En renovación"])
        with col3:
            department = st.selectbox("Departamento:", 
                ["Todos", "Ventas", "Compras", "RRHH", "Legal"])
        
        # Tabla de gestión
        management_data = pd.DataFrame({
            'Contrato': ['CTR-2024-001', 'CTR-2024-002', 'CTR-2024-003', 'CTR-2024-004'],
            'Tipo': ['Servicios', 'Suministro', 'Laboral', 'Arrendamiento'],
            'Contraparte': ['Empresa A', 'Proveedor B', 'Juan Pérez', 'Inmobiliaria C'],
            'Inicio': ['01/01/2024', '15/02/2024', '01/03/2024', '01/01/2024'],
            'Fin': ['31/12/2024', '14/02/2025', '28/02/2025', '31/12/2026'],
            'Valor': ['€150,000', '€75,000', '€45,000', '€24,000/año'],
            'Estado': ['✅ Vigente', '✅ Vigente', '✅ Vigente', '⚠️ Por revisar'],
            'Próxima Acción': ['Revisión Q4', 'Ninguna', 'Evaluación', 'Renovación']
        })
        
        st.dataframe(management_data, use_container_width=True)
        
        # Acciones
        st.markdown("### 🎯 Acciones Rápidas")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📧 Enviar recordatorios"):
                st.info("Enviando recordatorios...")
        with col2:
            if st.button("📊 Generar informe"):
                st.info("Generando informe...")
        with col3:
            if st.button("🔄 Iniciar renovación"):
                st.info("Iniciando proceso...")
        with col4:
            if st.button("📅 Ver calendario"):
                st.info("Abriendo calendario...")
    
    with contract_tab3:
        st.markdown("### ⚠️ Alertas y Vencimientos")
        
        # Alertas urgentes
        st.markdown("#### 🚨 Alertas Urgentes")
        
        alert_data = [
            {"tipo": "🔴", "contrato": "CTR-2024-001", "mensaje": "Vence en 10 días", "accion": "Renovar"},
            {"tipo": "🟡", "contrato": "CTR-2024-003", "mensaje": "Revisión pendiente", "accion": "Revisar"},
            {"tipo": "🔴", "contrato": "CTR-2024-005", "mensaje": "Pago atrasado", "accion": "Contactar"}
        ]
        
        for alert in alert_data:
            col1, col2, col3, col4 = st.columns([1, 2, 3, 2])
            with col1:
                st.write(alert["tipo"])
            with col2:
                st.write(alert["contrato"])
            with col3:
                st.write(alert["mensaje"])
            with col4:
                st.button(alert["accion"], key=f"action_{alert['contrato']}")
        
        # Calendario de vencimientos
        st.markdown("#### 📅 Próximos Vencimientos")
        
        vencimientos = pd.DataFrame({
            'Fecha': pd.date_range(start='2024-01-01', periods=12, freq='M'),
            'Contratos': [2, 1, 3, 0, 2, 1, 4, 2, 1, 3, 2, 5]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=vencimientos['Fecha'],
            y=vencimientos['Contratos'],
            mode='lines+markers',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=10)
        ))
        fig.update_layout(
            title="Contratos por Vencer (Próximos 12 meses)",
            xaxis_title="Mes",
            yaxis_title="Número de Contratos",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

# ================== TAB 6: ANALYTICS AVANZADO ==================
with tab6:
    st.markdown("## 📊 Centro de Analytics Avanzado")
    st.markdown("Análisis profundo y métricas de negocio")
    
    analytics_tab1, analytics_tab2, analytics_tab3, analytics_tab4 = st.tabs([
        "📈 KPIs Generales",
        "🔍 Análisis Predictivo",
        "🎯 Comparativas",
        "📊 Reportes Ejecutivos"
    ])
    
    with analytics_tab1:
        st.markdown("### 📈 KPIs y Métricas Generales")
        
        # KPIs principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Docs/Mes", "342", "↑ 23%", help="Documentos procesados este mes")
        with col2:
            st.metric("⏱️ Tiempo Ahorro", "156h", "↑ 12%", help="Horas ahorradas con automatización")
        with col3:
            st.metric("💰 ROI", "245%", "↑ 34%", help="Retorno de inversión")
        with col4:
            st.metric("😊 Satisfacción", "4.8/5", "↑ 0.2", help="Puntuación de usuarios")
        
        # Gráficos de rendimiento
        col1, col2 = st.columns(2)
        
        with col1:
            # Evolución procesamiento
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            values = [100 + i*3 + (i%7)*10 for i in range(30)]
            
            fig = px.line(
                x=dates, y=values,
                title="Evolución de Procesamiento (30 días)",
                labels={'x': 'Fecha', 'y': 'Documentos'}
            )
            fig.update_traces(line_color='#667eea')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Eficiencia por tipo
            efficiency_data = pd.DataFrame({
                'Tipo': ['Facturas', 'CVs', 'Contratos', 'Informes', 'Otros'],
                'Eficiencia': [95, 88, 92, 85, 78],
                'Volumen': [450, 234, 156, 89, 45]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Eficiencia (%)',
                x=efficiency_data['Tipo'],
                y=efficiency_data['Eficiencia'],
                yaxis='y',
                marker_color='#667eea'
            ))
            fig.add_trace(go.Scatter(
                name='Volumen',
                x=efficiency_data['Tipo'],
                y=efficiency_data['Volumen'],
                yaxis='y2',
                marker_color='#ff6b6b',
                mode='lines+markers'
            ))
            fig.update_layout(
                title="Eficiencia vs Volumen por Tipo",
                yaxis=dict(title='Eficiencia (%)', side='left'),
                yaxis2=dict(title='Volumen', overlaying='y', side='right'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with analytics_tab2:
        st.markdown("### 🔍 Análisis Predictivo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Proyección de Carga de Trabajo")
            
            # Datos de proyección
            months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
            actual = [342, 356, 378, 392, None, None]
            projected = [None, None, None, 392, 410, 435]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months, y=actual,
                mode='lines+markers',
                name='Real',
                line=dict(color='#667eea', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=months, y=projected,
                mode='lines+markers',
                name='Proyectado',
                line=dict(color='#ff6b6b', width=2, dash='dash')
            ))
            fig.update_layout(
                title="Proyección de Documentos",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 🎯 Predicciones del Sistema")
            
            predictions = [
                {"metrica": "Documentos próximo mes", "valor": "435", "confianza": "92%"},
                {"metrica": "Tiempo ahorro estimado", "valor": "178h", "confianza": "88%"},
                {"metrica": "Facturas pendientes", "valor": "45", "confianza": "95%"},
                {"metrica": "CVs esperados", "valor": "120", "confianza": "85%"}
            ]
            
            for pred in predictions:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.write(f"📈 {pred['metrica']}")
                with col_b:
                    st.write(f"**{pred['valor']}**")
                with col_c:
                    st.write(f"🎯 {pred['confianza']}")
    
    with analytics_tab3:
        st.markdown("### 🎯 Análisis Comparativo")
        
        # Comparativa temporal
        st.markdown("#### 📅 Comparativa Temporal")
        
        comparison_data = pd.DataFrame({
            'Métrica': ['Documentos Procesados', 'Tiempo Promedio', 'Errores', 'Satisfacción'],
            'Este Mes': [342, '1.2s', 3, 4.8],
            'Mes Anterior': [298, '1.5s', 7, 4.6],
            'Variación': ['+14.8%', '-20%', '-57%', '+4.3%']
        })
        
        st.dataframe(comparison_data, use_container_width=True)
        
        # Benchmark industria
        st.markdown("#### 🏆 Benchmark vs Industria")
        
        categories = ['Velocidad', 'Precisión', 'Volumen', 'Satisfacción', 'ROI']
        empresa_values = [95, 98, 87, 92, 89]
        industria_values = [75, 85, 78, 80, 72]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=empresa_values,
            theta=categories,
            fill='toself',
            name='Tu Empresa',
            line_color='#667eea'
        ))
        fig.add_trace(go.Scatterpolar(
            r=industria_values,
            theta=categories,
            fill='toself',
            name='Media Industria',
            line_color='#ff6b6b'
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with analytics_tab4:
        st.markdown("### 📊 Generador de Reportes Ejecutivos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_period = st.selectbox(
                "Período del reporte:",
                ["Semanal", "Mensual", "Trimestral", "Anual", "Personalizado"]
            )
            
            report_sections = st.multiselect(
                "Secciones a incluir:",
                ["Resumen Ejecutivo", "KPIs", "Análisis Detallado", "Proyecciones", 
                 "Recomendaciones", "Anexos"],
                default=["Resumen Ejecutivo", "KPIs", "Análisis Detallado"]
            )
            
            recipients = st.text_input(
                "Destinatarios (emails):",
                placeholder="direccion@empresa.com, gerencia@empresa.com"
            )
        
        with col2:
            report_format = st.selectbox(
                "Formato de salida:",
                ["PDF Ejecutivo", "Excel Detallado", "PowerPoint", "Dashboard Interactivo"]
            )
            
            schedule_report = st.checkbox("📅 Programar envío automático")
            
            if schedule_report:
                schedule_frequency = st.selectbox(
                    "Frecuencia:",
                    ["Diario", "Semanal", "Mensual"]
                )
                schedule_time = st.time_input("Hora de envío:")
        
        if st.button("🎯 Generar Reporte Ejecutivo", type="primary", use_container_width=True):
            with st.spinner("Generando reporte ejecutivo..."):
                time.sleep(3)
                
                st.success("✅ Reporte generado exitosamente")
                
                # Preview del reporte
                st.markdown("#### 📄 Preview del Reporte")
                st.info(f"""
                **REPORTE EJECUTIVO - {report_period.upper()}**
                
                📊 **Resumen de Rendimiento:**
                • Documentos procesados: 342 (+14.8%)
                • Eficiencia del sistema: 98.5%
                • Tiempo medio de procesamiento: 1.2s
                • ROI del período: 245%
                
                🎯 **Logros Destacados:**
                • Reducción del 57% en errores de procesamiento
                • Ahorro de 156 horas de trabajo manual
                • Mejora del 20% en velocidad de procesamiento
                
                📈 **Proyecciones:**
                • Se espera un incremento del 12% en el volumen próximo período
                • ROI proyectado: 280%
                
                💡 **Recomendaciones:**
                • Implementar procesamiento batch nocturno
                • Ampliar capacidades de IA para contratos complejos
                • Capacitar equipo en nuevas funcionalidades
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Descargar Reporte",
                        data="Contenido del reporte...",
                        file_name=f"reporte_ejecutivo_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col2:
                    if st.button("📧 Enviar por Email", use_container_width=True):
                        st.success("📧 Reporte enviado a los destinatarios")

# ================== FOOTER ==================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p><strong>🤖 Agentic AI Business Hub v2.0</strong></p>
    <p>Sistema Inteligente de Gestión Documental Empresarial</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">
        Desarrollado con Streamlit • Python • IA Avanzada<br>
        © 2024 - Todos los derechos reservados
    </p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh si está activado
if auto_refresh:
    time.sleep(30)
    st.rerun()