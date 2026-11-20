
import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_assessments(content):
    for widget in content.winfo_children():
        widget.destroy()

    patients = {}
    therapists = {}

    title = tk.Label(content, text="Assessment Management", font=("Arial", 18, "bold"))
    title.pack(pady=10)

    search_frame = tk.Frame(content)
    search_frame.pack(fill="x", padx=15, pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=5)

    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ID", "Date", "Patient", "Physiotherapist", "Condition", "Body Area", "Pain Score","Mobility Limitations", "Assessment Notes")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=115, anchor="center")

    tree.column("Condition", width=180)
    tree.column("Patient", width=140)
    tree.column("Physiotherapist", width=150)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    horizontal_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=horizontal_scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    horizontal_scrollbar.pack(side="bottom", fill="x")

    form = tk.LabelFrame(content, text="Assessment Details", padx=10, pady=10)
    form.pack(fill="x", padx=15, pady=10)

    fields = [
        ("Assessment Date (YYYY-MM-DD)", "date"),
        ("Patient", "patient"),
        ("Physiotherapist", "therapist"),
        ("Condition Description", "condition"),
        ("Affected Body Area", "body_area"),
        ("Pain Score (0-10)", "pain_score"),
        ("Mobility Limitations", "mobility"),
        ("Assessment Notes", "notes")
    ]

    entries = {}
    for i, (label, key) in enumerate(fields):
        row = i // 2
        col = (i % 2) * 2

        tk.Label(form, text=label).grid(row=row, column=col, padx=5, pady=6, sticky="w")

        if key in ("patient", "therapist"):
            entry = ttk.Combobox(form, width=28, state="readonly")
        else:
            entry = tk.Entry(form, width=31)

        entry.grid(row=row, column=col + 1, padx=5, pady=6, sticky="w")
        entries[key] = entry

    def load_dropdowns():
        nonlocal patients, therapists

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT patient_id, first_name, last_name FROM patient ORDER BY patient_id")
        patients = {
            f"{row[0]} - {row[1]} {row[2]}": row[0]
            for row in cur.fetchall()
        }

        cur.execute("SELECT therapist_id, first_name, last_name FROM physiotherapist ORDER BY therapist_id")
        therapists = {
            f"{row[0]} - {row[1]} {row[2]}": row[0]
            for row in cur.fetchall()
        }

        cur.close()
        conn.close()

        entries["patient"]["values"] = list(patients.keys())
        entries["therapist"]["values"] = list(therapists.keys())

    def load_assessments(keyword=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT a.assessment_id, a.assessment_date,
                   p.first_name || ' ' || p.last_name,
                   t.first_name || ' ' || t.last_name,
                   a.condition_description, a.affected_body_area,
                   a.pain_score, a.mobility_limitations, a.assessment_notes
            FROM assessment a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN physiotherapist t ON a.therapist_id = t.therapist_id
            WHERE CAST(a.assessment_id AS TEXT) ILIKE %s
               OR p.first_name ILIKE %s
               OR p.last_name ILIKE %s
               OR a.condition_description ILIKE %s
            ORDER BY a.assessment_id
        """

        pattern = f"%{keyword}%"
        cur.execute(query, (pattern, pattern, pattern, pattern))

        for row in cur.fetchall():
            tree.insert("", "end", values=row)

        cur.close()
        conn.close()

    def clear_form():
        for key, entry in entries.items():
            entry.delete(0, "end")

    def add_assessment():
        try:
            patient_id = patients[entries["patient"].get()]
            therapist_id = therapists[entries["therapist"].get()]
            pain = int(entries["pain_score"].get())

            if not 0 <= pain <= 10:
                raise ValueError

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO assessment
                (assessment_date, condition_description, affected_body_area,
                 pain_score, mobility_limitations, assessment_notes,
                 patient_id, therapist_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entries["date"].get(),
                entries["condition"].get(),
                entries["body_area"].get(),
                pain,
                entries["mobility"].get(),
                entries["notes"].get(),
                patient_id,
                therapist_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_assessments()
            clear_form()
            messagebox.showinfo("Success", "Assessment added successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select a patient and physiotherapist.")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid pain score between 0 and 10.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_assessment():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select an assessment to update.")
            return

        try:
            assessment_id = tree.item(selected[0])["values"][0]
            patient_id = patients[entries["patient"].get()]
            therapist_id = therapists[entries["therapist"].get()]
            pain = int(entries["pain_score"].get())

            if not 0 <= pain <= 10:
                raise ValueError

            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE assessment
                SET assessment_date=%s, condition_description=%s,
                    affected_body_area=%s, pain_score=%s,
                    mobility_limitations=%s, assessment_notes=%s,
                    patient_id=%s, therapist_id=%s
                WHERE assessment_id=%s
            """, (
                entries["date"].get(),
                entries["condition"].get(),
                entries["body_area"].get(),
                pain,
                entries["mobility"].get(),
                entries["notes"].get(),
                patient_id,
                therapist_id,
                assessment_id
            ))

            conn.commit()
            cur.close()
            conn.close()

            load_assessments()
            clear_form()
            messagebox.showinfo("Success", "Assessment updated successfully.")

        except KeyError:
            messagebox.showerror("Error", "Please select a patient and physiotherapist.")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid pain score between 0 and 10.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_assessment():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select an assessment to delete.")
            return

        assessment_id = tree.item(selected[0])["values"][0]

        if not messagebox.askyesno("Confirm", "Delete this assessment?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM assessment WHERE assessment_id=%s",
                (assessment_id,)
            )

            conn.commit()
            cur.close()
            conn.close()

            load_assessments()
            clear_form()
            messagebox.showinfo("Success", "Assessment deleted successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def select_assessment(event):
        selected = tree.selection()

        if not selected:
            return

        assessment_id = tree.item(selected[0])["values"][0]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT assessment_date, condition_description, affected_body_area,
                   pain_score, mobility_limitations, assessment_notes,
                   patient_id, therapist_id
            FROM assessment
            WHERE assessment_id=%s
        """, (assessment_id,))

        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            clear_form()

            entries["date"].insert(0, str(row[0]))
            entries["condition"].insert(0, row[1] or "")
            entries["body_area"].insert(0, row[2] or "")
            entries["pain_score"].insert(0, str(row[3]))
            entries["mobility"].insert(0, row[4] or "")
            entries["notes"].insert(0, row[5] or "")

            for name, patient_id in patients.items():
                if patient_id == row[6]:
                    entries["patient"].set(name)
                    break

            for name, therapist_id in therapists.items():
                if therapist_id == row[7]:
                    entries["therapist"].set(name)
                    break

    buttons = tk.Frame(content)
    buttons.pack(pady=5)

    tk.Button(buttons, text="Add", width=12, command=add_assessment).pack(side="left", padx=5)
    tk.Button(buttons, text="Update", width=12, command=update_assessment).pack(side="left", padx=5)
    tk.Button(buttons, text="Delete", width=12, command=delete_assessment).pack(side="left", padx=5)
    tk.Button(buttons, text="Clear", width=12, command=clear_form).pack(side="left", padx=5)
    tk.Button(buttons, text="Refresh", width=12, command=lambda: load_assessments()).pack(side="left", padx=5)
    tk.Button(search_frame, text="Search", command=lambda: load_assessments(search_var.get())).pack(side="left", padx=5)
    tk.Button(search_frame, text="Show All", command=lambda: (search_var.set(""), load_assessments())).pack(side="left", padx=5)

    tree.bind("<<TreeviewSelect>>", select_assessment)

    try:
        load_dropdowns()
        load_assessments()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
