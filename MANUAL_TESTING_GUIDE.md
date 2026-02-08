# Manual Testing Guide for New Features

This guide provides step-by-step instructions for manually testing the newly implemented features.

## Feature 1: Purchase Items Management

### Test Case 1.1: Edit Purchase Item
**Objective:** Verify that purchase items can be edited

**Steps:**
1. Navigate to Invoices page
2. Select a purchase with items
3. Click on the "Edit" button for any item
4. Modify the following fields:
   - Description
   - SKU
   - Quantity (observe automatic total price calculation)
   - Unit Price (observe automatic total price calculation)
5. Click "Save Changes"

**Expected Results:**
- Modal should open with pre-filled item data
- Total price should recalculate automatically when quantity or unit price changes
- Item should be updated successfully with a success toast message
- Purchase details page should refresh and show the updated item

**API Endpoint Tested:** `PUT /api/v1/purchases/{purchase_id}/items/{item_id}`

---

### Test Case 1.2: Create New Material from Purchase Item
**Objective:** Verify that new materials can be created from purchase items

**Steps:**
1. Navigate to Invoices page
2. Select a purchase with unlinked items (items without material_id)
3. Click "Add to Stock" for an unlinked item
4. In the modal, click "Create New Material"
5. Fill in the material creation form:
   - Name (pre-filled from item description)
   - SKU (required, unique)
   - Description
   - Category (dropdown: panel, inverter, battery, cable, mounting, other)
   - Unit (default: "buc")
   - Unit Price (pre-filled from item)
   - Minimum Stock
6. Click "Create and Add to Stock"

**Expected Results:**
- Material creation modal should open with pre-filled data from the item
- After successful creation:
  - Success toast: "Material created and item added to stock!"
  - The item should now show as "In Stock" with a green badge
  - The new material should appear in the Materials list
  - Stock movement should be created
  - Initial stock quantity should equal the purchase item quantity

**API Endpoint Tested:** `POST /api/v1/purchases/{purchase_id}/items/{item_id}/create-material`

**Edge Cases to Test:**
- Try creating a material with an existing SKU (should fail with error)
- Enter invalid numeric values (should default to 0)

---

### Test Case 1.3: Link Existing Material to Purchase Item
**Objective:** Verify that purchase items can be linked to existing materials

**Steps:**
1. Navigate to Invoices page
2. Select a purchase with unlinked items
3. Click "Add to Stock" for an unlinked item
4. Select an existing material from the dropdown
5. Click "Add to Stock"

**Expected Results:**
- Modal should show a dropdown with all available materials
- After selection:
  - Success toast: "Item added to stock successfully!"
  - The item should show as "In Stock"
  - Stock movement should be created
  - The linked material name should appear under the item description

**API Endpoint Tested:** `POST /api/v1/purchases/{purchase_id}/items/{item_id}/add-to-stock`

---

## Feature 2: Project Cost Breakdown

### Test Case 2.1: Create Project with Cost Breakdown
**Objective:** Verify that new projects can be created with detailed cost breakdown

**Steps:**
1. Navigate to Projects page
2. Click "Add Project" or "Create Project"
3. Fill in basic project information:
   - Project Name
   - Client Name
   - Client Contact
   - Location
   - Capacity (kW)
   - Status
   - Start Date
   - End Date
4. Fill in cost fields:
   - Estimated Cost (RON)
   - Actual Cost (RON)
5. Fill in Cost Breakdown section:
   - Labor Cost - Estimated (RON)
   - Labor Cost - Actual (RON)
   - Transport Cost - Estimated (RON)
   - Transport Cost - Actual (RON)
   - Other Costs - Estimated (RON)
   - Other Costs - Actual (RON)
6. Click "Save" or "Create Project"

**Expected Results:**
- Form should display all new cost breakdown fields
- Project should be created successfully
- All cost values should be saved and retrievable

**API Endpoint Tested:** `POST /api/v1/projects/`

---

### Test Case 2.2: Edit Existing Project Costs
**Objective:** Verify that project cost breakdown can be updated

**Steps:**
1. Navigate to Projects page
2. Select an existing project
3. Click "Edit" or "Edit Project"
4. Modify cost breakdown fields:
   - Update labor costs
   - Update transport costs
   - Update other costs
5. Save the changes

**Expected Results:**
- Form should show existing cost values
- All cost fields should be editable
- Updated values should be saved successfully
- Project details should reflect the new cost values

**API Endpoint Tested:** `PUT /api/v1/projects/{project_id}`

---

### Test Case 2.3: View Project with Cost Breakdown
**Objective:** Verify that project costs are displayed correctly

**Steps:**
1. Navigate to Projects page
2. View a project with cost breakdown data
3. Check the project details view

**Expected Results:**
- All cost breakdown fields should be visible
- Cost values should be displayed correctly
- The display should differentiate between estimated and actual costs for each category

**API Endpoint Tested:** `GET /api/v1/projects/{project_id}`

---

## Database Schema Changes

The following fields were added to the `project` table:
- `labor_cost_estimated` (FLOAT, nullable)
- `labor_cost_actual` (FLOAT, nullable)
- `transport_cost_estimated` (FLOAT, nullable)
- `transport_cost_actual` (FLOAT, nullable)
- `other_costs_estimated` (FLOAT, nullable)
- `other_costs_actual` (FLOAT, nullable)

**To apply schema changes:**
```bash
cd backend
python3 init_db.py
```

The SQLModel ORM will automatically add the new columns to existing databases.

---

## Validation Tests

### Input Validation
1. **Numeric Fields:** Try entering non-numeric values (should default to 0 or show validation error)
2. **Required Fields:** Leave required fields empty (should show validation error)
3. **SKU Uniqueness:** Try creating a material with an existing SKU (should fail)

### Error Handling
1. **Network Errors:** Simulate network failures (should show error toast)
2. **Invalid IDs:** Try accessing non-existent purchase/item/project IDs (should show 404 error)
3. **Server Errors:** Any server errors should be caught and displayed to the user

---

## Regression Tests

Verify that existing functionality still works:
1. ✅ Creating purchases with items
2. ✅ Viewing purchase details
3. ✅ Creating materials through Materials page
4. ✅ Creating and editing projects
5. ✅ Adding materials to projects
6. ✅ Stock movements

---

## Notes for Testers

- All cost fields are optional (nullable)
- Total price calculations in purchase item editing are automatic
- Material SKUs must be unique across the system
- When creating a material from a purchase item, the initial stock quantity equals the purchase quantity
- Cost breakdown fields maintain backward compatibility with existing projects (old projects will have NULL values)
