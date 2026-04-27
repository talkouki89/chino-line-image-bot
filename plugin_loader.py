import importlib.util
import traceback
from pathlib import Path
from types import SimpleNamespace


class PluginManager:
    def __init__(self, plugin_dir, enabled=True):
        self.plugin_dir = Path(plugin_dir)
        self.enabled = enabled
        self.modules = {}
        self.mtimes = {}
        self.errors = {}
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def dispatch(self, context):
        if not self.enabled:
            return False
        handled = False
        for path in sorted(self.plugin_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module = self._load_if_changed(path)
            if module is None or not hasattr(module, "handle"):
                continue
            feature_key = getattr(module, "FEATURE_KEY", None)
            is_feature_enabled = getattr(context, "is_feature_enabled", None)
            if feature_key and is_feature_enabled and not is_feature_enabled(feature_key):
                continue
            try:
                if module.handle(context):
                    handled = True
                    break
            except Exception:
                self.errors[path.name] = traceback.format_exc()
                context.log_error(self.errors[path.name])
        return handled

    def _load_if_changed(self, path):
        mtime = path.stat().st_mtime
        cached = self.modules.get(path)
        if cached is not None and self.mtimes.get(path) == mtime:
            return cached

        module_name = f"bot_plugin_{path.stem}_{int(mtime * 1000)}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            self.errors[path.name] = traceback.format_exc()
            return None

        self.modules[path] = module
        self.mtimes[path] = mtime
        self.errors.pop(path.name, None)
        return module


def make_context(**kwargs):
    return SimpleNamespace(**kwargs)
