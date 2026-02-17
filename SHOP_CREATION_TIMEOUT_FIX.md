# Shop Creation Timeout Fix - Implementation Guide

## Overview
This solution improves the shop creation flow to handle long-running schema setup operations gracefully. Instead of timing out after 60 seconds, the system now:

1. **Immediately returns** shop creation response (~1-2 seconds)
2. **Queues async setup** via Celery (schema creation and migrations)
3. **Redirects user** to admin page with status notification
4. **Polls status** until shop is ready for use
5. **Shows appropriate messages** throughout the process

## What Changed

### Backend Changes

#### 1. Shop Model (`tenancy/models.py`)
Added `setup_status` field with three states:
- `'pending'` - Schema setup in progress
- `'ready'` - Shop fully configured and ready to use
- `'failed'` - Setup encountered an error

```python
setup_status = models.CharField(
    max_length=20,
    choices=SETUP_STATUS_CHOICES,
    default='pending',
    help_text="Status of shop schema setup"
)
```

#### 2. Celery Task (`tenancy/tasks.py`) - NEW FILE
Created async task `setup_shop_schema_async` that:
- Handles schema creation asynchronously
- Updates shop status to 'ready' on success
- Updates shop status to 'failed' on error
- Retries up to 3 times with exponential backoff

```python
@shared_task(bind=True, max_retries=3)
def setup_shop_schema_async(self, shop_id):
    # Creates schema and updates shop status
    # Non-blocking - returns immediately
```

#### 3. Signal Handler (`tenancy/signals.py`)
Modified `setup_shop_schema` signal to:
- Queue the Celery task INSTEAD of blocking on schema setup
- Return immediately (allows API response within ~1 second)

**Before:** Signal blocked for 60+ seconds during schema creation
**After:** Signal queues task in ~100ms

#### 4. Serializer (`tenancy/serializers.py`)
Updated `ShopSerializer` to:
- Include `setup_status` field in response
- Mark it as read-only (server-managed)

#### 5. ViewSet (`tenancy/views.py`)
Added custom action `check_setup_status`:
- Endpoint: `GET /api/v1/shops/{id}/check_setup_status/`
- Returns current setup status and status message
- Frontend uses this for polling

#### 6. Database Migration
Created migration `0010_shop_setup_status.py`:
- Adds the `setup_status` field to Shop table
- Applies automatically when you run `migrate`

### Frontend Changes

#### 1. AddShopModal Component (`frontend/components/AddShopModal.tsx`)
Enhanced to:
- **Handle timeout gracefully** - Catches timeout errors and redirects instead of showing error
- **Show setup progress** - Displays spinner and message while setup is in progress
- **Redirect to admin** - Redirects to admin page with shop info
- **Add router integration** - Uses Next.js router to redirect with status

Key improvements:
- Timeout no longer blocks the UI
- User sees immediate feedback (spinner for setup progress)
- System redirects to admin page automatically

#### 2. ShopsListPanel Component (`frontend/components/ShopsListPanel.tsx`)
Major enhancements:

**Status Display:**
- Shows setup status for each shop: "Ready", "Setting up...", or "Failed"
- Visual indicators with icons (✓, ⏳, ⚠️)
- Color-coded badges (green, blue, red)

**Automatic Polling:**
- Polls every 3 seconds for pending shops
- Checks if shop is ready via `check_setup_status` endpoint
- Automatically refreshes shop list when ready

**Query Parameter Handling:**
- Reads `shopCreated`, `shopCreating`, and `shopName` from URL
- Shows temporary notification confirming creation
- Auto-dismisses after 5-8 seconds

**Smart Actions:**
- Disables Edit button for pending/failed shops
- Uses appropriate tooltips to explain why actions are disabled
- Soft failure handling for polling errors (continues polling)

## How It Works - User Flow

### Step 1: Create Shop
```
User clicks "Create Shop" → Modal shows creation form
User fills form and clicks "Create Shop"
```

### Step 2: Quick Response
```
Frontend sends POST request to /api/v1/shops/
Backend creates Shop record IMMEDIATELY (1-2 seconds)
Backend queues Celery task for schema setup
Backend returns response with setup_status='pending'
```

### Step 3: Redirect & Notify
```
AddShopModal catches successful response
Shows spinner with "Setting up..." message
Redirects to admin page after 500ms
Passes shop info via URL parameters
```

### Step 4: Polling & Status
```
ShopsListPanel receives URL parameters
Shows notification: "Shop 'Downtown Store' created! Setting up schema..."
Automatically polls /api/v1/shops/{id}/check_setup_status/ every 3 seconds
Shops table shows status: "Setting up..." (blue badge with spinner)
```

### Step 5: Ready!
```
Celery task completes schema creation and migrations
Task updates shop.setup_status = 'ready'
Next polling request sees ready status
ShopsListPanel shows: "Shop is ready for use!"
Table badge changes to green "Ready"
Edit button becomes enabled
Notification auto-dismisses
```

## Testing

### Test 1: Normal Shop Creation
```
1. Click "Add Shop" in Admin Panel
2. Fill in shop name: "Test Store"
3. Click "Create Shop"
4. Modal shows spinner with "Setting up..." message
5. Page redirects to admin with blue notification
6. Watch the shops table - status shows "Setting up..." with spinner
7. After 10-30 seconds, status changes to green "Ready"
8. Edit button becomes enabled
9. Notification auto-dismisses
```

