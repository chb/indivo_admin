"""
Utilities for the Indivo admin tool
"""

from django.http import HttpResponseNotAllowed
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.forms.util import ErrorList

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

def render_admin_response(request, template_path, context={}):

    # add in the User and recent Records to all admin Contexts
    recents = request.session.get('recent_records', set([]))
    admin_context = {'recents':recents,
                     'user':request.user}
    admin_context.update(context)
    return render_to_response(template_path, admin_context,
                              context_instance=RequestContext(request))

def get_users_to_manage(request):
    users = User.objects.all().order_by('username')
    return users

def append_error_to_form(form, field_name, error_text):
    errors = form._errors.setdefault(field_name, ErrorList())
    errors.append(error_text)
