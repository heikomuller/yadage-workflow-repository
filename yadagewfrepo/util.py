"""Collection of helper methods."""

def from_list(elements, label_key='key', label_value='value'):
    """Convert a list of key-value pairs into a dictionary. The value that is
    associated with the key of each key-value pair will be the dictionary key.

    Parameters
    ----------
    elements : List
        List of key value pairs, i.e., [{label_key:..., label_value:...}].
    label_key : string
        Label for the key entry of key-value pairs in elements.
    label_value : string
        Label for the value entry of key-value pairs in elements.

    Returns
    -------
    Dictionary
        Dictionary of values.
    """
    dictionary = {}
    for kvp in elements:
        dictionary[kvp[label_key]] = kvp[label_value]
    return dictionary
