# Quick Implementation Example: Token-Based Evaluation Access

## Step 1: Update ProjectEvent Model

```python
# In shared/projects/models.py

import uuid
from django.db import models

class ProjectEvent(models.Model):
    # ... existing fields ...
    
    # Add these new fields
    evaluation_token = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text="Unique token for public evaluation access"
    )
    evaluation_enabled = models.BooleanField(
        default=True,
        help_text="Allow public evaluations for this activity"
    )
    
    def get_evaluation_url(self):
        """Generate public evaluation URL"""
        from django.urls import reverse
        try:
            return reverse('public_activity_evaluation', kwargs={'token': str(self.evaluation_token)})
        except:
            return f"/evaluate/{self.evaluation_token}/"
    
    def get_full_evaluation_url(self):
        """Get full URL with domain"""
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}{self.get_evaluation_url()}"
```

## Step 2: Create Migration

```bash
python manage.py makemigrations projects
python manage.py migrate
```

## Step 3: Create Public Evaluation View

```python
# In shared/projects/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import ProjectEvent, ActivityEvaluation

def public_activity_evaluation(request, token):
    """
    Public-facing evaluation form accessible via unique token
    No authentication required
    """
    try:
        activity = ProjectEvent.objects.select_related('project').get(
            evaluation_token=token, 
            evaluation_enabled=True
        )
    except ProjectEvent.DoesNotExist:
        return render(request, 'projects/evaluation_not_found.html', status=404)
    
    # Only allow evaluation for completed or ongoing activities
    if activity.status not in ['COMPLETED', 'ONGOING']:
        return render(request, 'projects/evaluation_not_available.html', {
            'message': 'Evaluation is not yet available for this activity.',
            'activity': activity
        })
    
    if request.method == 'POST':
        # Handle form submission
        evaluator_name = request.POST.get('evaluator_name', '').strip()
        if not evaluator_name:
            evaluator_name = 'Anonymous'
        
        # Create evaluation
        evaluation = ActivityEvaluation.objects.create(
            activity=activity,
            evaluated_by=request.user if request.user.is_authenticated else None,
            evaluator_name=evaluator_name,
            venue=activity.location or request.POST.get('venue', ''),
            
            # Trainings/Seminars Section
            attainment_of_objectives=int(request.POST.get('attainment_of_objectives', 0)) or None,
            time_management=int(request.POST.get('time_management', 0)) or None,
            resource_persons_facilitators=int(request.POST.get('resource_persons_facilitators', 0)) or None,
            topics=int(request.POST.get('topics', 0)) or None,
            training_venue=int(request.POST.get('training_venue', 0)) or None,
            food=int(request.POST.get('food', 0)) or None,
            materials_handouts=int(request.POST.get('materials_handouts', 0)) or None,
            trainings_seminars_overall=int(request.POST.get('trainings_seminars_overall', 0)) or None,
            
            # Timeliness Section
            held_as_scheduled=int(request.POST.get('held_as_scheduled', 0)) or None,
            answers_present_need=int(request.POST.get('answers_present_need', 0)) or None,
            timeliness_overall=int(request.POST.get('timeliness_overall', 0)) or None,
            
            # Comments
            comments=request.POST.get('comments', '')
        )
        
        return render(request, 'projects/evaluation_thank_you.html', {
            'activity': activity,
            'project': activity.project
        })
    
    # Show evaluation form
    return render(request, 'projects/public_activity_evaluation.html', {
        'activity': activity,
        'project': activity.project
    })
```

## Step 4: Add URL Route

```python
# In shared/projects/urls.py

urlpatterns = [
    # ... existing patterns ...
    
    # Public evaluation (no authentication required)
    path('evaluate/<uuid:token>/', public_activity_evaluation, name='public_activity_evaluation'),
]
```

## Step 5: Create Public Evaluation Template

