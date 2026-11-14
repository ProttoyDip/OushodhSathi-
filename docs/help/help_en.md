# Sathi app guide (English)

> **Needs native-speaker review.** Sathi answers only from this guide. Every `id` matches the Bangla guide.
> `{home}` is the family's home page (`/p/<id>`).

## start.what

group: Getting started
question: What does OushodhSathi do?
phrasings: what is this app for | what does the app do | how does it work
route: {home}
answer: OushodhSathi reads photos of every medicine strip and box at home and builds one list. Fixed rules look for the same medicine twice or risky combinations. You see a result only after a pharmacist or doctor confirms it.

## start.who

group: Getting started
question: Who is the app for?
phrasings: who should use it | is it for my parents | who is it made for
route: {home}
answer: For people who look after the medicines of an elderly parent or relative, especially when medicines come from several doctors or shops.

## start.add-member

group: Getting started
question: How do I add a family member?
phrasings: add a new patient | add my mother | make a list for someone else
route: /start
answer: On the first page, tap "Start for your family". Enter a name, age and conditions (optional) and create the list.

## scan.how

group: Scanning
question: How do I scan medicines?
phrasings: how do I take photos | how to scan | how do I add photos of medicines
route: {home}/scan
answer: On the home page tap "Scan medicines". Take a separate photo of each strip, box or prescription, up to 12 at a time, then tap "Read them".

## scan.good-photo

group: Scanning
question: How do I take a good photo?
phrasings: photo is not clear | best way to photograph a strip | what light should I use
route: {home}/scan
answer: Put the strip flat, near a window or light. Fit the side with the writing fully in the frame and avoid shiny glare.

## scan.cut-strip

group: Scanning
question: What if the strip is cut or half?
phrasings: cut strip | half strip | the name is cut off
route: {home}/scan
answer: Photograph the part where the medicine name and strength are printed. Add a photo of the box if you have it. If it still can't be read, you can type the name on the next page.

## scan.blurry

group: Scanning
question: What if the photo is blurry?
phrasings: blurry photo | photo is out of focus | it can't read my photo
route: {home}/scan
answer: Remove the blurry photo and take it again: hold the phone still and tap once on the writing to focus. Anything that could not be read clearly is marked "Please check".

## scan.prescription

group: Scanning
question: Can I scan a prescription?
phrasings: scan a prescription | doctor's paper | handwritten prescription
route: {home}/scan
answer: Yes, you can add prescription photos too. Handwriting can be hard to read, so look at each name when you check the list.

## scan.manual

group: Scanning
question: How do I add a medicine by hand?
phrasings: type a medicine myself | add manually | add a medicine without a photo
route: {home}/confirm
answer: At the bottom of the checking page, open "Add a medicine by name". Type the name and strength as printed on the strip and tap "Add".

## check.edit

group: Checking the list
question: How do I fix a wrong name?
phrasings: how do I correct it | the name is wrong | how do I edit a medicine
route: {home}/confirm
answer: Tap "Edit" on the medicine card, type the right name and strength, and tap "Save". If the name is right, just tap "Correct".

## check.please-check

group: Checking the list
question: What does "Please check" mean?
phrasings: dashed card | why is the card marked | orange dashed border
route: {home}/confirm
answer: It means the photo could not be read with full confidence, or the medicine is not in our list. Compare the name with the strip and tap "Correct" or "Edit".

## check.web

group: Checking the list
question: What does "Found on the web, not verified" mean?
phrasings: found on the web | internet result | why does it say not verified
route: {home}/confirm
answer: The medicine was not in our own list, so it was looked up on the internet. It is treated as uncertain until a pharmacist confirms it.

## check.times

group: Checking the list
question: How do I set when a medicine is taken?
phrasings: choose morning noon night | set the times | change the time of a medicine
route: {home}/confirm
answer: On each card tap morning, noon or night, as written on the prescription. To change the time of a confirmed medicine, tap "Edit times".

## review.who

group: Review
question: Who checks my list?
phrasings: who will look at this | which doctor sees it | who reviews it
route: {home}/status
answer: A registered pharmacist or doctor looks at every finding and confirms it. Serious ones go to a doctor, the rest to a pharmacist.

## review.how-long

group: Review
question: How long does checking take?
phrasings: how long will it take | when will I get the result | how many days
route: {home}/status
answer: Usually within a day. The home page shows the progress, and Sathi's card tells you when it is done.

## review.confirmed

group: Review
question: What does "confirmed" mean?
phrasings: confirmed meaning | what does checked mean | reviewed meaning
route: {home}/results
answer: It means a pharmacist or doctor looked at the finding and confirmed it is real. You are only ever shown confirmed findings.

