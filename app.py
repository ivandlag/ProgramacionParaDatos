# -*- coding: utf-8 -*-
"""
Dashboard: Esperanza de vida en el mundo (OMS, 2000-2015)
Tarea 4 - Programación para el análisis de datos (UNAD)
Autor: Iván Darío Ladino Gahona - Grupo 35

Extensión comunicativa del EDA de la Tarea 3 (dataset E: Life Expectancy WHO).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Esperanza de vida en el mundo", page_icon="🌎", layout="wide")
sns.set_theme(style="whitegrid")

# Etiquetas en lenguaje común para la audiencia no técnica
TIPO = {"Developed": "Desarrollado", "Developing": "En desarrollo"}
COLORES = {"Desarrollado": "#1f77b4", "En desarrollo": "#d62728"}
COLORES_NIVEL = {"Baja": "#f1948a", "Media": "#f7dc6f", "Alta": "#82e0aa"}


def n(x, d=1):
    """Número con coma decimal, como se escribe en español."""
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def cargar_datos(ruta: str = "life_expectancy.csv") -> pd.DataFrame:
    """Carga y limpia el dataset igual que en la Tarea 3."""
    df = pd.read_csv(ruta)
    # Los nombres originales traen espacios sobrantes ("Life expectancy ", " BMI ")
    df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)
    df["Tipo de país"] = df["Status"].map(TIPO)
    # Nivel de escolaridad por terciles (mismos cortes de la Parte 2 de la Tarea 3)
    p33, p66 = df["Schooling"].quantile([1 / 3, 2 / 3])
    df["Nivel escolaridad"] = pd.cut(df["Schooling"], bins=[-np.inf, p33, p66, np.inf],
                                     labels=["Baja", "Media", "Alta"])
    return df


df = cargar_datos()

# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.header("Filtros")
    st.caption("Todos los números y gráficos se actualizan con estos filtros.")
    tipos = st.multiselect("Tipo de país", options=list(TIPO.values()), default=list(TIPO.values()))
    anios = st.slider("Años", min_value=int(df["Year"].min()), max_value=int(df["Year"].max()),
                      value=(int(df["Year"].min()), int(df["Year"].max())))
    esc_min, esc_max = float(df["Schooling"].min()), float(df["Schooling"].max())
    escolaridad = st.slider("Años promedio de estudio de la población", min_value=esc_min, max_value=esc_max,
                            value=(esc_min, esc_max), step=0.5)
    incluir_sin_dato = st.checkbox("Incluir registros sin dato de escolaridad", value=True)
    st.divider()
    st.caption("Fuente: Organización Mundial de la Salud y Naciones Unidas (compilado en Kaggle por K. Rajarshi).")

filtro = (df["Tipo de país"].isin(tipos)
          & df["Year"].between(*anios)
          & (df["Schooling"].between(*escolaridad) | (df["Schooling"].isna() & incluir_sin_dato)))
dff = df[filtro]

# ------------------------------------------------------------------ Encabezado
st.title("¿De qué depende cuánto vive la gente?")
st.markdown("**Esperanza de vida en 193 países entre 2000 y 2015**, con datos de la Organización Mundial de la Salud. "
            "Use los filtros de la izquierda para explorar por tipo de país, periodo y nivel de estudio.")

if dff.empty or dff["Life expectancy"].dropna().empty:
    st.warning("No hay registros con los filtros seleccionados. Amplíe el rango de años o de escolaridad, "
               "o seleccione al menos un tipo de país.")
    st.stop()

tab_hall, tab_expl, tab_vis, tab_est, tab_acerca = st.tabs(
    ["📌 Hallazgos", "🔎 Exploración de datos", "📊 Visualizaciones", "✅ Validación estadística", "ℹ️ Acerca del análisis"])


def grafico_brecha(data: pd.DataFrame):
    """Evolución de la esperanza de vida promedio por tipo de país."""
    tend = data.groupby(["Year", "Tipo de país"])["Life expectancy"].mean().unstack()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for col in tend.columns:
        ax.plot(tend.index, tend[col], marker="o", color=COLORES[col], label=col)
    ax.set_title("Cuántos años vive en promedio una persona, según el tipo de país", fontweight="bold")
    ax.set_xlabel("Año")
    ax.set_ylabel("Años de vida esperados")
    ax.legend(title="Tipo de país")
    fig.tight_layout()
    return fig


def grafico_estudio(data: pd.DataFrame):
    """Mediana de la esperanza de vida por nivel de estudio (lectura simple del violín de la Tarea 3)."""
    med = data.groupby("Nivel escolaridad", observed=False)["Life expectancy"].median().reindex(["Baja", "Media", "Alta"])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    barras = ax.bar(["Pocos años de estudio", "Estudio medio", "Muchos años de estudio"], med.values,
                    color=list(COLORES_NIVEL.values()))
    ax.bar_label(barras, labels=[f"{v:.0f} años" if pd.notna(v) else "sin datos" for v in med.values], padding=3)
    ax.set_title("Años de vida esperados según cuánto estudia la población", fontweight="bold")
    ax.set_ylabel("Años de vida (valor típico)")
    ax.set_ylim(0, max(90, np.nanmax(med.values) + 8) if med.notna().any() else 90)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ Hallazgos (Componente 2)
with tab_hall:
    st.subheader("Lo que muestran los datos, en pocas palabras")

    st.markdown("#### ¿Qué analicé?")
    st.markdown(
        "Revisé cuántos años se espera que viva una persona al nacer en 193 países, año por año, entre 2000 y 2015. "
        "Además de esa cifra, la base incluye información sobre educación, ingresos, gasto en salud, vacunación y "
        "enfermedades como el VIH/SIDA. Son casi 3.000 registros, uno por país y por año.")

    st.markdown("#### ¿Qué encontré?")
    c1, c2 = st.columns(2)
    for col_, fig_ in ((c1, grafico_brecha(df)), (c2, grafico_estudio(df))):
        col_.pyplot(fig_)
        plt.close(fig_)
    st.markdown(
        "- **El mundo vive más que antes.** En 15 años la esperanza de vida promedio pasó de unos 67 a casi 72 años.\n"
        "- **Pero la diferencia entre países sigue siendo grande.** En los países desarrollados una persona vive, en "
        "promedio, unos 12 años más que en los países en desarrollo. Esa distancia se ha reducido muy poco: de 12 a 11 años.\n"
        "- **Donde la gente estudia más, también se vive más.** En los países con más años de estudio la vida típica "
        "llega a 77 años; en los de menos estudio, a 60. Es la relación más fuerte de toda la base, pero no prueba que "
        "estudiar alargue la vida por sí solo: los países con más educación también suelen tener más ingresos y "
        "mejores servicios de salud.\n"
        "- **Gastar más en salud no se refleja tanto como se esperaría.** El porcentaje del gasto público dedicado a "
        "salud se relaciona poco con los años de vida, mucho menos que la educación o el ingreso.\n"
        "- **La mejora más rápida vino de controlar el VIH/SIDA.** En los países en desarrollo las muertes de niños por "
        "esta causa bajaron cerca de tres cuartas partes en el periodo.")

    st.markdown("#### ¿Qué significa?")
    st.markdown(
        "Vivir más no depende de un solo factor. Los países donde se vive más suelen tener, al mismo tiempo, más "
        "educación y más ingresos, así que estos datos **no prueban** que estudiar por sí solo alargue la vida; muestran "
        "que ambos avanzan juntos. Lo que sí dejan claro es que la brecha entre países ricos y pobres no se está cerrando "
        "sola, y que los programas enfocados en una enfermedad concreta, como el VIH/SIDA, sí produjeron cambios visibles.")

    st.markdown("#### ¿Qué se recomendaría?")
    st.markdown(
        "1. **Mirar la educación y la salud como una sola agenda**, porque en los datos aparecen siempre juntas.\n"
        "2. **Medir resultados y no solo presupuesto:** más gasto en salud no garantiza más años de vida si no llega "
        "a donde se necesita.\n"
        "3. **Replicar el enfoque de los programas contra el VIH/SIDA** en otras causas de muerte evitables.\n"
        "4. **Usar este tablero para comparar periodos y grupos de países** antes de decidir dónde invertir, y "
        "complementarlo con un estudio que controle los demás factores.")

# ------------------------------------------------------------------ Exploración
with tab_expl:
    st.subheader("Exploración de datos")
    le = dff["Life expectancy"].dropna()
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Registros", f"{len(dff):,}".replace(",", "."))
    m2.metric("Países", dff["Country"].nunique())
    m3.metric("Esperanza de vida media", f"{n(le.mean())} años")
    m4.metric("Desviación estándar", f"{n(le.std())} años" if len(le) > 1 else "—")
    m5.metric("Mediana", f"{n(le.median())} años")
    st.caption("La desviación estándar indica qué tan distintos son los valores entre sí: "
               "cuanto más alta, más desigual es la esperanza de vida entre los registros filtrados.")

    columnas = ["Country", "Year", "Tipo de país", "Life expectancy", "Schooling", "Nivel escolaridad",
                "GDP", "Adult Mortality", "HIV/AIDS", "Total expenditure", "Income composition of resources"]
    nombres = {"Country": "País", "Year": "Año", "Life expectancy": "Esperanza de vida (años)",
               "Schooling": "Años de estudio", "GDP": "PIB per cápita (USD)",
               "Adult Mortality": "Mortalidad adulta (por 1.000)", "HIV/AIDS": "Muertes VIH/SIDA 0-4 años (por 1.000)",
               "Total expenditure": "Gasto en salud (% del gasto público)",
               "Income composition of resources": "Índice de ingreso y educación"}
    buscar = st.text_input("Buscar un país (en inglés, por ejemplo Colombia)")
    tabla = dff[columnas].rename(columns=nombres)
    if buscar:
        tabla = tabla[tabla["País"].str.contains(buscar, case=False, na=False)]
    st.dataframe(tabla.sort_values(["País", "Año"]), use_container_width=True, hide_index=True, height=380)
    st.download_button("Descargar datos filtrados (CSV)", tabla.to_csv(index=False).encode("utf-8"),
                       file_name="esperanza_vida_filtrada.csv", mime="text/csv")

# ------------------------------------------------------------------ Visualizaciones (Tarea 3, Parte 3)
with tab_vis:
    st.subheader("Visualizaciones del análisis exploratorio")
    v1, v2 = st.columns(2)

    with v1:
        # Gráfico 2 de la Tarea 3: boxplot por tipo de país
        fig, ax = plt.subplots(figsize=(7, 4.5))
        orden = [t for t in ["Desarrollado", "En desarrollo"] if t in dff["Tipo de país"].unique()]
        sns.boxplot(data=dff, x="Tipo de país", y="Life expectancy", hue="Tipo de país", order=orden,
                    palette=COLORES, legend=False, ax=ax)
        ax.set_title("Distribución de la esperanza de vida por tipo de país", fontweight="bold")
        ax.set_xlabel("Tipo de país")
        ax.set_ylabel("Esperanza de vida (años)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption("La caja muestra dónde está la mitad central de los registros. En los países en desarrollo es más "
                   "baja y más amplia: hay mucha más desigualdad entre ellos.")

    with v2:
        # Gráfico 4 de la Tarea 3: dispersión escolaridad vs esperanza de vida
        fig, ax = plt.subplots(figsize=(7, 4.5))
        datos_disp = dff.dropna(subset=["Schooling", "Life expectancy"])
        sns.scatterplot(data=datos_disp, x="Schooling", y="Life expectancy", hue="Tipo de país",
                        palette=COLORES, alpha=0.55, ax=ax)
        if len(datos_disp) > 2:
            sns.regplot(data=datos_disp, x="Schooling", y="Life expectancy", scatter=False, color="black",
                        line_kws={"lw": 1.5}, ax=ax)
        ax.set_title("Años de estudio y esperanza de vida", fontweight="bold")
        ax.set_xlabel("Años promedio de estudio")
        ax.set_ylabel("Esperanza de vida (años)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        if len(datos_disp) > 2:
            r = datos_disp["Schooling"].corr(datos_disp["Life expectancy"])
            fuerza = "fuerte" if abs(r) >= 0.7 else "moderada" if abs(r) >= 0.4 else "débil"
            st.caption(f"Cada punto es un país en un año. La línea muestra la tendencia: donde hay más años de estudio "
                       f"suele haber más años de vida. La relación es {fuerza} ({n(r, 2)}; 1 sería una relación perfecta), "
                       f"pero no demuestra que una cosa cause la otra.")

    v3, v4 = st.columns(2)
    with v3:
        # Gráfico 5 de la Tarea 3: violín por nivel de escolaridad
        fig, ax = plt.subplots(figsize=(7, 4.5))
        datos_v = dff.dropna(subset=["Nivel escolaridad", "Life expectancy"]).astype({"Nivel escolaridad": str})
        niveles = [n for n in ["Baja", "Media", "Alta"] if n in datos_v["Nivel escolaridad"].unique()]
        if niveles:
            sns.violinplot(data=datos_v, x="Nivel escolaridad", y="Life expectancy", hue="Nivel escolaridad",
                           order=niveles, hue_order=niveles, palette=COLORES_NIVEL, inner="quartile",
                           legend=False, ax=ax)
        ax.set_title("Esperanza de vida según el nivel de estudio", fontweight="bold")
        ax.set_xlabel("Nivel de estudio de la población (tercios)")
        ax.set_ylabel("Esperanza de vida (años)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Un violín más ancho indica más países con ese valor. Con poco estudio, los valores están muy "
                   "dispersos y bajan hasta 36 años; con mucho estudio se concentran entre 72 y 82 años.")

    with v4:
        # Gráfico 7 de la Tarea 3: tendencia temporal de mortalidad adulta y VIH/SIDA
        var = st.radio("Indicador", ["Mortalidad adulta", "Muertes por VIH/SIDA en niños"], horizontal=True)
        col = "Adult Mortality" if var == "Mortalidad adulta" else "HIV/AIDS"
        unidad = "por cada 1.000 adultos" if col == "Adult Mortality" else "por cada 1.000 nacidos vivos (0-4 años)"
        tend = dff.groupby(["Year", "Tipo de país"])[col].mean().unstack()
        fig, ax = plt.subplots(figsize=(7, 4.1))
        for c in tend.columns:
            ax.plot(tend.index, tend[c], marker="o", color=COLORES[c], label=c)
        ax.set_title(f"Evolución de {var.lower()}", fontweight="bold")
        ax.set_xlabel("Año")
        ax.set_ylabel(f"Muertes {unidad}", fontsize=9)
        ax.legend(title="Tipo de país")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Gráfico 8 de la Tarea 3: gráfico combinado PIB, esperanza de vida, tipo de país y escolaridad
    st.markdown("##### Ingreso, estudio y esperanza de vida en un mismo año")
    anios_disp = sorted(dff["Year"].unique())
    anio_sel = st.select_slider("Año a mostrar", options=anios_disp, value=2014 if 2014 in anios_disp else anios_disp[-1])
    d_anio = dff[dff["Year"] == anio_sel].dropna(subset=["GDP", "Life expectancy", "Schooling"])
    d_anio = d_anio[d_anio["GDP"] > 0]
    if d_anio.empty:
        st.info("No hay datos completos de ingreso y estudio para ese año con los filtros actuales.")
    else:
        fig, ax = plt.subplots(figsize=(11, 5))
        d_anio = d_anio.rename(columns={"Schooling": "Años de estudio"})
        sns.scatterplot(data=d_anio, x="GDP", y="Life expectancy", hue="Tipo de país", size="Años de estudio",
                        sizes=(15, 300), alpha=0.65, palette=COLORES, ax=ax)
        ax.set_xscale("log")
        ax.set_title(f"Ingreso por persona, estudio y esperanza de vida por país ({anio_sel})", fontweight="bold")
        ax.set_xlabel("Ingreso por persona (PIB per cápita en USD, escala logarítmica)")
        ax.set_ylabel("Esperanza de vida (años)")
        ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", title="")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Cada punto es un país; los puntos más grandes tienen más años de estudio. Subir el ingreso ayuda "
                   "mucho en los países más pobres y cada vez menos en los más ricos.")

# ------------------------------------------------------------------ Validación estadística (Tarea 3, Parte 1)
with tab_est:
    st.subheader("¿La diferencia entre países desarrollados y en desarrollo es real?")
    des = dff.loc[dff["Tipo de país"] == "Desarrollado", "Life expectancy"].dropna()
    endes = dff.loc[dff["Tipo de país"] == "En desarrollo", "Life expectancy"].dropna()
    if len(des) < 2 or len(endes) < 2:
        st.info("Para esta comparación seleccione los dos tipos de país en los filtros.")
    else:
        t_est, p_val = stats.ttest_ind(des, endes, equal_var=False)
        dif = des.mean() - endes.mean()
        e1, e2, e3 = st.columns(3)
        e1.metric("Promedio en países desarrollados", f"{n(des.mean())} años", help=f"{len(des)} registros")
        e2.metric("Promedio en países en desarrollo", f"{n(endes.mean())} años", help=f"{len(endes)} registros")
        e3.metric("Diferencia", f"{n(dif)} años")
        if p_val < 0.05:
            st.success(f"**Sí, la diferencia es real.** Con los filtros actuales, en los países desarrollados se vive en "
                       f"promedio {n(dif)} años más. Una diferencia así es demasiado grande para explicarse por el azar: "
                       f"si los dos grupos vivieran lo mismo, la probabilidad de ver una brecha como esta sería "
                       f"prácticamente nula.")
        else:
            st.warning("Con los filtros actuales la diferencia es pequeña o hay pocos datos, así que no se puede "
                       "asegurar que sea real; podría deberse al azar.")
        st.caption("Ojo: cada país aparece varias veces (una por año), así que la comparación es una aproximación. "
                   "Además, que exista la diferencia no explica por qué ocurre.")
        with st.expander("Detalle técnico (para especialistas)"):
            st.markdown(
                f"- Prueba: t de Welch para dos muestras independientes con varianzas distintas "
                f"(`scipy.stats.ttest_ind`, `equal_var=False`), α = 0,05.\n"
                f"- H0: la media de la esperanza de vida es igual en ambos grupos. H1: las medias son diferentes.\n"
                f"- Estadístico t = {t_est:.3f}; valor p = {p_val:.2e}.\n"
                f"- Con todos los datos (Tarea 3): t = 47,868 y p < 0,001; se rechaza H0.")

# ------------------------------------------------------------------ Acerca del análisis
with tab_acerca:
    st.subheader("Acerca del análisis")
    st.markdown(
        "Este tablero es la versión para público general del análisis exploratorio (EDA) realizado en la Tarea 3 del "
        "curso *Programación para el análisis de datos* de la UNAD. No es un análisis nuevo: usa los mismos datos, "
        "gráficos y conclusiones, presentados de forma interactiva.\n\n"
        "- **Datos:** *Life Expectancy (WHO)*, 2.938 registros de 193 países entre 2000 y 2015, publicados por el "
        "Observatorio Mundial de la Salud de la OMS y complementados con datos económicos de Naciones Unidas.\n"
        "- **Limpieza:** se eliminaron los espacios sobrantes en los nombres de las columnas y el nivel de estudio se "
        "dividió en tres grupos del mismo tamaño (bajo hasta 10,9 años, medio hasta 13,4 años y alto).\n"
        "- **Limitaciones:** hay datos faltantes en algunas variables (por ejemplo, población y PIB), algunos valores "
        "parecen errores de registro, y las relaciones observadas no prueban causa y efecto.\n"
        "- **Autor:** Iván Darío Ladino Gahona, Grupo 35. Tutor: Felipe Alexander Pipicano Guzmán. "
        "Universidad Nacional Abierta y a Distancia (UNAD), noviembre de 2026.")
