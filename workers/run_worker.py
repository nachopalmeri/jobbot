"""
CLI to run Celery workers for JobBot.
"""

import argparse
import os
import sys

# Ensure job_bot is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(description='JobBot Celery Worker Manager')
    parser.add_argument(
        'command',
        choices=['worker', 'beat', 'flower', 'purge'],
        help='Command to run: worker (process tasks), beat (schedule tasks), flower (monitor), purge (clear queue)'
    )
    parser.add_argument(
        '-q', '--queues',
        default='default,scraping,notifications,ai_processing',
        help='Comma-separated queue names to process (default: all)'
    )
    parser.add_argument(
        '-c', '--concurrency',
        type=int,
        default=4,
        help='Number of worker processes (default: 4)'
    )
    parser.add_argument(
        '-l', '--loglevel',
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Logging level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Set environment for Celery
    os.environ.setdefault('CELERY_APP', 'workers.celery_app:app')
    
    from workers.celery_app import app
    
    if args.command == 'worker':
        # Start worker
        queues = args.queues.split(',')
        argv = [
            'celery',
            'worker',
            '-A', 'workers.celery_app:app',
            '-Q', ','.join(queues),
            '--loglevel=' + args.loglevel,
            '--concurrency=' + str(args.concurrency),
            '-n', 'worker@%h',
        ]
        app.worker_main(argv)
        
    elif args.command == 'beat':
        # Start scheduler
        argv = [
            'celery',
            'beat',
            '-A', 'workers.celery_app:app',
            '--loglevel=' + args.loglevel,
            '-s', '/tmp/celerybeat-schedule',
        ]
        app.start(argv)
        
    elif args.command == 'flower':
        # Start monitoring
        try:
            import flower
            argv = [
                'celery',
                'flower',
                '-A', 'workers.celery_app:app',
                '--port=5555',
            ]
            app.start(argv)
        except ImportError:
            print("Flower not installed. Install with: pip install flower")
            sys.exit(1)
            
    elif args.command == 'purge':
        # Purge all waiting tasks
        app.control.purge()
        print("All waiting tasks purged.")


if __name__ == '__main__':
    main()
