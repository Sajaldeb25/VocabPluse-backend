from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.category_list, name="category-list"),
    path("wordsets/", views.wordset_list, name="wordset-list"),
    path("wordsets/<int:pk>/cards/", views.wordset_cards, name="wordset-cards"),
    path("words/<int:pk>/define/", views.word_define, name="word-define"),
    path("words/<int:pk>/explain/", views.word_explain, name="word-explain"),
    path("words/<int:pk>/questions/", views.word_questions, name="word-questions"),
]
