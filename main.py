import pandas as pd
import numpy as np
import seaborn as sns
sns.set()
from sklearn.cluster import KMeans

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

    fields_list = list(df)
    del fields_list[0]

    # fill in nulls: for numeric use the mean, for categorical use unknown label
    # otherwise grab the mode

    for c in list(df[quasi_ids]):
        if df[c].dtypes == np.int64:
            df[c]=df[c].fillna((df[c].mean()))
        elif df[c].dtypes == object:
            df[c]=df[c].fillna((df[c].mode()))

    #do some silly truncation to reduce the grain

        if df[c].nunique() / df[c].count() >= .005:
            while df[c].nunique() / df[c].count() >= .005 and df[c].map(lambda x: len(str(x))).min() > 1:
                df[c] = df[c].str[:-1]

    quasi_ids_cat = list()
    quasi_ids_wo_cat = list()

    for c in list(df[quasi_ids]):
        # encode as numeric for binning
        if df[c].dtypes != np.int64:
            df[c+'_cat'] = df[c].astype('category')
            df[c+'_cat'] = df[c+'_cat'].cat.codes
            df[c+'_cat'] = pd.to_numeric(df[c+'_cat'],errors = 'coerce')
            quasi_ids_cat.append(c+'_cat')
        else:
            quasi_ids_wo_cat.append(c)
    quasi_ids_w_wo_cat = quasi_ids_cat+quasi_ids_wo_cat

    df_cat_mapping = df[quasi_ids_cat+quasi_ids].copy().drop_duplicates()

    #get the rows that are still problematic
    df_aggs = df.groupby(quasi_ids_w_wo_cat).size().reset_index(name="count")
    df_slim_cats =  df_aggs[df_aggs['count']<=3] #guessing on this threshold

    # for our slim qid cats, we'll employ kmeans to increase bucket size and then
    # agg the identifiers together

    # we should be more intelligent about cluster count, but I'm in a rush 
    kmeans = KMeans(5)

    kmeans.fit(df_slim_cats)
    identified_clusters = kmeans.fit_predict(df_slim_cats)

    data_with_clusters = df_slim_cats.copy()
    data_with_clusters['Clusters'] = identified_clusters 

    #grab min qid per cluster
    #mode would be ideal, but again, low on time and haven't figured out how to make .transform() accept mode
    #taking mins here to make sure we get "real" values for things like hectare and date

    inner_join_df = pd.merge(df, data_with_clusters, on=quasi_ids_w_wo_cat, how='inner').drop(columns=['count'])
    # df
    # inner_join_df
    for c in list(inner_join_df[quasi_ids_w_wo_cat]):
        inner_join_df[c] = inner_join_df.groupby(['Clusters'])[c].transform('min')

    new_df = pd.merge(df, inner_join_df, on="id", how="left")

    #coalesce the clustered values, then the non-clustered ones
    for c in fields_list:
        if c+'_cat' in quasi_ids_cat:
            new_df[c] = new_df[c + '_cat_y'].combine_first(new_df[c + '_cat_x'])
        else:
            new_df[c] = new_df[c + '_y'].combine_first(new_df[c + '_x'])

    #clean up the columns
    reduced_df = new_df[all_fields].copy()

    d={}
    for c in quasi_ids_cat:
        d[c] = dict(df_cat_mapping[[c,c.replace("_cat", "")]].drop_duplicates().to_dict('split')['data'])
        reduced_df[c.replace("_cat", "")] = reduced_df[c.replace("_cat", "")].map(d[c])

    return reduced_df

