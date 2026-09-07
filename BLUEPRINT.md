# The Affiliate Content Engine — Blueprint & Operating Manual
### מקור אמת אחד למערכת. נבנה על StilettoVault, מתוכנן לשכפול לכל תחום שיווק-שותפים.
_עודכן: 2026-09-04_

---

## 0. מה זה, בשורה אחת
מכונה שמזהה מוצרים רווחיים בתחום נבחר, מייצרת להם ויזואל מקצועי (תמונה + וידאו) ב-AI, מפרסמת אותם אוטומטית לרשתות עם לינק שיווק-שותפים, ומודדת מי קנה — עם שני גייטים אנושיים בלבד (אישור מוצר + בחירת קריאייטיב).

**עיקרון-על:** אוטומציה מלאה בקצוות (איתור + הפצה + מדידה), החלטה אנושית רק בשני צמתים שקובעים כסף וטעם.

---

## 1. הארכיטקטורה — הצינור בחמישה שלבים

```
[1] SCOUT          → בוט בוקר סורק מקורות, מסנן לפי נישה, שולח מועמדים לטלגרם
        │             (אישור אנושי #1: ✅/❌ על כל מוצר)
        ▼
[2] PRODUCE (auto) → Space מייצר 4 קריאייטיבים → טלגרם לבחירה
        │             (אישור אנושי #2: בחירת מודעה A/B/C/D)
        ▼
[3] FINALIZE       → overlay של הדיל האמיתי + וידאו keyframe → drop מוכן
        ▼
[4] DISTRIBUTE     → אירוח (GitHub Pages) → תזמון (Zernio) → IG + TikTok
        ▼
[5] MEASURE        → דאשבורד: funnel, קליקים (GA), מכירות (Admitad subid)
```

**מה אוטומטי, מה ידני:**
| שלב | מי מפעיל | גייט אנושי |
|-----|----------|------------|
| Scout (08:00) | Windows Task | אישור מוצר בטלגרם |
| Produce (10:00) | Windows Task → `claude -p` | בחירת מודעה בטלגרם |
| Finalize + Video | Claude (סשן) | — |
| Distribute | `pickup_drop` → Zernio | — |
| Measure | דאשבורד + Task יומי | — |

---

## 2. התשתית — הכלים והחיבורים

| שכבה | כלי | תפקיד | למה נבחר |
|------|-----|-------|----------|
| **איתור** | `daily_heel_scout.py` + `aliexpress_scout.py` | סורק מקורות, מסנן נישה | curl (לא requests — TLS block) |
| **טעם/אישור** | Telegram Bot + `taste_engine.py` | אישור מוצר, למידת טעם | ערוץ מיידי, גייט אנושי טבעי |
| **תור** | `production_queue.json` | מחבר אישור→הפקה | קובץ פשוט, idempotent |
| **הפקה** | Magnific **Space** (`a2796464`) | מקור→4 מודעות→וידאו | node workflow חזותי, Veo 3.1 |
| **runner** | `run_producer.bat` → `claude -p` | מריץ Space אוטומטית | ה-MCP דורש Claude session |
| **overlay** | `overlay.py` (PIL) | דיל אמיתי על התמונה | **לא ממציא מחיר** — דאטה בלבד |
| **וידאו** | Veo 3.1 Lite (keyframes) | נקי→דיל | תומך start+end frames |
| **אירוח** | **GitHub Pages** | תמונות+וידאו+אתר | חינם, Zernio מושך משם |
| **הפצה** | **Zernio** API | מתזמן IG+TikTok | REST + delete, 16 פלטפורמות |
| **שיווק** | **Admitad** deeplink | לינק + מדידת מכירות | 6.9% AliExpress, subid tracking |
| **מדידה** | דאשבורד + GA4 + Admitad API | funnel/קליקים/מכירות | הכל במקום אחד |

---

## 3. החלטות מפתח — איפה שינינו כיוון ולמה (הלקחים היקרים)

