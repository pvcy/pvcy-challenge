# had help 
# from https://towardsdatascience.com/the-k-prototype-as-clustering-algorithm-for-mixed-data-type-categorical-and-numerical-fe7c50538ebb
# and https://latrobe.libguides.com/sensitivedata/deidentification
# and https://dev.to/r0f1/a-simple-way-to-anonymize-data-with-python-and-pandas-79g
# and https://github.com/qiyuangong/Mondrian/blob/master/anonymizer.py
# and https://sdcpractice.readthedocs.io/en/latest/anon_methods.html
# and https://medium.com/brillio-data-science/a-brief-overview-of-k-anonymity-using-clustering-in-python-84203012bdea

import pandas as pd
import numpy as np
import seaborn as sns
sns.set()
from sklearn.cluster import KMeans
from kmodes.kprototypes import KPrototypes

'''
Given this part in the prompt:
>Test datasets will not contain any direct identifiers (DIDs).

I will avoid looking for strings that resemble names, emails, or other contact info.

Reviewing the squirrel sample data, a few things are evident:

*Date*
Date is stored as an int with MMDDYYYY as the format. 

Dates are limited to the month of October. As an int, I'd assume that other, broader
datasets wouldn't include leading 0's, since they would only be possible on the
day of month, but not the month (eg 6052019 vs 652019). 

This is a gnarly way to store dates (certainly wouldn't happen in our warehouse)
and precludes me from doing inteligent date rounding via week, month, quarter, decade truncs.

Given additional time, a set of helper functions for detecting dates in all the 
inventive formats someone may choose to store them would be handy.

*Hectare*
This appears to be a categorical mapping column. Again, a more intelligent rounding 
approach would be preferable, but it's unclear what other test datasets would present.

My rounding approach heavily distorts the data. Doing a group on this and mapping back to
a mode rather than keeping the truncated value would have been better.

*Age* *Primary Fur Color* *Highlight Fur Color* *Location*
Each contain copious nulls. Going to fill these with some solid guesses

For categorical columns, we'll use the mode. For continuous vars, we'll go for the median

We then use the remaining QIDs to group and check for slim categories (<3 samples)

On those entries, we run kmeans clustering to bucket them into like groups and 
distort the data by taking a mean of the QIDs to represent the sample accross the whole
cluster

'''

def anonymize(df, qids):
    """
    The main implementation of your anonymization implementation.
    Trivial anonymizer included as an example.  Replace this code with your own.

    :param df: Untreated DataFrame
    :param qids: list of quasi-identifier columns
    :return: A valid Pandas DataFrame with your anonymized data
    """
    quasi_ids = qids

    #helpers 
    all_fields = list(df)

    #establish a set of category fields 
    #this will cast nulls to -1 and move strings to ints
    quasi_ids_cat = list()

    for c in list(df[quasi_ids]):
        df[c+'_cat'] = df[c].astype('category')
        df[c+'_cat'] = df[c+'_cat'].cat.codes
        df[c+'_cat'] = pd.to_numeric(df[c+'_cat'],errors = 'coerce')
        quasi_ids_cat.append(c+'_cat')

    categorical = []
    continuous = []

    for c in quasi_ids_cat:
        col = df[c]
        nunique = col.nunique()
        if nunique < 20: # how hacky is this?
            categorical.append(c)
        else:
            continuous.append(c)

    #just the data we need for kmeans/kmode
    clustering_df = df[quasi_ids_cat].copy()

    # Get the position of categorical columns
    catColumnsPos = [clustering_df.columns.get_loc(col) for col in categorical]
    dfMatrix = clustering_df.to_numpy()

    #I'm sure there's a programmatic way to get to the elbow graph, but it's beyond me at the moment, so I'm picking 4 clusters

    kprototype = KPrototypes(n_jobs = -1, n_clusters = 4, init = 'Huang', random_state = 0) 

    kprototype.fit_predict(dfMatrix, categorical = catColumnsPos)
    df['cluster_label'] = kprototype.labels_

    #get the mode of each column by cluster
    quasi_ids_mode = list()

    for c in list(df[quasi_ids]):
        # this is an insane syntax just to get a windowed mode. I can't believe it's not a param in .transform()
        df[c+'_mode'] = df['cluster_label'].map(df.groupby('cluster_label')[c].agg(lambda x: x.value_counts().idxmax())) 
        quasi_ids_mode.append(c+'_mode')

    #establish clean columns 
    quasi_ids_clean = list()

    for c in list(df[quasi_ids]):
        # this is an insane syntax just to get a windowed mode. I can't believe it's not a param in .transform()
        # df[c+'_clean'] = df[c].combine_first(df[c+'_cat'])
        df[c+'_clean'] = df[c].fillna('-')
        quasi_ids_clean.append(c+'_clean')

    df['n_count_of_qid']=df.groupby(quasi_ids_clean)['id'].transform('count')
    df['risky_grain'] = df['n_count_of_qid'].apply(lambda x: True if x < 4 else False) #4 is a complete guess here, not sure what is standard for the industry. 

    # #sort in desc order of unique values in the modes 
    # #help from https://www.pythoncentral.io/how-to-sort-a-list-tuple-or-object-with-sorted-in-python/

    def getKey(item):
        return item[1]

    unique_val_arr = []

    for c in quasi_ids_mode:
        unique_val_arr.append([c,df.groupby(c).size().sort_values(ascending=False).count()])

    unique_val_arr = sorted(unique_val_arr, key=getKey,reverse=True)

    #iterate over modes, largest to smallest
    #replace low-grain rows with mode
    #recount and break if we're good, if not, go through all of the qids

    for arr_val in unique_val_arr:
        c = arr_val[0]
        df[c.replace("_mode", "_clean")] = np.where(df["risky_grain"] == True, df[c], df[c.replace("_mode", "_clean")])
        #recount
        df['n_count_of_qid']=df.groupby(quasi_ids_clean)['id'].transform('count')
        df['risky_grain'] = df['n_count_of_qid'].apply(lambda x: True if x < 4 else False) #4 is a complete guess here, not sure what is standard for the industry. 

        try: 
            df.groupby('risky_grain').size()[True]
        except:
            break

    df.drop(df[df['risky_grain'] == True].index, inplace = True)

    fields_for_cleaned_df = list(set(all_fields) - set(quasi_ids)) + quasi_ids_clean
    cleaned_df = df[fields_for_cleaned_df].copy()

    for c in quasi_ids_clean:
        cleaned_df.rename({c: c.replace("_clean", "")}, axis=1, inplace=True)

    cleaned_df = cleaned_df.replace('-', np.nan)

    return cleaned_df
