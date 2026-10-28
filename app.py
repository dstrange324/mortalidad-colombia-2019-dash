"""Aplicacion web dinamica: Mortalidad en Colombia 2019.

Ejecutar local:   python app.py        -> http://localhost:8050
Despliegue PaaS:  gunicorn app:server  (ver requirements.txt / Procfile)
"""

import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

df = pd.read_parquet(os.path.join(DATA_DIR, "mortalidad_2019.parquet"))
cie10 = pd.read_parquet(os.path.join(DATA_DIR, "cie10.parquet"))
with open(os.path.join(DATA_DIR, "colombia_departamentos.geojson"), encoding="utf-8") as fh:
    geojson_dptos = json.load(fh)
with open(os.path.join(DATA_DIR, "colombia_municipios.geojson"), encoding="utf-8") as fh:
    geojson_mpios = json.load(fh)

DESCRIPCION_CIE10 = dict(zip(cie10["CODIGO"], cie10["DESCRIPCION"]))

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre",
    11: "Noviembre", 12: "Diciembre",
}

SEXOS = ["Hombre", "Mujer", "Indeterminado"]

ORDEN_CATEGORIAS_EDAD = [
    "Mortalidad neonatal (< 1 mes)",
    "Mortalidad infantil (1-11 meses)",
    "Primera infancia (1-4 anos)",
    "Ninez (5-14 anos)",
    "Adolescencia (15-19 anos)",
    "Juventud (20-29 anos)",
    "Adultez temprana (30-44 anos)",
    "Adultez intermedia (45-59 anos)",
    "Vejez (60-84 anos)",
    "Longevidad / Centenarios (85-100+ anos)",
    "Edad desconocida",
]

# Paleta sobria y consistente
COLOR_PRIMARIO = "#16324f"      # azul petroleo oscuro
COLOR_ACENTO = "#c0392b"        # rojo ladrillo
COLOR_HOMBRE = "#2c6fbb"
COLOR_MUJER = "#d56fa1"
COLOR_INDET = "#95a5a6"
COLOR_OTROS = "#9aa5b1"

