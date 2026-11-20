import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_exercises(content):
    for widget in content.winfo_children():
        widget.destroy()

    title = tk.Label(content, text="Exercise Management", font=("Arial", 18, "bold"))
    title.pack(pady=10)

    search_frame = tk.Frame(content)
    search_frame.pack(fill="x", padx=15, pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=5)

    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ID", "Exercise Name", "Target Body Area", "Difficulty Level", "Description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")

    tree.column("Exercise Name", width=180)
    tree.column("Description", width=300)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    form = tk.LabelFrame(content, text="Exercise Details", padx=10, pady=10)
    form.pack(fill="x", padx=15, pady=10)

    fields = [
        ("Exercise Name", "name"),
        ("Target Body Area", "body_area"),
        ("Difficulty Level", "difficulty"),
        ("Description", "description")
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        row = i // 2
        col = (i % 2) * 2

        tk.Label(form, text=label).grid(row=row, column=col, padx=5, pady=6, sticky="w")

        if key == "difficulty":
            entry = ttk.Combobox(
                form, width=28, state="readonly",
                values=("Beginner", "Intermediate", "Advanced")
            )
        else:
            entry = tk.Entry(form, width=31)

        entry.grid(row=row, column=col + 1, padx=5, pady=6, sticky="w")
        entries[key] = entry

    def load_exercises(keyword=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT exercise_id, exercise_name, target_body_area,
                   difficulty_level, description
            FROM exercise
            WHERE CAST(exercise_id AS TEXT) ILIKE %s
               OR exercise_name ILIKE %s
               OR target_body_area ILIKE %s
               OR difficulty_level ILIKE %s
            ORDER BY exercise_id
        """

        pattern = f"%{keyword}%"
        cur.execute(query, (pattern, pattern, pattern, pattern))

        for row in cur.fetchall():
            tree.insert("", "end", values=row)

        cur.close()
        conn.close()

    def clear_form():
        for entry in entries.values():
            entry.delete(0, "end")

    def add_exercise():
        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO exercise
                (exercise_name, description, target_body_area, difficulty_level)
                VALUES (%s, %s, %s, %s)
            """, (
                entries["name"].get(),
                entries["description"].get(),
                entries["body_area"].get(),
                entries["difficulty"].get()
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_exercises()
            clear_form()
            messagebox.showinfo("Success", "Exercise added successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_exercise():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select an exercise to update.")
            return

        try:
            exercise_id = tree.item(selected[0])["values"][0]

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE exercise
                SET exercise_name=%s, description=%s,
                    target_body_area=%s, difficulty_level=%s
                WHERE exercise_id=%s
            """, (
                entries["name"].get(),
                entries["description"].get(),
                entries["body_area"].get(),
                entries["difficulty"].get(),
                exercise_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_exercises()
            clear_form()
            messagebox.showinfo("Success", "Exercise updated successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_exercise():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select an exercise to delete.")
            return

        exercise_id = tree.item(selected[0])["values"][0]

        if not messagebox.askyesno("Confirm", "Delete this exercise?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM exercise WHERE exercise_id=%s",
                (exercise_id,)
            )

            conn.commit()
            cur.close()
            conn.close()

            load_exercises()
            clear_form()
            messagebox.showinfo("Success", "Exercise deleted successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def select_exercise(event):
        selected = tree.selection()

        if not selected:
            return

        exercise_id = tree.item(selected[0])["values"][0]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT exercise_name, description, target_body_area, difficulty_level
            FROM exercise
            WHERE exercise_id=%s
        """, (exercise_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            clear_form()
            entries["name"].insert(0, row[0] or "")
            entries["description"].insert(0, row[1] or "")
            entries["body_area"].insert(0, row[2] or "")
            entries["difficulty"].set(row[3] or "")

    buttons = tk.Frame(content)
    buttons.pack(pady=5)

    tk.Button(buttons, text="Add", width=12, command=add_exercise).pack(side="left", padx=5)
    tk.Button(buttons, text="Update", width=12, command=update_exercise).pack(side="left", padx=5)
    tk.Button(buttons, text="Delete", width=12, command=delete_exercise).pack(side="left", padx=5)
    tk.Button(buttons, text="Clear", width=12, command=clear_form).pack(side="left", padx=5)
    tk.Button(buttons, text="Refresh", width=12, command=lambda: load_exercises()).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Search",
        command=lambda: load_exercises(search_var.get())
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Show All",
        command=lambda: (search_var.set(""), load_exercises())
    ).pack(side="left", padx=5)

    tree.bind("<<TreeviewSelect>>", select_exercise)

    try:
        load_exercises()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
