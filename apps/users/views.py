# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.db.models import Q

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'login.html')


def signup_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')
        
        # TODO: Create user in database
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')
    
    return render(request, 'signup.html')

def search_view(request):
    """Handle search across materials, contractors, designers"""
    query = request.GET.get('q', '').strip()
    
    context = {
        'query': query,
        'materials': [],
        'contractors': [],
        'designers': [],
        'total_count': 0,
        'materials_count': 0,
        'contractors_count': 0,
        'designers_count': 0,
    }
    
    if query:
        # TODO: Replace with actual database queries
        # For now, using dummy data
        
        # Example: Search materials
        # materials = Material.objects.filter(
        #     Q(name__icontains=query) | 
        #     Q(description__icontains=query) |
        #     Q(brand__icontains=query)
        # )[:12]
        
        # Dummy data for demonstration
        context['materials'] = []
        context['contractors'] = []
        context['designers'] = []
        
        context['materials_count'] = len(context['materials'])
        context['contractors_count'] = len(context['contractors'])
        context['designers_count'] = len(context['designers'])
        context['total_count'] = (
            context['materials_count'] + 
            context['contractors_count'] + 
            context['designers_count']
        )
    
    return render(request, 'search.html', context)