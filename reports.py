import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection


def show_reports(content):
    for widget in content.winfo_children():
        widget.destroy()

    frame = tk.Frame(content, padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Reports", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 15))

    report_frame = tk.Frame(frame)
    report_frame.pack(fill="x", pady=5)

    tk.Label(report_frame, text="Select Report:", font=("Arial", 10)).pack(side="left", padx=5)

    report_var = tk.StringVar()
    report_combo = ttk.Combobox(
        report_frame,
        textvariable=report_var,
        width=38,
        state="readonly",
        values=[
            "Patient Treatment Overview",
            "Payment Summary by Plan",
            "Outstanding Balances",
            "Therapy Sessions by Physiotherapist",
            "Patient Progress Report"
        ]
    )
    report_combo.pack(side="left", padx=5)

    table_frame = tk.Frame(frame)
    table_frame.pack(fill="both", expand=True, pady=15)

    tree = ttk.Treeview(table_frame, show="headings")

    vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

    tree.configure(
        yscrollcommand=vertical_scroll.set,
        xscrollcommand=horizontal_scroll.set
    )

    tree.grid(row=0, column=0, sticky="nsew")
    vertical_scroll.grid(row=0, column=1, sticky="ns")
    horizontal_scroll.grid(row=1, column=0, sticky="ew")

    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    def run_report():
        selected = report_var.get()

        if not selected:
            messagebox.showerror("Error", "Please select a report.")
            return

        queries = {
            "Patient Treatment Overview": """
                SELECT
                    patient_id,
                    first_name || ' ' || last_name AS patient,
                    assessment_date,
                    condition_description,
                    plan_id,
                    plan_status,
                    total_fee
                FROM patient_treatment_overview
                ORDER BY patient_id
            """,

            "Payment Summary by Plan": """
                SELECT
                    plan_id,
                    first_name || ' ' || last_name AS patient,
                    total_fee,
                    number_of_payments AS payment_count,
                    total_paid
                FROM payment_summary_by_plan
                ORDER BY plan_id
            """,

            "Outstanding Balances": """
                SELECT
                    plan_id,
                    first_name || ' ' || last_name AS patient,
                    total_fee,
                    total_paid,
                    outstanding_balance AS balance
                FROM outstanding_balances
                ORDER BY balance DESC
            """,

            "Therapy Sessions by Physiotherapist": """
                SELECT
                    therapist_id,
                    first_name || ' ' || last_name AS physiotherapist,
                    total_sessions
                FROM sessions_by_physiotherapist
                ORDER BY total_sessions DESC
            """,

            "Patient Progress Report": """
                SELECT
                    patient_id,
                    patient_name AS patient,
                    session_id,
                    session_date,
                    recorded_date,
                    pain_score,
                    mobility_notes,
                    progress_notes
                FROM patient_progress_report
                ORDER BY patient_id, session_date
            """
        }

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute(queries[selected])

            rows = cur.fetchall()
            columns = [description[0] for description in cur.description]

            for item in tree.get_children():
                tree.delete(item)

            tree["columns"] = columns

            for col in columns:
                tree.heading(col, text=col.replace("_", " ").title())

                width = 150
                minwidth = 100

                if selected == "Patient Progress Report":
                    if col == "mobility_notes":
                        width = 300
                        minwidth = 200
                    elif col == "progress_notes":
                        width = 350
                        minwidth = 200

                tree.column(
                    col,
                    width=width,
                    minwidth=minwidth,
                    stretch=False
                )

            for row in rows:
                tree.insert("", "end", values=row)

            cur.close()
            conn.close()

            if not rows:
                messagebox.showinfo("Report", "No records found for this report.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(
        report_frame,
        text="Generate Report",
        command=run_report,
        width=16
    ).pack(side="left", padx=10)

    tk.Label(
        frame,
        text="Select a report and click Generate Report to view the results.",
        font=("Arial", 9),
        fg="gray"
    ).pack(anchor="w")