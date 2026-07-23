import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go

# ---------- Paleta Atlético Nacional (modo oscuro) ----------
VERDE = "#2FBF5F"
VERDE_BRILLO = "#5CE08A"
VERDE_OSC = "#12301F"
DORADO = "#E6C15A"
GRISES = "#7FA890"
TEXTO = "#EAF5EE"
SECUENCIA = [VERDE, VERDE_BRILLO, DORADO, GRISES, "#9AD9B0"]

def estilo_nacional(fig, sin_leyenda=False, titulo_leyenda=None):
    fig.update_layout(
        colorway=SECUENCIA,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=TEXTO,
        title_font_color=TEXTO,
        showlegend=not sin_leyenda,
    )
    if titulo_leyenda is not None:
        fig.update_layout(legend_title_text=titulo_leyenda)
    fig.update_xaxes(gridcolor="#1E4230", zeroline=False)
    fig.update_yaxes(gridcolor="#1E4230", zeroline=False)
    return fig

st.set_page_config(page_title="Demo Formativo", layout="wide")

@st.cache_data
def cargar():
    return pd.read_csv("datos_ejemplo.csv")

df = cargar()

# ---------- Encabezado ----------
st.warning("DEMO CON DATOS SINTÉTICOS — ningún dato corresponde a jugadores reales.")
st.markdown(
    f"<div style='background:{VERDE_OSC};border-left:6px solid {VERDE};"
    f"padding:14px 20px;border-radius:8px;'>"
    f"<h2 style='color:{TEXTO};margin:0;'>Seguimiento del fútbol formativo</h2>"
    f"<p style='color:{VERDE_BRILLO};margin:0;'>Concepto de tablero · datos sintéticos de ejemplo</p>"
    f"</div>", unsafe_allow_html=True)
st.write("")

# ---------- Vista 1: ficha longitudinal ----------
jugador = st.sidebar.selectbox("Jugador", sorted(df["jugador"].unique()))
d = df[df["jugador"] == jugador].sort_values("semestre")
ult = d.iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Posición", ult["posicion"])
c2.metric("Categoría actual", ult["categoria"])
c3.metric("Edad", f"{ult['edad']} años")
c4.metric("Minutos último semestre", int(ult["minutos"]))

st.subheader("Minutos por semestre")
fig = px.bar(d, x="semestre", y="minutos", color="categoria",
             color_discrete_sequence=SECUENCIA)
st.plotly_chart(estilo_nacional(fig, titulo_leyenda="Categoría"), width='stretch')

st.subheader("Evolución física y técnica (percentil vs. su categoría)")
mets = st.multiselect("Indicadores",
    ["sprint_30m_s", "salto_cm", "yoyo_m", "pase_pct", "duelos_pct"],
    default=["salto_cm", "pase_pct"])

INVERTIR = {"sprint_30m_s"}  # menor sprint = mejor
dfp = df.copy()
for m in ["sprint_30m_s", "salto_cm", "yoyo_m", "pase_pct", "duelos_pct"]:
    r = dfp.groupby(["semestre", "categoria"])[m].rank(pct=True) * 100
    dfp[m] = (100 - r) if m in INVERTIR else r

if mets:
    dp = dfp[dfp["jugador"] == jugador].sort_values("semestre")
    dd = dp.melt(id_vars="semestre", value_vars=mets,
                 var_name="indicador", value_name="percentil")
    fig = px.line(dd, x="semestre", y="percentil", color="indicador",
                  markers=True, color_discrete_sequence=SECUENCIA)
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(estilo_nacional(fig, titulo_leyenda="Indicador"), width='stretch')

st.subheader("Notas del cuerpo técnico")
st.table(d[["semestre", "categoria", "nota"]].reset_index(drop=True))

# ---------- Vista 2: embudo y sesgo de edad relativa ----------
st.divider()
st.header("Vista 2 — Embudo de desarrollo y sesgo de edad relativa")

perfil = df.sort_values("semestre").groupby("jugador").last().reset_index()
n = perfil["jugador"].nunique()

