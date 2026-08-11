# Accpick Xcellence (ApX) - Full User Manual

Compiled from the Word-exported help pages in `help/*.htm`. Original source: 'ApX Manual', Independent Systems, dated 2006-2012.

---



# 1. Point of Sale


## [11.htm]

1.
Invoice

Invoice Options:

8
Processing an Invoice

8
Invoice Information and Price
Adjustment Options

8
Cash Debtors

Processing an Invoice

(a) Select

,

(b) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view and select from the current
Debtor listing.

(c) Confirm the Debtor’s details by clicking [Yes Correct].

Note: View Account Balance displays the selected Debtor’s aged and
total outstanding balance, the standard terms, date and amount last paid and contact
details.

(d) The Invoice Header Details will be displayed. The system will prompt
for Date, Delivery Details, Order
Number, Customer Reference or Job Card Number, Area / Salesmen Number as
per the prompts selected in the System Parameter Setup. Enter the requested
details or alternatively press enter to accept the default details.

(e) The Online Invoice Entry and Print Screen will be displayed.

(f) Click on

to insert line details.

Note: A series of prompts will be displayed
in accordance with the Prompts, Tenders and Point of Sale Setups in System
Parameter Setup.

(g) At the Stock Code prompt, enter the stock code or alternatively, press
[Enter] and at the Description prompt, press the [Page Down] key to view and
select from the Stock Listing which is displayed in description order.

to toggle the stock search order by Stock
Code, Supplier Code or Stock Description.

(h) At the Quantity prompt, enter the number of units sold.

Note: Pressing [Page Up] at the Quantity
prompt will display last purchase details.

Note: Pressing [Page Down] at the Quantity
prompt will display Quantity on Hand as well as Selling Price level 1, 2, 3.

(i) At the Selling Price prompt, Accpick will automatically display the
Selling Price. Press [Enter] to accept
the default Selling Price or enter an adjusted price. Where a maximum discount
has been set in Stock Maintenance for a specific item this may not be exceeded.

Note: Where a stock item is sold below cost,
a warning is sounded and displayed.

(j) At the Discount % prompt, enter the discount percentage amount.
Where a maximum discount has been set in Stock Maintenance for a specific item
this may not be exceeded.

(k) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  Where the System Parameter options have been
set to the Tax Code Status, the Tax Code can be overwritten.  Press [Enter] to accept the default tax
status.

(l) The Total Inclusive Value for that stock item is displayed.

(m) To enter further line items select

.

To
capture a Non-Stock item, with the facility of
allocating to the correct department with the correct Gross Profit:

to select the required department, capture the
Cost Price, Markup % and edit/amend the Selling Price.

Note: Department Name may be overwritten for
Invoice Details.

Invoice
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

to insert comment details on the Invoice. (A “no
value” entry)

(n) When all the line items
have been entered, click on

to update the Invoice.

(o) At the Update Options prompt, enter Yes.

(p) At the Vat Number prompt, enter/confirm the Debtor’s Vat number.

(q) At the Print Options prompt, select the required print options.
Where the Debtor’s Masterfile has been set to Yes to print account balance
after this transaction, this will print on the invoice.

(r) Click on

to return to the Point of Sale Menu.

Invoice Information and Price Adjustments.

Gross Profit

Pressing the left arrow [ß] before updating the Invoice displays the Gross Profit in Rand and
% Value per line item. Repeating this procedure returns to normal display.

Note: There is NO prompt for this on the
screen; facility maybe password protected.

Sub Total Discount/Selling Price/ Gross
Profit/Header Details

At the Update Transaction prompt, substitute
the Y with S/P/G/H

Subtotal Discount Facility:

At the Update Transaction
prompt, press S to display the Subtotal
Discount prompt. Enter the Discount
% which will automatically be applied to all the line items on the invoice.  A minus (-) discount will automatically increase
the unit price of all line items.

Set Selling Price Facility

At the Update Transaction prompt, press P to display the Set Selling
Price prompt. Enter the
revised inclusive Total Amount of the Invoice. The system automatically adjusts
the prices of individual items in proportion to the new total price.

This facility
maybe password controlled

Display Gross
Profit Facility:

At the Update Transaction
prompt, press G to display the Transaction Gross
Profit. This facility
displays the gross profit value and gross profit percentage for the total invoice

Header Adjustments Facility

At the Update Transaction
prompt, press H to re-display Invoice Header details. This facility
returns to the invoice header with options to amend Delivery Details, Order Number,
Customer Reference/Job Card Number and Salesman details.

Cash Debtors

Note: Where the Debtor’s Account Category is set to C in
Debtor’s – File Maintenance and their payment terms are set to 0 (zero), the
invoice transaction will end with a Tender Routine, as in a Cash Sale.  An invoice plus a payment will be posted to
the Cash Debtor’s Account.

---

## [12.htm]

2.
Receipts on Account

Receipt on Account Options:

8
Processing a Receipt on
Account for a Balance Brought Forward Debtor

8
Processing a Receipt on
Account for an Open Item Debtor

8
Capturing Post Dated Cheques

Receipts from Balance Brought Forward Debtors

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view and select from the current
Debtor listing. The Debtor’s details will be displayed.

(b) At the Account Options prompt, confirm the Debtor’s details by
clicking on [Yes Correct]

(c) At the Date prompt, enter the date or press [Enter] to accept the
default date.

(d) At the Payment Allocation Screen, enter the amount due. Press [Enter].

(e) At the Amount Tendered prompt, enter the actual amount received.
Press [Enter].

(f) Accpick will automatically calculate the settlement discount amount.
This is the difference between the amount due and the amount tendered. Press [Enter] to accept this amount.

(g) Accpick will then automatically calculate the settlement discount
percentage. Press [Enter] to accept
the percentage.

(h) At the Additional Reference prompt, enter payment information of not
more than 20 characters. e.g. EFT, Cheque payment information or June Invoice /
July Invoice. This information will print on the Transaction Report. When the
System Parameter is set to Print Order Number on Statement, the Additional
Reference will print as a reference against the receipt.

(i) Allocate the payment to the correct ageing periods.

(j) At the Ok to Update prompt, click on

.

The Tender Routine will be activated
displaying the amount owing.

(k) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details –
Drawer’s Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint Payments: Process all Speedpoint payments by entering the value
at the Speedpoint prompt.

(l) At the Vat number prompt, enter/confirm the customer’s vat number.

(m) At the Print Options prompt, select the required print options.

(n) Click on

to return to the Point of Sale Menu.

Receipts from Open Item Debtors

(a)
At the Account Number prompt,
enter the Debtor’s account number or alternatively use the search facility to
view and select from the current Debtor listing. The Debtor’s details will be
displayed.

(b) At the Account Options prompt, confirm the Debtor’s details by
clicking on [Yes Correct]

(c) At the Open Item Receipt prompt, the amount due will automatically
be displayed. Enter the Date and Amount Paid and press [Enter].

(d) To allocate the payment, use the

,

[á] and
[â] arrows keys to move each of the transactions to be paid /
allocated to the top of the transaction listing.

(e) When the selected transaction is at the top of the listing, click

to allocate the payment against the
transaction.

(f) At the Amount Paid prompt, enter the amount paid. Press [Enter].

(g) At the Settlement Discount prompt, enter the Settlement Discount
Amount, if any, and press [Enter].

Note: Full Payment [*] vs Part Payment:

If
the Balance due is being paid in FULL: Note that
after you have entered the amount paid and the settlement discount amount, a
* is displayed alongside the entry indicating that this has been settled in
full. This entry will cease to appear in subsequent payment allocations
leaving only the unallocated entries in the allocation screen.

If only part of the Balance due is
being paid: Enter the value of the part payment being paid in the Amount
Paid field, press enter through the Settlement Discount field. (No Settlement
Discount on part payments).  Note, no *
appears alongside the entry and the balance outstanding on the entry will reappear
in subsequent allocation screens.

Note: Settlement Discount:

Where settlement discount is taken, we
suggest that the invoice with the greatest value be allocated last, and that
the total value of the settlement discount be allocated to this invoice.

(h) When completed and allocated amount is equal to the amount paid and
the balance for allocation is equal to NIL, click on

.

(i) At the Allocate Payment prompt, click on

.

the Tender Routine will be activated
displaying the amount owing.

(j) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details – Drawer’s
Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

(k) At the Print Options prompt, select the required print options.

(l) Click on

to return to the Point of Sale Menu.

Unallocated Receipts on Open Item Debtors

What is an Unallocated Receipt?

An unallocated receipt is a payment from
a debtor which has no transaction entry to which the receipt can be allocated
e.g.

8
deposit for an item not yet
invoiced

8
a payment received which is
NOT to be apportioned to any of the unallocated entries.

(a)
At the date request, press
[Page Up] key to display the “Unallocated – Open Item Receipt” screen.

(b) At the Unallocated - Open Item Receipt prompt, enter the Date and amount
paid.

(c) At the Post as Unallocated Payment prompt, click on

.

The Tender Routine will be activated
displaying the amount owing.

(d) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding information
box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details –
Drawer’s Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

(e) At the Print Options prompt, select the required print options.

(f) Click on

to return to the Point of Sale Menu.

Processing a Post Dated Cheque (PDC’s)

The PDC facility is for information purposes
only. i.e. PDC’s are NOT automatically credited to the bank or the debtor’s
account on due date.

PDC’s for tomorrow will print on today’s
final Day End report as a reminder to process as a normal receipt. They are
then automatically cleared from the PDC file.

To
process PDC for information purposes:

(a)
At the Account Number prompt,
enter the Debtor’s account number or alternatively use the search facility to
view and select from the current Debtor listing. The Debtor’s details will be
displayed.

(b) Confirm the Debtor’s details by clicking [Yes Correct].

(c) At the Date prompt, press the [Page
Down] key.

(d) At the prompts, enter the cheque date and amount.

(e) At the Confirmation prompt, click on [Yes].

To View and Print Post Dated Cheque
Listing:

8
1.

,

,

5. Post Dated
Cheque Listing.

8
2.

,

,

7. Post Dated
Cheque Listing.

8
3.

,

,

1. Individual
Account Enquiry,

Select P
to view Post Dated Cheques.

8
4.

B. Age Analysis

2. Monthly   Enter Y to include any Post                                                   Dated Cheques.

To Cancel a Post Dated Cheque:

8
1.

,

,

5. Cancel/Remove
PDC.

---

## [13.htm]

3.
Credit Note

Credit Note Options:

8
Processing a Credit Note from
an Original Invoice

8
Processing a Credit Note NOT
from Original Invoice

Processing a Credit Note from an Original
Invoice

(a) Select

,

(b) At the Credit Note from an Original Invoice prompt, click on

.

(c) At the Date of Invoice prompt, enter the invoice date.

(d) At the Invoice Number prompt, enter the invoice number.

(e) At the Account number prompt, enter the Debtor‘s account number or
use the Search facility.

The On-Line Credit from Original Invoice screen
will be displayed.

(f) At the Date prompt, enter the Credit Note date.

(g) The system will prompt for the Reason for the Return/Credit Note
being issued. The original Invoice Number and the Date on which it was processed
is displayed.

(h) Enter the requested details or alternatively press enter to accept
the default details.

The line item details of the original
invoice will be displayed.

(i) Edit the line items as required in order to generate the Credit note.

(j) Use the

and

arrow keys to move the required line items to
the top of the listing.

Use

and

to make correcting adjustments to the Credit
Note.

to locate a specific stock code captured on
the Invoice.

to display sub total details.

to insert comment details to appear on the Credit
Note.

Note: The Credit Note must reflect only the items and values to be
credited!

Note: No adjustments allowed on Credit Notes
to Open Item accounts.

(k) When the Credit Note is correct, click on

to update the Credit Note.

(l) At the Update Options prompt, enter Yes.

(m) At the Ageing prompt, age the Credit Note accordingly.

(n) At the Vat number prompt, enter/confirm the Customer’s Vat number.

(o) At the Print Options prompt, select the required print options.

(p) Click on

to return to the Point of Sale Menu.

Processing a Credit Note NOT from Original
Invoice

(a)
At the Credit Note from an
Original Invoice prompt, click on

.

(b)
At the Account Number prompt,
enter the Debtor’s account number or alternatively use the search facility to
view and select from the current Debtor listing. The Debtor’s details will be
displayed.

(c) Confirm the Debtor’s details by clicking [Yes Correct].

The On-Line Credit Note Entry and Print
screen will be displayed.

(d) At the Date prompt, enter the Credit Note date.

(e) The system will prompt for the Reason for the Return. Enter the
reason for the credit and the invoice number to which the credit refers.

(f) Enter the Customer’s Name, Address and Telephone Number, Order
Number, Job Card Number, Area / Salesmen Number. Enter the requested details or
alternatively press enter to accept the default details.

(g) Click on

to insert transaction details.

(h) Use

and

to make correcting adjustments to the Credit
Note.

to display sub total details.

to insert comment details to appear on the
Credit Note.

(i) When the Credit Note is complete, click on

to update the Credit Note.

(j) At the Update Options prompt, enter Yes.

(k) At the Ageing prompt, age the Credit Note accordingly.

(l) At the Vat number prompt, enter/confirm the Customer’s Vat number.

(m) At the Print Options prompt, select the required print options.

(n) Click on

to return to the Point of Sale Menu.

---

## [14.htm]

4.
Cash Sale

Cash Sale Options:

8
Processing a Cash Sale Invoice

8
Cash Sale Information and Price Adjustment
Options

8
Tender Routine

Processing a Cash Sale Invoice

(a) Select

,

(b) At the On-line Cash Sale entry screen the system will prompt for Date, Delivery Details, Order Number, Job
Card Number, Area / Salesmen Number as per the prompts selected in the
System Parameter Setup. Enter the requested details or alternatively press
enter to accept the default details.

(c) The Online Cash Sale Entry will be displayed.

(d) Click on

to insert line details.

Note: A series of prompts will be displayed
in accordance with the Prompts, Tenders and Point of Sale Setups in System
Parameter Setup.

(e) At the Stock Code prompt, enter the stock code or alternatively
press [Enter] and at the Description prompt, press the [Page Down] key to view
and select from the Stock Listing which is displayed in description order.

to toggle the stock search order by Stock
Code, Supplier Code or Stock Description.

(f) At the Quantity prompt, enter the number of units sold.

Note: Pressing [Page Up] at the Quantity
prompt will display last purchase details.

Note: Pressing [Page Down] at the Quantity
prompt will display Quantity on Hand as well as Selling Price level 1, 2, 3.

(g) At the Selling Price prompt, Accpick will automatically display the
Selling Price. Press [Enter] to
accept the default Selling Price or enter an adjusted price. Where a maximum
discount has been set in Stock Maintenance for a specific item this may not be
exceeded.

Note: Where a stock item is sold below cost,
a warning is sounded and displayed.

(h) At the Discount % prompt, enter the discount percentage amount.
Where a maximum discount has been set in Stock Maintenance for a specific item
this may not be exceeded.

(i) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  Where the System Parameter options have been
set to the Tax Code Status, the Tax Code can be overwritten.  Press [Enter] to accept the default tax
status.

(j) The Total Inclusive Value for the stock item is displayed.

(k) To enter further line items select

.

To
capture a Non-Stock item, with the facility of
allocating to the correct department with the correct Gross Profit:

to select the required department, capture the
Cost Price, Markup % and edit/amend the Selling Price.

Note: Department Name may be overwritten for
Invoice Details.

Cash Sale Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Cash Sale and automatically move it to the top of the listing.

and

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

to insert comment details on the Invoice. (A
“no value” entry)

(l) When all the line items
have been entered, click on

to update the Cash Sale Invoice.

(m) At the Update Options prompt, enter Yes.

At this point the Tender Routine will be
displayed. (See further)

Cash Sale
Information and Price Adjustments.

Gross Profit

Pressing the left arrow [ß] before updating the Cash Sale displays the Gross Profit in Rand and % Value per line item. Repeating this procedure
returns to normal display.

Note: There is NO prompt for this on the
screen; facility maybe password protected.

Sub Total Discount/Selling Price/ Gross
Profit/Header Details

At the Update Transaction prompt, substitute
the Y with S/P/G/H

Subtotal Discount Facility:

At the Update Transaction
prompt, press S to display the Subtotal
Discount prompt. Enter the
Discount % which will automatically be applied to all the line items on the
invoice.  A minus (-) discount will
automatically increase the unit price of all line items.

Set Selling Price Facility

At the Update Transaction prompt, press P to display the Set Selling
Price prompt. Enter the
revised inclusive Total Amount of the Invoice. The system automatically adjusts
the prices of individual items in proportion to the new total price.

This facility
maybe password controlled

Display Gross
Profit Facility:

At the Update Transaction
prompt, press G to display the Transaction Gross
Profit. This facility
displays the gross profit value and gross profit percentage for the invoice

Header Adjustments Facility

At the Update Transaction
prompt, press H to re-display Invoice Header details. This facility
returns to the invoice header with the option to amend Delivery Details, Order Number,
Customer Reference/Job Card Number and Salesman details.

Tender Routine

After the Cash Sale has been updated, the
Tender Routine will be activated displaying the amount owing.

(n) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details –
Drawer’s Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

(o) At the Vat number prompt, enter/confirm the customer’s vat number.

(p) At the Print Options prompt, select the required print options.

(q) Click on

to return to the Point of Sale Menu.

Note: To return to the body of the Cash Sale once the Tender
Routine Box is displayed, press [Page Up].

Note: To convert a Cash Sale
into and Account Sale,
press [Page Down] at the Tender Routine.

---

## [15.htm]

5.
Cash Return

Cash Return Options:

8
Processing a Cash Return from
an Original Cash Sale

8
Processing a Cash Return NOT
from an Original Invoice

Processing a Cash Return from an Original Cash Sale

(a) Select

,

.

(b) At the Cash Return from an Original Cash Sale prompt, click on

.

(c) At the Date of Cash Sale prompt, enter the Cash Sale date.

(d) At the Cash Sale Number prompt, enter the original Cash Sale number.

The Cash Return from Original Cash Sale
screen will be displayed.

(e) At the Date prompt, enter the Cash Return date.

(f) Under the Reason for the Return prompt, the system will display the
original Cash Sale details as a reference for the Cash Return. Edit these
details if necessary.

The Transaction details of the original Cash
Sale will be displayed.

(g) Use the

and

arrow keys to move the required line items to
the top of the listing.

Use

and

to make correcting adjustments to the Cash
Return.

Note: The Cash Return must only display the
items and values accepted for return.

to locate a specific stock code captured.

to display sub total details.

to insert comment details on the Cash Return.

(h) When the Cash Return details are correct, click on

to update the Cash Return.

(i) At the Update Options prompt, enter Yes.

(j) At the Tender prompt, enter the Tender Type and Amount.

(k) At the Vat Number prompt, enter/confirm the Customer’s Vat number.

(l) At the Print Options prompt, select the required print options.

Processing a Cash Return NOT from an
Original Cash Sale

(a)
At the Credit Note from an Original
Invoice prompt, click on

.

The On-Line Cash Return Entry screen will be
displayed.

(b) At the Date prompt, enter the Cash Return date.

(c) The system will prompt for the Reason for the Return. Enter the
reason for the return and the cash sale number to which the return refers.

(d) Enter the Customer’s Name, Address and Telephone Number, Order
Number, Job Card Number, Area / Salesmen Number as requested.

(e) Click on

to insert transaction details.

(f) Use

and

to make correcting adjustments to the Cash
Return.

to display sub total details.

to insert any comment details on the Cash
Return.

(g) When the Cash Return is complete, click on

(h) At the Update Options prompt, enter Yes.

(i) At the Tender prompt, enter the Tender Type and Amount.

(j) At the Vat number prompt, enter the Customer’s Vat number.

(k) At the Print Options prompt, select the required print options.

---

## [16.htm]

6.
Transaction Query

Transaction Query Options:

8
Reprint a Transaction

8
Search for a Transaction

Reprint a Transaction

(a) Select Reprint from the
Options Menu.

(b) Select Current or Archived month from the listing.

(c) At the Date prompt, enter the date of the transaction.

(d) All POS transaction for the selected date will be displayed: Account
number, Transaction Number, Time, Transaction Details and Total Amount.

(e) Use the

and

keys to move the transaction to be printed to
the top of the listing or, click on

to locate a transaction to be printed by
Account Number or Transaction Number thereby positioning it at the top of the
screen.

(f) Click on

to display a detailed breakdown of the
selected transaction.

(g) Click on

to reprint the transaction. The reprint will
display the word COPY.

Search for a Transaction

Search by: First Delivery Line Details

(a)
Select option to find First
Occurrence or to List All.

(b) At the Delivery Details prompt, enter the details that where
captured on the first line of the delivery address.

(c) Accpick searches the archives and displays the transaction listing
for the specific delivery details requested.

(d) Use the

and

keys to move the transaction to be printed to
the top of the listing.

(e) Click on

to display a detailed breakdown of the
selected transaction.

(f) Click on

to reprint the transaction. The reprint will
display the word COPY.

Search by: Transaction Number

(g) At the Transaction Number prompt, enter the transaction number.

(h) Accpick searches the archives and displays the transaction listing
for the requested transaction number.

(i) Use the

and

keys to move the transaction to be printed to
the top of the listing.

(j) Click on

to display a detailed breakdown of the
selected transaction.

(k) Click on

to reprint the transaction. The reprint will
display the word COPY on it.

Note: The facility to reprint a transaction
is also available by selecting:

J. Reprint Transaction

---

## [17.htm]

7.
Cash Control

Cash Control Options:

8
Cashier Station Enquiry

8
Hourly Analysis

8
Detailed Enquiry

8
Print Report

8
Payout Details

Cashier Station Enquiry.

(a) Select

,

(b) At the Cashier Station enquiry prompt, enter the Cashier Number.

Note: Leave blank to view Control Total for
ALL cashiers.

(c) The following information is displayed:

Transactions
Details:

The number and total value of all
transactions is displayed for Cash Sales, Cash Refunds, Account Invoices,
Account Credits, Receipts and Settlement Discounts, New Laybyes, Cancelled
Laybyes, Laybye Receipts, Lay-bye Refunds, Completed Laybyes and Payouts.

Takings
Details:

Refund
Details:

Hourly Analysis

Hourly Analysis displays the sales movement
on a 24 hour basis.

Detailed Enquiry

Detailed enquiry displays transaction
number, transaction type, date, account name/cash sale, net value, profit and
GP% per transaction.

to view display by Date and Time/Transaction
Number/Value.

for detailed breakdown of a selected
transaction.

to print report for selected
Transaction/Range, Detailed or Totals Only..

Report / Print

Prints Cash Control Report.

Payout Details:

Payout Details
will only be displayed if Payouts have been processed.

---

## [18.htm]

8. Laybye Control

Laybye Options:

8
Transactions         New Laybye Entry

Modify Existing Laybye

Cancel a Laybye

Receive Laybye Payment

8
Enquiry/Reports  Specific Laybye Status

Laybye Listing

Transactions

Stock on Laybye

8
Utilities                  Index Laybye files

1. Transactions

1. New Laybye Entry

(a)
At the Date prompt, confirm/amend the date.
Press [Enter].

(b)
At the prompts, enter the Customer’s Name,
Address, Contact details, Sales Person number and any Comments regarding the laybye.

(c)
Click on  to insert line details.

Note: A series of prompts will be displayed
in accordance with the Prompts, Tenders and Point of Sale Setups in System
Parameter Setup.

(d)
At the Stock Code prompt, enter the stock code
or alternatively press [Enter] at the Description prompt to view and select
from the Stock Listing which is displayed in description order.

to toggle the stock search order by
Stock Code, Supplier Code or Stock Description.

(e)
At the Quantity prompt, enter the number of
units sold.

Note: Pressing [Page Up] at the Quantity
prompt will display last purchase details.

Note: Pressing [Page Down] at the Quantity
prompt will display Quantity on Hand as well as Selling Price level 1, 2, 3.

(f)
At the Selling Price prompt, Accpick will
automatically display the Selling Price. Press [Enter] to accept the
default Selling Price or enter an adjusted price. Where a maximum discount has
been set in Stock Maintenance for a specific item this may not be exceeded.

Note: Where a stock item is sold below cost,
a warning is sounded and displayed.

(g)
At the Discount % prompt, enter the discount
percentage amount. Where a maximum discount has been set in Stock Maintenance
for a specific item this may not be exceeded.

(h)
The Total Inclusive Value for the stock item is
displayed.

(i)
To enter further line items select .

(j)
When complete, click on  to update the Laybye. The Total Value of
the Laybye transaction will be displayed.

(k)
At the Update prompt, select [Yes]

(l)
The Laybye Details screen will be displayed showing
the Total Amount due. The Expiry date defaults to 3 months from laybye date and
the deposit to &#8531; of the Total Due; amend if required.

(m)
At the Tender Routine, enter the Tender Type and
Value.

(n)
Click on any key to continue.

(o)
Select  to return to the Laybye Controls Menu.

2. Modify Existing Laybye

(a)
At the Laybye Number prompt, enter the Laybye
number or alternatively press [Enter] to view and select from the Laybye
listing.

The selected Laybye’s details will be displayed.

(b)
Press [Enter] to modify Address, Telephone,
Comment and Expiry Date Details.

(c)
At the Update prompt, click on Yes to update.

(d)
Select  to return to the Laybye Controls Menu.

3. Cancel a Laybye

(a)
At the Laybye Number prompt, enter the Laybye
number or alternatively press [Enter] to view and select from the Laybye
listing.

The selected Laybye’s details will be displayed.

(b)
Click on  to cancel the laybye.

(c)
The Refund Details will be displayed.

(d)
Enter the Retention %, if required.  Accpick
will automatically calculate the refund amount due. Press [Enter] to accept.

(e)
At the Tender Routine enter the Tender Type and
Amount.

(f)
At the Confirmation prompt, select OK.

(g)
Select  to return to the Laybye Controls Menu.

4. Receive Laybye Payment

(a)
At the Laybye Number prompt, enter the Laybye
number or alternatively press [Enter] to view and select from the Laybye
listing.

The Laybye Details are displayed.

(b)
Press [Enter] to post a payment.

(c)
Enter the Payment Date, Sales Person number and confirm
Payment Amount.

(d)
At the Tender Routine enter the Tender Type and
Amount.

(e)
At the Print Option, select [Yes].

(f)
Click on  to return to the POS Menu.

Note: On Final Payment, goods are taken out
of Laybye Stock, returned to Stock and sold via the Laybye Invoice which is
automatically generated.  Vat is only updated once the Invoice is generated.

2. Enquiry/Reports

1. Specific Laybye Status

This facility displays the current laybye
status for a selected customer.

(a)
At the Laybye Number prompt, enter the Laybye
number or alternatively press [Enter] to view and select from the Laybye listing.

(b)
Highlight and select the required Laybye. Press
[Enter]

(c)
The Laybye Details will be displayed.

to view
Payment History.

to view Stock
Details.

to print either
the original Laybye or the transaction history.

to return to
Laybye Menu.

2. Laybye Listing

Select Option to view listing of Active,
Expired, Cancelled and Completed Laybyes.

to view
individual Laybye details.

to print
report.

to return to
Laybye Menu.

3. Transaction Details

(a)
Select Start and End Dates.

(b)
Select Laybye transactions to view: New Laybyes,
Cancelled Laybyes, Completed Laybyes, Laybye Payments, Laybye Refunds or All of
the Above.

(c)
A listing is displayed. Use the arrows to

to view Laybye
Totals.

to print
report.

to return to
Laybye Menu.

4. Stock on Laybye.

To view valuation of stock on laybye.

to view Stock
Valuation Totals.

to print
report.

3. Utilities

Index Laybye
Files

Note: Laybyes affect the following:

Cash Control

Debtors Transactions

Stock

Laybye Stock

Vat Control

Note: On Final Payment, goods are taken out
of Laybye Stock, returned to Stock and sold via the Laybye Invoice which is
automatically generated.  Vat is only updated once the invoice is generated.

---

## [19.htm]

9.
Quotations

Quotation Options:

8
New Quotation

8
Transactions          Edit Quotation

Invoice
a Quotation

Cancel a
Quotation

8
Enquiry/Reports   Active Quotations

Charged
Out Quotations

Expired
Quotations

Cancelled Quotations

Converted
to Job

8
Utilities          Index Quotation files

Clear
Quotations

New Quotations

(a) Select

,

(b) Select Price Level Options from the listing on which the quotation’s
pricing will be based.

Note: Default is Selling Price 1. Quotes
based on Cost Price, Cost + Markup% and GP% may be password controlled.

(c) At the Date prompt, confirm/capture the capture date and enter the quotation’s
expiry date.

(d) Enter the Customer’s Name, Address, Telephone details, Sales Person
number and any Comments regarding the quotation or alternatively use the select
facility to view and select from the Debtor listing. The Debtors details will
be displayed.

(e) Complete the address, telephone, Salesperson details and any
comments as may be required regarding this quote.

(f) The Quotation Entry Screen will be displayed.

(g) Click on

to insert line details.

(h) At the Stock Code prompt, enter the stock code or alternatively
press [Enter] at the Description prompt, press the [Page Down] key to view and
select from the Stock Listing.

to toggle the stock search order by Stock
Code, Supplier Code or Stock Description.

(i) At the Quantity prompt, enter the number of units sold.

Note: Pressing [Page Up] at the Quantity
prompt will display last purchase details.

Note: Pressing [Page Down] at the Quantity
prompt will display Quantity on Hand as well as Selling Price level 1, 2, 3.

(j) At the Selling Price prompt, Accpick will automatically display the
Selling Price. Press [Enter] to
accept the default Selling Price or enter an adjusted price. Where a maximum
discount has been set in Stock Maintenance for a specific item this may not be
exceeded.

Note: Where a stock item is quoted below
cost, a warning is sounded and displayed.

(k) At the Discount % prompt, enter the discount percentage amount.
Where a maximum discount has been set in Stock Maintenance for a specific item
this may not be exceeded.

(l) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be
overwritten.  Press [Enter] to accept the
default tax status.

(m) The Total Inclusive Value for that stock item is displayed.

(n) To enter further line items select

.

Quotation
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the Quotation.

to display sub total details.

