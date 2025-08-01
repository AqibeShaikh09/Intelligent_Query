
import requests
import time
from sentence_transformers import SentenceTransformer, util

# Update these variables
API_URL = "http://localhost:3000/hackrx/run"
HACKRX_BEARER_TOKEN= "fd4d7c6b3d2f4441c504368af8eafd59025b77053a8123fd9946501c5ae23612"  # Replace with your actual token

# Leaderboard-style test: PDF URL and questions
PDF_URL = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
questions = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
]

# Expected answers for accuracy check (fill in with correct answers for your policy)
expected_answers = [
    "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
    "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
]

headers = {
    "Authorization": f"Bearer {HACKRX_BEARER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "documents": PDF_URL,
    "questions": questions,
    "prompt": "Answer each question concisely and directly, using only information found in the provided policy document. Do not add extra context or disclaimers. If the answer is not found, reply 'Not mentioned in document.'"
}

start_time = time.time()
response = requests.post(API_URL, headers=headers, json=payload)
end_time = time.time()

print("Status code:", response.status_code)

resp_json = response.json()
answers = resp_json.get("answers", [])

# Print raw answers for debugging
print("\nRaw answers from API:")
for i, ans in enumerate(answers):
    print(f"Q{i+1}: {ans}")

# Semantic similarity scoring
model = SentenceTransformer('all-MiniLM-L6-v2')

# Accuracy calculation
correct = 0
for i, (ans, exp) in enumerate(zip(answers, expected_answers)):
    # Hackathon-style semantic similarity for leaderboard accuracy
    emb_ans = model.encode(ans, convert_to_tensor=True)
    emb_exp = model.encode(exp, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(emb_ans, emb_exp).item()
    match = similarity > 0.7  # 70% threshold, adjust as needed for hackathon
    if match:
        correct += 1
    print(f"Q{i+1}:\nExpected: {exp}\nGot: {ans}\nSemantic Similarity: {similarity:.2f}\nMatch: {match}\n")

total = len(questions)
accuracy = correct / total * 100 if total else 0
avg_response_time = (end_time - start_time) / total if total else 0

print(f"\n--- KPI Results ---")
print(f"Overall Score: {accuracy:.2f}%")
print(f"Accuracy Ratio: {correct}/{total}")
print(f"Average Response Time: {avg_response_time:.2f}s per question")

# Token usage (if available)
if 'processing_info' in resp_json:
    print("Token Usage:", resp_json['processing_info'].get('token_usage'))