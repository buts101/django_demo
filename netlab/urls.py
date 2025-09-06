from django.urls import path
from . import views

app_name = 'netlab'

urlpatterns = [
    path('', views.index, name='index'),
    path('topology/<int:topology_id>/', views.topology_detail, name='topology_detail'),
    path('router/<int:router_id>/', views.router_detail, name='router_detail'),
    path('run-test/', views.run_test, name='run_test'),
    path('test-status/<int:test_id>/', views.test_status, name='test_status'),
    path('topology/<int:topology_id>/json/', views.topology_json, name='topology_json'),
]