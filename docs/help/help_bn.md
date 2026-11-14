# সাথী অ্যাপ গাইড (বাংলা)

> **Needs native-speaker review.** সাথী শুধু এই গাইড থেকে উত্তর দেয়। প্রতিটি অংশের `id` ইংরেজি গাইডের সাথে মেলে।
> `{home}` মানে পরিবারের হোম পেজ (`/p/<id>`)।

## start.what

group: শুরু
question: ওষুধসাথী কী করে?
phrasings: এই অ্যাপ কী কাজে লাগে | oushodhsathi ki kore | app ta kisher jonno | এটা দিয়ে কী হয়
route: {home}
answer: ওষুধসাথী বাড়ির সব ওষুধের পাতা আর বাক্সের ছবি পড়ে একটি তালিকা বানায়। একই ওষুধ দুইবার বা ঝুঁকিপূর্ণ মিশ্রণ আছে কি না, নিয়ম দিয়ে খোঁজে। একজন ফার্মাসিস্ট বা ডাক্তার নিশ্চিত করার পরই আপনি ফলাফল দেখেন।

## start.who

group: শুরু
question: অ্যাপটি কাদের জন্য?
phrasings: কে ব্যবহার করবে | kara use korbe | baba mar jonno | বয়স্ক মা-বাবার জন্য
route: {home}
answer: যাঁরা বয়স্ক মা-বাবা বা আত্মীয়ের ওষুধ দেখাশোনা করেন, তাঁদের জন্য। বিশেষ করে যাঁরা কয়েকজন ডাক্তার বা দোকান থেকে ওষুধ পান।

## start.add-member

group: শুরু
question: পরিবারের নতুন একজনকে কীভাবে যোগ করব?
phrasings: নতুন রোগী যোগ | notun manush add korbo | ma ke add | আরেকজনের তালিকা বানাব
route: /start
answer: প্রথম পাতায় "আপনার পরিবারের তালিকা বানান" চাপুন। নাম, বয়স আর অসুখ (ঐচ্ছিক) দিয়ে তালিকা তৈরি করুন।

## scan.how

group: স্ক্যান
question: ওষুধ কীভাবে স্ক্যান করব?
phrasings: ছবি কীভাবে তুলব | scan kivabe kori | chobi tulbo kivabe | ওষুধের ছবি দেব কীভাবে
route: {home}/scan
answer: হোম পেজে "ওষুধ স্ক্যান করুন" চাপুন। প্রতিটি পাতা, বাক্স বা প্রেসক্রিপশনের আলাদা ছবি তুলুন, একবারে বারোটি পর্যন্ত। তারপর "পড়ে দেখুন" চাপুন।

## scan.good-photo

group: স্ক্যান
question: ভালো ছবি কীভাবে তুলব?
phrasings: ছবি পরিষ্কার হচ্ছে না | valo chobi | ki vabe chobi tulle porte pare | আলো কেমন হবে
route: {home}/scan
answer: আলোর কাছে, সমান জায়গায় পাতাটি রাখুন। লেখা যে দিকে আছে সেই দিকটা পুরোটা ফ্রেমে আনুন, আর চকচকে আলো এড়িয়ে চলুন।

## scan.cut-strip

group: স্ক্যান
question: পাতা কাটা বা অর্ধেক হলে কী করব?
phrasings: কাটা পাতা | strip kata | ordhek pata | নাম কেটে গেছে
route: {home}/scan
answer: যে অংশে ওষুধের নাম আর শক্তি লেখা আছে, সেই অংশের ছবি তুলুন। বাক্স থাকলে বাক্সের ছবিও দিন। পড়া না গেলে পরের পাতায় নিজে নাম লিখে দিতে পারেন।

## scan.blurry

group: স্ক্যান
question: ছবি ঝাপসা হলে কী করব?
phrasings: ছবি ঝাপসা হলে? | chobi jhapsha | blur hoye geche | ছবি পড়া যাচ্ছে না
route: {home}/scan
answer: ঝাপসা ছবি মুছে আবার তুলুন: ফোন স্থির রাখুন আর লেখার ওপর একবার ট্যাপ করে ফোকাস করুন। যেগুলো ঠিকমতো পড়া যায়নি, সেগুলো "যাচাই করুন" দাগ দিয়ে দেখানো হবে।

## scan.prescription