### Test 2: Admin Page Refresh During Setup
```
1. Create a shop
2. Immediately refresh the page (Ctrl+R)
3. ShopsListPanel still shows correct setup status
4. Polling resumes automatically
5. Status updates when ready
```

### Test 3: Browser Close/Reopen
```
1. Create a shop
2. Close browser tab
3. Open admin page again after 30 seconds
4. Shops list shows correct status (either still pending or ready)
5. If pending, polling resumes
```

### Test 4: Failed Setup (Optional - Force Error)
```
If you want to simulate a failure:
1. Stop the Celery worker
2. Create a new shop
3. Wait for 3 retries (about 45 seconds)
4. Status changes to red badge "Failed"
5. Edit button remains disabled
6. Try deleting and recreating
```

## Configuration

### Celery Settings
The system uses the existing Celery configuration in `core/settings.py`:
```python
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
```

**Required:** Celery worker must be running:
```bash
# In backend/core directory
python manage.py celery -A core worker -l info
```

### Polling Intervals
To change polling frequency, edit `ShopsListPanel.tsx`:
```javascript
const interval = setInterval(pollShopStatus, 3000);  // Change 3000 to milliseconds you want
```

### Timeout Handling
The API endpoint timeout is configured in `lib/api.ts`:
```typescript
timeout: 60000, // 60 seconds - this no longer times out on shop creation
```

Shop creation now responds in ~1-2 seconds, so this timeout is not reached.

## Monitoring

### Check Celery Tasks
```bash
# In Redis CLI or terminal
redis-cli
> KEYS celery*  # See all tasks
> LLEN celery   # See task queue length
```

### Check Logs
Backend logs will show:
```
[CELERY] Starting async shop schema setup for shop_id=1
[CELERY] Tenant connection registered for TenantName
[CELERY] Schema creation completed for schema_name
[CELERY] ✅ Shop is now ready: Shop Name
```

Frontend console (DevTools) will show:
```
Polling shop status for shop_id: 1
Shop setup_status: pending
Shop setup_status: ready
```

## Troubleshooting

### Issue: Shop shows "Setting up..." forever
**Solution:**
1. Check Celery worker is running: `python manage.py celery -A core worker -l info`
2. Check logs for `setup_shop_schema_async` errors
3. Verify Redis is running: `redis-cli ping` should return "PONG"
4. Check shop status directly: `curl http://localhost:8000/api/v1/shops/1/check_setup_status/`

### Issue: Shop creation times out
**Solution:**
This shouldn't happen anymore, but if it does:
1. The frontend should catch timeout and redirect
2. Shop may still be created in background
3. Check admin page - shop might be there with "Setting up..." status
4. Wait and refresh to see final status

### Issue: Polling isn't working
**Solution:**
1. Check browser console (F12 → Console tab)
2. Verify shop ID is being passed correctly in URL parameters
3. Check that API endpoint `/api/v1/shops/{id}/check_setup_status/` is accessible
4. Ensure authentication token is valid

### Issue: "Max retries exceeded"
**Solution:**
1. Check error logs for the actual schema creation error
2. May indicate database connectivity issue
3. Verify database credentials in Django settings
4. Check disk space for new schema creation

## Benefits

✅ **User Experience:**
- No more 60-second timeout frustration
- Clear visual feedback during setup
- Automatic refresh when ready
- Can continue browsing while setup happens

✅ **System Reliability:**
- Async processing prevents request timeout
- Retry logic handles transient failures
- Status tracking for monitoring
- Graceful error handling

✅ **Operations:**
- Background work doesn't block user
- Real-time status updates
- Easy to monitor shop setup progress
- Can identify failed setups immediately

## Files Modified/Created

**Created:**
- `backend/core/tenancy/tasks.py` - Celery tasks
- `backend/core/tenancy/migrations/0010_shop_setup_status.py` - Database migration

**Modified:**
- `backend/core/tenancy/models.py` - Added setup_status field
- `backend/core/tenancy/signals.py` - Queue task instead of blocking
- `backend/core/tenancy/serializers.py` - Include setup_status in response
- `backend/core/tenancy/views.py` - Added check_setup_status endpoint
- `frontend/components/AddShopModal.tsx` - Timeout handling and redirect
- `frontend/components/ShopsListPanel.tsx` - Status display and polling

## Next Steps (Optional Enhancements)

1. **Email notification** - Notify admin when shop is ready
2. **WebSocket polling** - Real-time updates instead of interval polling
3. **Progress percentage** - Show schema creation progress (50%, 75%, etc.)
4. **Automatic retry** - Auto-retry failed setups after delay
5. **Setup logs** - Show detailed logs of what's being set up
6. **Batch creation** - Allow creating multiple shops at once

## Support

For issues or questions:
1. Check the logs in backend/core console
2. Open browser DevTools (F12) to see frontend errors
3. Verify Celery worker is running: `python manage.py celery -A core worker`
4. Check Redis is running: `redis-cli ping`
5. Review this guide's Troubleshooting section
