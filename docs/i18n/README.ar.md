<div dir="rtl">

# Lanshu OpenAI Media API

**توليد الصور وتحويل الصوت إلى نص للوكلاء، مع الاحتفاظ بسجلات الاستخدام.**

<div dir="ltr">

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)

</div>

<div dir="ltr">

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

</div>

واجهة أوامر صغيرة بلغة Python ومهارة قابلة للتوزيع لاستدعاء واجهات OpenAI الخاصة بتوليد الصور وتفريغ الملفات الصوتية والاستعلام عن التكاليف. تحتفظ كل عملية ناجحة بملفات الإخراج ومعرّف الطلب وبيانات الاستخدام. ملف README الإنجليزي هو المرجع الأساسي.

## الميزات

- توليد الصور باستخدام Sunburst أو Flare مع تحديد الأبعاد والجودة والعدد والصيغة.
- تحويل ملفات الصوت والفيديو إلى نص باستخدام GPT-Transcribe، مع تلميحات لغوية وكلمات متخصصة.
- قراءة سجلات التكاليف حسب المشروع ومفتاح API والنموذج باستخدام مفتاح إداري.
- إخراج نتائج تنفيذ API بصيغة JSON لتسهيل استخدامها بواسطة الوكلاء والبرامج.

## النماذج المختارة

<div dir="ltr">

| المهمة | النموذج | الاستخدام |
| --- | --- | --- |
| التركيز على جودة الصورة | `gpt-image-2.5-sunburst` | النموذج الافتراضي للصور |
| التركيز على سرعة التوليد | `gpt-image-2.5-flare` | مسودات سريعة |
| تحويل ملفات الصوت والفيديو إلى نص | `gpt-transcribe` | النموذج الافتراضي للتفريغ |

</div>

تاريخ مراجعة وثائق النماذج: 2026-10-29. يُستخدم النموذج المحدد صراحة دون استبداله تلقائيًا.

## المتطلبات

يلزم Python 3.9 أو أحدث. يعتمد التشغيل على المكتبة القياسية فقط. الأدوات curl وffprobe وzsh اختيارية: تُستخدم curl لاتصال HTTP، وffprobe لقراءة مدة صيغ صوتية إضافية، وzsh لتحميل المتغيرات المصدّرة مسبقًا من ~/.zshrc.

## البدء السريع

شغّل الأوامر من مجلد المشروع. اضبط مفتاح API العادي في بيئتك المحلية الحالية قبل إرسال طلب مدفوع.

### توليد صورة

<div dir="ltr">

```bash
python3 scripts/openai_media.py image \
  --prompt "قط برتقالي على حافة نافذة مشمسة، تصوير طبيعي، بلا نصوص" \
  --out output/cat.png
```

</div>

الإعدادات الافتراضية: صورة PNG واحدة بأبعاد 1024×1024 وجودة medium. للمسودات السريعة أضف --model gpt-image-2.5-flare --quality low، وللتفاصيل الدقيقة استخدم --quality high. تتوفر أيضًا --prompt-file و--size و--n و--output-format. يعرض --dry-run الطلب فقط. وجود ملف إخراج أو metadata بالاسم نفسه يوقف العملية قبل إرسال طلب مدفوع.

### تحويل الصوت إلى نص

<div dir="ltr">

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages ar \
  --keyword OpenAI \
  --out output/transcript.txt
