"""Preprocesa los anexos del DANE y genera archivos ligeros para la app Dash.

Salidas:
    data/mortalidad_2019.parquet  -> registros de defunciones no fetales 2019
    data/cie10.parquet            -> catalogo de codigos CIE-10 (3 y 4 caracteres)

Uso:
    python prep_data.py
"""

import unicodedata

import pandas as pd

ANEXO1 = "Anexo1.NoFetal2019_CE_15-03-23.xlsx"
ANEXO2 = "Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx"
DIVIPOLA = "Divipola_CE_.xlsx"


def normalizar(texto: str) -> str:
    """Mayusculas, sin acentos ni espacios extra (para cruzar nombres)."""
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


def cargar_divipola() -> pd.DataFrame:
    div = pd.read_excel(DIVIPOLA, sheet_name="Hoja1", dtype={"COD_DANE": int})
    div = div[["COD_DANE", "COD_DEPARTAMENTO", "DEPARTAMENTO", "MUNICIPIO"]].copy()
    div["COD_DEPARTAMENTO"] = div["COD_DEPARTAMENTO"].astype(int)
    return div


def cargar_mortalidad(div: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "COD_DANE", "COD_DEPARTAMENTO", "MES", "SEXO",
        "GRUPO_EDAD1", "MANERA_MUERTE", "COD_MUERTE",
    ]
    df = pd.read_excel(ANEXO1, sheet_name="No_Fetales_2019", usecols=cols)
    df["COD_DANE"] = df["COD_DANE"].astype(int)
    df["COD_DEPARTAMENTO"] = df["COD_DEPARTAMENTO"].astype(int)

    # Nombres de departamento y municipio desde DIVIPOLA
    df = df.merge(
        div[["COD_DANE", "DEPARTAMENTO", "MUNICIPIO"]], on="COD_DANE", how="left"
    )
    df["MUNICIPIO"] = df["MUNICIPIO"].fillna("COD. " + df["COD_DANE"].astype(str))

    df["SEXO"] = df["SEXO"].map({1: "Hombre", 2: "Mujer", 3: "Indeterminado"})

    # Categorias de edad segun la tabla de referencia (GRUPO_EDAD1)
    def categoria(cod: int) -> str:
        if 0 <= cod <= 4:
            return "Mortalidad neonatal (< 1 mes)"
        if 5 <= cod <= 6:
            return "Mortalidad infantil (1-11 meses)"
        if 7 <= cod <= 8:
            return "Primera infancia (1-4 anos)"
        if 9 <= cod <= 10:
            return "Ninez (5-14 anos)"
        if cod == 11:
            return "Adolescencia (15-19 anos)"
        if 12 <= cod <= 13:
            return "Juventud (20-29 anos)"
        if 14 <= cod <= 16:
            return "Adultez temprana (30-44 anos)"
        if 17 <= cod <= 19:
            return "Adultez intermedia (45-59 anos)"
        if 20 <= cod <= 24:
            return "Vejez (60-84 anos)"
        if 25 <= cod <= 28:
            return "Longevidad / Centenarios (85-100+ anos)"
        return "Edad desconocida"

    df["CATEGORIA_EDAD"] = df["GRUPO_EDAD1"].astype(int).map(categoria)
    df["COD_MUERTE"] = df["COD_MUERTE"].astype(str).str.strip().str.upper()
    return df


def cargar_cie10() -> pd.DataFrame:
    raw = pd.read_excel(ANEXO2, sheet_name="Final", header=None, skiprows=9)
    raw.columns = ["CAPITULO", "NOMBRE_CAPITULO", "COD3", "DESC3", "COD4", "DESC4"]
    raw = raw.dropna(subset=["COD3", "COD4"], how="all")

    cod3 = raw[["COD3", "DESC3"]].dropna().drop_duplicates("COD3")
    cod4 = raw[["COD4", "DESC4"]].dropna().drop_duplicates("COD4")

    cie = pd.concat(
        [
            cod3.rename(columns={"COD3": "CODIGO", "DESC3": "DESCRIPCION"}),
            cod4.rename(columns={"COD4": "CODIGO", "DESC4": "DESCRIPCION"}),
        ],
        ignore_index=True,
    )
    cie["CODIGO"] = cie["CODIGO"].astype(str).str.strip().str.upper()
    cie["DESCRIPCION"] = cie["DESCRIPCION"].astype(str).str.strip()
    return cie.drop_duplicates("CODIGO")


def main() -> None:
    div = cargar_divipola()
    mortalidad = cargar_mortalidad(div)
    cie10 = cargar_cie10()

    mortalidad.to_parquet("data/mortalidad_2019.parquet", index=False)
    cie10.to_parquet("data/cie10.parquet", index=False)

    print(f"mortalidad_2019.parquet: {mortalidad.shape}")
    print(f"cie10.parquet:           {cie10.shape}")
    faltantes = mortalidad["DEPARTAMENTO"].isna().sum()
    print(f"registros sin nombre de departamento: {faltantes}")


if __name__ == "__main__":
    main()