to insert comment details on the Quotation. (A
no value item)

(o) When the Quotation is complete, click on

to check the Gross Profit, Set the Price or
Update.

(p) At the Update Options prompt, select Update.

(q) At the Print Options prompt select the required print format:

Quotation, Valuation, Pro Forma Invoice or No Print.

(r) Click on

to return to the Point of Sale Menu.

Note: The Set Price facility allows the Total
End Value of the Quotation to be revised.
The prices of the individual items will be adjusted in proportion to the
new end value.

Transactions

Edit Quotation

(a)
At the Quotation Number prompt,
enter the Quotation number or alternatively use the select facility to view and
select from the Quotation listing.

The Quotation Details will be displayed.

Quotation
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the
Quotation.

to display sub total details.

to insert comment details on the Quotation. (A
no value item)

(b) Click on

to update the quotation.

(c) At the Print Options prompt select the required print format:

Quotation, Valuation or Pro Forma Invoice.

(d) Click on

to return to the Quotation Menu.

Invoice a Quotation

(a)
At the Quotation Number prompt,
enter the Quotation number or alternatively use the

facility to view and select from the Quotation
listing by using the

and

arrows to locate to top of screen and click on

.

(b) Select the Charge Options – Cash
or Account.

Cash Option

(c) Confirm/Amend the Invoice Date.

(d) Enter the Customer’s Delivery Details – e.g. Registration Number and
Make, Customer’s Name, Address and Telephone Details.

(e) Enter the Order Number and Customer Reference Number.

The Quotation Invoicing details will be
displayed.

Quotation
Line Item Adjustments/Deletions

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the
Quotation.

to display sub total details.

to insert comment details on the Quotation. (A
no value item)

(f) When the Invoice is
complete and correct, click on

to update the transaction.

After the Invoice has been updated, the
Tender Routine will be activated displaying the amount owing.

(g) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details – Drawer’s
Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

(h) At the Vat number prompt, enter/confirm the customer’s vat number.

(i) At the Print Options prompt, select the required print options.

(j) Click on

to return to the Point of Sale Menu.

Account Option

(a)
Select Account Options – Existing Debtor or New Debtor.

(b) For an Existing Debtor,
select and enter the Debtor’s Account Number or use the search facility to view
and select from the Debtor Listing..

(c) Confirm the Invoice Date.

(d) The Debtor’s Delivery Details will be displayed. Complete as
required.

(e) Enter the Order Number and Customer Reference Number.

The Quotation Invoicing details will be
displayed.

Quotation
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the
Quotation.

to display sub total details.

to insert comment details on the Quotation. (A
no value item)

(f) When the Invoice is
complete and correct, click on

to update the Transaction.

(g) At the Print Option, select the required print option.

(h) Click on

to return to the Point of Sale Menu.

Cancel a Quotation

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively use the select facility to view and
select from the Quotation listing. The Quotation Details will be displayed.

(b) Click on

to cancel the quotation.

(c) Select Yes ok to cancel.

2. Enquiry/Reports

1. Active Quotations

This facility displays all Active/Open
Quotations.

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively press [Enter] to display the
quotation listing.

(b)
Use the arrow keys to move the
required quotation to the top of the listing.

(c) Press

to view Quotation details.

(d)
Select

to print quotation.

(e)

to return to the Enquiry/Report Menu.

2. Charged Out Quotations

This facility displays all Quotations that
have been invoiced out in the current period.

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively press [Enter] to display the
quotation listing.

(b) Use the arrow keys to move the required quotation to the top of the
listing.

(c) Press

to view Quotation details.

(d) Select

to print quotation.

(e)

to return to the Enquiry/Report Menu.

3. Expired Quotations

This facility displays all Quotations still
on record, yet beyond their expiry date.

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively press [Enter] to display the
quotation listing.

(b) Use the arrow keys to move the required quotation to the top of the
listing.

(c) Press

to view Quotation details.

(d) Select

to print quotation and then

to return to the Enquiry/Report Menu.

4. Cancelled Quotations

This facility displays all Quotations that
have been cancelled.

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively press [Enter] to display the
quotation listing.

(b)
Use the arrow keys to move the
required quotation to the top of the listing.

(c) Press

to view Quotation details.

(d)
Select

to print quotation and then

to return to the Enquiry/Report Menu.

5. Quotations Converted to Job Cards

This facility displays all Quotations that
have been updated to Job Cards.

(a)
At the Quotation Number prompt,
enter the quotation number or alternatively press [Enter] to display the
quotation listing.Use the arrow keys to move the required quotation to the top
of the listing.

(b) Press

to view Quotation details.

(c)
Select

to print quotation and then

to return to the Enquiry/Report Menu.

Utilities

1. Index Files

Index files to resort the quotation data
files for the Current Period.

2. Clear Quotations

This facility has the option to remove all
Quotations expired prior to a selected date.

(a)
At the Date prompt, enter the date
for which quotations that have expired prior to this date will be cleared.

(b)
Select the required quotation
from the listing and select

to delete the required quotation/s.

(c) Press Enter and confirm deletion.

(d)

to return to the Quotation Menu.

Note: To clear ALL displayed expired
quotations select Clear All.

Note: Cleared Quotations do not reflect on
the Cancelled Enquiry Screen/Report.

---


# 1. Point of Sale (extra: Payout / Repairs / Cheque / Job Costing)


## [110.htm]

P.
Payout

Payout Options:

8
Payout Transaction

8
Payout Enquiries

8
Payout Reports

8
Password Control on Payouts

Payout Transaction

(a) Select

,

(b) At the Amount Paid prompt, enter the amount paid out

(c) At the Details prompt, enter to whom amount paid and description of
goods.

(d) a reference description.

(e) At the Update prompt, click on Yes to update.

(f) At the Print prompt, select Yes or No as required.

(g) Press

to return to the POS Main Menu.

Note: Where change is brought back from a
Payout, repeat the process with a minus value for the change. Add “Change” in
the Details.

Payout Enquiries

An option exists to view Payout Details at
Cash Control Enquiry.

Select:

(a)

,

(b) Cashier Number or leave blank to view for ALL Cashiers.

(c) Payout Details

Payout Reports

An option exists when printing Day End
Reports to print a detailed daily payout listing.

Payouts accumulated for the month may be
viewed and printed in

,

, 6. Payouts.

Password Control

Payouts may be password controlled. To initiate
a password control select:

,

,

2. Password Maintenance,

Point of Sale

To Block/Disallow Payouts at Point of Sale select:

,

,

4. Transactions,

POS and Stock Setups 2

Allow
Payouts from Cash in Draw? No

---

## [111.htm]

R.
Repair Controls

Repair Control Options:

8
Transactions          New Repair Entry

Modify
Repair Voucher

Issue
Items for Repairs

Receive
Repaired Items

Charge
for the Repair

Cancel a
Repair

8
Enquiry/Reports   Specific Repair Status

Repairs
by Supplier

Outstanding
Billings

8
Utilities          Index Repair Files

Transactions

1. New Repair Entry

(a) Select

,

,

Transactions,  New
Repair Entry

The Repair Voucher Creation screen is
displayed.

(b) At the Date prompt, confirm/capture the capture date of the Repair.

(c) At the Name request, enter the Customer’s Name, Address and
Telephone details or press [Enter] to view and select from the Debtor listing.

(d) Capture the Order Number, Date Repair Required, Quoted Value of
Repair excluding Vat (optional), Contact Person and Repair Details. Suggest
description of goods, serial number, fault description.

(e) At the Save prompt, select [Yes].

(f) At the Print prompt, select [Yes]. A sequential Repair Voucher
Number is allocated and printed on the Repair Voucher.

(g) Click on

to return to the Repair Control Menu.

2. Modify Repair Voucher

The system will display alphabetically a
list of all current Repair Dockets.

(a)
Use the arrow keys to move the
required Repair Docket to the top of the listing or alternatively select

to locate the required Repair Docket by
Customer Name.

(b)
Press

to view Repair Docket details.

(c) The Repair details will be displayed. Edit the details as required.
Press [Enter] to update the new details.

(d) Click on

to return to the Repair Control Menu.

3. Issue Items for Repairs to Supplier

The system will display alphabetically all
current Repair Dockets.

(a)
Use the Up and Down arrow keys
to move the required Repair to the top of the listing or alternatively select

to locate the Repair Docket by Customer Name.

(b)
When the required Repair Docket
is at the top of the listing, press

.

(c)
At the Supplier prompt enter
the Supplier’s Account Number or alternatively, press [Enter] to view and
select from the Supplier listing.

(d)
Enter the Issue Details – Date
Sent, Transport Mode, Issue Comments, Company Contact person and Supplier’s
Contact details.

(e)
Click on

to return to the Repair Control Menu.

(f)
At the Issue Repairs prompt,
select [Yes].

(g)
At the Print Confirmation
prompt, select [Yes].

Note: The Repair Request Voucher Number is
the same as the Repair Voucher Number to ensure traceability.

4. Received Repaired Items from
Supplier

(a)
At the Supplier prompt enter
the Supplier’s Account Number or alternatively press [Enter] to view and select
from the Supplier listing.

(b)
Press [Enter] if the Supplier
Account is correct.

The system will display a list of all
Repairs issued to the selected Supplier.

(c)
Use the Up and Down arrow keys
to move the required Repair to the top of the listing or alternatively select

.

(d)
When the required repair is at
the top of the listing, press

.

(e)
At the Date Repaired prompt,
enter the date the Repair was returned.

(f)
At the Capture Costs prompt,
select Yes/No.

(g)
If Yes, enter the Repair Cost Details –
Date, Supplier’s Invoice Number, Inclusive of or Exclusive of Vat, Expense
Category, (Suggest: Outwork), Repair Amount, Tax Code. The Vat amount and the
Supplier’s Invoice Total will automatically be displayed.

(h)
At the Supplier Comment prompt,
enter details if required.

(i)
At the Save prompt, select
[Yes].

(j)
Click on

(k)
At the Ok to Update prompt,
select [Yes].

(l)
At the Print Confirmation
prompt, select [Yes].

(m) Click on

to return to the Repair Control Menu.

5. Charge for the Repair

The system will display alphabetically all
current Repair Dockets.

Press

to toggle Repair Status and Date repair
received from Supplier.

(n) Use the Up and Down arrow keys to move the required Repair to the
top of the listing or alternatively select

.

(o) When the required repair is at the top of the listing, select

or

to mark Repair Dockets for multiple invoicing.

(p) At the Charge for Repair prompt, select [Yes].

(q) Select the Charge options – Cash or Account.

Cash
Option

The Repair Invoicing details will be
displayed as a Cash Sale.

(a)
Click on

to insert line details.

Note: To view Cost Price of Repair: Caps
locks on and press “C”. Cost of Repair is displayed on the left hand side of
the screen.

To
capture a Non-Stock item, with the facility of
allocating to the correct department with the correct Gross Profit:

to select the required department, capture the
Cost Price, Markup % and edit/amend the Selling Price.

Note: Department Name may be overwritten for
Invoice Details.

Cash Sale Line Item Adjustments/Deletions

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the
Quotation.

to display sub total details.

to insert comment details on the Cash Sale. (A
no value item)

(b) When the Cash Sale is complete and
correct, click on

to update the transaction.

(c) At the Update prompt, select
[Yes].

After the Invoice has been updated, the
Tender Routine will be activated displaying the amount owing.

(d) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details –
Drawer’s Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

(e) At the Vat number prompt, enter/confirm the customer’s vat number.

(f) At the Print Options prompt, select the required print options.

(g) Click on

to return to the Point of Sale Menu.

Account Option

(a)
Select Account Options – Existing Debtor or New Debtor.

(b) For an Existing Debtor,
select and enter the Debtor’s Account Number or use the search facility to view
and select from the Debtor Listing..

(c) Confirm/Capture the Invoice Date.

(d) The Debtor’s Delivery Details will be displayed. Complete as
required.

(e) Enter the Order Number and Customer Reference Number.

The Repair Invoicing details will be
displayed.

(f) Click on

to insert line details.

Note: To view Cost Price of Repair: Caps
locks on and press “C”. Cost of Repair is displayed on the left hand side of
the screen.

To
capture a Non-Stock item, with the facility of
allocating to the correct department with the correct Gross Profit:

to select the required department, capture the
Cost Price, Markup % and edit/amend the Selling Price.

Note: Department Name may be overwritten for
Invoice Details.

Invoice
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Repair and automatically move it to the top of the listing.

and

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

to insert comment details on the Invoice. (A
“no value” entry)

(g) When the Invoice is
complete and correct, click on

to update the Transaction.

(h) At the Update prompt, select [Yes].

(i) At the Print Option, select [Yes].

6. Cancel a Repair

The system will display alphabetically all
current Repair Dockets.

(a)
Use the Up and Down arrow keys
to move the required Repair to the top of the listing or alternatively select

.

(b)
Press

The Repair Details will be displayed.

(c) At the Cancel Repair prompt, select [Yes].

Enquiry/Reports

1. Specific Repair Status

This facility displays selected Repair
Voucher details.

(a)
At the Repair Voucher prompt,
enter the Repair Voucher number or alternatively press [Enter] at the prompt to
view and select from the listing.

The Repair Voucher Details will be
displayed.

(b) Use the arrow keys to view all line items on the Repair Voucher.

(c) Press * to print the Repair Voucher Enquiry.

(d) Press

to view further Repair Vouchers.

(e) Press

to return to Repair Control Menu.

2. Repairs by Suppliers

This facility displays all Repairs  - outstanding and/or returned -  for all or a specific Supplier.

to return to Repair Control Menu.

3. Outstanding Billings

This facility displays all Repair Vouchers
waiting to be invoiced out to Customers.

to toggle Repair Voucher listing order.

to toggle Repair Status and Date repair
received from Supplier.

to print listing.

to return to Laybye Menu.

Utilities

Index Files

Index Files to resort Repair Control data
files.

---

## [112.htm]

C.
Cash a Cheque

This facility results in the quantity and value of cheques being
increased and the value of cash being decreased.

(a) At the Cheque Amount prompt, enter the cheque value.

(b) At the Update prompt, select Yes.

(c) At the Bank Details prompt, enter the Drawer’s name, Bank and Account
Number, Id Number and Telephone Number.

Password Control

This facility may be password controlled.
To initiate a password control select:

,

,

2.
Password Maintenance, Point of Sale , Cash Control

---

## [113.htm]

J.
Job Costing

Job Costing Options:

8
Transactions          1. Open a New Job

2. Edit
a Job Card

3.
Cancel a Job Card

4.
Complete/Charge for the Job

Single
Job Card

Multiple
Job Cards

5. New Job
from a Quotation

8
Enquiry/Reports   1. Active/Open Jobs

2.
Completed/Charged Jobs

3.
Cancelled Jobs

4. Stock
on Jobs

8
Utilities          1. Index Files

2. Maintain
Operators

1. Transactions

1. Open a New Job

(a) At the Date prompt, enter the capture date of the Job or press
[Enter] to accept the default date.

(b) At the prompts, complete the details for each for each of the
prompts.

(c) Enter the Customer’s Name, Address, Telephone details Contact
details and Order Number or alternatively, press enter to view and select from
the Debtor listing.

(d) At the Job Description prompt, enter a brief the job description if
required or press [Page Down] to bypass.

(e) At the Capture Details prompt, select [Yes].

(f) Click on

to insert stock items from the stock listing.

Note: A series of prompts will be displayed
in accordance with the Prompts, Tenders and Point of Sale Setups in System
Parameter Setup.

(g) At the Stock Code prompt, enter the stock code or alternatively,
press [Enter] and at the Description prompt, press the [Page Down] key to view
and select from the Stock Listing which is displayed in description order.

to toggle the stock search order by Stock
Code, Supplier Code or Stock Description.

(h) At the Quantity prompt, enter the number of units sold.

Note: Pressing [Page Up] at the Quantity
prompt will display last purchase details.

Note: Pressing [Page Down] at the Quantity
prompt will display Quantity on Hand as well as Selling Price level 1, 2, 3.

(i) At the Selling Price prompt, Accpick will automatically display the
Selling Price. Press [Enter] to
accept the default Selling Price or enter an adjusted price. Where a maximum
discount has been set in Stock Maintenance for a specific item this may not be
exceeded.

Note: Where a stock item is sold below cost,
a warning is sounded and displayed.

(j) At the Discount % prompt, enter the discount percentage amount.
Where a maximum discount has been set in Stock Maintenance for a specific item
this may not be exceeded.

(k) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  Where the System Parameter options have been
set to the Tax Code Status, the Tax Code can be overwritten.  Press [Enter] to accept the default tax
status.

(l) The Total Inclusive Value for that stock item is displayed.

(m) To enter further line items select

.

To
capture a Non-Stock item, with the facility of
allocating to the correct department with the correct Gross Profit:

to select the required department, capture the
Cost Price, Markup % and edit/amend the Selling Price.

Note: Department Name may be overwritten for
Invoice Details.

Job Card
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

and

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

(n) When the Job Card is correct and complete, click on

to update the Job Card.

(o) At the Options prompt, select Update.

Note: At the Update prompt, selecting Set
Price will display the Set Selling Price prompt. Enter the revised inclusive
Total Amount of the Job. The system automatically adjusts the prices of
individual items in proportion to the new total price.

This facility maybe password controlled

Note: At the Update Transaction prompt,
selecting Check GP will display the Transaction Gross Profit. This facility
displays the gross profit value and gross profit percentage for the total Job.

(p) At the Print Options prompt, select Job Card to print the Job Card.

(q) Press [Escape] to return to the Job Costing Menu.

Note: This is now an ACTIVE Job.

2. Edit a Job Card

(a)
At the Job Number prompt, enter
the Job Card Number to display job card details.

Note: [0] and pressing

will display all active job cards in numerical
sequence.

to sort job card listing by Name, Registration
Number, Date, Operator Number, Sales Person or Job Number.

Highlight and press

to select the required job card from the
listing.

(b) Edit the Job Card Header details as required or alternatively press
[Page Down] to accept the default details.

(c)
At the Edit Details prompt, select
[Yes]

(d)
Click on

to insert additional stock items from the
stock listing,

to remove a line item/s.

to insert department details.

(e) When the Job Card is correct and complete, click on

to update the Job card.

(f) At the Options prompt, select Update.

(g) At the Print Options prompt, select Job Card to print the Job Card.

3. Cancel a Job Card

The system will display all active Job Cards
in Job Card Number sequence.

(a)

to sort job card listing by Name, Registration
Number, Date, Operator Number, Sales Person or Job Number.

(b)
Use the arrow keys to highlight
the required Job Card.

(c) Click on

to select the Job Card. The Job Card details
will be displayed.

(d) Click on

to cancel the Job card.

(e) At the Cancel Job Card prompt, select [Yes].

(f) At the Reason prompt, enter an explanation for the cancellation.

(g) At the Cancel prompt, click on [Ok].

Note: The Job Card is now CANCELLED.

4. Complete/Charge for the Job. i.e
Create an Invoice.

Invoice Single Job Card

(a)
At the Job Number prompt, enter
the Job Card Number to display job card details alternatively selecting [0] and
pressing [Enter] will display all active jobs in Job Card Number sequence.

The system will display all active Job Cards
in Job Card Number sequence.

(b) Highlight the required Job Card and click on

to select the Job Card.

(c)
Select Charge options – Cash,
Account on Job Card, Different Account.

(d) At the prompts, complete the Invoice Header details.

The Job Card Invoicing details will be
displayed.

Invoice
Line Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

(e) When the Invoice Details are correct and complete, click on

to update.

(f) At the Update Options prompt, enter Yes.

Note: If this is a Cash Sale, the Tender Routine is displayed.

(g) At the Tender prompt, enter the payment type and amount.

Note: Cash Payments: If Rounding has been selected; the Rounding
information box will be displayed showing the cash value to be accepted.

Cheque and Voucher Payments: Accpick will prompt for the cheque details –
Drawer’s Name, Bank and Bank Account Number, ID Number and Telephone number.

Speedpoint: Process all Speedpoint payments by entering the value at the
Speedpoint prompt.

Note: To return to the body of the Cash Sale once the Tender
Routine Box is displayed, press [Page Up].

Note: To convert a Cash Sale
into and Account Sale,
press [Page Down] at the Tender Routine.

(h) At the Vat number prompt, enter/confirm Customer’s Vat number.

(i) At the Print Options prompt, select the required print options.

(j) Press any key to return to the Job Costing Menu.

Note: This Job Card is now INVOICED.

Invoice Multiple Jobs

Note: This is only possible for Jobs opened
on the same Debtor’s Account. i.e Invoice multiple Jobs to a Single Debtor

The system will display all active Job Cards
in Job Card Number sequence.

(a)
Use the arrow keys to highlight
the required Job.

(b)  Click on

to tag the Job Card.

Note: A * will indicate which Jobs have been
selected for invoicing.

(c) Repeat until all required Jobs Cards have been tagged

(d) Click on

to invoice the tagged Jobs.

(e) At the prompts, complete the Invoice Header details.

(f) The Job Card Invoicing details will be displayed

Invoice
Lien Item Adjustments/Deletions:

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

to locate a specific stock code captured on
the Invoice and automatically move it to the top of the listing.

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

(g) When the Job Card is correct and complete, click on

to update the Job Card.

(h) At the Update Options prompt, enter Yes.

(i) At the Vat number prompt, enter/confirm the Debtor’s Vat number.

(j) At the Print Options prompt, select the required print options.

(k) Press any key to return to the Job Costing Menu.

Note: These Multiple Job Cards are now
INVOICED to a single Invoice.

5. New Job Card from a Quotation.

This facility allows the conversion of a Quotation
to a Job Card.

(a)
At the Quote Number prompt,
enter the Quotation Number.

Note: [0] will display all quotations in
numerical sequence.

to select the required Quotation from the
listing.

to sort Quotation listing.

(b) At the Date prompt, enter/confirm the capture date of the Job.

(c) At the prompts, complete the details for each of the prompts.

(d) Enter the Customer’s Name, Address, Telephone details and Order
Number or press [Enter] to accept the default details.

(e) At the Job Description prompt, enter a brief description if
required.

(f) At the Capture Details prompt, select [Yes].

The line items as per the
Quotation are displayed.

Job
Card Line Item Adjustments/Deletions:

Click on

to insert additional line items.

to locate a specific stock code captured on
the Quotation and automatically move it to the top of the listing.

Use the arrow keys to move the incorrect
transaction line/s to the top of the listing and delete/edit as required.

and

to make correcting adjustments to the entry
displayed at the top of the listing.

to display sub total details.

(g) When the Job Card is correct and complete, click on

to update the Job Card.

(h) At the Options prompt, select on Update.

(i) At the Print Options prompt, select Job Card to print the Job Card.

(j) Click on

to return to the Job Costing Menu.

Note: This is now an ACTIVE Job.

2. Enquiry/Reports

1. All Active/Open Job Cards

This facility displays all Active/Open Job
Cards.

(a)
At the Search Options Menu
select the required search option: Date
Range or Job Card Number.

A listing of all Active/Open Job Cards will
be displayed.

(b) Use the arrow keys to highlight the required Job Card.

(c)
Select

to view Job Card details.

(d)
At the View Header prompt,
select Yes/No.

(e)
At the Value options prompt,
select option to view Job Card Value at Cost Price or Selling Price.

(f)

to print Job Card.

(g)
Click on

to return to Job Card listing.

(h)

to return to Job
Costing Menu.

2. Completed/Charged Out Jobs

This facility displays all
completed/charged out Jobs.

(a)
At the Search Options Menu
select the required search option: Date
Range or Job Card Number.

A listing of all Completed/Charged Out Jobs
will be displayed.

(b) Use the arrow keys to highlight the required Job Card.

(c) Select

to view Job Card details.

(d) At the View Header prompt, select Yes/No.

(e) At the Value options prompt, select option to view Job Card Value at
Cost Price or Selling Price.

(f)

to print Job Card.

(g) Click on

to return to Job Card listing.

(h)

to return to Job Costing Menu.

3. Cancelled Jobs

(a)
At the Search Options Menu
select the required search option: Date
Range or Job Card Number.

A listing of all Cancelled Job Cards will be
displayed.

(b)

to sort Cancelled Job Card listing.

(c) Use the arrow keys to highlight the required Job Card.

(d)
Select

to view Job Card details.

(e)
At the View Header prompt,
select Yes/No.

(f)
At the Value options prompt,
select option to view Job Card Value at Cost Price or Selling Price.

(g)

to print Job Card.

(h)
Click on

to return to Job Card listing.

(i)

to return to Job Costing Menu.

4. Stock on Jobs.

To view valuation of stock on Jobs.

(a)
At the Stock Options prompt,
select enquiry options:

All Stock

Stock for a Specific Operator

Stock for a Specific Sale Person

(b)

to view listing by Stock Code, Description,
Department and Supplier.

(c)
Use the arrow keys to highlight
the required Job.

(d)
Select

to view stock details.

(e)

to print report.

(f)

to return to Job Costing Menu.

Utilities

1. Index Files

Index files to resort the Job Costing files
for the Current Month.

2. Maintain Operators

This facility provides the option of:

adding new operator details

,

modifying existing operator details

and deleting existing operator details.

---


# 2. Debtors - top level


## [24.htm]

Debtors
Reports

On the Debtors’ Reports Menu, the Data
Status Window will indicate which directory the reports will be extracted
from.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories.

For reports to print, the printer needs to
be on-line.

The following reports are available for
printing:

Reports

Report
Options

Report
Information

A. Account Details

Alphabetical or
Numerical Sequence

Include Credit Limits or Not

Address Details: Include Postal/Delivery/Both/None

Report by Area/Salesman

Report lists all
Debtors’ details including:

Account number, name, short-name, address, telephone number, area, vat number
and credit limits.

B. Age Analysis

Weekly or
Monthly

Alphabetical or Numeric Sequence

Start and End Areas

Totals or Detailed

Include Post Dated Cheques

Print last paid, telephone numbers and credit
limit information

Select for:

All accounts with Balances

Selective Ageing

Blocked Accounts

Accounts with Credit Limits

Report lists all
Debtors outstanding balances owing for the various periods according to the
selected report options.

C. Statement Print

- Current and

- Historical

Current Period:

Blank or Pre printed Stationery option

Verify or amend statement address details

Enter date to appear on statement

Include all active accounts and / or exclude all zero balance accounts

Insert message, if any, to print on all statements

Alphabetical or numeric order

Select Start at
short name/account number and Stop at short name /account number print points

Print for specific area or salesman

Print Open Item Statements as Open Item or Balance Brought Forward i.e.
detail the current month’s transactions only

Print COD accounts with zero balances

Option for line up

Historical Period:

Report will
print all monthly statements according to selected report options

Statements will print for Balance Brought Forward Debtors and Open Item
Debtors

Balance Brought Forward Debtors’ Statements will print the opening balance,
all current transactions, current payments and a closing balance which is
aged accordingly

Open Item
Debtors’ Statements will print for unmatched items, the original value and
all payments thereon, plus all unallocated transactions

Historical statements for a selected date range may be accessed where there
is archived data. Historical statements are first displayed on the screen.

D. Department Analysis

1.Current Period

2.Year to Date

3.Detailed Analysis for Selected Departments

4.Cash/Account Sales Split

Report lists all
information regarding the sales figures for selected departments and date
ranges

E. Transactions

Start and End
Dates

Detailed or Totals

Transaction Types:

- Invoices

- Credit Notes

- Cash Sales

- Cash Returns

- Receipts

- Settlement             Discounts

- Interest Charges

- Debit Journals

- Credit Journals

- Laybye Sales

- All the Above

Report lists all
account related transactions.

The system will default to the earliest and latest date for which there are
transactions

F. Area/ Salesman

Reports:

1. Year-to-date

2. Detailed Analysis:

Start and Stop at Area /
Sales Person

Start and Stop Date

Detailed or Totals

Sort and Total by Department

Include GP or not

Cash Sales Only/Account Sales Only or Both types of Sales

3. Masterfile Area

Report prints
sales transactions and or totals per area / salesman.

Master File Analysis prints a list, for selected areas, of each active Debtor
with Month –to-Date and Year-to-Date Sales and Profit.

G. Address Labels – name
and address details

Alphabetical or
Numeric Order

Specific Area

Number of copies to print

Option prints
address labels for statement envelopes.

H. Credit Limit Warning

Select and enter
Date to appear on Report

Alphabetical or Numerical sequence

Based on Credit Limit of Terms

Prints Credit
Warnings

I. Account Performance

Sales and GP
(MTD and YTD):

Alphabetical or Numerical sequence

Start and Stop Area

Start and Stop
Account Number

Option to Skip
Zero

Month-to-Date
Values

Date on Report

Past 12 Months Sales:

Specific area Y /N

Report prints
month-to-date and year-to-date Sales and Profit per account.

J. Reprint Transaction

Select Date of
Transaction

Locate or use arrow keys to access required transaction to top of screen.

Press Enter to display transaction details and Print

Reprints copy
invoices, credit notes and cash sales and cash returns from current or
archive months

K. Items Sold

Month to Date,
Historical and Average Area Department Totals

Month to Date:

Start and Stop Dates

for a specific Debtor Account or for all Debtor Accounts

Start and End Department Number

Start and End Supplier Number

Include Gross profit

Include Supplier Name

Historical:

Account Number

3month History / Average or 12 month   History
/ Average

Area Department Totals:

For selected Departments, lists Department Totals by Master Area.

Reports list
stock items sold to selected Debtor / Master Area.

L. Job Cards

Start and End
Dates

Report lists Job
Details by job number, transaction details, date, account name, transaction
value.

---


# 2.1 Debtors - Maintenance


## [211.htm]

1.
Account Details

Account Details Maintenance
Options

8
Adding a new account

8
Modifying an existing account

8
Deleting an existing account

Adding a New Account

(a) At the Debtor’s Maintenance Menu, select 1. Account Details and enter
a new Account number at the Account number prompt.

To select a new account number: Use
the search facility to view your current Debtor Listing or alternatively press the
[Page Down] key to allocate the next available account number or enter a series
number (e.g. 500) and press the [Page Down] key to allocate the next available
account number in that series.

(b) Add the Debtor’s account details. You will be prompted for the
following:

