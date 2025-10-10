# Small test harness to verify the fallback Q&A works
from alternative_qa import enhanced_legal_qa

sample_text = open('sample_legal_contract.txt','r',encoding='utf-8').read()
question = "What is the term of the agreement?"

print('Running fallback Q&A test...')
answer = enhanced_legal_qa(sample_text, question, gemini_token=None)
print('Answer:')
print(answer)
