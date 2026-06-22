from django.contrib import admin

from .models import AIExplanation, Category, ExampleQuestion, Word, WordSet


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}


class WordInline(admin.TabularInline):
    model = Word
    extra = 0
    fields = ("text", "part_of_speech", "level", "is_demo")


@admin.register(WordSet)
class WordSetAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "level", "order", "word_count")
    list_filter = ("category", "level")
    search_fields = ("title",)
    inlines = [WordInline]

    @admin.display(description="Words")
    def word_count(self, obj):
        return obj.words.count()


class ExampleQuestionInline(admin.TabularInline):
    model = ExampleQuestion
    extra = 0


class AIExplanationInline(admin.StackedInline):
    model = AIExplanation
    extra = 0
    readonly_fields = ("generated_at",)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("text", "word_set", "level", "is_demo")
    list_filter = ("level", "is_demo", "word_set__category")
    search_fields = ("text", "simple_definition")
    inlines = [AIExplanationInline, ExampleQuestionInline]


@admin.register(ExampleQuestion)
class ExampleQuestionAdmin(admin.ModelAdmin):
    list_display = ("word", "source", "year")
    list_filter = ("source",)
    search_fields = ("word__text", "question_text")