Name

Postal/Delivery
Addresses

Contact Person

Appears on Age Analysis with telephone number

Tel 1/Tel
2/Fax/Email

Area/Salesmen

Press 0 (zero) and enter to view current list of Area/Salesmen.

Click or press enter to select option.

Additional Information

E.g. Cell number

Trade Discount

Enter % discount (if any) by which each line item at POS will
automatically be reduced.

Credit Limit

Maximum amount Debtor may have outstanding on the account.

Price Code

Defaults to Price Level 1.

A Debtor may be linked to Price Level 1/2/3.

Price levels are set up in the Stock Control – Stock Maintenance
Menu.

Charge Interest on overdue accounts

Yes or No

Search Name

Quick access name for invoicing, enquiries etc.

Usually the first five characters of the name.

This field is also used for extracting enquiries and reports in
alphabetical sequence.

Account Category

Blank Balance
brought forward

O        Open Item

C        Cash
type customer

(Invoice update completes the           sale with tender type routine.           Invoice and payment are           posted to the           account.)

Vat/Tax Reference No.

SARS Vat Number.

Terms

30/60/90 days

0 days for Cash
type customer C

Prompt Discount %

% Value that the invoice may be reduced by if paid by due date as
indicated by Terms.

Print on Invoices

Yes – Prompt
payment discount value and message is to appear on invoice.

Discount Value is calculated from the terms and discount % as set
above.

No – No Prompt
payment message will appear on the invoice

Balance on POS Documents

Yes – If current
balance on account is to print on invoices and receipts after each transaction.

Change Block Status

What is block status?

A Debtors account status is either active or blocked.  When an account is blocked all
transactions are barred as indicated by selected option.

Block Options:

If Yes – then the
following options are available:

Select the relevant option.

Do you wish to save this account?

Yes or No.

(c) At the Save Account prompt, click on

.

(d) Click on

to return to the Debtor’s Maintenance Menu.

Modifying
an Existing Account

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view the current Debtor listing. The
Debtor’s details will be displayed.

(b) .Make the necessary modifications.

(c) Click

to save modifications.

(d) At the Save Modification prompt, click on

.

(e) Click

to return to the Debtors Maintenance Menu.

Deleting an Existing Account

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view the current Debtor listing. The Debtor’s
details will be displayed.

(b) Click on

to delete the account.

(c) Click on

to confirm deletion.

(d) Click

to return to previous menu.

Note: Deletion is not permitted when:

an account has a balance, or where
transactions were posted to this account for the current month.

---

## [212.htm]

2.
Account Balances

Account Balance Maintenance
Options:

8
Balance Take-On

8
Account
Category Conversion

Account Category Types

Open Item vs
Balance Brought Forward

All
Debtors/Customer Accounts are processed as either Open Item or Balance Brought Forward Accounts.

Balance
Brought Forward: If an
account is Balance Brought Forward, the total outstanding amount is broken down
into current, 30, 60, 90, 120, 150, 180 days. Receipts are allocated to the
relevant ageing periods. The Accpick Monthly Statements will display an opening
balance at the start of the period, all transactions for the current period and
a closing balance together with the ageing of the total balance.

Open
Item: If an account is
Open Item, all outstanding and unmatched transaction types are listed. The
Accpick Monthly Statements will display a list of all outstanding transactions
from the previous periods and all the current transactions and the ageing of
the above.

Receipts on Open Item Accounts must
be allocated to specific transactions or posted as unallocated.  This is useful for customers who pay on
invoice number and whose remittance advice reflects this detail.

Balance Take-On

(a) At the
Order prompt, select and enter order of entry:

A – Alphabetical Order as per Short Account
Name (A – ZZZ)

N – Numerical Order as per Account Number (1 – 9999)

Note: The Balance Brought Forward Entry
screen or the Open Item Entry screen will automatically appear according to the
account category that was selected when the Debtor/Customer account was added
in the Debtors Maintenance Menu.

Balance Take-On: Balance
Brought Forward

(b) At the Ageing prompt, enter the outstanding balances from Current to
180 days. Press the [Enter] key to move through the ageing options.

(c) At the Update prompt enter Yes.

(d)

Result: You will be prompted with
the next account. Continue taking outstanding balance on.

Balance Take-On: Open
Item

(a) Click on the

button.

(b) Click on the required transaction type from the list.

(c) Enter the transaction number, the date and total amount of the
transaction.

(d) Age the transaction by selecting and entering the appropriate number
e.g. 2 = 30 days.

(e) Repeat for all outstanding transactions for this Debtor until you
have arrived at the correct balance.

(f) Click on

when completed.

(g) At the Save and Post prompt, click on

.

(h) Result: You will be prompted with the next account.

(i) When all account balances have been processed, click on

to return to the Debtors Maintenance Menu.

Account
Category Conversions

Accpick allows you to change the Debtor’s
Account Category from Open Item to Balance Brought Forward and visa versa.

Open Item to Balance Brought Forward

(a) Select

,

and

1. Account Details

(b) Use the search facility to view your debtor listing and enter the
Debtors account number at the Account number prompt.

(c) Change the Account Category from

(O = Open Item) to

(Blank = Balance Forward)

(d) Click on

.

(e) At the Save Modification prompt, click on

.

(f) At the Options prompt, click on [Yes]
to confirm conversion from Open Item to Balance Brought Forward and [Yes] to clear all open item
transactions..

(g)

Click on

.

Re-index all files in order to remove all
Open Item entries by selecting

from the Main Menu and

from the Utilities Menu.

Note: Re-indexing is a single user operation.

Balance Brought Forward to Open Item

(a) Select

,

and

1. Account Details

(b) Use the search facility to view your debtor listing and enter the
Debtors account number at the Account Number prompt.

(c) Change the Account Category from

(Blank =
Balance Forward)

(O = Open Item)

(d) Click on

.

(e) At the Save Modification prompt, click on

.

Result: The Open Item Entry Screen will
appear.

(f)
Click on

to enter all outstanding transactions.

(g) Click on

when totals are in balance.

(h) Click on

.

If Ageing is not correct the following
screen will appear:

Click on [Continue] and edit entry to correct ageing.

---

## [213.htm]

3.
Sales Areas / Salesmen

Sales Areas / Salesmen Maintenance
Options:

8
Add a new Sales Area / Salesman

8
Modify an existing Sales Area / Salesman

All Debtors can be categorized by Area or
by Salesman to enable the extraction of management or performance reports.

These are created at the time of system set
up. Note that each category is allocated a number and a name.

Add a New Sales Area/Salesman

(a) At the Sales Area / Salesman Number prompt enter a new number or,
use the search facility to view your current Sales Area / Salesman Listing to allocate
a new Sales Area / Salesman number [1 - 99] or,

(b) At the Number prompt, press the [Page
Down] key to allocate the next available Sales Area / Salesman number.
Press [Enter].

(c) At the Name prompt, type in the new Sales Area / Salesman name.
Press [Enter].

(d) At the Insertion Option prompt, click on

.

(e) Press

to return to the Debtor Maintenance Menu.

Modify an Existing Sales Area/Salesman

(a) At the number prompt, enter the Sales Area / Salesman number
requiring modification or, use the search facility to view the current Sales
Area / Salesman Listing.

(b) Make the required adjustments.

(c) At the Replacement request, click on

.

(d) Press

to return to the Debtor Maintenance Menu.

---

## [214.htm]

4.
Sales Departments

Sales Department Maintenance
Options:

8
Create a new Sales Department

8
Modify an existing Sales Department

Accpick allows all Stock Items to be
categorized into Departments/Categories/Groups to enable the extraction of
management or performance reports. Each department is allocated a number (1 –
999) and a name.

Create a New Sales Department.

(a) At the Sales Department number prompt enter a new Sales Department
number or, use the search facility to view and select from the current Sales
Department listing. [1 - 99] or,

(b) At the Sales Department Number prompt, press the [Page Down] key to allocate the next
available Sales Department number.

(c) At the Sales Department Name prompt, type in the new Department name.
Press [Enter].

(d) At the Insertion Option prompt, click on

.

(e) Click

to return to the Debtors Maintenance Menu.

Modify a Sales Department.

(a) At the Sales Department number prompt, enter the Sales Department
number requiring modification or, use the search facility to view the current
Sales Department Listing.

(b) Select the Sales Department you wish to modify.

(c) Make the required adjustments. Press [Enter].

(d) At the Replacement request, click on .

(e) Click

to return to the Debtors Maintenance Menu.

---


# 2.2 Debtors - Journals


## [221.htm]

1.
Debit Journal

(Increases the balance owing by the
Debtor)

Debit Journal Options

8
Debit Journals for Balance Brought
Forward Debtors

8
Debit Journals for Open Item Debtors

Debit Journal for Balance Brought Forward
Debtors

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to select a Debtor.

(b) Confirm the Debtor’s details by clicking on [Yes Correct].

(c) At the Date prompt, enter the journal date or alternatively press [Enter]
through the default date.

(d) At the Journal Amount prompt, enter the journal amount.

(e) At the Additional Reference prompt, enter a short explanation
motivating the journal. This information appears on the Debtor’s Statement, the
Journal Transactions Report and on the General Ledger Integration.

(f) At the Journal Number prompt, enter the journal number or
alternatively press [Enter] through the default journal number. Accpick
automatically allocates journal numbers in a consecutive sequence.  Should you repeat a journal number the
following screen will appear:

(g)  Allocate Ageing accordingly.
Ensure the Ageing Total balances with Journal Amount.  If not, Accpick will prompt you to make the correction.

(h) At the Ok to Update prompt, click on

. The Debit
Journal entry screen is displayed allowing further journal entries to be
captured.

(i) When completed capturing all journals in the batch, click on

.

(j) Click on

to confirm batch total and end the batch.
Accpick will return to the Debtors Transaction Menu.

Debit Journal for Open Item Debtors

The Open Item entry screen will
automatically appear according to the Debtor’s Account category selected on the
Debtor’s Account Details Menu.

At the Debit Journal Posting Screen, follow
the same procedure as for Balance Brought Forward Debtors but note the
following differences:

The total value of the journal may only be
allocated to ONE ageing period. Press the [é] and [ê] arrow keys to highlight the period
to which the total journal amount is to be allocated. Press [Enter] to update
the journal transaction immediately.

Every journal entry must be allocated a
unique journal number. The same journal number on open item is not allowed.

---

## [222.htm]

2.
Credit Journal

(Decreases the balance owing by the
Debtor)

Credit Journal Options

8
Credit Journals for Balance Brought
Forward Debtors

8
Credit Journals for Open Item
Debtors

Credit Journal for Balance Brought Forward
Debtors

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to select a Debtor.

(b) Confirm the Debtor’s details by clicking on [Yes Correct].

(c) At the Date prompt, enter the journal date or alternatively press
[Enter] through the default date.

(d) At the Journal Amount prompt, enter the journal amount.

(e) At the Additional Reference prompt, enter a short explanation
motivating the journal. This information appears on the Debtor’s Statement, Journal
Transactions Report and on the General Ledger Integration.

(f) At the Journal Number prompt, enter the journal number or
alternatively press [Enter] through the default journal number. Accpick
automatically allocates journal numbers in a consecutive sequence.  Should you repeat a journal number the
following screen will appear:

(g)  Allocate ageing accordingly.
Ensure the Ageing Total balances with the Journal Amount.  If not, Accpick will prompt you to make the
correction.

(h) At the Ok to Update prompt, click on

. The Credit
Journal Posting Menu appears which allows further journal entries to be
captured.

(i) When completed capturing all journals, click on

(j) Click on

to confirm batch total and end the batch.
Accpick will return to the Debtor Transaction Menu.

Credit Journal for Open Item Debtors

The Open Item entry screen will
automatically appear according to the Debtor’s account category selected on the
Debtor’s Account Details Menu.

At the Credit Journal Posting Screen,
follow the same procedure as for Balance Brought Forward Debtors but note the
following differences:

The total value of the journal may only be
allocated to ONE ageing period. Press the [é] and [ê] arrow keys to highlight the period
to which the total journal amount is to be allocated. Press [Enter] to update
journal transaction immediately.

Every Journal Entry must be allocated a
unique journal number. The same journal number on open item is not allowed.

---

## [223.htm]

3.
Interest Charging

Note: This should only be done at month end
after a backup.

(a)

Make a backup. Invoke the backup procedure by double clicking on the
Accpick Back-Up Icon on the desktop.

(b) Confirm backup procedure has been completed by clicking on

. The Interest
Charging Routine screen will be displayed.

(c) At the Date for Interest Charge prompt, enter the date interest is
to be charged on – usually the Month End date.
This date will appear on the Debtors’ Statements and on the Transactions
Report. Press [Enter].

(d) At the Start Charging at prompt, select, from the display list, the
period from which interest must be charged. E.g. If 2 is selected, interest
will be charged on all outstanding balances in 30 days and above.

(e) Enter the monthly interest rate to be charged.

(f) At the Pay Interest on Credit Balances prompt, enter N = No or Y =
Yes.

(g) Click on

to invoke the process.

The total interest amount for the current
month will be displayed.

(h) At the Interest Information prompt, click on Ok to return to the
Debtors Transaction Menu.

Note: To view the interest charges select:

4.
Transactions

1.
Date Selection

Leave Default Dates

Select Interest
Charges

Note: To print the interest charges:

E.
Transactions

Specific
Date Range

Leave Default Dates

Select
Interest Charges

Select Output to Printer or File.

---

## [224.htm]

4.
Batch Receipt Posting

This procedure does not update the Cashier
Day End Report.

Batch Receipt Posting Options:

8
Receipt Posting for Balance Brought
Forward Debtors

8
Receipt Posting for Open Item
Debtors

8
Processing a Post Dated Cheque

Receipt Posting for Balance Brought
Forward Debtors

(a) At the Account Number prompt, enter the Debtor’s Account number or
alternatively use the search facility to view and select from the current
Debtor listing.

(b) Confirm the Debtor’s details by clicking on [Yes Correct]. The Batch Posting of Payments Received screen will
be displayed.

(c) At the Date prompt, enter the date of the transaction. Press [Enter].

(d) At the Amount Due prompt, enter the total amount due. Press [Enter].

(e) At the Amount Tendered prompt, enter the amount received in respect
of the amount due from the Debtor. Press [Enter].

Note: If a settlement discount has been
taken, the amount tendered will be less than the amount due. Accpick will
automatically calculate the settlement discount amount and the settlement discount
percentage.

(f) At the Additional Reference prompt, enter any additional
information. This information will appear on the Debtor’s Statement and on the
Debtor’s Receipt Transactions Report.

(g) Enter the Receipt Number or press [Enter] to accept the default
Receipt number.

(h) Allocate ageing accordingly. Total Ageing must balance with Amount
Due and not Amount Tendered. If Ageing does not balance Accpick will prompt you
to make the correction.

(i) At the Ok to Update prompt, click on

. Accpick will
return to the Batch Posting of Payments Received screen.

(j) Continue processing all Debtor’s receipts.

(k) On completion, click

.

(l) Click

, to confirm
batch total and end the batch. Accpick will return to the Debtors Transaction Menu

Receipt Posting for Open Item Debtors

(m) At
the Account Number prompt, enter the Debtor’s account number or alternatively use
the search facility to view and select from the current Debtor listing.

(n) Confirm the Debtor’s details by clicking on [Yes Correct]. The Open Item Receipt screen will appear in the top
right hand corner.

(o) At the Date prompt, enter the Date.

(p) At the Amount Paid prompt, enter the actual amount received from the
Debtor.

(q) At the Receipt number request, enter the receipt number. Accpick automatically
allocates receipt numbers in a consecutive sequence. Should you repeat a receipt
number the following screen will appear:

(r) Confirm Open Item Allocation, by clicking on [OK]. The Open Item Payment Allocation screen will be displayed
detailing all unallocated transactions making up the amount due.

(s) To allocate payment, use the [á] and [â] arrows to move each of the
transactions to be paid / allocated to the top of the transaction listing.
Alternatively, click on

to find a specific transaction.

(t) When the selected transaction is at the top of the transaction
listing, click on

to allocate payment against the transaction.

(u) At the amount Paid prompt, enter the amount received. Press [Enter].

(v) At the Settlement Discount prompt, enter the settlement discount
amount, if any. Press [Enter].

Note:
Full Payment [*] vs Part Payment:

If the Balance due is being paid in FULL:
Note that after you have entered the amount paid and the settlement discount amount,
a * is displayed alongside the entry indicating that this has been settled in
full. This entry will cease to appear in subsequent payment allocations leaving
only the unallocated entries in the allocation screen.

If only part of the Balance due is being
paid: Enter the value of the part payment being paid in the Amount Paid
field, press enter through the Settlement Discount field. (No settlement
Discount on part payments).  Note, no * appears alongside the entry and the
entry will reappear in subsequent allocation screens.

(w) When all transactions making up the receipt have been allocated,
click on

.

(x) At the Allocate Payment prompt, click on

.

(y) Continue processing all Debtor’s receipts.

(z) On completion, click

.

(aa)
Click on

, to confirm
batch total and end the batch.

(bb)
Accpick will return to the Debtors
Transaction Menu.

Processing a Post Dated Cheque (PDC’s)

The PDC facility is for information
purposes only. i.e. PDC’s are NOT automatically credited to the bank or the
debtor’s account on due date.

PDC’s for tomorrow will print on today’s
final Day End report and clear as a reminder to process as a normal receipt.

To
process PDC for information purposes:

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view and select from the current
Debtor listing. The Debtor’s details will be displayed.

(b) Confirm the Debtor’s details by clicking [Yes Correct].

(c) At the Date prompt, press the [Page
Down] key.

(d) At the prompts, enter the cheque date and the cheque amount.

(e) At the Confirmation prompt, click on [Yes]

---

## [225.htm]

5.
Cancel / Remove PDC

(a) At the Cancel/Remove Post Dated Cheque entry screen, use the

and

arrows keys to move the cheque that needs to
be cancelled or removed to the top of the listing. Alternatively, click on

to locate by account name.

(b) When the selected cheque is at the top of the listing, click on

to cancel/remove the post dated cheque.

(c) Confirm deletion by clicking on

.

(d) Click on

to return to Debtors Transaction Menu.

---


# 2.3 Debtors - Enquiries


## [231.htm]

1.
Individual Account

Individual Account Enquiry options:

8
Current vs Archive Enquiries

8
Balance Brought Forward Debtors

8
Open Item Debtors

Current vs Archive Enquiries

On the Enquiries Menu, the Data Status
window will indicate from which directory the enquiries will be made.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories.

Balance Brought Forward Debtor

(a) At the Account Number prompt, enter the Debtor’s Account number or
use the search facility to view and select from the current Debtor listing.

(b)

displays the Debtor’s balance from Current to
180 days.

(c)

displays the Debtor’s Sales Balance per month
and Year to Date.

(d)

displays a Debtor’s transaction history which
will include the total balance brought forward, all current transaction entries
and the closing balance.

(e)

enables a transaction search by transaction
number.

(f)

displays the transaction details for the line
item at the top of the listing. Select format to view:

(g)

enables the insertion of an order number and/or
a vat number.

(h)

prints the transaction screen.

(i) Click on

to view another Debtor’s Balance.

(j) Click on

to return to the Debtor’s Enquiry Menu.

Open Item Debtor

(a) In addition to the above,

displays a listing of all unmatched Open Item
transactions by Type, Transaction Number, Date, Balance Due and Ageing.

(b)

displays the Debtor’s Opening Balance.

(c)

enables the a transaction search by transaction
number.

(d)

displays the Debtor’s transaction history.

(e)

prints a listing of all unmatched
transactions.

(f)

to toggle between Ageing and Balance Due.

(g) Click on

to return to the Main Debtor’s Enquiry Menu.

---

## [232.htm]

2.
Total Debtors Summary

(Age Analysis)

Total Debtors Summary Options:

8
Weekly or Monthly Age Analysis

8
Control Enquiry

Weekly or Monthly Age Analysis

(a) Select Summary Options.

Weekly Age Analysis:

(b) At the Report Date prompt, enter the report date.

(c) At the Sequence prompt, enter sequence listing options:                                   A
= alphabetically by account name,

N = numerically by
account number

(d) At the Area/Salesman prompt, enter the Area/Salesman number.

(e) At the List if no Transactions prompt, enter [Y] to list all debtors
with zero balance or [N] to only list debtors with balances.

Accpick will extract the Debtor’s balances
and display the Age Analysis by week.

(f) Press [Escape] to return to the Debtors Enquiry Menu.

Monthly Age Analysis

(a) At the Sequence prompt, enter sequence listing options:                                   A
= alphabetically by account name,

N = numerically by
account number

(b) At the Skip Zero Balances prompt, enter [Y] to list all debtors with
zero balance or [N] to only list debtors with balances.

(c) At the Area/Salesman prompt, enter the Area/Salesman number.

Accpick will extract the Debtor’s balances
and display the Age Analysis by month.

(d) Click on

to view Debtor Summary by Account Number, Account
Name or Total Due.

(e) Click on

to view total due for each ageing period.

(f) Select option to view Age Analysis again or to print a Summary Print
or a list of Inactive Debtors.

(g) Click on

to return to Debtors’ Enquiry Menu.

Control Enquiry

(a) Accpick will extract and display the Control Totals.

(b) Click on

to print Debtors Control.

(c) At the Date prompt, enter the date to print on the report.

(d) Click on

to return to Debtors’ Enquiry Menu.

---

## [233.htm]

3.
Top Accounts

(a) At the Debtors Account Performance Menu, select the required options
from the Menu box. Press [Enter] through each option.

or, left click on

to accept the default options.

Result:
A Debtors’ Account Performance Report will appear
on the screen listing your debtors’ performance.

(b) Click on

to print the Top Accounts report or * to
export this report to a CSV file.

(c) Click on

to return to the Debtor’s Enquiry Menu.

---

## [234.htm]

4.
Transactions

Transactions Options:

8
Date Selection

8
Gross Profit

8
Search

8
Daily Totals

8
Cashup Details

1. Date Selection

Automatically
Defaults to Current Period.

Accpick automatically defaults to the earliest and
latest dates for which there are transactions in the Current period.

Archive
Periods

To access archive periods, use the Quick
Function facility at the top of the screen to select an archive month. Accpick
will default to the earliest and latest date for which there are transactions
in the selected month.

(a) At the Start and End Date prompts enter the required dates or leave
the default dates.

(b) Press

to select entry types for enquiry:

The system displays all transactions by
Type, Transaction Number, Date, Transaction Details, Sub Total, Vat Amount and
Total Amount.

(c)

to view listing by Transaction Number,
Transaction Date, Transaction Details or Value.

to export data to a .csv file.

to view selected transaction details.

to view transaction totals.

to print listing with option to print

Detailed listing or Totals Only listing.

(d) Use the Return or

followed by [Escape] to return to the Debtor’s
Enquiry Menu.

2. Gross Profit

(a) At the Start and Stop Transaction Number prompts, enter the
transaction number or press [Enter] to accept the default numbers.

(b) At the Include Cash Transactions prompt, enter Yes or No.

(c) At the Specific Salesman/Area prompt, enter Yes or No. If Yes, enter
the Salesman/Area number.

The system will display Transaction Details,
Date, Account Name, Net Value, Profit Value and Gross Profit % per Transaction.

(d)

to view selected transaction details.

to print listing.

(e) Click on

to return to the Debtors Enquiry Menu.

3. Search

Search Criteria:           By 1st Delivery Line
Details

By
Transaction Number

1st Delivery Line Details

(a) Select search criteria – First Occurrence or List All.

(b) At the Delivery Details prompt, enter the first delivery line
details.

The system will display all transactions
matching the selected delivery line details.

(c) Use

and

to navigate through the listing.

to view selected transaction’s details.

to print listing.

(d) Click on

to return to the Debtors Enquiry Menu.

Transaction Number

(a) At the Transaction Number prompt, enter the transaction number.

The system will display all transactions
matching the selected transaction number.

Note: Should not have duplicate transaction
numbers.

(b) Use

and

to navigate through the listing.

to view selected transaction’s details.

to print listing.

(c) Click on

to return to the Debtors Enquiry Menu.

4. Daily Totals

The system will display Daily Transaction
Totals by Total Sales, Total Returns and percentage value of Total Sales.

to print listing to printer or export to CSV
file.

to view Gross Profit Value and Percentage.

to return to the Debtors Enquiry Menu.

5. Cashup Details

The system will display Daily Cashup Totals
by Date, Time, Cash, Cheque, Voucher, Speedpoint, Rounding, Abandoned,
Invoices, Credit Notes, Cash Sales, Cash Returns, Receipts on Account, Payouts,
New Laybyes, Laybye Receipts and Cancelled Laybyes.

to print listing.

to return to the Debtors Enquiry Menu.

---

## [235.htm]

5.
Sales Departments

View month-by-month performance of
selected Sales Departments.

(a) At the Department Number Prompt, enter the Department number or use
the search facility to view and selected from the Department listing. To view
total for ALL Departments, press the page down key at the department prompt.

(b) The Sales Totals with the proportionate % of the total sales ratio
will be displayed for the selected department.

(c) Use the

facility to display a graphical
representation of the data.

(d) Click on

to return to the Debtors Enquiry Menu.

---

## [237.htm]

7.
Post Dated Cheque Listing

(a) Select Order of Listing:

(b) Result: The Post Dated Cheque Listing will be displayed.

(c) Use the

and

keys to navigate through the Listing.

(d) Click on

to Print Listing.

(e) Click on

to return to the Debtors Enquiry Menu.

---

## [238.htm]

8.
Account Sales History

(a) At the Start and End Date prompts enter the selected dates or press
[Enter] to the accept default dates.

(b) At the Account Number prompt, prompt, enter the Debtor’s account
number or alternatively use the search facility to view the current Debtor
listing.

The
system will display the sales transactions for the selected Debtor by Date,
Stock Item, Quantity, Cost Price, Selling Price and Gross Profit.

(c) Use

and

to navigate through the listing.

to view sales totals.

to print listing.

(d) Click on

to return to the Debtors Enquiry Menu.

---


# 3. Stock Control - top level


## [34.htm]

Reports

On the Stock Control Reports Menu, the Data
Status Window will indicate from which directory the reports will be
extracted.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories.

For reports to print, the printer needs to
be on-line.

The following reports are available for
printing:

Reports

Report
Options

A. Stock Details

List Stock Details by:

1.Department

2.Supplier

3.Code
Range

4.Descriptor

5.Contracts

Select Report Options:

Start at and End At Codes for Department,

Supplier and Stock

Cost Price – Last / Ave/ Neither.

Selling Price – 1/2/3/All/Special/Future

Inclusive/Exclusive of Vat

New Page per Depart/Supplier Y/N

Print Markup and GP % Y/N

Include Supplier Name Y/N

Which Codes – Own / Supplier/Both

Which stock Items – All/Only those with Quantities

Select sort order options by:

Description

Stock Code

Supplier Code

B. Stock Take Forms

Select Report Format:

1.Department

2.Supplier

3.Code Range

4.Descriptor

5.Bin Number

Select Report Options:

Start and End Ranges for Departments, Suppliers and Stock Codes

Space between line

Active /Every Item A/E

New Page / Department Y/N

Select sort order options:

Description

Stock Code

Supplier Code

C. Stock Transactions

Select Report Format:

1. Detailed

2. Total Quantities – by
Supplier or Department

3. Special Deals – Detailed or
Consolidated

4. Stock Adjustments – Quantity or Price

Select Report Options:

Start and End Dates

Start and End Codes

Detailed or Totals Only

Select possible report formats from the listing.

D. Stock Valuation

Select Valuation Options:

1.Actual Quantity on Hand

2.Quantity Counted

Select Sort Options:

1. Department

2. Stock Code

3. Description

4. Supplier

5. Bin #

3. All Values i.e. on Hand, On
Jobs, Laybyes and RFC’s - department range for Detailed or Totals only.

Select Report Options:

Print Zero Holding Y/N

Start at and End at Range for Department, Stock Code, Supplier and Bin
Number.

Date to print on Report

New Page per Dept Y/N

E. Stock Variance

Select Report Order:

1. Department

2. Supplier

3. Code
Range

4. Description

5. Bin #

Select Report Options:

Costing Method – Last/
Average/ Selling Price 1/2/3

Print Items with Quantity on Hand but not yet           counted

Date on Report.

Select Sort Order Options:

Department

Department + Code

Department +  Supplier Code

Department + Supplier Number + Description

Department + Description

F. Slow Movers

Select Report Options:

Enter Date for Last Sale Search

Start At and End At Range for Department and           Supplier

Print if Quantity on Hand is Zero Y/N

Print in Code or Description order C/D

Consider Date Last Purchased Y/N

G. Re-Order

Select Re-order Options:

1. Items Below Re-Order

2. Historiccal Statistics

1. Items Below Re-order Level

Select Supplier Type –
Preferred or Last

Press [Page Down] at the Supplier Number to select           order by Description, Stock Code, Supplier           Code or Department

Ignore items with Zero Quantity on Hand Y/N

Ignore Items where Quantity on Hand = re-order           level Y/N

Consider Sales and Purchase Order Quantity.

Date on Report

2. Historical Statistics.

Select by:

1. Supplier

2. Department

Ignore Non Active Items Y/N

Number of Lines between

Report Options:

4 Month Sales

3 Month Sales + Average Sales + recommended re-order

12 Month Sales Values

H. Gross Profit

Select Report Format:

1. Detailed – for selected Department Range

2. Totals Only – Current
or for Past 12 months,

Include Cost Column Y/N

3. Department and Supplier – Detailed / Totals

I. Stock Received /
Returned

Received / Returned Options:

1. By Date

Start and End Dates
Range

Report Type: Received or Returned

Report Type: Detailed or Totals Only

For Specific Supplier (Y/N)

Transaction Number to Print: Internal GRN Number or Supplier Invoice Number.

2. By Department

Received/Returned, Print to Printer or File

3. By Supplier and Department

Net purchases - Detailed
or Totals only

Print to Printer or File

J. Sales Trends

Report Format:

1. By Department

2. By Supplier

3. By Code
Range

Select Report Options:

Select required range

Date on Report

