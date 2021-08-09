import functools
from time import sleep


class BaseRover:
    def __init__(self, mirobot):
        self._mirobot = mirobot

    def time_decorator(fn):
        @functools.wraps(fn)
        def time_wrapper(self, *args, **kwargs):
            args_names = fn.__code__.co_varnames[:fn.__code__.co_argcount]
            args_dict = dict(zip(args_names, args))

            def get_arg(arg_name, default=None):
                if arg_name in args_dict:
                    return args_dict.get(arg_name)
                elif arg_name in kwargs:
                    return kwargs.get(arg_name)
                else:
                    return default

            time = get_arg('time', 0)
            wait = get_arg('wait', True)

            output = fn(self, *args, **kwargs)

            if time:
                sleep(time)
                self.stop(wait=wait)

            return output

        return time_wrapper

    @time_decorator
    def move_upper_left(self, time=0, wait=True):
        instruction = "W7"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_upper_right(self, time=0, wait=True):
        instruction = "W9"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_bottom_left(self, time=0, wait=True):
        instruction = "W1"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_bottom_right(self, time=0, wait=True):
        instruction = "W3"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_left(self, time=0, wait=True):
        instruction = "W4"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_right(self, time=0, wait=True):
        instruction = "W6"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def rotate_left(self, time=0, wait=True):
        instruction = "W10"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def rotate_right(self, time=0, wait=True):
        instruction = "W11"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_forward(self, time=0, wait=True):
        instruction = "W8"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    @time_decorator
    def move_backward(self, time=0, wait=True):
        instruction = "W2"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')

    def stop(self, wait=True):
        instruction = "W0"
        return self._mirobot.send_msg(instruction, wait=wait, terminator='\r\n')
