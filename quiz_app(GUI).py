
#　ver.1.4

import csv
import json
import os
import random
import tkinter as tk
from tkinter import ttk, messagebox

# ===== ファイルパス設定 =====
CSV_FILES = {"section1": "section1.csv",      
             "section2":"section2.csv"}

JSON_FILES = {"mistakes": "mistakes.json"}

# ===== ファイル読み込み・保存関数 =====
def load_words_from_csv(filename, section_name):
    if not os.path.exists(filename):
        return []
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [{"word": row["word"], "meaning": row["meaning"], "section": section_name} for row in reader]

def load_words_from_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_words_to_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== データ初期化：アプリ起動時に一度だけ読み込む =====
CSV_DATA = {section: load_words_from_csv(path, section) for section, path in CSV_FILES.items()}
MISTAKES_DATA = load_words_from_json(JSON_FILES["mistakes"])

# ===== GUI クラス定義 =====
class FlashcardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("英単語クイズ")
        self.geometry("320x480")
        self.configure(bg="#FAFAFA")

        # 状態変数
        self.mistakes = MISTAKES_DATA.copy()
        self.current_words = []
        self.current_index = 0
        self.score = 0
        self.total = 0
        self.session_mistakes = []
        self.current_section = ""

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (MainMenu, QuizPage, MistakeReviewPage, MistakeListPage):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainMenu")

    def show_frame(self, name):
        self.frames[name].tkraise()

    def start_quiz(self, section=None, num_questions=None, review_mode=False):
        self.session_mistakes = []
        self.current_section = section

        if review_mode:
            review_words = [w for w in self.mistakes if w["section"] == section]
            if not review_words:
             messagebox.showinfo("情報", f"{section} で間違えた単語がありません")
             return
            self.current_words = random.sample(review_words, min(num_questions, len(review_words)))
            self.total = len(self.current_words)
            self.current_index = 0
            self.score = 0
            self.frames["MistakeReviewPage"].start_review()
            self.show_frame("MistakeReviewPage")
        else:
            words = CSV_DATA.get(section, [])
            if not words:
                messagebox.showinfo("エラー", f"{section} に単語が見つかりません")
                return
            self.current_words = random.sample(words, min(num_questions, len(words)))
            self.total = len(self.current_words)
            self.current_index = 0
            self.score = 0
            self.frames["QuizPage"].load_question()
            self.show_frame("QuizPage")


    def add_mistake(self, word):
        if word not in self.session_mistakes:
            self.session_mistakes.append(word)

    def finalize_mistakes(self, selected_words):
        for word in selected_words:
            if not any(w["word"] == word["word"] and w["section"] == word["section"] for w in self.mistakes):
                self.mistakes.append(word)
        save_words_to_json(JSON_FILES["mistakes"], self.mistakes)
        self.frames["MistakeListPage"].load_mistakes()

    def remove_mistake(self, word):
        self.mistakes = [w for w in self.mistakes if not (w["word"] == word["word"] and w["section"] == word["section"])]
        save_words_to_json(JSON_FILES["mistakes"], self.mistakes)

class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="White.TFrame")
        self.controller = controller

        # スタイル設定
        style = ttk.Style()
        style.theme_use("clam")  # カスタムしやすいテーマ

        # ボタン共通スタイル（背景を明るく）
        style.configure("TButton", font=("Meiryo", 14), padding=10, background="#f0f0f0", foreground="black")
        style.map("TButton",
                  background=[("active", "#d0e0ff")],
                  relief=[("pressed", "sunken")])

        # フレームとラベルのスタイル（背景を白）
        style.configure("White.TFrame", background="white")
        style.configure("TLabel", background="white", font=("Meiryo", 14))

        # タイトルラベル
        ttk.Label(self, text="📖 セクションを選択", font=("Meiryo", 15, "bold")).pack(pady=(30, 20))

        # セクション選択メニュー
        self.section_var = tk.StringVar(value="section1")
        section_menu = ttk.OptionMenu(self, self.section_var, "section1", *CSV_FILES.keys())
        section_menu.pack(pady=5)

        # 出題数の選択
        self.num_questions_var = tk.IntVar(value=10)
        ttk.Label(self, text="📝 出題数").pack(pady=(20, 5))
        num_menu = ttk.OptionMenu(self, self.num_questions_var, 10, 5, 10, 15, 20, 30)
        num_menu.pack(pady=10)

        # 各ボタン（TButtonスタイルが自動で適用）
        ttk.Button(self, text="クイズ開始", command=self.start_quiz).pack(pady=(20, 10))
        ttk.Button(self, text="復習モード", command=self.start_review).pack(pady=5)
        ttk.Button(self, text="間違えた単語リスト", command=lambda: controller.show_frame("MistakeListPage")).pack(pady=5)

    def start_quiz(self):
        section = self.section_var.get()
        num_questions = self.num_questions_var.get()
        self.controller.start_quiz(section=section, num_questions=num_questions)

    def start_review(self):
        section = self.section_var.get()
        num_questions = self.num_questions_var.get()
        self.controller.start_quiz(section=section, num_questions=num_questions, review_mode=True)

class QuizPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(style="White.TFrame")  # 白背景

        # ==== スタイル設定 ====
        style = ttk.Style()
        style.configure("Quiz.TLabel", font=("Meiryo", 12), background="white")
        style.configure("QuizWord.TLabel", font=("Meiryo", 20, "bold"), background="white")
        style.configure("QuizFeedback.TLabel", font=("Meiryo", 14), background="white")

        style.configure("Quiz.TButton", font=("Meiryo", 12), padding=4)
        style.configure("Correct.TButton", font=("Meiryo", 12), foreground="white", background="#88D38C")
        style.map("Correct.TButton", background=[("active", "#88D38C")])

        style.configure("Incorrect.TButton", font=("Meiryo", 12), foreground="white", background="#F77A7A")
        style.map("Incorrect.TButton", background=[("active", "#D06060")])

        style.configure("Next.TButton", font=("Meiryo", 13), padding=6)

        # ==== UI構成 ====
        self.progress_label = ttk.Label(self, text="", style="Quiz.TLabel")
        self.progress_label.pack(pady=(25, 8))

        self.word_label = ttk.Label(self, text="", style="QuizWord.TLabel")
        self.word_label.pack(pady=15)

        self.buttons = []
        for i in range(4):
            btn = ttk.Button(self, text="", command=lambda i=i: self.check_answer(i), style="Quiz.TButton", width=18)
            btn.pack(pady=4, padx=20, ipady=6)
            self.buttons.append(btn)

        self.feedback = ttk.Label(self, text="", style="QuizFeedback.TLabel")
        self.feedback.pack(pady=8)

        self.next_btn = ttk.Button(self, text="次へ", command=self.next_question, state="disabled", style="Next.TButton", width=10)
        self.next_btn.pack(pady=8)

    def load_question(self):
        if self.controller.current_index >= self.controller.total:
            self.show_result()
            return

        word = self.controller.current_words[self.controller.current_index]
        section_words = CSV_DATA[word["section"]]
        self.progress_label.config(text=f"{self.controller.current_index + 1}/{self.controller.total} 問目")
        self.word_label.config(text=word["word"])

        correct_meaning = word["meaning"]
        wrong_choices = [w["meaning"] for w in section_words if w["meaning"] != correct_meaning]
        options = random.sample(wrong_choices, min(3, len(wrong_choices))) + [correct_meaning]
        random.shuffle(options)

        self.correct_answer = correct_meaning
        self.current_word = word

        for i, opt in enumerate(options):
            self.buttons[i].config(text=opt, state="normal", style="Quiz.TButton")

        self.feedback.config(text="")
        self.next_btn.config(state="disabled")

    def check_answer(self, index):
        selected = self.buttons[index].cget("text")
        is_correct = selected == self.correct_answer

        if is_correct:
            self.controller.score += 1
            self.feedback.config(text="正解！", foreground="green")
            self.buttons[index].config(style="Correct.TButton")
        else:
            self.feedback.config(text=f"不正解（正解: {self.correct_answer}）", foreground="red")
            self.controller.add_mistake(self.current_word)
            self.buttons[index].config(style="Incorrect.TButton")

        for btn in self.buttons:
            btn.config(state="disabled")

        if is_correct:
            self.after(1000, self.next_question)
        else:
            self.next_btn.config(state="normal")

    def next_question(self):
        self.controller.current_index += 1
        self.load_question()

    def show_result(self):
        if not self.controller.session_mistakes:
            messagebox.showinfo("結果", f"スコア: {self.controller.score}/{self.controller.total}\n間違えた単語はありません。")
            self.controller.show_frame("MainMenu")
            return

        popup = tk.Toplevel(self)
        popup.title("間違えた単語の確認")
        ttk.Label(popup, text="追加する間違えた単語を選択してください：", font=("Meiryo", 13)).pack(pady=10)

        vars = []
        for word in self.controller.session_mistakes:
            var = tk.BooleanVar(value=True)
            vars.append((var, word))
            ttk.Checkbutton(popup, text=f"{word['word']} - {word['meaning']} ({word['section']})", variable=var).pack(anchor="w", padx=20)

        def confirm():
            selected = [word for var, word in vars if var.get()]
            self.controller.finalize_mistakes(selected)
            popup.destroy()
            self.controller.show_frame("MainMenu")

        ttk.Button(popup, text="確定", command=lambda: [messagebox.showinfo("結果", f"スコア: {self.controller.score}/{self.controller.total}"), confirm()]).pack(pady=10)