Report based on Quantity, Value or Profit.

K. Department Analysis

Report lists
sales for the month and % of total sales

Report Options:

Select Department Range

Date to print on Report

Print Zero Department Sales (Y/N)

L. Salesman / Area

Report Format:

1. Year – to – Date

2. Detailed Analysis:

Report Options:

For selected area and dates

Detailed or Totals Only

Sort and Total by Department

Option to include GP

Cash/Account/Both

---


# 3.1 Stock Control - Maintenance


## [311.htm]

1.
Maintain Stock Item(s)

Maintain Stock Items Options:

8
Preparation of Creditors
Accounts

8
Creating Sales Departments

8
Stock Item Maintenance

Preparation of Creditors Accounts:

It is advisable to create the Creditors accounts
maintenance

(* Please refer to Creditors Maintenance) and Sales Departments, BEFORE
preparing the stock file.

1. Creating Sales Departments

(a) From the Main Menu, select

(b) From the Stock Control Menu, select

(c) From the Maintenance Menu, select 4. Sales Depts

(d) At the Department Number prompt, enter a new Department number.
Press [Enter]

(e) At the Department Name prompt, enter a description. Press [Enter].

(f) At the Insertion prompt, click on

.

(g) Click on

and return to the Stock Control Maintenance
Menu.

Stock Item Maintenance

(a)
At the Stock Items Maintenance
screen, the system will prompt for the following information:

Prompt

Action

Stock Code

Enter a 1-13
alpha numeric number.

Item Description

Department Number

Enter a valid
sales department number to which sales of this item will be categorised.  Use the select facility to view and select
from the current Sales Department listing.

Tax Code

Enter the tax
code applicable to this stock item. i.e.

1 = 14%

2. = 0%.

Accpick displays
the default tax code:

1 = 14%.

Re-order Quantity

Enter the level
at which , or below which, the stock code is to appear on the re-order
report.

Supplier Number

Enter a Supplier
number or use the select facility to view and select from the current
Supplier listing.

Default Selling
Quantity

Accpick defaults
to 1.

Automatic Returns:

May be set to -1 when the stock item is an automatic stock return e.g. an
empty bottle in a bottle store.

Allow Negative
Quantities

If No is
selected, Accpick will not allow a stock item with zero quantity on hand to
be processed at Point of Sale.

Supplier Code

Enter the
Supplier’s re-order number or stock code.

Cost Price

Enter the cost
price per unit exclusive of vat.

Maximum Discount
% Allowed

Enter the maximum
discount allowed on the stock item when processed at Point of Sale.

Mark-Up%

Enter the desired
Mark-up % on each of the selected price levels. This results in an automatic
recommended selling price. This is a recommendation only. The selling price
can be amended by the operator as necessary. The Mark-Up % will be adjusted
accordingly.

(b) Click on

to save the stock item’s information.

(c) At the save prompt, enter:

Yes/ No to save

Count    to enter quantity on hand for this new           stock item

Multi      to copy code to multiple companies automatically

Repeat  to repeat the information for the next stock item                       because it has almost identical
information to the                     current
stock item.

Note: The
C and M functions only apply at initial stock capture.

will appear on the top right hand corner when the
system recognises an entry as a new stock item.

will appear on the top right hand corner when
the system recognises an existing stock code.

To Delete
a Stock Item once the Item is displayed:
Press Page Down key.
Accpick only allows a stock item to be deleted when there is no stock on hand,
nor any stock movement for the current period.

(d) Click on

to return to the Stock Control Maintenance
Menu.

---

## [312.htm]

2.
Special Deal Maintenance

Special Deal Maintenance allows the
creation of a “special price file” for price changes for a specified period of
time.

Special Deal Maintenance Options:

8
1. Individual Stock Items

8
2. Entire Departments

1. Individual Stock Items

(a) At the Stock Code prompt, enter the stock code or alternatively use
the select facility to view the current Stock Code listing. The Stock Code
details will be displayed.

(b) At the Cost Price prompt, enter the “special cost price”

(c) At the Special Start and End Dates prompts, enter the period for
which the special deal will run.

(d) At the Mark-up % prompt, enter the mark-up percentage amounts.  The recommended Selling prices will
automatically be displayed; where these are amended the mark up % amounts will
automatically be adjusted.

(e) At the Save prompt, click on

.

(f) Click on

to return to the Stock Control Maintenance
Menu.

2. Entire Departments

Note: It is recommended that a backup be done
prior to this process.

(a)
At the Department listing
select a department to which the “special pricing” will apply.

(b)
At the Increase / Decrease prompt,
enter + to increase all prices or – to decrease all prices.

(c)
At the Percentage / Rand Value
prompt, enter P to adjust all prices by a % value or R to adjust all prices by
a rand value.

(d)
At the Amount prompt, enter the
% amount or rand value amount that the prices have to be adjusted by depending
on the selection above.

(e)
At the Select Sales Price level
prompt, enter the Sales price levels to which this special deal applies. 1.2.3
for Levels 1,2,3 or 9 for ALL levels.

(f)
At the Special Start and End
Dates prompts, enter the period for which the special deal will run.

(g) At the Continue prompt, click on

to confirm the adjustment.

(h) Click on

to return to the Stock Control Maintenance
Menu.

---

## [313.htm]

3.
Prices

Price Maintenance Options:

8
1. Individual Stock Items

8
2. Range of Stock Items

By
Department

By
Supplier

8
3. Future Pricing

Set
and Maintain

Update
and Print

8
4. Set Maximum Discount

By
Department

By
Supplier

8
5. View Maximum Discounts

1. Individual Stock Items

(a) At the Stock Code prompt, enter the stock code or alternatively use
the select facility to view and select from the current Stock listing. The
Stock details will be displayed.

(b) Accpick allows adjustments to be made to the Cost Price, Mark Up%
amounts and the Selling Prices of individual stock items. Make the necessary
adjustments to the prices where applicable by clicking on the field and
inserting the new price/s.

(c) At the Save prompt, enter Y.
Press [Enter].

(d) Click on

to return to the Stock Control Maintenance
Menu.

2. Range of Items

By Department:

(a)
At the Department listing
select a department for which price adjustments need to be made.

(b)
At the Increase / Decrease
prompt, enter + to increase all prices or – to decrease all prices. Press [Enter].

(c)
At the Percentage / Rand Value
prompt, enter P to adjust all prices
by a % value or R to adjust all
prices by a rand value. Press [Enter].

(d)
At the Cost or Selling Price
prompt, enter C to adjust all Cost
Prices or S to adjust all Selling
Prices. Press [Enter].

(e)
At the Amount prompt, enter the
% amount or rand value amount that the prices have to be adjusted by depending
on the selection above. Press [Enter].

(f)
At the Select Sales Price level
prompt, enter the Sales Price levels to which the adjustments apply. 1.2.3 for Levels 1,2,3 or 9 for ALL levels. Press [Enter].

(g) At the Continue prompt, click on

to confirm the price adjustment/s.

(h) Accpick will update the prices.

(i) Click on

to return to the Stock Control Maintenance
Menu.

By Supplier:

(a)
At the Creditor listing select
a Creditor for which price adjustments need to be made.

(b) At the Account Options prompt, click on [Yes Correct].

(c)
At the Increase / Decrease
prompt, enter + to increase all prices
or – to decrease all prices. Press [Enter].

(d)
At the Percentage / Rand Value
prompt, enter P to adjust all prices
by a % value or R to adjust all
prices by a rand value.

(e)
At the Cost or Selling Price
prompt, enter C to adjust all Cost
Prices or S to adjust all Selling
Prices. Press [Enter].

(f)
At the Amount prompt, enter the
% amount or rand value amount that the prices have to be adjusted by depending
on the selection above. Press [Enter].

(g)
At the Select Sales Price level
prompt, enter the Sales Price levels to which the adjustments apply. 1.2.3 for Levels 1,2,3 or 9 for ALL levels. Press [Enter].

(h) At the Continue prompt, click on

to confirm the price adjustment/s.

(i) Accpick will update the prices.

(j) Click on

to return to the Stock Control Maintenance
Menu.

Note: Mark up % is not automatically
adjusted. Re-index your data in order that the % markup may be adjusted by
selecting:

,

Current Month

5. All Data

Re-indexing is a
single user operation.

3 Future Pricing

Accpick allows future prices to be set and then
updated on selected stock items.  Accpick
automatically updates the future prices for the following day when Day End
procedures are run. A list of the price changes may be printed. Where Day End
is not normally processed, use the “Update” facility (see further).

Set and Maintain Future Prices:

(a)
At the Stock Code prompt, enter
the stock code or alternatively use the select facility to view the current
Stock Code listing. The Stock Code details will be displayed.

(b) At the Cost Price prompt, enter the cost price. Press [Enter].

(c) At the Future Start Date prompt, enter the date from which the new
prices are effective.

(d) At the Mark-up % prompt, enter the mark-up percentage amounts.  The recommended Selling prices will
automatically be displayed; where these are amended the mark up % amounts will
automatically be adjusted.

(e) At the Save prompt, click on

.

(f) Click on

to return to the Stock Control Maintenance
Menu.

Update and Print Future Prices:

Select the Update option to automatically
update the current stock file with the selling prices prepared in the Set and
Maintain section above.

In Set and Maintain where the Future Start
Date is set at 01/06/06, then the update facility will be for Prices dated
later than 31/05/06 i.e. one day prior.

Set and Maintain Facility:

Update Facility:

4. Set Maximum Discount

By Department:

(a)
At the Department listing
select a department for which maximum discounts need to be set.

(b)
At the Maximum Discount %
prompt, enter the percentage amount. Press [Enter].

(c) At the Continue prompt, click on

to confirm the discount adjustment/s.

(d) Accpick will update the discount %.

(e) Click on

to return to the Stock Control Maintenance
Menu.

By Supplier:

(a)
At the Creditor listing select
a Creditor for which price adjustments need to be made.

(b) At the Account Options prompt, click on [Yes Correct].

(c) At the Maximum Discount % prompt, enter the percentage amount. Press
[Enter].

(d) At the Specific Department prompt, enter Y/N.

(e) Yes – prompts for the specific department number.

(f) At the Continue prompt, click on

to confirm the discount adjustment/s.

(g) Accpick will update the discount %.

(h) Click on

to return to the Stock Control Maintenance
Menu.

5. View Maximum Discounts per Supplier

(a)
At the Supplier prompt, enter
the supplier number or alternatively use the select facility to view and select
from the Supplier listing.

(b)
At the Department prompt, enter
Yes or No for a specific department. If Yes , select the required
department from the listing.

(c)
Maximum Discount Settings for
the selected Supplier will be displayed.

---

## [314.htm]

4.
Sales Departments

Create
a New Sales Department.

(a) At the Sales Department File Maintenance screen, use the search
facility to view your current Sales Department listing. These are displayed in
alphabetical order; right click on “Dept” to display in numerical order (1-99).
Decide on a Department number and click/press [Escape] twice. Enter the new
Department number and press [Enter].

(b) At the Sales Department Name prompt, type in the new Department
name. Press [Enter].

(c) At the Insertion Option prompt, click on

.

(d) Click

to return to the Stock Control Maintenance
Menu.

Modify a Sales Department.

(a)
At the Sales Department number
prompt, enter the Sales Department number requiring modification or, use the
search facility to view and select from your current Sales Department Listing.

(b)
Make the correcting
adjustments. Press [Enter].

(c)
At the Replacement request,
click on

.

(d)
Click on

to return to the Stock Control Maintenance
Menu.

---

## [315.htm]

5.
Sales Areas

Add a New Sales Area/Salesman

(a) At the Sales Area / Salesman Number prompt, enter a new Sales Area /
Salesman number or alternatively, use the search facility to view your current
Sales Area / Salesman Listing. These are displayed numerically (1-99). Right
click to display alphabetically. Click/Press [Escape] twice.

(b) At the Number prompt, press the [Page
Down] key to allocate the next available Sales Area / Salesman number or
enter the number you have selected and press [Enter].

(c) At the Name prompt, type in the new Sales Area / Salesman name.
Press [Enter].

(d) At the Insertion Option prompt, click on

.

(e) Click on

to return to the Stock Control Maintenance
Menu.

Modify an Existing Sales Area/Salesman

(a)
At the number prompt, enter the
Sales Area / Salesman number requiring modification or, use the search facility
to view and select from the current Sales Area / Salesman Listing.

(b) Make the correcting adjustments.

(c) At the Replacement request, click on

.

(d) Press

to return to the Stock Control Maintenance
Menu.

---

## [316.htm]

6.
One-Touch Look-Up Keys

This facility allows one to link the
alphabet keys on the keyboard to stock codes for fast access at POS.

Customisation
only.

Note: Use Capital Letters only.

Set up

(a) Press the shift (for capital) + apha key (e.g. A).

(b) At the Stock Code Prompt, enter the stock code or alternatively use
the search facility to view and select from the current Stock Code listing.

(c) At the Save prompt, enter Yes. Press [Enter].

To view current alpha settings:

Press [?] to display current alpha settings.

To clear all current alpha settings:

Press [-] to clear all alpha settings.

Fast Access at POS:

(a)
Instead on clicking on INSERT to
insert line items, enter your fast access key and the stock details linked to
the fast access key will be displayed.

(b)
Continue entering the
transaction details.

---

## [317.htm]

7.
Contract Pricing

Contract Pricing enables Debtors to be
linked to contract prices on:

8
specific stock code(s), i.e.
per line item

8
specific % discount or markup on
selected departments

8
specific % discount on sales
related to specific suppliers

8
specific % discount on specific
supplier for selected department(s)

The Contract Price will automatically be
displayed at POS.  The Contract Price
takes priority over all master file prices and special-deal pricing.

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view the current Debtor listing.

(b) At the Fixed Pricing prompt, enter Yes or No.

Fixed Pricing

If set to Yes, the
POS routines may NOT attract lower or higher discounts than those set in the
contract pricing for the customer.

Setting a Price per Line Item (Specific Stock Code)

(a)

selects the method for pricing:

Select as required.

Set
Actual Price:

(b) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle the
stock search order by Stock Code, Supplier Code or Stock Description and select
required item.

Calculate
Price using Cost, Mup% and GP%

Select Stock Code or search by description
as indicated above

Enter the Mup% - the GP% will automatically appear.

Amend the Selling Price if required and save.

(c) At the Exclusive Price prompt, enter the contract price.

Specific Discount/Markup on Selected
Department:

to insert discount % or markup % for specific
Department.

Specific Discount/Markup on Sales from
a Specific Supplier:

to insert discount % or markup % for selected
Supplier

Specific Discount/Markup on Specific
Supplier for Selected Department:

to select Supplier and Department followed by discount
% or markup %

Options exist for :

to adjust contract price.

to print contract listing.

to locate contract item by Code/Description.

to delete contract price.

---

## [318.htm]

8.
Shrink Wraps

Shrink Wrap Options:

8
Shrink Wraps Maintenance

8
View / Print Shrink Wrap
Relationships

Where items are bought in bulk and sold in
shrinks or units, this facility creates the relationship between the “bulk” and
the “shrinks”.

A stock code must exist for each type of
unit relating to the bulk:

Bulk             000-003      Bic Pens 48Pack

Shrink          000-005      Bic Pens Single

Shrink Wrap Maintenance

(a) At the Shrink Pack Code prompt, enter the shrink pack stock code or
alternatively, use the select facility to view and select from the current
stock listing.

(b) At the Bulk Pack Code prompt, enter the bulk pack stock code or
alternatively, use the select facility to view and select from the current
stock listing.

(c) At the quantity of Shrink in Bulk prompt, enter the quantity of
shrinks in the bulk.. To calculate quantity: divide the bulk quantity (48) by
the shrink quantity (1) .g. 48 / 1 = 48

(d) At the Save prompt, click on Yes.

(e) Click on

to return to the Stock Control Maintenance
Menu.

View / Print Shrink Wrap Relationship

To view / print shrink wrap relationships
select:

,

,

D.
Shrink / Bulks

1.
Relationship

---

## [319.htm]

9.
Packs / Bundles

Packs / Bundles Options:

8
Packs / Bundles Maintenance

8
View Compositions of Packs /
Bundles

Where items are grouped together for resale
a “finished product” or “recipe” file is created.  Any combination of stock items and quantities
or part quantities thereof may form part of the finished product
maintenance.  Stock codes must exist for
each of the “ingredients”.

Packs / Bundles Maintenance

To
Create a New Pack/Bundle:

Step 1         Finished Product Maintenance

Create
Stock Code for the finished product.

Step 2         Ingredient Maintenance

Insert
stock items – “ingredients” – making up the                     finished
product.

Finished Product Maintenance

(a) At the Stock Control Maintenance Menu, select                     9.
Packs/Bundles

(b) At the Stock Code prompt, enter the stock code to be allocated to
the finished product.

(c) At the Description prompt, enter the description of the finished
product e.g. Ration Pack #1

(d) At the Department prompt, enter the Department number or
alternatively use the select facility to view and select from the current Department
listing.

(e) At the Tax Code prompt, enter the tax code.  Defaults to Tax Code 1.

(f) At the Default Selling Quantity, enter the quantity. Defaults to 1.

(g) At the Supplier Number prompt, enter the Supplier called Internal. (Create
a supplier called “Internal” in Creditors.)

(h) At the Allow Negative Quantity prompt, enter Yes or No.

(i) At the Maximum Discount % Allowed prompt, enter the discount
percentage or alternatively leave blank if no block is required.

Step 2: Ingredient Maintenance

(j) Click on

to insert stock item codes required in the
finished product.

(k) Complete the line item details by entering the stock code, stock
description and quantity. Select stock codes from the Stock Code listing by
pressing the [Page Down] key at the description prompt.

(l) Repeat for all stock items making up the finished product.  The value of each “ingredient” and total cost
of the product is displayed.

(m) Click on the

to end ingredient maintenance.

(n) The cost price of the finished product is displayed.

(o) At the Update prompt, click on Yes to update.

(p) At the Markup % and Selling Price prompts enter the required values.

(q) At the Save prompt, click on Yes.

(r) Click on

to return to the Stock Control Maintenance
Menu.

View Packs / Bundles

To view composition of a pack / bundle,
select:

,

, C. Packs/Bundles ,

1. Composition

Note: See

,

,

5. Manufacture Items  for creation and updating of Finished goods.

---


# 3.2 Stock Control - Transactions


## [321.htm]

1.
Incoming Stock

Note: Updates Stock only.

To Update Stock and Creditors use the Creditors Transaction
Receiving Stock Items Option.

(a) At the Invoice Date prompt, enter the invoice date. Suggest date is
entered as date on which goods are received into stock. Press [Enter].

(b) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat.  Press [Enter]
to accept the default selection.

(c) At the Invoice Number prompt, enter the Supplier’s invoice number.

(d) At the Additional Reference prompt, enter any additional
information. Suggestion: Enter Supplier’s Name

(e) At the Goods Received Note screen, click on

to insert the transaction lines on the
Supplier’s invoice.

(f) The stock may be captured by:

1.       Stock
Code

2.       Description.

(g) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle the
stock search order by Stock Code, Supplier Code or Stock Description.

Note: Once the Stock Code and Stock
Description have been entered an information window is displayed on the right
hand side listing the Stock Item’s current quantity on hand, monthly sales to
date and the Supplier’s Code.

(h) At the Quantity prompt, enter the number of units received.

(i) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be
overwritten.  Press [Enter] to accept the default tax status.

(j) Accpick will automatically calculate the unit cost inclusive or
exclusive of vat depending on the option selected above.  If the Cost Price per Unit displayed is
different to the invoice price, enter the new cost price at the Cost prompt.
Press [Enter].

Note: New Cost Prices.

When the System registers a new cost price
and the Supplier’s Maintenance option: Update Selling Price on Stock
Receipts, is set to YES, an Update Selling Price prompt will be displayed.

When NOW is selected, a Pricing Update
screen is displayed with the new cost price, the current % markup for Selling
Price 1,2 and 3. Adjustments to the markup % results in adjustments to the
relative Selling Prices and vice versa. Press [Enter] to return to the Goods
Received Note screen.

(k) When all the line items have been entered and the total quantity
received, total vat and total inclusive amount on the Goods Received Note
balances with the Supplier’s invoice, click on

to update the Goods Received Note.

(l) If the Goods Received Note and the Supplier’s Invoice do not
balance, use the arrow keys to move the incorrect transaction line/s to the top
of the listing. Click on

or

to make the correcting adjustments. Once
correct, click on

to update the Goods Received Note.

(m) The Update Options Menu will be displayed:

Note: Surcharge.

e.g. Transport Charges

This option allows the Supplier’s surcharge to be apportioned to all line items
and printed on the Goods Received Note. This amount is exclusive of vat.

(n) Click on

to update the transaction and display the
Print Options Menu.

(o) At the Print Options Menu, click on the required print options:

Selling Price

Selling Price, Markup and Gross
Profit %

Selling Price and Gross Profit
Value

No print

(p) The Goods Received Note entry screen will be displayed.  Continue entering further invoices by
entering the invoice date.

(q) Once completed click on

to return to the Stock Control Transaction
Menu.

---

## [322.htm]

2.
Stock Returns

Note: Updates Stock only

(a) At the Document Date prompt, enter the date. Press [Enter].

(b) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat.  Press [Enter]
to accept the default selection.

(c) At the Document Number prompt, enter the Supplier’s Credit Note
number.

(d) At the Additional Reference prompt, enter any additional
information.

(e) At the Goods Returned Note screen, click on

to insert the transaction line/s on the
Supplier’s Credit Note.

(f) The stock may be captured by:

1.       Stock
Code

2.       Description.

(g) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle
stock search order by Stock Code, Supplier Code or Stock Description.

Note: Once the Stock Code and Stock
Description have been entered an information window is displayed on the right
hand side listing the Stock Item’s current quantity on hand, monthly sales and
the Supplier’s Code.

(h) At the Quantity prompt, enter the number of units to be returned.

(i) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be
overwritten.  Press [Enter] to accept the default tax status.

(j) Accpick will automatically calculate the unit cost inclusive or
exclusive of vat depending on the option selected above.

(k) When all the line items have been entered and the total quantity
returned, total vat and total inclusive amount on the Goods Returned Note
balances with the Supplier’s credit note, click on

to update the Goods Returned Note.

(l) If the Goods Return Note and the Supplier’s Credit Note do not
balance, use the arrow keys to move the incorrect transaction line/s to the top
of the listing. Click on

or

to make the correcting adjustments.

(m) Once correct, click on

to update the Goods Returned Note.

(n) The Update Options Menu will be displayed:

(o) Click on

to update the transaction and display the
Print Options Menu.

(p) Accpick will update the transaction and display the print options
prompt.  Click on [Yes] to print the
Goods Returned Note.

(q) Once completed, click on

to return to the Stock Control Transaction
Menu.

---

## [323.htm]

3.
Stock Take and

4.
Stock Take - Update

Stock Take Procedure:

A       Print Stock Take Forms

B       Stock Take

C       Stock Variance Report

D       Stock Valuation – Qty Counted
(Optional)

E       Daily Backup

F        Stock Take Update

G       Stock Valuation Report – Actual Qty on                            Hand

H
Stock Adjustments Report

A     Print
Stock Take Forms

(a) Select Stock Control

(b) Select

(c) Select order:

(d) Select Report Options: e.g. by Department

Note: We suggest “Active” Items only.

(e) Select Sort order options:

B     Stock Take

(a)
Select Stock Control

.

(b) Select

.

(c) Select Stock Take Options, according to order of Stock Take Forms
printed in A.

(d) The Stock Code and Stock Item Description is displayed. At the Quantity
Counted prompt, enter then quantity counted. Press [Enter] to display the next
stock item.

(e) Repeat for all Stock items.

[Page
Down] skips stock items.

[Page
Up] to view previous stock item.

Counting from Multiple Locations:

Where there are multiple locations from
which stock quantities for a specific item are to be counted, the system allows
for this condition with the following prompt at the second and subsequent
entries:

“Previous Quantity counted = x”

“To add this quantity to quantity, press +”

“To replace with new Quantity, press [Enter]”

C     Stock Variance Report.

This will report on the quantities and
values of all items counted where the stock quantity counted is not equal to
the computer’s quantity on hand.

(a)
Select Stock Control

(b)
Select

(c)
Select Report Order, Department
Order and Sort Order.

(d)
Check report for all variances.
Make the necessary correcting adjustments:

Replacing a counted quantity with a subsequent count.

Select
Stock Control

.

Select

.

Select 5.
Individually.

Enter the
Stock Code and new quantity.

Where a
previous quantity is being overridden by a subsequent quantity prior to stock
take update, select the option prompt:

To replace with new quantity, press [Enter].

D     Print Stock Valuation of Quantity Counted
(Optional).

This is important for obtaining a Stock
Valuation where Stock Take Update is effected AFTER TRADING or where input
needs to be verified..

(a)
Select Stock Control

(b) Select

(c) Select 2. Quantity Counted.

E     Daily
Back Up

Note: Make sure ALL users have logged out of
Accpick.

Invoke the Back Up procedure by clicking on
the Accpick Backup icon on the Desktop.

F     Stock Take Update.

Replaces
the quantity on hand on the computer with the quantity counted.

This should only be effected once the final stock
variance report has been successfully extracted.

(a)
Select Stock Control

.

(b) Select 4. Stock Take - Update.

(c) Select Stock Take Options:

1. Before Trading

Where Stock Take has been performed and no
trading has taken place since the Stock Take.

The Stock Take Update will update all stock
records accessed in the stock take routine; i.e. physical stock counted becomes
the new stock-on-hand.

Reset
negative values to zero?:      Yes or No depending on your requirements. Suggest NO as these
ought to be analysed.

Set
items not counted to zero? Yes or No. Suggest No.

2. After Trading

Where stock has been performed at a
specific date, but not yet captured in the system, and there has been trading
since Stock Take.

The Stock Take Update will update all stock
records accessed in the Stock Take routine i.e. physical stock counted becomes
the new stock-on-hand at a specified
date.

Note:
Should you require a Stock Valuation of the quantity Counted this must be
printed before the AFTER TRADING UPDATE.

(a)
Select Stock Control

(b)
Select    D. Stock Valuation

(c)
Select    2. Quantity Counted

(a)
Reset negative values to zero?: Yes or No depending on your requirements.
Suggest NO as these ought to be analysed.

(b) Set items not counted to
zero?: Yes
or No. Suggest No.

(c) At the prompts, enter the first working day after stock count and
the time trading started. This will insert the stock count to just prior to the
time and date entered and re-adjusts all subsequent stock movement to arrive at
the current stock holding.

G. Print Stock Valuation Report:

,

, D. Stock Valuation

H. Print a Stock Adjustment Report:

,

, . C. Stock Transactions 4. Stock
Adjustments by Quantity

Stock Item Adjustment

This facility allows a stock take update on
a selected item without going through the process of a stock count.

All adjustments processed in this manner
report to the Stock Adjustment Report.

Select

,

.3 Item Adjustment

Note: Recommend that this procedure, as with
all Stock Take update procedures, be password controlled.

---

## [325.htm]

5.
Manufacture Item(s)

This procedure updates stock of
manufactured goods (bundle codes) and depletes the stock of the ingredient
codes.

The Packs / Bundles Listing is displayed.

(a) Locate the required Pack/Bundle using

.

(b)  Use the

and

to move the Pack / Bundle to the top of the listing.

(c) View the ingredient details:

Click

.

Press [M] to manufacture this item.

Enter quantity manufactured

Option to warn on items out of stock

Enter the Date of manufacture

Press [Escape] and [M] to confirm manufacture

Option to print list of ingredients used.

(d) Click on

to return to the Stock Control Maintenance
Menu.

(e) Details are recorded in the Stock Movement Enquiry. To view:
Select:  Stock Control

,

4. Stock Movements

---


# 3.3 Stock Control - Enquiries


## [331.htm]

1.
Individual Stock Item(s)

Current vs Archive Enquiries

On the Enquiries Menu, the Data Status
window will indicate from which directory the enquiries are being extracted.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories

Individual Stock Item Enquiry.

Individual Stock Item Enquiry will detail
the following information:

Stock Code

Stock Description

Preferred and Last Supplier

Department

Average Cost

Current Cost Price

Standard Mark up %

Selling Price – exclusive and           inclusive

Projected Gross Profit Margin.

Quantity on Hand and Value           thereof

Quantity on Sales Order and           Purchase
Order

Sales Statistics for MTD and YTD:

Sales Quantity,

Gross Profit Value

Gross Profit %

Date Stock last purchased and           last
Sold

to view previous stock item or the following
stock item as per the stock listing.

to view Current Sales Details for selected
stock code by: Date, Time, Transaction Type, Debtor, Quantity, Unit Cost Price
and Unit Selling Price.

to view purchase history of the selected stock
code by Month and Total Value.

---

## [332.htm]

2.
Stock Item History

(a) At the Stock Code prompt, enter the Stock Code or alternatively use
the search facility to view and select from the current Stock listing.

(b) At the “To and From” Date prompts, enter the required dates.
Archives are scanned for the selected dates requested.

(c) At the Sales or Purchase History prompt enter S for Sales history
and P for Purchase history.

(d) Sales

If Sales is selected, the system prompts for sales history

8 for a specific Debtor or across all Sales,

8 from a specific Salesman / Sales Area or across all                 Salesmen / Sales Areas.

(e) The Sales History for the selected stock code will be displayed by Date,
Transaction details, Customer Details, Quantity and Total Profit.

(f) Purchases

If Purchases is selected, the purchase history for the selected stock code will
be displayed by Date, Transaction Details, Supplier Details, Quantity and Unit
Cost.

(g) Use the

and

to navigate through the listings.

(h) Click on

to return to the Stock Control Enquiries Menu.

---

## [333.htm]

3.
Stock Valuation

The system prompts for:

8
Stock Valuation for Quantity on Hand or
Quantity Counted

8
Option to Scroll through the entire stock
file (S) or view totals only (T).

8
Quantity Selection: All Stock Items (A), skip
zero stock quantities (S) or view negative quantities only (N).

8
Order Selection: Where Scroll is selected,
select Code or Description order.

8
Stock Valuation for a specific Department
or for All stock items.

