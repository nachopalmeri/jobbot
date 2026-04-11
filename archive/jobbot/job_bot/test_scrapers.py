"""Test rápido del scraper con LinkedIn AR + fuentes remotas."""
import sys
sys.path.insert(0, ".")
from job_scraper import JobScraper
import config

scraper = JobScraper()
keywords = ["python", "backend", "fullstack junior"]
location = "Buenos Aires Argentina"

print(f"Keywords: {keywords}")
print(f"Location: {location}")
print(f"Sources: {[k for k,v in config.SOURCES_ENABLED.items() if v]}")
print()

jobs = scraper.search_all(keywords, location)

print(f"\n{'='*60}")
print(f"TOTAL JOBS ENCONTRADOS: {len(jobs)}")
print(f"{'='*60}")
for i, job in enumerate(jobs[:15], 1):
    print(f"\n[{i}] {job['title']}")
    print(f"    Empresa: {job['company']}")
    print(f"    Ubicación: {job['location']}")
    print(f"    Fuente: {job['source']}")

filtered = JobScraper.apply_negative_filter(jobs, experience_level="junior")
print(f"\nDespués del filtro negativo: {len(filtered)} jobs (de {len(jobs)})")
print("\nJobs después de filtro:")
for i, job in enumerate(filtered[:10], 1):
    print(f"  [{i}] {job['title']} ({job['source']})")
