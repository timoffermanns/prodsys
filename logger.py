from functools import partial, wraps

import state


class Datacollector:
    data = {'States': []}

    def patch_state(self, __state, attr, pre=None, post=None):
        """Patch *state* so that it calls the callable *pre* before each
        put/get/request/release operation and the callable *post* after each
        operation.  The only argument to these functions is the resource
        instance."""
        def get_wrapper(func):
            # Generate a wrapper for a process state function
            @wraps(func)
            def wrapper(*args, **kwargs):
                # This is the actual wrapper
                # Call "pre" callback
                if pre:
                    pre(__state)
                # Perform actual operation
                ret = func(*args, **kwargs)
                # Call "post" callback
                if post:
                    post(__state)
                return ret
            return wrapper
        # Replace the original operations with our wrapper
        for name in attr:
            if hasattr(__state, name):
                setattr(__state, name, get_wrapper(getattr(__state, name)))

    def register_patch(self, __state, attr, pre=None, post=None):
        if pre is not None:
            pre = self.register_monitor(pre, self.data['States'])
        if post is not None:
            post = self.register_monitor(post, self.data['States'])
        self.patch_state(__state, attr, pre, post)

    def register_monitor(self, monitor, data):
        partial_monitor = partial(monitor, data)
        return partial_monitor

def pre_monitor_state(data, __state: state.State):
    """This is our monitoring callback."""
    item = (
        __state.resource.ID,
        __state.ID,
        'Start',
        __state.env.now,
    )
    data.append(item)

def post_monitor_state(data, __state: state.State):
    """This is our monitoring callback."""
    item = (
        __state.resource.ID,
        __state.ID,
        'End',
        __state.env.now,
        __state.done_in
    )
    data.append(item)


