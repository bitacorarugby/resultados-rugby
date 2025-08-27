import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Resultados Rugby", layout="wide")
st.title("🏉 Resultados de Rugby")

LOGOS_DIR = "logos"

# Función para encontrar logo PNG o JPEG
def find_logo(equipo):
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(LOGOS_DIR, f"{equipo}.{ext}")
        if os.path.exists(path):
            return path
    return None

# Subida de CSV
uploaded_file = st.file_uploader("Sube un CSV con los partidos", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Sidebar filtros
        st.sidebar.header("⚙️ Filtros")
        competiciones = st.sidebar.multiselect("Competición", options=df["Competicion"].unique())
        temporadas = st.sidebar.multiselect("Temporada", options=df["Temporada"].unique())
        jornadas = st.sidebar.multiselect("Jornada", options=df["Jornada"].unique())
        equipos = st.sidebar.multiselect("Equipo", options=pd.concat([df["Local"], df["Visitante"]]).unique())

        if competiciones:
            df = df[df["Competicion"].isin(competiciones)]
        if temporadas:
            df = df[df["Temporada"].isin(temporadas)]
        if jornadas:
            df = df[df["Jornada"].isin(jornadas)]
        if equipos:
            df = df[(df["Local"].isin(equipos)) | (df["Visitante"].isin(equipos))]

        # Sistema de puntos
        st.sidebar.header("🏆 Sistema de puntos")
        pts_victoria = st.sidebar.number_input("Puntos por victoria", 0, 10, 4)
        pts_empate = st.sidebar.number_input("Puntos por empate", 0, 10, 2)
        pts_derrota = st.sidebar.number_input("Puntos por derrota", 0, 10, 0)
        bonus_defensivo = st.sidebar.number_input("Bonus defensivo", 0, 5, 1)

        # ----- Mostrar Partidos -----
        st.subheader("📋 Partidos filtrados")
        for _, row in df.iterrows():
            col1, col2, col3 = st.columns([1,1,1])
            
            with col1:
                logo_path = find_logo(row['Local'])
                if logo_path:
                    st.image(logo_path, width=40)
                st.markdown(f"### {row['Local']}")
            
            with col2:
                st.markdown(f"## {row['PuntosLocal']} - {row['PuntosVisitante']}")
            
            with col3:
                logo_path = find_logo(row['Visitante'])
                if logo_path:
                    st.image(logo_path, width=40)
                st.markdown(f"### {row['Visitante']}")
            
            st.caption(f"{row['Competicion']} | {row['Temporada']} | {row['Jornada']}")
            st.markdown("---")

        # ----- Clasificación -----
        equipos_dict = {}
        for _, row in df.iterrows():
            local, visitante = row["Local"], row["Visitante"]
            pl, pv = row["PuntosLocal"], row["PuntosVisitante"]

            for eq in [local, visitante]:
                if eq not in equipos_dict:
                    equipos_dict[eq] = {"PJ":0, "PG":0, "PE":0, "PP":0, "PF":0, "PC":0, "Puntos":0}

            equipos_dict[local]["PJ"] += 1
            equipos_dict[visitante]["PJ"] += 1
            equipos_dict[local]["PF"] += pl
            equipos_dict[local]["PC"] += pv
            equipos_dict[visitante]["PF"] += pv
            equipos_dict[visitante]["PC"] += pl

            if pl > pv:
                equipos_dict[local]["PG"] += 1
                equipos_dict[visitante]["PP"] += 1
                equipos_dict[local]["Puntos"] += pts_victoria
                equipos_dict[visitante]["Puntos"] += pts_derrota
                if (pl - pv) <= 7:
                    equipos_dict[visitante]["Puntos"] += bonus_defensivo
            elif pv > pl:
                equipos_dict[visitante]["PG"] += 1
                equipos_dict[local]["PP"] += 1
                equipos_dict[visitante]["Puntos"] += pts_victoria
                equipos_dict[local]["Puntos"] += pts_derrota
                if (pv - pl) <= 7:
                    equipos_dict[local]["Puntos"] += bonus_defensivo
            else:
                equipos_dict[local]["PE"] += 1
                equipos_dict[visitante]["PE"] += 1
                equipos_dict[local]["Puntos"] += pts_empate
                equipos_dict[visitante]["Puntos"] += pts_empate

        clasificacion = pd.DataFrame.from_dict(equipos_dict, orient="index").reset_index()
        clasificacion.rename(columns={"index":"Equipo"}, inplace=True)
        clasificacion["Dif"] = clasificacion["PF"] - clasificacion["PC"]
        clasificacion = clasificacion.sort_values(by=["Puntos","Dif"], ascending=[False, False]).reset_index(drop=True)

        # Mostrar Clasificación visual
        st.subheader("🏆 Clasificación visual")
        max_puntos = clasificacion["Puntos"].max()

        for i, row in clasificacion.iterrows():
            if i == 0:
                color = "gold"
            elif i == 1:
                color = "silver"
            elif i == 2:
                color = "#cd7f32"
            else:
                color = "white"
            
            cols = st.columns([1,3,1,1,1,1,1,1,1,2])
            
            # Logo
            logo_path = find_logo(row["Equipo"])
            if logo_path:
                cols[0].image(logo_path, width=40)
            else:
                cols[0].write("")
            
            # Nombre con color top3
            cols[1].markdown(f"<div style='background-color:{color};padding:5px'>{row['Equipo']}</div>", unsafe_allow_html=True)
            
            # Estadísticas
            cols[2].write(row["PJ"])
            cols[3].write(row["PG"])
            cols[4].write(row["PE"])
            cols[5].write(row["PP"])
            cols[6].write(row["PF"])
            cols[7].write(row["PC"])
            cols[8].write(row["Dif"])
            
            # Barra de puntos
            barra = int((row["Puntos"]/max_puntos)*100)
            cols[9].markdown(f"<div style='background-color:#4caf50;width:{barra}%;color:white;text-align:center'>{row['Puntos']}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error al procesar el CSV: {e}")

else:
    st.info("👉 Sube un CSV con columnas: Local,Visitante,PuntosLocal,PuntosVisitante,Competicion,Temporada,Jornada")

