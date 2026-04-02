from email.utils import parsedate_to_datetime
import datetime

now = datetime.datetime.now(datetime.timezone.utc)
date_str = "Sun, 08 Mar 2025 12:34:56 GMT"
job_date = parsedate_to_datetime(date_str)

if job_date.tzinfo is None:
    print("No tzinfo!")
    job_date = job_date.replace(tzinfo=datetime.timezone.utc)

days_old = (now - job_date).days
print(f"Now: {now}, Job: {job_date}, Days: {days_old}")
