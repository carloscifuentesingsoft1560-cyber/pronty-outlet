from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')

def product_list(request):
    return render(request, 'catalog/product_list.html')

def product_detail(request):
    return render(request, 'catalog/product_detail.html')