# CSC Booking System — Human Tester Guide

> **Purpose:** This guide provides structured test scenarios for human QA testers
> validating the Cascade Ski Club (CSC) booking system before production launch.
> Each section includes the objective, prerequisites, step-by-step instructions,
> and expected results.

---

## Table of Contents

1. [Test Environment Setup](#1-test-environment-setup)
2. [Member Registration & Onboarding](#2-member-registration--onboarding)
3. [Member Dashboard](#3-member-dashboard)
4. [Booking Flow — Individual](#4-booking-flow--individual)
5. [Booking Flow — Family](#5-booking-flow--family)
6. [Booking Flow — With Guests](#6-booking-flow--with-guests)
7. [Payment — Wallet](#7-payment--wallet)
8. [Payment — Stripe](#8-payment--stripe)
9. [Payment — Mixed (Wallet + Stripe)](#9-payment--mixed-wallet--stripe)
10. [Booking Cancellation & Refund](#10-booking-cancellation--refund)
11. [Member Booking History & Detail](#11-member-booking-history--detail)
12. [Admin Booking Flow](#12-admin-booking-flow)
13. [Admin — Manage & Refund Bookings](#13-admin--manage--refund-bookings)
14. [Membership Subscriptions](#14-membership-subscriptions)
15. [Invoicing](#15-invoicing)
16. [Notifications](#16-notifications)
17. [Wallet Operations](#17-wallet-operations)
18. [Profile & Family Management](#18-profile--family-management)
19. [Security & Access Control](#19-security--access-control)
20. [Edge Cases & Negative Testing](#20-edge-cases--negative-testing)
21. [Mobile / Responsive Testing](#21-mobile--responsive-testing)
22. [Cross-Browser Testing](#22-cross-browser-testing)
23. [Race Conditions & Concurrency Testing](#23-race-conditions--concurrency-testing)

---

## 1. Test Environment Setup

### Objective
Ensure the test environment is correctly configured before beginning manual tests.

### Prerequisites
- Access to the staging environment at the designated URL
- Test accounts with different roles:
  - **Regular member** (with active subscription)
  - **Regular member** (without subscription)
  - **Booking administrator**
  - **Financial administrator**
  - **New/unregistered user** (valid invitation email)
- Stripe test mode enabled (use test card `4242 4242 4242 4242`)
- Test wallet with balance > $200

### Checklist
- [ ] Staging URL loads without errors
- [ ] All test accounts can log in
- [ ] Stripe test mode confirmed (dashboard shows "Test mode")
- [ ] Database has sample rooms (bunks and private rooms)
- [ ] At least one active `CancellationPolicy` exists
- [ ] Notification templates exist for: `booking_confirmed`, `booking_cancelled`, `invoice_created`
- [ ] Current fiscal year exists (Oct 1 – Sep 30)

---

## 2. Member Registration & Onboarding

### Objective
Verify the invitation-based registration flow works end to end.

### Test 2.1 — Send Invitation
1. Log in as an **admin**
2. Navigate to invitation management
3. Enter a test email address
4. Send invitation
5. **Expected:** Invitation email received with unique registration link

### Test 2.2 — Register via Invitation
1. Open the invitation link from email
2. Fill in registration form (first name, last name, password)
3. Submit
4. **Expected:** Account created, redirected to dashboard, profile created automatically

### Test 2.3 — Expired Invitation
1. Use an invitation link older than 7 days
2. **Expected:** Error message, cannot register

### Test 2.4 — Used Invitation
1. Use an invitation link that has already been redeemed
2. **Expected:** Error message, cannot register again

### Test 2.5 — Login with Email
1. Attempt login with registered email + password
2. **Expected:** Successful login, redirected to dashboard
3. Attempt login with username (not email)
4. **Expected:** Login fails

---

## 3. Member Dashboard

### Objective
Verify the member dashboard displays correct information.

### Test 3.1 — Dashboard Overview
1. Log in as regular member
2. Navigate to dashboard
3. **Expected:** See overview with booking summary, wallet balance, subscription status

### Test 3.2 — Bookings Tab
1. Click Bookings tab/section
2. **Expected:** List of past and upcoming bookings with status badges (confirmed, refunded, cancelled)

### Test 3.3 — Wallet Tab
1. Click Wallet tab/section
2. **Expected:** Current balance displayed, transaction history with credits/debits

### Test 3.4 — Profile Tab
1. Click Profile tab/section
2. **Expected:** Member information, membership type, family members (if applicable)

---

## 4. Booking Flow — Individual

### Objective
Verify a single member can check availability, book a room, and receive confirmation.

### Test 4.1 — Check Availability
1. Log in as member with active subscription
2. Navigate to "Book" or "Check Availability"
3. Select check-in date (≥ tomorrow) and check-out date (1–3 nights)
4. Submit
5. **Expected:** Available rooms listed, occupied rooms excluded, prices shown per membership type

### Test 4.2 — Add Room to Cart
1. From availability results, select a bunk room
2. Assign yourself as occupant
3. Click "Add to Cart"
4. **Expected:** Room added to cart, cart timer starts (15 minutes), page redirects back to the
   availability page. The added room card shows an **"Added to Cart"** badge to confirm it is
   reserved. Navigate to the cart to see the room listed.

### Test 4.3 — View Cart
1. Navigate to cart
2. **Expected:** Selected room(s) listed with dates, occupants, price breakdowns, total
3. Cart timer visible and counting down

### Test 4.4 — Cart Expiration
1. Add room to cart
2. Wait 15+ minutes without proceeding
3. Refresh page
4. **Expected:** Reserved room released, cart empty, room available to others

### Test 4.5 — Remove from Cart
1. Add room to cart
2. Click remove button next to the room
3. **Expected:** Room removed, cart total updated, room released for others

### Test 4.6 — Clear Cart
1. Add multiple rooms to cart
2. Click "Clear Cart"
3. **Expected:** All rooms removed, cart empty

### Test 4.7 — Availability Page Filters
1. Navigate to availability results (any date range with rooms returned)
2. Use the **"Filter by Location"** dropdown to select a specific lodge location (e.g., "Snorers",
   "Adults (18+)", "Women Only")
3. **Expected:** Room cards filtered to only show the selected location
4. Select the **"⚡ CPAP Accessible"** filter option
5. **Expected:** Only rooms marked as CPAP-accessible are shown

---

## 5. Booking Flow — Family

### Objective
Verify family members can be booked together in rooms.

### Test 5.1 — Family Member Selection
1. Log in as family primary contact
2. Check availability
3. Select room
4. Assign family members (spouse, children) as occupants
5. **Expected:** Dropdown shows all family members, children have age indicator

### Test 5.2 — Multiple Family Members in One Room
1. Select a private room
2. Assign 2+ family members as occupants
3. **Expected:** Room capacity not exceeded, all members listed

### Test 5.3 — Family Members Across Rooms
1. Add bunk room with Member A as occupant
2. Add another bunk room with Spouse B as occupant
3. **Expected:** Both rooms in cart, each with correct occupant

### Test 5.4 — Child Booking Without Adult
1. Try to book only a child without an adult occupant
2. **Expected:** Should follow family booking permission rules

---

## 6. Booking Flow — With Guests

### Objective
Verify guest (non-member) bookings work correctly.

### Test 6.1 — Add Guest to Room
1. Check availability
2. Select room
3. Choose "Guest" as occupant, enter name and age
4. **Expected:** Guest added as room occupant

### Test 6.2 — Guest with Member
1. Select room
2. Add both a member profile and a guest as occupants
3. **Expected:** Both listed in room assignment

---

## 7. Payment — Wallet

### Objective
Verify full wallet payment flow.

### Test 7.1 — Pay Entirely from Wallet
1. Ensure wallet balance ≥ booking total
2. Add room to cart, proceed to checkout
3. Enable the **"Use wallet credit?"** toggle switch; an amount input field appears — enter
   the full booking amount (or the amount you wish to apply)
4. **Expected:** Stripe card form is hidden, wallet balance covers the total; submit to
   confirm — wallet is debited, booking confirmed immediately, no Stripe charge

### Test 7.2 — Wallet Insufficient Balance
1. Ensure wallet balance < booking total
2. Proceed to checkout
3. **Expected:** Wallet option shows remaining amount, Stripe payment required for difference

---

## 8. Payment — Stripe

### Objective
Verify Stripe credit card payment flow.

### Test 8.1 — Pay via Stripe (Test Card)
1. Add room to cart, proceed to checkout
2. Choose credit card payment
3. Enter test card: `4242 4242 4242 4242`, any future expiry, any CVC
4. Submit payment
5. **Expected:** Payment processes, booking confirmed, confirmation page shown

### Test 8.2 — Stripe Card Declined
1. Proceed to checkout
2. Enter declined test card: `4000 0000 0000 0002`
3. **Expected:** Payment fails, appropriate error message, booking not confirmed

### Test 8.3 — Payment Success Notification
1. After successful Stripe payment
2. **Expected:** In-app notification received, email confirmation sent (check inbox)

---

## 9. Payment — Mixed (Wallet + Stripe)

### Objective
Verify combined wallet + Stripe payment.

### Test 9.1 — Partial Wallet + Stripe
1. Ensure wallet balance > $0 but < booking total
2. At checkout, enable the **"Use wallet credit?"** toggle; enter the partial wallet amount in
   the amount field that appears (e.g., enter your full wallet balance to apply it all)
3. Pay the remaining balance via Stripe (card form appears automatically for the remainder)
4. **Expected:** Wallet debited for the entered amount, Stripe charged for remainder,
   combined total matches booking cost

---

## 10. Booking Cancellation & Refund

### Objective
Verify cancellation policies and refund processing.

### Test 10.1 — Full Refund (> 72 Hours Before Check-in)
1. Create booking with check-in > 72 hours away
2. Navigate to booking and click "Cancel" / "Refund"
3. **Expected:** 100% refund issued, wallet credited (or Stripe refund), booking status → "refunded"

### Test 10.2 — Partial Refund (48–72 Hours Before Check-in)
1. Create booking with check-in 48–72 hours away
2. Cancel booking
3. **Expected:** 50% refund issued, remaining 50% forfeited

### Test 10.3 — No Refund (< 48 Hours Before Check-in)
1. Create booking with check-in < 48 hours away
2. Attempt cancellation
3. **Expected:** No refund, booking cancelled, rooms released

### Test 10.4 — Refund Notification
1. After any refund
2. **Expected:** Cancellation notification sent (in-app + email)

---

## 11. Member Booking History & Detail

### Objective
Verify members can view their booking history and individual booking details from the dashboard.

### Test 11.1 — Booking History List
1. Log in as a member with at least one completed booking
2. Navigate to the dashboard and open the Bookings section
3. **Expected:** All past and upcoming bookings listed with status badges
   (`confirmed`, `cancelled`, `refunded`, `partially_refunded`)

### Test 11.2 — Booking Detail View
1. From the bookings list, click on a booking
2. **Expected:** Booking detail page shows check-in/check-out dates, room(s), occupant(s),
   per-room prices, total paid, booking source, and payment method

### Test 11.3 — Multi-Period Date Display
1. Find (or create) a booking that includes rooms on **different date ranges** within the same booking
2. View the booking detail
3. **Expected:** Rather than a single misleading date range, a "Stay Periods" section lists each
   distinct date span separately (e.g., "Dec 26–28" and "Dec 30–Jan 1")

### Test 11.4 — Booking Invoice from Dashboard
1. From the booking detail page, click the invoice link or button
2. **Expected:** Invoice opens with prefix `BKG-`, correct line items, and booking details

---

## 12. Admin Booking Flow

### Objective
Verify booking administrators can book on behalf of members.

### Test 12.1 — Admin Dashboard Access
1. Log in as Booking Administrator
2. Navigate to admin booking dashboard
3. **Expected:** Admin interface loads with member search and date selection

### Test 12.2 — Search for Member
1. In admin booking, type member name or email in search
2. **Expected:** Matching members appear, selectable

### Test 12.3 — Admin Book on Behalf
1. Select member from search
2. Check availability with dates
3. Add rooms, assign occupants
4. Complete booking
5. **Expected:** Booking created with `booking_source="admin"`, 2-hour reservation window

### Test 12.4 — Free Booking (Comp)
1. As admin, create a booking and proceed to the checkout/payment step
2. Select the **"Free Booking"** radio card (always visible at the top of the payment options)
3. Confirm the booking
4. **Expected:** Free booking created with $0 charge, no payment taken, booking confirmed

### Test 12.5 — Double Booking Override
1. As admin, check availability
2. Enable "Allow Double Booking" toggle
3. Select a room that is already booked
4. **Expected:** Room appears in results despite existing booking

---

## 13. Admin — Manage & Refund Bookings

### Objective
Verify admin booking management capabilities.

### Test 13.1 — View All Bookings
1. Navigate to "Manage Bookings"
2. **Expected:** All bookings listed with status, dates, members, totals

### Test 13.2 — View Transactions
1. Navigate to "Transactions"
2. **Expected:** All payments/transactions listed with details

### Test 13.3 — Admin Refund Booking
1. Find a confirmed booking
2. Process refund
3. **Expected:** Booking refunded, wallet credited, rooms released, notification sent

### Test 13.4 — Override Room Price at Admin Checkout
1. As admin, start a new booking and add rooms
2. At the checkout step, use the price editing field next to each room to enter a custom amount
3. Confirm the booking
4. **Expected:** Booking confirmed with the overridden price; total reflects `custom price × nights`
   **Note:** Room prices can only be edited at **checkout time** before the booking is confirmed.
   Already-confirmed bookings do not have an editable price field.

### Test 13.5 — Booking Detail Modal
1. Navigate to "Manage Bookings" as admin
2. Click on any booking row
3. **Expected:** A detail modal slides open showing:
   - Booking summary (member name, dates, source, total)
   - Per-room breakdown (room name, occupant(s), price, nights)
   - Action buttons relevant to the booking status (e.g., Refund for confirmed bookings)
4. Close the modal and click a different booking
5. **Expected:** Modal updates with the newly selected booking's details

---

## 14. Membership Subscriptions

### Objective
Verify subscription lifecycle management.

### Test 14.1 — View Subscription Status
1. Log in as member
2. Check profile/dashboard for subscription status
3. **Expected:** Shows "Active" with period dates, or "No active subscription"

### Test 14.2 — Subscription Required for Booking
1. Log in as member **without** active subscription
2. Navigate to Check Availability and search for dates
3. **Expected (availability page):** A warning message appears: "None of your family profiles have
   active subscriptions. You'll need active subscriptions to complete bookings." Available rooms
   are still visible (browse-only)
4. Add a room to cart and proceed to checkout
5. **Expected (checkout):** Checkout is blocked with an error message identifying the occupant
   whose subscription has lapsed; user is redirected to the cart

### Test 14.3 — Family Subscription Coverage
1. Log in as family primary with active subscription
2. Check that family members (spouse, children) are covered
3. **Expected:** Dependents can be booked, subscription status shows coverage

---

## 15. Invoicing

### Objective
Verify invoice generation and management.

### Test 15.1 — Subscription Invoice
1. Check invoicing section (admin or member view)
2. **Expected:** Subscription invoices with prefix `SUB-`, correct amounts

### Test 15.2 — Booking Invoice
1. After booking payment, check for invoice
2. **Expected:** Booking invoice with prefix `BKG-`, line items matching booked rooms

### Test 15.3 — Invoice Status Transitions
1. View draft invoice → mark as sent → record payment → verify paid status
2. **Expected:** Status progresses: draft → sent → paid

### Test 15.4 — Void Invoice
1. Find unpaid invoice
2. Void it
3. **Expected:** Status changes to "void", no payment required

---

## 16. Notifications

### Objective
Verify notification delivery and management.

### Test 16.1 — Booking Confirmation Notification
1. Complete a booking
2. **Expected:** In-app notification appears, email sent

### Test 16.2 — Cancellation Notification
1. Cancel a booking
2. **Expected:** Cancellation notification received

### Test 16.3 — Invoice Notification
1. Have admin send an invoice
2. **Expected:** Invoice notification received by member

### Test 16.4 — Mark as Read
1. View notifications
2. Click on unread notification
3. **Expected:** Marked as read, count decremented

### Test 16.5 — Mark All as Read
1. Accumulate multiple unread notifications
2. Click "Mark all as read"
3. **Expected:** All notifications marked read

### Test 16.6 — Notification Preferences
1. Navigate to notification preferences
2. Disable email for a specific trigger
3. Trigger that notification
4. **Expected:** In-app notification created, email NOT sent

---

## 17. Wallet Operations

### Objective
Verify wallet funding, balance tracking, and transaction display.

### Test 17.1 — Fund Wallet via Stripe
1. Navigate to wallet section
2. Enter funding amount
3. Pay via Stripe test card
4. **Expected:** Wallet balance increases, transaction recorded as "credit"

### Test 17.2 — Wallet Balance After Booking
1. Note wallet balance
2. Complete wallet-paid booking
3. **Expected:** Balance reduced by booking total, "debit" transaction recorded

### Test 17.3 — Wallet Balance After Refund
1. Note wallet balance
2. Cancel a wallet-paid booking
3. **Expected:** Balance increased by refund amount, "credit" transaction with source "refund"

### Test 17.4 — Transaction History
1. View wallet transaction history
2. **Expected:** All credits and debits listed chronologically with descriptions

---

## 18. Profile & Family Management

### Objective
Verify profile editing and family member management.

### Test 18.1 — View Profile
1. Navigate to profile page
2. **Expected:** Shows name, email, membership type, family info

### Test 18.2 — Family Member Display
1. Log in as family primary
2. View family section
3. **Expected:** All family members listed (adults, children), roles shown

### Test 18.3 — Child Profile
1. View a child profile in the family
2. **Expected:** Shows child name, age, "is_child" indicator, no user account

### Test 18.4 — Guest Management
1. View/add guest entries
2. **Expected:** Guests linked to member profile, name and age tracked

---

## 19. Security & Access Control

### Objective
Verify role-based access control enforcement.

### Test 19.1 — Anonymous Access
1. Open booking URLs without logging in
2. **Expected:** All protected pages redirect to login

### Test 19.2 — Member Cannot Access Admin
1. Log in as regular member
2. Manually navigate to admin booking URLs
3. **Expected:** 403 Forbidden or redirect to login

### Test 19.3 — Cannot Access Other User's Data
1. Log in as Member A
2. Try to access Member B's booking or wallet (by manipulating URLs/IDs)
3. **Expected:** 404 or 403, cannot view or modify other member's data

### Test 19.4 — Admin Can Access All Bookings
1. Log in as Booking Administrator
2. **Expected:** Can view all members' bookings
3. Can process refunds for any booking

### Test 19.5 — CSRF Protection
1. Try to submit a POST form without CSRF token (use browser dev tools)
2. **Expected:** 403 Forbidden

### Test 19.6 — Session Timeout
1. Log in and remain idle for 24+ hours
2. Return and try to access protected page
3. **Expected:** Redirected to login (session expired)

---

## 20. Edge Cases & Negative Testing

### Objective
Test boundary conditions and error handling.

### Test 20.1 — Past Date Booking
1. Try to book with check-in date in the past
2. **Expected:** Error message, booking prevented

### Test 20.2 — Same Day Check-in/Check-out
1. Try to book with same check-in and check-out date
2. **Expected:** Error message (0 nights not allowed)

### Test 20.3 — Duplicate Occupant Prevention
1. If `SystemSettings.prevent_duplicate_occupant_bookings` is enabled
2. Try to book the same person in two rooms for overlapping dates
3. **Expected:** Error message, duplicate prevented

### Test 20.4 — Room Capacity Exceeded
1. Try to assign more occupants than room capacity
2. **Expected:** Error or warning

### Test 20.5 — Very Long Stay
1. Try to book 30+ nights
2. **Expected:** System handles correctly (or shows max stay limit)

### Test 20.6 — Concurrent Booking
1. Open two browser tabs with same availability dates
2. Reserve same room in both tabs
3. **Expected:** Second reservation fails (room taken), appropriate error

**Note:** For comprehensive concurrency testing, see [Section 23: Race Conditions & Concurrency Testing](#23-race-conditions--concurrency-testing)

### Test 20.7 — Browser Back Button During Payment
1. Start payment process
2. Hit browser back button
3. **Expected:** System handles gracefully, no double booking

### Test 20.8 — Multiple Browser Tabs
1. Open cart in two tabs
2. Add items in one, checkout in another
3. **Expected:** Consistent cart state across tabs (session-based)

### Test 20.9 — Booking Without Subscription
1. Member whose subscription just expired attempts booking
2. **Expected:** Blocked with clear message about subscription requirement

### Test 20.10 — Large Number of Bookings
1. Create 10+ bookings for different dates
2. **Expected:** Dashboard lists all, pagination works if applicable

---

## 21. Mobile / Responsive Testing

### Objective
Verify the application works on mobile devices and small screens.

### Test 21.1 — Phone Layout (375px wide)
- Check availability page: date pickers usable, room cards readable
- Cart: room details visible, remove buttons accessible
- Checkout: payment form usable, Stripe card input works
- Dashboard: tabs/navigation accessible

### Test 21.2 — Tablet Layout (768px wide)
- Same flows as phone but verify two-column layouts render correctly

### Test 21.3 — Touch Interactions
- Date picker is touch-friendly
- Buttons have sufficient tap targets (≥ 44px)
- Scroll areas work smoothly

---

## 22. Cross-Browser Testing

### Objective
Verify compatibility across major browsers.

### Browsers to Test
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest, if Mac available)
- [ ] Edge (latest)

### Per-Browser Checklist
- [ ] Login flow works
- [ ] Availability check renders correctly
- [ ] Cart operations function
- [ ] Stripe payment form loads and processes
- [ ] Notifications display
- [ ] Dashboard renders properly

---

## 23. Race Conditions & Concurrency Testing

### Objective
Verify that the Phase 5 race condition fixes work correctly under concurrent user load. These tests simulate multiple users interacting with the system simultaneously to ensure data integrity and prevent double-bookings, payment conflicts, and wallet balance issues.

### Prerequisites
- Multiple browser windows or devices (or use Chrome DevTools to simulate multiple sessions)
- Multiple test accounts ready (User A, User B, User C)
- Fresh database state before each test
- PostgreSQL database (SQLite won't enforce exclusion constraints)

### Important Notes
⚠️ **These tests require precise timing and coordination**. Use a timer/stopwatch and follow steps carefully.

---

### Test 23.1 — Double-Booking Prevention (Issue 5.1)

**Setup:**
- Room 101 available for dates Jan 1-3
- Two users (User A, User B) logged in different browser windows

**Steps:**
1. Both users navigate to availability check simultaneously
2. Both users search for the same dates (Jan 1-3)
3. Both users see Room 101 available
4. **User A adds Room 101 to cart at time T**
5. **User B adds Room 101 to cart at time T+1 second**

**Expected Result:**
- User A: Room added to cart successfully ✅
- User B: Error message "Room is no longer available — just reserved by another member" ❌
- Database: Only 1 reservation exists for Room 101

**Verification:**
- As admin, check BookedRoom records - only User A should have a reservation
- User B's cart should be empty

---

### Test 23.2 — Concurrent Cart Additions (Issue 5.1)

**Setup:**
- 5 available bunk rooms
- 3 users (User A, User B, User C) all viewing availability

**Steps:**
1. All 3 users search for the same dates
2. **Simultaneously** (within 1 second):
   - User A adds Rooms 101, 102, 103 to cart
   - User B adds Rooms 102, 103, 104 to cart
   - User C adds Rooms 103, 104, 105 to cart
3. Wait for all operations to complete (3-5 seconds)

**Expected Result:**
- Room 102: Reserved by User A only (first request wins)
- Room 103: Reserved by User A only (first request wins)
- Room 104: Reserved by User B or C (whoever got there first)
- Some users receive "Room is no longer available" messages for conflicting rooms
- No room is reserved by multiple users simultaneously

**Verification:**
```sql
-- As admin in Django shell
from bookings.models import BookedRoom
conflicts = BookedRoom.objects.filter(
    room__room_number__in=['101','102','103','104','105'],
    status='reserved'
).values('room__room_number').annotate(count=Count('id')).filter(count__gt=1)

# Should return 0 results (no duplicates)
```

---

### Test 23.3 — Payment Conflict Prevention (Issue 5.2)

**Setup:**
- User A has Room 101 in cart (reserved, expires in 15 minutes)
- User B logged in, viewing availability for same dates

**Steps:**
1. User A begins checkout process (opens payment page)
2. **While User A's checkout page is open**, use Django admin to manually expire User A's reservation:
   ```python
   # Admin Django shell
   from bookings.models import BookedRoom
   from django.utils import timezone
   res = BookedRoom.objects.get(user=userA, room__room_number='101', status='reserved')
   res.expires_at = timezone.now() - timedelta(minutes=1)
   res.save()
   ```
3. User B immediately adds Room 101 to cart (should succeed - room is now expired)
4. User A submits payment form (tries to pay for the now-unavailable room)

**Expected Result:**
- User A payment fails with error: "One or more rooms have already been booked. Please return to your cart."
- User B successfully reserves Room 101
- No double charge occurs
- User A's cart is empty after returning to cart view

---

### Test 23.4 — Cart Expiration During Checkout (Issue 5.4)

**Setup:**
- User A has 2 rooms in cart
- Cart expires in 30 seconds

**Steps:**
1. User A opens checkout page with 30 seconds left on timer
2. User A fills out payment form slowly (take 45+ seconds)
3. Meanwhile, User B is viewing availability page and refreshes at T+35 seconds
4. User A submits payment at T+50 seconds

**Expected Result:**
- At T+30s: Expiration cleanup marks User A's cart as expired
- At T+35s: User B sees rooms as available
- At T+50s: User A's payment fails with "Your cart is empty" or "Rooms no longer available"
- No payment is charged
- Cleanup process with `skip_locked` doesn't interfere with User B's queries

---

### Test 23.5 — Wallet Concurrent Debit Prevention (Issue 5.3)

**Setup:**
- User A has wallet balance of $100
- User A opens 2 browser windows (Window 1, Window 2)

**Steps:**
1. Window 1: Create booking for $80, proceed to checkout, select "Use wallet credit" for $80
2. Window 2: Create booking for $80, proceed to checkout, select "Use wallet credit" for $80
3. **Simultaneously** submit both payment forms (click both submit buttons within 1 second)

**Expected Result:**
- One payment succeeds, wallet balance becomes $20
- Other payment fails with "Insufficient wallet funds"
- **Wallet balance never goes negative** (database constraint prevents this)

**Verification:**
```python
# Check wallet balance
from wallet.models import Wallet
wallet = Wallet.objects.get(user=userA)
assert wallet.balance >= 0  # Should never be negative
```

---

### Test 23.6 — Stripe Webhook Race with Booking Creation

**Setup:**
- User creates booking and pays via Stripe
- Simulate slow booking creation process

**Steps:**
1. User completes checkout with Stripe payment
2. Stripe payment succeeds immediately
3. **While booking creation is still processing** (first few seconds), Stripe webhook fires
4. Webhook tries to confirm booking before it's fully created

**Expected Result:**
- No errors occur
- Booking is confirmed exactly once
- No duplicate payments
- Invoice is created after booking confirmation

**Note:** This is difficult to test manually. Verify via monitoring logs during load testing or check that `handle_successful_payment` in `stripe_webhook_utils.py` has proper atomic transactions.

---

### Test 23.7 — Multiple Tabs Same User Cart

**Setup:**
- User A logged in two browser tabs (Tab 1, Tab 2)

**Steps:**
1. Tab 1: Add Room 101 to cart
2. Tab 2: Refresh and verify Room 101 appears in cart
3. Tab 1: Add Room 102 to cart
4. Tab 2: Remove Room 101 from cart
5. Tab 1: Proceed to checkout

**Expected Result:**
- Cart state synchronized across tabs (session-based)
- Only Room 102 proceeds to checkout
- No race condition between tabs' cart operations

---

### Test 23.8 — Load Test: 5 Users, 3 Rooms

**Setup:**
- 3 available rooms (101, 102, 103)
- 5 users (A, B, C, D, E) all logged in

**Steps:**
1. All 5 users navigate to availability check
2. All 5 users see the 3 available rooms
3. **Countdown: 3, 2, 1, GO**
4. All 5 users click "Add to Cart" on Room 101 simultaneously
5. Count how many get "Added successfully" vs "No longer available"

**Expected Result:**
- Exactly 1 user successfully adds Room 101 to cart
- Other 4 users receive "Room is no longer available" error
- Database has exactly 1 BookedRoom record for Room 101

**Repeat for Rooms 102 and 103:**
- After Room 101 test, have remaining 4 users try Room 102
- After Room 102 test, have remaining 3 users try Room 103
- Final state: 3 users have rooms, 2 users have empty carts

---

### Test 23.9 — Expired Reservation During Add-to-Cart

**Setup:**
- User A has Room 101 in cart, expires in 5 seconds
- User B viewing availability

**Steps:**
1. T=0s: User A adds Room 101 to cart (15 min reservation starts)
2. Use admin to set expiration to T+5s:
   ```python
   res.expires_at = timezone.now() + timedelta(seconds=5)
   res.save()
   ```
3. T=3s: User B tries to add Room 101 to cart (should fail - still reserved)
4. T=7s: User B tries to add Room 101 to cart again (should succeed - expired)

**Expected Result:**
- T=3s: User B gets "Room is no longer available"
- T=7s: User B successfully adds Room 101 to cart
- User A's cart shows expired when they next view it

---

### Test 23.10 — Back Button During Payment

**Setup:**
- User has Room 101 in cart, proceeds to checkout

**Steps:**
1. User fills out payment form (Stripe card details)
2. User clicks "Submit Payment"
3. Payment processing starts (2-5 seconds)
4. **While processing spinner shows**, user clicks browser Back button
5. User sees cart again, clicks "Proceed to Checkout" again
6. User submits payment a second time

**Expected Result:**
- First payment processes successfully
- Booking confirmed from first payment
- Second payment attempt fails with "Your cart is empty" or "Booking already completed"
- No double-charge occurs
- Only one booking exists

---

### Test 23.11 — Validation Helper Function Deprecation

**Technical Test (Developer/QA only)**

**Steps:**
1. Open Django shell: `python manage.py shell`
2. Import the old function:
   ```python
   from bookings.views_collection.utils import validate_cart_availability
   from abs.booking_cart import BookingCartData
   from django.contrib.auth import get_user_model
   import warnings
   
   User = get_user_model()
   user = User.objects.first()
   cart = BookingCartData()
   
   # Should raise DeprecationWarning
   with warnings.catch_warnings(record=True) as w:
       warnings.simplefilter("always")
       result = validate_cart_availability(cart, date.today(), date.today()+timedelta(days=3), user)
       print(f"Warnings caught: {len(w)}")
       if w:
           print(f"Warning message: {w[0].message}")
   ```

**Expected Result:**
- DeprecationWarning is raised
- Warning message mentions function is deprecated
- Recommends using `validate_cart_availability_with_lock` instead

---

### Performance Benchmarks (Optional)

Use browser DevTools Network tab to measure:

**Metric** | **Target** | **Notes**
-----------|------------|----------
Add to Cart (with conflict check) | < 500ms | Should be fast even with locking
Cart View (page load) | < 300ms | Includes expiration cleanup
Checkout Page Load | < 600ms | Includes conflict checks
Payment Submit → Confirmation | < 3s | Includes Stripe API + webhook

---

### Automated Test Verification

After manual testing, verify automated tests pass:

```bash
# Run all race condition tests
pytest tests/test_race_conditions.py -v

# Run slow load tests (10 concurrent users)
pytest tests/test_race_conditions.py -v --run-slow

# Run with database logging to see lock behavior
pytest tests/test_race_conditions.py -v --log-cli-level=DEBUG
```

**Expected:**
- All tests pass ✅
- No IntegrityError exceptions (or properly handled)
- No negative wallet balances
- No duplicate bookings in database

---

## Bug Reporting Template

When filing a bug, include:

```
**Title:** [Brief description]
**Severity:** Critical / Major / Minor / Cosmetic
**Test Case:** [Reference number, e.g., Test 4.2]
**Environment:** [Browser, OS, screen size]
**Steps to Reproduce:**
1. ...
2. ...
3. ...
**Expected Result:** ...
**Actual Result:** ...
**Screenshot/Video:** [Attach if applicable]
**Account Used:** [test account email, no passwords]
```

---

