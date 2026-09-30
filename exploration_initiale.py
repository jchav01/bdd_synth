"""
EXPLORATION INITIALE - base brute (aucune modification des données)
Objectif : décrire fidèlement le contenu du classeur, repérer ce qui
devra être traité au nettoyage, produire des graphes descriptifs simples.
"""

import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------------------------------------------------
# 0. PARAMÈTRES
# ----------------------------------------------------------------------
FICHIER = "base_synthetique_shopper_retail_analytics.xlsx"
DOSSIER_FIGURES = "figures_exploration"

# Feuilles descriptives (texte) : affichées telles quelles, non analysées
FEUILLES_TEXTE = ["Summary", "Dictionary", "Methodology"]

# Si une feuille a un titre avant le tableau, indiquer ici la ligne d'en-tête
# (0 = première ligne). Exemple : {"Stores": 2}
LIGNE_ENTETE = {}

MAX_MODALITES = 30    # au-delà, une colonne texte n'est pas tracée en barres
TOP_N = 10            # nombre de modalités affichées dans les barres
COLS_GRILLE = 3

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 80)
os.makedirs(DOSSIER_FIGURES, exist_ok=True)


# ----------------------------------------------------------------------
# 1. CHARGEMENT
# ----------------------------------------------------------------------
def charger(fichier):
    """Retourne (feuilles_texte, feuilles_donnees) sous forme de dicts."""
    noms = pd.ExcelFile(fichier).sheet_names
    texte, donnees = {}, {}
    for nom in noms:
        if nom in FEUILLES_TEXTE:
            texte[nom] = pd.read_excel(fichier, sheet_name=nom, header=None)
        else:
            entete = LIGNE_ENTETE.get(nom, 0)
            donnees[nom] = pd.read_excel(fichier, sheet_name=nom, header=entete)
    return texte, donnees


def titre(txt):
    print("\n" + "=" * 80 + f"\n{txt}\n" + "=" * 80)


# ----------------------------------------------------------------------
# 2. OUTILS DE DIAGNOSTIC
# ----------------------------------------------------------------------
def cols_texte(df):
    """Colonnes non numériques, non dates, non booléennes (texte/catégories)."""
    t = pd.api.types
    return [c for c in df.columns
            if not (t.is_numeric_dtype(df[c]) or t.is_datetime64_any_dtype(df[c])
                    or t.is_bool_dtype(df[c]))]


def cols_identifiants(df):
    """Colonnes dont toutes les valeurs sont uniques (clés probables)."""
    return [c for c in df.columns if df[c].notna().all() and df[c].is_unique]


def types_suspects(df):
    """Colonnes texte qui ressemblent à des nombres ou des dates."""
    suspects = []
    for c in cols_texte(df):
        s = df[c].dropna()
        if s.empty:
            continue
        if pd.to_numeric(s, errors="coerce").notna().mean() > 0.9:
            suspects.append((c, "nombre stocké en texte"))
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if pd.to_datetime(s, errors="coerce").notna().mean() > 0.9:
                suspects.append((c, "date stockée en texte"))
    return suspects


def variantes_texte(df):
    """Colonnes texte où des valeurs ne diffèrent que par casse/espaces."""
    res = []
    for c in cols_texte(df):
        s = df[c].dropna().astype(str)
        if s.nunique() > s.str.strip().str.lower().nunique():
            res.append(c)
    return res


def valeurs_aberrantes_iqr(df):
    """Nombre de valeurs hors [Q1-1.5*IQR ; Q3+1.5*IQR] (simple repérage)."""
    lignes = []
    for c in df.select_dtypes(include="number").columns:
        s = df[c].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        n = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()
        lignes.append({"colonne": c, "hors_IQR": n,
                       "%": round(100 * n / len(s), 2),
                       "négatifs": int((s < 0).sum()),
                       "zéros": int((s == 0).sum())})
    return pd.DataFrame(lignes)


# ----------------------------------------------------------------------
# 3. PROFIL TEXTUEL D'UNE TABLE
# ----------------------------------------------------------------------
def profil(df, nom):
    titre(f"TABLE : {nom}")
    print(f"Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes")

    print("\n--- Aperçu (5 premières / 5 dernières lignes) ---")
    print(df.head())
    print(df.tail())

    print("\n--- Types, valeurs manquantes, valeurs uniques ---")
    resume = pd.DataFrame({
        "type": df.dtypes.astype(str),
        "non_nuls": df.notna().sum(),
        "manquants": df.isna().sum(),
        "% manquants": (100 * df.isna().mean()).round(2),
        "nb_uniques": df.nunique(),
    })
    print(resume)

    print(f"\n--- Lignes dupliquées (lignes entières) : {df.duplicated().sum()}")

    ids = cols_identifiants(df)
    print(f"--- Colonnes à valeurs toutes uniques (clés probables) : {ids}")
    constantes = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    print(f"--- Colonnes constantes : {constantes}")

    susp = types_suspects(df)
    print(f"--- Types suspects : {susp if susp else 'aucun'}")
    print(f"--- Variantes casse/espaces : {variantes_texte(df) or 'aucune'}")

    num = df.select_dtypes(include="number")
    if not num.empty:
        print("\n--- Statistiques des colonnes numériques ---")
        print(num.describe().T)
        print("\n--- Repérage valeurs extrêmes / négatives / nulles ---")
        print(valeurs_aberrantes_iqr(df).to_string(index=False))

    cat = cols_texte(df)
    if cat:
        print("\n--- Colonnes catégorielles : modalités les plus fréquentes ---")
        for c in cat:
            print(f"\n[{c}] ({df[c].nunique()} modalités)")
            print(df[c].value_counts(dropna=False).head(TOP_N))

    dates = df.select_dtypes(include="datetime")
    if not dates.empty:
        print("\n--- Colonnes dates : étendue ---")
        for c in dates.columns:
            print(f"{c} : {df[c].min()}  ->  {df[c].max()}")