1. **ffmpeg → Space keyframe.** במקום לצרוב את הדיל על הווידאו עם ffmpeg, נתנו ל-Veo שני keyframes (מודעה נקייה → תמונת פוסט עם דיל). המודל מאנפף — הדיל "נכנס" בתנועה חלקה. **פתר:** איכות + מחק תלות ב-ffmpeg.

2. **חסימת auto-download של AliExpress הוסרה.** `taste_engine` חיכה לתמונות ידניות → כל ליד נתקע על `_LINK.txt`. עכשיו source יורד אוטומטית מ-`image_url` (curl fallback). **פתר:** השרשרת האוטומטית זקוקה למקור.

3. **slug ייחודי (space_runner.slugify).** הגרסה הישנה (Shopify-only) קיבצה כל "Stiletto Heels" גנרי ל-slug אחד → 10 מוצרים חלקו תמונה + לינק. הוחלף בכל מקום (`build_site`, `pickup_drop`). **פתר:** התאמה תמונה↔לינק↔מוצר.

4. **caption ייחודי (deal).** Zernio מחזיר 409 על תוכן זהה. השם הגנרי גרם לחסימה. הוספת `· <discount> OFF · $<sale>`. **פתר:** מונע כפילויות.

5. **הצגת תוצרים שלנו בלבד באתר.** לא AliExpress raw ולא שבורות — רק `post_image`/`ad` שלנו או assets מתארחים אצלנו. **פתר:** אמון + המרה.

6. **Admitad subid = מדידת מכירות.** כל לינק נושא `subid=<slug>` → API מחזיר conversions פר-מוצר. scope "statistics" מאושר. **פתר:** "איך נדע אם מישהו קנה".

7. **credits: MCP ≠ unlimited.** לחשבון יש Premium+ unlimited, אבל `unlimitedAppliesHere:false` ב-MCP → הרצות דרך הכלי **צורכות credits**. **מסקנה:** אוטומציה נוחה אך עולה; UI ידני = חינם. trade-off מודע.

8. **restart בוט אחרי שינוי קוד.** הבוט מייבא `taste_engine` פעם אחת — שינוי קוד לא נטען עד restart. **לקח:** deploy = restart.

9. **בדוק `posted` לפני הפצה.** הפצה כפולה של אותו מוצר יצרה duplicate. **לקח:** לבדוק סטטוס לפני שיבוץ.

10. **TikTok "at capacity" → self-heal, לא draft.** ל-direct posting של TikTok יש תקרת קצב משותפת ב-Zernio; ריכוז פוסטים בחלון קצר (4 כל שעתיים) מפיל אותם ל-`failed`/`attempts:0`/`usageRefunded` (לא נוסה בכלל — לא בעיית מדיה). **הפתרון שנשאר אוטומטי:** `tiktok_retry.py` — `--apply` מחייה failed לסלוטים עתידיים, `--spread` מנרמל ל-≤3/יום ב-08/14/20 UTC (מרווח 6h). מחובר ל-`run_producer.bat`. **דחינו `draft:true`** — הוא אמין אבל שובר את האוטומציה (מחייב לחיצה ידנית ב-Creator Inbox). API: עדכון פוסט = `PUT /posts/{id}` (PATCH=405).

---

## 4. שיווק שותפים
- **מרכזי: Admitad deeplink** (`rzekl.com/g/…`, ad space "Stiletto Vault Website" 2984135), AliExpress 6.9%, `subid=<slug>` לייחוס.
- גיבוי: Amazon `thegothicvaul-20` (4%, PA-API נעול עד 3 מכירות), Killstar/DarkInLove (10%).
- **מדידה:** `admitad_stats.py` → `/statistics/actions/` פר subid → דאשבורד.
- ⚠️ מלא pool רק מ-URLs אמיתיים (עופר/API) — לא WebSearch (לינקים מתים).

## 5. מקורות תוכן
- **AliExpress scout** (curl על עמוד חיפוש → `itemList.content` JSON). מוכח 60 מוצרים/בקשה. מגבלה: חסימת IP תחת עומס — עדין (1×/יום).
- **taste_engine** לומד מאישורים/דחיות + תמונות reference (Mia Vision).
- Amazon pool (ASINs) + Shopify (GTHIC/Killstar).

