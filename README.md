# এআই-এর আগে ও পরে: বাংলা উইকিমিডিয়ার এক দশকের পরিসংখ্যান

বাংলা উইকিসম্মেলন ২০২৬-এর সেশন "এআই-এর আগে ও পরে: এক দশকের পরিসংখ্যানে বাংলা উইকিমিডিয়া প্রকল্পগুলোর পাঠক, সম্পাদক ও টেকসই ভবিষ্যৎ"-এর ডেটা ও কোড।

সব ডেটা উন্মুক্ত উৎস থেকে নেওয়া: [উইকিমিডিয়া অ্যানালিটিক্স API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/), বাংলা উইকিপিডিয়ার [MediaWiki API](https://bn.wikipedia.org/w/api.php) আর [বিশ্বব্যাংক API](https://data.worldbank.org/)। যেকোনো ভাষার সম্প্রদায় নিজের উইকির জন্য স্ক্রিপ্টগুলো চালাতে পারে।

## চালানোর নিয়ম

```bash
pip install requests pandas
export WIKI_CONTACT="আপনার ইমেইল বা উইকি ব্যবহারকারী পাতার লিংক"
python scripts/bangla_wiki_data.py
python scripts/extra_data.py
```

উইকিমিডিয়া API ব্যবহারকারীদের পরিচয় দিতে বলে, তাই `WIKI_CONTACT` দিন। ডেটা জমা হয় `data/` ফোল্ডারে। প্রতিবার চালালে গত সম্পূর্ণ মাস পর্যন্ত নতুন ডেটা আসে। `extra_data.py`-এর নির্দিষ্ট ধাপ আলাদা চালাতে: `python scripts/extra_data.py --only hourly_rhythm,top_articles`।

## কী কী আছে

| ফাইল | কী করে |
|---|---|
| `scripts/bangla_wiki_data.py` | বাংলা উইকিপিডিয়া, পাঁচটি সহপ্রকল্প, ছয়টি ভারতীয় ভাষা ও ইংরেজি উইকিপিডিয়ার মাসিক পেজভিউ (মানুষ, স্পাইডার, স্বয়ংক্রিয় বট), ইউনিক ডিভাইস, সম্পাদক, নতুন অ্যাকাউন্ট, সম্পাদনা ও নতুন নিবন্ধ; বিশ্বব্যাংকের ইন্টারনেট ব্যবহারকারী |
| `scripts/extra_data.py` | দিনের কোন ঘণ্টায় মানুষ ও বট পড়ে, প্রতি বছরের সবচেয়ে বেশি পড়া নিবন্ধ, কনটেন্ট ট্রান্সলেশন, দ্রুত অপসারণের স১৫ ধারায় (এআই-তৈরি পাতা) অপসারণ, দেশভিত্তিক পাঠক, সম্পাদক-ধরনভিত্তিক সম্পাদনা, আর আজকের সারসংক্ষেপ |
| `scripts/quarry_queries.sql` | ঐচ্ছিক Quarry কোয়েরি |
| `data/raw/` | প্রতি মেট্রিকের একটি CSV, প্রতি উইকির একটি কলাম, প্রতি মাসের একটি সারি |
| `data/derived/` | বটের ভাগ, মোবাইলের ভাগ, প্রতি নতুন অ্যাকাউন্টে সম্পাদনা, সক্রিয় সম্পাদক (মাসে ৫+ সম্পাদনা) |
| `data/summary/` | পর্বভিত্তিক সারাংশ, প্রতি বছরের একই মাসগুলোর গড়, ইন্টারনেটের সঙ্গে তুলনা |
| `data/extra/` | `extra_data.py`-এর ফল |
| `deck/` | সেশনের স্লাইডের সোর্স (claude.ai Slides ফরম্যাট) |
| `notes/speech_bn.md` | পুরো বক্তৃতা, স্লাইড ধরে |

## পদ্ধতি নিয়ে কয়েকটি সতর্কতা

- বছরওয়ারি তুলনায় প্রতি বছরের একই মাসগুলোর (জানুয়ারি থেকে শেষ সম্পূর্ণ মাস) গড় নেওয়া হয়েছে, যাতে মৌসুমি ওঠানামা ভুল সংকেত না দেয়।
- পর্ব: এআই-পূর্ব ২০১৭–২০১৯; কোভিড ২০২০–২০২১; প্রাথমিক এআই ডিসেম্বর ২০২২ – জুন ২০২৪; এআই মূলধারা জুলাই ২০২৪ থেকে। জানুয়ারি–নভেম্বর ২০২২ অন্তর্বর্তী সময় হিসেবে বাদ।
- "স্বয়ংক্রিয়" (automated) ট্রাফিকের আলাদা হিসাব শুরু এপ্রিল ২০২০ থেকে; তার আগের বটের ভাগ কম দেখায়।
- উইকিমিডিয়া ফাউন্ডেশন ২০২৫ সালে বট শনাক্তকরণ হালনাগাদ করে এবং মার্চ–আগস্ট ২০২৫-এর ডেটা নতুন নিয়মে পুনঃশ্রেণিবিন্যাস করে ([Diff, ১৭ অক্টোবর ২০২৫](https://diff.wikimedia.org/2025/10/17/new-user-trends-on-wikipedia/))। তার আগের ডেটা পুরোনো নিয়মে আছে, তাই ২০২৪-এর "মানুষ" পেজভিউয়ে এমন বট থাকতে পারে যা এখন ধরা পড়ত।
- দেশভিত্তিক পেজভিউ উইকিমিডিয়া গোপনীয়তার কারণে শ্রেণিবদ্ধ ও ঊর্ধ্বমুখী গোলাকার করে প্রকাশ করে; বাংলাদেশের সংখ্যা সেখানে নেই।

## English summary

Data and code for a Bangla WikiConference 2026 talk comparing Bangla Wikimedia projects before and after generative AI (January 2016 onwards). `bangla_wiki_data.py` pulls monthly readership (human, crawler and automated-bot pageviews, unique devices), editor and content metrics for Bangla Wikipedia, its sister projects, six Indic-language Wikipedias and English Wikipedia; `extra_data.py` adds hourly reading rhythms, top articles, Content Translation output, deletions under the Bangla Wikipedia speedy-deletion criterion for AI-generated pages (S15), readers by country and a current snapshot. Set `WIKI_CONTACT` and run both scripts; change the wiki lists at the top of each script to study another language.

Data: Wikimedia Foundation (CC0 for analytics data), World Bank (CC BY 4.0).
