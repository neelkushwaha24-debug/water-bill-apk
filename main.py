import flet as ft
from datetime import datetime
import calendar

# --- Business Logic ---
RATE_SLABS = [
    {"rate": 9.25, "start": datetime(1980, 1, 1), "end": datetime(1996, 3, 31)},
    {"rate": 40, "start": datetime(1996, 4, 1), "end": datetime(2011, 3, 31)},
    {"rate": 80, "start": datetime(2011, 4, 1), "end": datetime(2016, 6, 30)},
    {"rate": 100, "start": datetime(2016, 7, 1), "end": datetime(2025, 3, 31)},
    {"rate": 150, "start": datetime(2025, 4, 1), "end": datetime(2050, 12, 31)}
]

def format_date(d):
    return d.strftime("%d/%m/%Y")

def get_overlap_months(slab_start, slab_end, user_start, user_end):
    overlap_start = max(slab_start, user_start)
    overlap_end = min(slab_end, user_end)
    if overlap_start > overlap_end:
        return 0
    months = (overlap_end.year - overlap_start.year) * 12
    months -= overlap_start.month
    months += overlap_end.month
    return months + 1

def calculate_amount_for_date_range(req_start, req_end):
    if req_start > req_end:
        return 0
    amt = 0
    for slab in RATE_SLABS:
        m = get_overlap_months(slab["start"], slab["end"], req_start, req_end)
        if m > 0:
            amt += m * slab["rate"]
    return amt