LAYOUT_BASE = dict(
    font_family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    margin=dict(l=10, r=10, t=12, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    autosize=True,
)

# ---------------------------------------------------------------------------
# Estilos de cartografia (MapLibre, sin necesidad de token)
# ---------------------------------------------------------------------------
ESRI_SATELITAL = {
    "version": 8,
    "sources": {
        "esri-imagery": {
            "type": "raster",
            "tiles": [
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
            "attribution": "Esri, Maxar, Earthstar Geographics",
        },
        "esri-labels": {
            "type": "raster",
            "tiles": [
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
        },
    },
    "layers": [
        {"id": "esri-imagery", "type": "raster", "source": "esri-imagery"},
        {"id": "esri-labels", "type": "raster", "source": "esri-labels"},
    ],
}

ESTILOS_MAPA = {
    "Satelital (Esri)": ESRI_SATELITAL,
    "OpenStreetMap": "open-street-map",
    "Carto Claro": "carto-positron",
    "Carto Oscuro": "carto-darkmatter",
    "Carto Voyager": "carto-voyager",
}
ESTILO_DEFECTO = "Satelital (Esri)"

# ---------------------------------------------------------------------------
# Catalogos para los filtros y convencion de color por departamento
# ---------------------------------------------------------------------------
DEPARTAMENTOS = (
    df[["COD_DEPARTAMENTO", "DEPARTAMENTO"]]
    .drop_duplicates()
    .sort_values("DEPARTAMENTO")
    .values.tolist()
)

# Convencion general: un color fijo por departamento en todo el dashboard
_PALETA = px.colors.qualitative.Light24 + px.colors.qualitative.Dark24
DEPTO_COLORES = {
    nombre: _PALETA[i % len(_PALETA)]
    for i, (_, nombre) in enumerate(DEPARTAMENTOS)
}

# Causas de muerte presentes en los datos, ordenadas por frecuencia
_causas_freq = df.groupby("COD_MUERTE").size().sort_values(ascending=False)
OPCIONES_CAUSAS = [{"label": "Todas las causas", "value": "TODAS"}] + [
    {
        "label": f"{cod} - {DESCRIPCION_CIE10.get(cod, 'Sin descripcion')[:48]}",
        "value": cod,
    }
    for cod in _causas_freq.index
]


def _bounds_feature(feature):
    """[oeste, sur, este, norte] de una geometria GeoJSON."""
    lons, lats = [], []

    def rec(coords):
        if isinstance(coords[0], (int, float)):
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                rec(c)

    rec(feature["geometry"]["coordinates"])
    return min(lons), min(lats), max(lons), max(lats)


BOUNDS_DPTO = {
    f["properties"]["DPTO_CCDGO"]: _bounds_feature(f)
    for f in geojson_dptos["features"]
}

VISTA_NACIONAL = dict(center={"lat": 4.2, "lon": -73.6}, zoom=4.6)


def _filtrar(dpto, mes, causa, sexo):
    """Aplica los cuatro filtros principales al dataset."""
    dff = df
    if dpto != "TODOS":
        dff = dff[dff["COD_DEPARTAMENTO"] == int(dpto)]
    if mes != 0:
        dff = dff[dff["MES"] == mes]
    if causa != "TODAS":
        dff = dff[dff["COD_MUERTE"] == causa]
    if sexo != "TODOS":
        dff = dff[dff["SEXO"] == sexo]
    return dff


def _figura_vacia():
    """Figura de reemplazo cuando los filtros no devuelven datos."""
    fig = go.Figure()
    fig.add_annotation(text="Sin datos para los filtros seleccionados",
                       showarrow=False,
                       font=dict(size=13, color="#7c93a8"))
    fig.update_layout(**LAYOUT_BASE, xaxis_visible=False, yaxis_visible=False)
    return fig


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
def fig_mapa(dpto, mes, causa, sexo, estilo):
    """Coropletico nacional por departamento o, al filtrar, por municipio."""
    dff = _filtrar("TODOS" if dpto == "TODOS" else dpto, mes, causa, sexo)

    if dpto == "TODOS":
        agg = (
            dff.groupby(["COD_DEPARTAMENTO", "DEPARTAMENTO"], as_index=False)
            .size().rename(columns={"size": "TOTAL"})
        )
        agg["CODIGO"] = agg["COD_DEPARTAMENTO"].apply(lambda c: f"{c:02d}")
        geojson, fid, hover = geojson_dptos, "properties.DPTO_CCDGO", "DEPARTAMENTO"
        bounds = None
    else:
        agg = (
            dff.groupby(["COD_DANE", "MUNICIPIO"], as_index=False)
            .size().rename(columns={"size": "TOTAL"})
        )
        agg["CODIGO"] = agg["COD_DANE"].apply(lambda c: f"{c:05d}")
        geojson = {
            "type": "FeatureCollection",
            "features": [f for f in geojson_mpios["features"]
                         if f["properties"]["DPTO_CCDGO"] == dpto],
        }
        fid, hover = "properties.MPIO_CCNCT", "MUNICIPIO"
        o, s, e, n = BOUNDS_DPTO[dpto]
        pad = 0.12
        bounds = {"west": o - pad, "south": s - pad,
                  "east": e + pad, "north": n + pad}

    fig = px.choropleth_map(
        agg, geojson=geojson, locations="CODIGO", featureidkey=fid,
        color="TOTAL", hover_name=hover,
        hover_data={"CODIGO": False, "TOTAL": ":,"},
        color_continuous_scale="Reds", opacity=0.7,
        map_style=ESTILOS_MAPA[estilo],
        labels={"TOTAL": "Muertes"},
        center=VISTA_NACIONAL["center"], zoom=VISTA_NACIONAL["zoom"],
    )
    if bounds is not None:
        fig.update_layout(map_bounds=bounds)
    fig.update_layout(
        font_family=LAYOUT_BASE["font_family"],
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(
            title="Muertes", thickness=14, len=0.55, x=0.005, y=0.28,
            bgcolor="rgba(255,255,255,0.75)", outlinewidth=0,
        ),
    )
    return fig


def fig_lineas_mes(dpto, mes_sel, causa, sexo):
    """Total de muertes por mes (resalta el mes filtrado)."""
    dff = _filtrar(dpto, 0, causa, sexo)  # la linea siempre muestra el ano
    por_mes = dff.groupby("MES", as_index=False).size().rename(columns={"size": "TOTAL"})
    por_mes["MES_NOMBRE"] = por_mes["MES"].map(MESES)
    por_mes = por_mes.sort_values("MES")

    fig = px.line(por_mes, x="MES_NOMBRE", y="TOTAL", markers=True,
                  labels={"MES_NOMBRE": "Mes", "TOTAL": "Muertes"})
    fig.update_traces(line_color=COLOR_PRIMARIO, line_width=2.5,
                      marker=dict(size=6, color=COLOR_ACENTO),
                      line_shape="spline", line_smoothing=0.6,
                      selector=dict(type="scatter"))
    if mes_sel != 0:
        fila = por_mes[por_mes["MES"] == mes_sel]
        if not fila.empty:
            fig.add_scatter(x=fila["MES_NOMBRE"], y=fila["TOTAL"],
                            mode="markers", showlegend=False,
                            marker=dict(size=15, color="rgba(192,57,43,0.30)",
                                        symbol="circle"))
    fig.update_layout(**LAYOUT_BASE, hovermode="x unified")
    fig.update_yaxes(rangemode="tozero", gridcolor="#eceff3",
                     zerolinecolor="#eceff3")
    fig.update_xaxes(tickangle=-45, tickfont_size=9)
    return fig


def fig_ciudades_violentas(dpto, mes, causa, sexo):
    """5 ciudades mas violentas: homicidios por arma de fuego (CIE-10 X95*)."""
    dff = _filtrar(dpto, mes, causa, sexo)
    x95 = dff[dff["COD_MUERTE"].str.startswith("X95")]
    top5 = (
        x95.groupby("MUNICIPIO", as_index=False).size()
        .rename(columns={"size": "HOMICIDIOS"})
        .nlargest(5, "HOMICIDIOS").sort_values("HOMICIDIOS")
    )
    if top5.empty:
        return _figura_vacia()
    fig = px.bar(top5, x="HOMICIDIOS", y="MUNICIPIO", orientation="h",
                 text="HOMICIDIOS",
                 labels={"HOMICIDIOS": "Homicidios (X95*)", "MUNICIPIO": ""})
    fig.update_traces(marker_color=COLOR_ACENTO, marker_line_width=0,
                      textposition="outside", opacity=0.9)
    fig.update_layout(**{**LAYOUT_BASE, "margin": dict(l=10, r=46, t=12, b=10)},
                      showlegend=False, yaxis_tickfont_size=10)
    fig.update_xaxes(gridcolor="#eceff3", zerolinecolor="#eceff3",
                     range=[0, top5["HOMICIDIOS"].max() * 1.18])
    return fig


def fig_pie_menor_mortalidad(dpto, mes, causa, sexo):
    """10 ciudades con menor indice de mortalidad (menos defunciones)."""
    dff = _filtrar(dpto, mes, causa, sexo)
    por_mpio = (
        dff.groupby("MUNICIPIO", as_index=False).size()
        .rename(columns={"size": "TOTAL"})
    )
    bottom10 = por_mpio.nsmallest(10, "TOTAL")
    if bottom10.empty:
        return _figura_vacia()
    fig = px.pie(bottom10, names="MUNICIPIO", values="TOTAL",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textposition="inside", textinfo="label+value",
                      textfont_size=10,
                      marker=dict(line=dict(color="white", width=2)),
                      hovertemplate="%{label}<br>Muertes: %{value}<extra></extra>")
    fig.update_layout(**LAYOUT_BASE, showlegend=False)
    return fig


def fig_principales_causas(dpto, mes, causa, sexo):
    """10 principales causas de muerte, cada barra dividida por departamento."""
    dff = _filtrar(dpto, mes, causa, sexo)
    if dff.empty:
        return _figura_vacia()
    top10_cod = dff.groupby("COD_MUERTE").size().nlargest(10).index.tolist()
    d10 = dff[dff["COD_MUERTE"].isin(top10_cod)].copy()

    # Departamentos con mas casos dentro de esas causas; el resto = "Otros"
    top_dptos = d10.groupby("DEPARTAMENTO").size().nlargest(5).index.tolist()
    d10["SEGMENTO"] = d10["DEPARTAMENTO"].where(
        d10["DEPARTAMENTO"].isin(top_dptos), "Otros")

    agg = (
        d10.groupby(["COD_MUERTE", "SEGMENTO"], as_index=False)
        .size().rename(columns={"size": "TOTAL"})
    )
    desc = {c: DESCRIPCION_CIE10.get(c, "Sin descripcion") for c in top10_cod}
    agg["CAUSA"] = agg["COD_MUERTE"].map(desc)
    agg["ETIQUETA"] = agg["COD_MUERTE"].map(
        lambda c: f"{c} - {desc[c][:26]}{'...' if len(desc[c]) > 26 else ''}")

    orden_causas = (
        d10.groupby("COD_MUERTE").size()
        .sort_values(ascending=False).index.tolist()
    )
    orden_etq = [agg.loc[agg["COD_MUERTE"] == c, "ETIQUETA"].iloc[0]
                 for c in orden_causas]
    orden_seg = sorted(top_dptos) + ["Otros"]
    colores = {**DEPTO_COLORES, "Otros": COLOR_OTROS}

    fig = px.bar(
        agg, y="ETIQUETA", x="TOTAL", color="SEGMENTO", orientation="h",
        barmode="stack",
        category_orders={"ETIQUETA": orden_etq, "SEGMENTO": orden_seg},
        color_discrete_map=colores,
        labels={"TOTAL": "Casos", "ETIQUETA": "", "SEGMENTO": "Departamento"},
        hover_name="CAUSA",
        hover_data={"TOTAL": True, "ETIQUETA": False, "COD_MUERTE": True,
                    "CAUSA": False},
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        **{**LAYOUT_BASE, "margin": dict(l=6, r=8, t=38, b=8)},
        showlegend=True, yaxis_tickfont_size=8,
        legend=dict(orientation="h", y=1.04, x=0, font_size=8,
                    title=dict(text="Departamento:", font_size=8),
                    itemsizing="constant", tracegroupgap=0,
                    bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(gridcolor="#eceff3", zerolinecolor="#eceff3")
    return fig


def fig_barras_apiladas_sexo(dpto, mes, causa, sexo):
    """Muertes por sexo: por departamento (nacional) o municipio (filtrado)."""
    dff = _filtrar(dpto, mes, causa, sexo)
    if dff.empty:
        return _figura_vacia()
    if dpto == "TODOS":
        agg = (
            dff.groupby(["DEPARTAMENTO", "SEXO"], as_index=False).size()
            .rename(columns={"size": "TOTAL"})
        )
        orden = dff.groupby("DEPARTAMENTO").size().sort_values(ascending=False).index.tolist()
        eje = "DEPARTAMENTO"
    else:
        agg = (
            dff.groupby(["MUNICIPIO", "SEXO"], as_index=False).size()
            .rename(columns={"size": "TOTAL"})
        )
        orden = dff.groupby("MUNICIPIO").size().nlargest(15).index.tolist()
        agg = agg[agg["MUNICIPIO"].isin(orden)]
        eje = "MUNICIPIO"

    fig = px.bar(
        agg, x=eje, y="TOTAL", color="SEXO", barmode="stack",
        category_orders={eje: orden, "SEXO": SEXOS},
        color_discrete_map={"Hombre": COLOR_HOMBRE, "Mujer": COLOR_MUJER,
                            "Indeterminado": COLOR_INDET},
        labels={eje: "", "TOTAL": "Muertes", "SEXO": "Sexo"},
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**LAYOUT_BASE, xaxis_tickangle=-60, xaxis_tickfont_size=8,
                      legend=dict(orientation="h", y=1.02, font_size=10,
                                  title=None, bgcolor="rgba(0,0,0,0)"))
    fig.update_yaxes(gridcolor="#eceff3", zerolinecolor="#eceff3")
    return fig


def fig_histograma_edad(dpto, mes, causa, sexo):
    """Distribucion de muertes por categoria de edad (GRUPO_EDAD1)."""
    dff = _filtrar(dpto, mes, causa, sexo)
    conteo = (
        dff["CATEGORIA_EDAD"].value_counts()
        .reindex(ORDEN_CATEGORIAS_EDAD, fill_value=0)
        .rename_axis("CATEGORIA").reset_index(name="TOTAL")
    )
    fig = px.histogram(
        conteo, x="CATEGORIA", y="TOTAL", text_auto=True,
        category_orders={"CATEGORIA": ORDEN_CATEGORIAS_EDAD},
        labels={"CATEGORIA": "", "TOTAL": "Muertes"},
        color_discrete_sequence=[COLOR_PRIMARIO],
    )
    fig.update_traces(textposition="outside", textfont_size=9,
                      marker_line_width=0, opacity=0.9)
    fig.update_layout(**LAYOUT_BASE, xaxis_tickangle=-35, xaxis_tickfont_size=8)
    fig.update_yaxes(gridcolor="#eceff3", zerolinecolor="#eceff3",
                     title_text="Muertes")
    return fig


def kpis(dpto, mes, causa, sexo):
    """Indicadores del encabezado segun los filtros activos."""
    dff = _filtrar(dpto, mes, causa, sexo)
    total = len(dff)
    x95 = dff["COD_MUERTE"].str.startswith("X95").sum()
    if causa != "TODAS":
        texto_causa = f"{causa} - {DESCRIPCION_CIE10.get(causa, '')}"
    else:
        top = dff["COD_MUERTE"].mode()
        texto_causa = "—"
        if not top.empty:
            cod = top.iloc[0]
            texto_causa = f"{cod} - {DESCRIPCION_CIE10.get(cod, '')}"
    return f"{total:,}", f"{x95:,}", texto_causa


# ---------------------------------------------------------------------------
# Layout de la aplicacion
# ---------------------------------------------------------------------------
app = Dash(__name__, title="Mortalidad en Colombia 2019", update_title=None)
server = app.server  # entrada para gunicorn en el despliegue PaaS

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            html, body { margin: 0; padding: 0; height: 100%;
                         overflow: hidden; background: #dfe6ec;
                         font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }

            /* ---------- Encabezado de ancho completo ---------- */
            .encabezado {
                position: fixed; top: 0; left: 0; right: 0; z-index: 2000;
                min-height: 82px;
                box-shadow: 0 2px 14px rgba(15, 35, 60, 0.10);
                border-bottom: 1px solid #e3e9f0;
                display: flex; align-items: center; gap: 12px;
                padding: 8px 18px; box-sizing: border-box;
                flex-wrap: nowrap;
            }
            /* Fondo con blur separado para no crear bloque contenedor */
            .encabezado-fondo {
                position: absolute; inset: 0; z-index: -1;
                background: rgba(255, 255, 255, 0.97);
                backdrop-filter: blur(8px);
            }
            /* Linea divisoria vertical entre bloques del encabezado */
            .divisor {
                width: 1px; align-self: stretch;
                margin: 14px 0;
                background: linear-gradient(to bottom, transparent,
                                            #d3dce5 20%, #d3dce5 80%,
                                            transparent);
            }

            .kpi { text-align: left; min-width: 78px; }
            .kpi .valor { font-size: 18px; font-weight: 700;
                          color: #16324f; line-height: 1.15; }
            .kpi .valor.rojo { color: #c0392b; }
            .kpi .rotulo { font-size: 10px; color: #6b7f92;
                           text-transform: uppercase; letter-spacing: .5px; }
            .kpi-amplio { flex: 1 1 auto; min-width: 140px; max-width: 320px; }
            .kpi-amplio .valor { font-size: 12px; font-weight: 600;
                                 white-space: normal; line-height: 1.25;
                                 color: #33506b; }

            .filtro label { font-size: 10px; font-weight: 700; color: #16324f;
                            text-transform: uppercase; letter-spacing: .5px; }

            /* Boton hamburguesa */
            .boton-menu {
                display: none; background: transparent; border: none;
                font-size: 24px; cursor: pointer; color: #16324f;
                padding: 4px 8px; line-height: 1; border-radius: 6px;
            }
            .boton-menu:hover { background: rgba(22, 50, 79, 0.08); }

            /* Menu de filtros: inline en escritorio, drawer en movil */
            .menu-filtros {
                display: flex; align-items: center;
                gap: 10px; flex-wrap: nowrap;
            }
            .menu-filtros .filtro { flex: 0 0 auto; }

            /* ---------- Contenedor principal y paneles ---------- */
            .contenedor-dashboard {
                position: fixed; top: 82px; left: 0; right: 0; bottom: 0;
                display: grid;
                grid-template-columns: minmax(320px, 440px) 1fr minmax(320px, 440px);
                grid-template-areas: "izq mapa der";
                pointer-events: none;
            }
            .columna-izquierda {
                grid-area: izq;
                pointer-events: auto;
                display: flex; flex-direction: column; gap: 10px;
                padding: 14px; box-sizing: border-box;
                height: calc(100vh - 112px); overflow: hidden;
                position: static; min-width: 0;
            }
            .columna-derecha {
                grid-area: der;
                pointer-events: auto;
                display: flex; flex-direction: column; gap: 10px;
                padding: 14px; box-sizing: border-box;
                height: calc(100vh - 112px); overflow: hidden;
                position: static; min-width: 0;
            }
            .mapa-envoltorio {
                grid-area: mapa;
                position: relative; pointer-events: auto;
                min-width: 0;
            }
            .mapa-principal {
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            }

            /* ---------- Paneles laterales/columnas ---------- */
            .panel-columna {
                background: rgba(255, 255, 255, 0.92);
                backdrop-filter: blur(8px);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.65);
                box-shadow: 0 6px 24px rgba(15, 35, 60, 0.12);
                padding: 10px 12px;
                box-sizing: border-box;
            }
            .panel-lateral { overflow: hidden; }
            .grafica {
                height: calc((100vh - 224px) / 3);
                width: 100%;
            }

            /* ---------- Paneles flotantes (cartografia) ---------- */
            .panel-flotante {
                position: absolute; z-index: 1000;
                background: rgba(255, 255, 255, 0.92);
                backdrop-filter: blur(8px);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.65);
                box-shadow: 0 6px 24px rgba(15, 35, 60, 0.12);
                padding: 10px 12px;
                box-sizing: border-box;
            }

            /* Menus de los selectores siempre por encima de todo */
            .Select-menu-outer, .Select-menu,
            .dash-dropdown [class*="menu"] { z-index: 9999 !important; }

            /* Secciones: encabezados tipo chip, mas suaves */
            details.seccion { margin: 0 0 4px; }
            details.seccion > summary {
                cursor: pointer; font-weight: 600; font-size: 12.5px;
                color: #33506b; padding: 5px 10px;
                background: #f2f6fa; border-radius: 8px;
                list-style: none; user-select: none;
                transition: background .15s ease;
            }
            details.seccion > summary::before {
                content: "\\25B8  "; font-size: 10px; color: #7c93a8;
            }
            details.seccion[open] > summary::before { content: "\\25BE  "; }
            details.seccion > summary:hover { background: #e7eef5; }

            /* ---------- Responsive: movil ---------- */
            @media (max-width: 900px) {
                html, body { overflow-y: auto; height: auto; }

                .encabezado {
                    min-height: 64px; padding: 8px 12px;
                    gap: 10px; justify-content: space-between;
                }
                .encabezado .titulo-grupo {
                    flex: 1 1 auto; min-width: 0; overflow: hidden;
                }
                .encabezado .titulo-grupo div:first-child {
                    font-size: 14px !important;
                    white-space: normal !important;
                    line-height: 1.2;
                }
                .encabezado .titulo-grupo div:last-child {
                    font-size: 9px !important;
                    white-space: nowrap; overflow: hidden;
                    text-overflow: ellipsis;
                }
                /* En movil el encabezado solo muestra titulo y hamburguesa;
                   los KPIs se consultan en las graficas para evitar solapamientos. */
                .encabezado .kpi, .encabezado .divisor { display: none; }
                .boton-menu {
                    display: block; flex-shrink: 0;
                    position: relative; z-index: 3001;
                }

                .menu-filtros {
                    position: fixed !important; inset: 0 !important; z-index: 3000 !important;
                    flex-direction: column !important; align-items: stretch !important;
                    gap: 18px !important; padding: 70px 18px 18px !important;
                    background: rgba(255, 255, 255, 0.98) !important;
                    backdrop-filter: blur(10px) !important;
                    transform: translateY(-110%) !important;
                    transition: transform .25s ease !important;
                    display: flex !important;
                    box-shadow: 0 8px 30px rgba(15, 35, 60, 0.18) !important;
                }
                .menu-filtros.abierto { transform: translateY(0) !important; }
                .menu-filtros .filtro { width: 100% !important; flex-shrink: 0 !important; }
                .menu-filtros .dash-dropdown { width: 100% !important; }

                .contenedor-dashboard {
                    position: relative; top: auto; left: auto; right: auto; bottom: auto;
                    display: block; padding-top: 64px;
                }
                .mapa-envoltorio {
                    width: 100%; height: 55vh;
                }
                .mapa-principal { position: relative; height: 100%; }
                .columna-izquierda, .columna-derecha {
                    width: 100%; height: auto;
                    padding: 10px; gap: 10px;
                    overflow: visible;
                }
                .panel-columna {
                    width: 100%; margin-bottom: 10px;
                    border-radius: 12px;
                }
                .grafica { height: 320px; }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


def seccion(titulo, id_grafica, figura):
    """Seccion colapsable; la grafica ocupa todo el espacio disponible."""
    return html.Details(
        className="seccion", open=True,
        children=[
            html.Summary(titulo),
            html.Div(className="grafica", children=[
                dcc.Graph(id=id_grafica, figure=figura,
                          config={"displayModeBar": False},
                          style={"height": "100%", "width": "100%"},
                          responsive=True),
            ]),
        ],
    )


ANCHO_PANEL = "440px"
ALTURA_PANEL = "calc(100vh - 112px)"  # sin scroll: ocupa toda la pantalla

app.layout = html.Div(children=[

    # --- Encabezado de ancho completo: titulo | KPIs | menu hamburguesa --
    html.Header(
        className="encabezado",
        children=[
            # Fondo con blur separado para no afectar el posicionamiento fijo
            html.Div(className="encabezado-fondo"),

            html.Div(className="titulo-grupo", children=[
                html.Div("Mortalidad en Colombia · 2019",
                         style={"fontWeight": "bold", "fontSize": "16px",
                                "color": COLOR_PRIMARIO, "whiteSpace": "nowrap"}),
                html.Div("DANE · Estadísticas Vitales · Defunciones no fetales",
                         style={"fontSize": "10px", "color": "#6b7f92"}),
            ]),

            html.Div(className="divisor"),

            html.Div(className="kpi", children=[
                html.Div(id="kpi-total", className="valor"),
                html.Div("Defunciones", className="rotulo"),
            ]),
            html.Div(className="kpi", children=[
                html.Div(id="kpi-x95", className="valor rojo"),
                html.Div("Homicidios X95", className="rotulo"),
            ]),
            html.Div(className="kpi kpi-amplio", children=[
                html.Div(id="kpi-causa", className="valor"),
                html.Div("Causa principal de muerte", className="rotulo"),
            ]),

            html.Div(className="divisor"),

            # Menu hamburguesa (solo visible en movil)
            html.Button("☰", id="boton-menu", className="boton-menu",
                        n_clicks=0, type="button"),

            # Filtros: inline en escritorio, drawer en movil
            html.Div(
                id="menu-filtros",
                className="menu-filtros",
                style={"display": "flex", "flexDirection": "row", "gap": "10px"},
                children=[
                    html.Div(className="filtro", children=[
                        html.Label("Departamento"),
                        dcc.Dropdown(
                            id="filtro-departamento",
                            options=[{"label": "Todos", "value": "TODOS"}] + [
                                {"label": nombre.title(), "value": f"{codigo:02d}"}
                                for codigo, nombre in DEPARTAMENTOS
                            ],
                            value="TODOS", clearable=False, searchable=True,
                            style={"width": "130px", "fontSize": "12px"},
                        ),
                    ]),
                    html.Div(className="filtro", children=[
                        html.Label("Mes del año"),
                        dcc.Dropdown(
                            id="filtro-mes",
                            options=[{"label": "Todos", "value": 0}] + [
                                {"label": nombre, "value": num}
                                for num, nombre in MESES.items()
                            ],
                            value=0, clearable=False, searchable=False,
                            style={"width": "100px", "fontSize": "12px"},
                        ),
                    ]),
                    html.Div(className="filtro", children=[
                        html.Label("Causa de muerte"),
                        dcc.Dropdown(
                            id="filtro-causa",
                            options=OPCIONES_CAUSAS,
                            value="TODAS", clearable=False, searchable=True,
                            style={"width": "190px", "fontSize": "11.5px"},
                        ),
                    ]),
                    html.Div(className="filtro", children=[
                        html.Label("Sexo"),
                        dcc.Dropdown(
                            id="filtro-sexo",
                            options=[{"label": "Todos", "value": "TODOS"}] + [
                                {"label": s, "value": s} for s in SEXOS
                            ],
                            value="TODOS", clearable=False, searchable=False,
                            style={"width": "100px", "fontSize": "12px"},
                        ),
                    ]),
                ],
            ),
        ],
    ),

    # --- Contenedor principal: mapa + columnas -------------------------
    # Orden DOM: mapa, izquierda, derecha. En escritorio CSS Grid las ubica
    # a los lados; en movil el DOM natural apila mapa primero y graficas debajo.
    html.Div(
        className="contenedor-dashboard",
        children=[
            # --- Mapa ----------------------------------------------------
            html.Div(
                className="mapa-envoltorio",
                children=[
                    dcc.Graph(
                        id="mapa-departamentos",
                        figure=fig_mapa("TODOS", 0, "TODAS", "TODOS", ESTILO_DEFECTO),
                        config={"displayModeBar": False, "scrollZoom": False},
                        className="mapa-principal",
                        responsive=True,
                    ),
                    # Control de cartografia SOBRE el mapa
                    html.Div(
                        className="panel-flotante selector-cartografia",
                        style={"bottom": "18px", "left": "50%",
                               "transform": "translateX(-50%)",
                               "display": "flex", "alignItems": "center",
                               "gap": "12px", "padding": "7px 14px",
                               "zIndex": 1000, "opacity": 0.94},
                        children=[
                            html.Div(className="filtro", children=[
                                html.Label("Cartografía"),
                                dcc.Dropdown(
                                    id="selector-estilo-mapa",
                                    options=[{"label": k, "value": k} for k in ESTILOS_MAPA],
                                    value=ESTILO_DEFECTO, clearable=False, searchable=False,
                                    style={"width": "180px", "fontSize": "12px"},
                                ),
                            ]),
                        ],
                    ),
                ],
            ),

            # --- Columna izquierda (3 graficas) -------------------------
            html.Div(
                className="panel-columna panel-lateral columna-izquierda",
                children=[
                    seccion("Muertes por mes", "g-mes",
                            fig_lineas_mes("TODOS", 0, "TODAS", "TODOS")),
                    seccion("Ciudades más violentas (X95*)", "g-violentas",
                            fig_ciudades_violentas("TODOS", 0, "TODAS", "TODOS")),
                    seccion("Menor índice de mortalidad", "g-pie",
                            fig_pie_menor_mortalidad("TODOS", 0, "TODAS", "TODOS")),
                ],
            ),

            # --- Columna derecha (3 graficas) ---------------------------
            html.Div(
                className="panel-columna panel-lateral columna-derecha",
                children=[
                    seccion("10 principales causas de muerte por departamento", "g-causas",
                            fig_principales_causas("TODOS", 0, "TODAS", "TODOS")),
                    seccion("Muertes por sexo y departamento", "g-sexo",
                            fig_barras_apiladas_sexo("TODOS", 0, "TODAS", "TODOS")),
                    seccion("Distribución por grupo de edad", "g-edad",
                            fig_histograma_edad("TODOS", 0, "TODAS", "TODOS")),
                ],
            ),
        ],
    ),
])


# ---------------------------------------------------------------------------
# Callback principal: los cuatro filtros actualizan todo el dashboard
# ---------------------------------------------------------------------------
@app.callback(
    Output("mapa-departamentos", "figure"),
    Output("g-mes", "figure"),
    Output("g-violentas", "figure"),
    Output("g-pie", "figure"),
    Output("g-causas", "figure"),
    Output("g-sexo", "figure"),
    Output("g-edad", "figure"),
    Output("kpi-total", "children"),
    Output("kpi-x95", "children"),
    Output("kpi-causa", "children"),
    Input("filtro-departamento", "value"),
    Input("filtro-mes", "value"),
    Input("filtro-causa", "value"),
    Input("filtro-sexo", "value"),
    Input("selector-estilo-mapa", "value"),
)
def actualizar(dpto, mes, causa, sexo, estilo):
    total, x95, causa_txt = kpis(dpto, mes, causa, sexo)
    return (
        fig_mapa(dpto, mes, causa, sexo, estilo),
        fig_lineas_mes(dpto, mes, causa, sexo),
        fig_ciudades_violentas(dpto, mes, causa, sexo),
        fig_pie_menor_mortalidad(dpto, mes, causa, sexo),
        fig_principales_causas(dpto, mes, causa, sexo),
        fig_barras_apiladas_sexo(dpto, mes, causa, sexo),
        fig_histograma_edad(dpto, mes, causa, sexo),
        total, x95, causa_txt,
    )


# --- Callback para el menu hamburguesa -----------------------------------
@app.callback(
    Output("menu-filtros", "className"),
    Input("boton-menu", "n_clicks"),
    State("menu-filtros", "className"),
    prevent_initial_call=True,
)
def alternar_menu(n_clicks, class_name):
    if not n_clicks:
        return "menu-filtros"
    if class_name and "abierto" in class_name:
        return "menu-filtros"
    return "menu-filtros abierto"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
