## Tool Name
MXAPIWOSCHEDULE-SCHEDULEWORKORDER

## Purpose
Schedules an existing Maximo work order: sets its scheduled start, scheduled finish and,
optionally, the lead (the labor code of the person responsible). Use it when a planner asks
to schedule, reschedule, move or assign a lead to a work order.

## Strict Rules
* **Mandatory input**: 'wonum' and 'siteid' identify the work order. If the user gives only a
  work order number, use the user's default site; if the site is still unknown, ask.
* **Dates**: 'schedstart' and 'schedfinish' are ISO 8601 timestamps with time zone, for example
  2026-10-27T08:00:00+03:00. Resolve words like "Monday" or "next week" from today's date and
  confirm the resolved date in the answer. Never invent a date the user did not give.
* **Finish after start**: if the user gives a start and a duration, compute the finish. If the
  finish would be before the start, STOP and ask.
* **Lead**: 'lead' is a labor code (for example WILSON). Pass it only when the user names a
  person. Do not guess.
* **One work order per call**. For several work orders, call the tool once per work order.

## Usage
Use only to change the schedule or lead of a work order. Do not use it to change status,
create work orders or record work.