## review.why-wait

group: Review
question: Why don't results show straight away?
phrasings: why is there a delay | why can't I see results now | why wait
route: {home}/status
answer: Machines make mistakes, and a wrong warning can cause fear or harm. So nothing is shown until a person has confirmed it.

## results.colors

group: Results
question: What do red and amber mean?
phrasings: what does red mean | what does orange mean | what do the colours mean
route: {home}/results
answer: Red means a doctor looked at it because it matters more. Amber means a pharmacist looked at it. Each one also has a word and an icon.

## results.explanation

group: Results
question: How do I read the explanation?
phrasings: I don't understand the explanation | what does the text mean | explain the result
route: {home}/results
answer: Each result names the medicines involved and the note from the pharmacist or doctor. If something is unclear, send a question with "Ask the pharmacist".

## passport.print

group: Passport
question: How do I print the medicine passport?
phrasings: print the passport | get it on paper | how to print
route: /passport/{id}
answer: Open "Medicine passport" from the home page and tap "Print". It prints clearly in black and white on A5 paper.

## passport.whatsapp

group: Passport
question: How do I send the passport on WhatsApp?
phrasings: share on whatsapp | send the passport | share the passport
route: /passport/{id}
answer: Tap "Print", choose "Save as PDF", then send the file on WhatsApp. Or send a screenshot of the passport.

## passport.doctor

group: Passport
question: What should I show the doctor?
phrasings: what to take to the doctor | before the doctor visit | what to bring to the clinic
route: {home}/visit
answer: Show the medicine passport at every doctor visit. The "Before the doctor visit" page puts the medicines, blood pressure and your questions together.

## passport.emergency

group: Passport
question: What does the QR code on the passport do?
phrasings: what is the qr code | emergency page | scan the qr
route: /passport/{id}
answer: The QR code opens an emergency page with only the medicines, allergies and an emergency contact. You can switch it off any time from the passport page.

## refill.how

group: Refills
question: How will I know a medicine is running out?
phrasings: medicine running out | refill reminder | when will it finish
route: {home}/report
answer: If you enter "Pills left" on the list, Sathi tells you when a medicine will run out within five days. Check the prescription before buying more.

## bp.add

group: Blood pressure
question: How do I add a blood pressure reading?
phrasings: add bp | log blood pressure | enter pressure reading
route: {home}/report
answer: On the report page tap "Add a blood pressure reading". Type the top and bottom numbers from the machine, or take a photo of the machine.

## sathi.can

group: Sathi
question: What can Sathi do?
phrasings: what can you do | what can I ask | how can you help
route: {home}
answer: I tell you the next thing to do and help you use the app. I send questions about medicines to the pharmacist.

## sathi.cant

group: Sathi
question: Why doesn't Sathi answer questions about medicines?
phrasings: why won't you answer | are you a doctor | why can't you tell me about my medicine
route: {home}/questions
answer: I am not a doctor, so I don't answer about medicines, doses or illness. I send your question to the pharmacist, who will answer it.

## privacy.store

group: Privacy
question: What information do you keep?
phrasings: do you keep my photos | what data do you store | where is my data
route: {home}
answer: We keep the medicine list, the checked results and the blood pressure you enter. Photos are deleted right after they are read. Patient names are never sent to an AI model.

## privacy.delete

group: Privacy
question: How do I delete our data?
phrasings: delete my data | remove my account | erase everything
route: {home}/questions
answer: Ask for deletion with "Ask the pharmacist". Our team deletes the whole list and all its data.

## privacy.who-sees

group: Privacy
question: Who can see our list?
phrasings: who can see it | is it private | can others see my list
route: {home}
answer: Only people who have your family's private link, and the reviewing pharmacist or doctor. Give the link only to people you trust.

## share.family

group: Privacy
question: How do I show the list to my brother or sister?
phrasings: send the link to my brother | share with family | let my sister see it
route: {home}
answer: On the home page tap "Share with family". It sends a private link they can use to see the list.

## access.language

group: Language and accessibility
question: How do I change the language?
phrasings: switch to bangla | show in english | change language
route: {home}
answer: Tap "English" or "বাংলা" in the top right corner. The whole app changes at once.

## access.text-size

group: Language and accessibility
question: How do I make the text bigger or hear it read aloud?
phrasings: text is too small | bigger text | read it to me
route: {home}
answer: Making the text larger in your phone's settings also makes the app's text larger. Tap "Listen" next to Sathi's answers and today's medicines to hear them, if your phone has a Bangla voice.
