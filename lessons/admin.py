from django.contrib import admin
from .models import Lesson, LessonSlot

# Register your models here.

class LessonSlotInline(admin.TabularInline):
    model = LessonSlot
    extra = 1  
    fields = ('starts_at', 'ends_at', 'status')
    readonly_fields = ()  

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active', 'teacher')
    search_fields = ('title', 'description', 'teacher__email')
    inlines = [LessonSlotInline]  