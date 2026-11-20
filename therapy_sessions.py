import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_therapy_sessions(content):
    for widget in content.winfo_children():
        widget.destroy()

    plans = {}
    therapists = {}

    title = tk.Label(content, text="Therapy Session Management", font=("Arial", 18, "bold"))
    title.pack(pady=10)

    search_frame = tk.Frame(content)
    search_frame.pack(fill="x", padx=15, pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=5)

    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ID", "Date", "Time", "Patient", "Physiotherapist", "Status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=135, anchor="center")

    tree.column("Patient", width=150)
    tree.column("Physiotherapist", width=155)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    form = tk.LabelFrame(content, text="Therapy Session Details", padx=10, pady=10)
    form.pack(fill="x", padx=15, pady=10)

    fields = [
        ("Session Date (YYYY-MM-DD)", "date"),
        ("Session Time (HH:MM)", "time"),
        ("Treatment Plan", "plan"),
        ("Physiotherapist", "therapist"),
        ("Session Status", "status"),
        ("Session Notes", "notes")
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        row = i // 2
        col = (i % 2) * 2

        tk.Label(form, text=label).grid(row=row, column=col, padx=5, pady=6, sticky="w")

        if key in ("plan", "therapist"):
            entry = ttk.Combobox(form, width=30, state="readonly")
        elif key == "status":
            entry = ttk.Combobox(
                form, width=30, state="readonly",
                values=("Scheduled", "Completed", "Cancelled")
            )
        else:
            entry = tk.Entry(form, width=33)

        entry.grid(row=row, column=col + 1, padx=5, pady=6, sticky="w")
        entries[key] = entry

    def load_dropdowns():
        nonlocal plans, therapists

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT tp.plan_id, p.first_name || ' ' || p.last_name,
                   tp.start_date
            FROM treatment_plan tp
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            ORDER BY tp.plan_id
        """)

        plans = {
            f"{row[0]} - {row[1]} - {row[2]}": row[0]
            for row in cur.fetchall()
        }

        cur.execute("""
            SELECT therapist_id, first_name, last_name
            FROM physiotherapist
            ORDER BY therapist_id
        """)

        therapists = {
            f"{row[0]} - {row[1]} {row[2]}": row[0]
            for row in cur.fetchall()
        }

        cur.close()
        conn.close()

        entries["plan"]["values"] = list(plans.keys())
        entries["therapist"]["values"] = list(therapists.keys())

    def load_sessions(keyword=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT s.session_id, s.session_date, s.session_time,
                   p.first_name || ' ' || p.last_name,
                   t.first_name || ' ' || t.last_name,
                   s.session_status
            FROM therapy_session s
            JOIN treatment_plan tp ON s.plan_id = tp.plan_id
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN physiotherapist t ON s.therapist_id = t.therapist_id
            WHERE CAST(s.session_id AS TEXT) ILIKE %s
               OR p.first_name ILIKE %s
               OR p.last_name ILIKE %s
               OR s.session_status ILIKE %s
            ORDER BY s.session_id
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

    def add_session():
        try:
            plan_id = plans[entries["plan"].get()]
            therapist_id = therapists[entries["therapist"].get()]

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO therapy_session
                (session_date, session_time, session_status,
                 session_notes, plan_id, therapist_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                entries["date"].get(),
                entries["time"].get(),
                entries["status"].get(),
                entries["notes"].get(),
                plan_id,
                therapist_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_sessions()
            clear_form()
            messagebox.showinfo("Success", "Therapy session added successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select a treatment plan and physiotherapist.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_session():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a session to update.")
            return

        try:
            session_id = tree.item(selected[0])["values"][0]
            plan_id = plans[entries["plan"].get()]
            therapist_id = therapists[entries["therapist"].get()]

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE therapy_session
                SET session_date=%s, session_time=%s, session_status=%s,
                    session_notes=%s, plan_id=%s, therapist_id=%s
                WHERE session_id=%s
            """, (
                entries["date"].get(),
                entries["time"].get(),
                entries["status"].get(),
                entries["notes"].get(),
                plan_id,
                therapist_id,
                session_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_sessions()
            clear_form()
            messagebox.showinfo("Success", "Therapy session updated successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select a treatment plan and physiotherapist.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_session():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a session to delete.")
            return

        session_id = tree.item(selected[0])["values"][0]

        if not messagebox.askyesno("Confirm", "Delete this session?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM therapy_session WHERE session_id=%s",
                (session_id,)
            )

            conn.commit()
            cur.close()
            conn.close()

            load_sessions()
            clear_form()
            messagebox.showinfo("Success", "Therapy session deleted successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def select_session(event):
        selected = tree.selection()

        if not selected:
            return

        session_id = tree.item(selected[0])["values"][0]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT session_date, session_time, session_status,
                   session_notes, plan_id, therapist_id
            FROM therapy_session
            WHERE session_id=%s
        """, (session_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            clear_form()

            entries["date"].insert(0, str(row[0]))
            entries["time"].insert(0, str(row[1]))
            entries["status"].set(row[2])
            entries["notes"].insert(0, row[3] or "")

            for name, plan_id in plans.items():
                if plan_id == row[4]:
                    entries["plan"].set(name)
                    break

            for name, therapist_id in therapists.items():
                if therapist_id == row[5]:
                    entries["therapist"].set(name)
                    break

    buttons = tk.Frame(content)
    buttons.pack(pady=5)

    tk.Button(buttons, text="Add", width=12, command=add_session).pack(side="left", padx=5)
    tk.Button(buttons, text="Update", width=12, command=update_session).pack(side="left", padx=5)
    tk.Button(buttons, text="Delete", width=12, command=delete_session).pack(side="left", padx=5)
    tk.Button(buttons, text="Clear", width=12, command=clear_form).pack(side="left", padx=5)
    tk.Button(buttons, text="Refresh", width=12, command=lambda: load_sessions()).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Search",
        command=lambda: load_sessions(search_var.get())
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Show All",
        command=lambda: (search_var.set(""), load_sessions())
    ).pack(side="left", padx=5)

    tree.bind("<<TreeviewSelect>>", select_session)

    try:
        load_dropdowns()
        load_sessions()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
