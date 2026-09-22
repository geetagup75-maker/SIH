import numpy as np
import pandas as pd

MIN_SAMPLE_SIZE = 5

def _clean(series, min_n=MIN_SAMPLE_SIZE):
    x = pd.to_numeric(series, errors="coerce").dropna()
    if len(x) < min_n:
        return None
    return x

def iqr_analysis(series, min_n=MIN_SAMPLE_SIZE):
    x = _clean(series, min_n)
    if x is None:
        return {"status":"insufficient_sample","n":0,"outlier_count":0}
    q1, q3 = x.quantile(.25), x.quantile(.75)
    iqr = q3-q1
    out = x[(x < q1-1.5*iqr) | (x > q3+1.5*iqr)]
    return {"status":"ok","n":len(x),"Q1":q1,"Q3":q3,"IQR":iqr,"outlier_count":len(out)}

def mad_analysis(series, min_n=MIN_SAMPLE_SIZE):
    x = _clean(series, min_n)
    if x is None:
        return {"status":"insufficient_sample","n":0,"outlier_count":0}
    med=x.median(); mad=np.median(np.abs(x-med))
    if mad==0:
        return {"status":"ok","n":len(x),"median":med,"MAD":0,"outlier_count":0}
    mz=.6745*(x-med)/mad
    return {"status":"ok","n":len(x),"median":med,"MAD":mad,"outlier_count":int((mz.abs()>3.5).sum())}
