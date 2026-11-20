# Glossary

For readers outside Bangladesh, and outside pharmacy. Bangla words are given with a pronunciation guide.

## The product

| Term | Meaning |
| --- | --- |
| **OushodhSathi** (ওষুধসাথী, *oh-shudh-sha-thee*) | "Medicine companion": *oushodh* is medicine, *sathi* is companion |
| **Sathi** (সাথী) | The in-app helper. It answers questions about using the app from a written guide and passes every medical question to a person |
| **Household** | One elderly patient's home and the family members who look after their medicines |
| **Family link** | The private link that opens one household. There are no usernames or passwords for families |
| **Finding** | A possible safety problem raised by a rule, for example the same medicine twice. It reaches the family only after a clinician confirms it |
| **Reviewer** | A registered pharmacist or doctor who confirms or dismisses findings |
| **Medicine passport** | A printable one-page list of a patient's confirmed medicines, grouped by time of day, with a QR code for emergencies |
| **Check-in** | A short daily phone call or WhatsApp message asking whether each dose was taken |
| **Demo household** | Rahima Begum, 68, from Cumilla: an invented patient used for every demo and screenshot |

## How medicines reach patients in Bangladesh

| Term | Meaning |
| --- | --- |
| **Brand vs generic** | The generic is the medicine itself (paracetamol); a brand is a company's name for it (Napa, Ace). Many companies sell the same generic under different brands, which is how a patient can take the same medicine twice without knowing |
| **Strip** | A blister strip of tablets. Families often cut strips into pieces, losing the printed name or expiry |
| **Village doctor** (পল্লী চিকিৎসক, *polli chikitshok*) | A rural health practitioner, often without formal medical registration, who prescribes and sells medicines |
| **Drug shop** (ফার্মেসি / ওষুধের দোকান) | A local pharmacy. Many medicines, including antibiotics, are bought over the counter without a prescription |
| **Outpatient department (OPD)** | A hospital clinic where a doctor sees patients without admitting them |
| **Sehri / iftar** | The pre-dawn and sunset meals during Ramadan. Fasting patients need their medicine times moved, which only a clinician may do |
| **999** | Bangladesh's national emergency number |
| **৳ / BDT** | Bangladeshi taka, the currency |

## Clinical terms used in the rules

| Term | Meaning |
| --- | --- |
| **Duplicate generic** | Two brands containing the same medicine: a risk of a double dose |
| **Therapeutic duplication** | Two different medicines from the same drug class (two blood-pressure medicines of the same type), where usually one is enough |
| **Interaction** | Two medicines that affect each other's action or safety when taken together |
| **Beers Criteria** | The American Geriatrics Society's list of medicines that are risky for people aged 65 and over (2023 update) |
| **Anticholinergic burden** | The combined effect of medicines that block acetylcholine; a high total is linked to confusion and falls in older adults |
| **Look-alike / sound-alike names** | Two brands whose names look or sound similar but contain different medicines, a common cause of mix-ups |
| **Triple whammy** | An ACE inhibitor or ARB, plus a diuretic, plus an NSAID taken together: a known cause of acute kidney injury in older adults |
| **eGFR** | Estimated glomerular filtration rate, a measure of kidney function computed from a creatinine blood test (2021 CKD-EPI equation) |
| **WHO AWaRe** | The World Health Organization's grouping of antibiotics into Access, Watch and Reserve, used to spot antibiotics that should not be bought without a prescription |
| **STOPP/START** | European criteria for medicines older people should stop (STOPP) or might be missing (START) |
| **Polypharmacy** | Taking five or more medicines at the same time |

## Technical terms

| Term | Meaning |
| --- | --- |
| **Deterministic rules engine** | Fixed, tested code that always gives the same answer for the same input. It makes every finding; no AI does |
| **Vision model** | An AI model that reads text from photos (here, mainly NVIDIA Nemotron) |
| **OCR second reader** | A separate text-recognition model that re-reads strength and expiry and flags disagreements for a person to check |
| **Confidence** | The model's own estimate (0 to 1) that it read a medicine correctly. Under 0.75, a person must check it |
| **95% CI** | A 95% confidence interval: the range the true value probably lies in, given a small sample |
| **Hybrid search / RAG** | Finding the right help-guide entry by combining word matching with meaning-based (vector) search |
| **Knowledge graph** | A network of brands, generics, drug classes and rules, used to show a reviewer *why* a finding fired |
| **MCP server** | A Model Context Protocol server that lets AI assistants use the medicine logic through four read-only tools |
