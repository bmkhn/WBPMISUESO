# Activity Evaluation Implementation Plan
## Based on PSU-ESO 004 Evaluation Form (2025)

## Current Situation
- **Current System**: Evaluations are done at the **project level** only
- **Client Requirement**: Evaluations should be done for **each activity** (ProjectEvent) with detailed criteria and results should be tallied

## Proposed Solution

### 1. Database Model Changes

#### New Model: `ActivityEvaluation`
Create a new model to store detailed evaluations for each activity (ProjectEvent):

```python
class ActivityEvaluation(models.Model):
    """
    Detailed evaluation for a specific activity (ProjectEvent) based on PSU-ESO 004 form
    """
    # Basic Information
    activity = models.ForeignKey(ProjectEvent, on_delete=models.CASCADE, related_name='evaluations')
    evaluated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activity_evaluations')
    evaluator_name = models.CharField(max_length=255, blank=True, null=True, help_text="Optional name if evaluator is not a system user")
    venue = models.CharField(max_length=255, blank=True, null=True)
    evaluation_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Trainings/Seminars Section (A)
    # Sub-items a-g (each rated 1-5)
    attainment_of_objectives = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    time_management = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    resource_persons_facilitators = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    topics = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    training_venue = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    food = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    materials_handouts = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    trainings_seminars_overall = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    # Timeliness Section
    held_as_scheduled = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    answers_present_need = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    timeliness_overall = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    # Additional Comments
    comments = models.TextField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['activity', '-evaluation_date'], name='act_eval_act_date_idx'),
            models.Index(fields=['evaluated_by', '-evaluation_date'], name='act_eval_user_idx'),
        ]
    
    def __str__(self):
        return f"Evaluation of {self.activity.title} by {self.evaluated_by.username if self.evaluated_by else self.evaluator_name} on {self.evaluation_date}"
    
    @property
    def trainings_seminars_average(self):
        """Calculate average rating for Trainings/Seminars section"""
        ratings = [
            self.attainment_of_objectives,
            self.time_management,
            self.resource_persons_facilitators,
            self.topics,
            self.training_venue,
            self.food,
            self.materials_handouts
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None
    
    @property
    def timeliness_average(self):
        """Calculate average rating for Timeliness section"""
        ratings = [self.held_as_scheduled, self.answers_present_need]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None
```

### 2. Tally/Aggregation System

#### Model Methods for Tallying
Add methods to `ProjectEvent` model to calculate aggregated statistics:

```python
# In ProjectEvent model
@property
def evaluation_statistics(self):
    """Get aggregated evaluation statistics for this activity"""
    evaluations = self.evaluations.all()
    if not evaluations.exists():
        return None
    
    stats = {
        'total_evaluations': evaluations.count(),
        'trainings_seminars': {
            'attainment_of_objectives': self._calculate_average(evaluations, 'attainment_of_objectives'),
            'time_management': self._calculate_average(evaluations, 'time_management'),
            'resource_persons_facilitators': self._calculate_average(evaluations, 'resource_persons_facilitators'),
            'topics': self._calculate_average(evaluations, 'topics'),
            'training_venue': self._calculate_average(evaluations, 'training_venue'),
            'food': self._calculate_average(evaluations, 'food'),
            'materials_handouts': self._calculate_average(evaluations, 'materials_handouts'),
            'overall_average': self._calculate_average(evaluations, 'trainings_seminars_overall'),
        },
        'timeliness': {
            'held_as_scheduled': self._calculate_average(evaluations, 'held_as_scheduled'),
            'answers_present_need': self._calculate_average(evaluations, 'answers_present_need'),
            'overall_average': self._calculate_average(evaluations, 'timeliness_overall'),
        },
        'rating_distribution': self._get_rating_distribution(evaluations),
    }
    return stats

def _calculate_average(self, evaluations, field_name):
    """Helper method to calculate average rating for a field"""
    values = [getattr(eval, field_name) for eval in evaluations if getattr(eval, field_name) is not None]
    return sum(values) / len(values) if values else None

def _get_rating_distribution(self, evaluations):
    """Get distribution of overall ratings (1-5)"""
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for eval in evaluations:
        overall = eval.trainings_seminars_overall or eval.timeliness_overall
        if overall:
            distribution[overall] = distribution.get(overall, 0) + 1
    return distribution
```

### 3. Views Implementation

#### New Views Needed:
1. **Activity Evaluation List View**: `activity_evaluations(request, project_pk, activity_pk)`
   - Display all evaluations for a specific activity
   - Show tally/aggregated results
   - Allow adding new evaluations

2. **Add/Edit Activity Evaluation View**: `add_activity_evaluation(request, project_pk, activity_pk)`
   - Form matching PSU-ESO 004 structure
   - All criteria with 1-5 rating scale
   - Optional evaluator name field

