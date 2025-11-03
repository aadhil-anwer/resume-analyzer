from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")  # Change to where you want user to land after signup
    else:
        form = UserCreationForm()
    return render(request, "auth/signup.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")  # Change this too
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})

@login_required(login_url="/login/")
def logout_view(request):
    logout(request)
    return redirect("login")
