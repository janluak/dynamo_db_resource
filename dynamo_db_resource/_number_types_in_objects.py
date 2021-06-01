from decimal import Decimal


__all__ = ["object_with_decimal_to_float", "object_with_float_to_decimal"]


def object_with_decimal_to_float(data):
    """
    Convert all decimal values to type=float

    Parameters
    ----------
    data : object

    Returns
    -------
    dict

    """

    def to_basic(vi):
        if isinstance(vi, Decimal):
            if vi % 1 == 0:
                return int(vi)
            return float(vi)
        return vi

    if isinstance(data, (list, tuple)):
        data = [object_with_decimal_to_float(i) for i in data]
    elif isinstance(data, float):
        return to_basic(data)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                object_with_decimal_to_float(v)
            elif isinstance(v, (list, tuple)):
                data[k] = [
                    object_with_decimal_to_float(x)
                    if isinstance(x, dict)
                    else to_basic(x)
                    for x in v
                ]
            else:
                data[k] = to_basic(v)
    return data


def object_with_float_to_decimal(data):
    """
    Convert all float values to type=Decimal

    Parameters
    ----------
    data : object

    Returns
    -------
    dict

    """

    def to_basic(vi):
        if isinstance(vi, float):
            return Decimal(str(vi))
        return vi

    if isinstance(data, (list, tuple)):
        data = [object_with_float_to_decimal(i) for i in data]
    elif isinstance(data, float):
        return to_basic(data)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                object_with_float_to_decimal(v)
            elif isinstance(v, (list, tuple)):
                data[k] = [
                    object_with_float_to_decimal(x)
                    if isinstance(x, dict)
                    else to_basic(x)
                    for x in v
                ]
            else:
                data[k] = to_basic(v)
    return data
