import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_patients(content):
    for widget in content.winfo_children():
        widget.destroy()

    tk.Label(
        content,
        text="Patient Management",
        font=("Arial", 20, "bold"),
        bg="#f4f6f9",
        fg="#243447"
    ).pack(pady=15)

    # Search
    search_frame = tk.Frame(content, bg="#f4f6f9")
    search_frame.pack(fill="x", padx=20, pady=5)

    tk.Label(search_frame, text="Search:", bg="#f4f6f9").pack(side="left")

    search_entry = tk.Entry(search_frame, width=35)
    search_entry.pack(side="left", padx=10)

    # Patient form
    form = tk.LabelFrame(
        content, text="Patient Details",
        bg="#f4f6f9", padx=10, pady=10
    )
    form.pack(fill="x", padx=20, pady=10)

    fields = [
        "First Name", "Last Name", "Date of Birth",
        "Gender", "Phone", "Email", "Address"
    ]

    entries = {}

    for i, field in enumerate(fields):
        row = i // 4
        col = (i % 4) * 2

        tk.Label(form, text=field, bg="#f4f6f9").grid(
            row=row, column=col, padx=5, pady=7, sticky="w"
        )

        entry = tk.Entry(form, width=20)
        entry.grid(row=row, column=col + 1, padx=5, pady=7)

        entries[field] = entry

    # Patient table
    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = (
        "ID", "First Name", "Last Name", "Date of Birth",
        "Gender", "Phone", "Email"
    )

    tree = ttk.Treeview(
        table_frame, columns=columns,
        show="headings", height=10
    )

    widths = [45, 100, 100, 100, 80, 110, 150]

    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=tree.yview
    )

    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Load patients
    def load_patients(search=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            query = """
                SELECT patient_id, first_name, last_name,
                       date_of_birth, gender, phone, email, address
                FROM patient
                WHERE CAST(patient_id AS TEXT) ILIKE %s
                   OR first_name ILIKE %s
                   OR last_name ILIKE %s
                   OR phone ILIKE %s
                ORDER BY patient_id
            """

            pattern = f"%{search}%"
            cur.execute(query, (pattern, pattern, pattern, pattern))

            for row in cur.fetchall():
                tree.insert("", "end", values=row)

            cur.close()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            if conn:
                conn.close()

    # Clear form
    def clear_form():
        for entry in entries.values():
            entry.delete(0, tk.END)

        tree.selection_remove(tree.selection())

    # Select patient
    def select_patient(event):
        selected = tree.focus()

        if not selected:
            return

        patient_id = tree.item(selected, "values")[0]

        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT first_name, last_name, date_of_birth,
                       gender, phone, email, address
                FROM patient
                WHERE patient_id = %s
            """, (patient_id,))

            values = cur.fetchone()
            cur.close()

            if values:
                for field, value in zip(fields, values):
                    entries[field].delete(0, tk.END)
                    entries[field].insert(
                        0, str(value) if value is not None else ""
                    )

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        finally:
            if conn:
                conn.close()

    tree.bind("<<TreeviewSelect>>", select_patient)

    # Get form values
    def get_form_values():
        values = [entries[field].get().strip() for field in fields]

        if not values[0] or not values[1] or not values[4]:
            messagebox.showwarning(
                "Missing Details",
                "First name, last name and phone are required."
            )
            return None

        values[2] = values[2] or None
        values[3] = values[3] or None
        values[5] = values[5] or None
        values[6] = values[6] or None

        return values

    # Add patient
    def add_patient():
        values = get_form_values()

        if values is None:
            return

        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO patient
                    (first_name, last_name, date_of_birth,
                     gender, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, values)
                cur.close()

            messagebox.showinfo("Success", "Patient added successfully.")
            clear_form()
            load_patients(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            if conn:
                conn.close()

    # Update patient
    def update_patient():
        selected = tree.focus()

        if not selected:
            messagebox.showwarning(
                "Select Patient",
                "Please select a patient from the table first."
            )
            return

        values = get_form_values()

        if values is None:
            return

        patient_id = tree.item(selected, "values")[0]
        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE patient
                    SET first_name=%s, last_name=%s,
                        date_of_birth=%s, gender=%s,
                        phone=%s, email=%s, address=%s
                    WHERE patient_id=%s
                """, values + [patient_id])
                cur.close()

            messagebox.showinfo("Success", "Patient updated successfully.")
            clear_form()
            load_patients(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            if conn:
                conn.close()

    # Delete patient
    def delete_patient():
        selected = tree.focus()

        if not selected:
            messagebox.showwarning(
                "Select Patient",
                "Please select a patient from the table first."
            )
            return

        patient_id = tree.item(selected, "values")[0]

        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this patient?"
        ):
            return

        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM patient WHERE patient_id=%s",
                    (patient_id,)
                )
                cur.close()

            messagebox.showinfo("Success", "Patient deleted successfully.")
            clear_form()
            load_patients(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror(
                "Error",
                "Could not delete patient. They may have related records.\n\n"
                + str(e)
            )

        finally:
            if conn:
                conn.close()

    # Search and refresh
    def search_patients():
        load_patients(search_entry.get().strip())

    def refresh_patients():
        search_entry.delete(0, tk.END)
        load_patients()

    # Buttons
    button_frame = tk.Frame(content, bg="#f4f6f9")
    button_frame.pack(pady=8)

    tk.Button(
        button_frame, text="Add Patient",
        command=add_patient, width=13
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Update Patient",
        command=update_patient, width=13
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Delete Patient",
        command=delete_patient, width=13
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Clear Form",
        command=clear_form, width=13
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Search",
        command=search_patients
    ).pack(side="left")

    tk.Button(
        search_frame, text="Refresh",
        command=refresh_patients
    ).pack(side="left", padx=5)

    load_patients()
