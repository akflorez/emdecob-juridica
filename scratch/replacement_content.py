class MatchResult:
    def __init__(self, is_valid: bool, match_type: Optional[str] = None, reasons: Optional[str] = None,
                 score: int = 0, estado_validacion: str = "descartado", texto_bloque_match: str = "",
                 elementos_detectados: dict = None):
        self.is_valid = is_valid
        self.match_type = match_type
        self.reasons = reasons
        self.score = score
        self.estado_validacion = estado_validacion
        self.texto_bloque_match = texto_bloque_match
        self.elementos_detectados = elementos_detectados or {}

def split_document_into_lines(text: str) -> List[str]:
    """Divide el texto en líneas limpias, manejando saltos de línea y tabulaciones"""
    if not text: return []
    # Reemplazar retornos de carro por \n y dividir
    lines = text.replace('\r', '\n').split('\n')
    # Limpiar espacios
    lines = [line.strip() for line in lines if line.strip()]
    return lines

def build_context_window(text: str, match_position: int, size: int = 1200) -> str:
    """Extrae un bloque de texto alrededor de una posición, asegurando capturar contexto cercano."""
    if not text: return ""
    start_pos = max(0, match_position - size // 2)
    end_pos = min(len(text), match_position + size // 2)
    return text[start_pos:end_pos]

def important_tokens(name: str) -> List[str]:
    """Extrae tokens importantes de una parte, ignorando stop-words corporativos y genéricos."""
    if not name: return []
    name_clean = normalize_text(name).upper()
    for suffix in ["S.A.S.", "SAS", "S.A.", "LIMITADA", "LTDA", "E.S.P.", "ESP", "COOPERATIVA", "MULTIACTIVA", "NACIONAL", "FIDUCIARIA", "BANCO"]:
        name_clean = name_clean.replace(suffix, " ")
    blacklist = {"del", "los", "las", "con", "sin", "por", "para", "sus", "una", "uno", "mas", "que", "les", "sus", "y", "o", "de", "la", "el", "en"}
    tokens = [t.lower() for t in name_clean.split() if len(t) >= 3 and t.lower() not in blacklist]
    return tokens

def parties_match(block_text: str, party_name: str) -> bool:
    """Valida si al menos dos tokens importantes de una parte están presentes en el bloque."""
    if not party_name or not block_text: return False
    tokens = important_tokens(party_name)
    if not tokens: return False
    
    block_norm = normalize_text(block_text).lower()
    
    # Excepción: Si solo hay 1 token importante (ej. "TALERO"), exigir que aparezca
    if len(tokens) == 1:
        return tokens[0] in block_norm
        
    # Exigir al menos 2 tokens importantes
    matches = sum(1 for t in tokens if t in block_norm)
    return matches >= 2

def classify_document_match(text: str, radicado: str, demandante: str = "", demandado: str = "", is_filtered_source: bool = False) -> MatchResult:
    """
    Nuevo motor de validación estricta y antifalsos positivos.
    Evalúa coincidencias basándose en proximidad/bloques y asigna un puntaje.
    """
    if not text:
        return MatchResult(False, None, "Texto vacío", 0, "descartado", "")
        
    digits = only_digits(radicado)
    if len(digits) != 23:
        return MatchResult(False, None, "Radicado incompleto", 0, "descartado", "")

    # Componentes
    despacho = digits[:12]
    year = digits[12:16]
    consecutivo = digits[16:21]
    
    # Variantes de radicado
    rad_hyphenated = f"{digits[:5]}-{digits[5:7]}-{digits[7:9]}-{digits[9:12]}-{digits[12:16]}-{digits[16:21]}-{digits[21:]}"
    rad_spaces = f"{digits[:5]} {digits[5:7]} {digits[7:9]} {digits[9:12]} {digits[12:16]} {digits[16:21]} {digits[21:]}"
    
    # Variantes internos
    internal_num_dash = f"{year}-{consecutivo}"
    internal_num_no_dash = f"{year}{consecutivo}"
    internal_num_short_dash = f"{year}-{int(consecutivo)}" if consecutivo.isdigit() else consecutivo
    internal_num_short_no_dash = f"{year}{int(consecutivo)}" if consecutivo.isdigit() else consecutivo
    
    internal_variants = [internal_num_dash, internal_num_no_dash, internal_num_short_dash, internal_num_short_no_dash]
    
    # Buscamos coincidencias fuertes globales (que garantizan 100 o 95 pts sin importar contexto)
    text_norm = normalize_text(text)
    text_digits = "".join(c for c in text if c.isdigit())
    
    # 1. Radicado exacto (100 pts)
    if digits in text_digits:
        pos = text_digits.find(digits)
        # Buscar posición original aproximada
        pos_orig = text.find(digits[:5]) if digits[:5] in text else len(text)//2
        bloque = build_context_window(text, pos_orig, 800)
        return MatchResult(True, "radicado_completo", "Radicado completo sin guiones", 100, "validado", bloque, {"full_radicado": True})
        
    if rad_hyphenated in text:
        pos = text.find(rad_hyphenated)
        bloque = build_context_window(text, pos, 800)
        return MatchResult(True, "radicado_completo_con_guiones", "Radicado completo con guiones", 100, "validado", bloque, {"full_radicado": True})
        
    # 2. Radicado con espacios (95 pts)
    if rad_spaces in text:
        pos = text.find(rad_spaces)
        bloque = build_context_window(text, pos, 800)
        return MatchResult(True, "radicado_completo_con_espacios", "Radicado completo con espacios", 95, "validado", bloque, {"full_radicado": True})

    # No hay coincidencia global fuerte, buscamos por bloques (Ventanas de contexto)
    best_score = 0
    best_result = MatchResult(False, None, "No se encontró coincidencia fuerte", 0, "descartado", "")
    
    # Recorrer todas las posibles apariciones del número interno como anclas
    for iv in internal_variants:
        for match in re.finditer(re.escape(iv), text):
            # Extraer bloque de contexto (aprox 1200 caracteres alrededor del hit)
            block = build_context_window(text, match.start(), 1200)
            block_norm = normalize_text(block).lower()
            
            # Detectar componentes en el bloque
            has_despacho = (despacho in block_norm) or (f"{digits[:5]} {digits[5:7]} {digits[7:9]} {digits[9:12]}" in block_norm) or (f"{digits[:5]}-{digits[5:7]}-{digits[7:9]}-{digits[9:12]}" in block_norm)
            
            has_demandante = parties_match(block, demandante)
            has_demandado = parties_match(block, demandado)
            
            score = 0
            motivo = ""
            estado = "descartado"
            m_type = "ninguno"
            
            if has_despacho and has_demandante and has_demandado:
                score = 92
                estado = "validado"
                m_type = "despacho_partes_interno"
                motivo = f"Número interno ({iv}) junto con despacho y ambas partes"
            elif has_despacho:
                score = 90
                estado = "validado"
                m_type = "despacho_interno"
                motivo = f"Despacho y número interno ({iv}) en el mismo bloque"
            elif has_demandante and has_demandado:
                score = 88
                estado = "validado"
                m_type = "interno_ambas_partes"
                motivo = f"Número interno ({iv}) y ambas partes en el bloque"
            elif (has_demandante or has_demandado) and is_filtered_source:
                score = 78
                estado = "requiere_revision"
                m_type = "interno_una_parte_fuente_filtrada"
                motivo = f"Número interno ({iv}) y una parte en el bloque (fuente oficial del despacho)"
            elif is_filtered_source:
                # El documento viene de la búsqueda oficial del despacho, y encontramos el número interno pero sin partes
                score = 65
                estado = "requiere_revision" if score >= 70 else "descartado"
                m_type = "interno_fuente_filtrada"
                motivo = f"Número interno ({iv}) en fuente del despacho, pero sin partes ni despacho textual"
                
            elementos = {
                "internal": iv,
                "despacho": has_despacho,
                "demandante": has_demandante,
                "demandado": has_demandado
            }
                
            if score > best_score:
                best_score = score
                best_result = MatchResult(
                    is_valid=(estado == "validado"),
                    match_type=m_type,
                    reasons=motivo,
                    score=score,
                    estado_validacion=estado,
                    texto_bloque_match=block.strip(),
                    elementos_detectados=elementos
                )

    # Considerar casos de extracción pobre
    if best_score < 70 and is_filtered_source:
        # Si extrajimos muy poco texto (ej. imagen escaneada no ocrizada) pero venía de fuente oficial
        if len(text.strip()) < 500:
            return MatchResult(False, "extraccion_pobre", "Extracción de texto pobre en fuente oficial. Requiere revisión visual.", 50, "requiere_revision", text.strip()[:200], {})

    return best_result

def validate_strong_match(text: str, radicado_completo: str, demandante: str = "", demandado: str = "") -> MatchResult:
    # Para retrocompatibilidad
    return classify_document_match(text, radicado_completo, demandante, demandado, is_filtered_source=False)

def find_radicado_in_context(text: str, radicado: str, demandante: str = "", demandado: str = "") -> MatchResult:
    return classify_document_match(text, radicado, demandante, demandado, is_filtered_source=False)
