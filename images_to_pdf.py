commit aaec3c40e29e18ba7674d8924f193faa119877ee
Author: Garynio <garybizc@gmail.com>
Date:   Fri Apr 10 11:16:18 2026 +0800

    Initial commit: add images_to_pdf.py with .gitignore

diff --git a/images_to_pdf.py b/images_to_pdf.py
new file mode 100644
index 0000000..d182c3c
--- /dev/null
+++ b/images_to_pdf.py
@@ -0,0 +1,282 @@
+#!/usr/bin/env python3
+"""
+图片文件夹批量转 PDF 工具
+----------------------------------
+选择源文件夹 A：其每个子文件夹内的图片将被合并成一个 PDF
+选择目标文件夹 B：生成的 PDF 文件保存到此处
+"""
+
+import os
+import sys
+import threading
+import tkinter as tk
+from tkinter import filedialog, messagebox, ttk
+from pathlib import Path
+
+# Pillow 用于处理图片 -> PDF
+try:
+    from PIL import Image
+except ImportError:
+    messagebox.showerror("缺少依赖", "请先安装 Pillow：\npip install Pillow")
+    sys.exit(1)
+
+# 支持的图片扩展名
+IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}
+
+
+import re
+
+def _natural_key(path: Path):
+    """自然排序 key：将文件名中的数字段按数值大小排序"""
+    parts = re.split(r'(\d+)', path.name.lower())
+    return [int(p) if p.isdigit() else p for p in parts]
+
+
+def collect_images(folder: Path) -> list[Path]:
+    """收集文件夹内所有图片，按文件名自然排序（数字按大小）"""
+    images = sorted(
+        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS],
+        key=_natural_key
+    )
+    return images
+
+
+def images_to_pdf(images: list[Path], output_path: Path):
+    """将图片列表合并为一个 PDF"""
+    pil_images = []
+    for img_path in images:
+        img = Image.open(img_path).convert("RGB")
+        pil_images.append(img)
+
+    if not pil_images:
+        return False
+
+    first = pil_images[0]
+    rest = pil_images[1:] if len(pil_images) > 1 else []
+    first.save(output_path, save_all=True, append_images=rest)
+    return True
+
+
+class App(tk.Tk):
+    def __init__(self):
+        super().__init__()
+        self.title("图片文件夹 → PDF 批量转换")
+        self.resizable(False, False)
+        self._build_ui()
+
+    def _build_ui(self):
+        PAD = 12
+        BG = "#f5f5f7"
+        ACCENT = "#0071e3"
+        self.configure(bg=BG)
+
+        # ── 标题 ──
+        title_frame = tk.Frame(self, bg=ACCENT, pady=10)
+        title_frame.pack(fill="x")
+        tk.Label(
+            title_frame, text="📂  图片文件夹批量转 PDF",
+            font=("Helvetica", 16, "bold"), fg="white", bg=ACCENT
+        ).pack()
+
+        # ── 主体 ──
+        body = tk.Frame(self, bg=BG, padx=PAD * 2, pady=PAD)
+        body.pack(fill="both", expand=True)
+
+        # 源文件夹
+        self._make_folder_row(body, "源文件夹 A（含子文件夹）：", "src")
+        # 目标文件夹
+        self._make_folder_row(body, "目标文件夹 B（PDF 输出）：", "dst")
+
+        # ── 日志区 ──
+        log_label = tk.Label(body, text="转换日志：", font=("Helvetica", 11), bg=BG, anchor="w")
+        log_label.pack(fill="x", pady=(PAD, 2))
+
+        log_frame = tk.Frame(body, bg=BG)
+        log_frame.pack(fill="both", expand=True)
+
+        self.log_text = tk.Text(
+            log_frame, height=12, width=64,
+            state="disabled", font=("Menlo", 10),
+            bg="#1c1c1e", fg="#30d158",
+            insertbackground="white", relief="flat",
+            padx=8, pady=8
+        )
+        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
+        self.log_text.configure(yscrollcommand=scrollbar.set)
+        self.log_text.pack(side="left", fill="both", expand=True)
+        scrollbar.pack(side="right", fill="y")
+
+        # ── 进度条 ──
+        self.progress = ttk.Progressbar(body, mode="determinate", length=400)
+        self.progress.pack(fill="x", pady=(PAD, 4))
+
+        self.status_var = tk.StringVar(value="准备就绪")
+        tk.Label(body, textvariable=self.status_var, font=("Helvetica", 10),
+                 bg=BG, fg="#666").pack(anchor="w")
+
+        # ── 按钮 ──
+        btn_frame = tk.Frame(body, bg=BG)
+        btn_frame.pack(pady=(PAD, 4))
+
+        self.convert_btn = tk.Button(
+            btn_frame, text="  开始转换  ",
+            font=("Helvetica", 13, "bold"),
+            bg=ACCENT, fg="white",
+            activebackground="#005bb5", activeforeground="white",
+            relief="flat", padx=20, pady=8,
+            cursor="hand2",
+            command=self._start_conversion
+        )
+        self.convert_btn.pack(side="left", padx=6)
+
+        tk.Button(
+            btn_frame, text="清空日志",
+            font=("Helvetica", 11),
+            bg="#e5e5ea", fg="#333",
+            relief="flat", padx=12, pady=8,
+            cursor="hand2",
+            command=self._clear_log
+        ).pack(side="left", padx=6)
+
+        # 底部留白
+        tk.Frame(body, bg=BG, height=8).pack()
+
+    def _make_folder_row(self, parent, label_text, attr):
+        PAD = 12
+        BG = "#f5f5f7"
+        row = tk.Frame(parent, bg=BG)
+        row.pack(fill="x", pady=(PAD, 4))
+
+        tk.Label(row, text=label_text, font=("Helvetica", 11),
+                 bg=BG, anchor="w", width=22).pack(side="left")
+
+        var = tk.StringVar()
+        setattr(self, f"{attr}_var", var)
+
+        entry = tk.Entry(row, textvariable=var, font=("Helvetica", 11),
+                         relief="flat", bg="white",
+                         highlightthickness=1, highlightbackground="#ccc",
+                         width=38)
+        entry.pack(side="left", padx=(4, 6), ipady=4)
+
+        def browse(v=var):
+            path = filedialog.askdirectory()
+            if path:
+                v.set(path)
+
+        tk.Button(
+            row, text="浏览",
+            font=("Helvetica", 10),
+            bg="#e5e5ea", fg="#333",
+            relief="flat", padx=10, pady=4,
+            cursor="hand2",
+            command=browse
+        ).pack(side="left")
+
+    # ── 日志 ──
+    def _log(self, msg: str):
+        self.log_text.configure(state="normal")
+        self.log_text.insert("end", msg + "\n")
+        self.log_text.see("end")
+        self.log_text.configure(state="disabled")
+
+    def _clear_log(self):
+        self.log_text.configure(state="normal")
+        self.log_text.delete("1.0", "end")
+        self.log_text.configure(state="disabled")
+
+    # ── 转换逻辑 ──
+    def _start_conversion(self):
+        src = self.src_var.get().strip()
+        dst = self.dst_var.get().strip()
+
+        if not src:
+            messagebox.showwarning("提示", "请先选择源文件夹 A")
+            return
+        if not dst:
+            messagebox.showwarning("提示", "请先选择目标文件夹 B")
+            return
+
+        src_path = Path(src)
+        dst_path = Path(dst)
+
+        if not src_path.is_dir():
+            messagebox.showerror("错误", f"源文件夹不存在：\n{src}")
+            return
+
+        dst_path.mkdir(parents=True, exist_ok=True)
+
+        # 在子线程中执行，避免卡界面
+        self.convert_btn.configure(state="disabled")
+        thread = threading.Thread(target=self._run_conversion,
+                                  args=(src_path, dst_path), daemon=True)
+        thread.start()
+
+    def _run_conversion(self, src: Path, dst: Path):
+        # 找出所有含图片的子文件夹
+        subdirs = [d for d in sorted(src.iterdir()) if d.is_dir()]
+
+        if not subdirs:
+            self.after(0, lambda: self._log("⚠️  源文件夹内没有子文件夹"))
+            self.after(0, lambda: self.convert_btn.configure(state="normal"))
+            return
+
+        total = len(subdirs)
+        done = 0
+        success = 0
+        skipped = 0
+
+        self.after(0, lambda: self.progress.configure(maximum=total, value=0))
+        self.after(0, lambda: self._log(f"🚀 开始处理，共 {total} 个子文件夹\n"))
+
+        for subdir in subdirs:
+            images = collect_images(subdir)
+            name = subdir.name
+            pdf_path = dst / f"{name}.pdf"
+
+            if not images:
+                self.after(0, lambda n=name: self._log(f"  ⏭️  跳过「{n}」（无图片）"))
+                skipped += 1
+            else:
+                # 打印排序后的文件列表，方便调试
+                names_log = "  📋  排序结果："
+                self.after(0, lambda n=name, c=len(images):
+                           self._log(f"  🖼️  「{n}」→ {c} 张图片"))
+                for i, img_path in enumerate(images):
+                    self.after(0, lambda idx=i, fname=img_path.name:
+                               self._log(f"     [{idx+1}] {fname}"))
+                self.after(0, lambda n=name: self.status_var.set(f"正在处理：{n}"))
+                try:
+                    ok = images_to_pdf(images, pdf_path)
+                    if ok:
+                        self.after(0, lambda n=name, p=str(pdf_path):
+                                   self._log(f"  ✅  已生成 {n}.pdf"))
+                        success += 1
+                    else:
+                        self.after(0, lambda n=name: self._log(f"  ❌  「{n}」转换失败（无有效图片）"))
+                        skipped += 1
+                except Exception as e:
+                    err = str(e)
+                    self.after(0, lambda n=name, e=err:
+                               self._log(f"  ❌  「{n}」出错：{e}"))
+                    skipped += 1
+
+            done += 1
+            d = done
+            self.after(0, lambda v=d: self.progress.configure(value=v))
+
+        summary = f"\n🎉 完成！成功 {success} 个，跳过 {skipped} 个，共 {total} 个子文件夹"
+        self.after(0, lambda: self._log(summary))
+        self.after(0, lambda: self.status_var.set(f"完成：{success} 个 PDF 已生成"))
+        self.after(0, lambda: self.convert_btn.configure(state="normal"))
+        self.after(0, lambda: messagebox.showinfo(
+            "转换完成",
+            f"成功生成 {success} 个 PDF 文件\n"
+            f"跳过 {skipped} 个（无图片或出错）\n\n"
+            f"输出目录：\n{dst}"
+        ))
+
+
+if __name__ == "__main__":
+    app = App()
+    app.mainloop()
