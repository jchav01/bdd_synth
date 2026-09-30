# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 13:32:05 2026

@author: CES
"""

import pandas as pd
import os

fichier = "base_synthetique_shopper_retail_analytics.xlsx"

obs = pd.read_excel(fichier, sheet_name="Observations")
stores = pd.read_excel(fichier, sheet_name="Stores")
products = pd.read_excel(fichier, sheet_name="Products")
campaigns = pd.read_excel(fichier, sheet_name="Campaigns")
dico = pd.read_excel(fichier, sheet_name="Dictionary")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", None)
print(dico)

obs.info()