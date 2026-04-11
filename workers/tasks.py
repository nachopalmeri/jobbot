"""
Celery tasks for JobBot background processing.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from ..job_bot.database import Database
from ..job_bot.job_scraper import JobScraper
from ..job_bot.config import DEFAULT_LOCATION

try:
    from ..job_bot.bot import send_job_to_user
except ImportError:
    send_job_to_user = None

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=300,
    soft_time_limit=120,
)
def scrape_jobs_for_user(
    self,
    telegram_id: int,
    keywords: Optional[list] = None,
    location: Optional[str] = None,
    max_age_days: int = 30,
):
    """
    Scrape jobs for a specific user asynchronously.
    
    Args:
        telegram_id: User's Telegram ID
        keywords: List of keywords to search
        location: Location filter
        max_age_days: Max age of job postings
    
    Returns:
        dict with scraped jobs count and new jobs found
    """
    try:
        db = Database()
        scraper = JobScraper()
        
        # Get user profile if keywords not provided
        if not keywords:
            profile = db.get_user_profile(telegram_id)
            keywords = db.get_user_keywords(telegram_id) or db.generate_smart_keywords(telegram_id)
            if not keywords:
                keywords = ["python junior"]
        
        search_location = location or db.get_user(telegram_id).get("location") or DEFAULT_LOCATION
        
        # Perform scraping
        jobs = scraper.search_all(
            keywords,
            search_location,
            max_age_days=max_age_days,
        )
        
        # Filter by user preferences
        profile = db.get_user_profile(telegram_id)
        jobs = JobScraper.apply_negative_filter(
            jobs,
            experience_level=profile.get("experience_level", "junior"),
        )
        
        # Filter modality
        modality = profile.get("job_modality", "cualquiera")
        if modality != "cualquiera":
            jobs = JobScraper.apply_modality_filter(jobs, modality)
        
        # Filter schedule
        schedule = profile.get("job_schedule", "cualquiera")
        if schedule != "cualquiera":
            jobs = JobScraper.apply_schedule_filter(jobs, schedule)
        
        # Check for new jobs (not already seen)
        new_jobs = []
        for job in jobs:
            job_hash = scraper._generate_hash(job)
            if not db.is_job_seen(telegram_id, job_hash):
                new_jobs.append(job)
                db.mark_job_seen(telegram_id, job_hash, job.get("source", "unknown"))
        
        return {
            "telegram_id": telegram_id,
            "total_scraped": len(jobs),
            "new_jobs": len(new_jobs),
            "keywords": keywords,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except SoftTimeLimitExceeded:
        logger.warning(f"Soft time limit exceeded for user {telegram_id}")
        return {
            "telegram_id": telegram_id,
            "error": "timeout",
            "partial": True,
        }
    except Exception as exc:
        logger.error(f"Scraping failed for user {telegram_id}: {exc}")
        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_alert_batch(
    self,
    telegram_id: int,
    job_ids: list,
    batch_id: str,
):
    """
    Send a batch of job alerts to a user.
    
    Args:
        telegram_id: User's Telegram ID
        job_ids: List of job IDs to send
        batch_id: Batch identifier for tracking
    
    Returns:
        dict with delivery status
    """
    try:
        if not send_job_to_user:
            logger.error("Bot not available for sending alerts")
            return {"error": "bot_not_available"}
        
        db = Database()
        scraper = JobScraper()
        
        sent_count = 0
        for job_id in job_ids:
            try:
                job = scraper.get_job_by_id(job_id)
                if job:
                    send_job_to_user(telegram_id, job)
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send job {job_id}: {e}")
        
        # Update batch status
        db.update_batch_status(batch_id, "sent", sent_count)
        
        return {
            "telegram_id": telegram_id,
            "batch_id": batch_id,
            "sent": sent_count,
            "failed": len(job_ids) - sent_count,
        }
        
    except Exception as exc:
        logger.error(f"Alert batch failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
)
def process_cv_analysis(
    self,
    telegram_id: int,
    cv_text: str,
    job_description: Optional[str] = None,
):
    """
    Process CV analysis asynchronously using AI.
    
    Args:
        telegram_id: User's Telegram ID
        cv_text: Extracted text from CV
        job_description: Optional job description for matching
    
    Returns:
        dict with analysis results
    """
    try:
        from ..job_bot.cv_analyzer import analyze_cv, compare_cv_with_offer
        
        if job_description:
            result = compare_cv_with_offer(cv_text, job_description)
        else:
            result = analyze_cv(cv_text)
        
        # Store result in database
        db = Database()
        db.store_cv_analysis(telegram_id, result)
        
        return {
            "telegram_id": telegram_id,
            "analysis_id": result.get("id"),
            "score": result.get("score"),
            "completed": True,
        }
        
    except Exception as exc:
        logger.error(f"CV analysis failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def generate_cover_letter(
    telegram_id: int,
    cv_text: str,
    job_title: str,
    company: str,
    job_description: str,
):
    """
    Generate a cover letter asynchronously.
    
    Args:
        telegram_id: User's Telegram ID
        cv_text: User's CV text
        job_title: Job title
        company: Company name
        job_description: Job description
    
    Returns:
        dict with generated cover letter
    """
    try:
        from ..job_bot.cv_analyzer import generate_cover_letter as cv_generate_cover_letter
        
        cover_letter = cv_generate_cover_letter(
            cv_text,
            job_title,
            company,
            job_description,
        )
        
        # Store in database
        db = Database()
        db.store_cover_letter(telegram_id, cover_letter)
        
        return {
            "telegram_id": telegram_id,
            "cover_letter": cover_letter,
            "generated": True,
        }
        
    except Exception as exc:
        logger.error(f"Cover letter generation failed: {exc}")
        raise


@shared_task
def cleanup_old_jobs():
    """
    Periodic task to clean up old job listings.
    
    Returns:
        dict with cleanup statistics
    """
    try:
        db = Database()
        # Remove jobs older than 90 days
        deleted = db.cleanup_old_jobs(max_age_days=90)
        
        logger.info(f"Cleaned up {deleted} old jobs")
        
        return {
            "deleted": deleted,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Cleanup failed: {exc}")
        raise


@shared_task
def schedule_user_alerts():
    """
    Check all users and trigger alerts for those who need them.
    This is called periodically by the beat scheduler.
    
    Returns:
        dict with scheduling statistics
    """
    try:
        db = Database()
        users = db.get_active_users_with_alerts()
        
        scheduled = 0
        for user in users:
            telegram_id = user["telegram_id"]
            
            # Check if it's time to alert this user
            last_check = user.get("last_check_timestamp", 0)
            interval_hours = user.get("check_interval_hours", 6)
            
            import time
            now = time.time()
            if now - last_check >= interval_hours * 3600:
                # Schedule scraping task
                scrape_jobs_for_user.delay(telegram_id)
                scheduled += 1
        
        logger.info(f"Scheduled alerts for {scheduled} users")
        
        return {
            "scheduled": scheduled,
            "total_active": len(users),
        }
        
    except Exception as exc:
        logger.error(f"Alert scheduling failed: {exc}")
        raise
