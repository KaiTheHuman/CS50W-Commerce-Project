from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Auction(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=200)
    starting_price=models.DecimalField(max_digits=10, decimal_places=2)
    current_price=models.DecimalField(max_digits=10, decimal_places=2)
    sold_status = models.BooleanField(default=False)
    category=models.CharField(max_length=64)
    image=models.URLField(blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auctions")
    watchlist =models.ManyToManyField(User, blank=True, related_name="WL_auctions")
    buyer=models.ForeignKey(User, blank=True,null=True, on_delete=models.SET_NULL, related_name="won_auctions")

class Bid(models.Model):
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    item=models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    user=models.ForeignKey(User, on_delete=models.CASCADE)

class Comment(models.Model):
    comment=models.CharField(max_length=200)
    commenter=models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    item=models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="comments")