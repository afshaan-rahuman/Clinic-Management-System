import tkinter as tk
from patients import show_patients
from physiotherapists import show_physiotherapists
from assessments import show_assessments
from treatment_plans import show_treatment_plans
from exercises import show_exercises
from therapy_sessions import show_therapy_sessions
from progress_records import show_progress_records
from payments import show_payments
from reports import show_reports

root = tk.Tk()
root.title("Clinic Management System")
root.geometry("1100x650")
root.configure(bg="#f4f6f9")

# Header
header = tk.Frame(root, bg="#243447", height=70)
header.pack(fill="x")

tk.Label(
    header,
    text="Clinic Management System",
    font=("Arial", 22, "bold"),
    fg="white",
    bg="#243447"
).pack(side="left", padx=25, pady=18)

# Main layout
main_frame = tk.Frame(root, bg="#f4f6f9")
main_frame.pack(fill="both", expand=True)

# Sidebar
sidebar = tk.Frame(main_frame, bg="#243447", width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# Content area
content = tk.Frame(main_frame, bg="#f4f6f9")
content.pack(side="right", fill="both", expand=True)


def show_dashboard():
    for widget in content.winfo_children():
        widget.destroy()

    tk.Label(
        content,
        text="Welcome to the Clinic Management System",
        font=("Arial", 20, "bold"),
        bg="#f4f6f9",
        fg="#243447"
    ).pack(pady=50)

    tk.Label(
        content,
        text="Select a module from the sidebar to get started.",
        font=("Arial", 12),
        bg="#f4f6f9",
        fg="#555555"
    ).pack()


# Navigation
modules = [
    ("Dashboard", show_dashboard),
    ("Patients", lambda: show_patients(content)),
    ("Physiotherapists", lambda: show_physiotherapists(content)),
    ("Assessments", lambda: show_assessments(content)),
    ("Treatment Plans", lambda: show_treatment_plans(content)),
    ("Exercises", lambda: show_exercises(content)),
    ("Therapy Sessions", lambda: show_therapy_sessions(content)),
    ("Progress Records", lambda: show_progress_records(content)),
    ("Payments", lambda: show_payments(content)),
    ("Reports", lambda: show_reports(content))
]

for module, command in modules:
    tk.Button(
        sidebar,
        text=module,
        font=("Arial", 11),
        bg="#243447",
        fg="white",
        activebackground="#34495e",
        activeforeground="white",
        relief="flat",
        anchor="w",
        padx=20,
        pady=10,
        command=command
    ).pack(fill="x")

show_dashboard()

root.mainloop()
