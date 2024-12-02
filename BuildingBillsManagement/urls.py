from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('residents/', include('accounts.urls')),
    path('building/', include('building.urls')),
    path('', include('pages.urls')),
]
