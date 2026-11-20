import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_physiotherapists(content):
    for widget in content.winfo_children():
        widget.destroy()

    tk.Label(
        content,
        text="Physiotherapist Management",
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

    # Form
    form = tk.LabelFrame(
        content, text="Physiotherapist Details",
        bg="#f4f6f9", padx=10, pady=10
    )
    form.pack(fill="x", padx=20, pady=10)

    fields = [
        "First Name", "Last Name", "Specialization",
        "Phone", "Email", "Joining Date"
    ]

    entries = {}

    for i, field in enumerate(fields):
        row = i // 3
        col = (i % 3) * 2

        tk.Label(form, text=field, bg="#f4f6f9").grid(
            row=row, column=col, padx=5, pady=7, sticky="w"
        )

        entry = tk.Entry(form, width=22)
        entry.grid(row=row, column=col + 1, padx=5, pady=7)

        entries[field] = entry

    # Table
    table_frame = tk.Frame(content)
    table_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = (
        "ID", "First Name", "Last Name",
        "Specialization", "Phone", "Email", "Joining Date"
    )

    tree = ttk.Treeview(
        table_frame, columns=columns,
        show="headings", height=10
    )

    widths = [45, 100, 100, 140, 110, 150, 100]

    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")

    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=tree.yview
    )

    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Load physiotherapists
    def load_physiotherapists(search=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            query = """
                SELECT therapist_id, first_name, last_name,
                       specialization, phone, email, joining_date
                FROM physiotherapist
                WHERE CAST(therapist_id AS TEXT) ILIKE %s
                   OR first_name ILIKE %s
                   OR last_name ILIKE %s
                   OR specialization ILIKE %s
                ORDER BY therapist_id
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

    # Select physiotherapist
    def select_physiotherapist(event):
        selected = tree.focus()

        if not selected:
            return

        therapist_id = tree.item(selected, "values")[0]
        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT first_name, last_name, specialization,
                       phone, email, joining_date
                FROM physiotherapist
                WHERE therapist_id = %s
            """, (therapist_id,))

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

    tree.bind("<<TreeviewSelect>>", select_physiotherapist)

    # Get form values
    def get_form_values():
        values = [entries[field].get().strip() for field in fields]

        if not values[0] or not values[1] or not values[3]:
            messagebox.showwarning(
                "Missing Details",
                "First name, last name and phone are required."
            )
            return None

        values[2] = values[2] or None
        values[4] = values[4] or None
        values[5] = values[5] or None

        return values

    # Add
    def add_physiotherapist():
        values = get_form_values()

        if values is None:
            return

        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO physiotherapist
                    (first_name, last_name, specialization,
                     phone, email, joining_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, values)
                cur.close()

            messagebox.showinfo(
                "Success", "Physiotherapist added successfully."
            )
            clear_form()
            load_physiotherapists(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            if conn:
                conn.close()

    # Update
    def update_physiotherapist():
        selected = tree.focus()

        if not selected:
            messagebox.showwarning(
                "Select Physiotherapist",
                "Please select a physiotherapist first."
            )
            return

        values = get_form_values()

        if values is None:
            return

        therapist_id = tree.item(selected, "values")[0]
        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE physiotherapist
                    SET first_name=%s, last_name=%s,
                        specialization=%s, phone=%s,
                        email=%s, joining_date=%s
                    WHERE therapist_id=%s
                """, values + [therapist_id])
                cur.close()

            messagebox.showinfo(
                "Success", "Physiotherapist updated successfully."
            )
            clear_form()
            load_physiotherapists(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            if conn:
                conn.close()

    # Delete
    def delete_physiotherapist():
        selected = tree.focus()

        if not selected:
            messagebox.showwarning(
                "Select Physiotherapist",
                "Please select a physiotherapist first."
            )
            return

        therapist_id = tree.item(selected, "values")[0]

        if not messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this physiotherapist?"
        ):
            return

        conn = None

        try:
            conn = get_connection()

            with conn:
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM physiotherapist WHERE therapist_id=%s",
                    (therapist_id,)
                )
                cur.close()

            messagebox.showinfo(
                "Success", "Physiotherapist deleted successfully."
            )
            clear_form()
            load_physiotherapists(search_entry.get().strip())

        except Exception as e:
            messagebox.showerror(
                "Error",
                "Could not delete physiotherapist. They may have related records.\n\n"
                + str(e)
            )

        finally:
            if conn:
                conn.close()

    # Search and refresh
    def search_physiotherapists():
        load_physiotherapists(search_entry.get().strip())

    def refresh_physiotherapists():
        search_entry.delete(0, tk.END)
        load_physiotherapists()

    # Buttons
    button_frame = tk.Frame(content, bg="#f4f6f9")
    button_frame.pack(pady=8)

    tk.Button(
        button_frame, text="Add Physiotherapist",
        command=add_physiotherapist, width=17
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Update",
        command=update_physiotherapist, width=12
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Delete",
        command=delete_physiotherapist, width=12
    ).pack(side="left", padx=5)

    tk.Button(
        button_frame, text="Clear Form",
        command=clear_form, width=12
    ).pack(side="left", padx=5)

    tk.Button(
        search_frame, text="Search",
        command=search_physiotherapists
    ).pack(side="left")

    tk.Button(
        search_frame, text="Refresh",
        command=refresh_physiotherapists
    ).pack(side="left", padx=5)

    load_physiotherapists()