# ----------------------------------------------------------------------
# 4. GRAPHES DESCRIPTIFS
# ----------------------------------------------------------------------
def grille(n, titre_fig, largeur=5, hauteur=3.5):
    """Crée une grille de sous-graphes ; retourne (fig, axes utilisables)."""
    n_cols = min(COLS_GRILLE, n)
    n_rows = -(-n // n_cols)
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(largeur * n_cols, hauteur * n_rows),
                             squeeze=False)
    axes = axes.flatten()
    for ax in axes[n:]:
        ax.set_visible(False)
    fig.suptitle(titre_fig, fontsize=13, fontweight="bold")
    return fig, axes[:n]


def sauver(fig, nom_fichier):
    fig.tight_layout()
    chemin = os.path.join(DOSSIER_FIGURES, nom_fichier)
    fig.savefig(chemin, dpi=120)
    plt.show()
    plt.close(fig)


def graphes(df, nom):
    sain = nom.replace(" ", "_").lower()
    ids = cols_identifiants(df)

    # 4.1 Valeurs manquantes
    manq = (100 * df.isna().mean()).sort_values()
    if manq.max() > 0:
        fig, ax = plt.subplots(figsize=(7, max(3, 0.3 * len(manq))))
        manq.plot.barh(ax=ax, color="indianred")
        ax.set_xlabel("% de valeurs manquantes")
        ax.set_title(f"{nom} - valeurs manquantes par colonne")
        sauver(fig, f"{sain}_manquants.png")

    # 4.2 Distributions numériques (histogrammes) + boîtes à moustaches
    num = [c for c in df.select_dtypes(include="number").columns if c not in ids]
    if num:
        fig, axes = grille(len(num), f"{nom} - distributions numériques")
        for ax, c in zip(axes, num):
            ax.hist(df[c].dropna(), bins=30, color="steelblue", edgecolor="white")
            ax.set_title(c)
            ax.set_ylabel("effectif")
        sauver(fig, f"{sain}_histogrammes.png")

        fig, axes = grille(len(num), f"{nom} - boîtes à moustaches")
        for ax, c in zip(axes, num):
            ax.boxplot(df[c].dropna(), vert=False)
            ax.set_title(c)
        sauver(fig, f"{sain}_boxplots.png")

    # 4.3 Colonnes catégorielles (top modalités)
    cat = [c for c in cols_texte(df)
           if c not in ids and 1 < df[c].nunique() <= MAX_MODALITES]
    if cat:
        fig, axes = grille(len(cat), f"{nom} - répartition des modalités (top {TOP_N})")
        for ax, c in zip(axes, cat):
            df[c].value_counts().head(TOP_N).sort_values().plot.barh(
                ax=ax, color="seagreen")
            ax.set_title(c)
            ax.set_xlabel("effectif")
        sauver(fig, f"{sain}_categories.png")

    # 4.4 Colonnes dates : effectifs par mois
    dates = list(df.select_dtypes(include="datetime").columns)
    if dates:
        fig, axes = grille(len(dates), f"{nom} - effectifs par mois")
        for ax, c in zip(axes, dates):
            df[c].dropna().dt.to_period("M").value_counts().sort_index() \
                .plot(ax=ax, marker="o")
            ax.set_title(c)
            ax.set_ylabel("effectif")
        sauver(fig, f"{sain}_dates.png")


# ----------------------------------------------------------------------
# 5. LIENS ENTRE TABLES (colonnes en commun = clés de jointure potentielles)
# ----------------------------------------------------------------------
def liens_entre_tables(donnees):
    titre("COLONNES COMMUNES ENTRE TABLES (jointures potentielles)")
    noms = list(donnees)
    trouve = False
    for i, a in enumerate(noms):
        for b in noms[i + 1:]:
            communes = set(donnees[a].columns) & set(donnees[b].columns)
            for c in communes:
                va, vb = set(donnees[a][c].dropna()), set(donnees[b][c].dropna())
                if not va or not vb:
                    continue
                trouve = True
                print(f"{a} <-> {b} | colonne '{c}' | "
                      f"valeurs de {a} absentes de {b} : {len(va - vb)} | "
                      f"valeurs de {b} absentes de {a} : {len(vb - va)}")
    if not trouve:
        print("Aucune colonne commune trouvée.")


# ----------------------------------------------------------------------
# 6. EXÉCUTION
# ----------------------------------------------------------------------
if __name__ == "__main__":
    feuilles_texte, donnees = charger(FICHIER)

    for nom, contenu in feuilles_texte.items():
        titre(f"FEUILLE DESCRIPTIVE : {nom}")
        print(contenu.dropna(how="all").dropna(axis=1, how="all").to_string(
            header=False, index=False))

    for nom, df in donnees.items():
        profil(df, nom)
        graphes(df, nom)

    liens_entre_tables(donnees)
    print(f"\nTerminé. Figures enregistrées dans : {os.path.abspath(DOSSIER_FIGURES)}")
