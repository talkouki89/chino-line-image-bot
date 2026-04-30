#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "已建立 .env，請先填入 LINE 登入與管理員設定。"
fi

for name in ban temp features; do
  if [ ! -f "json/${name}.json" ] && [ -f "json/${name}.example.json" ]; then
    cp "json/${name}.example.json" "json/${name}.json"
  fi
done

echo "安裝完成。啟動方式：source .venv/bin/activate && python main.py"
