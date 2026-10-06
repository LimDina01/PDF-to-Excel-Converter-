"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('converter.urls')),
]

from django.urls import re_path
from django.views.static import serve
from django.conf import settings

# Serve static files in production securely by reading directly from the collected staticfiles directory
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Auto-create admin user on startup
import sys
if 'runserver' in sys.argv or 'gunicorn' in sys.modules or 'gunicorn' in sys.argv[0] if sys.argv else True:
    try:
        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError, ProgrammingError
        
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'Tr!ckP@ssw0rd$2026')
            print("Auto-created superuser 'admin'")
        else:
            u = User.objects.get(username='admin')
            u.set_password('Tr!ckP@ssw0rd$2026')
            u.is_staff = True
            u.is_superuser = True
            u.save()

        # Auto-create demo user for testing on production
        if not User.objects.filter(username='demo_user').exists():
            User.objects.create_user('demo_user', 'demo@example.com', 'password123')
            print("Auto-created sample user 'demo_user'")
        else:
            du = User.objects.get(username='demo_user')
            du.set_password('password123')
            du.save()
    except (OperationalError, ProgrammingError, Exception):
        pass  # Fails gracefully if the database isn't migrated yet