# A. Sesgo de edad relativa (RAE)
st.subheader("A. ¿A quién selecciona la cantera? (trimestre de nacimiento)")
c = perfil["trimestre_nac"].value_counts().reindex([1, 2, 3, 4], fill_value=0)
rae = pd.DataFrame({"trimestre": ["Q1 (Ene-Mar)", "Q2", "Q3", "Q4 (Oct-Dic)"],
                    "jugadores": c.values})
fig = px.bar(rae, x="trimestre", y="jugadores", text="jugadores",
             color_discrete_sequence=[VERDE])
fig.add_hline(y=n * 0.25, line_dash="dash", line_color=DORADO,
              annotation_text="Esperado si no hubiera sesgo (25%)")
st.plotly_chart(estilo_nacional(fig, sin_leyenda=True), width='stretch')
q1, q4 = c[1] / n * 100, c[4] / n * 100
st.caption(f"Q1 concentra el {q1:.0f}% de la cantera; Q4 solo el {q4:.0f}%. "
           f"Una brecha grande sugiere que se está seleccionando madurez física, no talento.")

# B. Embudo de desarrollo
st.subheader("B. Embudo: de la cantera al perfil de primer equipo")
llego = perfil.query("categoria == 'Sub-20'")["jugador"].nunique()
minutos = perfil.query("categoria == 'Sub-20' and minutos > 1000")["jugador"].nunique()
umbral = perfil["pase_pct"].quantile(0.75)
top = perfil.query("categoria == 'Sub-20' and minutos > 1000 and pase_pct > @umbral")["jugador"].nunique()
emb = pd.DataFrame({"etapa": ["En cantera", "Llegó a Sub-20",
                              "Con minutos (>1000)", "Perfil 1er equipo"],
                    "n": [n, llego, minutos, top]})
fig = px.funnel(emb, x="n", y="etapa", color_discrete_sequence=[VERDE])
st.plotly_chart(estilo_nacional(fig, sin_leyenda=True), width='stretch')

# C. Cruce RAE x promoción
st.subheader("C. Tasa de promoción según trimestre de nacimiento")
perfil["promovido"] = perfil.eval("categoria == 'Sub-20' and minutos > 1000").astype(int)
tasa = (perfil.groupby("trimestre_nac")["promovido"].mean() * 100).reindex([1, 2, 3, 4]).fillna(0)
tdf = pd.DataFrame({"trimestre": ["Q1", "Q2", "Q3", "Q4"], "tasa_promocion": tasa.values})
fig = px.bar(tdf, x="trimestre", y="tasa_promocion", text_auto=".0f",
             color_discrete_sequence=[VERDE])
st.plotly_chart(estilo_nacional(fig, sin_leyenda=True), width='stretch')
st.caption("Si Q1 también promociona a mayor tasa, el club está AMPLIFICANDO el sesgo. "
           "Si Q3/Q4 promocionan igual o más, significa que los tardíos que sobreviven "
           "la selección temprana suelen ser mejores — un argumento de datos para retenerlos.")

# ---------- Vista 3: Radar de perfil ----------
st.divider()
st.header("Vista 3 — Perfil del jugador (radar de percentiles)")

IND = ["sprint_30m_s", "salto_cm", "yoyo_m", "pase_pct", "duelos_pct"]
ETIQ = {"sprint_30m_s": "Velocidad", "salto_cm": "Salto", "yoyo_m": "Resistencia",
        "pase_pct": "Pase", "duelos_pct": "Duelos"}
dr = dfp[dfp["jugador"] == jugador].sort_values("semestre").iloc[-1]
ejes = [ETIQ[m] for m in IND] + [ETIQ[IND[0]]]
vals = [dr[m] for m in IND] + [dr[IND[0]]]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=vals, theta=ejes, fill="toself",
                              name=jugador, line_color=VERDE))
fig.add_trace(go.Scatterpolar(r=[50] * len(ejes), theta=ejes,
                              name="Media categoría (P50)",
                              line=dict(color=DORADO, dash="dash")))
