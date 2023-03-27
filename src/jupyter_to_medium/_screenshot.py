import platform
import shutil
import subprocess
import base64
import io
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from matplotlib import image as mimage

MAX_CROP = 0.22


def get_system():
    system = platform.system().lower()
    if system in ["darwin", "linux", "windows"]:
        return system
    else:
        raise OSError(f"Unsupported OS - {system}")


def get_chrome_path(chrome_path=None):
    system = get_system()
    if chrome_path:
        return chrome_path

    if system == "darwin":
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
        for path in paths:
            if Path(path).exists():
                return path
        raise OSError("Chrome executable not able to be found on your machine")
    elif system == "linux":
        paths = [
            None,
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
            "/opt/google/chrome",
        ]
        commands = [
            "google-chrome",
            "chrome",
            "chromium",
            "chromium-browser",
            "brave-browser",
        ]
        for path in paths:
            for cmd in commands:
                chrome_path = shutil.which(cmd, path=path)
                if chrome_path:
                    return chrome_path
        raise OSError("Chrome executable not able to be found on your machine")
    elif system == "windows":
        import winreg

        locs = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
        ]
        for loc in locs:
            handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, loc)
            num_values = winreg.QueryInfoKey(handle)[1]
            if num_values > 0:
                return winreg.EnumValue(handle, 0)[1]
        raise OSError("Cannot find chrome.exe on your windows machine")


class Screenshot:
    def __init__(
        self,
        center_df=True,
        max_rows=None,
        max_cols=None,
        chrome_path=None,
        fontsize=18,
        encode_base64=True,
        limit_crop=True,
    ):
        self.center_df = center_df
        self.max_rows = max_rows
        self.max_cols = max_cols
        self.ss_width = 1200
        self.ss_height = 900
        self.chrome_path = get_chrome_path(chrome_path)
        self.css = self.get_css(fontsize)
        self.encode_base64 = encode_base64
        self.limit_crop = limit_crop
        self.enlarge_attempts = 0

    def get_css(self, fontsize):
        mod_dir = Path(__file__).resolve().parent
        css_file = mod_dir / "static" / "style.css"
        with open(css_file) as f:
            css = "<style>" + f.read() + "</style>"
        justify = "center" if self.center_df else "left"
        css = css.format(fontsize=fontsize, justify=justify)
        return css

    def take_screenshot(self):
        temp_dir = TemporaryDirectory()
        temp_html = Path(temp_dir.name) / "temp.html"
        temp_img = Path(temp_dir.name) / "temp.png"
        with open(temp_html, "w") as f:
            f.write(self.html)

        with open(temp_img, "wb") as f:
            args = ["--enable-logging", "--disable-gpu", "--headless"]

            if self.ss_width and self.ss_height:
                args.append(f"--window-size={self.ss_width},{self.ss_height}")

            args += [
                "--hide-scrollbars",
                f"--screenshot={str(temp_img)}",
                str(temp_html),
            ]

            subprocess.run(executable=self.chrome_path, args=args)

        with open(temp_img, "rb") as f:
            img_bytes = f.read()

        buffer = io.BytesIO(img_bytes)
        img = mimage.imread(buffer)
        return self.possibly_enlarge(img)

    def possibly_enlarge(self, img):
        enlarge = False
        img2d = img.mean(axis=2) == 1

        all_white_vert = img2d.all(axis=0)
        # must be all white for 30 pixels in a row to trigger stop
        if all_white_vert[-30:].sum() != 30:
            self.ss_width = int(self.ss_width * 1.2)
            enlarge = True

        all_white_horiz = img2d.all(axis=1)
        if all_white_horiz[-30:].sum() != 30:
            self.ss_height = int(self.ss_height * 1.2)
            enlarge = True

        if self.enlarge_attempts < 15:
            if enlarge:
                self.enlarge_attempts += 1
                return self.take_screenshot()

        return self.crop(img, all_white_vert, all_white_horiz)

    def crop(self, img, all_white_vert, all_white_horiz):
        diff_vert = np.diff(all_white_vert)
        left = diff_vert.argmax()
        right = -diff_vert[::-1].argmax()
        if self.limit_crop:
            max_crop = int(img.shape[1] * MAX_CROP)
            left = min(left, max_crop)
            right = max(right, -max_crop)

        diff_horiz = np.diff(all_white_horiz)
        top = diff_horiz.argmax()
        bottom = -diff_horiz[::-1].argmax()
        new_img = img[top:bottom, left:right]
        return new_img

    def finalize_image(self, img):
        buffer = io.BytesIO()
        mimage.imsave(buffer, img)
        img_str = buffer.getvalue()
        if self.encode_base64:
            img_str = base64.b64encode(img_str).decode()
        return img_str

    def run(self, html):
        self.html = self.css + html
        img = self.take_screenshot()
        img_str = self.finalize_image(img)
        return img_str
