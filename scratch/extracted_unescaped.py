"MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

class MatchResult:
    def __init__(self, is_valid: bool, match_type: Optional[str] = None, reasons: Optional[str] = None):
        self.is_valid = is_valid
        self.match_type = match_type
        self.reasons = reasons

def validate_strong_match(text: str, radicado_completo: str, demandante: str = "", demandado: str = "") -> MatchResult:
    if not text or len(text) < 10:
        return MatchResult(False, None, "Texto vacÃ­o o demasiado corto")
        
    rad_norm = "".join(filter(str.isdigit, radicado_completo))
    if len(rad_norm) != 23:
        return MatchResult(False, None, "El radicado no tiene 23 dÃ­gitos")
        
    text_upper = text.upper()
    text_clean = " ".join(text_upper.split())
    
    # A. Radicado completo sin guiones
    rad_sin_guiones = rad_norm
    # B. Radicado completo con guiones
    rad_con_guiones = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}-{rad_norm[12:16]}-{rad_norm[16:21]}-{rad_norm[21:]}"
    # C. Radicado completo con espacios
    rad_con_espacios = f"{rad_norm[:5]} {rad_norm[5:7]} {rad_norm[7:9]} {rad_norm[9:12]} {rad_norm[12:16]} {rad_norm[16:21]} {rad_norm[21:]}"
    
    # D. Despacho + nÃºmero interno (no dashes)
    despacho_sin = rad_norm[:12]
    interno_sin = rad_norm[12:21]
    # E. Despacho con guiones + nÃºmero interno con guion
    despacho_con = f"{rad_norm[:5]}-{rad_norm[5:7]}-{rad_norm[7:9]}-{rad_norm[9:12]}"
    interno_con = f"{rad_norm[12:16]}-{rad_norm[16:21]}"
    
    # Check A, B, C with regex (flexible spacing/dashing)
    pattern_flex = r"".join([c + r"[\s-]*" for c in rad_norm[:-1]]) + rad_norm[-1]
    if re.search(pattern_flex, text_clean):
        if rad_con_guiones in text_clean:
            return MatchResult(True, "radicado_completo_con_guiones", "Coincidencia con radicado completo con gui
<truncated 24529 bytes>