def main(page: ft.Page):
    page.title = "वाटर बिल कैलकुलेटर"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 450
    page.window_height = 800
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#f3f4f6"  # Light gray background like standard mobile apps
    
    # App Bar (Header)
    header = ft.Container(
        content=ft.Row([
            ft.Text("वाटर बिल (नगर पालिका परिषद)", size=20, weight=ft.FontWeight.BOLD, color="white")
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#2563eb",  # Primary blue
        padding=ft.padding.only(top=40, bottom=20),
        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="black26")
    )
    
    # Calculate Default End Date
    today = datetime.today()
    if today.month == 1:
        prev_month_end = datetime(today.year - 1, 12, 31)
    else:
        last_day = calendar.monthrange(today.year, today.month - 1)[1]
        prev_month_end = datetime(today.year, today.month - 1, last_day)

    # Inputs
    start_date_input = ft.TextField(
        label="बिल प्रारंभ तिथि (Start Date):",
        value="2011-01-01",
        keyboard_type=ft.KeyboardType.DATETIME,
        border_color="#d1d5db",
        focused_border_color="#2563eb",
        border_radius=8,
        expand=True,
    )
    
    end_date_input = ft.TextField(
        label="बिल समाप्ति तिथि (End Date):",
        value=prev_month_end.strftime("%Y-%m-%d"),
        keyboard_type=ft.KeyboardType.DATETIME,
        border_color="#d1d5db",
        focused_border_color="#2563eb",
        border_radius=8,
        expand=True,
    )
    
    advance_payment_input = ft.TextField(
        label="अग्रिम भुगतान (Advance Payment ₹):",
        value="300",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#d1d5db",
        focused_border_color="#2563eb",
        border_radius=8,
        hint_text="उदा: 150, 300, 450",
    )
    
    lok_adalat_switch = ft.Switch(
        label="लोक अदालत स्लैब नियम लागू करें (चालू वर्ष की पेनल्टी छोड़कर)",
        value=False,
        active_color="#2563eb",
    )

    # Summary Text Fields
    val_bill_amount = ft.Text("₹0.00", weight=ft.FontWeight.BOLD, size=16)
    val_penalty_label = ft.Text("पेनल्टी (10%)", size=14, color="black54")
    val_penalty_amount = ft.Text("₹0.00", weight=ft.FontWeight.BOLD, size=16, color="white")
    
    discount_container = ft.Container(
        content=ft.Row([
            ft.Text("Lok Adalat Discount (छूट)", size=14, color="#155724"),
            ft.Container(expand=True),
            ft.Text("- ₹0.00", weight=ft.FontWeight.BOLD, size=16, color="#155724")
        ]),
        bgcolor="#d4edda",
        padding=10,
        border_radius=4,
        visible=False
    )
    
    val_advance_amount = ft.Text("₹0.00", weight=ft.FontWeight.BOLD, size=16, color="white")
    val_final_charge = ft.Text("₹0.00", weight=ft.FontWeight.BOLD, size=20)
    
    # Remark Box
    remark_text = ft.Text("", size=14)
    remark_box = ft.Container(
        content=remark_text,
        bgcolor="#e9ecef",
        border=ft.border.all(2, "#28a745"),
        border_radius=6,
        padding=15,
        visible=False,
        margin=ft.margin.only(bottom=15)
    )

    # Slabs Table
    slabs_datatable = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Rate(₹)", size=12)),
            ft.DataColumn(ft.Text("Start", size=12)),
            ft.DataColumn(ft.Text("End", size=12)),
            ft.DataColumn(ft.Text("Mths", size=12)),
            ft.DataColumn(ft.Text("Amt(₹)", size=12)),
        ],
        rows=[],
        column_spacing=10,
        data_row_min_height=40,
        heading_row_height=40,
        horizontal_margin=10,
    )

    def show_snackbar(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def on_calculate(e):
        try:
            user_start = datetime.strptime(start_date_input.value, "%Y-%m-%d")
            user_end = datetime.strptime(end_date_input.value, "%Y-%m-%d")
        except ValueError:
            show_snackbar("कृपया सही तिथि (YYYY-MM-DD) दर्ज करें।")
            return
            
        try:
            advance = float(advance_payment_input.value) if advance_payment_input.value else 0
        except ValueError:
            show_snackbar("अग्रिम भुगतान संख्या में होना चाहिए।")
            return

        if advance > 0 and advance % 150 != 0:
            show_snackbar("अग्रिम भुगतान केवल 150 के गुणांक में ही दर्ज करें।")
            return
            
        if user_start > user_end:
            show_snackbar("प्रारंभ तिथि समाप्ति तिथि से पहले की होनी चाहिए!")
            return

        is_lok_adalat = lok_adalat_switch.value
        
        # Populate slabs table
        slabs_datatable.rows.clear()
        total_bill = 0
        last_month_rate = 0
        
        for slab in RATE_SLABS:
            months = get_overlap_months(slab["start"], slab["end"], user_start, user_end)
            amount = 0
            if months > 0:
                amount = months * slab["rate"]
                total_bill += amount
                
            if slab["start"] <= user_end <= slab["end"]:
                last_month_rate = slab["rate"]
                
            slabs_datatable.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"₹{slab['rate']}", size=12)),
                    ft.DataCell(ft.Text(format_date(slab["start"]), size=12)),
                    ft.DataCell(ft.Text(format_date(slab["end"]), size=12)),
                    ft.DataCell(ft.Text(str(months if months > 0 else 0), size=12)),
                    ft.DataCell(ft.Text(f"₹{amount}", size=12)),
                ])
            )

        # Arrears and Current FY calculations
        today_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        curr_year = today_date.year
        curr_month = today_date.month
        
        curr_fy_start_year = curr_year if curr_month >= 4 else curr_year - 1
        curr_fy_start = datetime(curr_fy_start_year, 4, 1) # month 4 is April
        end_of_arrears = datetime(curr_fy_start_year, 3, 31)
        
        arrears_bill = calculate_amount_for_date_range(user_start, min(user_end, end_of_arrears))
        current_fy_bill = calculate_amount_for_date_range(max(user_start, curr_fy_start), user_end)
        
        penaltyable_arrears = arrears_bill
        penaltyable_current_fy = current_fy_bill
        
        # Grace Due Date (15th of next month)
        m = user_end.month + 1
        y = user_end.year
        if m > 12:
            m = 1
            y += 1
        grace_due_date = datetime(y, m, 15)
        
        is_grace_period = today_date <= grace_due_date
        
        if is_grace_period:
            if current_fy_bill >= last_month_rate and total_bill > 0:
                penaltyable_current_fy -= last_month_rate
            elif arrears_bill >= last_month_rate and total_bill > 0:
                penaltyable_arrears -= last_month_rate
                
        standard_arrears_penalty = penaltyable_arrears * 0.10
        current_fy_penalty = penaltyable_current_fy * 0.10
        final_arrears_penalty = standard_arrears_penalty
        
        discount_amt = 0
        
        base_label_text = "Penalty 10%"
        if is_grace_period:
            base_label_text += f" (Grace till {format_date(grace_due_date)})"
        else:
            base_label_text += " (After Due Date)"
            
        if is_lok_adalat:
            if total_bill <= 10000:
                final_arrears_penalty = 0
                discount_amt = standard_arrears_penalty
                val_penalty_label.value = base_label_text + " - Arrears 100% Waived"
            elif 10000 < total_bill <= 50000:
                final_arrears_penalty = standard_arrears_penalty * 0.25
                discount_amt = standard_arrears_penalty * 0.75
                val_penalty_label.value = base_label_text + " - Arrears 75% Waived"
            elif total_bill > 50000:
                final_arrears_penalty = standard_arrears_penalty * 0.50
                discount_amt = standard_arrears_penalty * 0.50
                val_penalty_label.value = base_label_text + " - Arrears 50% Waived"
        else:
            final_arrears_penalty = standard_arrears_penalty
            discount_amt = 0
            val_penalty_label.value = base_label_text

        if discount_amt > 0:
            discount_container.visible = True
            discount_container.content.controls[2].value = f"- ₹{discount_amt:.2f}"
        else:
            discount_container.visible = False
            
        final_penalty = final_arrears_penalty + current_fy_penalty
        total_charge = total_bill + final_penalty + advance
        
        # Update Summary
        val_bill_amount.value = f"₹{total_bill:.2f}"
        val_penalty_amount.value = f"₹{final_penalty:.2f}"
        val_advance_amount.value = f"₹{advance:.2f}"
        val_final_charge.value = f"₹{total_charge:.2f}"
        
        # Remark Box
        if total_charge > 0 or total_bill > 0:
            remark_box.visible = True
            
            # Simple workaround since textspans can be tricky with formatting in some flet versions
            text_lines = [
                f"📌 रिमार्क: दिनांक {format_date(user_start)} से {format_date(user_end)} तक की कुल देय राशि ₹{total_charge:.2f} है।"
            ]
            if discount_amt > 0:
                text_lines.append(f"🎉 (लोक अदालत के अंतर्गत ₹{discount_amt:.2f} की पेनल्टी छूट दी गई है।)")
                
            remark_text.value = "\n\n".join(text_lines)
            
            if discount_amt > 0:
                remark_text.color = "green800"
            else:
                remark_text.color = "red800"
                
        else:
            remark_box.visible = False
            
        page.update()

    lok_adalat_switch.on_change = on_calculate

    def create_card(title, content):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="#1f2937"),
                    ft.Divider(color="#e5e7eb"),
                    content
                ]),
                padding=20
            ),
            elevation=2,
            margin=ft.margin.only(bottom=15),
        )

    # Input Section Content
    input_content = ft.Column([
        ft.Row([start_date_input, end_date_input], spacing=15),
        ft.Container(height=10),
        advance_payment_input,
        ft.Container(height=10),
        ft.Container(
            content=lok_adalat_switch,
            bgcolor="#fff3cd",
            border=ft.border.all(1, "#ffeeba"),
            border_radius=4,
            padding=10
        ),
        ft.Container(height=15),
        ft.Row([
            ft.ElevatedButton(
                "बिल कैलकुलेट करें", 
                on_click=on_calculate,
                style=ft.ButtonStyle(
                    bgcolor="#2563eb",
                    color="white",
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.all(15)
                ),
                expand=True
            ),
        ]),
        ft.Container(height=5),
        ft.Row([
            ft.ElevatedButton(
                "🖨️ प्रिंट बिल",
                on_click=lambda _: show_snackbar("Flet App में Print सुविधा के लिए PDF जेनरेट करना होगा। (Coming Soon)"),
                style=ft.ButtonStyle(
                    bgcolor="#28a745",
                    color="white",
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.all(15)
                ),
                expand=True
            )
        ])
    ])

    # Summary Section Content
    def summary_row(label, value_control, bg_color):
        return ft.Container(
            content=ft.Row([
                ft.Text(label, size=14, color="black87" if bg_color not in ["#ff8b94", "#4facfe"] else "white"),
                ft.Container(expand=True),
                value_control
            ]),
            bgcolor=bg_color,
            padding=10,
            border_radius=4
        )

    summary_content = ft.Column([
        summary_row("Bill Amount (Arrears + Current Year)", val_bill_amount, "#a8e6cf"),
        ft.Container(height=2),
        summary_row("Penalty 10%", val_penalty_amount, "#ff8b94"),
        ft.Container(height=2),
        discount_container,
        ft.Container(height=2),
        summary_row("Advance Payment", val_advance_amount, "#4facfe"),
        ft.Container(height=2),
        summary_row("Total Charge", val_final_charge, "#e0e0e0"),
    ], spacing=0)

    # Build Page Layout
    page.scroll = "auto"
    page.add(
        header,
        ft.Container(
            content=ft.Column([
                create_card("बिल विवरण दर्ज करें", input_content),
                remark_box,
                create_card("बिल समरी", summary_content),
                create_card("दर विवरण (Slabs)", slabs_datatable),
                ft.Container(height=20) # Bottom padding
            ], spacing=0),
            padding=15
        )
    )
    
    # Run initial calculation
    on_calculate(None)

if __name__ == "__main__":
    ft.app(target=main)
