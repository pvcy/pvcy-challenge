import random
from string import ascii_lowercase, ascii_uppercase, digits


def create_char_map():
    charmap = {}
    all_chars = ascii_lowercase + ascii_uppercase + digits
    for c in all_chars:
        t = random.choice(ascii_lowercase + ascii_uppercase + digits)
        charmap[c] = t
    return charmap


charmap = create_char_map()


def transform_value(v):
    if isinstance(v, str):
        transformed = ''.join([charmap[c] if c in charmap else c for c in v])
        return transformed
    elif isinstance(v, int):
        return -v
    elif isinstance(v, float):
        return -v
    return v


def anonymize(df, qids):
    # Randomly shuffle column values
    anon_df = df.copy()
    for colname in qids:
        anon_df[colname] = anon_df[colname].transform(func=transform_value)

    # Suppress arbitrary percent of rows at random
    return anon_df.drop(
        labels=anon_df.sample(frac=0.5).index,
        axis=0
    )
