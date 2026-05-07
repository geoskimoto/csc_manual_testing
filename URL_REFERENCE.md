# CSC Booking System — URL Reference

All URL patterns. Prefix each with its app mount path from `csc_booking_system/urls.py`.

---

## Root / System

| URL | Name | Notes |
|-----|------|-------|
| `/admin/` | — | Django admin site |
| `/favicon.ico` | — | Redirects to static favicon |
| `/ckeditor5/` | — | CKEditor5 file uploads |

---

## lodge — mounted at `/`

| URL | Name |
|-----|------|
| `/` | `lodge:index` |
| `/rates/` | `lodge:rates` |
| `/membership-rates/` | `lodge:membership-rates` |
| `/faq/` | `lodge:faq` |
| `/contact-us/` | `lodge:contact_us` |
| `/lodge-rules/` | `lodge:lodge-rules` |
| `/report-maintenance/` | `lodge:report-maintenance` |
| `/about-the-club/` | `lodge:about_the_club` |

---

## userauths — mounted at `/user/`

| URL | Name |
|-----|------|
| `/user/sign-up/` | `userauths:sign-up` |
| `/user/sign-in/` | `userauths:sign-in` |
| `/user/sign-out/` | `userauths:sign-out` |
| `/user/membership_application/` | `userauths:membership_application` |
| `/user/send-invite/` | `userauths:send_invite_admin` |
| `/user/register/<uuid:token>/` | `userauths:register_with_invite` |
| `/user/register-family/<uuid:token>/` | `userauths:register_with_invite_family` |
| `/user/password-reset/` | `userauths:password_reset` |
| `/user/password-reset/done/` | `userauths:password_reset_done` |
| `/user/reset/<uidb64>/<token>/` | `userauths:password_reset_confirm` |
| `/user/reset/done/` | `userauths:password_reset_complete` |

---

## bookings — mounted at `/bookings/`

| URL | Name |
|-----|------|
| `/bookings/check_availability/` | `bookings:check_availability` |
| `/bookings/check_availability/partial/` | `bookings:check_availability_partial` |
| `/bookings/add_accommodations_to_cart/` | `bookings:add_accommodations_to_cart` |
| `/bookings/remove-cart-item/` | `bookings:remove_accomodation_from_cart` |
| `/bookings/clear-cart/` | `bookings:clear_cart` |
| `/bookings/clear-booking-results/` | `bookings:clear_booking_results` |
| `/bookings/view_booking_cart/` | `bookings:view_booking_cart` |
| `/bookings/checkout/` | `bookings:checkout` |
| `/bookings/create-payment-intent/` | `bookings:create_payment_intent` |
| `/bookings/stripe-webhook/` | `bookings:stripe_webhook` |
| `/bookings/booking-status/` | `bookings:booking_status` |
| `/bookings/payment-success/` | `bookings:payment_success` |
| `/bookings/payment-processing/` | `bookings:payment_processing` |
| `/bookings/booking-failed/` | `bookings:booking_failed` |
| `/bookings/refund-booking/<str:booking_id>` | `bookings:refund_booking` |
| `/bookings/payment/wallet/` | `bookings:wallet_payment` |
| `/bookings/payment/wallet-success/` | `bookings:wallet_full_payment_view` |
| `/bookings/admin/stuck-payment-dashboard/` | `bookings:stuck_payment_dashboard` |
| `/bookings/populate_family_members/<str:user_id>/` | `bookings:populate_family_members` |

---

## booking_admin — mounted at `/admin-bookings/`

| URL | Name |
|-----|------|
| `/admin-bookings/` | `booking_admin:admin_booking_dashboard` |
| `/admin-bookings/manage-bookings/` | `booking_admin:admin_manage_bookings` |
| `/admin-bookings/booking-detail/<str:booking_id>/` | `booking_admin:admin_booking_detail` |
| `/admin-bookings/check-availability/` | `booking_admin:admin_check_availability` |
| `/admin-bookings/add-accommodations-to-cart/` | `booking_admin:admin_add_accommodations_to_cart` |
| `/admin-bookings/booking-cart/` | `booking_admin:admin_booking_cart` |
| `/admin-bookings/checkout/` | `booking_admin:admin_checkout` |
| `/admin-bookings/process-payment/` | `booking_admin:admin_process_payment` |
| `/admin-bookings/booking-success/<str:booking_id>/` | `booking_admin:admin_booking_success` |
| `/admin-bookings/search-members/` | `booking_admin:search_members_api` |
| `/admin-bookings/remove-from-cart/<int:item_index>/` | `booking_admin:admin_remove_from_cart` |
| `/admin-bookings/clear-cart/` | `booking_admin:admin_clear_cart` |
| `/admin-bookings/update-cart-item/<int:item_index>/` | `booking_admin:admin_update_cart_item` |
| `/admin-bookings/transactions/` | `booking_admin:admin_transactions` |
| `/admin-bookings/refund-booking/<str:booking_id>/` | `booking_admin:admin_refund_booking` |
| `/admin-bookings/api/booking-wallets/<str:booking_id>/` | `booking_admin:get_booking_wallets` |
| `/admin-bookings/api/update-pricing/` | `booking_admin:update_pricing_ajax` |
| `/admin-bookings/api/update-room-price/` | `booking_admin:update_room_price` |
| `/admin-bookings/api/create-payment-intent/` | `booking_admin:admin_create_payment_intent` |
| `/admin-bookings/api/confirm-payment/` | `booking_admin:admin_confirm_payment` |

---

## financials — mounted at `/financials/`

