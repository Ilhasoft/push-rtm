import os
import mimetypes

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class MimetypeValidator:
    def __init__(self, mimetypes):
        self.mimetypes = mimetypes
    
    def __call__(self, value):
        ext = os.path.splitext(value.name)[1]
        if ext.lower() != ".json":
            raise ValidationError(_("Unsupported file extension."))
        
        try:
            mime = mimetypes.guess_type("{}".format(value.name))[0]
            if not mime in self.mimetypes:
                raise ValidationError(_("This file is not an accetale file type"))
        except AttributeError as e:
            raise ValidationError(_("This file could not be validated for file type"))
