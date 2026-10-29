# Lanshu OpenAI Media API

**エージェント向けの OpenAI 画像生成・音声文字起こしツール。使用量を記録できます。**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

OpenAI の画像生成、ファイル文字起こし、費用照会 API を呼び出す小さな Python CLI と、単体で配布できるスキルです。成功した呼び出しの出力ファイル、リクエスト ID、使用量を一緒に保存します。英語版 README を主文書としています。

## 機能

- Sunburst と Flare による画像生成。サイズ、品質、枚数、形式を指定できます。
- GPT-Transcribe による音声・動画ファイルの文字起こし。複数言語のヒントと専門用語に対応します。
- 管理者キーを使い、プロジェクト、API キー、モデルで費用記録を絞り込めます。
- API の実行結果を JSON で出力し、エージェントやスクリプトから利用できます。

## 厳選モデル

| 用途 | モデル | 選択 |
| --- | --- | --- |
| 画質を重視した画像生成 | `gpt-image-2.5-sunburst` | 画像の既定値 |
| 速度を重視した画像生成 | `gpt-image-2.5-flare` | 素早い下書き |
| 音声・動画の文字起こし | `gpt-transcribe` | ASR の既定値 |

モデル情報の確認日：2026-10-29。明示的に指定されたモデルを維持し、自動的に別モデルへ切り替えません。

## 動作要件

Python 3.9 以上。実行時の Python 依存は標準ライブラリのみです。curl、ffprobe、zsh は任意です。curl は HTTP 通信、ffprobe は WAV 以外の長さの取得、zsh は既存の ~/.zshrc の読み込みに使用します。

## クイックスタート

プロジェクトディレクトリで実行します。課金が発生する呼び出しの前に、既存のローカル環境へ通常の API キーを設定してください。

### 画像を生成する

```bash
python3 scripts/openai_media.py image \
  --prompt "日差しの入る窓辺に座る茶トラ猫。自然な写真、文字なし" \
  --out output/cat.png
```

既定値は 1024×1024、medium 品質の PNG 1 枚です。素早い下書きには --model gpt-image-2.5-flare --quality low、詳細な画像には --quality high を使えます。--prompt-file、--size、--n、--output-format にも対応します。--dry-run はリクエストを表示するだけです。出力や metadata が既存の場合は、課金リクエストの前に停止します。

### 音声を文字に変換する

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages ja \
  --keyword OpenAI \
  --out output/transcript.txt
```

--languages を繰り返すと複数の想定言語を渡せます。--prompt は録音の背景情報、--keyword は関連する用語のヒントです。empty_transcript: true は空の応答を示します。現在の CLI はファイル用で、マイクのリアルタイム入力、話者分離、単語単位の時刻情報は扱いません。

### 費用を照会する

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

日付と識別子を実際の値に置き換えてください。キー名が重複する場合は --api-key-id を使います。費用照会には管理者キーを使用します。

### コマンドをインストールする

ソーススクリプトはそのまま実行できます。専用コマンドが必要な場合は仮想環境へインストールします。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

## 認証情報

| 変数 | 用途 |
| --- | --- |
| `OPENAI_API_KEY` | 画像生成と文字起こし |
| `OPENAI_ADMIN_KEY` | 費用照会とキー名の解決 |
| `OPENAI_ADMIN_API_KEY` | 管理者キーの互換エイリアス |

明示的な --env-file が対応する環境変数に優先します。指定がなければプロセス環境を読み、必要に応じて ~/.zshrc から export 済みの値を取得します。--no-shell-env でこのフォールバックを無効にできます。認証ファイルはリテラルの代入として解析し、実行しません。シェル起動時の出力を破棄し、キーは専用のメモリパイプで読み込みます。

キーは既存のローカル環境や認証ファイルに保持し、リポジトリ、ログ、配布パッケージに含めません。管理者キーは費用照会に使用します。

## 他のエージェントで使用する

ルートには SKILL.md、エージェント用メタデータ、呼び出しスクリプトがあります。以下のコマンドで独立したスキルフォルダー、ZIP、チェックサム一覧を生成します。生成したフォルダーを各エージェントの skills ディレクトリに配置してください。Codex の一般的な場所は ~/.codex/skills/ です。呼び出し名は $lanshu-openai-media-api。以前のビルドを置換する場合は --force を指定します。

```bash
python3 tools/build_skill.py --output-dir dist
```

## 出力と課金の扱い

画像・文字起こしファイルに加え、同名の .metadata.json を保存します。リクエスト引数、HTTP ステータス、request ID、usage、経過時間、出力先、応答メタデータを保持し、キーや画像の base64 は含めません。

usage は使用量です。Costs API の amount は UTC の日次集計です。プロジェクト、キー、モデルで絞り込んでも個々の request ID の明細にはなりません。UTC 以外の日付は複数の UTC バケットと重なるため、returned_daily_buckets と date_window_exact を確認してください。記録がないことは無料を意味しません。

POST の自動再試行やモデル変更は行いません。GET のネットワークエラーは最大 1 回再試行します。接続が切れた場合は、既存のファイルと metadata を確認してから判断します。

## 開発と検証

プロトコルテストはローカル HTTP サーバーと合成データを使い、実際のキーを必要としません。CI は Python 3.9、3.11、3.13 を対象とします。CLI は Sunburst 画像生成と 30 秒の中国語文字起こしを実 API で確認済みですが、すべての文書言語で認識精度を評価したという意味ではありません。

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

引数、確認日付きの価格情報、公式資料は [API ノート](../../references/api-notes.md) を参照してください。動作を変更した場合は英語版、翻訳文書、スキルを合わせて更新します。

## ライセンス

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.
