import platform
from datetime import datetime

import sys

from jet_bridge_base import settings
from jet_bridge_base.configuration import configuration
from jet_bridge_base.db import Session
from jet_bridge_base.exceptions.api import APIException
from jet_bridge_base.exceptions.not_found import NotFound
from jet_bridge_base.exceptions.permission_denied import PermissionDenied
from jet_bridge_base.exceptions.validation_error import ValidationError
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.responses.template import TemplateResponse


class APIView(object):
    request = None
    session = None
    permission_classes = []

    def prepare(self):
        method_override = self.request.headers.get('X_HTTP_METHOD_OVERRIDE')
        if method_override is not None:
            self.request.method = method_override

        if self.request.method != 'OPTIONS':
            self.check_permissions()

        self.session = Session()

    def on_finish(self):
        if self.session:
            self.session.close()
            self.session = None

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def check_permissions(self):
        for permission in self.get_permissions():
            if not permission.has_permission(self):
                raise PermissionDenied(getattr(permission, 'message', 'forbidden'))

    def check_object_permissions(self, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(self, obj):
                raise PermissionDenied(getattr(permission, 'message', 'forbidden'))

    def default_headers(self):
        ACCESS_CONTROL_ALLOW_ORIGIN = 'Access-Control-Allow-Origin'
        ACCESS_CONTROL_EXPOSE_HEADERS = 'Access-Control-Expose-Headers'
        ACCESS_CONTROL_ALLOW_CREDENTIALS = 'Access-Control-Allow-Credentials'
        ACCESS_CONTROL_ALLOW_HEADERS = 'Access-Control-Allow-Headers'
        ACCESS_CONTROL_ALLOW_METHODS = 'Access-Control-Allow-Methods'

        return {
            ACCESS_CONTROL_ALLOW_ORIGIN: '*',
            ACCESS_CONTROL_ALLOW_METHODS: 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
            ACCESS_CONTROL_ALLOW_HEADERS: 'Authorization,DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-Application-Warning,X-HTTP-Method-Override',
            ACCESS_CONTROL_EXPOSE_HEADERS: 'Content-Length,Content-Range,Content-Disposition,Content-Type,X-Application-Warning',
            ACCESS_CONTROL_ALLOW_CREDENTIALS: 'true'
        }

    # def handle_exception(self, exc):
    #     if isinstance(exc, ValidationError):
    #         return JSONResponse({
    #             'error': True,
    #             'exc': type(exc).__name__
    #         })
    #
    #     raise exc

    def error_response(self, exc_type, exc, traceback):
        # exc_type = exc = traceback = None

        # if kwargs.get('exc_info'):
        #     exc_type, exc, traceback = kwargs['exc_info']

        # if isinstance(exc, APIException):
        #     status_code = exc.status_code

        if isinstance(exc, PermissionDenied):
        # if status_code == status.HTTP_403_FORBIDDEN:
            return TemplateResponse('403.html', {
                'path': self.request.path,
            })
        # elif status_code == status.HTTP_404_NOT_FOUND:
        elif isinstance(exc, NotFound):
            return TemplateResponse('404.html', {
                'path': self.request.path,
            })
        else:
            if settings.DEBUG:
                ctx = {
                    'path': self.request.path,
                    'full_path': self.request.protocol + "://" + self.request.host + self.request.path,
                    'method': self.request.method,
                    'type': configuration.get_type(),
                    'version': configuration.get_version(),
                    'current_datetime': datetime.now().strftime('%c'),
                    'python_version': platform.python_version(),
                    'python_executable': sys.executable,
                    'python_path': sys.path
                }

                if exc:
                    ctx.update({
                        'exception_type': exc_type.__name__,
                        'exception_value': str(exc)
                    })

                if traceback:
                    last_traceback = traceback

                    while last_traceback.tb_next:
                        last_traceback = last_traceback.tb_next

                    ctx.update({
                        'exception_last_traceback_line': last_traceback.tb_lineno,
                        'exception_last_traceback_name': last_traceback.tb_frame
                    })

                return TemplateResponse('500.debug.html', ctx)
            else:
                return TemplateResponse('500.html')

    def dispatch(self, action, *args, **kwargs):
        if not hasattr(self, action):
            raise NotFound()
        return getattr(self, action)(*args, **kwargs)

    def build_absolute_uri(self, url):
        return self.request.protocol + "://" + self.request.host + url
