-- =====================================================================
-- Quarry queries for the Bangla Wikimedia "before vs after AI" talk
-- Run at https://quarry.wmcloud.org (log in with your Wikimedia account,
-- click "New query", choose the database shown above each query, Submit).
-- Download results with "Download data" -> CSV.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Q1. New Bangla Wikipedia articles created with Content Translation,
--     per month. Compare with new_articles_by_humans.csv from the script
--     to get the share of new articles that start as translations.
-- Database: bnwiki_p
-- ---------------------------------------------------------------------
SELECT LEFT(rev_timestamp, 6) AS month,
       COUNT(*)               AS content_translation_articles
FROM revision
JOIN page           ON rev_page   = page_id
JOIN change_tag     ON ct_rev_id  = rev_id
JOIN change_tag_def ON ctd_id     = ct_tag_id
WHERE page_namespace = 0
  AND rev_parent_id  = 0
  AND ctd_name       = 'contenttranslation'
  AND rev_timestamp >= '20160101000000'
GROUP BY month
ORDER BY month;


-- ---------------------------------------------------------------------
-- Q2. Bangla on Wikidata (current snapshot): how many items have a
--     Bangla label and a Bangla description. Can take several minutes.
-- Database: wikidatawiki_p
-- ---------------------------------------------------------------------
SELECT wby_name                     AS term_type,
       COUNT(DISTINCT wbit_item_id) AS items_with_bangla
FROM wbt_item_terms
JOIN wbt_term_in_lang ON wbit_term_in_lang_id = wbtl_id
JOIN wbt_type         ON wbtl_type_id         = wby_id
JOIN wbt_text_in_lang ON wbtl_text_in_lang_id = wbxl_id
WHERE wbxl_language = 'bn'
  AND wby_name IN ('label', 'description')
GROUP BY wby_name;


-- ---------------------------------------------------------------------
-- Q3. Where do new Bangla articles come from? New articles per year,
--     split by whether the creator's account was less than 30 days old.
--     Shows whether newcomers are still creating content.
-- Database: bnwiki_p
-- ---------------------------------------------------------------------
SELECT LEFT(rev_timestamp, 4) AS year,
       SUM(TIMESTAMPDIFF(DAY, STR_TO_DATE(user_registration, '%Y%m%d%H%i%s'),
                              STR_TO_DATE(rev_timestamp,     '%Y%m%d%H%i%s')) < 30) AS by_newcomers,
       COUNT(*)                                                                    AS all_new_articles
FROM revision
JOIN page  ON rev_page  = page_id
JOIN actor ON rev_actor = actor_id
JOIN user  ON actor_user = user_id
WHERE page_namespace = 0
  AND page_is_redirect = 0
  AND rev_parent_id  = 0
  AND user_registration IS NOT NULL
  AND rev_timestamp >= '20160101000000'
GROUP BY year
ORDER BY year;