fig.update_polars(bgcolor="rgba(0,0,0,0)",
                  radialaxis=dict(range=[0, 100], gridcolor="#1E4230"),
                  angularaxis=dict(gridcolor="#1E4230"))
st.plotly_chart(estilo_nacional(fig), width='stretch')
st.caption("Cada eje es el percentil del jugador dentro de su categoría en el último semestre. "
           "Área grande = perfil por encima de la media; picos = fortalezas diferenciales.")

# ---------- Vista 4: Alertas automáticas ----------
st.divider()
st.header("Vista 4 — Alertas automáticas")

sems = sorted(df["semestre"].unique())
ult_sem, prev_sem = sems[-1], sems[-2]
minu = df[df["semestre"] == ult_sem][["jugador", "minutos", "categoria", "posicion"]]
pctl = dfp[dfp["semestre"] == ult_sem][["jugador", "pase_pct", "duelos_pct"]]
prev = df[df["semestre"] == prev_sem][["jugador", "minutos"]].rename(columns={"minutos": "min_prev"})
al = minu.merge(pctl, on="jugador").merge(prev, on="jugador", how="left")
al["dif_min"] = al["minutos"] - al["min_prev"]

alertas = []
for _, r in al.iterrows():
    if r["pase_pct"] >= 70 and r["minutos"] < 600:
        alertas.append([r["jugador"], r["posicion"], "Talento con pocos minutos",
                        "Percentil de pase alto pero minutos bajos: riesgo de fuga o descarte injusto."])
    if pd.notna(r["dif_min"]) and r["dif_min"] <= -400:
        alertas.append([r["jugador"], r["posicion"], "Caída de minutos",
                        f"Bajó {int(-r['dif_min'])} min vs. semestre anterior: revisar lesión o decisión técnica."])
    if r["duelos_pct"] >= 80:
        alertas.append([r["jugador"], r["posicion"], "Perfil físico destacado",
                        "Top de su categoría en duelos: candidato a probar en categoría superior."])

if alertas:
    st.dataframe(pd.DataFrame(alertas, columns=["Jugador", "Posición", "Alerta", "Detalle"]),
                 width='stretch', hide_index=True)
else:
    st.success("Sin alertas en el último semestre.")
st.caption("Reglas de ejemplo. En producción, los umbrales se definen con el cuerpo técnico.")

# ---------- Vista 5: Comparador directo de jugadores ----------
st.divider()
st.header("Vista 5 — Comparador directo de jugadores")

nombres = sorted(df["jugador"].unique())
colA, colB = st.columns(2)
jA = colA.selectbox("Jugador A", nombres, index=0, key="jA")
jB = colB.selectbox("Jugador B", nombres, index=1, key="jB")

def ult_pctl(j):
    return dfp[dfp["jugador"] == j].sort_values("semestre").iloc[-1]

rA, rB = ult_pctl(jA), ult_pctl(jB)
ejes = [ETIQ[m] for m in IND] + [ETIQ[IND[0]]]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=[rA[m] for m in IND] + [rA[IND[0]]], theta=ejes,
                              fill="toself", name=jA, line_color=VERDE))
fig.add_trace(go.Scatterpolar(r=[rB[m] for m in IND] + [rB[IND[0]]], theta=ejes,
                              fill="toself", name=jB, line_color=DORADO))
fig.update_polars(bgcolor="rgba(0,0,0,0)",
                  radialaxis=dict(range=[0, 100], gridcolor="#1E4230"),
                  angularaxis=dict(gridcolor="#1E4230"))
st.plotly_chart(estilo_nacional(fig), width='stretch')

st.subheader("Datos del último semestre")
raw = df.sort_values("semestre").groupby("jugador").last()
cols = ["posicion", "categoria", "edad", "minutos",
        "sprint_30m_s", "salto_cm", "yoyo_m", "pase_pct", "duelos_pct"]
tabla = raw.loc[[jA, jB], cols].T
tabla.columns = [jA, jB]
st.dataframe(tabla, width='stretch')
st.caption("Radar = percentiles dentro de su categoría. Tabla = valores crudos. "
           "Herramienta directa para decidir entre dos jugadores de la misma posición.")