from sqlalchemy import create_engine, text

db_url = "postgresql://emdecob:emdecob2026@84.247.130.122:5432/emdecob_consultas"
engine = create_engine(db_url)

def update_2805():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Updating publication 2805...")
            conn.execute(text("""
                UPDATE case_publications 
                SET estado_validacion = 'validado_por_fuente_oficial',
                    match_score = 95,
                    requiere_revision = False
                WHERE id = 2805
            """))
            trans.commit()
            print("Successfully updated publication 2805!")
        except Exception as e:
            trans.rollback()
            print(f"Error updating: {e}")

if __name__ == "__main__":
    update_2805()
