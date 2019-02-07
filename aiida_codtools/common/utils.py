# -*- coding: utf-8 -*-


def get_input_node(cls, value):
    """Return a `Node` of a given class and given value.

    If a `Node` of the given type and value already exists, that will be returned, otherwise a new one will be created,
    stored and returned.

    :param cls: the `Node` class
    :param value: the value of the `Node`
    """
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.data.base import Bool, Float, Int, Str
    from aiida.orm.data.parameter import ParameterData

    if cls in (Bool, Float, Int, Str):

        result = QueryBuilder().append(cls, filters={'attributes.value': value}).first()

        if result is None:
            node = cls(value).store()
        else:
            node = result[0]

    elif cls is ParameterData:
        result = QueryBuilder().append(cls, filters={'attributes': {'==': value}}).first()

        if result is None:
            node = cls(dict=value).store()
        else:
            node = result[0]

    else:
        raise NotImplementedError

    return node