```html
<!-- templates/projects/public_activity_evaluation.html -->
{% extends "base_public.html" %}
{% load static %}

{% block content %}
<div class="evaluation-container" style="max-width:800px;margin:2rem auto;padding:2rem;">
    <!-- Activity Information -->
    <div class="activity-info" style="background:#f5f5f5;padding:1.5rem;border-radius:8px;margin-bottom:2rem;">
        <h2 style="margin-top:0;">{{ activity.title }}</h2>
        <p><strong>Project:</strong> {{ project.title }}</p>
        <p><strong>Date:</strong> {{ activity.datetime|date:"F d, Y" }}</p>
        {% if activity.location %}
        <p><strong>Location:</strong> {{ activity.location }}</p>
        {% endif %}
    </div>
    
    <!-- Evaluation Form -->
    <form method="post" class="evaluation-form">
        {% csrf_token %}
        
        <!-- Evaluator Name -->
        <div class="form-group" style="margin-bottom:1.5rem;">
            <label style="display:block;margin-bottom:0.5rem;font-weight:600;">
                Your Name (Optional)
            </label>
            <input type="text" name="evaluator_name" 
                   placeholder="Enter your name" 
                   style="width:100%;padding:0.75rem;border:1px solid #ddd;border-radius:4px;">
        </div>
        
        <!-- Trainings/Seminars Section -->
        <div class="evaluation-section" style="margin-bottom:2rem;">
            <h3 style="border-bottom:2px solid #0A6C44;padding-bottom:0.5rem;">
                A. Trainings/Seminars
            </h3>
            
            <table style="width:100%;border-collapse:collapse;margin-top:1rem;">
                <thead>
                    <tr style="background:#f9f9f9;">
                        <th style="padding:0.75rem;text-align:left;border:1px solid #ddd;">Criteria</th>
                        <th style="padding:0.75rem;text-align:center;border:1px solid #ddd;">Excellent<br>(5)</th>
                        <th style="padding:0.75rem;text-align:center;border:1px solid #ddd;">Very Good<br>(4)</th>
                        <th style="padding:0.75rem;text-align:center;border:1px solid #ddd;">Good<br>(3)</th>
                        <th style="padding:0.75rem;text-align:center;border:1px solid #ddd;">Fair<br>(2)</th>
                        <th style="padding:0.75rem;text-align:center;border:1px solid #ddd;">Poor<br>(1)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:0.75rem;border:1px solid #ddd;">a. Attainment of Objectives</td>
                        <td style="padding:0.75rem;text-align:center;border:1px solid #ddd;">
                            <input type="radio" name="attainment_of_objectives" value="5" required>
                        </td>
                        <td style="padding:0.75rem;text-align:center;border:1px solid #ddd;">
                            <input type="radio" name="attainment_of_objectives" value="4">
                        </td>
                        <td style="padding:0.75rem;text-align:center;border:1px solid #ddd;">
                            <input type="radio" name="attainment_of_objectives" value="3">
                        </td>
                        <td style="padding:0.75rem;text-align:center;border:1px solid #ddd;">
                            <input type="radio" name="attainment_of_objectives" value="2">
                        </td>
                        <td style="padding:0.75rem;text-align:center;border:1px solid #ddd;">
                            <input type="radio" name="attainment_of_objectives" value="1">
                        </td>
                    </tr>
                    <!-- Repeat for other criteria: time_management, resource_persons_facilitators, etc. -->
                </tbody>
            </table>
        </div>
        
        <!-- Timeliness Section -->
        <div class="evaluation-section" style="margin-bottom:2rem;">
            <h3 style="border-bottom:2px solid #0A6C44;padding-bottom:0.5rem;">
                Timeliness
            </h3>
            <!-- Similar table structure -->
        </div>
        
        <!-- Comments -->
        <div class="form-group" style="margin-bottom:1.5rem;">
            <label style="display:block;margin-bottom:0.5rem;font-weight:600;">
                Additional Comments (Optional)
            </label>
            <textarea name="comments" rows="4" 
                      style="width:100%;padding:0.75rem;border:1px solid #ddd;border-radius:4px;"
                      placeholder="Share any additional feedback..."></textarea>
        </div>
        
        <!-- Submit Button -->
        <button type="submit" 
                style="background:#0A6C44;color:white;padding:1rem 2rem;border:none;border-radius:4px;font-size:1.1rem;cursor:pointer;width:100%;">
            Submit Evaluation
        </button>
    </form>
</div>
{% endblock %}
```

