from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from decimal import Decimal
from django.contrib.auth.decorators import login_required

from .models import User, Auction, Comment, Bid

categories_list=(
    ("misc", "Misc"),
    ("fashion", "Fashion"),
    ("toys", "Toys"),
    ("electronics", "Electronics"),
    ("home", "Home"),
    ("pet", "Pet")
)


def index(request):
    auctions= Auction.objects.filter(sold_status=False)
    return render(request, "auctions/index.html",{
        "auctions":auctions
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create(request):
    if not request.user.is_authenticated:
        return render(request, "auctions/login.html", {
            "message": "Loggin to Create a Listing"
        })
    if request.method =="POST":
        form=NewPostForm(request.POST)
        if form.is_valid():
            auction= Auction.objects.create(
                name=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                starting_price=form.cleaned_data["price"],
                current_price=form.cleaned_data["price"],
                category=form.cleaned_data["category"],
                image=form.cleaned_data["image"],
                seller=request.user

            )
            return HttpResponseRedirect(reverse("listing", args=[auction.id]))
    return render(request, "auctions/create.html", {
        "form": NewPostForm()
    })

def listing(request,listing_id):
    listing= Auction.objects.get(pk=listing_id)
    watchlist=False
    message=None
    if request.user.is_authenticated:
        watchlist = listing.watchlist.filter(id=request.user.id).exists()

    if request.method =="POST":
        if request.POST.get("action")=="bid":
            amount= Decimal(request.POST["bid"])
            if amount>=listing.starting_price and amount > listing.current_price:
                listing.current_price=amount
                listing.save()
                Bid.objects.create(
                    amount = amount,
                    item = listing,
                    user = request.user
                )
            else:
                message="Bid Value Too low"
        elif request.POST.get("action")=="comment":
            Comment.objects.create(
                comment= request.POST["comment"],
                commenter= request.user,
                item= listing
            )
    bids= listing.bids.order_by("-amount")
    comments = listing.comments.all().order_by("-id")
    return render(request, "auctions/listings.html", {
        "listing":listing,
        "watchlist":watchlist,
        "bids":bids,
        "message":message,
        "comments":comments
    })

@login_required
def add_watchlist(request,listing_id):
    listing= Auction.objects.get(pk=listing_id)
    listing.watchlist.add(request.user)
    return HttpResponseRedirect( reverse("listing", args=[listing_id]))

@login_required
def remove_watchlist(request,listing_id):
    listing= Auction.objects.get(pk=listing_id)
    listing.watchlist.remove(request.user)
    return HttpResponseRedirect( reverse("listing", args=[listing_id]))

@login_required
def close_listing(request, listing_id):
    listing= Auction.objects.get(pk=listing_id)
    listing.sold_status=True
    if listing.bids.first():
        winning_bid= listing.bids.order_by("-amount").first()
        listing.buyer= winning_bid.user

    listing.save()
    return HttpResponseRedirect( reverse("listing", args=[listing_id]))

@login_required
def watchlist(request):
    watch_list= request.user.WL_auctions.all()
    return render(request, "auctions/watchlist.html",{
        "watchlist":watch_list
    })

@login_required
def remove_watchlist2(request,listing_id):
    listing= Auction.objects.get(pk=listing_id)
    listing.watchlist.remove(request.user)
    return HttpResponseRedirect( reverse("watchlist"))

def categories(request, cat):
    items= Auction.objects.filter(sold_status=False).filter(category = cat)
    return render(request, "auctions/categories.html", {
        "cats":categories_list,
        "auctions":items
    })


class NewPostForm(forms.Form):
    title = forms.CharField(label="Name of Item",  max_length=64)
    description = forms.CharField(label="Description",widget=forms.Textarea(), max_length=200)
    price = forms.DecimalField(label="Starting Price €",  min_value=0, decimal_places=2)
    category=forms.ChoiceField(label="Category", choices=categories_list, required=False)
    image=forms.URLField(label="Image", required=False)