Scroll Stock File
Option:

Scroll
though entire stock file displays the stock holding by stock code, description,
quantity on hand, average/last cost price and value of quantity on hand.

View Totals Option:

View
Totals option displays total quantity and total value:

---

## [334.htm]

4.
Stock Movements

The system prompts for:

8
Stock Code

8

Specific
Start and End Dates.

Stock Movement Enquiry displays the Item
Description, Transaction Date, Movement Details, Transaction Number, Quantity
In, Quantity Out, Quantity Balance and Value per Unit.

Balance Brought Forward is the opening
stock balance in units, at the beginning of the month: thereafter stock balance
in chronological order:

8
Stock received via
Stock or Creditors

8
Stock returned via
Stock or Creditors

8
Stock sold

8
Sales returns

8
Stock count
updated by station number

8
Stock used in
bundle/pack number

8
Stock issued
from bulk item number

8
Stock issued to
and from lay-byes

8
Stock issued to
and from job cards

8
Stock issued to
and from RFC’s

(a) Use the

and

keys to navigate through the Listing.

(b) Use the

to find stock movement by date.

(c) Click on

to Print Listing.

(d) Click on

to return to the Stock Control Enquiry Menu.

---

## [335.htm]

5.
Stock Contribution

Stock Contribution Options:

8
Departmental Sales and Stock
Holding

8
Sales Units by Department

8
Sales Units by Supplier

Departmental Sales and Stock Holding

The system prompts for:

8
Cost (C) or
Selling Price (S) Valuation

8
Include (Y) or
Ignore (N) Negative Cost Quantities

Department Sales and Stock Holding lists
the Departments, Total Value Sold, % of Total Value Sold based on selected
reporting of (C) or (S) and, Value on Hand and % Total of Value on Hand.

(a) Click on

to navigate through the listing.

(b) Total Value Sold and Total Value on Hand are displayed at the end of
the listing.

(c) Click on

to Print Listing.

(d) Click on

to return to the Stock Control Enquiry Menu.

Sales Units by Department

Unit Sales by Department displays
Departments, Quantity Sold, Value, Gross Profit and GP%.

(e) Use the

and

keys to navigate through the listing.

(f)

to view listing by

Quantity, Gross Profit and Gross
Profit %,

Quantity, % of Total Value

Quantity, Value, Gross Profit and % of
Total Gross Profit

(g) Click on

to Print Listing.

(h)

Click on

to return to the Stock Control Enquiry Menu.

Sales Units by Supplier

Unit Sales by Supplier displays Supplier,
Quantity Sold, Value, Gross Profit and GP%.

(a)
Use the

and

keys to navigate through the listing.

(b)

to view listing by

Quantity, Value, Gross Profit
and Gross Profit %,

Quantity, Value, % of Total
Value

Quantity, Gross Profit and %
of Total Gross Profit

Quantity and % of Total
Quantity

(c) Click on

to Print Listing.

(d) Click on

to return to the Stock Control Enquiry Menu.

---

## [336.htm]

6.
Sales Trends

(a) At the Stock Code prompt, enter the Stock Code or alternatively use
the search facility to view and select from the Stock listing.

(b) The Monthly Statistics for the selected Stock Code will be displayed
showing Quantity, % of Total Quantity, Value Sold, % of Total Value, Profit and
% of Total Profit.

(c) The system will prompt for:

(d) Click on

to return to the Stock Control Enquiry Menu.

---

## [337.htm]

7.
Sales Departments

View monthly sales analysis and
year-to-date performance of selected departments.  This is a calendar month analysis.

(a) At the Department Number Prompt, enter the Department number or use
the search facility to view and selected from the Department listing. To view
total for ALL Departments, press the page down key at the department prompt.

(b) The Sales Totals with the proportionate % of the total sales ratio
will be displayed for the selected department.

(c) Use the

facility to display a graphical
representation of the data.

(d) Click on

to return to the Stock Control Enquiry Menu.

---

## [338.htm]

8.
Salesman / Area Enquiry

View month-by-month and year-to date
performance of selected Salesmen/Areas.

(a) At the Salesman Number Prompt, enter the Salesman number or use the
search facility to view and selected from the Salesman listing.

(b) The Sales Totals with the proportionate % of the total sales ratio
will be displayed for the selected Salesman.

(c) Use the

facility to display a graphical representation
of the data.

(d) Click on

to return to the Stock Control Enquiry Menu.

---

## [339.htm]

9.
Hourly Analysis

View hourly sales values for all stock

(a) At the Start and end Date prompts, enter the date range for the
selected month.

(b) An hourly analysis of stock sales is displayed showing Sales Value, %
of Total Sales, Profit and % of Total profit.

(c) The Total Sales Value, Total Profit Value and the Gross Profit for
the period is displayed on the right and side of the screen.

(d) For a graphical representation of the data click on Graph.

(e) To print, click on print.

(f) Click on

to return to the Stock Control Enquiry Menu.

---


# 3.3 Stock Control - Enquiries (extra)


## [3310.htm]

A.
Purchase History

(a) At the date prompts, enter the selected date range or alternatively
press [Enter] to accept the default dates.
Date range will default to the earliest and latest date on current
transaction file.

(b) At the Scroll / Total prompt, select S to view detailed listing or T
to view totals only.

(c) All stock purchases for the selected period will be displayed by
date, transaction number, stock item details, exclusive value, tax value and
inclusive value.  Total Purchase Values
inclusive and exclusive of tax will be displayed at the end of the listing.

(d) Click on

to print the listing.

(e) Click on

to return to the Stock Control Enquiries Menu.

---

## [3311.htm]

B.
Top Sellers

(a) At the prompts, select the required options to base sales
performance on i.e. Month, Day or Year and Value or Quantity.

(b) At the Options prompt, select the category for which to extract top
sellers - all items, a specific department or a specific supplier.

Where the “Quantity” option is selected, the
system prompts to view Quantity on Hand.

(c) A list of Top Sellers will be displayed in descending order by Stock
Code, Description, Total Sales Value for the Month, Gross Value for the Month,
Total Sales Value for the Year and Total Gross Value for the Year.

(d) At the Options prompt, click on

to view view further items down the listing or

to print the listing.

(e) At the Print Options prompt, click on the required option – no
print, print or print with quantity on hand value.

---

## [3312.htm]

C.
Packs / Bundles

(a) At the Pack / Bundle Options prompt, select the required option.

(b) 1. Composition will display the ingredient stock items making up a
specific Pack / Bundle. Click on

to view ingredient stock item listing.

(c) 2. Where Used will display all packs / bundles where a specific
stock item is located. At the Stock Code prompt, enter the ‘ingredient’ stock
code and a listing of pack / bundles using the ‘ingredient’ stock code will be
displayed.

(d) Click on

to print the listings.

(e) Click on

to return to the Stock Control Enquiries Menu.

---

## [3313.htm]

D.
Shrink Wrap / Bulk

(a) At the Shrink Options prompt, select the required option:

1. Relationship will display the quantity of shrinks in each bulk

2. Bulk Sales will display the bulk item sales history by supplier
or by department.

(b) Click on

to print the listings.

(c) Enter Start an d Stop Code Range to print.

(d) Click on

to return to the Stock Control Enquiries Menu.

---


# 4. Creditors - top level


## [44.htm]

Creditors
Reports

On the Creditor’ Reports Menu, the Data
Status Window will indicate which directory the reports will be extracted from.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories.

For reports to print, the printer is
required to be on-line.

The following reports are available for
printing:

Reports

Report Options

Report Information

1. Account
Details

Address Details: Include Postal/Delivery/None

Alphabetical or Numerical Sequence

Include Banking Details (Y/N)

Report lists all Creditors’ details.

2. Age
Analysis

Totals Summary or Detailed

Include only Account Balances or transaction details

Alphabetical or Numerical Sequence

Include Zero Balances (Y/N)

Print Last Paid and Terms Details (Y/N)

Print business account number and supplier’s banking details

Date to appear on Report

Report lists all Creditors outstanding balances
owing for the various periods according to the selected report options.

3. Remittance
Advices

Current Period or Historical Periods

Enter date to appear on statement

Print Additional Reference (Y/N)

Include Zero Balances (Y/N)

Alphabetical or numeric order

Select Start at short name/account number and Stop at short name /account
number

Report prints a remittance advice for selected suppliers.

Remittance Advices  will print for
Balance Brought Forward Creditors and Open Item Creditors

4.
Transactions

Start and End Dates

Detailed or Totals Only Report Type

Transaction Types:

- Invoices

- Payments

- Credit Notes

- Settlement                    Discounts

- Debit Journals

- Credit Journals

- All the Above

Report lists all creditor related transactions.

The system will default to the earliest and latest
date for which there are transactions

5. Expense
and Tax Reports

Reports:

1. Monthly and Tax Analysis

2. Expense Analysis – YTD

3. Detailed Transactions

4. Categories by Range

Report Criteria

Alphabetical or Numerical Sequence

Report on Zero Expenses (Y/N)

Date on Report

Start and End Expense Category Print Points

Chronological or Expense Category Order

Print to Printer or File

Print Categories by Date Range – Current or Historical.

Report lists Expense Category and Tax details by:

- month

- year-to-date

- transactions

- categories.

6. Payouts

Start and End Dates

Lists Payout details by Date and Amount.

Totals the Payouts via POS and Payout Totals via
Creditors.

---


# 4.1 Creditors - Accounts


## [411.htm]

1.
Accounts

Supplier Account Maintenance
Options

8
Adding a New Supplier

8
Modifying an Existing Supplier

8
Deleting an Existing Account

Adding
a New Supplier

(a) At the Supplier Maintenance screen, enter a new Account number at
the Account number prompt.

To select a new account number: Use the search facility to view your
current Creditor Listing or alternatively press the [Page Down] key to allocate
the next available account number or enter a series number (e.g. 500) and press
the [Page Down] key to allocate the next available account number in that
series.

(b) Add the Supplier’s account details. You will be prompted for the
following:

Name

Physical/Postal
Addresses

Telephone/Fax
Numbers

Account Type

Blank  Balance Brought Forward

O         Open Item Account

E-Mail Address

Contact Person

Our Account Number

Our account number with the supplier.
This prints on the Remittance Advice.

Update S/Pr on Stk Rec

Yes allows the
selling price to be updated when new stock is received and the cost price has
changed.

No retains the
existing selling price when new stock is received

Credit Terms

30,60 or 90 days

Prompt Payment Discount %

Capture Banking Details

Yes prompts for
Bank Name, Branch Code and Account Number.

(c) When all details have been completed, click on

.

(d) At the Save Account prompt, click on

.

(e) Click on

to return to the Creditor’s Maintenance Menu.

Modifying
an Existing Account

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the select facility to
view and select from the current Supplier listing. The Supplier’s details will
be displayed.

(b)
Make the necessary
modifications.

(c)
Click

to save modifications.

(d)
At the Save Account prompt, click
on

.

(e)
Click

to return to the Creditor’s Maintenance Menu.

Deleting an Existing Account

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the search facility to
view and select from the current Supplier listing. The Supplier’s details will
be displayed.

(b)
Click on

to delete the account.

(c)
Click on

to confirm deletion.

(d)
Click

to return to Creditors Maintenance Menu.

Note: Deletion is not permitted when:

an account has a balance, or where
transactions were posted to this account for the current month.

---

## [412.htm]

2.
Expense Categories

Expense Category Maintenance
Options:

8
Creating New Categories

8
Modifying Existing Categories

8
Deleting Existing Categories

When inserting a new category it is
advisable to refer to the standard Accpick Xcellence Chart of Accounts. This is
a numbering system that conforms to the setup requirements of the Accpick
General Ledger. Category numbers may be 1-8 digit numeric codes.

Here is a typical, very general, numbering
system:

4010

Advertising

4050

Bank Charges

4080

Computer Consumables

4120

Electricity and Water

4160

Insurance

4500

Postage

4540

Rent

4600

Salaries

4680

Security

4700

Stationery and Print

4750

Telephones

4755

Telephones - Cell

Creating
a New Expense Category

(a) Use the search facility to view your current Expense category
listing. Select a new Expense category number. Press [Escape] to return to the Expense Category File Maintenance Screen.

(b) At the Category Number prompt, enter the new Expense category
number. Press [Enter].

(c) At the Category Name prompt, enter the new category name. Press [Enter].

(d) At the Save Category prompt, click on

.

(e) Click on

and return to the Creditors Maintenance Menu.

Note: At the time of installation, you may be
issued with Expense Categories for the Creditors’ Module and the Cash Book
module. Common expenses will reflect the same category number. Further Expense
Categories which are added at a later stage in one module (e.g. Creditors) and
are common to another module (e.g. Cash Book) must be created separately in
each module using the SAME category number.

Modifying an Existing Expense Category

(a)
At the Category Number prompt,
enter the Expense category’s number or use the select facility to view and
select from your current Expense category listing.

(b) At the Category Name prompt, edit the category name. Press [Enter].

(c) At the Save Category prompt, click on

.

(d) Click on

and return to the Creditors Maintenance Menu.

Deleting
an Existing Expense Category

(a)
At the Category Number prompt,
enter the expense category’s number or use the search facility to view and select
from your current Expense category listing.

(b)  Click on

.

(c) At the Confirm Deletion prompt, click on

.

(d) Click on

and return to the Main Menu.

Note: An Expense category cannot be deleted
if there have been expenses recorded against this category.

---

## [413.htm]

3.
Outstanding Balance Capture

Outstanding Balance Capture
Options:

8
Balance Take-On – Balance
Brought Forward

8
Balance Take-On – Open Item

8
Account Category Conversion

Balance Take-On

(a) At the
Order prompt, select and enter order of entry:

A – Alphabetical Order (A – ZZZ)

N – Numerical Order as per Account Number (1 – 9999)

Note: The Balance Brought Forward Entry screen or the Open Item
Entry screen will automatically appear according to the account category that
was selected when the Supplier account was added in the Creditors Maintenance
Menu.

Balance Take-On: Balance
Brought Forward

(b) At the Ageing prompt, enter the outstanding balances from Current to
180 days. Press the [Enter] key to
move through the ageing options.

(c) At the Update prompt (Yes/No/Skip).
Enter Y.

(d) Result: You will be prompted with the next account. Continue taking
outstanding balances on.

Balance Take-On: Open Item

(a)
Click on the

button.

(b) Click on the required transaction type from the list.

(c) Enter the transaction number, the date and total amount of the
transaction.

(d) Age the transaction by selecting and entering the appropriate number
e.g. 2 = 30 days.

(e) Repeat for all outstanding transactions for this Debtor.

(f) Click on

when completed.

(g) At the Post prompt, click on

.

(h) Result: You will be prompted with the next account. Continue taking outstanding balances on.

(i) When all account balances have been processed, click on

to return to the Creditors Maintenance Menu.

Account Category Conversions

Accpick allows you to change the Supplier’s
Account Category from Open Item to Balance Brought Forward and visa versa.

Open Item to Balance Brought Forward

(a)
From the Creditors Maintenance
Menu, select 1.Accounts.

(b) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the search facility to view and select from the current
Supplier listing. The Supplier’s details will be displayed.

(c) Change the Account Category from

(O = Open Item) to

(Blank = Balance Brought Forward)

(d) Click on

.

(e) At the Save Modification prompt, click on

.

(f) At the Options prompt, click on [Yes]
to confirm conversion from Open Item to Balance Brought Forward.

(g) Click on

to return to the Creditors Maintenance Menu.

Re-index
all files in order to remove all redundant Open Item entries by selecting

from the Main Menu and

from the Utilities Menu.

Note: This
is a single user operation! Make sure all other users are out of the system.

Balance Brought Forward to Open Item

It is recommended that this be done
immediately after a month end…….. Print an Age Analysis prior to the conversion
and immediately after the conversion to ensure that balances and ageing are
correct.

(a)
From the Creditors Maintenance
Menu, select 1.Accounts.

(b) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the search facility to view and select from the current
Supplier listing. The Supplier’s details will be displayed.

(c) Change the Account Category from

(Blank = Balance Brought Forward) to

(O = Open Item).

Note: The Open Item Entry Screen will automatically
be displayed, showing the Total Outstanding Amount and the values in the ageing
groups. The Open Item entries MUST equal in value to both the total and the
ageing group.

(d) Click on

to enter all outstanding transactions.

(e) Click on

when totals are in balance.

(f) Click on

to return to the Creditors Maintenance Menu.

If Ageing is not correct the following
screen will appear:

Click on [Continue] and edit entry to correct ageing.

Click on

to return to the Creditors Maintenance Menu.

---


# 4.2 Creditors - Transactions


## [421.htm]

1.
Receiving - Stock Items

(Goods Received Note)

(This option updates Stock, the Supplier’s Balance and Vat Controls
simultaneously.)

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the select option to view and select from the current
Supplier listing.

(b) At the Account Options prompt, click on [Yes Correct] to verify the
Supplier’s details.

(c) At the Invoice Date prompt, enter the Invoice date. Suggest date is
entered as date on which goods are received into stock. Press [Enter].

(d) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat.  Press [Enter]
to accept the default selection.

(e) At the Invoice Number prompt, enter the Supplier’s invoice number.

(f) At the Additional Reference prompt, enter any additional information.

(g) At the Code Selection prompt, click on

as these are generally the same as the
Suppliers Codes.

(h) At the Goods Received Note – From Supplier screen, click on

to insert the transaction lines.

(i) The stock may be captured by:

1.       Stock
Code

2.       Description.

(j) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle the
stock search order by Stock Code, Supplier Code or Stock Description.

Note: Once the Stock Code and Stock Description
have been entered an information window is displayed on the right hand side
listing the Stock Item’s current quantity on hand, monthly sales to date and
the Supplier’s Code.

(k) At the Quantity prompt, enter the number of units received.

(l) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be overwritten.  Press [Enter]
to accept the default tax status.

(m) Accpick will automatically calculate the unit cost inclusive or
exclusive of vat depending on the option selected above.  If the Cost Price per Unit displayed is different
to the invoice price, enter the new cost price at the Cost prompt. Press [Enter].

Note: New Cost Prices.

When the System registers a new cost price
and the Supplier’s Maintenance option: Update Selling Price on Stock
Receipts, is set to YES, an Update Selling Price prompt will be displayed.

When NOW is selected, a Pricing Update
screen is displayed with the new cost price, the current % markup for Selling
Price 1,2 and 3. Adjustments to the markup % results in adjustments to the
relative Selling Prices and vice versa. Press [Enter] to return to the Goods Received
Note screen.

(n) When all the line items have been entered and the total quantity
received, total vat and total inclusive amount on the Goods Received Note
balances with the Supplier’s invoice, click on

to update the Goods Received Note.

(o) If the Goods Received Note and the Supplier’s Invoice do not
balance, use the arrow keys to move the incorrect transaction line/s to the top
of the listing. Click on

or

to make the correcting adjustments. Once
correct, click on

to update the Goods Received Note.

(p) The Update Options Menu will be displayed:

Note: Surcharge.

e.g. Transport Charges

This option allows the Supplier’s surcharge to be apportioned to all line items
and printed on the Goods Received Note. This amount is exclusive of vat.

Note: Pay and Update

Use the Pay and Update facility where a Supplier is paid cash out of the
current day’s cash sale money.

The Payment Details window will be displayed allowing the payment details for
the stock purchased to be entered and updated immediately. i.e. updating posts
invoice and payment to the supplier, reduces cash in the drawer, increases pay
outs, receives items into stock, updates vat controls and updates Day End
Report.

(q) Click on

to update the transaction and display the
Print Options Menu.

(r) At the Print Options Menu, click on the required print options:

a. Selling Price

b. Selling Price, Markup and Gross Profit %

c. Selling Price and Gross Profit Value

d. No print

(s) The Goods Received Note – From Supplier screen will be
displayed.  Enter another Supplier number
to continue entering further invoices.

(t) Once completed click on

to return to the Creditors Transaction Menu.

---

## [422.htm]

2.
Returns - Stock Items

(Credit Note or Goods Returned Note)

When a Supplier issues a Credit Note
in respect of goods returned, this option updates Stock, the Supplier’s account
balance and the Vat controls simultaneously.

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the select option to view and select from the current
Supplier listing.

(b) At the Account Options prompt, click on [Yes Correct] to verify the
Supplier’s details.

(c) At the Document Date prompt, enter the date. Press [Enter].

(d) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat.  Press [Enter]
to accept the default selection.

(e) At the Document Number prompt, enter the Supplier’s Credit Note
number.

(f) At the Additional Reference prompt, enter any additional
information.

(g) At the Goods Returned Note – To Supplier screen, click on

to insert the transaction line/s on the
Supplier’s Credit Note.

(h) The stock may be captured by:

1.       Stock
Code

2.       Description.

(i) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle
stock search order by Stock Code, Supplier Code or Stock Description.

Note: Once the Stock Code and Stock
Description have been entered an information window is displayed on the right
hand side listing the Stock Item’s current quantity on hand, monthly sales and
the Supplier’s Code.

(j) At the Quantity prompt, enter the number of units to be returned.

(k) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be
overwritten.  Press [Enter] to accept the default tax status.

(l) Accpick will automatically calculate the unit cost inclusive or
exclusive of vat depending on the option selected above

(m) When all the line items have been entered and the total quantity returned,
total vat and total inclusive amount on the Goods Returned Note balances with
the Supplier’s credit note, click on

to update the Goods Returned Note.

(n) If the Goods Return Note and the Supplier’s Credit Note do not
balance, use the arrow keys to move the incorrect transaction line/s to the top
of the listing. Click on

or

to make the correcting adjustments.

(o) Once correct, click on

to update the Goods Returned Note.

(p) The Update Options Menu will be displayed:

(q) Click on

to update the transaction and display the
Print Options Menu.

(r) The Ageing Menu will be displayed.
Select the period to which the Credit Note must be allocated.

(s) Accpick will update the transaction and display the print options
prompt.  Click on [Yes] to print the
Goods Returned Note.

(t) Enter another Supplier Number to continue entering further returns.

(u) Once completed, click on

to return to the Creditors Transaction Menu.

---

## [423.htm]

3.
Invoice Capture - Expense

(E.g. Telkom and Stationery Accounts.)

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the select option to view and select from the current
Supplier listing.

(b) At the Account Options prompt, click on [Yes Correct] to verify the
Supplier’s details.

(c) At the Invoice Date prompt, enter the Invoice date. Press [Enter].

(d) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat. Suggest use I for inclusive. Press [Enter] to accept the default
selection.

(e) At the Invoice Number prompt, enter the Supplier’s invoice number.

(f) At the Additional Reference prompt, enter any additional
information.

(g) At the Invoice – Expense Categories screen, click on

to insert the transaction line/s.

(h) At the Category prompt, enter the account category number or
alternatively use the select facility to view and select from the Expense
category listing.

(i) At the Cost prompt, enter the cost amount inclusive or exclusive of
vat depending on the option selected above.

(j) At the Tax prompt, enter the tax option or press [Enter] to accept the default option.1
= 14%, 2 = 0%.

(k) To make correcting adjustments to the line items, use the arrow keys
to move the incorrect line/s to the top of the listing. Click on

or

and make the correcting adjustments.

(l) Once correct, click on

to update the transaction.

(m) The Update Options Menu will be displayed.

Note: Pay and Update

Use the Pay and Update facility where a Supplier is paid cash out of the
current day’s cash sale money.

The Payment Details window will be displayed allowing the payment details for
the expense incurred to be entered and updated immediately. i.e. updating posts
invoice and payment to the supplier, reduces cash in the drawer, increases pay
outs, receives items into stock, updates vat controls and updates Day End
report.

(n) Click on

to update the transaction.

(o) The Print Options menu will be displayed. Click on [Yes] to print
the Goods Received Note .

(p) Continue capturing Expense invoices by entering another Supplier Number.

(q) Once completed entering all Expense invoices, click on

to return to the Creditors Transaction Menu.

---

## [424.htm]

4.
Returns - Expense Categories

(E.g. Credit Notes for Advertising Account.)

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the select option to view and select from the current
Supplier listing.

(b) At the Account Options prompt, click on [Yes Correct] to verify the
Supplier’s details.

(c) At the Document Date prompt, enter the document date. Press [Enter].

(d) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to
enter the transactions Inclusive or Exclusive of Vat.  Press [Enter]
to accept the default selection.

(e) At the Document Number prompt, enter the Supplier’s Credit Note
number.

(f) At the Additional Reference prompt, enter any additional
information.

(g) At the Returns – Expense Categories screen, click on

to insert the transaction lines.

(h) At the Category prompt, enter the account category number or
alternatively use the select facility to view and select from the Expense
category listing.

(i) At the Cost prompt, enter the amount inclusive or exclusive of vat depending
on the option selected above.

(j) At the Tax prompt, enter the tax option or press [Enter] to accept the default option.1
= 14%, 2 = 0%.

(k) To make correcting adjustments to the line items, use the arrow keys
to move the incorrect line/s to the top of the listing. Click on

or

and make the correcting adjustments.

(l) Once correct, click on

to update the transaction.

(m) The Update Options Menu will be displayed:

(n) Click on

to update the transaction.

(o) The Credit Ageing Menu will be displayed.  Select the period to which the Credit Note
must be allocated.

(p) The Print Options menu will be displayed. Click on [Yes] to print
the invoice.

(q) Continue capturing further Expense Credit Notes by entering another
Supplier number.

(r)
Once completed entering all
Expense Credit Notes, click on

to return to the Creditors Transaction Menu.

---

## [425.htm]

5.
Post Payment(s)

(Use only if the Creditors Module is
not integrated with the Cash Book.)

Post Payments Options:

8
Post Payments for Balance
Brought Forward Creditors

8
Post Payments for Open Item
Creditors.

8
Unallocated Payments for Open
Item Creditors

Balance Brought Forward Creditors

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the search facility to view and select from the current
Supplier listing. The Supplier’s details will be displayed.

(b) At the Account Options prompt, confirm the Creditor’s details by
clicking on [Yes Correct].

(c) At the Payment Date prompt, enter the payment date or press [Enter] to accept the default date.

(d) At the Payment Reference and the Additional Reference prompt, enter
the payment reference information.

(e) In the Payment Details Screen, enter the amount due at the Amount
Due prompt. Press [Enter].

(f) At the Amount Tendered prompt, enter the actual amount paid. Press [Enter].

(g) Accpick will automatically calculate the settlement discount amount.
This is the difference between the amount due and the amount paid. Press [Enter] to accept this amount.

(h) Accpick also automatically calculates the settlement discount
percentage.  Press [Enter] to accept the percentage.

(i) The Total to Post Amount will be displayed.

(j) At the Payment Ageing prompt, allocate the payment to the correct
ageing periods. Press [Enter].

(k) At the OK to Update prompt, click on

.

(l) Accpick will automatically update the transaction and return to the
Payments to Suppliers entry screen.

(m) Continue entering further payments by clicking on

to select a Creditor from the Creditor
Listing.

(n) When all payments have been entered, click on

to return to the Creditors Transaction Menu.

Open Item Creditors

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the search facility to
view and select from the current Supplier listing.

(b) At the Account Options prompt, click on [Yes Correct] to verify the
Supplier’s details.

When an Open Item Creditor is accessed, the
Open Item Payment screen is automatically displayed on the top right hand
corner as well as the total amount due.

(c) At the Payment Date prompt, enter the Payment date. Press [Enter].

(d) At the Amount Paid prompt, enter the amount paid.

(e) At the Payment Reference and Additional Reference prompt, enter the
payment reference details.

The Open Item Payment screen will be
displayed listing all unallocated transactions types making up the amount due.

(f) To allocate payment, use the [á] and [â] arrows to move each of the
transactions to be paid / allocated to the top of the transaction listing.
Alternatively, click on

to find the specific transaction by
transaction number.

(g) When the selected transaction is at the top of the transaction listing,
click on

to allocate payment against the transaction.

(h) At the amount Paid prompt, enter the amount received. Press [Enter].

(i) At the Settlement Discount prompt, enter the settlement discount
amount, if any. Press [Enter].

Note: Full Payment [*] vs Part Payment:

If the Balance due is being paid in FULL:
Note that after you have entered the amount paid and where applicable, the
settlement discount amount, a ü is displayed alongside the entry
indicating that this has been settled in full. This entry will cease to appear
in subsequent payment allocations leaving only the unallocated entries in the
allocation screen.

If only part of the Balance due is being
paid: Enter the value of the part payment being paid in the Amount Paid
field, press enter through the Settlement Discount field. (No settlement
Discount on part payments).  Note, no ü
appears alongside the entry and the entry with the balance due will reappear in
subsequent allocation screens.

Note: Settlement
Discount:

Where
settlement discount is taken, we suggest that the invoice with the greatest
value be allocated last, and that the total value of the settlement discount be
allocated to this invoice

(j) When all transactions making up the receipt have been allocated,
click on

.

As each payment is allocated, the
“Allocated” and “Balance” amounts on the top right hand corner of the screen
are being updated.  The transaction may
only be updated once the Amount Paid agrees with the “Allocated” and the
“Balance” is zero.

(k) At the Allocate Payment prompt, click on

.

Accpick will update the transaction and
return to the Payments to Supplier entry screen.

(l) Continue processing further payments by entering another Supplier
Account number at the Supplier prompt.

(m) On completion, click

and return to the Creditors Transaction Menu.

Unallocated
Payments on Open Item Creditors

What is an Unallocated Payment?

An unallocated payment is a payment to a
creditor which has no transaction entry to which the payment must be
allocated.

8
.e.g.       - payment for an item not yet invoiced

8
- a payment is made which is NOT to be apportioned to
any of the unallocated entries.

(a)
At the date request, press the
[Page Up] key to display the “Unallocated – Open Item Payment” screen.

(b) At the Unallocated - Open Item Payment prompt, enter the date and
amount paid

(c) At the Post as Unallocated Payment prompt, click on

.

(d) Accpick will update the transaction and return to the Payments to
Supplier Screen.

---

## [426.htm]

6.
Journal Entries

Debit Journal – Reduce amount owing
to Supplier

Credit Journal – Increase amount
owing to Supplier.

Journal Entry Options:

8
Debit Journals

Balance
Brought Forward Creditors

