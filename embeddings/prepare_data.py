import pandas as pd
import numpy as np

""" This script prepares data for embeddings by loading a CSV file,
    cleaning the text, and saving the processed data to a new CSV file."""
    
# Load the CSV file
data = pd.read_csv(r'..\data\raw\winedb.csv')


def build_doc(row):
    return (
        f"Wine: {row['Title']} from {row['Product_Countries']}.\n"
        f"Aromas: {row['Aromas']}.\n"
        f"Flavors: {row['Flavors']}.\n"
        f"Food pairings: {row['Food_Pairings']}.\n"
        f"Type: {row['Product_Types']}.\n"
        f"Alcohol: {row['Alcohol_Content']}%.\n"
        f"Price: {row['Price']}.\n"
        f"Region: {row['Wine_Region_Classification']}.\n"
        f"Buy here: {row['Buy_Link']}."
    )

data['document'] = data.apply(build_doc, axis=1) 

data[['document']].to_csv("../data/processed/wine_docs.csv", index=False) 