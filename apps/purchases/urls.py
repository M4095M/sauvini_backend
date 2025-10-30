from django.urls import path
from . import views

urlpatterns = [
    # Admin purchases endpoints
    path('auth/admin/purchases', views.admin_list_purchases, name='admin_list_purchases'),
    path('auth/admin/purchases/statistics', views.admin_purchase_statistics, name='admin_purchase_statistics'),
    path('auth/admin/purchases/<uuid:purchase_id>', views.admin_get_purchase, name='admin_get_purchase'),
    path('auth/admin/purchases/<uuid:purchase_id>/status', views.admin_update_purchase_status, name='admin_update_purchase_status'),
    path('auth/admin/purchases/<uuid:purchase_id>/delete', views.admin_delete_purchase, name='admin_delete_purchase'),
]


