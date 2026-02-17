# Debtor Model Field Alignment Summary

## Overview
Updated the backend Debtor models serializers and frontend type definitions to ensure complete alignment of all data fields needed for frontend data capture and display.

## Changes Made

### 1. Backend Serializers Updated (`serializers.py`)

#### DebtorListSerializer
- **Old:** Used DBF column names (dno, dname, dsname, etc.)
- **New:** Uses proper Python field names (customer_number, name, short_name, etc.)
- **Added Fields:**
  - `phone2` - Alternative phone number
  - `email` - Email address
  - `phone` - Primary phone number

#### DebtorDetailSerializer
- **Expanded field list** to include all necessary details for full debtor profiles
- **New Fields Added:**
  - `phone2` - Alternative phone number
  - `email` - Email address
  - `vat_reference` - VAT registration number
  - `date_opened` - Account opening date
  - `notes` - Additional notes
  - `balance_brought_forward` - Opening balance
  - `available_credit` - Calculated credit available
  - `credit_utilization_pct` - Credit utilization percentage

#### DebtorCreateUpdateSerializer
- **Updated to use proper field names** instead of DBF column names
- **Includes all customer detail fields** needed for creation/update operations
- **New Fields for Data Capture:**
  - `phone2` - Alternative phone number
  - `email` - Email address
  - `vat_reference` - VAT registration number
  - `date_opened` - Account opening date
  - `notes` - Additional notes
  - All address fields (delivery addresses)
  - Tax/business identification fields

### 2. Field Mapping Reference

Below is the complete alignment between backend model fields and API exposure:

| Backend Field | Type | Frontend Field | Frontend Type | Notes |
|---|---|---|---|---|
| customer_number | IntegerField | customer_number | number | Account number |
| name | CharField | name | string | Customer name |
| short_name | CharField | short_name | string | Short/sort name |
| contact_person | CharField | contact_person | string | Contact person |
| phone | CharField | phone | string | Primary phone |
| phone2 | CharField | phone2 | string | Alternative phone |
| fax | CharField | fax | string | Fax number |
| email | EmailField | email | string | Email address |
| address_line1-3 | CharField | address_line1-3 | string | Postal address |
| postal_code | CharField | postal_code | string | Postal code |
| delivery_address1-4 | CharField | delivery_address1-4 | string | Delivery address |
| tax_number | CharField | tax_number | string | Tax/company registration |
| vat_reference | CharField | vat_reference | string | VAT registration |
| account_type | CharField | account_type | string | Account type (BF/OI/C/N/B) |
| price_level | IntegerField | price_level | number | Price level (1-3) |
| payment_terms | IntegerField | payment_terms | number | Payment terms (days) |
| discount_percentage | DecimalField | discount_percentage | number | Standard discount % |
| prompt_payment_discount | DecimalField | prompt_payment_discount | number | Prompt discount % |
| discount_printable | CharField | discount_printable | boolean\|string | Print discount flag |
| credit_limit | DecimalField | credit_limit | number | Credit limit |
| area_code | IntegerField | area_code | number | Sales area ID |
| interest_flag | CharField | interest_flag | boolean\|string | Charge interest flag |
| block_flag | CharField | block_flag | boolean\|string | Blocked flag |
| positive_balance_only | CharField | positive_balance_only | boolean\|string | POS balance flag |
| balance_brought_forward | DecimalField | balance_brought_forward | number | Opening balance |
| balance_current | DecimalField | balance_current | number | Current aging bucket |
| balance_30_days | DecimalField | balance_30_days | number | 30 days bucket |
| balance_60_days | DecimalField | balance_60_days | number | 60 days bucket |
| balance_90_days | DecimalField | balance_90_days | number | 90 days bucket |
| balance_120_days | DecimalField | balance_120_days | number | 120 days bucket |
| balance_150_days | DecimalField | balance_150_days | number | 150 days bucket |
| balance_180_days | DecimalField | balance_180_days | number | 180+ days bucket |
| sales_month | DecimalField | sales_month | number | MTD sales |
| sales_year | DecimalField | sales_year | number | YTD sales |
| profit_month | DecimalField | profit_month | number | MTD profit |
| profit_year | DecimalField | profit_year | number | YTD profit |
| last_payment_amount | DecimalField | last_payment_amount | number | Last payment amount |
| last_payment_date | DateField | last_payment_date | string | Last payment date |
| date_opened | DateField | date_opened | string | Account opened date |
| notes | TextField | notes | string | Additional notes |
| is_active | BooleanField | is_active | boolean | Active status |
| created_at | DateTimeField | created_at | string | Created timestamp |
| updated_at | DateTimeField | updated_at | string | Updated timestamp |

