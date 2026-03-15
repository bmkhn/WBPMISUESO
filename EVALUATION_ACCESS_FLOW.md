# Activity Evaluation Access Flow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTIVITY CREATION                            │
│  Admin creates/updates activity (ProjectEvent)                  │
│  System auto-generates: evaluation_token (UUID)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ADMIN ACCESSES EVALUATION LINK                    │
│  Admin goes to: Project → Activities → [Activity]              │
│  Clicks: "Get Evaluation Link" or "View QR Code"                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              EVALUATION LINK OPTIONS                            │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │   QR CODE        │  │  SHAREABLE LINK  │                   │
│  │   [QR Image]     │  │  /evaluate/abc123│                   │
│  │                  │  │  [Copy Button]   │                   │
│  └──────────────────┘  └──────────────────┘                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────────┐          ┌──────────────────┐
│  PRINT QR CODE   │          │  SHARE DIGITALLY  │
│  Display at event│          │  Email/SMS/Post   │
└──────────────────┘          └──────────────────┘
        │                                  │
        └──────────────┬───────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              PARTICIPANT ACCESSES EVALUATION                    │
│  Option 1: Scans QR code with phone                            │
│  Option 2: Clicks shared link                                   │
│  Option 3: Types URL manually                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PUBLIC EVALUATION FORM LOADS                      │
│  • No login required                                            │
│  • Shows activity details (title, date, location)              │
│  • Displays PSU-ESO 004 form structure                         │
│  • Optional name field                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PARTICIPANT FILLS EVALUATION                       │
│  • Trainings/Seminars section (7 criteria)                     │
│  • Timeliness section (2 criteria)                             │
│  • Comments (optional)                                         │
│  • Clicks "Submit"                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              EVALUATION SAVED                                  │
│  ActivityEvaluation record created:                            │
│  • Linked to activity via token                                │
│  • All ratings stored                                          │
│  • Timestamp recorded                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              THANK YOU PAGE                                    │
│  "Thank you for your evaluation!"                               │
│  Participant can close browser                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ADMIN VIEWS TALLIED RESULTS                       │
│  Project → Activities → [Activity] → Evaluations               │
│  • See all evaluations                                         │
│  • View aggregated statistics                                  │
│  • Export data                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Access Methods Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **QR Code** | ✅ No typing needed<br>✅ Fast access<br>✅ Works offline (printed) | ❌ Requires smartphone<br>❌ Needs QR scanner app | In-person events |
| **Shareable Link** | ✅ Works on any device<br>✅ Can be shared via email/SMS | ❌ Requires typing/copying | Digital distribution |
| **Activity ID URL** | ✅ Simple to remember<br>✅ Easy to communicate | ❌ Less secure<br>❌ Predictable | Internal use only |

## Recommended: Hybrid Approach

**Use BOTH QR Code + Shareable Link:**
- QR Code for in-person events (display at venue)
- Shareable link for email/SMS distribution
- Both use the same token system

## Example URLs

### Token-based (Recommended):
```
https://yourdomain.com/evaluate/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

### Activity ID-based (Simpler):
```
https://yourdomain.com/projects/123/activities/456/evaluate/
```

## Security Features

1. **Unique Token**: Each activity gets unique UUID
2. **Token Regeneration**: Admin can regenerate if needed
3. **Status Check**: Only COMPLETED/ONGOING activities can be evaluated
4. **Enable/Disable**: Admin can disable evaluation per activity
5. **Optional Rate Limiting**: Prevent spam (can add later)

## Mobile Optimization

The public evaluation form should be:
- ✅ Responsive (works on phone/tablet)
- ✅ Touch-friendly (large buttons)
- ✅ Fast loading
- ✅ Works offline (if using service worker)
- ✅ Accessible (screen reader friendly)

## Analytics Tracking (Optional)

Track evaluation access:
- How many times link was accessed
- How many evaluations submitted
- Average time to complete
- Device type (mobile/desktop)
- Geographic location (if needed)