3. **Activity Evaluation Tally View**: `activity_evaluation_tally(request, project_pk, activity_pk)`
   - Display aggregated statistics
   - Charts/graphs showing distribution
   - Export functionality

### 4. URL Structure

```python
# In shared/projects/urls.py
path('<int:pk>/activities/<int:activity_pk>/evaluations/', activity_evaluations, name='activity_evaluations'),
path('<int:pk>/activities/<int:activity_pk>/evaluations/add/', add_activity_evaluation, name='add_activity_evaluation'),
path('<int:pk>/activities/<int:activity_pk>/evaluations/<int:eval_id>/edit/', edit_activity_evaluation, name='edit_activity_evaluation'),
path('<int:pk>/activities/<int:activity_pk>/evaluations/tally/', activity_evaluation_tally, name='activity_evaluation_tally'),
```

### 5. Template Structure

#### Activity Evaluations Page
- Link from activity card in `project_events.html`: "View Evaluations" button
- Display list of evaluations with expandable details
- Show tally summary at the top
- Form matching PSU-ESO 004 layout

#### Tally/Summary View
- Overall statistics dashboard
- Rating distribution charts
- Average ratings per criterion
- Percentage calculations (e.g., "X% rated as Good or better")

### 6. Integration Points

#### In `project_events.html`:
Add evaluation link/button for each activity:
```html
<a href="{% url 'activity_evaluations' project.id event.id %}" class="evaluation-link">
    <i class="fa-solid fa-clipboard-check"></i> Evaluations ({{ event.evaluations.count }})
</a>
```

#### Navigation:
- Add "Evaluations" tab or section in activity details
- Show evaluation count badge on activity cards

### 7. Key Features to Implement

1. **Detailed Evaluation Form**
   - Match PSU-ESO 004 form structure exactly
   - All criteria with radio buttons (1-5 scale)
   - Labels: Excellent (5), Very Good (4), Good (3), Fair (2), Poor (1)

2. **Tally/Aggregation System**
   - Calculate averages for each criterion
   - Count responses per rating level
   - Percentage calculations
   - Overall statistics

3. **Export Functionality**
   - Export evaluation data to Excel/PDF
   - Generate reports matching PSU-ESO 004 format
   - Include tally results

4. **Visualization**
   - Charts showing rating distribution
   - Bar charts for average ratings per criterion
   - Progress indicators

5. **Performance Indicator 3**
   - Track "Percentage of persons who rate timeliness as good or better"
   - Good = 3, 4, or 5
   - Calculate: (Count of 3+ ratings / Total evaluations) × 100

### 8. Migration Strategy

1. **Keep existing ProjectEvaluation** for backward compatibility
2. **Add ActivityEvaluation** as new model
3. **Gradually migrate** if needed (optional)
4. **Both can coexist** - project-level and activity-level evaluations

### 9. User Flow

1. User navigates to Project → Activities
2. Clicks on an activity
3. Sees "Evaluations" option
4. Can view existing evaluations and tally
5. Can add new evaluation using PSU-ESO 004 form
6. System automatically calculates and displays tallied results

### 10. Example Tally Output

```
Activity: "Training on Sustainable Farming"
Total Evaluations: 25

Trainings/Seminars Section:
- Attainment of Objectives: 4.2 (Very Good)
- Time Management: 3.8 (Good)
- Resource Persons/Facilitators: 4.5 (Very Good)
- Topics: 4.0 (Very Good)
- Training Venue: 3.6 (Good)
- Food: 4.1 (Very Good)
- Materials/Handouts: 3.9 (Good)
- Overall Average: 4.0 (Very Good)

Timeliness Section:
- Held as Scheduled: 4.3 (Very Good)
- Answers Present Need: 4.4 (Very Good)
- Overall Average: 4.35 (Very Good)

Rating Distribution:
- Excellent (5): 8 (32%)
- Very Good (4): 12 (48%)
- Good (3): 4 (16%)
- Fair (2): 1 (4%)
- Poor (1): 0 (0%)

Performance Indicator 3: 96% rated timeliness as Good or better
```

## Implementation Priority

1. **Phase 1**: Create ActivityEvaluation model and basic CRUD
2. **Phase 2**: Implement tally/aggregation system
3. **Phase 3**: Create UI matching PSU-ESO 004 form
4. **Phase 4**: Add visualization and export features
5. **Phase 5**: Integration with existing project/activity views

## Benefits

- ✅ Evaluations at activity level (as required)
- ✅ Detailed criteria matching official form
- ✅ Automatic tallying and aggregation
- ✅ Performance indicator tracking
- ✅ Better insights per activity
- ✅ Maintains backward compatibility with project-level evaluations





