"""
🔍 Utilidades de Extracción de Datos
Funciones especializadas para extraer información de diferentes tipos de documentos
"""

import re

def extract_enhanced_invoice_data(content):
    """
    Extracción mejorada para múltiples formatos de facturas
    Maneja facturas tradicionales, de servicios profesionales, etc.
    """
    entities_found = []
    
    # ================================
    # 💰 PATRONES DE IMPORTES MEJORADOS
    # ================================
    
    # 1. BASE IMPONIBLE / SUBTOTAL
    subtotal_patterns = [
        r'(?:BASE IMPONIBLE|Base imponible|SUBTOTAL|Subtotal|Base tributable):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:Importe sin IVA|Sin IVA):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)'
    ]
    
    for pattern in subtotal_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        if matches:
            subtotal_found = matches[0].strip()
            entities_found.append({
                "Tipo": "SUBTOTAL", 
                "Valor": subtotal_found, 
                "Confianza": "95%"
            })
            break
    
    # 2. IVA
    iva_patterns = [
        r'(?:IVA|I\.V\.A\.)\s*\((\d+)%\):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:IVA|I\.V\.A\.)\s*\(21%\):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:IVA|I\.V\.A\.)\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
    ]
    
    for pattern in iva_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # Si captura porcentaje y valor, toma el valor
            if isinstance(matches[0], tuple) and len(matches[0]) > 1:
                iva_found = matches[0][1].strip()
            else:
                iva_found = matches[0].strip()
            entities_found.append({
                "Tipo": "IVA", 
                "Valor": iva_found, 
                "Confianza": "95%"
            })
            break
    
    # 3. TOTAL FACTURA (PRIORIDAD)
    total_patterns = [
        r'(?:TOTAL FACTURA|Total factura|TOTAL FINAL|Total final):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:TOTAL A PAGAR|Total a pagar):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:IMPORTE TOTAL|Importe total):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
        r'(?:TOTAL|Total)(?!\s*(?:sin|Sin|base|Base)):\s*([€$£]?\s*[\d,]+\.?\d*\s*(?:EUR|€)?)',
    ]
    
    # Buscar desde el final hacia atrás para encontrar el total definitivo
    lines = content.split('\n')
    for line in reversed(lines):
        for pattern in total_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                total_found = matches[0].strip()
                entities_found.append({
                    "Tipo": "TOTAL", 
                    "Valor": total_found, 
                    "Confianza": "98%"
                })
                break
        if any(e["Tipo"] == "TOTAL" for e in entities_found):
            break
    
    # ================================
    # 📄 INFORMACIÓN DE LA FACTURA
    # ================================
    
    # 4. NÚMERO DE FACTURA
    factura_patterns = [
        r'(?:FACTURA|Factura):\s*([A-Z0-9\-]+)',
        r'(?:Nº|N°|Número)\s*(?:factura|Factura):\s*([A-Z0-9\-]+)',
        r'(?:Ref|REF|Referencia):\s*([A-Z0-9\-]+)'
    ]
    
    for pattern in factura_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            entities_found.append({
                "Tipo": "Nº_FACTURA", 
                "Valor": matches[0], 
                "Confianza": "95%"
            })
            break
    
    # 5. FECHAS
    fecha_patterns = [
        r'(?:Fecha de emisión|Fecha emisión|Fecha):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(?:Date|Fecha):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b'
    ]
    
    fechas_encontradas = set()
    for pattern in fecha_patterns:
        matches = re.findall(pattern, content)
        for fecha in matches:
            if fecha not in fechas_encontradas and len(fecha) >= 8:
                fechas_encontradas.add(fecha)
                entities_found.append({
                    "Tipo": "FECHA", 
                    "Valor": fecha, 
                    "Confianza": "92%"
                })
    
    # ================================
    # 🏢 INFORMACIÓN DE EMPRESAS
    # ================================
    
    # 6. CIF/NIF
    cif_patterns = [
        r'(?:CIF|NIF|CIF/NIF):\s*([A-Z]?\d{8}[A-Z]?)',
        r'\b([A-Z]\d{8})\b',
        r'\b([A-Z]\d{7}[A-Z])\b'
    ]
    
    cifs_encontrados = set()
    for pattern in cif_patterns:
        matches = re.findall(pattern, content)
        for cif in matches:
            if len(cif) >= 8 and cif not in cifs_encontrados:
                cifs_encontrados.add(cif)
                entities_found.append({
                    "Tipo": "CIF/NIF", 
                    "Valor": cif, 
                    "Confianza": "95%"
                })
    
    # 7. EMPRESAS
    empresa_patterns = [
        r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&]+(?:S\.A\.|S\.L\.|S\.L\.U\.|S\.A\.U\.|ASOCIADOS))\b',
        r'^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s&]{10,}?)(?=\n|CIF)',
        r'(?:Cliente|CLIENTE):\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s&\.]+)',
    ]
    
    empresas_encontradas = set()
    for pattern in empresa_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for empresa in matches:
            empresa_clean = empresa.strip()
            if len(empresa_clean) > 8 and empresa_clean not in empresas_encontradas:
                if not any(word in empresa_clean.lower() for word in ['factura', 'fecha', 'total', 'iva', 'base']):
                    empresas_encontradas.add(empresa_clean)
                    entities_found.append({
                        "Tipo": "EMPRESA", 
                        "Valor": empresa_clean, 
                        "Confianza": "90%"
                    })
    
    # ================================
    # 📧 CONTACTO
    # ================================
    
    # 8. EMAILS
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
    for email in emails[:2]:
        entities_found.append({
            "Tipo": "EMAIL", 
            "Valor": email, 
            "Confianza": "95%"
        })
    
    # 9. TELÉFONOS
    phone_patterns = [
        r'(?:Teléfono|Tel|Phone|Móvil):\s*([+34\s]?[679]\d{8})',
        r'\b([679]\d{8})\b',
    ]
    
    telefonos_encontrados = set()
    for pattern in phone_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for telefono in matches:
            clean_phone = re.sub(r'[^\d+]', '', str(telefono))
            if len(clean_phone) >= 9 and clean_phone not in telefonos_encontrados:
                telefonos_encontrados.add(clean_phone)
                entities_found.append({
                    "Tipo": "TELÉFONO", 
                    "Valor": telefono, 
                    "Confianza": "90%"
                })
    
    # 10. FORMA DE PAGO
    pago_patterns = [
        r'(?:Forma de pago|Método de pago|Pago):\s*([A-Za-z\s\d]+)',
        r'(?:Transferencia|Efectivo|Tarjeta|Cheque|Domiciliación)\s*(\d+\s*días?)?'
    ]
    
    for pattern in pago_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            pago_info = matches[0] if isinstance(matches[0], str) else ' '.join(matches[0])
            entities_found.append({
                "Tipo": "FORMA_PAGO", 
                "Valor": pago_info.strip(), 
                "Confianza": "85%"
            })
            break
    
    # 11. SERVICIOS/PRODUCTOS
    servicio_patterns = [
        r'▶\s*([A-Za-z\s]+(?:Q3|septiembre|consulta|revisión|gestión|asesoramiento)[A-Za-z\s]*)',
        r'(?:Concepto|Descripción|Servicio):\s*([A-Za-z\s]{10,})',
        r'(?:SERVICIOS|Servicios)\s*([A-Za-z\s]{5,}?):'
    ]
    
    servicios_encontrados = set()
    for pattern in servicio_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for servicio in matches[:3]:  # Máximo 3 servicios
            servicio_clean = servicio.strip()
            if len(servicio_clean) > 5 and servicio_clean not in servicios_encontrados:
                servicios_encontrados.add(servicio_clean)
                entities_found.append({
                    "Tipo": "SERVICIO", 
                    "Valor": servicio_clean, 
                    "Confianza": "80%"
                })
    
    return entities_found