import hashlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


REPO_URL = "https://github.com/talkouki89/chino-line-image-bot.git"
ZIP_URL = "https://github.com/talkouki89/chino-line-image-bot/archive/refs/heads/master.zip"
PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
GIT_LATEST_RELEASE_API = "https://api.github.com/repos/git-for-windows/git/releases/latest"
PROJECT_DIR_NAME = "chino-line-image-bot"

ROOT = None
VENV = None
PYTHON = None
REQ_HASH = None
BOT_PROCESS = None


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
        *common_python_paths(),
    ]
    for candidate in candidates:
        if command_works(candidate):
            return candidate
    installer = install_python()
    candidates = [["py", "-3"], ["python"], *common_python_paths()]
    for candidate in candidates:
        if command_works(candidate):
            return candidate
    raise FileNotFoundError(
        "找不到 Python。已下載並啟動安裝程式，請確認安裝完成且勾選 Add python.exe to PATH，"
        f"再重新執行 Launcher。安裝檔：{installer}"
    )


def command_works(command):
    try:
        subprocess.check_call(
            [*command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def common_python_paths():
    roots = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python",
        Path(os.environ.get("ProgramFiles", "")),
    ]
    paths = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("Python3*/python.exe")):
            paths.append([str(path)])
    return paths


def install_python():
    installer = launcher_dir() / "python-3.11.9-amd64.exe"
    if not installer.exists():
        print("找不到 Python，開始下載 Python 3.11 安裝程式。")
        download_url(PYTHON_INSTALLER_URL, installer)
    print("即將開啟 Python 安裝程式。請勾選 Add python.exe to PATH，安裝完成後回到此視窗。")
    subprocess.run([str(installer)])
    wait_for_enter("Python 安裝完成後按 Enter 繼續...")
    delete_installer(installer)
    return installer


def find_git(install=False):
    candidates = [["git"], *common_git_paths()]
    for candidate in candidates:
        if command_works(candidate):
            return candidate[0]
    if install:
        installer = install_git()
        refresh_process_path()
        candidates = [["git"], *common_git_paths()]
        for candidate in candidates:
            if command_works(candidate):
                return candidate[0]
        raise FileNotFoundError(
            "找不到 Git。已下載並啟動安裝程式，請確認安裝完成，"
            f"再重新執行 Launcher。安裝檔：{installer}"
        )
    return None


