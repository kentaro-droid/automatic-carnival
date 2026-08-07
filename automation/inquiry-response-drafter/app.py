import tkinter as tk
from tkinter import ttk, messagebox

from inquiry_response import Inquiry, generate_response


class InquiryResponseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rental Inquiry Response Drafter")
        self.geometry("980x760")
        self.minsize(820, 650)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(18, 16, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Rental Inquiry Response Drafter", font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Enter fictional or anonymized inquiry data. Always verify property facts before sending.",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

        form = ttk.Frame(body, padding=12)
        output = ttk.Frame(body, padding=12)
        body.add(form, weight=1)
        body.add(output, weight=2)

        self.language = tk.StringVar(value="en")
        self.customer_name = tk.StringVar(value="Alex Smith")
        self.property_name = tk.StringVar(value="Sakura Residence Azabu")
        self.request_type = tk.StringVar(value="viewing")
        self.move_in_date = tk.StringVar(value="2026-09-15")
        self.budget = tk.StringVar(value="JPY 650,000/month")

        fields = [
            ("Reply language", self.language, ("en", "ja")),
            ("Customer name", self.customer_name, None),
            ("Property name", self.property_name, None),
            ("Request type", self.request_type, ("viewing", "availability", "application", "general")),
            ("Move-in date", self.move_in_date, None),
            ("Budget", self.budget, None),
        ]

        for row, (label, variable, choices) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row * 2, column=0, sticky="w", pady=(6, 2))
            if choices:
                widget = ttk.Combobox(form, textvariable=variable, values=choices, state="readonly")
            else:
                widget = ttk.Entry(form, textvariable=variable)
            widget.grid(row=row * 2 + 1, column=0, sticky="ew")

        ttk.Label(form, text="Requirements").grid(row=12, column=0, sticky="w", pady=(10, 2))
        self.requirements = tk.Text(form, height=6, wrap="word")
        self.requirements.insert(
            "1.0",
            "a furnished 2LDK or larger apartment in the Azabu area with English support",
        )
        self.requirements.grid(row=13, column=0, sticky="ew")

        ttk.Label(form, text="Internal notes").grid(row=14, column=0, sticky="w", pady=(10, 2))
        self.notes = tk.Text(form, height=5, wrap="word")
        self.notes.insert("1.0", "Fictional test data only.")
        self.notes.grid(row=15, column=0, sticky="ew")

        buttons = ttk.Frame(form)
        buttons.grid(row=16, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Generate Draft", command=self.generate).pack(side="left")
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left", padx=(8, 0))

        form.columnconfigure(0, weight=1)

        ttk.Label(output, text="Generated draft", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.result = tk.Text(output, wrap="word", undo=True)
        self.result.pack(fill="both", expand=True, pady=(6, 8))
        ttk.Button(output, text="Copy to Clipboard", command=self.copy_result).pack(anchor="e")

    def generate(self):
        required = {
            "Customer name": self.customer_name.get().strip(),
            "Property name": self.property_name.get().strip(),
            "Move-in date": self.move_in_date.get().strip(),
            "Budget": self.budget.get().strip(),
            "Requirements": self.requirements.get("1.0", "end").strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            messagebox.showwarning("Missing information", "Please complete: " + ", ".join(missing))
            return

        inquiry = Inquiry(
            inquiry_language=self.language.get(),
            customer_name=self.customer_name.get().strip(),
            property_name=self.property_name.get().strip(),
            request_type=self.request_type.get(),
            move_in_date=self.move_in_date.get().strip(),
            budget=self.budget.get().strip(),
            requirements=self.requirements.get("1.0", "end").strip(),
            notes=self.notes.get("1.0", "end").strip(),
        )

        try:
            draft = generate_response(inquiry)
        except ValueError as exc:
            messagebox.showerror("Input error", str(exc))
            return

        self.result.delete("1.0", "end")
        self.result.insert("1.0", draft)

    def copy_result(self):
        text = self.result.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Nothing to copy", "Generate a draft first.")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def clear(self):
        self.customer_name.set("")
        self.property_name.set("")
        self.move_in_date.set("")
        self.budget.set("")
        self.requirements.delete("1.0", "end")
        self.notes.delete("1.0", "end")
        self.result.delete("1.0", "end")


if __name__ == "__main__":
    InquiryResponseApp().mainloop()