Open
Item Creditors

8
Credit Journals

Balance
Brought Forward Creditors

Open
Item Creditors

Debit Journal for Balance Brought Forward Creditors

(a) At the Supplier prompt, enter the Supplier’s account number or
alternatively use the select facility to select a Creditor.

(b) Confirm the Creditor’s details by clicking on [Yes Correct].

(c) At the Date prompt, enter the journal date or alternatively press [Enter] through the default date.

(d) At the Journal Number prompt, enter the journal number or
alternatively press [Enter] through
the default journal number. Accpick automatically allocates journal numbers in
a consecutive sequence.

(e) At the Additional Reference prompt, enter a short explanation
motivating the journal. This information appears on the Creditor’s Statement
and on the Journal Transactions Report.

(f) At the Journal Amount prompt, enter the journal amount.

(g) Allocate Ageing accordingly. Ensure that the Total Aged balances
with the Journal Amount.  If not, Accpick
will prompt you to make the correction.

(h) At the Update Journal prompt, click on

. The Debit
Journal Posting entry screen is displayed allowing further journal entries to
be captured.

(i) When completed capturing all journals in the batch, click on

and return to
the Creditors Transaction Menu.

Debit Journal for Open Item Creditors

The Open Item entry screen will
automatically appear according to the Creditors Account category selected on
the Creditor’s Account Details Menu.

At the Debit Journal Posting Screen, follow
the same procedure as for Balance Brought Forward Creditors but note the
following differences:

The total value of the journal may only be
allocated to ONE ageing period. Press the [é] and [ê] arrow keys to highlight the period
to which the total journal amount is to be allocated. Press [Enter] to update
the journal transaction immediately.

Every journal entry must be allocated a
unique journal number. The same journal number on open item journals is not
allowed.

Credit Journal for Balance Brought Forward
Creditors

(a)
At the Account Number prompt,
enter the Creditor’s account number or alternatively use the search facility to
select a Creditor.

(b) Confirm the Creditor’s details by clicking on [Yes Correct].

(c) At the Journal Date prompt, enter the journal date or alternatively
press [Enter] through the default date.

(d) At the Journal Number prompt, enter the journal number or
alternatively press [Enter] through
the default journal number. Accpick automatically allocates journal numbers in
a consecutive sequence.

(e) At the Additional Reference prompt, enter a short explanation
motivating the journal. This information appears on the Creditor’s Statement
and on the Journal Transactions Report.

(f) At the Journal Amount prompt, enter the journal amount.

(g) Allocate ageing accordingly. Ensure the Ageing Total balances with
the Journal Amount.  If not, Accpick will
prompt you to make the correction.

(h) At the Ok to Update prompt, click on

. The Credit
Journal Posting Menu is displayed allowing further journal entries to be
captured.

(i) When completed capturing all journals, click on

and return to the Creditors Transaction Menu.

Credit Journal for Open Item Creditors

The Open Item entry screen will
automatically appear according to the Creditor’s account category selected on
the Creditor’s Account Details Menu.

At the Credit Journal Posting Screen,
follow the same procedure as for Balance Brought Forward Creditors but note the
following differences:

The total value of the journal may only be
allocated to ONE ageing period. Press the [é] and [ê] arrow keys to highlight the period
to which the total journal amount is to be allocated. Press [Enter] to update
journal transaction immediately.

Every Journal Entry must be allocated a
unique journal number. The same journal number on open item journals is not
allowed.

---

## [427.htm]

7.
RFC Controls

Return for Credit Control Options:

8
1. Send Stock to Suppliers

8
2. Update Supplier Returns

Credit
Granted

Stock
Replaced

8
3. View RFC Status

By
Stock Item

By
Supplier

8
4. Value of Stock RFC

This facility has been designed to control
stock returned to Suppliers for either:

Stock
Replacement

ó

Rand
Value Credit

ó

Goods returned to Suppliers via RFC are
transferred from the normal stock file to the “Returns for Credit” stock file.
A value of all the stock on RFC is available and this figure, ought to be taken
into account as part of the Final Stock Valuation in the Income Statement and
Balance Sheet.

A Request for Credit document may be
printed on POS stationery.

Once the Supplier has actioned the Request
for Credit:

1.
Stock Replacement: stock is transferred
back from the Returns for Credit File to the Normal Stock file.

2.
Rand Value Credit:

a.  Stock is transferred from the Returns
for Credit file to the Normal Stock file.

b.  Stock is returned to the Supplier via
a credit note.

c.  Supplier’s account is reduced by the
value of the credit note.

Rand Value less than Credit Request:

Where Rand Value of Credit received is less
than the Credit Request sent to the Supplier:

1.
New Rand Value can be entered
which will update the Supplier file.

2.
Stock will be transferred from
the Returns for Credit file back into normal stock

3.
The immediate issue of a credit
note will transfer the stock out of the Normal Stock file.

Note: The last cost price in Stock
Maintenance remains unaltered.

Enquiry Facilities

Enquiry facilities provide options to view
RFC status by

1.
Stock Item

2.
Supplier.

3.
Total Value of RFC’s.

4.
Stock Movement

Where RFC’s are outstanding for a specific
Supplier, a Creditors enquiry into such supplier will indicate the outstanding
RFC amount, exclusive of vat, on the
bottom left hand side of the Creditors Enquiry screen.

Remittance
Advice for Pending RFC’s:

The total amount of outstanding RFC’s,
exclusive of vat, is printed at the bottom of the remittance advice.

1. Send Stock to Suppliers

(a) At the Supplier Number prompt, enter the Supplier’s account number
or alternatively use the select option to view and select from the current
Supplier listing.

(b) At the Account options prompt, click on [Yes Correct] to verify the
Supplier’s details.

(c) At the Return Date prompt, enter the return date or alternatively,
press [Enter] through the default date.

(d) At the Goods Returned for Credit/Replacement screen, click on

to insert the transaction line/s.

(e) The stock may be capture by:

1.       Stock
Code

2.       Description.

(f) At the Stock Code prompt, enter the stock code or alternatively, at
the Description prompt, press the [Page Down] key to view and select from the
Stock Listing.  Right click to toggle
stock search order by Stock Code, Supplier Code or Stock Description.

Note: Once the Stock Code and Stock
Description have been entered an information window is displayed listing the
Stock Item’s current quantity on hand, monthly sales and the Supplier’s Code.

(g) At the Quantity prompt, enter the number of units to be returned.

(h) At the Tax Code prompt, Accpick will default to the tax status for
this stock code which was set up in Stock Maintenance.  This Tax Code can however be
overwritten.  Press [Enter] to accept the tax status.

(i) Accpick will automatically calculate the last unit cost inclusive and
exclusive of vat.

(j) At the Comments prompt, enter an explanation motivating the return.
Press [Enter].

(k) At the Purchase Date prompt, enter the purchase date. Enter
00/00/0000 to leave this field blank.

(l) At the Reference Number prompt, enter the reference number. E.g.
Original Invoice number. Press [Enter].

(m) The transaction line information will be displayed.

(n) Enter further line items by clicking on

.

(o) To edit or delete a line, use the arrow keys to move the incorrect
transaction line/s to the top of the listing. Click on

or

to make the correcting adjustments.

(p) Once the Goods Returned for Credit/Replacement Note is complete,
click on

to update the transaction.

(q) The Update Options Menu will be displayed:  Click on

to update the transaction and display the
Print Options Menu.

(r) Click on [Yes] to print the Goods Returned for Credit/Replacement Note.

(s) At the Values prompt, select Yes or No to print the values on the
Goods Returned for Credit/Replacement Note.

(t) Click on

to return to the Creditors Transaction Menu.

2.1. Update Supplier Returns: Credit Granted

ó

The stock is not replaced and a credit note
is passed.

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the select option to
view and select from the current Supplier listing.

(b)
At the Account options prompt,
click on [Yes Correct] to verify the Supplier’s details.

(c)
At the Credit Date prompt,
enter the date. Press [Enter].

(d)
At the Inclusive / Exclusive of
Vat prompt, enter [I] or [E] to enter the transactions Inclusive or Exclusive
of Vat.  Press [Enter] to accept the default selection.

(e)
At the Document number prompt,
enter the Supplier’s Credit Note number.

(f)
At the Additional Reference
prompt, enter any additional information.

(g)
The RFC’s – Credit Granted by
Supplier screen will be displayed listing all the outstanding items.

(h)
To create a Credit Note, delete all the line items that are NOT
being credited. Use the arrow keys to move the transaction lines that are
not required to the top of the listing. Click on

to remove the transaction line/s.

(i)
The screen should now only
display the transaction items that the Supplier has agreed to credit.

(j)
If the Rand Value or the Quantity of the Credit Note is different, use the arrow keys to move the incorrect transaction line to the
top of the listing. Click on

and make the necessary adjustments to the Cost
Price and/or the Quantity fields.

(k)
Once the Credit note details
and value are correct, click on

to update the Credit Note.

(l)
Click on

to update the transaction.

(m) The Ageing Menu will be displayed.
Select the period to which the Credit Note must be allocated. Press [Enter].

(n)
At the Print Options prompt, click
on [Yes] to print the Credit Note.

(o)
Click on

to return to the Creditors Transaction Menu.

2.2. Update Supplier Returns: Stock
Replaced

ó

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the select option to
view and select from the current Supplier listing.

(b)
At the Account options prompt,
click on [Yes Correct] to verify the Supplier’s details.

(c)
At the Replacement Date prompt,
enter the date. Press [Enter].

(d)
At the Document number prompt,
enter the Supplier’s document number.

(e) The screen will display all the outstanding items.

(f) Use the arrow keys to move the transaction line, which corresponds
with the stock that is being replaced, to the top of the listing.

(g) Press [+] or [=] to accept the Credit.

(h) At the Quantity Replaced prompt, press [Enter] to accept the quantity or make the correcting adjustments
and press [Enter].

(i) Press the [Esc] button to Update and Exit.

(j) At the Update prompt, click on

.

(k) At the Print Confirmation prompt, click on

(l) Click on

to return to the Creditors Transaction Menu.

3.1. View RFC Status: By Stock Item.

(a)
At the Stock code prompt, enter
the stock code.

(b)
All outstanding RFC’s for this
stock item will be displayed.

(c)
To View the Listing: Use the arrow and
page keys move the line items.

(d)
[TAB]: Press the Tab button to toggle
the display between the Comment Line, Reference Number, the Purchase Date and
RFC Number..

(e)
[-]: Press the [–] minus button to
remove the RFC at the top of the listing. At the Delete prompt, click on Yes to
confirm deletion.

(f)
[*]: Press the star button to print the
listing.

(g)
Click on

to return to the Creditors Transaction Menu.

3.2. View RFC Status: By Supplier.

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the select option to
view and select from the current Supplier listing.

(b)
At the Account options prompt,
click on [Yes Correct] to verify the Supplier’s details. Press [Enter].

(c) All outstanding RFC’s for this Supplier will be displayed.

(d) To View the Listing: Use the arrow and page keys to move the line items.

(e) [TAB]: Press the Tab button to toggle the display between the Comment
Line, Reference Number, the Purchase Date and RFC Number.

(f) [-]: Press the [–] minus button to remove the RFC at the top of the
listing. At the Delete prompt, click on Yes to confirm deletion.

(g) [*]: Press the star button to print the listing.

(h) Click on

to return to the Creditors Transaction Menu.

4. Value of Stock RFC

This lists all the Stock out on RFC.

(a)
At the Select Month prompt,
select the month from which the report data is to be extracted. Press [Enter].

(b)
At the specific Department
prompt, enter [Y] to specify a
department. Select the Department from the Department listing. Enter [N] to list all outstanding RFC’s.

(c)
The

facility toggles the display between the Unit
Cost, Value, Supplier, Reference Number, Date of RFC and Comment Line.

(d)

displays the Value of the Total RFC Stock.

(e)

prints the RFC listing.

---


# 4.3 Creditors - Enquiries


## [431.htm]

1.
Individual Account Enquiry

Individual Account Enquiry options:

8
Current vs Archive Enquiries

8
Balance Brought Forward
Creditors

8
Open Item Creditors

Current vs Archive Enquiries

On the Enquiries Menu, the Data Status
window will indicate from which directory the enquiries will be made.

The default directory is the current
directory.

Click on the Quick Functions drop
down menu at the top of the screen to access archive directories.

Balance Brought Forward Creditors

(a) At the Supplier Number prompt, enter the Supplier’s Account number
or use the search facility to view and select from the Supplier Listing.

The Creditor’s Details will be displayed
including all outstanding balances, amounts last paid, purchases month to date
and purchases year to date.

(b)

displays the total purchase values for each
month.

(c) Click on

to return to the Creditor’s Enquiry Menu.

Open Item Creditor

(a)
In addition to the above,

displays a listing of all unmatched Open Item
transactions by Type, Transaction Number, Date, Balance Due and Ageing.

(b)

Total of Creditor’s Open Item Entries Balance.

(c)

enables a transaction search by transaction
number.

(d)

facility toggles the display between the
Original amount and the Ageing period.

(e)

displays the audit trail for the line item at
the top of the listing. I.e. the original amount and all payments thereon.

(f)

prints a listing of all unmatched
transactions.

(g) Click on

to return to the Main Debtor’s Enquiry Menu.

---

## [432.htm]

2.
Total Creditors Summary

(Age Analysis)

Total Creditors Summary Options:

8
1. Age Analysis

8
2. Control Enquiry

1. Age Analysis

(a) At the Order prompt, enter sequence listing options:                               A
= alphabetically by account name,

N = numerically by
account number

V = by value /
amount outstanding.

(b) At the Skip Zero Balances prompt, enter [Y] to include all Creditors
with zero balances in the listing or [N] to only list Creditors with balances.

(c) Accpick will extract the Creditor’s balances and display the Age
Analysis.

(d)

toggles the Creditor’s Summary by:

Account Number

Account Name

Total Due.

(e)

displays the Total Due for each ageing period,
the Active and Inactive Account Status.

(f) From the Options Menu click Return to revisit the Age Analysis or
Summary Print to print the Age Analysis.

(g) At the Date prompt, enter the date to appear on the report.

(h) Click on

to return to Creditors’ Enquiry Menu.

2. Control Enquiry

(a)
Accpick will extract and
display the Control Totals.

(b) Click on

to print Creditors’ Control Totals.

(c) Click on

to return to Creditors’ Enquiry Menu.

---

## [433.htm]

3.
Transaction Scroll

(a) At the Start and End Date prompts enter the enquiry dates.

Automatically Defaults to Current Period.

Accpick
automatically defaults to the earliest and latest dates for which there are
transactions in the Current period. Accpick will also default to the earliest
and latest date for which there are transactions in each (archive) period.

Archive Periods

To access archive
periods, use the Quick Function facility at the top of the screen to
select an archive month.

(b) At the Enquiry type prompt, select:

Scroll: to  list all transactions by type, transaction
number, Creditor, Net Amount, Vat Amount and Total Amount.

Totals: to view transaction totals
for each entry type

(c) Press

to select entry types for enquiry:

(d) Use the Return or

to return to the Main Creditor’s Enquiry Menu.

---

## [434.htm]

4.
Expense & Tax Analysis

1. Expenditure Totals:

The total expenditure and tax amount for the
selected month is displayed.

To access totals for archive periods, use the Quick
Functions facility at the top of the screen to select an archive month.

2. Expense Category Totals:

Use the

facility to view month to date and tax value
totals for each expense category.

3. Expense Category Details:

Use the

facility to view transaction details by date,
transaction number, Supplier name, amount, tax and total amount for each
individual expense category.

8
Click on

to return to the Creditors Enquiry Menu.

---

## [435.htm]

5.
Monthly Expense Details

(a) At the Category Number prompt, enter the Expense Category number or
alternatively use the select facility to view and select form the current Expense
Category listing.

(b) The Monthly Expense totals from January to December together with
the proportionate % to total expense ratio will be displayed for the selected
expense category.

(c) Use the

facility to display a graphical representation
of the data.

(d) Click on

to return to the Creditors Enquiry Menu.

---

## [436.htm]

6.
Purchase History

(a) Net stock purchases exclusive of vat will be displayed by Supplier,
Total Purchase amounts and Monthly Purchase amounts.

(b) Use the

facility to toggle the sort order by Supplier
Number and Total Purchase amounts.

(c) Use the

facility to print the Net Stock Purchases
report.

(d) Click on

to return to the Creditors Enquiry Menu.

---


# 5. Cash Book - top level


## [54.htm]

Reports

On the Cash Book Reports Menu, the Data
Status Window will indicate from which directory the reports will be extracted.

The default directory is the current
directory.

8
Click on the Quick Functions
drop down menu at the top of the screen to access archive directories.

The following reports are available for
printing:

Reports

Report Options

Report Information

1. Banking Account

Detailed or  Consolidated

Detailed Report
lists each debtor’s receipts within a deposit, each category allocation for
Other income and Other Expenses.

The Consolidated
Report merges all details to display a single total per deposit and payment.

2. Transactions

Specific Date
Range

Specific
Transaction Type

Detailed or Totals
Only

Lists all
transactions according to the selected options.

3. Categories and Tax
Analysis

1. Income

2. Expenses

3. Cash Book Income        and Tax

4. Cash Book Expenses and Tax

5. Historical   Category

Monthly Values

Monthly Values

Current Values

Current Values

Archive

4. Detailed Category
Report

Date Order or,

Category Order

Detailed break
down of selected details for Income / Expenditure Categories for selected
date range.

---


# 5.1 Cash Book - Categories


## [511.htm]

DOCPROPERTY
ManDocTitle1.1 1. Income Categories

Income Category Maintenance
Options:

8
Creating New Categories

8
Modifying Existing Categories

8
Deleting Existing Categories

When inserting a new category it is
advisable to refer to the standard Accpick Xcellence Chart of Accounts. This is
a numbering system that conforms to the setup requirements of the Accpick
General Ledger.

Here is a typical, very general, numbering
system:

8500

Cash Control (Daily Banking)

8501

Speedpoint (Daily Banking)

3020

Interest Received from Bank

1300

Rebates Received

1500

Product Bonus Received

Creating a New Income Category

(a) At the CASH BOOK MAINTENANCE MENU, select 1. Income Categories.

(b) Use the search facility to view your current Income category
listing. Select a new Income category number. Press [Escape] to return to the
Income Category File Maintenance Screen.

(c) At the Category Number prompt, enter the new Income category number.
Press [Enter].

(d) At the Category Name prompt, enter the new category name. Press [Enter].

(e) At the Save Category prompt, click on

.

(f) Click on

and return to the Main Cash Book Menu.

Modifying
an Existing Income Category

(a)
At the CASH BOOK MAINTENANCE
MENU, select Income Categories.

(b)
At the Category Number prompt,
enter the Income category’s number or use the search facility to view and
select from your current Income category listing.

(c)
At the Category Name prompt,
edit the category name. Press [Enter].

(d)
At the Save Category prompt,
click on

.

(e)
Click on

and return to the Main Menu.

Deleting an Existing Income Category

(a)
At the CASH BOOK MAINTENANCE
MENU, select Income Categories.

(b)
At the Category Number prompt,
enter the income category’s number or use the search facility to view and
select from your current Income category listing

(c)
Click on

or press the [Page Down] key.

(d)
At the Confirm Deletion prompt,
click on

.

(e)
Click on

and return to the Main Menu.

Note: An Income category cannot be deleted if
there have been income transactions recorded against this category.

---

## [512.htm]

2.
Expense Categories

Expense Category Maintenance
Options:

8
Creating New Categories

8
Modifying Existing Categories

8
Deleting Existing Categories

When inserting a new category it is
advisable to refer to the standard Accpick Xcellence Chart of Accounts. This is
a numbering system that conforms to the setup requirements of the Accpick
General Ledger.

Here is a typical, very general, numbering
system:

4010

Advertising

4050

Bank Charges

4120

Electricity and Water

4160

Insurance

4540

Rent

4600

Salaries

4605

Salaries – Medical Aid

4615

Salaries – Skills Development

4620

Salaries - UIF

4630

Salaries - PAYE

4750

Telephones

4755

Telephones - Cell

4950

Wages

Creating
a New Expense Category

(a) At the CASH BOOK MAINTENANCE MENU, select Expense Categories.

(b) Use the search facility to view your current Expense category
listing. Select a new Expense category number. Press [Escape] to return to the Expense Category File Maintenance Screen.

(c) At the Category Number prompt, enter the new Expense category
number. Press [Enter].

(d) At the Category Name prompt, enter the new category name. Press [Enter].

(e) At the Save Category prompt, click on

.

(f) Click on

and return to the Main Menu.

Note: At the time of installation, you may be
issued with Expense Categories for the Creditors’ Module and the Cash Book
module. Common expenses will reflect the same category number. Further Expense
Categories which are added at a later stage in one module,    (e.g. Creditors) and are common to another
module, (e.g. Cash Book) must be created separately in each module using the
SAME category number.

Modifying an Existing Expense Category

(a)
At the CASH BOOK MAINTENANCE
MENU, select Expense Categories.

(b) At the Category Number prompt, enter the Expense category’s number
or use the search facility to view and select from your current Expense
category listing.

(c) At the Category Name prompt, edit the category name. Press [Enter].

(d) At the Save Category prompt, click on

.

(e) Click on

and return to the Main Menu.

Deleting
an Existing Expense Category

(a)
At the CASH BOOK MAINTENANCE
Menu select Expense Categories.

(b) At the Category Number prompt, enter the expense category’s number
or use the search facility to view and select from your current Expense category
listing.

(c)  Click on

or press the [Page Down] key.

(d) At the Confirm Deletion prompt, click on

.

(e) Click on

and return to the Main Menu.

Note: An Expense category cannot be deleted
if there have been expenses recorded against it.

---


# 5.2 Cash Book - Transactions


## [521.htm]

1.
Receipts from Debtors

(Updates Debtors and Cash book)

Receipts from Debtors Options:

8
Receipts from Balance Brought
Forward Debtors

8
Receipts from Open Item
Debtors

8
Unallocated Payments on Open
Item Debtor

8
Capturing Post Dated Cheques

8
Posting RD Cheques on an Open
Item Debtor

8
“Offsetting” transactions on
an Open Item Debtor

Note: The Receipt Screen for Balance Brought
Forward Debtors and Open Item Debtors will automatically be displayed according
to the account category that was selected on the Debtor’s Details Maintenance Menu.

Receipts from Balance Brought Forward Debtors

(a) At the Account Number prompt, enter the Debtor’s account number or
alternatively use the search facility to view and select from the current
Debtor listing. The Debtor’s details will be displayed.

(b) At the Account Options prompt, confirm the Debtor’s details by
clicking on [Yes Correct]

(c) At the Date prompt, enter the date or press [Enter] to accept the default date.

(d) At the Payment Allocation Screen, enter the amount due. Press [Enter].

(e) At the Amount Tendered prompt, enter the actual amount received.
Press [Enter].

(f) Accpick will automatically calculate the settlement discount amount.
This is the difference between the amount due and the amount tendered. Press [Enter] to accept this amount.

(g) Accpick will then automatically calculate the settlement discount
percentage. Press [Enter] to accept
the percentage.

(h) At the Additional Reference prompt, enter payment information of not
more than 20 characters. e.g. EFT, Cheque payment information or June Invoice /
July Invoice. This information will print on the Transaction Report. When the
System Parameter is set to Print Order Number on Statement, the Additional
Reference will print as a reference against the receipt.

(i) Allocate the payment to the correct ageing periods.

(j) At the Ok to Update prompt, click on

.

(k) The Cash Book Payment Posting screen is once again displayed.

(l) Continue entering all the individual receipts which make up a single
deposit.

(m) When all receipts making up the deposit have been entered, click on

.

(n) At the Confirmation prompt, check the total amount received (Batch
Total) is correct.

(o) Click on

to end this batch and return to the Cash Book
Transaction Menu.

Receipts from Open Item Debtors

(a)
At the Account Number prompt,
enter the Debtor’s account number or alternatively use the search facility to
view and select from the current Debtor listing. The Debtor’s details will be
displayed.

(b)
At the Account Options prompt,
confirm the Debtor’s details by clicking on [Yes Correct]

(c)
At the Open Item Receipt
prompt, the amount due will automatically be displayed. Enter the Date, Amount
Paid and Receipt Number or press [Enter] to accept the default information.

(d)
Confirm the Open Item
allocation by clicking on [OK].

(e)
To allocate the payment, use the

,

[á] and
[â] arrows keys to move each of the transactions to be paid /
allocated to the top of the transaction listing.

(f)
When the selected transaction
is at the top of the listing, click

to allocate the payment against the
transaction.

(g)
At the Amount Paid prompt,
enter the amount paid. Press [Enter].

(h)
At the Settlement Discount
prompt, enter the Settlement Discount Amount. Press [Enter].

Note: Full Payment [*] vs Part Payment:

If
the Balance due is being paid in FULL: Note that
after you have entered the amount paid and the settlement discount amount, a
* is displayed alongside the entry indicating that this has been settled in
full. This entry will cease to appear in subsequent payment allocations
leaving only the unallocated entries in the allocation screen.

If only part of the Balance due is
being paid: Enter the value of the part payment being paid in the Amount
Paid field, press enter through the Settlement Discount field. (No settlement
Discount on part payments).  Note, no *
appears alongside the entry and the entry will reappear in subsequent
allocation screens.

Note: Settlement Discount:

Where settlement discount is taken, we
suggest that the invoice with the greatest value be allocated last, and that
the total value of the settlement discount be allocated to this invoice

(i) When completed, click on

.

(j) At the Allocate Payment prompt, click on

.

(k) Accpick will automatically update the transactions and return to the
Cashbook Payment Posting screen.

(l) Continue entering all the individual receipts which make up a single
deposit by entering another Debtor’s account number at the Account Number
prompt.

(m) When all receipts making up the deposit have been entered, click on

.

(n) At the Confirm prompt, check the total amount received (Batch Total)
is correct.

(o) Click on [Yes] to end this batch and return to the Cashbook
Transaction Menu.

Unallocated Receipts on Open Item Debtors

What is an Unallocated Receipt?

An unallocated receipt is a payment from
a debtor which has no transaction entry to which the receipt can be allocated
e.g.

8
deposit for an item not yet
invoiced

8
a payment received which is
NOT to be apportioned to any of the unallocated entries.

(a)
At the date request, press
[Page Up] key to display the “Unallocated – Open Item Receipt” screen.

(b) At the Unallocated - Open Item Receipt prompt, enter the Date and amount
paid

(c) At the Post as Unallocated Payment prompt, click on

.

(d) Accpick will update the transaction and return to the Cash Book
Payment Posting Received Menu.

Capturing Post Dated Cheques (PDC’s)

To process Post Dated Cheques

(a)
At the date request, press the
[Page Down] key. The Post Dated Cheque Entry screen will be displayed.

(b)
At the Cheque Date and Amount
prompt, enter the cheque details. Press [Enter].

(c)
At the Ok to Post prompt, click
[Yes].

NOTE: This facility is for information
purposes only.

Post dated cheques for banking tomorrow will print on today’s final Day End
report and clear.  Post dated cheques will
NOT automatically be updated to Debtors/Cash Book on due date.  They are to be processed as a normal receipt
on due date.

To View and Print Post Dated Cheque
Listing:

8
1.

,

,

5. Post Dated
Cheque Listing.

8
2.

,

,

7. Post Dated
Cheque Listing.

8
3.

,

,

1. Individual
Account Enquiry,

Select P
to view Post Dated Cheques.

8
4.

B. Age Analysis

2. Monthly

Enter
Y to include any Post Dated                                         Cheques.

Posting Returned (RD) Cheques on an Open Item Debtor.

Capture this receipt as an unallocated
payment with a negative (minus) value. In other words, follow the same
procedure as above but enter a negative value.

“Offsetting” transactions on an Open Item Debtor.

i.e. contra transactions against each
other.

This may be done within a payment
allocation or alternatively, in Cash Book receipting.

Process the transaction as a payment where
the Amount Paid is Nil. The Open Item allocation screen is displayed; contra
the required items making sure that the Balance to be allocated is finally Nil
before attempting to update.

---

## [522.htm]

2.
Other Income

These are income receipts in the Cash Book
which do not update in the Debtors Module.

Examples of Other Income transactions
include:

8
Interest Received

8
Rent Received

8
Staff Loans Repaid

8
Rebate Cheques / Product
Bonuses Received

(a) At the Transaction Date prompt, enter the date or press [Enter] to accept the default date.

(b) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to enter the transactions Inclusive
or Exclusive of Vat. Press [Enter] to accept default selection.

(c) At the Transaction Reference and the Additional Reference prompt,
enter the reference information. E.g. Deposit number and details of the
depositor i.e. from whom received.

(d) Click on

to display Income Received entry screen.

(e) Click on

to insert a transaction line.

(f) Click on

to display the Income Category Listing and
select an Income Category or at the Income Category prompt, enter the Income
category number. Press [Enter].

(g) Enter the amount received. Press [Enter].

(h) Enter the tax status. Code 1 - 14%, Code 2 - 0%. Press [Enter]. The extended amounts are
automatically displayed.

(i) If necessary, click on

to continue inserting additional transaction
lines to complete the deposit.

NOTE: To Edit or Delete a
transaction line:

8
Use

and

to move the required transaction to the top
of the transaction listing.

8
Click on

to change the transaction line information

8
Click on

to remove the transaction line.

(j) When completed, click on

.

(k) At the Post and Update prompt, click on

.

(l) Accpick will automatically update the transaction and return to the
Income Received Screen.

(m) Click on

to return to the Cash Book Transaction Menu.

---

## [523.htm]

3.
Payments to Creditors

Payments to Creditors Options:

8
- Payments to Balance Brought
Forward Creditors

8
- Payments to Open Item
Creditors

8
- Unallocated Payments to
Open Item Creditors

Note: The Payment Screen for Balance Brought
Forward Creditors and Open Item Creditors will automatically be displayed
according to the account category that was selected on the Creditors Details Maintenance
Menu.

Payments to Balance Brought Forward Creditors

(a)
At the Supplier Number prompt,
enter the Supplier’s account number or alternatively use the search facility to
view and select from the current Supplier listing. The Supplier’s details will
be displayed.

