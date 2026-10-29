# Lanshu OpenAI Media API

**Ajanlar için OpenAI ile metin ve görsel üretimi ve ses dökümü; kullanım kayıtlarıyla birlikte.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)
[![岚叔 X](https://img.shields.io/badge/%E5%B2%9A%E5%8F%94-X-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/LufzzLiz)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

OpenAI metin ve görsel üretimi, dosya dökümü ve maliyet API’lerini çağıran küçük bir Python CLI ve bağımsız dağıtılabilen bir beceridir. Başarılı çağrılarda çıktı dosyaları, istek kimliği ve kullanım verileri birlikte saklanır. İngilizce README ana belgedir.

## Özellikler

- Responses API ile metin üretin; dört seçilmiş model, akıl yürütme düzeyi ve çıktı token sınırı kullanın.
- Sunburst veya Flare ile boyut, kalite, adet ve biçim seçerek görsel üretin.
- GPT-Transcribe ile ses ve video dosyalarını yazıya dökün; birden fazla dil ipucu ve alan terimi sağlayın.
- Yönetici anahtarıyla proje, API anahtarı ve modele göre maliyet kayıtlarını okuyun.
- API yürütme sonuçlarını ajanların ve betiklerin kullanabileceği JSON biçiminde alın.

## Seçilmiş modeller

| Görev | Model | Seçim |
| --- | --- | --- |
| Günlük metin ve kodlama | `gpt-6.1-sol` | Varsayılan metin modeli, dengeli |
| Zorlu akıl yürütme ve uzmanlık işleri | `gpt-6-astra` | En yüksek zekâ |
| Yazma ve düzenleme | `gpt-6.1-terra` | Hızlı ve verimli |
| Odaklı, yüksek hacimli işler | `gpt-6-luna` | Hız ve maliyet öncelikli |
| Görsel kalitesi öncelikli | `gpt-image-2.5-sunburst` | Varsayılan görsel modeli |
| Üretim hızı öncelikli | `gpt-image-2.5-flare` | Hızlı taslaklar |
| Ses ve video dosyalarını yazıya dökme | `gpt-transcribe` | Varsayılan ASR modeli |

Model belgelerinin kontrol tarihi: 2026-10-29. Açıkça belirtilen model korunur ve otomatik olarak başka bir modele geçilmez.

## Gereksinimler

Python 3.9 veya üzeri gerekir; çalışma zamanında yalnızca standart kütüphane kullanılır. curl, ffprobe ve zsh isteğe bağlıdır. curl HTTP aktarımında, ffprobe diğer ses biçimlerinin süresini okumada, zsh ise mevcut ~/.zshrc dışa aktarımlarını yüklemede kullanılır.

## Hızlı başlangıç

Komutları proje dizininden çalıştırın. Ücretli bir çağrıdan önce normal API anahtarını mevcut yerel ortamınızda yapılandırın.

### Metin üretme

```bash
python3 scripts/openai_media.py text \
  --model gpt-6.1-sol \
  --prompt "API otomasyonunun faydalarını üç kısa cümleyle açıkla." \
  --reasoning-effort low \
  --out output/answer.txt
```

Varsayılanlar: `gpt-6.1-sol`, `medium` akıl yürütme ve 4096 çıktı token sınırı. Zorlu işler için `gpt-6-astra`, verimli yazım için `gpt-6.1-terra`, hızlı odaklı işler için `gpt-6-luna` seçin. `python3 scripts/openai_media.py models --task text` yalnızca metin modellerini listeler. [Resmî model rehberi](https://developers.openai.com/api/docs/guides/latest-model).

`--prompt-file` UTF-8 girdisini okur; `--instructions` genel talimatları belirler; `--max-output-tokens` akıl yürütme tokenlarını da içeren çıktı sınırıdır. Astra ve Sol `low` veya üstünü, Terra ve Luna ayrıca `none` düzeyini destekler. İstekler `store: false` kullanır. `--dry-run` anahtar okumaz, API çağırmaz ve dosya oluşturmaz.

`.txt` ve yanındaki `.metadata.json`, metni, yanıt kimliğini, dönen modeli, durumu, request ID ve kullanım verilerini saklar. Eksik, reddedilen veya boş yanıtlar dosyaları ve kullanımı korur; `ok: false` ve çıkış kodu 1 döndürür. Yeni çağrıdan önce `response_status`, `incomplete_details` ve `refusals` alanlarını inceleyin; POST otomatik yinelenmez.

### Görsel üretme

```bash
python3 scripts/openai_media.py image \
  --prompt "Güneşli bir pencere önünde turuncu bir kedi, doğal fotoğraf, yazı yok" \
  --out output/cat.png
```

Varsayılan çıktı 1024×1024 boyutunda, medium kalitede tek bir PNG’dir. Hızlı taslak için --model gpt-image-2.5-flare --quality low, ayrıntılı görsel için --quality high kullanın. --prompt-file, --size, --n ve --output-format da desteklenir. --dry-run yalnızca planlanan isteği gösterir. Aynı adlı çıktı veya metadata varsa ücretli istek gönderilmeden durulur.

### Sesi yazıya dökme

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages tr \
  --keyword OpenAI \
  --out output/transcript.txt
```

Birden fazla beklenen dil için --languages seçeneğini tekrarlayın. --prompt kayıt bağlamını, --keyword ise ilgili terimleri sağlar. empty_transcript: true boş metin döndüğünü gösterir. CLI dosyaları işler; canlı mikrofon akışı, konuşmacı ayrımı veya kelime düzeyinde zaman damgası sunmaz.

### Maliyet sorgulama

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

Tarih ve kimlikleri gerçek değerlerle değiştirin. Anahtar adı benzersiz değilse --api-key-id kullanın. Bu komut yönetici anahtarıyla çalışır.

### Komutu yükleme

Kaynak betik kurulum gerektirmeden çalışır. Ayrı bir komut için projeyi sanal ortama yükleyin.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

## Kimlik bilgileri

| Değişken | Kullanım |
| --- | --- |
| `OPENAI_API_KEY` | Metin ve görsel üretimi ve ses dökümü |
| `OPENAI_ADMIN_KEY` | Maliyet sorgusu ve anahtar adı çözümleme |
| `OPENAI_ADMIN_API_KEY` | Yönetici anahtarının uyumlu alternatif adı |

Açıkça verilen --env-file, ilgili ortam değişkeninin önüne geçer. Aksi halde önce işlem ortamı, gerekirse ~/.zshrc içindeki dışa aktarılmış değişkenler okunur. --no-shell-env bu geri dönüşü kapatır. Kimlik dosyası sabit değer atamaları olarak ayrıştırılır; içeriği çalıştırılmaz. Kabuk başlangıç çıktısı atılır ve anahtar özel bir bellek kanalıyla okunur.

Anahtarlar mevcut yerel ortamınızda veya kimlik dosyanızda kalır; depoya, günlüklere ve dağıtım paketine eklenmez. Yönetici anahtarı maliyet sorgularında kullanılır.

## Diğer ajanlarda kullanım

Proje kökünde SKILL.md, ajan metaverileri ve çağrı betikleri bulunur. Aşağıdaki komut bağımsız beceri klasörü, ZIP ve sağlama toplamı listesi üretir. Klasörü ajanınızın skills dizinine yerleştirin; Codex genellikle ~/.codex/skills/ kullanır. Çağrı adı $lanshu-openai-media-api’dir. Önceki derlemeyi değiştirmek için --force kullanın.

```bash
python3 tools/build_skill.py --output-dir dist
```

## Çıktılar ve faturalandırma sınırları

İstenen çıktı dosyasıyla birlikte aynı adlı .metadata.json yazılır. Kayıt; istek parametrelerini, HTTP durumunu, request ID, usage, geçen süreyi, çıktı yollarını ve yanıt metaverilerini içerir. Anahtarlar ve görsel base64 verileri hariç tutulur.

usage tüketimi gösterir. Costs API içindeki amount, UTC günlerine göre toplanmış maliyettir. Proje, anahtar ve model filtresi bunu tek bir request ID’nin makbuzuna dönüştürmez. Yerel tarih birden fazla UTC aralığıyla örtüşebilir; returned_daily_buckets ve date_window_exact alanlarını inceleyin. Kayıt bulunmaması isteğin ücretsiz olduğunu kanıtlamaz.

POST istekleri otomatik yinelenmez ve model değiştirilmez. GET ağ hatası en fazla bir kez yeniden denenir. Bağlantı kesilirse sonraki adımdan önce mevcut dosyaları ve metadata kayıtlarını kontrol edin.

## Geliştirme ve kontroller

Protokol testleri yerel HTTP sunucusu ve sentetik veriler kullanır; gerçek anahtar gerekmez. CI yapılandırması Python 3.9, 3.11 ve 3.13’ü hedefler. CLI ayrıca Sunburst görsel üretimi ve 30 saniyelik Çince ses dökümüyle gerçek API üzerinde kontrol edilmiştir; bu, tüm belge dillerinde doğruluk ölçümü yapıldığı anlamına gelmez.

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

Parametreler, tarihli fiyat bilgileri ve resmî kaynaklar için [API notlarına](../../references/api-notes.md) bakın. Davranış değişikliklerinde İngilizce belgeyi, çevirileri ve beceriyi birlikte güncelleyin.

## Lisans

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.
