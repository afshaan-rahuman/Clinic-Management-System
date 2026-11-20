import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_payments(content):
    for widget in content.winfo_children():
        widget.destroy()

    selected_id = None
    plans = {}

    frame = tk.Frame(content, padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Payments", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 12))

    search_frame = tk.Frame(frame)
    search_frame.pack(fill="x", pady=5)

    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=35).pack(side="left", padx=(0, 8))

    form = tk.LabelFrame(frame, text="Payment Details", padx=10, pady=10)
    form.pack(fill="x", pady=10)

    tk.Label(form, text="Payment Date").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    date_entry = tk.Entry(form, width=25)
    date_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(form, text="Treatment Plan").grid(row=0, column=2, sticky="w", padx=5, pady=5)
    plan_var = tk.StringVar()
    plan_combo = ttk.Combobox(form, textvariable=plan_var, width=38, state="readonly")
    plan_combo.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(form, text="Amount Paid").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    amount_entry = tk.Entry(form, width=25)
    amount_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(form, text="Payment Method").grid(row=1, column=2, sticky="w", padx=5, pady=5)
    method_var = tk.StringVar()
    method_combo = ttk.Combobox(
        form, textvariable=method_var, width=35,
        values=["Cash", "Card", "UPI", "Bank Transfer"], state="readonly"
    )
    method_combo.grid(row=1, column=3, padx=5, pady=5)

    table_frame = tk.Frame(frame)
    table_frame.pack(fill="both", expand=True, pady=10)

    columns = ("ID", "Date", "Patient", "Plan ID", "Amount Paid", "Payment Method")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=130)

    tree.column("Patient", width=180)
    tree.column("Payment Method", width=160)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def load_plans():
        nonlocal plans
        plans = {}

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tp.plan_id, p.first_name, p.last_name
            FROM treatment_plan tp
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            ORDER BY tp.plan_id
        """)

        options = []
        for plan_id, first, last in cur.fetchall():
            label = f"{plan_id} - {first} {last}"
            plans[label] = plan_id
            options.append(label)

        plan_combo["values"] = options
        cur.close()
        conn.close()

    def load_payments(search=""):
        for item in tree.get_children():
            tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT pay.payment_id, pay.payment_date,
                   p.first_name || ' ' || p.last_name,
                   tp.plan_id, pay.amount_paid, pay.payment_method
            FROM payment pay
            JOIN treatment_plan tp ON pay.plan_id = tp.plan_id
            JOIN assessment a ON tp.assessment_id = a.assessment_id
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE CAST(pay.payment_id AS TEXT) ILIKE %s
               OR CAST(tp.plan_id AS TEXT) ILIKE %s
               OR p.first_name ILIKE %s
               OR p.last_name ILIKE %s
            ORDER BY pay.payment_id
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))

        for row in cur.fetchall():
            tree.insert("", "end", values=row)

        cur.close()
        conn.close()

    def clear_fields():
        nonlocal selected_id
        selected_id = None
        date_entry.delete(0, tk.END)
        amount_entry.delete(0, tk.END)
        plan_combo.set("")
        method_combo.set("")

    def select_payment(event):
        nonlocal selected_id
        selected = tree.focus()
        if not selected:
            return

        values = tree.item(selected, "values")
        selected_id = values[0]

        date_entry.delete(0, tk.END)
        date_entry.insert(0, str(values[1]))

        amount_entry.delete(0, tk.END)
        amount_entry.insert(0, str(values[4]))

        method_combo.set(values[5])

        for label, plan_id in plans.items():
            if plan_id == int(values[3]):
                plan_combo.set(label)
                break

    def add_payment():
        try:
            date = date_entry.get().strip()
            amount = float(amount_entry.get())
            method = method_var.get()
            plan_id = plans.get(plan_var.get())

            if not date or plan_id is None or not method:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            if amount <= 0:
                messagebox.showerror("Error", "Amount paid must be greater than zero.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO payment (amount_paid, payment_date, payment_method, plan_id)
                VALUES (%s, %s, %s, %s)
            """, (amount, date, method, plan_id))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Payment added successfully.")
            clear_fields()
            load_payments(search_var.get())

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_payment():
        if selected_id is None:
            messagebox.showerror("Error", "Please select a payment to update.")
            return

        try:
            date = date_entry.get().strip()
            amount = float(amount_entry.get())
            method = method_var.get()
            plan_id = plans.get(plan_var.get())

            if not date or plan_id is None or not method:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            if amount <= 0:
                messagebox.showerror("Error", "Amount paid must be greater than zero.")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE payment
                SET amount_paid = %s, payment_date = %s,
                    payment_method = %s, plan_id = %s
                WHERE payment_id = %s
            """, (amount, date, method, plan_id, selected_id))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Payment updated successfully.")
            clear_fields()
            load_payments(search_var.get())

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_payment():
        if selected_id is None:
            messagebox.showerror("Error", "Please select a payment to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete this payment?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM payment WHERE payment_id = %s", (selected_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Success", "Payment deleted successfully.")
            clear_fields()
            load_payments(search_var.get())

        except Exception as e:
            messagebox.showerror("Error", str(e))

    tree.bind("<<TreeviewSelect>>", select_payment)

    tk.Button(search_frame, text="Search", command=lambda: load_payments(search_var.get())).pack(side="left", padx=3)
    tk.Button(search_frame, text="Show All", command=lambda: (search_var.set(""), load_payments())).pack(side="left", padx=3)

    button_frame = tk.Frame(frame)
    button_frame.pack(fill="x", pady=5)

    tk.Button(button_frame, text="Add", width=12, command=add_payment).pack(side="left", padx=5)
    tk.Button(button_frame, text="Update", width=12, command=update_payment).pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete", width=12, command=delete_payment).pack(side="left", padx=5)
    tk.Button(button_frame, text="Clear", width=12, command=clear_fields).pack(side="left", padx=5)

    load_plans()
    load_payments()
