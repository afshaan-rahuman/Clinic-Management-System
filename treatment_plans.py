import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_treatment_plans(content):
    for widget in content.winfo_children():
        widget.destroy()

    assessments = {}
    assessment_therapists = {}

    title = tk.Label(content, text="Treatment Plan Management", font=("Arial", 18, "bold"))
    title.pack(pady=10)

    search_frame = tk.Frame(content)
    search_frame.pack(fill="x", padx=15, pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=5)

    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ID", "Start Date", "End Date", "Patient", "Physiotherapist", "Status", "Total Fee")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=125, anchor="center")

    tree.column("Patient", width=145)
    tree.column("Physiotherapist", width=150)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    form = tk.LabelFrame(content, text="Treatment Plan Details", padx=10, pady=10)
    form.pack(fill="x", padx=15, pady=10)

    fields = [
        ("Start Date (YYYY-MM-DD)", "start_date"),
        ("End Date (YYYY-MM-DD)", "end_date"),
        ("Assessment", "assessment"),
        ("Plan Status", "status"),
        ("Total Fee", "fee"),
        ("Goals", "goals"),
        ("Notes", "notes")
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        row = i // 2
        col = (i % 2) * 2

        tk.Label(form, text=label).grid(row=row, column=col, padx=5, pady=6, sticky="w")

        if key == "assessment":
            entry = ttk.Combobox(form, width=40, state="readonly")
        elif key == "status":
            entry = ttk.Combobox(
                form, width=28, state="readonly",
                values=("Active", "Completed", "On Hold")
            )
        else:
            entry = tk.Entry(form, width=31)

        entry.grid(row=row, column=col + 1, padx=5, pady=6, sticky="w")
        entries[key] = entry

    def load_dropdowns():
        nonlocal assessments, assessment_therapists

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT a.assessment_id, a.assessment_date,
                   p.first_name || ' ' || p.last_name,
                   a.therapist_id,
                   t.first_name || ' ' || t.last_name
            FROM assessment a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN physiotherapist t ON a.therapist_id = t.therapist_id
            ORDER BY a.assessment_id
        """)

        assessments = {}
        assessment_therapists = {}

        for row in cur.fetchall():
            assessment_name = f"{row[0]} - {row[1]} - {row[2]} - {row[4]}"

            assessments[assessment_name] = row[0]
            assessment_therapists[assessment_name] = row[3]

        cur.close()
        conn.close()

        entries["assessment"]["values"] = list(assessments.keys())

    def load_plans(keyword=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT tp.plan_id, tp.start_date, tp.end_date,
                   p.first_name || ' ' || p.last_name,
                   t.first_name || ' ' || t.last_name,
                   tp.plan_status, tp.total_fee
            FROM treatment_plan tp
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN physiotherapist t ON tp.therapist_id = t.therapist_id
            WHERE CAST(tp.plan_id AS TEXT) ILIKE %s
               OR p.first_name ILIKE %s
               OR p.last_name ILIKE %s
               OR tp.plan_status ILIKE %s
            ORDER BY tp.plan_id
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

    def add_plan():
        try:
            assessment_name = entries["assessment"].get()
            assessment_id = assessments[assessment_name]
            therapist_id = assessment_therapists[assessment_name]
            fee = float(entries["fee"].get())

            if fee < 0:
                raise ValueError

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO treatment_plan
                (start_date, end_date, goals, plan_status, total_fee,
                 notes, assessment_id, therapist_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entries["start_date"].get(),
                entries["end_date"].get(),
                entries["goals"].get(),
                entries["status"].get(),
                fee,
                entries["notes"].get(),
                assessment_id,
                therapist_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_plans()
            clear_form()
            messagebox.showinfo("Success", "Treatment plan added successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select an assessment.")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid non-negative total fee.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_plan():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a treatment plan to update.")
            return

        try:
            plan_id = tree.item(selected[0])["values"][0]
            assessment_name = entries["assessment"].get()
            assessment_id = assessments[assessment_name]
            therapist_id = assessment_therapists[assessment_name]
            fee = float(entries["fee"].get())

            if fee < 0:
                raise ValueError

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE treatment_plan
                SET start_date=%s, end_date=%s, goals=%s,
                    plan_status=%s, total_fee=%s, notes=%s,
                    assessment_id=%s, therapist_id=%s
                WHERE plan_id=%s
            """, (
                entries["start_date"].get(),
                entries["end_date"].get(),
                entries["goals"].get(),
                entries["status"].get(),
                fee,
                entries["notes"].get(),
                assessment_id,
                therapist_id,
                plan_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_plans()
            clear_form()
            messagebox.showinfo("Success", "Treatment plan updated successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select an assessment.")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid non-negative total fee.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_plan():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a treatment plan to delete.")
            return

        plan_id = tree.item(selected[0])["values"][0]

        if not messagebox.askyesno("Confirm", "Delete this treatment plan?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM treatment_plan WHERE plan_id=%s",
                (plan_id,)
            )

            conn.commit()
            cur.close()
            conn.close()

            load_plans()
            clear_form()
            messagebox.showinfo("Success", "Treatment plan deleted successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def select_plan(event):
        selected = tree.selection()

        if not selected:
            return

        plan_id = tree.item(selected[0])["values"][0]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT start_date, end_date, goals, plan_status,
                   total_fee, notes, assessment_id
            FROM treatment_plan
            WHERE plan_id=%s
        """, (plan_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            clear_form()

            entries["start_date"].insert(0, str(row[0]))
            entries["end_date"].insert(0, str(row[1]) if row[1] else "")
            entries["goals"].insert(0, row[2] or "")
            entries["status"].set(row[3])
            entries["fee"].insert(0, str(row[4]))
            entries["notes"].insert(0, row[5] or "")

            for name, assessment_id in assessments.items():
                if assessment_id == row[6]:
                    entries["assessment"].set(name)
                    break

    buttons = tk.Frame(content)
    buttons.pack(pady=5)

    tk.Button(buttons, text="Add", width=12, command=add_plan).pack(side="left", padx=5)
    tk.Button(buttons, text="Update", width=12, command=update_plan).pack(side="left", padx=5)
    tk.Button(buttons, text="Delete", width=12, command=delete_plan).pack(side="left", padx=5)
    tk.Button(buttons, text="Clear", width=12, command=clear_form).pack(side="left", padx=5)
    tk.Button(buttons, text="Refresh", width=12, command=lambda: load_plans()).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Search",
        command=lambda: load_plans(search_var.get())
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Show All",
        command=lambda: (search_var.set(""), load_plans())
    ).pack(side="left", padx=5)

    tree.bind("<<TreeviewSelect>>", select_plan)

    try:
        load_dropdowns()
        load_plans()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
