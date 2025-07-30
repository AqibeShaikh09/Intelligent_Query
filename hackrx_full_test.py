import requests
import time
import difflib

# Hackathon leaderboard test parameters
API_URL = "http://localhost:8000/hackrx/run"
BEARER_TOKEN = "fd4d7c6b3d2f4441c504368af8eafd59025b77053a8123fd9946501c5ae23612"  # Hackathon leaderboard token
PDF_URL = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
questions = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
    "Does this policy cover maternity expenses, and what are the conditions?",
    "What is the waiting period for cataract surgery?",
    "Are the medical expenses for an organ donor covered under this policy?",
    "What is the No Claim Discount (NCD) offered in this policy?",
    "Is there a benefit for preventive health check-ups?",
    "How does the policy define a 'Hospital'?",
    "What is the extent of coverage for AYUSH treatments?",
    "Are there any sub-limits on room rent and ICU charges for Plan A?"
]
expected_answers = [
    "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
    "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
    "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months. The benefit is limited to two deliveries or terminations during the policy period.",
    "The policy has a specific waiting period of two (2) years for cataract surgery.",
    "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person and the donation complies with the Transplantation of Human Organs Act, 1994.",
    "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year. The maximum aggregate NCD is capped at 5% of the total base premium.",
    "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break. The amount is subject to the limits specified in the Table of Benefits.",
    "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7, a fully equipped operation theatre, and which maintains daily records of patients.",
    "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit, provided the treatment is taken in an AYUSH Hospital.",
    "Yes, for Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured. These limits do not apply if the treatment is for a listed procedure in a Preferred Provider Network (PPN)."
]
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "documents": PDF_URL,
    "questions": questions
}
print("\n--- HackRx Leaderboard Full Test ---")
start_time = time.time()
response = requests.post(API_URL, headers=headers, json=payload)
end_time = time.time()
print("Status code:", response.status_code)
resp_json = response.json()
answers = resp_json.get("answers", [])
print("\nRaw answers from API:")
for i, ans in enumerate(answers):
    print(f"Q{i+1}: {ans}")
# Fuzzy accuracy calculation
correct = 0
fuzzy_matches = []
for i, (ans, exp) in enumerate(zip(answers, expected_answers)):
    ratio = difflib.SequenceMatcher(None, ans.strip().lower(), exp.strip().lower()).ratio()
    match = ratio > 0.7  # 70% similarity threshold
    fuzzy_matches.append(match)
    if match:
        correct += 1
    print(f"Q{i+1}:\nExpected: {exp}\nGot: {ans}\nFuzzy Match Ratio: {ratio:.2f} | Pass: {match}\n")
total = len(questions)
accuracy = correct / total * 100 if total else 0
avg_response_time = (end_time - start_time) / total if total else 0
print(f"\n--- KPI Results ---")
print(f"Overall Score: {accuracy:.2f}%")
print(f"Accuracy Ratio: {correct}/{total}")
print(f"Average Response Time: {avg_response_time:.2f}s per question")
if 'processing_info' in resp_json:
    print("Token Usage:", resp_json['processing_info'].get('token_usage'))
