"""
Utilities for the Indivo admin tool
"""

from django.http import HttpResponseNotAllowed

# taken from pointy-stick.com with some modifications
class MethodDispatcher(object):
    def __init__(self, method_map):
        self.methods= method_map
    
    def resolve(self, request):
        view_func = self.methods.get(request.method, None)
        return view_func
    
    @property
    def resolution_error_response(self):
        return HttpResponseNotAllowed(self.methods.keys())
    
    def __call__(self, request, *args, **kwargs):
        view_func = self.resolve(request)
        if view_func:
            return view_func(request, *args, **kwargs)
        return self.resolution_error_response
