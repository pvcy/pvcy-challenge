from scipy.spatial import KDTree
from collections import defaultdict


def create_qid_df_with_numerical_features(df, qids):
    """
    Given input df and list of qids, return a new df containing only those columns.
    The columns' categorical values will be replaced with numerical values.
    """
    def compute_numerical_mappings(df, columns):
        """
        Given input df and list of columns, return a dict mapping categorical values to scale numerical values.
        Example Result:
        {
            "col1": {
                "val1": 0.5,
                "val2": 1.0,
            },
        }
        """
        numerical_mapping = {}
        for column in columns:
            arr_unique = df[column].unique()
            num_distinct_vals = len(arr_unique)
            cat_to_num_mapping = { val: i/num_distinct_vals for i,val in enumerate(sorted(arr_unique)) }
            numerical_mapping[column] = cat_to_num_mapping

        return numerical_mapping

    df = df.copy()
    df = df[qids]
    
    column_mapping = compute_numerical_mappings(df, qids)
    for qid in qids:
        df[qid] = df[qid].apply(lambda x: column_mapping[qid][x])
    
    return df

def compute_clusters_from_pairs(pairs):
    """
    Given a list of pairs (as returned from KDTree search), arrange in structures to efficiently lookup clusters.
    """
    clusters = defaultdict(list)
    for i,j in pairs:
        clusters[i].append(j)
    
    return clusters

def compute_remaining_identifiable_rows(df, qids):
    """
    Given input df and list of qids, return subset of rows that identifiable due to the fact
    that their combination of qids are fully distinct (i.e. count == 1).
    """
    groups = df.groupby(qids)
    
    qid_duplicate_counts = groups.agg(lambda x: len(x))["id"]
    first_id_for_qid_group = groups.agg(lambda x: x.iloc[0])["id"]
    
    distinct_ids = first_id_for_qid_group[qid_duplicate_counts == 1]
    
    return df.loc[distinct_ids]

def merge_dataframes(left, right):
    """
    Given two dfs, return the full left df with all updates applied from right df.
    """
    df = left.copy()
    df.loc[right.index, :] = right[:]

    return df

def print_anonymity_metrics(df, qids):
    mean_anonymity = df.groupby(qids).agg("count")["id"].mean()
    num_distinct = (df.groupby(qids).agg("count")["id"] == 1).sum()
    max_duplicates = df.groupby(qids).agg("count")["id"].max()

    print(f"mean_anonymity: {mean_anonymity}")
    print(f"num_distinct: {num_distinct}")
    print(f"max_duplicates: {max_duplicates}\n")

def anonymize_recursive(df, qids, iteration=1):
    """
    Helper method for anonymize. Enables recursive calls without having to change the function signature of top-level anonymize().
    """
    # Max iteration depth
    if iteration > 10:
        return df.copy()
    
    # Set radius of clusters.
    # Start small and increase with each iteration, so higher distortion is only used for difficult-to-anonymize rows.
    cluster_search_radius = 0.1 * iteration
    
    print(f"iteration: {iteration}")
    print(f"search radius: {cluster_search_radius}\n")
    
    # Basic data copying + cleaning.
    # An absence of data (e.g. NaN) can still be use to correlate, so we treat it as a valid categorical value ("").
    anon_df = df.copy().fillna("")
    
    # We are calculating K-D distance between rows,
    # so we need to convert and scale into a numerical representation in order to compute distances.
    anon_df_numerical = create_qid_df_with_numerical_features(anon_df, qids)
    
    # Compute the KDTree representation of the data and find all pairs within the set clustering radius.
    kd_tree = KDTree(anon_df_numerical)
    pairs = kd_tree.query_pairs(cluster_search_radius)
    
    # We compute a data structure to more effectively store/query neighbors of a given point in a cluster.
    clusters = compute_clusters_from_pairs(pairs)

    # Iterate through clusters and assign all neighbors the same values as the candidate selected
    # to represent the cluster (approximating the 'center').
    for candidate,neighbors in clusters.items():
        for qid in qids:
            anon_df.iloc[neighbors, anon_df.columns.get_loc(qid)] = anon_df.iloc[candidate][qid]
    
    print_anonymity_metrics(anon_df, qids)
    
    # Find rows that are trivially identifiable, where row has distinct set of qids.
    remaining_identifiable_rows = compute_remaining_identifiable_rows(anon_df, qids)

    # If some rows have not yet been anonymized, we distort them more aggressively
    # and then merge into the existing iteration.
    if len(remaining_identifiable_rows) > 0:
        anon_df = merge_dataframes(
            anon_df,
            anonymize_recursive(remaining_identifiable_rows, qids, iteration=iteration+1),
        )

    return anon_df


def anonymize(df, qids):
    """
    Implementation of iterative kd-tree clustering anonymizer.

    :param df: Untreated DataFrame
    :param qids: list of quasi-identifier columns
    :return: A valid Pandas DataFrame with your anonymized data
    """

    # Make top-level recursive call
    anon_df = anonymize_recursive(df, qids)

    print("\n\nOverall Anonymity Metrics:")
    print_anonymity_metrics(anon_df, qids)

    return anon_df