def common_git_paths():
    roots = [
        Path(os.environ.get("ProgramFiles", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Git" / "cmd" / "git.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Git" / "cmd" / "git.exe",
    ]
    return [[str(path)] for path in roots if path.exists()]


def install_git():
    installer = launcher_dir() / "Git-for-Windows-64-bit.exe"
    if not installer.exists():
        print("找不到 Git，開始下載 Git for Windows 安裝程式。")
        download_url(resolve_git_installer_url(), installer)
    print("即將開啟 Git 安裝程式。建議使用預設選項，安裝完成後回到此視窗。")
    subprocess.run([str(installer)])
    wait_for_enter("Git 安裝完成後按 Enter 繼續...")
    delete_installer(installer)
    return installer


def resolve_git_installer_url():
    try:
        with urllib.request.urlopen(GIT_LATEST_RELEASE_API, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for asset in payload.get("assets", []):
            name = asset.get("name", "")
            url = asset.get("browser_download_url", "")
            if name.endswith("64-bit.exe") and "Portable" not in name and url:
                return url
    except Exception as exc:
        print(f"取得最新版 Git 下載網址失敗，改用備援版本：{exc}")
    return "https://github.com/git-for-windows/git/releases/download/v2.54.0.windows.1/Git-2.54.0-64-bit.exe"


def refresh_process_path():
    additions = []
    for command in common_git_paths():
        additions.append(str(Path(command[0]).parent))
    for command in common_python_paths():
        additions.append(str(Path(command[0]).parent))
    current = os.environ.get("PATH", "")
    for path in additions:
        if path and path not in current:
            current = f"{path};{current}"
    os.environ["PATH"] = current


def delete_installer(path):
    try:
        Path(path).unlink(missing_ok=True)
        print(f"已刪除安裝檔：{path}")
    except Exception as exc:
        print(f"安裝檔刪除失敗，可手動刪除：{path} ({exc})")


def wait_for_enter(message):
    if sys.stdin and sys.stdin.isatty():
        input(message)
    else:
        print(message.replace("按 Enter", "繼續"))


def download_project(base_dir):
    target = base_dir / PROJECT_DIR_NAME
    if target.exists() and is_project_root(target):
        return target
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"{target} 已存在但不是 ChinoBot 專案，請移走或改用空資料夾。")

    print(f"找不到專案，開始下載到：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    git = find_git()
    if git:
        run([git, "clone", REPO_URL, str(target)], cwd=base_dir)
        return target

    zip_path = base_dir / f"{PROJECT_DIR_NAME}.zip"
    print("找不到 Git，改用 GitHub zip 下載。")
    download_url(ZIP_URL, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(base_dir)
    extracted = base_dir / f"{PROJECT_DIR_NAME}-master"
    if extracted.exists():
        extracted.rename(target)
    zip_path.unlink(missing_ok=True)
    if not is_project_root(target):
        raise FileNotFoundError("專案下載失敗，找不到 main.py 或 requirements.txt。")
    return target


def download_url(url, path):
    try:
        urllib.request.urlretrieve(url, path)
        return
    except ssl.SSLCertVerificationError:
        pass
    except urllib.error.URLError as exc:
        if not isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError):
            raise
    print("SSL 憑證驗證失敗，改用不驗證憑證的備援下載。")
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(url, context=context) as response, open(path, "wb") as target:
        shutil.copyfileobj(response, target)


def ensure_env_files():
    if not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copyfile(ROOT / ".env.example", ROOT / ".env")
        print("已建立 .env，請記得填入 LINE 登入與管理員設定。")
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


def requirements_need_git():
    requirements = ROOT / "requirements.txt"
    if not requirements.exists():
        return False
    text = requirements.read_text(encoding="utf-8", errors="ignore").lower()
    return "git+" in text or "@ git" in text


def save_requirements_hash():
    requirements = ROOT / "requirements.txt"
    REQ_HASH.write_text(file_sha256(requirements), encoding="utf-8")


def ensure_venv():
    if not PYTHON.exists():
        run([*find_system_python(), "-m", "venv", str(VENV)])
    if not requirements_changed():
        print("依賴沒有變更，跳過 pip 安裝。")
        return
    print("偵測到 requirements.txt 變更或尚未安裝依賴，開始安裝。")
    if requirements_need_git():
        git = find_git(install=True)
        print(f"Git 可用：{git}")
    run([str(PYTHON), "-m", "pip", "install", "-U", "pip"])
    run([str(PYTHON), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
    save_requirements_hash()


def prepare_environment():
    setup_paths()
    print(f"專案路徑：{ROOT}")
    ensure_env_files()
    ensure_venv()


def launch_bot(wait=True):
    global BOT_PROCESS
    prepare_environment()
    args = [str(PYTHON), str(ROOT / "main.py")]
    if wait:
        run(args)
        return None
    print(f"> {' '.join(args)}")
    BOT_PROCESS = subprocess.Popen(args, cwd=ROOT)
    return BOT_PROCESS


def main():
    setup_paths()
    print(f"專案路徑：{ROOT}")
    if "--check" in sys.argv:
        print(f"虛擬環境 Python：{PYTHON}")
        print(f"系統 Python：{' '.join(find_system_python())}")
        if requirements_need_git():
            print(f"Git：{find_git(install=False) or '尚未安裝'}")
        print("Launcher 檢查完成。")
        return
    launch_bot(wait=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("")
        print(f"啟動失敗：{exc}")
        input("按 Enter 關閉...")
        raise