(b) At the Account Options prompt, confirm the Supplier’s details by clicking
on [Yes Correct].

(c) At the Payment Date prompt, enter the payment date or press [Enter] to accept the default date.

(d) At the Transaction Reference and the Additional Reference prompt,
enter the payment reference information.

(e) In the Payment Details Screen, enter the amount due at the Amount
Due prompt. Press [Enter].

(f) At the Amount Tendered prompt, enter the actual amount paid. Press [Enter].

(g) Accpick will automatically calculate the settlement discount amount.
This is the difference between the amount due and the amount paid. Press [Enter] to accept this amount.

(h) Accpick also automatically calculates the settlement discount
percentage.  Press [Enter] to accept the percentage.

(i) At the Total to Post prompt, press [Enter] to accept total amount to post.

(j) Allocate the payment to the correct ageing periods. Press [Enter].

(k) At the Ok to Update prompt, click on

.

(l) Accpick will automatically update the transaction and return to the
Payments to Suppliers entry screen.

(m) Continue entering further payments by clicking on

to select a Creditor from the Creditor
Listing.

(n) When all payments have been entered, click on

to return to the Cash Book Transaction Menu.

Payments to Open Item Creditors

(a)
At the Cash Book Payments to
Suppliers Screen, click on

to view Creditor Listing.

(b) Select Creditor.

(c) Confirm the Creditor’s details by clicking on [Yes Correct] at the
Account Options prompt.

(d) The Payment Screen will be displayed showing Open Item Payment and
the Total Due on the top right hand corner.

(e) At the Open Item Payment Screen, enter the Payment Date, Amount
Paid, Payment Reference and Additional Reference information. The Amount Paid
amount is the actual amount paid net of any settlement discount.

(f) The Open Item Allocation Screen is displayed, listing all
unallocated transaction types making up the Total Due.

(g) To allocate the payment, use the

and

arrows keys to move each of the transactions
to be paid / allocated to the top of the transaction listing.

(h) When the selected transaction is at the top of the transaction
listing, click on

to allocate the payment against the
transaction.

(i) At the Amount Paid prompt, enter the amount paid. Press [Enter].

(j) At the Settlement Discount prompt, enter the Settlement Discount
Amount. Press [Enter].

Note:
Full Payment [X] vs Part payment:

If the Balance due is being paid in FULL: Note
that after you have entered the amount paid and the settlement discount a [X]
is displayed alongside the entry indicating that this has been settled in
full. This entry will cease to appear in subsequent payment allocations
leaving only the unallocated entries in the allocation screen.

If only part of the Balance due is
being paid: Enter the value of the part payment being paid in the Amount
Paid field, press enter through the Settlement Discount field. (No settlement
Discount on part payments).  Note, no [X
] will appear alongside the entry and the entry will reappear in subsequent
allocation screens.

Settlement Discount Note:

Where settlement discount is taken, we
suggest that the invoice with the greatest value be allocated last, and that
the total value of the settlement discount be allocated against this invoice.

See example screen below.

(k) When payment allocation is completed, click on

.

(l) At the Allocation prompt, click on

.

(m) Accpick will automatically update the transaction and return to the
Payments to Supplier Screen.

(n) Select another Creditor to continue processing payments.

(o) When all payments have been processed, click on

and return to the Cash Book Transaction Menu.

Unallocated Payments to Open Item Creditors.

What is an Unallocated Payment?

An unallocated payment is a payment to a
creditor which has no transaction entry to which the payment can be
allocated.

8
.e.g.       a payment for an item not yet invoiced

a payment made which is NOT to be apportioned
to                    any of the
unallocated entries.

(a)
At the date request, press [Page
Up] key to display the “Unallocated – Open Item Payment” screen”.

(b)
At the Unallocated - Open Item
Payment screen, enter the Payment Date, Amount Paid, Payment Reference and Additional
Reference information. Press [Enter] through each selection.

(c)
At the Post as Unallocated
Payment prompt, click on [Yes].

(d)
Accpick will automatically
update the transaction and return to the Payments to Supplier Screen.

(e)
Click on

to return to the Cash Book Transaction Menu.

---

## [524.htm]

4.
Other Expenses

These are expenses incurred via the Cash Book which do not update
the Creditors Module.

Examples of Other Expenses include

8
Bank Charges,

8
Electricity,

8
Telephone,

8
Salaries and Wages.

(a)

At the Payment Date prompt, enter the payment date or press [Enter] to accept the default date.

(b) At the Inclusive / Exclusive of Vat prompt, enter [I] or [E] to enter the transactions Inclusive
or Exclusive of Vat. Press [Enter] to accept default selection.

(c) At the Payment Reference and the Additional Reference prompt, enter
the payment reference information. E.g. EFT No. / Cheque Number and name of
payee.

(d) Click on

to insert a transaction line.

(e) Click on

to display the Expense Category Listing and
select an Expense Category or at the Expense Category prompt, enter the Expense
category number. Press [Enter].

(f) Enter the amount. Press [Enter].

(g) Enter the tax status. Code 1 - 14%, Code 2 - 0%. Press [Enter]. The extended amounts are
automatically displayed.

(h) If required, click on

to continue inserting transaction lines until
the payment is fully allocated.

NOTE: To edit or delete a
transaction line:

8
Use

and

to move the required transaction to the top
of the transaction list.

8
Click on

to change the transaction line information.

8
Click on

to remove the transaction line.

(i) When payment is completed, click on

.

(j) At the Post and Update prompt, click on

.

(k) Accpick will automatically update the transaction and return to the
Payment of Expense Category Screen.

(l) Click on

to return to the Cash Book Transaction Menu.

---

## [525.htm]

5.
Bank Reconciliation

This is the bank reconciliation facility which allows the “tagging”
of items which are common to both the Cash Book and the Bank Statement. Where a
new Cash Book is captured, a facility exists for capturing unpresented cheques
at take-on and thereby arriving at a reconciled bank balance.

(a) At the Balance as per Statement prompt, enter the balance as per the
Bank Statement. If in overdraft capture the bank balance with a minus (-)
before the value.

(b) Click on the

,

, Page Up or
Page Down keys to move the selected transaction to the top of the transaction
listing.

(c) Alternatively, click on

for speedy location of an item by selecting
one of the following search criteria:

(d) When the required line item is at the top of the listing, click on

to tag the line item or double click the line
item common to both the Cash Book and the Bank Statement.

To “Untag” an item click on

again to remove the tag.

(e) When all the required entries have been tagged, click on

.

(f) Result: The Bank Reconciliation Summary window is displayed. The Bank
Balance reconciled amounts should agree with the Cash Book Balance amounts.

(g) If they agree, click on Update Files. This will save all “tagging” until a further
Bank Reconciliation or a Month End is processed.

If they do not agree, click on Continue
to return to the current Bank Reconciliation to make the correcting
adjustments.

To Ignore all “tagging” and discontinue
the current Bank Reconciliation, click on abandon.

Note: To account for unpresented
cheques from previous month(s) reconciliations(s):

For New Cash Book:

8
Click on

and enter cheque details.

For Subsequent Cash Books:

8
Where unpresented cheques
from previous months are presented in reconciliations during the current
month, “tag” these cheques and they will cease to be displayed.

Prior to Cash Book Month End:

8
Print the final bank
reconciliation. This cannot be printed from an archive.

8
The Month End for the Cash Book
will clear all “tagged” transactions and carry forward the closing balance as
well as all cheques listed as outstanding from previous month(s).

Bank Reconciliation Recommendation.

It is advisable to process the Bank
Reconciliation on a daily or weekly basis.  This increases efficiency and reduces the
volume of transactions to be tagged.

The tagged transactions will be displayed
until a month end is processed.

---


# 5.3 Cash Book - Enquiries


## [531.htm]

1.
Banking Account

On the Cash Book Enquiry Menu, the Data
Status Window will indicate from which directory the reports will be extracted.

The default directory is the current
directory.

8
Click on the Quick Functions
drop down menu at the top of the screen to access archive directories.

At this Enquiry Menu, the Bank Account is
displayed in chronological (date) order.
The closing balance is displayed on the top left hand side of all
screens i.e. it is not necessary to page down through to the last transaction
in order to view the final balance.

To
display detailed information with regard to Debtors, Deposits, Other Income and
Other Payments:

(a) Highlight the selected entry.

(b) Click on

. A detailed
listing of all the line items making up the one transaction on the Bank Account
will be displayed.

(c) Press [Escape] to return
to the Bank Account Enquiry.

(d) Click on

to return to the Cash Book Enquiry Menu.

---

## [532.htm]

2.
Transaction Scroll

(a) At the Start and End Date prompts, insert the required dates or
press [Enter] to accept the default
dates.  The system will default to the
earliest and the latest dates for which there are transactions in the current
period.

(b) At the Scroll / Totals prompt, select Scroll to view the entire
transaction listing or select Totals to view a summary total all the
transactions. Press [Enter].

(c) Select the Transaction Type or click on 5. All of the Above to
include all transaction types.

(d)  Use the Scroll Bar or Arrow [â, á] keys to up or down the screen.

(e)

to view totals.

(f)

to sort display by Transaction Details,
Transaction Type, Transaction Number or Transaction Date.

(g) Press

to return to the Cash Book Enquiry Menu.

---

## [533.htm]

3.
Monthly Category Analysis

The Monthly Category Analysis will display
on the screen a year-to-date calendar analysis of Income or Expenses.

(a) Select Category type:

(b) The Income / Expenses Category Enquiry Screen will be displayed.

(c) Click on

to select an Income or Expense Category
Number.

(d) Click on

to display figures graphically.

(e) Click on

to return to the Cash Book Enquiry Menu.

---

## [534.htm]

4.
Category & Tax Analysis

Category and Tax Analysis will display the
Current Month’s Income / Expense details and the VAT thereon.

(a) Select Category type:

Result: The Income / Expense Totals plus Vat
are displayed.

(b) Click on

to the Totals per Income / Expense Category.

(c) Select a specific category by clicking on the category to highlight
the category.

(d) Click on

to display a detailed breakdown of all entries
making up the total of the selected category.

(e) Click on

to return to the Cash Book Enquiry Menu.

---

## [535.htm]

5.
Post Dated Cheque Listing

(a) Select Order of Listing:

(b) Result: The Post Dated Cheque Listing will be displayed.

(c) Use the

and

keys to navigate through the Listing.

(d) Click on

to Print Listing.

(e) Click on

to return to the Cash Book Enquiry Menu.

---

## [536.htm]

6.
Control Summary

The Control Summary will be displayed as
follows:

(a) Click on

to print Control Summary.

(b) Click on

to return to the Cash Book Enquiry Menu.

---


# 7.1 General Ledger - Maintenance


## [711.htm]

1.
Chart of Accounts

Chart of Accounts Maintenance
Options:

8
Creating New Accounts

8
Modifying Existing Accounts

8
Deleting Existing Accounts

Creating a New General Ledger Account

(a) Select

,

1. Maintenance, 1. Chart of Accounts.

(b) At the Account Number prompt, enter the new Account number. Press
[Enter].

To view current listing:

Press [Enter] at the account number prompt and the Account listing will be
displayed alphabetically.

to display the listing by Account Number.

(c) At the Account Name prompt, enter the new account name. Press
[Enter].

(d) Indicate whether the account is an Income Statement or a Balance
Sheet account. I/B

(e) At the Debit/Credit prompt, indicate whether the account is normally
a debit or a credit account. D/C

(f) Click on

to save the account.

(g) Click on

to return to the General Ledger Maintenance
Menu.

Modifying an Existing Account Category

(a)
Select

,

1. Maintenance, 1. Chart of Accounts.

(b)
At the Account Number prompt,
enter the account number or use the select facility to view and select from the
current Chart of Accounts. Press [Enter].

(c)
Edit the Account Name, Income
Statement or Balance Sheet selection. Press [Enter].

Note: Do not amend the Debit/Credit Account
selection as this should only be done after Year End.

(d)
Click on

to save the account.

(e)
Click on

to return to the General Ledger Maintenance
Menu.

Deleting an Existing Account Category

(a)
Select

,

1. Maintenance, 1. Chart of Accounts.

(b)
At the Account Number prompt,
enter the Account number you wish to delete or alternatively use the select
facility to view and select the account number from the current Chart of
Accounts.

(c)
Click on

or press the [Page Down] key.

(d)
At the Delete Account prompt,
click on

.

(e)
Click on

to return to the General Ledger Maintenance
Menu.

Note: A General Ledger Account cannot be
deleted:

- if there have been any transactions recorded in the account in the current
month or current year.

- where there is a batch entry relating to the account which has not been updated.

Note: Once Adjustments have been made to the
Chart of Accounts, the Report formats must be checked to ensure correct
calculation of Totals. Call your Accpick Support Consultant for Assistance.

---

## [712.htm]

2.
Budgets

Budget
Options:

8

Creating and Entering Budgets

Creating and Entering Budget Values for
each month of the Year.

(a) Select

,

1. Maintenance, 2. Budgets.

(b) At the Account Number prompt, enter the account number or use the
select facility to view and select from the current Chart of Accounts. Press [Enter].

(c) Enter the budget values for each month of the year.

Note: Should the value be identical for each
month of the year, insert the value in the first month and press the [Page
Down] key for automatic repeat into all remaining months.

(d) Continue to enter further budget values by selecting another account
number.

(e) Click on

to return to the General Ledger Maintenance Menu.

---

## [713.htm]

3.
Standing Journals

Journals that are repeated frequently with the same values may be
set up as Standing Journals to be repeated on a Monthly, Quarterly or Bi-Annual
basis.

Creating a Standing Journal

(a) Select

,

1. Maintenance, 3. Standing Journals.

(b) At the Descriptor prompt, enter an identifying reference

(c) At the Times to Apply prompt, enter the frequency – Monthly(12),
Quarterly(4), Bi-Annually(2), Annually(1) or (999) for Continuous.

Note : Standing Journals require two entries
in order to comply with the double entry system of accounting – one a debit
entry and the other a credit entry.

(d)  Click on

to insert the Journal details.

(e) Enter the Account number or use the select facility to view and
select from the current Chart of Accounts.

(f) Enter the Journal Details, Amount and indicate whether the journal is
a Debit or a Credit value.

(g) Click on

to save.

(h) Click on

to insert the Contra Account details.

Note: Only Journals which are in balance will
be saved. Total Debits must equal Total Credits.

Journal adjustments can be made by clicking
on:

,

,

(i)

to print journal
entry.

(j) Click on

and click on

to save.

(k) Click on

to return to the Maintenance Menu.

---

## [714.htm]

4.
Integration

The
Integration Procedure transfers transactions from the Debtors, Stock, Creditors
and Cash Book Modules to the General Ledger.

(a) Select:

,

1. Maintenance, 4. Integration

(b) Select for each Module – Debtors, Stock Control, Creditors, Cash
Book.

A list of transaction transfers and their
corresponding debit and credit accounts and their narrations will be displayed.

(c) Go through each of these and ensure that every entry has a Dr
Account Detail and a Credit Account Detail in place. Failing to check this will
result in the integration being aborted.

to remove transaction transfers.

to repeat setup of an Account Number and
Account Narration.

to print the listing.

Note: Stock Integration :

Stock Inter branch transfers (IBT’s) do not need Account Details if IBT’s are
not used.

---

## [715.htm]

5.
Report Formats

Report Format Options:

8
Income Statement

8
Balance Sheet

Note: Please consult your Accpick Consultant before making any
adjustments to the layout of the Income Statement or Balance Sheet.

Formatting Reports

(a) Select

,

1. Maintenance, 5. Report Format.

(b) From the Options Menu select the Income Statement or Balance
Sheet to format.

The Chart of Accounts is displayed in
numeric order. Automatic line numbering is allocated.

(c)

to insert line details: Page Headers, Column
Headers, Sum Total or Add Total Lines.

(d)

to edit the Report Format and make the
necessary adjustments.

(e)

to print report format.

(f) Click on

to return to the Main GL Menu.

(g)

Click on

to save.

Note: Once the Report formats have been set and saved, adding a new
account in the Chart of Accounts will automatically position such account in
the Report format in numeric account order and adjust the required calculations
automatically.

Note: It is recommended that once the Income
Statement and Balance sheet Report Formats have been setup and saved, the
formats be checked whenever any new accounts have been added or deleted from
the Chart of Accounts.

---


# 7.2 General Ledger - Transactions


## [721.htm]

1.
Journal Entry

Journal Entry Options:

8
Create a New Journal Entry

8
Edit an Existing Journal
Entry

Creating a New Journal Entry

(a) Select

,

2. Transactions, 1. Journal Entry.

(b) At the Options Menu select New
Batch.

(c) Select Period to post journal – Current or Past Periods. Usually Current
Period.

Note : Journals require two entries in order
to comply with the double entry system of accounting – one a debit entry and
the other a credit entry.

(d)  Click on

to insert the Account Number.

(e) Enter the Account Number or use the select facility to view and
select an account from the current Chart of Accounts.

(f) Enter the Journal Details, Date of Entry, Journal Reference i.e
Source Document/Report, Amount and indicate whether this entry has a Debit or
Credit Value.

(g) Click on

to accept entry.

(h) Click on

to insert the Contra Account details. See (e)
and (f).

(i) Click on

to accept entry.

Note: Only Journals which are in balance will
be saved.

(j) Journal adjustments can be made by clicking on:

to edit a line

to delete an entire Journal

to remove one entry of the Journal.

(k) Click on

.

(l) Click on

to save the batch.

Note:
This entry now sits in a BATCH – it is not yet posted to the relevant account.
This is processed in:

, 2. Transactions, 4. Batch Update.

Editing an Existing Batch

(a)
Select

,

2. Transactions, 1. Journal Entry.

(b) At the Options Menu select Edit.

(c) Use the arrow keys to highlight the Batch to be edited and press
[Enter].

(d) Use the arrow keys to highlight the journal entry to edited and
press[Enter].

(e) Amend the Journal details as required.

(f) Click on

to accept.

(g) Click on

.

(h) Click on

to save the batch.

---

## [722.htm]

2.
Standing Journal Update

This facility updates the Standing Journals set up in General
Leger Maintenance, Standing Journals.

Any adjustments to Standing Journals must be done in Maintenance prior to running the Update
Maintenance routine

Standing Journal Update Routine.

(a) Select

,

2. Transactions,

2. Standing Journal Update.

Note: The number of Journals and Total Debit
and Credit Value is displayed.

(b) At the Ready to Proceed prompt, select [Ok].

(c) At the Options Menu select Update Options:

Update and Print

Update and No Print

Abandon Update should you wish to
abort the process.

(d) Accpick will automatically update the standing Journals and post to the
relevant accounts.

---

## [723.htm]

3.
Integration Transfer

Refer to Integration Procedures.

---

## [724.htm]

4.
Batch Update

This facility posts to the relevant
accounts ALL journal entries in the batches selected for updating.

Batch Update Routine.

(a) Select

,

2. Transactions, 4. Batch Update.

All Batches awaiting update are displayed in Batch Number order.

(b) Click on individual batch followed by

to tag batches to be updated.

(c) Click on

(d) Select Update Options:

Update & Print

Update No Print

Abandon Update

(e) Accpick will automatically update the Batch and return to the General
Ledger Transaction Menu.

---


# 7.3 General Ledger - Enquiries


## [731.htm]

1.
Ledger Account

This facility allows you to view all
entries and balances relating to individual General Ledger Accounts.

The Account Details for the selected
account are displayed by Reference Number, Date, Details, Debit and Credit
Value, Total, Entry Type, Source and Station number.

The Opening Balance and all subsequent
entries for the period are displayed.

to print Ledger Account.

---

## [732.htm]

3.
Outstanding Batches

This facility displays all “unposted”
batches.

to print highlighted Journal Batch

to print all outstanding Journal Batches.

---

## [734.htm]

4.
Trial Balance

This facility displays the Trial Balance in
Account or Name order with the option to exclude zero balances.

The Year to Date Values are displayed in
the last two columns on the right.

to print Trial Balance with selected Date on
Trial Balance.

to export trial balance for spreadsheet or
word processor import.

---

## [735.htm]

5.
Income Statement

This facility displays the Income Statement
with the following layout options:

Current Period and Year to Date

Current Periods and Last Year

Current Period and Budget Values

Budgeted Values – 12 Months

Current Budget Variance Year to Date Budget
Variance

Actual Values – 12 Months.

to print Income Statement with options to
print Account Number and Zero Balance items.

Note: This Date is for Report Header purposes
only. The Income Statement Values are the latest values for the current/archive
period selected.

to export Income Statement into a spreadsheet
format. (*.csv). File Name displayed as Incstat.csv.

User is prompted for Filename e.g.
APR06IS.csv.

The file will be created as APR06IS.csv in
the Accpick Data folder.

In the Appendix, see Notes on Opening a
.csv file in a spreadsheet format.

---

## [736.htm]

6.
Balance Sheet

This facility displays the Balance Sheet

to print Balance Sheet with options to select a
Date; include/exclude Account Numbers and include/exclude Zero Balances.

to export Balance Sheet into spreadsheet format
(*.csv). File Name is exported as balsheet.csv in the Accpick Data folder.

In the Appendix, see notes on opening a
.csv file in a spreadsheet format.

---


# 8. Utilities - top level


## [81.htm]

System
Parameters

System Parameter Options:

8
Address Details

8
Password Maintenance

8
Tax Codes and Costing

8
Transaction Details

8
Data Archiving

1. Address Details

(a) At the Address prompt, enter your business address.

(b) At the Vat prompt, enter your business’s vat number.

These details appear on all Point-of-Sale
documents where blank stationery is used as well as on all Creditors’
remittance advices.

(c) At the Options prompt to reset registration number, click on [NO]. Access to the program will be
denied if the registration number is changed. Only change the registration
number on the instruction of an Accpick Consultant.

(d)
Click on

to return to the Utilities Main Menu.

2. Password Maintenance

Password Hierarchy:

Highest Level                            Global Password

Second Level                            Entry
level password per Module

Third Level                                Selectable
functions per Module.

Global
Password

Where this is set, the global password is
needed to gain entry into “Password Maintenance”.

Module
Passwords

Selectable per Module. Option to block
operator from entry into selected module without its specific password.

Functions
Passwords

Maintenance, Transactions, Enquiry and
Report passwords are available for each function.

(a)
At the Module listing, select
the Module.

(b)
At the Password Maintenance
screen, enter passwords for each function level as required.

(c)
Click on

to return to the Utilities Main Menu.

3. Tax Codes and Costing

Five Tax Codes are available.

Tax Code 1 is normally used for the current VAT rate.

Tax Code 2 is normally used for Non – Taxable items.

Costing Method for Stock and Gross Profit
Calculations:

Select A for Average or Select L for Last Cost

Pricing of Goods and Services:

Select I for Inclusive or E for Exclusive of Vat.

4. Transaction Details

Prompts,
Tenders and POS Setups:

Select the option for user access on all POS transactions:

Select Tender Options prompts:

Select POS Parameter Settings:

Select Vat Reference prompt limits:

Select Rounding options:

Select POS and Stock limits:

Select Banking
Detail Headings:

Select Ageing Headers:

Transaction
Numbering:

This displays the next transaction number for each transaction type in your
system.

Headers
and Prompts Set Ups.

Select Invoice Header settings for POS access:

Select Cash Sale Header
Settings

Select Headers and Prompt settings:

Stationery
Details

Select Stationery type.

Message
on Dockets:

Enter message for Invoices, Cash Sales, POS Returns, Statements and Repair
dockets.

Example:

Printer
Setups:

Set printers up according to Station, Function, Type and Port.

5. Data Archiving.

Set Data Archiving ON or OFF.

Suggest this be set to ON.

Where this is set ON, the month-end routine will transfer all the data for the month
into the relevant month’s archive before proceeding with the month-end
clearing.

Enquiries and Reports into archived data
may be made by selecting Month from the Quick Functions Menu on the Enquiry and
Reports Menu.

---

## [82.htm]

Tax
Control

Vat Procedures:   (Recommended on a Monthly basis)

8 Print Tax Control Report for relevant Month

8 Print Transaction Reports

8 Reconcile Transaction Reports with Tax Control Report

8 Complete a copy of the Vat 201 Form for the relevant Month.

Once 2 month cycle is complete:

8 Print Tax control Report for the 2 month cycle, check and complete
SARS form.

Step
1: Print Tax Control Report for the required Month/s.

(a) Select Tax Report Options:

(b)

(c) For a Specific Month, select the month from the listing.

(d) Enter the Date to appear on the report.

(e) Click OK to print report.

Step 2:   Print the Transactions Report for Debtors,
Creditors and Cash Book.

Debtors
Transaction Report select:

(a)

,

(b)
Quick
Function: Select Month to access required month.

(c)
E.
Transactions, Specific
Date Range

(d)
Accept
Default Dates. Do not alter these dates.

(e)
Select
Totals only T.

(f)
Select
All of the Above.,

.

Creditors
Transaction Report select:

(a)

,

(b)
Quick
Function: Select Month to access required month.

(c)
4.
Transaction Report

(d)
Accept
Default Dates – Do NOT alter these dates.

(e)
Select
Totals only T

(f)
Select
All of the Above,

Cash
Book Transactions select:

(a)

,

(b)
Quick
Function: Select Month to Access Archives.

(c)
2.Transactions

(d)
Accept
Default Dates – Do NOT alter these
dates.

(e)
Select
Totals only T

(f)
Select
All of the Above ,

Step 3:   Reconcile the Transactions Reports with the
Tax Control Report to verify the values.

Reports

Item

Vat Value

A

A

A

A

Debtors Transactions

Debtors Transactions

Debtors Transactions

Cash Book Transactions

TAX VALUES on:

Total Invoices

Total Cash Sales

Total Laybye Sales

Other Income

Total

4199.51

4409.70

254.80

210.00

9074.02

Total = A on Tax Control Report

Total

9074.02

Reports

Item

Vat Value

B

B

Creditors Transactions

Creditors Transactions

TAX VALUES on

Total Credit Notes

Total Settlement Disc

Total

434.00

61.40

495.40

Total = B on Tax Control Report

Total

495.40

Reports

Item

Vat Value

C

C

Creditors Transactions

Cash Book Transactions

TAX VALUES on:

Total Invoices

Other Expenses

Total

1449.00

21.00

1470.00

Total = C on Tax Control Report

Total

1470.00

Reports

Item

Vat Value

D

D

Debtors Transactions

Debtors Transactions

TAX VALUES on

Total Credit Notes

Total Cash Returns

Total

439.60

829.10

1268.70

Total = D on Tax Control Report

Total

1268.70

Reports

Item

Vat Value

E

Debtors Transactions

TAX VALUE on

Total Settlement Disc

Total

9.21

9.21

Total = E on Tax Control Report

Total

9.21

Reports

Item

Vat Value

F

F

F

F

F

F

Gross Income includ Vat

Debtors Transaction Report

Debtors Transaction Report

Debtors Transaction Report

Cash Bk Transaction Report

Tax Control Report

TOTAL AMOUNT on

Total Invoices

Add: Total Cash Sales

Add: Total Laybye Sales

Add: Other Income

Less: Exempt& Non Supp

34196.01

35907.61

2074.80

3860.00

(2150.00)

Total = F on
Tax Control Report

Total

73888.42

Step 4: Complete the Vat
201 form

Complete the Vat 201 form using the information provided in the
Tax Control Report as follows:

See Vat 201 example

Training Schedule

Reports

Item

Vat Value

A

A

A

A

Debtors Transactions

Debtors Transactions

Debtors Transactions

Cash Book Transactions

TAX VALUES on:

Total Invoices

Total Cash Sales

Total Laybye Sales

Other Income

Total

Total = A on Tax Control Report

Total

Reports

Item

Vat Value

B

B

Creditors Transactions

Creditors Transactions

TAX VALUES on

Total Credit Notes

Total Settlement Disc

Total

Total = B on Tax Control Report

Total

Reports

Item

Vat Value

C

C

Creditors Transactions

Cash Book Transactions

TAX VALUES on:

Total Invoices

Other Expenses

Total

Total = C on Tax Control Report

Total

Reports

Item

Vat Value

D

D

Debtors Transactions

Debtors Transactions

TAX VALUES on

Total Credit Notes

Total Cash Returns

Total

Total = D on Tax Control Report

Total

Reports

Item

Vat Value

E

Debtors Transactions

TAX VALUE on

Total Settlement Disc

Total

Total = E on Tax Control Report

Total

Reports

Item

Vat Value

F

F

F

F

F

F

Gross Taxable
Income incl Vat

Debtors Transaction Report

Debtors Transaction Report

Debtors Transaction Report

Cash Bk Transaction Report

Tax Control Report

TOTAL AMOUNT on

Total Invoices

Add: Total Cash Sales

Add: Total Laybye Sales

Add: Other Income

Less: Exempt& Non Supp

Total = F on
Tax Control Report

Total

---

## [83.htm]

Index
File Maintenance

Indexing re-sorts the data files for
Current or selected Archive Periods.

Note: This is a single user operation. All
users to log off before this procedure is run or else data corruption may
occur!

This procedure must be run in the following
instances:

8
Immediately after restoring
data from back up.

8
After multiple deletions of
Debtors/Suppliers/Sales Areas/Sales Departments/Income Categories/Expense
Categories. Indexing frees the deleted numbers for re-use.

8
Before Month-End reports are
run.

8

At any time that Enquiries/Reports appear to print irregularly or
reports seem to be distorted, re-index and run the report again.

(a) Select a period to re-index from the listing.

(b) Select a Module to re-index or 5. All Data.

(c) All files will be indexed.

(d) Click on

to return to the Utilities Main Menu.

---

## [84.htm]

File
Clearance

File Clearance Options:

8
Zero Values

8
Create New Files

8
Archive Files

File Clearance is a DANGEROUS operation and
ought to be password protected!. Only to
be run after consulting with Accpick Support and a backup has been done. Failure
to follow these procedures can result in the loss of all data.

Note: This is a single user operation. All
users to log off before this procedure is run or else data corruption may
occur!

1. Zero Values

