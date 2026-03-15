
from django.contrib import admin
from .models import ActivityEvaluation


@admin.register(ActivityEvaluation)
class ActivityEvaluationAdmin(admin.ModelAdmin):
    list_display = ['activity', 'evaluator_name', 'evaluation_date', 'trainings_seminars_overall', 'timeliness_overall']
    list_filter = ['evaluation_date', 'activity', 'activity__project']
    search_fields = ['evaluator_name', 'activity__title', 'activity__project__title']
    readonly_fields = ['created_at', 'evaluation_date']
    date_hierarchy = 'evaluation_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('activity', 'evaluated_by', 'evaluator_name', 'venue', 'evaluation_date', 'created_at', 'edited_at')
        }),
        ('Trainings/Seminars', {
            'fields': ('attainment_of_objectives', 'time_management', 'resource_persons_facilitators', 
                      'topics', 'training_venue', 'food', 'materials_handouts', 'trainings_seminars_overall')
        }),
        ('Timeliness', {
            'fields': ('held_as_scheduled', 'answers_present_need', 'timeliness_overall')
        }),
        ('Comments', {
            'fields': ('comments',)
        }),
    )