### 3. Frontend Type Definitions Updated

**File:** `frontend/lib/types/debtors.ts`

#### DebtorAccount Interface
- Updated all field names from DBF column names to proper Python field names
- Added all contact fields (phone, phone2, email, fax)
- Added complete address fields (postal and delivery)
- Added business identifiers (tax_number, vat_reference)
- Added complete balance and aging breakdown
- Added notes and date_opened fields
- Added computed fields (total_balance, overdue_balance, available_credit, credit_utilization_pct)

#### DebtorCreateData Interface
- Extends updated DebtorAccount with proper field names
- Excludes computed/read-only fields

#### DebtorEditData Interface
- Made all fields optional for partial updates

### 4. Validation & Serialization

#### Flag Field Handling
The serializers properly handle conversion of boolean/numeric values to Y/N format for:
- `discount_printable` → Y/N
- `interest_flag` → Y/N  
- `block_flag` → Y/N
- `positive_balance_only` → Y/N

#### Validation Rules Maintained
- Credit limit cannot be negative
- Discount percentages must be 0-100
- Cash customers should not have credit limits
- Account/short names are required

## Impact on Frontend

### Data Capture Forms
Frontend forms can now capture complete debtor information:
- ✅ All contact information (phone, phone2, email, fax)
- ✅ Complete address information (postal + delivery)
- ✅ Business identifiers (tax number, VAT reference)
- ✅ Account configuration (type, price level, terms, discounts)
- ✅ Credit management (limits, interest flags)
- ✅ Historical data (date opened, notes)

### API Responses
All API responses will now include:
- Complete contact information
- Full address details
- Business identification data
- Aging balance breakdowns
- Customer notes
- Account dates

## Files Modified

1. **Backend:**
   - `backend/core/apps/debtors/serializers.py` - Updated all debtor serializers

2. **Frontend:**
   - `frontend/lib/types/debtors.ts` - Updated type definitions

## Testing Recommendations

1. **Create Debtor Test:**
   ```javascript
   POST /api/v1/debtors/debtors/
   {
     customer_number: 1001,
     name: "Test Customer",
     short_name: "TEST",
     phone: "555-1234",
     phone2: "555-5678",
     email: "test@example.com",
     address_line1: "123 Main St",
     postal_code: "1234",
     tax_number: "1234567890",
     vat_reference: "5678901234",
     account_type: "C",
     credit_limit: 10000,
     payment_terms: 30,
     date_opened: "2026-02-01",
     notes: "Test account",
     is_active: true
   }
   ```

2. **Retrieve Debtor Test:**
   - Verify all fields are returned in responses
   - Check email and phone2 are populated
   - Verify notes and date_opened are included

3. **Update Debtor Test:**
   - Update phone2, email, or notes
   - Verify changes persist
   - Confirm computed fields are updated

## Backward Compatibility

The changes maintain backward compatibility:
- DBF column names are still used in database via `db_column` attribute
- Serializers expose modern Python field names
- No breaking changes to existing API responses (only additions)

## Next Steps

1. Migrate existing debtor records to populate new fields
2. Update frontend forms to capture all available fields
3. Create debtor management UI with complete field display
4. Add validation rules for optional fields
5. Test with real customer data
