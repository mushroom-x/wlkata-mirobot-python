from dataclasses import asdict, astuple, fields
import numbers
import operator


class basic_dataclass:
    def asdict(self):
        return asdict(self)

    def astuple(self):
        return astuple(self)

    def fields(self):
        return fields(self)

    @classmethod
    def _new_from_dict(cls, dictionary):
        return cls(**dictionary)


class featured_dataclass(basic_dataclass):
    def _cross_same_type(self, other, operation_function, single=False):
        new_values = {}
        for f in self.fields():
            this_value = getattr(self, f.name)

            if single:
                other_value = other
            else:
                other_value = getattr(other, f.name)

            result = operation_function(this_value, other_value)

            new_values[f.name] = result

        return new_values

    def _binary_operation(self, other, operation):
        def operation_function(this_value, other_value):
            if None in (this_value, other_value):
                return None
            else:
                return operation(this_value, other_value)

        if isinstance(other, type(self)):
            new_values = self._cross_same_type(other, operation_function)

        elif isinstance(other, numbers.Real):
            new_values = self._cross_same_type(other, operation_function, single=True)

        else:
            raise NotImplementedError(f"Cannot handle {type(self)} and {type(other)}")

        return self._new_from_dict(new_values)

    def _unary_operation(self, operation_function):
        new_values = {f.name: operation_function(f)
                      for f in self.fields()}

        return self._new_from_dict(new_values)

    def _basic_unary_operation(self, operation):
        def operation_function(field):
            value = getattr(self, field.name)
            if value is not None:
                return operation(value)
            else:
                return None

        return self._unary_operation(operation_function)

    def _comparision_operation(self, other, operation):
        def operation_function(this_value, other_value):
            if None in (this_value, other_value):
                return True
            else:
                return operation(this_value, other_value)

        if isinstance(other, type(self)):
            new_values = self._cross_same_type(other, operation_function).values()

        elif isinstance(other, (int, float)):
            new_values = self._cross_same_type(other, operation_function, single=True).values()

        else:
            raise NotImplementedError(f"Cannot handle {type(self)} and {type(other)}")

        if all(new_values):
            return True

        elif not any(new_values):
            return False

        else:
            return None

    def __or__(self, other):
        def operation_function(this_value, other_value):
            if this_value is None:
                return other_value
            else:
                return this_value

        new_values = self._cross_same_type(other, operation_function)
        return self._new_from_dict(new_values)

    def __and__(self, other):
        def operation_function(this_value, other_value):
            if None not in (this_value, other_value):
                return this_value
            else:
                return None

        new_values = self._cross_same_type(other, operation_function)
        return self._new_from_dict(new_values)

    def int(self):
        def operation_function(field):
            value = getattr(self, field.name)
            if field.type in (float,) and value is not None:
                return int(value)
            else:
                return value

        return self._unary_operation(operation_function)

    def round(self):
        def operation_function(field):
            value = getattr(self, field.name)
            if field.type in (float,) and value is not None:
                return round(value)
            else:
                return value

        return self._unary_operation(operation_function)

    def __add__(self, other):
        return self._binary_operation(other, operator.add)

    def __radd__(self, other):
        return self._binary_operation(other, operator.add)

    def __sub__(self, other):
        return self._binary_operation(other, operator.sub)

    def __rsub__(self, other):
        def rsub(dataclass_value, number):
            return operator.sub(number, dataclass_value)

        return self._binary_operation(other, rsub)

    def __mul__(self, other):
        return self._binary_operation(other, operator.mul)

    def __rmul__(self, other):
        return self._binary_operation(other, operator.mul)

    def __div__(self, other):
        return self._binary_operation(other, operator.div)

    def __rdiv__(self, other):
        def rdiv(dataclass_value, number):
            return operator.div(number, dataclass_value)

        return self._binary_operation(other, rdiv)

    def __truediv__(self, other):
        return self._binary_operation(other, operator.truediv)

    def __rtruediv__(self, other):
        def rtruediv(dataclass_value, number):
            return operator.truediv(number, dataclass_value)

        return self._binary_operation(other, operator.truediv)

    def __mod__(self, other):
        return self._binary_operation(other, operator.mod)

    def __abs__(self):
        return self._basic_unary_operation(operator.abs)

    def __pos__(self):
        return self._basic_unary_operation(operator.pos)

    def __neg__(self):
        return self._basic_unary_operation(operator.neg)

    def __lt__(self, other):
        return self._comparision_operation(other, operator.lt)

    def __le__(self, other):
        return self._comparision_operation(other, operator.le)

    def __eq__(self, other):
        return self._comparision_operation(other, operator.eq)

    def __ne__(self, other):
        return self._comparision_operation(other, operator.ne)

    def __ge__(self, other):
        return self._comparision_operation(other, operator.ge)

    def __gt__(self, other):
        return self._comparision_operation(other, operator.gt)