```

</div>

يمكن تكرار --languages لتحديد أكثر من لغة متوقعة. يوفّر --prompt سياق التسجيل، ويضيف --keyword مصطلحات مرتبطة بالمحتوى. تشير empty_transcript: true إلى استجابة نصية فارغة. تعالج هذه الواجهة الملفات ولا تنفذ بث الميكروفون المباشر أو فصل المتحدثين أو التوقيت على مستوى الكلمات.

### الاستعلام عن التكاليف

<div dir="ltr">

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

</div>

استبدل التاريخ والمعرّفات بالقيم الفعلية. استخدم --api-key-id إذا كان اسم المفتاح غير فريد. يتطلب هذا الأمر مفتاحًا إداريًا.

### تثبيت أمر التشغيل

يمكن تشغيل السكربت مباشرة من المصدر. للحصول على أمر مستقل، ثبّت المشروع داخل بيئة افتراضية.

<div dir="ltr">

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

</div>

## بيانات الاعتماد

<div dir="ltr">

| المتغير | الاستخدام |
| --- | --- |
| `OPENAI_API_KEY` | توليد الصور وتحويل الصوت إلى نص |
| `OPENAI_ADMIN_KEY` | التكاليف وتحديد معرّف المفتاح من اسمه |
| `OPENAI_ADMIN_API_KEY` | اسم بديل متوافق للمفتاح الإداري |

</div>

يتقدم --env-file المحدد صراحة على متغير البيئة المقابل. بخلاف ذلك تُقرأ بيئة العملية، ثم المتغيرات المصدّرة في ~/.zshrc عند الحاجة. يعطّل --no-shell-env هذا المسار البديل. يُحلّل ملف الاعتماد كقيم نصية ثابتة دون تنفيذ محتواه. يُهمَل إخراج بدء الصدفة ويُنقل المفتاح عبر قناة ذاكرة خاصة.

تبقى المفاتيح في بيئتك المحلية أو ملف الاعتماد الموجود، ولا تُضمّن في المستودع أو السجلات أو حزم التوزيع. يُستخدم المفتاح الإداري للاستعلام عن التكاليف.

## الاستخدام بواسطة وكلاء آخرين

يحتوي جذر المشروع على SKILL.md وبيانات الوكيل وسكربتات الاستدعاء. ينشئ الأمر التالي مجلد مهارة مستقلًا وملف ZIP وقائمة بصمات تحقق. ضع المجلد الناتج في دليل المهارات الخاص بالوكيل؛ يستخدم Codex عادة ~/.codex/skills/. اسم الاستدعاء هو $lanshu-openai-media-api. استخدم --force لاستبدال بناء سابق.

<div dir="ltr">

```bash
python3 tools/build_skill.py --output-dir dist
```

</div>

## المخرجات وحدود بيانات الفوترة

تُحفظ الملفات الناتجة مع ملف .metadata.json مرافق. يشمل السجل معاملات الطلب وحالة HTTP ومعرّف request ID وبيانات usage والوقت المنقضي ومسارات الإخراج وبيانات الاستجابة، دون المفاتيح أو بيانات الصور بصيغة base64.

تعبّر usage عن الاستهلاك. تمثل amount في واجهة Costs مجاميع يومية بتوقيت UTC. لا يحول الترشيح حسب المشروع والمفتاح والنموذج هذه البيانات إلى إيصال لطلب منفرد. قد يتداخل التاريخ المحلي مع أكثر من فترة UTC؛ افحص returned_daily_buckets وdate_window_exact. عدم وجود سجلات لا يثبت أن الطلب مجاني.

لا تُعاد طلبات POST تلقائيًا ولا يُستبدل النموذج. تُعاد محاولة GET مرة واحدة كحد أقصى عند خطأ شبكي. بعد انقطاع الاتصال، افحص الملفات وmetadata قبل اتخاذ الخطوة التالية.

## التطوير والتحقق

تستخدم اختبارات البروتوكول خادم HTTP محليًا وبيانات اصطناعية ولا تحتاج إلى مفتاح فعلي. يستهدف إعداد CI إصدارات Python 3.9 و3.11 و3.13. جرى كذلك اختبار توليد صورة Sunburst وتفريغ 30 ثانية من الكلام الصيني عبر API؛ لا يعني ذلك قياس دقة التعرف في جميع لغات الوثائق.

<div dir="ltr">

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

</div>

راجع [ملاحظات API](../../references/api-notes.md) للاطلاع على المعاملات والأسعار المؤرخة والمصادر الرسمية. حدّث الدليل الإنجليزي والترجمات والمهارة معًا عند تغيير السلوك.

## الترخيص

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.

</div>
