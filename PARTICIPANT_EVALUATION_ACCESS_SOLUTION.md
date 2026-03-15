# Participant Evaluation Access Solution

## Problem Statement
**How do participants (who may not be system users) access and evaluate a specific activity?**

Participants need a simple, accessible way to:
1. Find the evaluation form for the activity they attended
2. Submit their evaluation without needing to log in
3. Be sure they're evaluating the correct activity

## Proposed Solutions

### Solution 1: Unique Evaluation Token/Link (Recommended) ⭐

Generate a unique, shareable token for each activity that allows public evaluation access.

#### Implementation:

**1. Add Token Field to ProjectEvent Model:**
```python
# In shared/projects/models.py - ProjectEvent model
import uuid

class ProjectEvent(models.Model):
    # ... existing fields ...
    
    evaluation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, 
                                       help_text="Unique token for public evaluation access")
    evaluation_enabled = models.BooleanField(default=True, 
                                            help_text="Allow public evaluations for this activity")
    
    def get_evaluation_url(self):
        """Generate public evaluation URL"""
        from django.urls import reverse
        return reverse('public_activity_evaluation', kwargs={'token': str(self.evaluation_token)})
    
    def get_evaluation_qr_code_data(self):
        """Get data for QR code generation"""
        from django.conf import settings
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
        return f"{base_url}{self.get_evaluation_url()}"
```

**2. Create Public Evaluation View:**
```python
# In shared/projects/views.py

def public_activity_evaluation(request, token):
    """
    Public-facing evaluation form accessible via unique token
    No authentication required
    """
    try:
        activity = ProjectEvent.objects.get(evaluation_token=token, evaluation_enabled=True)
    except ProjectEvent.DoesNotExist:
        return render(request, 'projects/evaluation_not_found.html', status=404)
    
    # Check if activity is completed or ongoing (allow evaluation)
    if activity.status not in ['COMPLETED', 'ONGOING']:
        return render(request, 'projects/evaluation_not_available.html', {
            'message': 'Evaluation is not yet available for this activity.'
        })
    
    if request.method == 'POST':
        # Handle form submission
        form_data = request.POST
        
        # Create evaluation (evaluator_name is required, evaluated_by is optional)
        ActivityEvaluation.objects.create(
            activity=activity,
            evaluated_by=request.user if request.user.is_authenticated else None,
            evaluator_name=form_data.get('evaluator_name', 'Anonymous'),
            venue=activity.location or form_data.get('venue', ''),
            # ... all other evaluation fields ...
        )
        
        return render(request, 'projects/evaluation_thank_you.html', {
            'activity': activity
        })
    
    # Show evaluation form
    return render(request, 'projects/public_activity_evaluation.html', {
        'activity': activity,
        'project': activity.project
    })
```

**3. URL Configuration:**
```python
# In shared/projects/urls.py
path('evaluate/<uuid:token>/', public_activity_evaluation, name='public_activity_evaluation'),
```

**4. Generate QR Code:**
```python
# Add QR code generation utility
# In shared/projects/utils.py
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def generate_evaluation_qr_code(activity):
    """Generate QR code for activity evaluation"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(activity.get_evaluation_qr_code_data())
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    # Save to media storage
    filename = f"evaluation_qr_{activity.id}.png"
    file_path = default_storage.save(f"qr_codes/{filename}", ContentFile(buffer.getvalue()))
    return default_storage.url(file_path)
```

---

### Solution 2: Simple Public URL with Activity ID

Simpler approach using activity ID (less secure but easier).

#### Implementation:

**1. Public Evaluation View:**
```python
def public_activity_evaluation_by_id(request, project_id, activity_id):
    """
    Public evaluation form using project and activity IDs
    Only works for COMPLETED activities or with special access
    """
    activity = get_object_or_404(ProjectEvent, pk=activity_id, project_id=project_id)
    
    # Only allow evaluation for completed or ongoing activities
    if activity.status not in ['COMPLETED', 'ONGOING']:
        return render(request, 'projects/evaluation_not_available.html', status=403)
    
    # ... rest of implementation similar to Solution 1 ...
```

**2. URL:**
```python
path('projects/<int:project_id>/activities/<int:activity_id>/evaluate/', 
     public_activity_evaluation_by_id, 
     name='public_activity_evaluation'),
```

---

### Solution 3: QR Code Display in Activity Management

Add QR code display in the activity management interface for easy sharing.

#### Implementation:

**1. Add QR Code to Activity Card:**
```html
<!-- In project_events.html -->
<div class="activity-actions">
    <button onclick="showEvaluationQR({{ event.id }})">
        <i class="fa-solid fa-qrcode"></i> Get Evaluation Link
    </button>
</div>

<!-- QR Code Modal -->
<div id="qr-modal-{{ event.id }}" class="modal">
    <div class="modal-content">
        <h3>Evaluation QR Code</h3>
        <img src="{% url 'activity_evaluation_qr' project.id event.id %}" alt="QR Code">
        <p>Share this QR code with participants</p>
        <div class="evaluation-link">
            <input type="text" value="{{ event.get_evaluation_url }}" readonly>
            <button onclick="copyLink(this)">Copy Link</button>
        </div>
    </div>
</div>
```

