from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import native_executor as n
candidate=json.loads((n.B/'evidence/ismerim-barbearia/candidate.json').read_text(encoding='utf8'));n.evidence_preflight(candidate)
blocked={'presence_audit':{'test':{'file':str(n.B/'runtime/results/public-barbudus-search-v1/0.html'),'url':'https://www.google.com/search?q=Barbudus','sha256':'TEST_ONLY'}}}
try:n.evidence_preflight(blocked);raise AssertionError('CAPTCHA accepted')
except ValueError as e:assert 'CHALLENGE' in str(e)
print('PASS: genuine Ismerim evidence accepted; CAPTCHA source rejected before qualification/build/publication')