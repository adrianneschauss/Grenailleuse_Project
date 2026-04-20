from __future__ import annotations

from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = REPO_ROOT / "dist"
BUNDLE_DIR = DIST_DIR / "newest_animation_bundle"

FILES_TO_COPY = {
    REPO_ROOT / "newest_animation.py": "newest_animation.py",
    REPO_ROOT / "demo_variable_conveyor_tempon.py": "demo_variable_conveyor_tempon.py",
    REPO_ROOT / "functions.py": "functions.py",
    REPO_ROOT / "simpy_objects.py": "simpy_objects.py",
    REPO_ROOT / "monitoring.py": "monitoring.py",
    REPO_ROOT / "Parameter_horizontal.py": "Parameter_horizontal.py",
    REPO_ROOT / "Animation_Image.png": "Animation_Image.png",
    REPO_ROOT / "deployment" / "newest_animation" / "README.md": "README.md",
    REPO_ROOT / "deployment" / "newest_animation" / "requirements.txt": "requirements.txt",
    REPO_ROOT / "deployment" / "newest_animation" / "build_requirements.txt": "build_requirements.txt",
    REPO_ROOT / "deployment" / "newest_animation" / "run_newest_animation_windows.ps1": "run_newest_animation_windows.ps1",
    REPO_ROOT / "deployment" / "newest_animation" / "run_newest_animation_windows.bat": "run_newest_animation_windows.bat",
    REPO_ROOT / "deployment" / "newest_animation" / "build_windows_exe.ps1": "build_windows_exe.ps1",
    REPO_ROOT / "deployment" / "newest_animation" / "build_windows_exe.bat": "build_windows_exe.bat",
    REPO_ROOT / "deployment" / "newest_animation" / "newest_animation.spec": "newest_animation.spec",
}


def main() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    missing = [str(src) for src in FILES_TO_COPY if not src.exists()]
    if missing:
        raise FileNotFoundError("Missing required bundle files:\n" + "\n".join(missing))

    for src, relative_dest in FILES_TO_COPY.items():
        dest = BUNDLE_DIR / relative_dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    archive_base = DIST_DIR / "newest_animation_bundle"
    zip_path = shutil.make_archive(str(archive_base), "zip", root_dir=BUNDLE_DIR)

    print(f"Bundle folder: {BUNDLE_DIR}")
    print(f"Bundle zip: {zip_path}")


if __name__ == "__main__":
    main()
