from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class CustomUserAdmin(BaseUserAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
            # Este codigo se debe descomentar si tampoco se quiere que se seleccionen grupos
            #if 'groups' in form.base_fields:
            #    form.base_fields['groups'].disabled = True
        return form

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