## Step 6: Add QR Code Generation (Optional)

```python
# Install: pip install qrcode[pil]

# In shared/projects/utils.py
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

def generate_evaluation_qr_code(activity):
    """Generate QR code for activity evaluation"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(activity.get_full_evaluation_url())
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    filename = f"evaluation_qr_{activity.id}.png"
    file_path = default_storage.save(f"qr_codes/{filename}", ContentFile(buffer.getvalue()))
    return default_storage.url(file_path)
```

## Step 7: Add "Get Evaluation Link" to Activity Card

```html
<!-- In shared/projects/templates/projects/project_events.html -->
<!-- Add this button to each activity card -->

<button onclick="showEvaluationLink({{ event.id }}, '{{ event.evaluation_token }}')" 
        style="background:#0A6C44;color:white;padding:0.5rem 1rem;border:none;border-radius:4px;cursor:pointer;">
    <i class="fa-solid fa-link"></i> Get Evaluation Link
</button>

<!-- Modal for showing evaluation link -->
<div id="eval-link-modal-{{ event.id }}" class="modal" style="display:none;">
    <div class="modal-content">
        <span class="close" onclick="closeEvalLinkModal({{ event.id }})">&times;</span>
        <h3>Evaluation Link for: {{ event.title }}</h3>
        
        <div style="text-align:center;margin:2rem 0;">
            <img src="{% url 'activity_evaluation_qr' project.id event.id %}" 
                 alt="QR Code" 
                 style="max-width:300px;">
        </div>
        
        <div style="margin:1rem 0;">
            <label>Shareable Link:</label>
            <div style="display:flex;gap:0.5rem;">
                <input type="text" 
                       id="eval-link-{{ event.id }}" 
                       value="{{ event.get_full_evaluation_url }}" 
                       readonly 
                       style="flex:1;padding:0.5rem;">
                <button onclick="copyEvaluationLink({{ event.id }})">Copy</button>
            </div>
        </div>
    </div>
</div>

<script>
function showEvaluationLink(eventId, token) {
    document.getElementById('eval-link-modal-' + eventId).style.display = 'flex';
}

function copyEvaluationLink(eventId) {
    const input = document.getElementById('eval-link-' + eventId);
    input.select();
    document.execCommand('copy');
    alert('Link copied to clipboard!');
}
</script>
```

## Step 8: Create QR Code View

```python
# In shared/projects/views.py

def activity_evaluation_qr(request, project_id, activity_id):
    """Generate and return QR code image"""
    from .utils import generate_evaluation_qr_code
    
    activity = get_object_or_404(ProjectEvent, pk=activity_id, project_id=project_id)
    qr_code_url = generate_evaluation_qr_code(activity)
    return redirect(qr_code_url)
```

## Step 9: Add URL for QR Code

```python
# In shared/projects/urls.py

path('<int:pk>/activities/<int:activity_id>/evaluation-qr/', 
     activity_evaluation_qr, 
     name='activity_evaluation_qr'),
```

## Testing Checklist

- [ ] Create an activity
- [ ] Verify evaluation_token is auto-generated
- [ ] Access evaluation link: `/evaluate/<token>/`
- [ ] Fill and submit evaluation form
- [ ] Verify evaluation is saved
- [ ] Check "Get Evaluation Link" button works
- [ ] Test QR code generation
- [ ] Test link copying functionality
- [ ] Test on mobile device
- [ ] Verify no login required for public form

## Summary

This implementation provides:
1. ✅ Unique token for each activity
2. ✅ Public evaluation form (no login)
3. ✅ QR code generation
4. ✅ Shareable link
5. ✅ Easy integration with existing system

The participant simply scans the QR code or clicks the link, fills the form, and submits - no account needed!