group: স্ক্যান
question: প্রেসক্রিপশনের ছবি দেওয়া যাবে?
phrasings: প্রেসক্রিপশন স্ক্যান | prescription scan | daktar er kagoj | হাতের লেখা প্রেসক্রিপশন
route: {home}/scan
answer: হ্যাঁ, প্রেসক্রিপশনের ছবিও দিতে পারেন। হাতের লেখা পড়া কঠিন হতে পারে, তাই তালিকা মিলিয়ে নেওয়ার সময় প্রতিটি নাম দেখে নিন।

## scan.manual

group: স্ক্যান
question: হাতে লিখে ওষুধ যোগ করব কীভাবে?
phrasings: নিজে নাম লিখব | hate likhe add | manually add | ছবি ছাড়া ওষুধ যোগ
route: {home}/confirm
answer: তালিকা মিলিয়ে নেওয়ার পাতার নিচে "নাম লিখে ওষুধ যোগ করুন" খুলুন। পাতায় যেমন লেখা, তেমন নাম আর শক্তি লিখে "যোগ করুন" চাপুন।

## check.edit

group: তালিকা
question: ভুল নাম কীভাবে ঠিক করব?
phrasings: কীভাবে ঠিক করব? | nam vul | kivabe thik korbo | edit korbo kivabe
route: {home}/confirm
answer: ওষুধের কার্ডে "বদলান" চাপুন, ঠিক নাম আর শক্তি লিখে "সংরক্ষণ করুন" চাপুন। নাম ঠিক থাকলে শুধু "ঠিক আছে" চাপুন।

## check.please-check

group: তালিকা
question: "যাচাই করুন" দাগ মানে কী?
phrasings: দাগ দেওয়া কার্ড | jachai korun mane | dotted card | কার্ডে কমলা দাগ কেন
route: {home}/confirm
answer: এর মানে ছবিটি পুরোপুরি নিশ্চিতভাবে পড়া যায়নি, বা ওষুধটি আমাদের তালিকায় নেই। ছবির সাথে নামটা মিলিয়ে ঠিক থাকলে "ঠিক আছে", না হলে "বদলান" চাপুন।

## check.web

group: তালিকা
question: "ওয়েব থেকে পাওয়া — যাচাই হয়নি" মানে কী?
phrasings: ওয়েব থেকে পাওয়া | web theke | internet e pawa | যাচাই হয়নি লেখা কেন
route: {home}/confirm
answer: ওষুধটি আমাদের নিজস্ব তালিকায় ছিল না, তাই ইন্টারনেটে খোঁজা হয়েছে। ফার্মাসিস্ট নিশ্চিত না করা পর্যন্ত এটাকে অনিশ্চিত ধরা হয়।

## check.times

group: তালিকা
question: ওষুধ কখন খান তা কীভাবে লিখব?
phrasings: সকাল দুপুর রাত বাছাই | kokhon khay likhbo | somoy set | সময় বদলাব কীভাবে
route: {home}/confirm
answer: প্রতিটি কার্ডে সকাল, দুপুর বা রাত চাপুন, প্রেসক্রিপশনে যেমন লেখা। আগে নিশ্চিত করা ওষুধের সময় বদলাতে "সময় বদলান" চাপুন।

## review.who

group: যাচাই
question: আমার তালিকা কে দেখবেন?
phrasings: এটা কে দেখবেন? | ke dekhbe | kon daktar dekhbe | কে যাচাই করে
route: {home}/status
answer: একজন নিবন্ধিত ফার্মাসিস্ট বা ডাক্তার প্রতিটি বিষয় দেখে নিশ্চিত করেন। জরুরি বিষয় ডাক্তারের কাছে যায়, বাকিগুলো ফার্মাসিস্টের কাছে।

## review.how-long

group: যাচাই
question: যাচাই করতে কত সময় লাগে?
phrasings: কতক্ষণ লাগবে | koto din lagbe | kokhon jabe result | কখন উত্তর পাব
route: {home}/status
answer: সাধারণত এক দিনের মধ্যে। হোম পেজে অবস্থা দেখা যায়, আর শেষ হলে সাথীর কার্ডে জানানো হয়।

## review.confirmed

group: যাচাই
question: "নিশ্চিত" মানে কী?
phrasings: confirmed mane | নিশ্চিত করা হয়েছে মানে | nishchit mane ki | যাচাই হয়েছে মানে
route: {home}/results
answer: এর মানে একজন ফার্মাসিস্ট বা ডাক্তার বিষয়টি দেখে সত্যি বলে নিশ্চিত করেছেন। শুধু নিশ্চিত করা বিষয়ই আপনাকে দেখানো হয়।

