import numpy as np
import pandas as pd
from airfare_index.outlier_detector import iqr_analysis, mad_analysis

def descriptive_statistics(series):
    s=pd.to_numeric(series, errors="coerce").dropna()
    return {"count":len(s),"mean":s.mean(),"median":s.median(),"std":s.std(),"min":s.min(),
            "q1":s.quantile(.25),"q3":s.quantile(.75),"max":s.max()}

def calculate_z_score(series):
    s=pd.to_numeric(series, errors="coerce")
    std=s.std()
    return pd.Series(np.zeros(len(s)), index=s.index) if std==0 else (s-s.mean())/std

def zscore_analysis(series, threshold=3):
    z=calculate_z_score(series)
    return {"z_scores":z,"outlier_count":int((z.abs()>threshold).sum())}

def coefficient_of_variation(series):
    s=pd.to_numeric(series, errors="coerce").dropna()
    if len(s)<2 or s.mean()==0: return np.nan
    return s.std()/s.mean()*100
