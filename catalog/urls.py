from django.urls import path
from . import views

urlpatterns =[
    path('', views.home, name='home'),
    path('productos/', views.product_list, name= 'product_list'),
    path('productos/producto-ejemplo/', views.product_detail, name='product_detail'),
]

