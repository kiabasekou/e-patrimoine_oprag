from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Inclusion de l'app patrimoine avec le namespace 'biens'
    path('', include(('patrimoine.urls', 'patrimoine'), namespace='biens')),
]
