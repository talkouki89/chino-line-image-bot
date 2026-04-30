import hashlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


REPO_URL = "https://github.com/talkouki89/chino-line-image-bot.git"
ZIP_URL = "https://github.com/talkouki89/chino-line-image-bot/archive/refs/heads/master.zip"
PROJECT_DIR_NAME = "chino-line-image-bot"

ROOT = None
VENV = None
PYTHON = None
REQ_HASH = None


def is_project_root(path):
    return (path / "main.py").exists() and (path / "requirements.txt").exists()


def launcher_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def find_project_root():
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([exe_dir, exe_dir.parent, exe_dir / PROJECT_DIR_NAME, Path.cwd()])
    script_dir = Path(__file__).resolve().parent
    candidates.extend([script_dir, script_dir.parent, Path.cwd(), Path.cwd() / PROJECT_DIR_NAME])

    for candidate in candidates:
        if is_project_root(candidate):
            return candidate
    return download_project(launcher_dir())


def setup_paths():
    global ROOT, VENV, PYTHON, REQ_HASH
    ROOT = find_project_root()
    VENV = ROOT / ".venv"
    PYTHON = VENV / "Scripts" / "python.exe"
    REQ_HASH = VENV / ".requirements.sha256"


def run(args, cwd=None):
    print(f"> {' '.join(str(arg) for arg in args)}")
    subprocess.check_call(args, cwd=cwd or ROOT)


def find_system_python():
    candidates = [
        ["py", "-3"],
        ["python"],
        ["python3"],
    ]
    for candidate in candidates:
        try:
            subprocess.check_call(
                [*candidate, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return candidate
        except (OSError, subprocess.CalledProcessError):
            continue
    raise FileNotFoundError("找不到 Python。請先安裝 Python 3，並勾選 Add python.exe to PATH。")


def find_git():
    try:
        subprocess.check_call(
            ["git", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "git"
    except (OSError, subprocess.CalledProcessError):
        return None


def download_project(base_dir):
    target = base_dir / PROJECT_DIR_NAME
    if target.exists() and is_project_root(target):
        return target
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"{target} 已存在但不是 ChinoBot 專案，請移開後再重新執行。")

    print(f"找不到專案根目錄，將自動下載到：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    git = find_git()
    if git:
        run([git, "clone", REPO_URL, str(target)], cwd=base_dir)
        return target

    zip_path = base_dir / f"{PROJECT_DIR_NAME}.zip"
    print("找不到 Git，改用 GitHub zip 下載。")
    urllib.request.urlretrieve(ZIP_URL, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(base_dir)
    extracted = base_dir / f"{PROJECT_DIR_NAME}-master"
    if extracted.exists():
        extracted.rename(target)
    zip_path.unlink(missing_ok=True)
    if not is_project_root(target):
        raise FileNotFoundError("專案下載完成，但找不到 main.py 或 requirements.txt。")
    return target


def ensure_env_files():
    if not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
        print("已建立 .env，請先打開填入 LINE 登入與管理員設定。")
    for name in ("ban", "temp", "features"):
        target = ROOT / "json" / f"{name}.json"
        example = ROOT / "json" / f"{name}.example.json"
        if not target.exists() and example.exists():
            shutil.copyfile(example, target)


def file_sha256(path):
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def requirements_changed():
    requirements = ROOT / "requirements.txt"
    if not PYTHON.exists() or not REQ_HASH.exists():
        return True
    current_hash = file_sha256(requirements)
    return REQ_HASH.read_text(encoding="utf-8").strip() != current_hash


def save_requirements_hash():
    requirements = ROOT / "requirements.txt"
    REQ_HASH.write_text(file_sha256(requirements), encoding="utf-8")


def ensure_venv():
    if not PYTHON.exists():
        run([*find_system_python(), "-m", "venv", str(VENV)])
    if not requirements_changed():
        print("依賴已是最新，跳過安裝檢查。")
        return
    print("第一次啟動或 requirements.txt 有更新，開始安裝依賴。")
    run([str(PYTHON), "-m", "pip", "install", "-U", "pip"])
    run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
    save_requirements_hash()


def main():
    setup_paths()
    print(f"專案位置：{ROOT}")
    if "--check" in sys.argv:
        print(f"虛擬環境 Python：{PYTHON}")
        print(f"系統 Python：{' '.join(find_system_python())}")
        print("Launcher 檢查完成。")
        return
    ensure_env_files()
    ensure_venv()
    run([str(PYTHON), str(ROOT / "main.py")])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("")
        print(f"啟動失敗：{exc}")
        input("按 Enter 關閉視窗...")
        raise