This will delete all transactions and set all values to zero for the selected
module for the Current period leaving all Masterfile data in place. Masterfile
data includes all Debtors Names, Creditors Names, Stock Codes and Cashbook
Category Names. Transaction numbers will be reset to the default settings.

The General Ledger Module has a separate
File Clearance option.

2. Create New Files

This
destroys all existing data in the selected Modules for the Current period
and creates new blank files.

3. Archive Files

This
destroys selected archive data.

The amount of space occupied on the hard
drive by each archive month will be displayed with an option to delete selected
archives in order to create more space on the hard drive.

---

## [85.htm]

Consolidated
Expenditure

Consolidated Expenditure Options:

8
Specific Month

8
Year-to-Date

This is a screen report of Expenditure
sourced from the Creditors Expense and Cash Book Expense fields for either a specific
month or for Year-to-Date.

1. Specific Month

(a) From the Period listing, select a month.

(b) Enter the date to appear on the report.

(c) Select Yes or No to print zero expenditure categories.

(d) A Consolidated Expense listing by category will be displayed.

(e) Use the

and

keys to navigate through the listing.

(f) Use the

facility to locate Account Categories.

(g) Use the

facility to print the report.

(h) Click on

to return to the Utilities Main Menu.

---

## [86.htm]

Day End

Day End Procedures:

8
Ensure all Users are logged
off.

8
Back Up

8
Print Day End Reports

8
Clear Day End File

8
Check Cashier File has been
Cleared

Previous Day End Procedures:

8
Printing a Previous Day End
Report.

1. Ensure all Users are logged off.

Day End is a single user operation.
Ensure all other uses have been logged off. Return to your desktop.

2. Back Up Daily Files

Note: This backup is of current data only.

(a) Check the Status Bar at the bottom of the screen and ensure all
other Accpick programs have been closed off before continuing. This must be
done at the Server and all the Terminals.

(b) Insert the Disk/CD/Flash
Drive labeled for that day
e.g. Monday into the drive.

(c) Double Click on the Accpick Backup Icon.

(d) Select 1. Daily Backup  The
backup procedure will run automatically.

(e) Once the Backup has completed you will return automatically to the
Backup Utility Main Menu.

(f) Select Exit to return to the Windows/Linux Desktop

(g) Remove the Disk/CD/Flash
Drive and store in a safe
place.

3. Print Day End Reports and Clear Cashier Data

(a)
Insert paper into the printer
for Day End reports

(b) Double Click on the Accpick Icon

(c) Print the STOCK TRANSACTIONS REPORT
for that day.

Stock Control Report:

Select

Select

Select          C.
Stock Transactions

Select 1. Detailed

Select Start and End
Date as being current day

Press enter through
Start and End Code

Select D for Detailed

Select Report Format
2 and report will print

Return to Main Menu

(d) Print the DAY END REPORT:

Day End Report:

Select

Select

Select Current Day
End.

If prompted, select
the default options; Day End options may be automated. The Day End Report will
print.

(e) After all reports have printed successfully, click on YES at the
Clear Daily Totals prompt.

(f) At the Are you Sure? Prompt, click on YES.

4. Check Cashier Values have been Cleared

(a)
Check that Cashier Values have
been cleared by selecting:

,

At Cashier to view, select [Enter] and check
that all values are zeroed.

(b) Exit out of Accpick Xcellence.

Printing a Previous Day End Report

Before a previous Day End can be reprinted
there needs to be at least one POS transaction on the file.

(a)
Select

(b) Select

(c) Select Previous Day End.

The system will display a listing of all Day
Ends for the Current Month.

(d) Select the required Day End to reprint.

(e) Select the default options and the Day End Report will print.

---

## [88.htm]

Data
Integrity Report

The Data Integrity Report will run
automatically.

The Data Integrity Report will scan and
validate

8
Duplicate Stock Codes

8
Stock Markups

8
Stock Movements

8
Account Balances

8
Account Codes

(a) Ensure there is white paper in the printer and the printer is on
line.

(b) Select

.

(c) Select

.

Should there be any discrepancies with
regard to duplicate Stock Codes, Debtors and Creditors Transactions and Balances
and Stock Movements a report detailing these differences will be printed.  The report will indicate the Module and
relevant accounts / stock codes “out of synch”. Call the ACCPICK help desk on
(033) 3433047 should you need assistance in rectifying these discrepancies.

Data Integrity will also auto adjust markup
% in stock maintenance where e.g. goods have been received at a cost different
to last cost but the selling price remains unaltered.

If all is in order, nothing will print.

---


# 8.7 Utilities - Period End and Reporting


## [871.htm]

Period
End and Reporting

Period End Options:

8
Month End – All Modules with
option to exclude Cash book

8
Month End - Cash Book Module.

8

Note: General ledger has its own
Period End Procedure

Year End Options:

8
Year End

8
Archive a Year

1. Month End

Month End Procedures.

There are 6 steps to be taken:

1.      Ensure all users are logged off.

2.      Data Integrity Report

3.      Month End Back up

4.      Period End Routines

5.      Check Month End has been successfully                           completed

6.      Month End Reports

Note: Only Month End once all transactions,
(including interest charging if required), have been processed.

1. Ensure all other users are logged off.

Month End is a single user operation.  Ensure all other uses have been logged off.

2. Data Integrity Report.

(a) Ensure there is paper in the printer and the printer is on line.

(b) Select

.

(c) Select

.

Should there be any duplicate Stock Codes,
discrepancies with regard to Debtors and Creditors Transactions/Balances and
discrepancies with Stock Movements, a report detailing these differences will
be printed.  The report will indicate the
Module and relevant accounts / stock codes “out of synch”. Call the ACCPICK
help desk on (033) 3433047 should you need assistance in rectifying these
discrepancies.

Data Integrity will also auto adjust markup
% in stock maintenance where e.g. goods have been received at a cost different
to last cost but the selling price remains unaltered.

If all is in order, nothing will print.

3. Month-End Backup

(a)
Return to your desktop and check
the Status Bar at the bottom of the screen to ensure all other Accpick programs
have been closed off before continuing.

(b) Insert the Disk /CD/Flash Drive
labeled for the month e.g. March into the drive.

(c) Double Click on the Accpick Backup Icon.

(d) Select 2. Monthly Backup  The
backup procedure will run automatically.

(e) Once the Backup has completed you will return automatically to the
Backup Utility Main Menu.

(f) Select Exit to return to the Windows/Linux Desktop

(g) Remove the Disk/CD/Flash
Drive and store in a safe
place.

4. Period End Routines

(a)
Select

(b) Select

(c) Select Month End All Modules.

Note: This excludes the General Ledger, which
has its own Period End procedure.

(d) Select Month to month end e.g. March.

(e) Select Month End Options:

Age Debtors Credit
Balances               NO

Monthly Backup been done?                YES

Include Cash Book?                    NO/Yes

NO     If Bank Statement still needs to be
reconciled

YES    If Bank Statement has been reconciled. The
system                   will prompt for
the Start Date of the New Month for                   the
Cash Book Opening Balance.

Month End
Cash Book

Note: If
the Cash Book is not included, you will need to Period End the Cash Book
separately once the Bank Reconciliation has been processed and printed.

Select

,

Select

,

Select Month-End Cash Book.

5. Check Month End has successfully been completed

Debtors
in New Month:

Select

,

,

Select 4.
Transactions

If a message is displayed confirming there
are no transactions on file then the Month End procedure has been successful.

If this message is not displayed the Month
End procedure has not been successful. Contact ACCPICK Help Desk on (033)
3433047 before processing transactions in the new month.

Debtors
in Archive Month:

To check that the data has been month ended
in the correct archive:

Select

,

,

Select Month for which period end was run
(e.g. March) from the Quick Functions facility.

Select 4.
Transactions,

Select 1.Date
Selection

The Dates for the Transactions in the
previous month should be displayed e.g.         Start
Date          01/03/2006

End
Date      31/03/2006

Creditors
in New Month:

Select

,

Select 3.
Transaction Scroll

If a message is displayed confirming there
are no transactions on file then the Month End procedure has been successful.

If this message is not displayed the Month
End procedure has not been successful. Contact ACCPICK Help Desk on (033)
3433047 before processing transactions in the new month.

Creditors
in Archive Month:

To check that the data has been month ended
in the correct archive:

Select

,

,

Select Month for which period end was run
(e.g. March) from the Quick Functions facility,3. Transaction Scroll.

The Dates for the Transactions in the
previous month should be displayed e.g.         Start
Date          01/03/2006

End
Date      31/03/2006

Stock
in New Month:

Select

,

Select C.
Stock Transactions

Select 1.
Detailed

Start at Date and Stop at Date – should be
blank.

Stock
in Archive Month:

To check that the data has been month ended
in the correct archive:

Select

,

,

Select Month for which period end was run
(e.g. March) from the Quick Functions facility,

Select C.
Stock Transactions

Select 1.
Detailed

The Dates for the Transactions in the
previous month should be displayed e.g.         Start
Date          01/03/2006

End
Date      31/03/2006

Cash
Book in New Month:

Select

,

,

Select 2.
Transaction Scroll

If a message is displayed confirming there
are no transactions on file then the Month End procedure has been successful.

If this message is not displayed the Month
End procedure has not been successful. Contact ACCPICK Help Desk before
processing transactions in the new month.

Cash
Book in Archive Month:

To check that the data has been month ended
in the correct archive:

Select

,

,

Select Month for which period end was run
(e.g. March) from the Quick Functions facility

Select 2.
Transaction Scroll

The Dates for the Transactions in the
previous month should be displayed e.g.         Start
Date          01/03/2006

End
Date      31/03/2006

6. Month End Reports

Month End Reports may either be processed
before or after the Period End Routines have been completed.

If Period end has been completed, then the
Reports must be accessed via the Archives, i.e. at the Report Menu, select the
month from the Quick Functions facility. The Data Status Block on the Report
Enquiry Menu will always indicate which directory you are in. The default
directory is the current directory.

This section requires that the printer be
on-line.

The following reports are recommended:

Reports

Menu
Process

Debtors Control Enquiry

The Control
balance should agree to the Age Analysis balance.

A Summary of
Opening Balance, Invoices, Credit Notes, Payments, Settlement Discounts,
Debit and Credit Journals,
Interest Charged and the New Control Balance is displayed.

,

Quick Function:
Select Month to Access Archives.

2. Total Debtors
Summary

3. Control Enquiry

Age Analysis

Age Analysis cont/d

Listing of
Debtors with Total of each account outstanding analysed into 30, 60, 90, 150,
180 days, amount and optional date last paid and telephone number.

Report has
weekly and monthly options.

Select

,

Quick Function:
Select Month to Access Archives.

B. Age Analysis

2. Monthly

Enter Month End
date

Select Apha / Numeric order

Start at Area–Press Enter.

End at Area–Press Enter

Totals T

Space between lines (1)

Include PDC Y/N

Print last paid, tel numbers and credit limits Y/N

Select All with Balances

Statements

Produce
Statements for account customers.  Use
Accpick paper for monthly statement run.

Select

,

Quick Function:
Select Month to Access Archives.

C. Statements

1. Current Period.

Blank / Pre-Printed

Address Details

Enter date to appear on Statements

Exclude Zero Balances

Enter Statement Message, if required

Statement Sequence Alpha / Numeric A/N

Select From Short Name/
Account Name

Select To Short Name/Account Name

Print for a specific area No

Print Open Item Statements as Balance Brought Forward O/B

Print a line-up or Statement print

Departmental
Analysis

Select

,

Quick Function:
Select Month to Access Archives.

D Departmental Analysis.

4.Cash /account Sales

Leave the Default Start and Stop Dates.

Transaction
Report

Reports on all
account related transactions. The system will default to earliest and latest
date for which there are transactions. Do
NOT alter these dates.

Totals
Report:

Select

,

Quick Function: Select Month
to Access Archives.

E Transactions.

Specific Date Range

Select Default Dates – Do not alter
these dates.

Select Totals only T Print
Report

Detailed
Report

Go back and print
detailed reports only for those transaction types printed in the Totals
Report above

Select

,

Quick Function: Select Month
to Access Archives.

E Transactions.

Specific Date Range

Select Default Dates – Do not alter
these dates.

Select Detailed D

Select from the Transaction list the transaction type required

Print Report

Repeat until all detailed reports have been printed for the selected
transaction types.

Reports

Menu
Process

Transaction
Report

Reports on all
account related transactions. The system will default to earliest and latest
date for which there are transactions. Do
NOT alter these dates.

Totals
Report:

Select

,

Quick Function: Select Month
to Access Archives.

C Stock Transactions

2. Total Quantities

Select Start and End Default Dates – Do
not alter these dates.

Select default Departments

Sort by Supplier / Department

Detailed
Report

Optional – not required
if printing detailed report on a daily basis

Select

,

Quick Function: Select Month
to Access Archives.

C Stock Transactions

1. Detailed

Select Default Start and End Dates – Do
not alter these dates.

Select Detailed D

Select format of print required.

Stock
Valuation

Stock
Valuation cont/d

Select

,

Quick Function: Select Month
to Access Archives.

D Stock Valuation

3. All Values

Select Departments

Select Detailed or Totals

Date to Print on Report: Month End Date

New Page per Department Y/N

Select Valuation Option: Last Cost / Average.

Value Negatives Y/N

sort by Department Code or Description.

Gross
Profit

Lists total
sales, gross profit, gross profit % for the current month and cost

Select

,

Quick Function: Select Month
to Access Archives.

H Gross Profit

2 Totals Only

Current Month

Enter Month End Date for Report Date.

Select Default Departments

Stock
Received / Returned

Select

,

Quick Function: Select Month
to Access Archives.

I Stock Received / Returned

Process for both Report Types 1 and 2

Option for report by Date/Dept/ Supplier and Dept

Reports

Menu
Process

Creditors Control Enquiry

The Control
balance should agree to the Age Analysis balance.

A Summary of Opening Balances, Invoices, Credit Notes, Payments, Settlement
Discounts, Debit and Credit Journals, Interest Charged and the Control Balance is
displayed.

Select

,

Quick Function: Select Month to Access Archives.

2. Total Creditors Summary

2. Control Enquiry

Age Analysis

Select

,

Quick Function: Select Month
to Access Archives.

2. Age Analysis

1. Account Balances Only.

Select Apha / Numeric order A/N

Print Zero Balances Y/N

Print last paid details and terms details Y/N

Print our Account Number and Supplier Banking Details Y/N

Date on Report: Enter Month End Date

Transaction
Report

Transaction
Report cont/d

Repeat until all
detailed reports have been printed for the selected transaction types.

Reports on all account related transactions. The system will default to
earliest and latest date for which there are transactions. Do NOT alter these dates.

Totals
Report:

Select

,

Quick Function: Select Month
to Access Archives.

4 Transaction Report.

Select Default Dates – Do NOT alter
these dates.

Select Totals only T,

Detailed
Report

Go back and
print detailed reports. Select only those transaction types printed in the
Totals Report.

Select

,

Quick Function: Select Month
to Access Archives.

4. Transaction Report.

Select Default Dates – Do not alter
these dates.

Select Detailed D

Select required transaction type from the list

Expense
and Tax Report

Select

,

Quick Function: Select Month
to Access Archives.

5.Expense and Tax Report.

Expense and Tax Analysis

Alphabetical or Numeric order A/N

Report on Zero Expenses Y/N

Date on Report: Enter Month End Date

Start and Stop at Expense Category: Leave Defaults

Stock
on RFC

Select

,

7. RFC Controls

4.Vale of Stock RFC

Select
Month from Archive

Select specific Department Y/N

Once the cash book reconciliation has been
completed, balanced, cash book transactions printed and Period End for the Cash
Book has been processed, proceed with the following reports:

Reports

Menu
Process

Control Summary

Select

,

6.control Summary

Date on Printout: Enter Month-End date.

Banking
Account

Select

,

Quick Function: Select Month
to Access Archives.

1.Banking Account

Print Consolidated Report C

Date on Report: Enter Month End Date

Transaction
Report

Transaction
Report cont/d

Repeat until all
detailed reports have been printed for the selected transaction types.

Reports on all account related transactions. The system will default to
earliest and latest date for which there are transactions. Do NOT alter these dates.

Totals
Report:

Select

,

Quick Function: Select Month
to Access Archives.

2 Transactions

Select Default Dates – Do NOT alter
these dates.

Select Totals only T

Detailed
Report

Go back and print
detailed reports. Select only those transaction types printed in the Totals
Report above

Select

,

Quick Function: Select Month
to Access Archives.

2. Transactions

Select Default Dates – Do not alter
these dates.

Select Detailed D

Select required transaction type from the list

Category
and Tax Analysis

1. Income

2. Expenses

3. Cash Income and Tax

4. Cash Expenses & Tax

5. Historical Category

Select

,

Select 3.Category and Tax
Analysis

Process for each
of the following

1. Income , 2. Expenses ,3. Cash Income and Tax ,

4. Cash Expenses and Tax or 5. Historical Categories

Report on Zero Values Y/N

Date on Report: Enter Month End Date

Detailed
Category Analysis

1. Income

2. Expenses

Select

,

Quick Function: Select Month
to Access Archives.

4. Detailed Category

1. Income.

or

2. Expenses

Print in Category Order C

From and To Category: Select Default

Date on Report: Enter Month End Date

In order to facilitate the completion of
the Vat 201 return, the tax control report must be printed every month. Refer to notes for Utilities – Tax Control.

Record the data on a photocopy of the Vat
201 return, marked for the current month.

Reports

Menu Process

Tax
Control

(Monthly)

Select

,

Specific
Month

Date on Report: Enter Month
End Date.

Where the return is rendered on a 2 month
basis, combine the detail recorded for the applicable months, as described
above. Compare the results of this calculation to the 2 Month Vat Cycle report, which is printed as follows:

Reports

Menu Process

Tax
Control

(2
Month Cycle)

Select

,

2 Month Vat Cycle

Date on Report: Enter Month
End Date.

---

## [873.htm]

2. Period End

Period End Options:

8
Year End - Procedures

8
Year End - Reports

Year End Procedures.

The Year-End Clearance will reset to zero all
year to date values in the current directory.

This procedure should be carried our only after the Month End procedures for the
last month of the financial year have been completed.

1. Ensure all other users are logged off.

Year End is a single user operation.
Ensure all other uses have been logged off.

2. Year End Routines

(a)
Select

,

(b) Select: Year-End.

(c) Select All Modules.

(d) At the Continue prompts, click Yes.

(e) The Year End procedure will run automatically.

---

## [874.htm]

3.
Archive-a-Year

Note: It is important that all Day End / Period
End and Year End routines have been finalised for your specific Year End, BEFORE
proceeding.

Data will be copied to another directory i.e.
data in the archives Mar 2005 to Feb 2006 currently residing in \DATA will be
copied to a new directory e.g. \0006DATA from where it will be accessed via the
Quick Function: Switch Company.

1. Ensure all other users are logged off.

Archive a Year is a single user operation.  Ensure all other uses have been logged off.

2. Archive a Year

(a)
Select

,

(b)
Select: Archive a Year.

(c) At the Company Name prompt, press enter to accept default name or
amend as required.

(d) At the Data Directory prompt, press enter to accept the default
directory or amend as required.

Note: The Company name and Data Directory
must be unique. NO special characters, symbols, *, - , etc to be included in
the name.

Check Year End Archiving

(a)
At the Accpick Main Menu,
select Switch Company from the Quick Functions drop down Menu.

(b)
Highlight Company Name and press
[Enter].

(c)
Only Enquiry and Report Menu’s
are accessible in the Archive Year.

---


# Gas Controller (gas_gen.acc) — Custom Add-on Module

**Not part of the standard ApX Manual** — this is a site-specific customisation (hence
the "gas" in `accpickxgas`) bolted onto standard Accpick Xcellence. It manages an
**LPG / gas cylinder exchange and hire business**: clients are delivered full cylinders,
return empties, are charged a hire fee on cylinders held, and are periodically invoiced.
Reconstructed from embedded strings in the binary (no manual exists for this module,
so menu wording below is inferred from program strings, not verbatim manual prose).

## Gas Controller Main Menu

### 1. Transactions
- **D/Note Capture** — Delivery Note Capture: records cylinders delivered and cylinders
  returned for a client account on a given date/area/salesman ("Cylinders Taken",
  "Cylinders Returned"). Supports "Cylinder Exchange Only" (straight swap, no charge)
  vs a priced delivery.
- **Generate Invoice from D/Notes** — batch-converts outstanding Delivery Notes into
  Tax Invoices (uses the standard Accpick invoice/credit-note transaction types:
  INVOICE, CASHSALE, CNOTE, SORDER, etc.), and can print an "Invoice Line-up" first
  for review.
- **D/Note + Invoice Capture and Print** — combined single-step capture and invoice
  print, skipping the two-stage D/Note-then-invoice flow.
- **Allocate Cylinder Movements** — reconciles/matches outstanding cylinder movements
  (taken vs returned) against client balances; flags accounts with an outstanding
  cylinder balance.

### 2. Maintenance
- **Client Contracts** — contract-specific pricing per client, stored in `CONTRACT.DBF`
  (keyed by account). Lets a specific debtor be locked to negotiated gas prices,
  separate from standard stock pricing.
- **Price Changes** — maintains the gas price file (`GASMAST`/`GasPrices`): set/move
  prices up or down by a percentage or amount, cost price vs selling price,
  inclusive vs exclusive of VAT, per stock line. Warns if a price would sell below
  cost price.

### 3. Reports
- **Delivery Notes Report** — list of Delivery Notes over a date range.
- **Contract Pricing Report** — "Gas Contract Pricing as at [date]" per client.
- **No Activity** — clients with no cylinder movement in the period.
- **Cylinder Holding** — "Cylinder Holding as at [date]": quantity of cylinders each
  client currently holds (can print zero-holding accounts too).
- **Invoice Line-ups** — pre-invoice review listing of what's about to be billed.
- **Movement by Area** — cylinder movement (taken/returned) grouped by
  Area/Salesman ("Cylinder Movement by area report").

### 4. Utilities
- **Index** — rebuilds indexes on the gas data files (`GASMAST`, `GASTRN`, `GASTRND`,
  `CONTRACT.DBF`) — single-user operation.
- **Month-End** — closes the gas transaction period: processes Hire Charges
  ("Gas Cylinder Hire Charge"), emails Hire Invoices as PDF attachments, and clears
  the transaction file. Guards against re-running month-end twice, and requires all
  D/Notes to be invoiced first ("Please Generate invoices for ALL Delivery Notes
  before proceeding"). Records which station/user ran month-end.
- **Clear Accpick Deletions** — purges records tied to items deleted in the main
  Accpick Stock Master.
- **Synchronize Pricing** (`AP_SYNCH_GASPRICES`) — resets the Gas price file to match
  the main Accpick Stock Master prices ("This will set prices in Gas files to be the
  same as Accpick Stock Master prices"). Locks the gas price file against concurrent
  edits while running.

## Data files referenced
- `GASMAST` — Gas Master: per-client cylinder/pricing master
- `GASTRN` / `GASTRND` / `GASTRNO` — Gas Transactions (delivery notes, movements)
- `CONTRACT.DBF` — client contract pricing
- `DAREA` — delivery/sales areas (shared with core Accpick Area/Salesman structure)

## Integration with core Accpick
Gas Controller invoices post through the same transaction types as standard POS/Debtors
(`INVOICE`, `CASHSALE`, `CNOTE`, `SORDER`, `SORDERA`, `AUTOCN`, etc.), so gas sales flow
into the same Debtors, Stock, and General Ledger integration as any other Accpick sale —
it's a specialised front-end for capturing cylinder-based transactions, not a separate
accounting system.


# 6. Purchase Orders

**New module found via `pdf/POrders.pdf` — not present in the older `help/*.htm` export.**
The old 2006-2012 HTML manual had no `6xx.htm` files (menu numbering jumped from
Stock Control=3 to Creditors=4, skipping 6 entirely in the old set). The Dec-2017 PDF
set confirms module 6 on the Main Menu is **Purchase Orders**, sitting between Cash
Book (5) and General Ledger (7).

## Purchase Orders Menu
1. Transactions — New Purchase Order, Cancel Purchase Order, Stock Received
2. Enquiries — Delivery Date, Specific Stock Items
3. Reports
4. Utilities — Index Files, Reset P/Order Qty's

### 1. Transactions

**New Purchase Order**
(a) Select 6.Purch Orders, 1.Transactions, 1.New Purchase Order. PO is created at
Cost/Retail per System Setup default ([Page Down] at Order Date to alter).
(b) Enter Supplier number (or search Creditor listing), confirm details.
(c)-(e) Enter Order Date, Delivery Date; choose whether to auto-extract stock items.
(f)-(h) If extracting, choose All Stock Items and an Order Layout: "Month to Date
Sales and Quantity on Hand" or "Re-Order Quantity and Quantity to Order".
(i)-(k) On the Purchase Order Creation screen, use Order(*) to order an item at its
existing cost, or Special Deal(/) if the cost price is changing. Total Landed Cost
excl. Vat is displayed.
(l)-(r) Insert(+) to add items not in the extract; enter Stock Code, Quantity, Last
Cost (defaults to last cost, editable — effective on receipt), Tax Code. Adjustments:
Delete(-), Expense Cat(\) to capture costs like transport (pulled from Creditors
Module expense categories), Special Deal(/) for qty+cost edits, Order(*) for
quantity-only edits, Comment(/) for no-value comment lines.
(s)-(v) End(ESC) to update, select Update, choose print options.

**Cancel Purchase Order**
Enter/select the Order Number, view PO details, End(ESC) to cancel, confirm Yes.

**Stock Received** (Goods Received Note)
Updates Stock, Supplier's Balance and Vat Controls simultaneously (per System
Parameter setup) — or stock only, depending on setup.
(a) Enter/select Order Number. (b) Confirm Invoice Date (suggest: date goods
received). (c) Enter Supplier's Invoice Number. (d) Confirm Additional Reference
(e.g. PO number). (e) Choose extraction: "Items with Quantity Ordered" or "Items
with No Quantity" (manual entry).
Line adjustments: Locate(\) to find a stock code, Edit Qty(=) to correct quantity
received/net cost. When the GRN balances with the supplier's invoice, End(ESC) to
update, confirm Yes, choose print options.
Note: where goods are short-delivered or cost changes, options exist to print a
Delivery Variance and to automatically create a Back Order.

### 2. Enquiries

**Delivery Date** — lists all outstanding POs within a date range by Order Number,
Date Ordered, Supplier Name, Exclusive Value Due. Find(\) to search by PO number,
Toggle Display(Tab) to switch between Date Ordered/Expired Delivery Date views,
Totals(=) for value due, Print(*) to print the listing.

**Specific Stock Items** — shows all outstanding POs containing a given stock code:
PO Date, Expected Delivery Date, PO Number, Supplier Name, Quantity Due, Expected
Landed Cost.

### 3. Reports
| Report | Options | Output |
|---|---|---|
| Outstanding POs by Delivery Date | Start/End dates | PO details by delivery date |
| Outstanding POs by Stock Items | Stock codes | PO details by stock item |
| Outstanding POs by Supplier | Supplier names | Order #, Date Ordered, Expiry Delivery Date, Exclusive Value Due |
| Reprint a Purchase Order | outstanding POs only | reprints a copy |
| Back Orders | — | back orders per supplier |
| Pre Orders | supplier names, include costs | planning aid |
| Delivered Orders | — | all received orders |

### 4. Utilities
- **Index Files** — resorts PO data files for the current period.
- **Reset Purchase Order Quantities** — resyncs "quantity on order" values in the
  Stock Master against the actual outstanding Purchase Orders.

---

# Note on `pdf/` folder PDF manuals vs. the `help/*.htm` manual

The user later added a `pdf/` folder containing 8 module PDFs
(`PointOfSale.pdf`, `Debtors.pdf`, `StockC.pdf`, `Creditors.pdf`, `CashBook.pdf`,
`GL.pdf`, `Utilities.pdf`, `POrders.pdf`) plus a feature-comparison sheet
(`Accpick-detailed-list.pdf`), alongside what appears to be a live production data
directory (`.dbf` files — not documentation, not processed here).

Comparison findings:
- **`PointOfSale.pdf` is line-for-line identical** in procedure content to the
  `help/1*.htm` pages already compiled above (same screenshots, same steps) — just
  re-paginated as one continuous per-module PDF ("Printed 29-Dec-17" cover date, but
  individual page footers retain original authoring dates back to 2005-2006). This
  confirms the `pdf/` set is the same underlying "ApX Manual" library, packaged
  differently, not a rewritten/updated manual.
- **Purchase Orders (module 6) is new** — genuinely absent from the old `help/*.htm`
  export — and has been transcribed in full above.
- The remaining module PDFs (Debtors, StockC, Creditors, CashBook, GL, Utilities)
  were not individually re-transcribed here, since the Point-of-Sale comparison
  showed the content is identical to what's already compiled in the sections above;
  re-processing all ~600+ pages across the remaining 6 PDFs would just duplicate
  content already captured, at high cost. If discrepancies matter for a specific
  procedure, tell me which one and I'll pull that exact page.
- **`Accpick-detailed-list.pdf`** is a current (undated internally, filename
  suggests 2025) sales/marketing feature-comparison sheet from Accpick Automotive
  Solutions (PTY) LTD (member of the POSeSYS Group, accpick.co.za), claiming "+126
  features". It lists many capabilities not documented anywhere in the 2005-2017
  manual set: Cloud server sync/backup/reporting, Ubuntu 16 servers, Scale Weighing
  software for Hawkers, Warehouse Orders, Remote Salesman Ordering, Group Reporting,
  Email/SMS marketing and reminders, Bulk recurring invoicing, Supplier catalogue
  download/import (Bosal, Dunlop), Loyalty Programs (BSA, Dunlop), Multiple Branch
  Centralisation (dynamic ledger departments, stock/price/currency/rep/ledger/
  creditor/debtor centralisation), Recall Documents, Bills of Quantity, Stock Serial
  Numbers, Workshop User module. **None of these newer features are documented in
  the manual content compiled above** — they postdate the 2005-2017 manual set and
  are not covered by any file found in this project directory. If you need details
  on how any of them actually work, that would require newer documentation this
  install doesn't appear to have, or direct testing in the live system.