## review.why-wait

group: যাচাই
question: ফলাফল সাথে সাথে দেখায় না কেন?
phrasings: সাথে সাথে দেখায় না কেন | result keno dekhay na | eto deri keno | আগে দেখাবে না কেন
route: {home}/status
answer: যন্ত্র ভুল করতে পারে, আর ভুল সতর্কতা ভয় বা বিপদ ডেকে আনতে পারে। তাই একজন মানুষ নিশ্চিত না করা পর্যন্ত আমরা কিছু দেখাই না।

## results.colors

group: ফলাফল
question: লাল আর কমলা রঙের মানে কী?
phrasings: লাল মানে কী | lal mane ki | komola mane | রং দিয়ে কী বোঝায়
route: {home}/results
answer: লাল মানে বিষয়টি ডাক্তার দেখেছেন, কারণ এটা বেশি গুরুত্বপূর্ণ। কমলা মানে ফার্মাসিস্ট দেখেছেন। প্রতিটির সাথে লেখা আর চিহ্নও থাকে।

## results.explanation

group: ফলাফল
question: ব্যাখ্যাটা কীভাবে পড়ব?
phrasings: ব্যাখ্যা বুঝি না | bujhte parchi na | explanation | লেখাটার মানে কী
route: {home}/results
answer: প্রতিটি ফলাফলে কোন ওষুধগুলো জড়িত আর ফার্মাসিস্ট বা ডাক্তারের নোট থাকে। বুঝতে না পারলে "ফার্মাসিস্টকে জিজ্ঞেস করুন" দিয়ে প্রশ্ন পাঠান।

## passport.print

group: পাসপোর্ট
question: ওষুধের পাসপোর্ট কীভাবে প্রিন্ট করব?
phrasings: পাসপোর্ট প্রিন্ট | print korbo kivabe | passport ber korbo | কাগজে বের করব
route: /passport/{id}
answer: হোম পেজ থেকে "ওষুধের পাসপোর্ট" খুলে "প্রিন্ট করুন" চাপুন। এটা A5 কাগজে সাদা-কালোতে পরিষ্কার আসে।

## passport.whatsapp

group: পাসপোর্ট
question: পাসপোর্ট হোয়াটসঅ্যাপে কীভাবে পাঠাব?
phrasings: whatsapp e pathabo | হোয়াটসঅ্যাপ | share korbo | পাসপোর্ট শেয়ার
route: /passport/{id}
answer: "প্রিন্ট করুন" চেপে "PDF হিসেবে সেভ" বেছে নিন, তারপর ফাইলটি হোয়াটসঅ্যাপে পাঠান। বা পাসপোর্টের স্ক্রিনশট পাঠাতে পারেন।

## passport.doctor

group: পাসপোর্ট
question: ডাক্তারকে কী দেখাব?
phrasings: ডাক্তারের কাছে কী নেব | daktar ke ki dekhabo | visit e ki nibo | ডাক্তার দেখানোর আগে
route: {home}/visit
answer: প্রতিবার ডাক্তার দেখানোর সময় ওষুধের পাসপোর্ট দেখান। "ডাক্তারের কাছে যাওয়ার আগে" পাতায় ওষুধ, রক্তচাপ আর আপনার প্রশ্ন একসাথে পাবেন।

## passport.emergency

group: পাসপোর্ট
question: পাসপোর্টের কিউআর কোড কী কাজ করে?
phrasings: qr code ki | কিউআর কোড | emergency page | জরুরি পাতা
route: /passport/{id}
answer: কিউআর কোড একটি জরুরি পাতা খোলে, যেখানে শুধু ওষুধ, অ্যালার্জি আর জরুরি যোগাযোগ থাকে। পাসপোর্ট পাতা থেকে আপনি এটা যেকোনো সময় বন্ধ করতে পারেন।

## refill.how

group: ওষুধ শেষ হওয়া
question: ওষুধ শেষ হওয়ার কথা কীভাবে জানব?
phrasings: ওষুধ ফুরিয়ে যাবে | sesh hoye jabe | refill | কবে শেষ হবে
route: {home}/report
answer: তালিকায় "আর কয়টি বড়ি আছে" লিখে রাখলে, পাঁচ দিনের মধ্যে শেষ হওয়ার আগে সাথী জানাবে। নতুন ওষুধ আনার আগে প্রেসক্রিপশন দেখে নিন।

## bp.add

