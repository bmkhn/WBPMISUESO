# Activity Evaluation - Quick Reference Guide

## Current vs. Proposed System

### Current System ❌
```
Project
  └── ProjectEvaluation (Simple: Rating 1-5 + Comment)
      └── One evaluation per project
```

### Proposed System ✅
```
Project
  └── ProjectEvent (Activity)
      └── ActivityEvaluation (Detailed: Multiple Criteria)
          ├── Trainings/Seminars (7 criteria)
          ├── Timeliness (2 criteria)
          └── Tally Results (Aggregated Statistics)
```

## PSU-ESO 004 Form Structure

### Evaluation Criteria

#### A. Trainings/Seminars Section
| Criteria | Field Name | Rating Scale |
|----------|-----------|--------------|
| a. Attainment of Objectives | `attainment_of_objectives` | 1-5 |
| b. Time Management | `time_management` | 1-5 |
| c. Resource Persons/Facilitators | `resource_persons_facilitators` | 1-5 |
| d. Topics | `topics` | 1-5 |
| e. Training venue | `training_venue` | 1-5 |
| f. Food | `food` | 1-5 |
| g. Materials/Handouts | `materials_handouts` | 1-5 |
| **Over-all Rating** | `trainings_seminars_overall` | 1-5 |

#### Timeliness Section
| Criteria | Field Name | Rating Scale |
|----------|-----------|--------------|
| a. Extension service is held as scheduled | `held_as_scheduled` | 1-5 |
| b. Extension service answers the present need | `answers_present_need` | 1-5 |
| **Over-all Rating** | `timeliness_overall` | 1-5 |

### Rating Scale
- **5 (100-95)**: Excellent
- **4 (94-89)**: Very Good
- **3 (88-83)**: Good
- **2 (82-77)**: Fair
- **1 (76 and below)**: Needs Improvement (Poor)

## Tally Calculations

### What to Tally:
1. **Average Rating per Criterion**: Sum of all ratings / Number of evaluations
2. **Rating Distribution**: Count of each rating (1-5) as percentage
3. **Overall Averages**: Average of all criteria in each section
4. **Performance Indicator 3**: 
   - Count evaluations with timeliness rating ≥ 3 (Good or better)
   - Percentage = (Good+ ratings / Total) × 100

### Example Tally Output Format:
```
┌─────────────────────────────────────────┐
│ Activity: [Activity Title]             │
│ Total Evaluations: 25                   │
├─────────────────────────────────────────┤
│ Trainings/Seminars:                     │
│   • Attainment of Objectives: 4.2 ⭐⭐⭐⭐ │
│   • Time Management: 3.8 ⭐⭐⭐          │
│   • Resource Persons: 4.5 ⭐⭐⭐⭐        │
│   • Topics: 4.0 ⭐⭐⭐⭐                  │
│   • Training Venue: 3.6 ⭐⭐⭐           │
│   • Food: 4.1 ⭐⭐⭐⭐                    │
│   • Materials/Handouts: 3.9 ⭐⭐⭐        │
│   Overall: 4.0 (Very Good)              │
├─────────────────────────────────────────┤
│ Timeliness:                             │
│   • Held as Scheduled: 4.3 ⭐⭐⭐⭐       │
│   • Answers Present Need: 4.4 ⭐⭐⭐⭐     │
│   Overall: 4.35 (Very Good)             │
├─────────────────────────────────────────┤
│ Rating Distribution:                    │
│   Excellent (5): ████████ 32%           │
│   Very Good (4): ████████████ 48%       │
│   Good (3): ████ 16%                    │
│   Fair (2): █ 4%                        │
│   Poor (1): 0%                          │
├─────────────────────────────────────────┤
│ Performance Indicator 3: 96% ✅         │
└─────────────────────────────────────────┘
```

## Database Schema Summary

### New Table: `ActivityEvaluation`
```sql
- activity (FK → ProjectEvent)
- evaluated_by (FK → User, nullable)
- evaluator_name (CharField, optional for external evaluators)
- venue (CharField)
- evaluation_date (DateField)
- created_at, edited_at (DateTimeField)

-- Trainings/Seminars (all PositiveSmallIntegerField, 1-5)
- attainment_of_objectives
- time_management
- resource_persons_facilitators
- topics
- training_venue
- food
- materials_handouts
- trainings_seminars_overall

-- Timeliness (all PositiveSmallIntegerField, 1-5)
- held_as_scheduled
- answers_present_need
- timeliness_overall

- comments (TextField)
```

## URL Routes Needed

```
/projects/<project_id>/activities/<activity_id>/evaluations/
  → List all evaluations for activity

/projects/<project_id>/activities/<activity_id>/evaluations/add/
  → Add new evaluation

/projects/<project_id>/activities/<activity_id>/evaluations/<eval_id>/edit/
  → Edit evaluation

/projects/<project_id>/activities/<activity_id>/evaluations/tally/
  → View aggregated tally results
```

## UI Components Needed

1. **Evaluation Form Modal/Page**
   - Matches PSU-ESO 004 layout
   - Radio buttons for each criterion (1-5)
   - Optional evaluator name field
   - Venue field (pre-filled from activity location)

2. **Evaluation List View**
   - Cards showing each evaluation
   - Expandable details
   - Edit/Delete buttons (if owner)

3. **Tally Dashboard**
   - Summary statistics at top
   - Average ratings per criterion
   - Rating distribution chart
   - Performance Indicator 3 display

4. **Activity Card Integration**
   - "View Evaluations" button/link
   - Evaluation count badge
   - Quick stats preview

## Key Implementation Notes

1. **Multiple Evaluations**: Each activity can have multiple evaluations (one per evaluator/participant)

2. **Optional Evaluator**: Support both system users and external evaluators (via `evaluator_name`)

3. **Automatic Calculations**: Tally results calculated on-the-fly from stored evaluations

4. **Backward Compatibility**: Keep existing `ProjectEvaluation` model for project-level evaluations

5. **Validation**: Ensure all ratings are between 1-5, required fields are filled

6. **Permissions**: 
   - Anyone can view evaluations
   - Authenticated users can add evaluations
   - Evaluator can edit/delete their own evaluation
   - Admins can manage all evaluations

## Next Steps

1. ✅ Review this plan with client
2. Create database migration for `ActivityEvaluation` model
3. Implement views and forms
4. Create templates matching PSU-ESO 004
5. Add tally/aggregation logic
6. Integrate with activity views
7. Add export functionality
8. Test with sample data





