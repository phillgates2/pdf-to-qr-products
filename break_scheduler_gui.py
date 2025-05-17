import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv
import fitz  # PyMuPDF
import ttkbootstrap as tb

entries = []
selected_item = None

def add_or_update_entry():
    global selected_item
    date = date_var.get()
    name = name_var.get().strip()
    btype = type_var.get().strip().capitalize()
    start = start_var.get()
    end = end_var.get()

    if not date or not name or not btype or not start or not end:
        messagebox.showwarning("Input Error", "All fields must be filled.")
        return

    if selected_item:
        i = tree.index(selected_item)
        entries[i] = (date, name, btype, start, end)
        tree.item(selected_item, values=(date, name, btype, start, end))
        selected_item = None
    else:
        entries.append((date, name, btype, start, end))
        tree.insert("", "end", values=(date, name, btype, start, end))

    clear_inputs()

def clear_inputs():
    global selected_item
    selected_item = None
    date_var.set(datetime.today().strftime("%Y-%m-%d"))
    name_var.set("")
    type_var.set("")
    start_var.set("")
    end_var.set("")

def on_row_select(event):
    global selected_item
    selected = tree.focus()
    if selected:
        selected_item = selected
        vals = tree.item(selected, 'values')
        date_var.set(vals[0])
        name_var.set(vals[1])
        type_var.set(vals[2])
        start_var.set(vals[3])
        end_var.set(vals[4])

def delete_selected():
    global selected_item
    if not selected_item:
        return
    i = tree.index(selected_item)
    del entries[i]
    tree.delete(selected_item)
    selected_item = None
    clear_inputs()

def save_to_csv():
    if not entries:
        messagebox.showinfo("No Data", "Nothing to save.")
        return
    with open("break_schedule.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Name", "Type", "Start", "End"])
        writer.writerows(entries)
    messagebox.showinfo("Saved", "Saved to break_schedule.csv")

def import_pdf():
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if not pdf_path:
        return
    seen = set()
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            lines = page.get_text().splitlines()
            current_date = None
            i = 0
            while i < len(lines):
                line = lines[i]
                if "Date:" in line:
                    try:
                        current_date = datetime.strptime(line.split("Date:")[1].strip(), "%A, %d %B %Y").date()
                    except:
                        pass
                elif "," in line and any(c.isdigit() for c in line):
                    parts = line.strip().rsplit(" ", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        hours = float(parts[1])
                        if (current_date, name) in seen:
                            i += 1
                            continue
                        seen.add((current_date, name))
                        has_lunch = False
                        if i + 1 < len(lines) and "X" in lines[i + 1]:
                            has_lunch = True
                        shift_start = datetime.strptime("08:00", "%H:%M")
                        shift_end = shift_start + timedelta(hours=hours)

                        if hours >= 4:
                            t1 = shift_start + timedelta(hours=2)
                            t1_end = t1 + timedelta(minutes=15)
                            add_entry(str(current_date), name, "Tea", t1.strftime("%H:%M"), t1_end.strftime("%H:%M"))

                        if has_lunch:
                            l_start = shift_start + timedelta(hours=4)
                            l_end = l_start + timedelta(minutes=30)
                            add_entry(str(current_date), name, "Lunch", l_start.strftime("%H:%M"), l_end.strftime("%H:%M"))

                        if hours >= 7.5 and has_lunch:
                            t2_end = shift_end - timedelta(hours=1)
                            t2_start = t2_end - timedelta(minutes=15)
                            add_entry(str(current_date), name, "Tea", t2_start.strftime("%H:%M"), t2_end.strftime("%H:%M"))
                i += 1
        doc.close()
        messagebox.showinfo("Imported", "PDF imported successfully.")
    except Exception as e:
        messagebox.showerror("Import Error", str(e))

def add_entry(date, name, btype, start, end):
    entries.append((date, name, btype, start, end))
    tree.insert("", "end", values=(date, name, btype, start, end))

# GUI setup
app = tb.Window(themename="darkly")
app.title("Break Scheduler - Full Version")

date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
name_var = tk.StringVar()
type_var = tk.StringVar()
start_var = tk.StringVar()
end_var = tk.StringVar()

frm = tb.Frame(app)
frm.pack(pady=10)

tb.Label(frm, text="Date").grid(row=0, column=0)
tb.Entry(frm, textvariable=date_var, width=15).grid(row=0, column=1)

tb.Label(frm, text="Name").grid(row=1, column=0)
tb.Entry(frm, textvariable=name_var, width=15).grid(row=1, column=1)

tb.Label(frm, text="Type").grid(row=2, column=0)
tb.Entry(frm, textvariable=type_var, width=15).grid(row=2, column=1)

tb.Label(frm, text="Start").grid(row=3, column=0)
tb.Entry(frm, textvariable=start_var, width=15).grid(row=3, column=1)

tb.Label(frm, text="End").grid(row=4, column=0)
tb.Entry(frm, textvariable=end_var, width=15).grid(row=4, column=1)

tb.Button(app, text="Add/Update", command=add_or_update_entry).pack(pady=2)
tb.Button(app, text="Delete Selected", command=delete_selected).pack(pady=2)
tb.Button(app, text="Import from PDF", command=import_pdf).pack(pady=2)
tb.Button(app, text="Save to CSV", command=save_to_csv).pack(pady=2)

tree = ttk.Treeview(app, columns=("Date", "Name", "Type", "Start", "End"), show="headings", height=10)
for col in ("Date", "Name", "Type", "Start", "End"):
    tree.heading(col, text=col)
    tree.column(col, width=100)
tree.pack(pady=10)
tree.bind("<ButtonRelease-1>", on_row_select)

app.mainloop()