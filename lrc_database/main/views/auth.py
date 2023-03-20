from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, password_validation
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from ..forms import LogIn, ResetPassword
from ..models import LRCDatabaseUser

def login_user(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		form = LogIn(request.POST)
		if not form.is_valid():
			messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
			return redirect("login")
		else:
			data = form.cleaned_data
			try:
				user = LRCDatabaseUser.objects.get(username=data['username'])
				if not user.has_usable_password():
					try:
						password_validation.validate_password(data["password"], user)
					except ValidationError as error:
						html = "<br/><br/><ul>"
						for e in error:
							html += f"<li>{e}</li>"
						html += "</ul>"
						messages.add_message(request, messages.ERROR, f"Error while setting your new password: {html}")
						return redirect("login")
					user.set_password(data["password"])
					user.save()
					messages.add_message(request, messages.SUCCESS, f"Password used to log in, has become your new password.")
			except:
				messages.add_message(request, messages.ERROR, f"Username not found.")
				return redirect("login")
			user = authenticate(request, username=data['username'], password=data['password'])
			if user is not None:
				login(request, user)
				return redirect("/")
			else:
				messages.add_message(request, messages.ERROR, f"Username and password combination doesn't match.")
				return redirect("login")
	else:
		form = LogIn()
		return render(request, "registration/login.html", {"form":form})

def reset_password(request: HttpRequest) -> HttpRequest:
	if request.method == "POST":
		form = ResetPassword(request.POST)
		if not form.is_valid():
			messages.add_message(request, messages.ERROR, f"Form errors: {form.errors}")
			return redirect("login")
		else:
			user = form.cleaned_data["user"]
			user.set_unusable_password()
			user.save()
			messages.add_message(request, messages.SUCCESS, f"{user}'s password has been succesfully reset. Tell them to login with password of their choice.")
			return redirect("reset_password")
	else:
		form = ResetPassword()
		return render(request, "registration/reset_password.html", {"form":form})