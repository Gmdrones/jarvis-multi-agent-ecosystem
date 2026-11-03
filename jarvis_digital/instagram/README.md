# Dedicated public Instagram curation

curation_worker.py reuses only its adjacent browser_profile_jarvis_digital profile. Launch with Python/Playwright; login manually if needed. It never reads cookies/passwords, sends DMs, follows accounts or downloads source media. DroneHub Social is separate.

Create queue/JOB.json with job_id (lowercase letters, digits and hyphens), status QUEUED, and urls containing1..4 exact public Instagram profile/post URLs. Results are written beside the queue item; original public main HTML and observation records with URLs, UTC dates and SHA256 are under curation/JOB. No automatic retry of failed jobs. A STOP_WORKER marker closes the dedicated session cleanly. Existing queue result files prevent replay under the same filename.

Actual validation03/11/2026: studio962-20261103 observed the public profile and3 posts, with12 public post links on the profile. This is reference collection, not automatic business identity/site absence qualification or a grant of media rights. Files/profile data stay local. The site revision uses3 official embeds with responsive framing; it remains dependent on Instagram.
