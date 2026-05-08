import functools
import inspect


def single_arg_constraint(*constraints):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for key, val in bound_args.arguments.items():
                if key in ["cls", "self"]:
                    continue
                if not val in constraints:
                    raise ValueError(f'"{val}" is not allowed argument, allows: {constraints}')

            return func(*args, **kwargs)

        return wrapper

    return decorator