| URL | Name |
|-----|------|
| `/financials/` | `financials:financial_dashboard` |
| `/financials/export/` | `financials:export_financial_data` |
| `/financials/api/monthly-comparison/` | `financials:monthly_comparison_api` |

---

## user_dashboard — mounted at `/dashboard/`

| URL | Name |
|-----|------|
| `/dashboard/` | `user_dashboard:dashboard` |
| `/dashboard/booking_detail/<booking_id>/` | `user_dashboard:booking_detail` |
| `/dashboard/invoice/<str:booking_id>/` | `user_dashboard:booking_invoice` |
| `/dashboard/bookings/` | `user_dashboard:bookings` |
| `/dashboard/bed-list-calendar/` | `user_dashboard:bed_list_calendar` |
| `/dashboard/bookings-by-date/` | `user_dashboard:get_bookings_by_date` |
| `/dashboard/profile/` | `user_dashboard:profile` |
| `/dashboard/profiles/` | `user_dashboard:profiles` |
| `/dashboard/profile/<int:profile_id>/edit/` | `user_dashboard:edit_profile` |
| `/dashboard/profile/old/` | `user_dashboard:profile_old` |
| `/dashboard/change-password/` | `user_dashboard:change_password` |
| `/dashboard/password-changed/` | `user_dashboard:password_changed` |
| `/dashboard/wallet/` | `user_dashboard:wallet` |

---

## wallet — mounted at `/wallet/`

| URL | Name |
|-----|------|
| `/wallet/add-funds/` | `wallet:add-funds` |

---

## membership_subscriptions — mounted at `/subscriptions/`

| URL | Name |
|-----|------|
| `/subscriptions/` | `membership_subscriptions:dashboard` |
| `/subscriptions/toggle-auto-renew/<int:subscription_id>/` | `membership_subscriptions:toggle_auto_renew` |
| `/subscriptions/admin/list/` | `membership_subscriptions:admin_list` |
| `/subscriptions/admin/assign/` | `membership_subscriptions:admin_assign` |
| `/subscriptions/admin/create/` | `membership_subscriptions:admin_create` |
| `/subscriptions/admin/profile/<int:profile_id>/json/` | `membership_subscriptions:get_profile_json` |
| `/subscriptions/admin/subscription/<int:subscription_id>/details/` | `membership_subscriptions:get_subscription_details` |
| `/subscriptions/admin/subscription/<int:subscription_id>/refund/` | `membership_subscriptions:admin_cancel_refund` |
| `/subscriptions/admin/subscription/<int:subscription_id>/wallets/` | `membership_subscriptions:get_subscription_wallets` |
| `/subscriptions/admin/subscription/<int:subscription_id>/invoice/` | `membership_subscriptions:get_subscription_invoice` |
| `/subscriptions/admin/subscription/<int:subscription_id>/resend-invoice/` | `membership_subscriptions:resend_invoice` |
| `/subscriptions/admin/subscription/<int:subscription_id>/cancel-invoice/` | `membership_subscriptions:cancel_invoice` |
| `/subscriptions/admin/profiles/subscription-status/` | `membership_subscriptions:get_profiles_subscription_status` |
| `/subscriptions/invoice/<int:invoice_id>/pay/` | `membership_subscriptions:invoice_payment` |
| `/subscriptions/invoice/<int:invoice_id>/process/` | `membership_subscriptions:process_invoice_payment` |
| `/subscriptions/webhooks/stripe/` | `membership_subscriptions:stripe_webhook` |

---

## notifications — mounted at `/notifications/`

| URL | Name |
|-----|------|
| `/notifications/` | `notifications:list` |
| `/notifications/<int:notification_id>/read/` | `notifications:mark_read` |
| `/notifications/<int:notification_id>/dismiss/` | `notifications:dismiss` |
| `/notifications/mark-all-read/` | `notifications:mark_all_read` |

---

## invoicing (billing) — mounted at `/billing/`

| URL | Name |
|-----|------|
| `/billing/webhooks/stripe/` | `invoicing:stripe_webhook` |
| `/billing/invoices/<int:invoice_id>/` | `invoicing:invoice_detail` |
| `/billing/invoices/<int:invoice_id>/pay/` | `invoicing:invoice_payment` |
| `/billing/invoices/<int:invoice_id>/process-payment/` | `invoicing:process_payment` |
| `/billing/invoices/<int:invoice_id>/payment-success/` | `invoicing:invoice_payment_success` |
| `/billing/invoices/<int:invoice_id>/payment-cancel/` | `invoicing:invoice_payment_cancel` |
| `/billing/my-invoices/` | `invoicing:my_invoices` |
| `/billing/admin/invoices/` | `invoicing:admin_invoice_list` |
| `/billing/admin/invoices/create/` | `invoicing:admin_create_invoice` |
| `/billing/admin-tool/` | `invoicing:admin_dashboard` |
| `/billing/admin-tool/create/` | `invoicing:admin_create` |
| `/billing/admin-tool/<int:pk>/` | `invoicing:admin_detail` |
| `/billing/admin-tool/<int:pk>/edit/` | `invoicing:admin_edit` |
| `/billing/admin-tool/<int:pk>/send/` | `invoicing:admin_send` |
| `/billing/admin-tool/<int:pk>/void/` | `invoicing:admin_void` |
| `/billing/admin-tool/<int:pk>/payment/` | `invoicing:admin_payment` |
| `/billing/admin-tool/<int:pk>/refund/` | `invoicing:admin_refund_payment` |
| `/billing/admin-tool/<int:pk>/pdf/` | `invoicing:admin_pdf` |
| `/billing/admin-tool/batch/send/` | `invoicing:admin_batch_send` |
| `/billing/admin-tool/reports/` | `invoicing:admin_reports` |
