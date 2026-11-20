import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_progress_records(content):
    for widget in content.winfo_children():
        widget.destroy()

    selected_id = None
    sessions = {}

    frame = tk.Frame(content, padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Progress Records", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 12))

    search_frame = tk.Frame(frame)
    search_frame.pack(fill="x", pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=(0, 8))

    form = tk.LabelFrame(frame, text="Progress Record Details", padx=10, pady=10)
    form.pack(fill="x", pady=10)

    tk.Label(form, text="Recorded Date").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    date_entry = tk.Entry(form, width=25)
    date_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(form, text="Therapy Session").grid(row=0, column=2, sticky="w", padx=5, pady=5)
    session_var = tk.StringVar()
    session_combo = ttk.Combobox(form, textvariable=session_var, width=35, state="readonly")
    session_combo.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(form, text="Pain Score (0-10)").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    pain_entry = tk.Entry(form, width=25)
    pain_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(form, text="Mobility Notes").grid(row=1, column=2, sticky="w", padx=5, pady=5)
    mobility_entry = tk.Entry(form, width=38)
    mobility_entry.grid(row=1, column=3, padx=5, pady=5)

    tk.Label(form, text="Progress Notes").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
    notes_entry = tk.Text(form, width=65, height=3)
    notes_entry.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")

    table_frame = tk.Frame(frame)
    table_frame.pack(fill="both", expand=True, pady=10)

    columns = ("ID", "Date", "Session ID", "Patient", "Pain Score", "Mobility Notes")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=130)

    tree.column("Patient", width=180)
    tree.column("Mobility Notes", width=220)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def load_sessions():
        nonlocal sessions
        sessions = {}

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.session_id, s.session_date, p.first_name, p.last_name
            FROM therapy_session s
            JOIN treatment_plan tp ON s.plan_id = tp.plan_id
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            ORDER BY s.session_id
        """)

        options = []
        for session_id, date, first, last in cur.fetchall():
            label = f"{session_id} - {date} - {first} {last}"
            sessions[label] = session_id
            options.append(label)

        session_combo["values"] = options
        cur.close()
        conn.close()

    def load_records(search=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pr.progress_id, pr.recorded_date, s.session_id,
                   p.first_name || ' ' || p.last_name,
                   pr.pain_score, pr.mobility_notes
            FROM progress_record pr
            JOIN therapy_session s ON pr.session_id = s.session_id
            JOIN treatment_plan tp ON s.plan_id = tp.plan_id
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE CAST(pr.progress_id AS TEXT) ILIKE %s
               OR CAST(s.session_id AS TEXT) ILIKE %s
               OR p.first_name ILIKE %s
               OR p.last_name ILIKE %s
            ORDER BY pr.progress_id
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))

        for row in cur.fetchall():
            tree.insert("", "end", values=row)

        cur.close()
        conn.close()

    def clear_fields():
        nonlocal selected_id
        selected_id = None
        date_entry.delete(0, tk.END)
        pain_entry.delete(0, tk.END)
        mobility_entry.delete(0, tk.END)
        notes_entry.delete("1.0", tk.END)
        session_combo.set("")

    def select_record(event):
        nonlocal selected_id
        selected = tree.focus()
        if not selected:
            return

        values = tree.item(selected, "values")
        selected_id = values[0]

        date_entry.delete(0, tk.END)
        date_entry.insert(0, str(values[1]))

        pain_entry.delete(0, tk.END)
        pain_entry.insert(0, str(values[4]))

        mobility_entry.delete(0, tk.END)
        mobility_entry.insert(0, values[5] or "")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pr.session_id, pr.progress_notes
            FROM progress_record pr
            WHERE pr.progress_id = %s
        """, (selected_id,))
        session_id, notes = cur.fetchone()
        cur.close()
        conn.close()

        for label, sid in sessions.items():
            if sid == session_id:
                session_combo.set(label)
                break

        notes_entry.delete("1.0", tk.END)
        notes_entry.insert("1.0", notes or "")

    def add_record():
        try:
            date = date_entry.get().strip()
            pain = int(pain_entry.get())
            mobility = mobility_entry.get().strip() or None
            notes = notes_entry.get("1.0", tk.END).strip() or None
            session_id = sessions.get(session_var.get())

            if not date or session_id is None:
                messagebox.showerror("Error", "Please enter the date and select a therapy session.")
                return

            if not 0 <= pain <= 10:
                messagebox.showerror("Error", "Pain score must be between 0 and 10.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO progress_record
                (recorded_date, pain_score, mobility_notes, progress_notes, session_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (date, pain, mobility, notes, session_id))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Progress record added successfully.")
            clear_fields()
            load_records(search_var.get())

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid pain score.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_record():
        if selected_id is None:
            messagebox.showerror("Error", "Please select a record to update.")
            return

        try:
            date = date_entry.get().strip()
            pain = int(pain_entry.get())
            mobility = mobility_entry.get().strip() or None
            notes = notes_entry.get("1.0", tk.END).strip() or None
            session_id = sessions.get(session_var.get())

            if not date or session_id is None:
                messagebox.showerror("Error", "Please enter the date and select a therapy session.")
                return

            if not 0 <= pain <= 10:
                messagebox.showerror("Error", "Pain score must be between 0 and 10.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE progress_record
                SET recorded_date = %s, pain_score = %s, mobility_notes = %s,
                    progress_notes = %s, session_id = %s
                WHERE progress_id = %s
            """, (date, pain, mobility, notes, session_id, selected_id))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Progress record updated successfully.")
            clear_fields()
            load_records(search_var.get())

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid pain score.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_record():
        if selected_id is None:
            messagebox.showerror("Error", "Please select a record to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete this progress record?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM progress_record WHERE progress_id = %s", (selected_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Progress record deleted successfully.")
            clear_fields()
            load_records(search_var.get())

        except Exception as e:
            messagebox.showerror("Error", str(e))

    tree.bind("<<TreeviewSelect>>", select_record)

    tk.Button(search_frame, text="Search", command=lambda: load_records(search_var.get())).pack(side="left", padx=3)
    tk.Button(search_frame, text="Show All", command=lambda: (search_var.set(""), load_records())).pack(side="left", padx=3)

    button_frame = tk.Frame(frame)
    button_frame.pack(fill="x", pady=5)

    tk.Button(button_frame, text="Add", width=12, command=add_record).pack(side="left", padx=5)
    tk.Button(button_frame, text="Update", width=12, command=update_record).pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete", width=12, command=delete_record).pack(side="left", padx=5)
    tk.Button(button_frame, text="Clear", width=12, command=clear_fields).pack(side="left", padx=5)

    load_sessions()
    load_records()
