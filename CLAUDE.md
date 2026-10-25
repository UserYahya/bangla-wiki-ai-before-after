# Bangla Wikimedia before and after AI: session project

Always reply to the user in Bengali (বাংলা). Slide text and speech are in Bengali, using Bengali digits.

## What this project is

A session at Bangla WikiConference 2026 (30 Oct – 1 Nov 2026; theme "Open Knowledge, Collaboration, Sustainable Future"), by Muhammad Yahya. Accepted as a **Demonstration, 20 minutes** (talk about 16 minutes, then Q&A).
Title: "এআই-এর আগে ও পরে: এক দশকের পরিসংখ্যানে বাংলা উইকিমিডিয়া প্রকল্পগুলোর পাঠক, সম্পাদক ও টেকসই ভবিষ্যৎ"

It compares Bangla Wikipedia and its sister projects before and after generative AI, using Wikimedia data from January 2016 to September 2026.

## Files

- `scripts/bangla_wiki_data.py`: monthly readers, editors and content metrics for Bangla projects, six Indic Wikipedias and English, plus World Bank internet users. Output in `data/raw`, `data/derived`, `data/summary`.
- `scripts/extra_data.py`: hourly reading rhythm (Bangladesh time, all and by desktop/mobile web), weekday rhythm, top articles, Content Translation publications, deletions under speedy-deletion criterion স১৫, AI-tagged pages, readers by country, edits by editor type, today's snapshot. Output in `data/extra`. `--only step,step` runs selected steps.
- `deck/`: copy of the deck source (`deck.json`, `slides/*.html`). The live deck is the claude.ai Slides artifact https://claude.ai/artifact/7EaJLdrQxbTxSJWMwBkgbc ; the user may edit it there, so read the artifact before changing slides.
- GitHub (public): https://github.com/UserYahya/bangla-wiki-ai-before-after — linked from the thanks and method slides. Commits use the account's noreply email, set in this repo's local git config only.
- `notes/speech_bn.md`: full speech, built from the slides' speaker notes. `notes/proposal_bn.md`: proposal answers (the accepted version on eventyay differs slightly).

## Method decisions

- Year-to-year comparisons use the January–September monthly average of each year.
- Periods: pre-AI 2017–2019; COVID 2020–2021; early AI Dec 2022 – Jun 2024; AI mainstream Jul 2024 onwards.
- "Automated" traffic only exists from April 2020. WMF reclassified March–August 2025 traffic with new bot rules (Diff, 17 Oct 2025); earlier data keeps the old rules.
- Active editors = 5+ content edits a month = sum of the API's 5..24, 25..99 and 100.. buckets (an earlier version wrongly used only 5..24).
- Hourly data is converted to Bangladesh time (UTC+6). Country data is bucketed and rounded up by WMF; Bangladesh is not listed.
- Content Translation share = published en→bn translations ÷ new pages by registered humans (approximate).

## Key findings (Jan–Sep averages, 2024 → 2026 unless stated)

- Machines (crawlers + automated) are 70.6% of bnwiki pageviews in 2026 (40.5% in 2024; English 31.6%). Automated bots beat humans in 7 of 9 months of 2026.
- Human pageviews 2.49 crore → 90 lakh (−64%); −43% vs 2019. Total traffic −26%; automated ×3.2; crawlers −22%. Unique devices −46%.
- Index 2016 = 100: bnwiki 432 in 2024 vs Bangladesh internet users 341; bnwiki 157 in 2026.
- Hourly: human reading peaks at 9 pm, lowest at 4 am. 9 pm human views −70%, 4 am −41%; the human rhythm keeps its shape, so the decline is real readers, not removed bots. Estimate of real decline revised from 26–64% (proposal) to 46–64%.
- Mobile web humans 2.21 crore → 63 lakh (−72%); desktop humans 26 → 27 lakh (+6%); automated bots on desktop about ×6, on mobile web ×2.
- Ekushe: "আন্তর্জাতিক মাতৃভাষা দিবস" in February: 19K (2016) → 2.43 lakh (2024) → 58K (2026). Language Day/Movement was the top article in all 9 Februaries with data, 2016–2025.
- Other wikis, human pageviews: hi −71%, bn −64%, mr −63%, ta −55%, ml −53%, te −46%, ur −19%, en −14%.
- Active editors 269 → 255 (−5%), 224 in 2019; Hindi −44%. 100+ edit editors 41 (2019) → 44.
- New accounts 1,974 (2019) → 1,103 (−44%); human edits per new account 11 → 27. Growth mentors: 23 (≈48 newcomers per mentor a month).
- Sister projects up: Wikisource +20% views/+28% devices; Wiktionary +11%/+28%; Wikibooks +10%/+26%; Wikiquote +157%/+68%; Wikivoyage +3%/+37%.
- Content Translation ≈ 55–64% of new human-created articles in 2022–2025 (≈10% before 2019; 31% in 2026).
- Speedy deletion criterion স১৫ (pages entirely created by AI) added 26 Aug 2025; 12 articles deleted under it by Jul 2026; 12 pages carry the AI-generated tag.
- About 0.9 human edits a minute in 2026 (≈18 during a 20-minute talk).

## Open tasks

1. Fill placeholders: contact on the thanks slide (`[ইমেইল বা উইকি ব্যবহারকারী পাতা]`), `[এক লাইনে নিজের পরিচয়]` in the cover's notes.
2. The repo has no license yet; ask the user before adding one.
3. Never invent statistics or quotes. Use only numbers from `data/`, verified primary sources, or ones the user supplies.
