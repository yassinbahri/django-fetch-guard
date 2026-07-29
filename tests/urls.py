from django.urls import path

from . import views


urlpatterns = [
    path("books/normal/", views.normal_books),
    path("books/peers/", views.peer_books),
    path("books/strict/", views.strict_books),
    path("books/strict-broken/", views.strict_broken_books),
]

