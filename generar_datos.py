import numpy as np
import pandas as pd

rng = np.random.default_rng(7)

SEMESTRES = ["2024-I", "2024-II", "2025-I", "2025-II", "2026-I", "2026-II"]
POSICIONES = ["Arquero", "Central", "Lateral", "Volante", "Extremo", "Delantero"]
ARQUETIPOS = {"progresa": 0.6, "estable": 0.1, "estancado": -0.4, "tardio": 0.25}
NOTAS = [
    "Buena actitud, mejorar toma de decisiones en último tercio.",
    "Salto físico notable este semestre.",
    "Irregular en entrenos, talento por encima del promedio.",
    "Líder del grupo, rendimiento estable.",
    "Dificultades con la carga, revisar con fisioterapia.",
    "Listo para minutos en categoría superior.",
]

filas = []
for i in range(1, 41):
    pos = rng.choice(POSICIONES)
    arq = rng.choice(list(ARQUETIPOS), p=[0.35, 0.30, 0.20, 0.15])
    # RAE sembrado: cantera real sobre-representa Q1 (sesgo a corregir)
    trimestre = int(rng.choice([1, 2, 3, 4], p=[0.42, 0.28, 0.18, 0.12]))
    edad0 = rng.uniform(13.5, 18.0)
    forma = rng.normal(0, 1)
    base = {
        "sprint": rng.normal(4.6, 0.15),   # 30m en segundos
        "salto": rng.normal(45, 5),        # cm
        "yoyo": rng.normal(1600, 200),     # metros
        "pase": rng.normal(74, 5),         # %
        "duelos": rng.normal(50, 6),       # %
    }
    for t, sem in enumerate(SEMESTRES):
        edad = edad0 + 0.5 * t
        cat = "Sub-15" if edad < 15.5 else ("Sub-17" if edad < 17.5 else "Sub-20")
        mej = ARQUETIPOS[arq] * t
        filas.append({
            "jugador": f"Jugador {i:02d}",
            "posicion": pos,
            "arquetipo": arq,
            "semestre": sem,
            "edad": round(edad, 1),
            "categoria": cat,
            "minutos": int(np.clip(rng.normal(900 + 120 * mej + 80 * forma, 180), 0, 1800)),
            "sprint_30m_s": round(base["sprint"] - 0.02 * mej - 0.01 * t + rng.normal(0, 0.04), 2),
            "salto_cm": round(base["salto"] + 1.2 * mej + 0.8 * t + rng.normal(0, 1), 1),
            "yoyo_m": int(base["yoyo"] + 60 * mej + 40 * t + rng.normal(0, 40)),
            "pase_pct": round(np.clip(base["pase"] + 1.5 * mej + rng.normal(0, 1.2), 40, 95), 1),
            "duelos_pct": round(np.clip(base["duelos"] + 1.2 * mej + rng.normal(0, 1.5), 30, 80), 1),
            "nota": rng.choice(NOTAS),
            "trimestre_nac": trimestre,
        })

pd.DataFrame(filas).to_csv("datos_ejemplo.csv", index=False)
print("OK: datos_ejemplo.csv generado")