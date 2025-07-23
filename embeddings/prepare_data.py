import pandas as pd
import numpy as np

""" This script prepares data for embeddings by loading a CSV file,
    cleaning the text, and saving the processed data to a new CSV file."""
    
# Load the CSV file
data = pd.read_csv(r'..\data\raw\winedb.csv')


def build_doc(row):
    return (
        f"Wine: {row.get('Title', 'N/A')} from {row.get('Product_Countries', 'N/A')}.\n"
        f"Aromas: {row.get('Aromas', 'N/A')}.\n"
        f"Flavors: {row.get('Flavors', 'N/A')}.\n"
        f"Food pairings: {row.get('Food_Pairings', 'N/A')}.\n"
        f"Type: {row.get('Product_Types', 'N/A')}.\n"
        f"Alcohol: {row.get('Alcohol_Content', 'N/A')}%.\n"
        f"Price: {row.get('Price', 'N/A')}.\n"
        f"Region: {row.get('Wine_Region_Classification', 'N/A')}.\n"
        f"Fullness/Sweetness: {row.get('Taste_Clock_1_Fullness_Sweetness', 'N/A')}.\n"
        f"Astringency: {row.get('Taste_Clock_2_Fullness_Astringency', 'N/A')}.\n"
        f"Acidity: {row.get('Taste_Clock_3_Acidity', 'N/A')}.\n"
        f"Buy here: {row.get('Permalink', 'N/A')}.\n"
        f"Image URL: {row.get('Image_URL', 'N/A')}.\n"
        f"Permalink: {row.get('Permalink', 'N/A')}.\n"
        f"Description: {row.get('Description', 'N/A')}"
    )

data['document'] = data.apply(build_doc, axis=1) 

data[['document']].to_csv("../data/processed/wine_docs.csv", index=False) 