group: রক্তচাপ
question: রক্তচাপ কীভাবে লিখব?
phrasings: প্রেসার লিখব | bp likhbo | pressure add | রক্তচাপ যোগ
route: {home}/report
answer: রিপোর্ট পাতায় "রক্তচাপ যোগ করুন" চাপুন। মেশিনের ওপরের আর নিচের সংখ্যা লিখুন, অথবা মেশিনের ছবি তুলুন।

## sathi.can

group: সাথী
question: সাথী কী করতে পারে?
phrasings: তুমি কী পারো | tumi ki paro | sathi ki kore | কী জিজ্ঞেস করা যায়
route: {home}
answer: আমি পরের কাজটা কী, তা বলি আর অ্যাপ ব্যবহারে সাহায্য করি। ওষুধ নিয়ে প্রশ্ন ফার্মাসিস্টের কাছে পাঠিয়ে দিই।

## sathi.cant

group: সাথী
question: সাথী ওষুধের প্রশ্নের উত্তর দেয় না কেন?
phrasings: ওষুধের প্রশ্নের উত্তর দাও না কেন | keno uttor dao na | tumi daktar na | ওষুধ নিয়ে বলো না কেন
route: {home}/questions
answer: আমি ডাক্তার নই, তাই ওষুধ, মাত্রা বা অসুখ নিয়ে উত্তর দিই না। আপনার প্রশ্নটা ফার্মাসিস্টকে পাঠাই, তিনি উত্তর দেবেন।

## privacy.store

group: গোপনীয়তা
question: আপনারা কী তথ্য রাখেন?
phrasings: ছবি রাখেন কি | chobi rakhen | ki data rakhen | তথ্য কোথায় থাকে
route: {home}
answer: আমরা ওষুধের তালিকা, যাচাইয়ের ফলাফল আর আপনার লেখা রক্তচাপ রাখি। ছবি পড়ার পরেই মুছে ফেলা হয়, রাখা হয় না। রোগীর নাম কখনো কোনো এআই মডেলে পাঠানো হয় না।

## privacy.delete

group: গোপনীয়তা
question: আমাদের তথ্য মুছব কীভাবে?
phrasings: তথ্য মুছে দিন | data delete | mucche dao | হিসাব বন্ধ করব
route: {home}/questions
answer: "ফার্মাসিস্টকে জিজ্ঞেস করুন" দিয়ে তথ্য মুছে দিতে বলুন। আমাদের দল পুরো তালিকা আর তার সব তথ্য মুছে দেবে।

## privacy.who-sees

group: গোপনীয়তা
question: আমাদের তালিকা কে দেখতে পারে?
phrasings: কে দেখতে পায় | ke dekhte pay | private ki | অন্য কেউ দেখবে কি
route: {home}
answer: শুধু যাঁদের কাছে আপনার পরিবারের ব্যক্তিগত লিংক আছে, আর যাচাইকারী ফার্মাসিস্ট বা ডাক্তার। লিংক শুধু বিশ্বস্ত মানুষকে দিন।

## share.family

group: গোপনীয়তা
question: ভাই-বোনকে তালিকা দেখাব কীভাবে?
phrasings: ভাইকে লিংক পাঠাব | link pathabo | share with family | বোনকে দেখাতে চাই
route: {home}
answer: হোম পেজে "পরিবারের সাথে শেয়ার করুন" চাপুন। এটা একটি ব্যক্তিগত লিংক পাঠায়, যেটা দিয়ে তাঁরাও তালিকা দেখতে পারবেন।

## access.language

group: ভাষা ও সুবিধা
question: ভাষা কীভাবে বদলাব?
phrasings: ইংরেজিতে দেখব | english e dekhbo | bhasha bodlabo | বাংলা ইংরেজি
route: {home}
answer: ওপরের ডান কোণে "English" বা "বাংলা" বোতাম চাপুন। পুরো অ্যাপ সাথে সাথে বদলে যাবে।

## access.text-size

group: ভাষা ও সুবিধা
question: লেখা বড় করব বা শুনব কীভাবে?
phrasings: লেখা ছোট | boro lekha | pore shonao | পড়ে শোনাও
route: {home}
answer: ফোনের সেটিংসে লেখার আকার বাড়ালে অ্যাপের লেখাও বড় হয়। সাথীর উত্তর আর আজকের ওষুধের পাশে "শুনুন" চাপলে পড়ে শোনানো হয়, যদি ফোনে বাংলা কণ্ঠ থাকে।
