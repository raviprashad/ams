from django.contrib import admin
from django.urls import path , include
from users.views import redirect_user
from core.views import home_view
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('redirect/', redirect_user, name='redirect_user'),
    
    # Custom login/logout
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # App URLs
    path('users/', include('users.urls')),
    path('academics/', include('academics.urls')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('user_messages/', include('user_messages.urls')),
    path('leaves/', include('leaves.urls')),
    path('timetable/', include('timetable.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