## 6. ערוצים והפצה
- **Instagram + TikTok** דרך **Zernio** (`zernio.com/api/v1`).
- **לוז: יום-כן-יום-לא, שבת לא** (משבצת שבת → ראשון). 3 סלוטים 14/18/22 IL.
- כל דרופ = וידאו 9:16 + תמונה, שניהם לשני הערוצים (`ig_/tt_` mirrored ב-`drop/`).
- **מדיה סופית לא מומרת** (PNG נשאר PNG).

## 7. מדידה — הדאשבורד (`thestilettovault.github.io/dashboard/`)
- **Funnel:** נסרק → אושר → הופק → שובץ → פורסם.
- **מכירות:** Admitad פר-נעל (subid). ✅ מחובר.
- **קליקים:** GA event `affiliate_click` פר-נעל. ✅ חי.
- **תנועה:** GA4 Data API (`ga_stats.py`) — ⏳ ממתין ל-setup.
- רענון: אוטומטי יומי (`run_producer.bat` → `collect_metrics --push`).

## 8. מסקנות ביצועים — עד 2026-09-04
- **17 מוצרים מתוזמנים** ב-Zernio (IG+TikTok), 22 נעליים חיות באתר.
- **מכירות: 0 עד כה** (המדידה חדשה — subid מייחס מכאן והלאה; פוסטים ישנים בלי subid לא נמדדים).
- **הפקה: ~500–700cr/מוצר** דרך MCP (נשרפו 281K/540K credits).
- הצינור האוטומטי הוכח מקצה-לקצה (אישור→מודעות→בחירה→וידאו→הפצה).
- **פערים פתוחים:** תנועה (GA4 setup), עוקבים, וידאו-action (Space prompt עודכן, טרם רץ בצינור), 16 נעליים מאושרות שטרם הופקו.

---

## 9. ההכללה — הכלי הגנרי לכל תחום affiliate

**מה קבוע (הסקלטון):** חמשת השלבים, שני הגייטים, מבנה ה-`production_queue`, זרימת GitHub→Zernio, subid tracking, מבנה הדאשבורד, כלל ה-restart, בדיקת `posted`.

**מה משתנה פר-תחום (הקונפיג):**
| פרמטר | Stiletto | תחום חדש |
|-------|----------|----------|
| נישה + פילטר scout | high-heels | <הגדר> |
| מקורות + pools | AliExpress/Amazon | <הגדר> |
| תוכנית שותפים + עמלה | Admitad 6.9% | <הגדר> |
| Space (סגנון קריאייטיב) | product+deal | <שכפל+התאם prompt> |
| מותג אתר + סגנIt | gothic dark | <הגדר> |
| לוז + סלוטים | יום-כן-יום-לא | <הגדר> |

**איך לשכפל:** קונפיג חדש (נישה/מקורות/שותף/מותג) → שכפול הסקריפטים עם ה-slug/domain החדש → Space חדש בסגנון הרצוי → אותו runner/dashboard/Zernio. **הליבה זהה, רק הקונפיג משתנה.**

---

## 10. Roadmap — שדרוגים למערכת
1. **וידאו-action** — הפוסטים הבאים: סרטון עם תנועה אמיתית (Space prompt כבר עודכן), לא גרפיקה נכנסת.
2. **GA4 traffic** — חיבור `ga_stats` (setup חד-פעמי).
3. **עוקבים** — IG/TikTok API לדאשבורד.
4. **חלק 3 של האוטומציה** — וידאו+הפצה אוטומטיים אחרי בחירה (כרגע ידני, בכוונה — גייט עלות).
5. **תיקון slug בזרימה** — `produce_queue.md` שישתמש ב-slug נקי (בלי prefix תאריך).
6. **חיסכון credits** — לשקול הרצה דרך UI (unlimited) לחלק מהשלבים.
7. **הכלל-config** — קובץ `niche_config.json` שהופך את המערכת לרב-תחומית בלחיצה.

---
_מקורות אמת תפעוליים: `.memory/project/stiletto_distribution_pipeline.md`, `GELEM/_SCHEDULE.md`, `data/approved_catalog.json`, `dashboard/data.json`._