**2. QR Code View:**
```python
def activity_evaluation_qr(request, project_id, activity_id):
    """Generate and return QR code image"""
    activity = get_object_or_404(ProjectEvent, pk=activity_id, project_id=project_id)
    
    qr_code_url = generate_evaluation_qr_code(activity)
    return redirect(qr_code_url)  # Or return image directly
```

---

## Recommended Complete Solution

### Combine Solutions 1 + 3:

1. **Unique Token System** (Solution 1) - Secure, trackable
2. **QR Code Generation** (Solution 3) - Easy distribution
3. **Public Evaluation Form** - No login required

### Features:

#### 1. Activity Evaluation Token
- Auto-generated unique UUID when activity is created
- Can be regenerated if needed
- Can be disabled per activity

#### 2. Public Evaluation Form
- Accessible via: `/evaluate/<token>/`
- Shows activity details (title, date, location)
- Matches PSU-ESO 004 form structure
- Optional evaluator name field
- No authentication required

#### 3. QR Code Generation
- Admin can view/download QR code
- QR code links directly to evaluation form
- Can be printed and displayed at event
- Can be shared digitally

#### 4. Evaluation Link Sharing
- Copy link button
- Share via email/SMS
- Embed in event materials

### User Flow:

```
1. Activity is created/updated
   ↓
2. Admin views activity → clicks "Get Evaluation Link"
   ↓
3. System shows:
   - QR Code (for printing/display)
   - Shareable link (for digital sharing)
   ↓
4. Participant scans QR code OR clicks link
   ↓
5. Public evaluation form loads (no login needed)
   ↓
6. Participant fills PSU-ESO 004 form
   ↓
7. Submission creates ActivityEvaluation
   ↓
8. Admin views tallied results
```

---

## Implementation Steps

### Phase 1: Database & Model
1. Add `evaluation_token` and `evaluation_enabled` to `ProjectEvent`
2. Create `ActivityEvaluation` model (from previous plan)
3. Run migrations

### Phase 2: Public Evaluation Form
1. Create `public_activity_evaluation` view
2. Create `public_activity_evaluation.html` template (matches PSU-ESO 004)
3. Add URL route
4. Test public access

### Phase 3: QR Code & Sharing
1. Install QR code library: `pip install qrcode[pil]`
2. Create QR code generation utility
3. Add QR code view
4. Add "Get Evaluation Link" button to activity cards
5. Create QR code modal/display

### Phase 4: Integration
1. Add evaluation link to activity management page
2. Add evaluation statistics display
3. Add export functionality
4. Test end-to-end flow

---

## Security Considerations

1. **Token Uniqueness**: UUID ensures uniqueness
2. **Token Regeneration**: Allow admins to regenerate if compromised
3. **Rate Limiting**: Prevent spam submissions (optional)
4. **Activity Status Check**: Only allow evaluation for completed/ongoing activities
5. **Optional IP Tracking**: Track evaluation submissions (for analytics)

---

## Template Structure

### `public_activity_evaluation.html`:
```html
{% extends "base_public.html" %}

{% block content %}
<div class="evaluation-container">
    <div class="activity-info">
        <h2>{{ activity.title }}</h2>
        <p><strong>Project:</strong> {{ project.title }}</p>
        <p><strong>Date:</strong> {{ activity.datetime|date:"F d, Y" }}</p>
        <p><strong>Location:</strong> {{ activity.location }}</p>
    </div>
    
    <form method="post" class="evaluation-form">
        {% csrf_token %}
        
        <!-- Evaluator Name (Optional) -->
        <div class="form-group">
            <label>Your Name (Optional)</label>
            <input type="text" name="evaluator_name" placeholder="Enter your name">
        </div>
        
        <!-- PSU-ESO 004 Form Fields -->
        <!-- Trainings/Seminars Section -->
        <!-- Timeliness Section -->
        <!-- Comments -->
        
        <button type="submit">Submit Evaluation</button>
    </form>
</div>
{% endblock %}
```

---

## Benefits

✅ **No Login Required**: Participants can evaluate without accounts  
✅ **Easy Distribution**: QR codes and shareable links  
✅ **Secure**: Unique tokens prevent unauthorized access  
✅ **Trackable**: Can see how many evaluations received  
✅ **Mobile-Friendly**: QR codes work great on mobile devices  
✅ **Offline Capable**: QR codes can be printed for offline distribution  

---

## Alternative: Participant Registration (Optional Enhancement)

If you want to track who evaluated:

```python
class ActivityParticipant(models.Model):
    """Optional: Track registered participants"""
    activity = models.ForeignKey(ProjectEvent, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    has_evaluated = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('activity', 'email')  # Prevent duplicate registrations
```

This allows:
- Pre-registration of participants
- Sending evaluation links via email
- Tracking who has/hasn't evaluated
- Reminder emails

---

## Next Steps

1. **Choose Solution**: Recommend Solution 1 (Token-based)
2. **Implement Model Changes**: Add evaluation_token to ProjectEvent
3. **Create Public Form**: Build public evaluation template
4. **Add QR Code**: Implement QR code generation
5. **Test Flow**: Test with sample participants
6. **Deploy**: Roll out to production