class MistakeReviewPage(QuizPage):
    def start_review(self):
        self.load_question()

class MistakeListPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="White.TFrame")
        self.controller = controller

        # スタイル設定（背景・ボタンなど）
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Meiryo", 14), padding=10, background="#f0f0f0", foreground="black")
        style.map("TButton", background=[("active", "#d0e0ff")])
        style.configure("TLabel", background="white", font=("Meiryo", 14))
        style.configure("White.TFrame", background="white")

        # ヘッダーラベル
        ttk.Label(self, text="間違えた単語リスト", font=("Meiryo", 16, "bold")).pack(pady=(30, 10))

        # セクション選択ドロップダウン
        self.section_var = tk.StringVar(value="全て")
        section_options = ["全て"] + sorted(set(word['section'] for word in controller.mistakes))
        section_menu = ttk.OptionMenu(self, self.section_var, self.section_var.get(), *section_options, command=self.on_section_change)
        section_menu.pack(pady=(5, 10))

        # 単語リスト（Listbox：複数選択・範囲選択対応）
        self.word_listbox = tk.Listbox(
            self, width=40, height=10, font=("Meiryo", 10),
            bg="#ccdedd", fg="black", selectbackground="#1383fb",
            selectmode="extended"  # ← 範囲選択可能なモード
        )
        self.word_listbox.pack(pady=10)

        # ボタン類
        ttk.Button(self, text="削除", command=self.remove_selected).pack(pady=(5, 3))
        ttk.Button(self, text="メニューに戻る", command=lambda: controller.show_frame("MainMenu")).pack(pady=(5, 20))

        # 初期データ読み込み
        self.load_mistakes()

    def load_mistakes(self):
        """現在のセクションに応じた単語を表示"""
        self.word_listbox.delete(0, tk.END)
        selected_section = self.section_var.get()
        self.filtered_mistakes = []

        for word in self.controller.mistakes:
            if selected_section == "全て" or word["section"] == selected_section:
                display_text = f"{word['word']} - {word['meaning']} ({word['section']})"
                self.word_listbox.insert(tk.END, display_text)
                self.filtered_mistakes.append(word)

    def on_section_change(self, *_):
        """セクション選択変更時にリストを更新"""
        self.load_mistakes()

    def remove_selected(self):
        """選択中の単語（複数）を削除し、リストを更新"""
        selected_indices = self.word_listbox.curselection()
        if not selected_indices:
            return

        for i in reversed(selected_indices):
            word_to_remove = self.filtered_mistakes[i]
            self.controller.remove_mistake(word_to_remove)

        self.load_mistakes()

# ===== 実行 =====
if __name__ == "__main__":
    app = FlashcardApp()
    app.mainloop()
#　ver.1.4