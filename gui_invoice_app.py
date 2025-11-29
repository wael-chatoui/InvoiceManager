import tkinter as tk
from tkinter import ttk, messagebox
from invoice_generator import create_invoice
import os
from datetime import datetime
from PIL import Image, ImageTk

# Default from address - edit this with your company information
DEFAULT_FROM_ADDRESS = "Wael\n9 rue Olympe de Gouges,\n92600 Asnières-sur-Seine, France"

class InvoiceApp:
    def __init__(self, master):
        self.master = master
        master.title("Invoice Generator")
        master.geometry("900x750")

        self.items = []
        self.total_amount = 0.0
        # Check for logo file (try both .png and .jpg)
        if os.path.exists("favicon.png"):
            self.logo_path = "favicon.png"
        else:
            self.logo_path = None

        self.i18n = {
            "en": {
                "title": "Invoice Generator",
                "add_item": "Add Item",
                "invoice_items": "Invoice Items",
                "description": "Description:",
                "quantity": "Quantity:",
                "unit_price": "Unit Price ($):",
                "add_button": "Add Item",
                "remove_button": "Remove Selected",
                "tree_desc": "Description",
                "tree_qty": "Quantity",
                "tree_price": "Unit Price ($)",
                "tree_total": "Total ($)",
                "total_label": "Total: ${:.2f}",
                "generate_button": "Generate Invoice",
                "clear_button": "Clear All",
                "mode_invoice": "Invoice",
                "mode_estimate": "Estimate",
                "lang_en": "English",
                "lang_fr": "French",
                "currency_symbol": "$",
                "generate_success": "Invoice successfully generated to {}",
                "generate_fail": "Failed to generate invoice: {}",
                "no_items": "No items added to the invoice.",
                "clear_confirm": "All items cleared.",
                "error_input": "Input Error",
                "error_desc_empty": "Description cannot be empty.",
                "error_qty_invalid": "Quantity must be a valid positive integer.",
                "error_price_invalid": "Unit Price must be a valid number.",
                "doc_title_label": "Document Title:",
                "from_address_label": "From Address:",
                "to_address_label": "To Address:",
                "no_selection": "Please select an item to remove.",
                "item_removed": "Item removed successfully.",
                "addresses_section": "Address Information",
                "from_label_pdf": "From:",
                "to_label_pdf": "To:",
            },
            "fr": {
                "title": "Générateur de Factures",
                "add_item": "Ajouter un Article",
                "invoice_items": "Articles de la Facture",
                "description": "Description :",
                "quantity": "Quantité :",
                "unit_price": "Prix Unitaire (€) :",
                "add_button": "Ajouter",
                "remove_button": "Supprimer la Sélection",
                "tree_desc": "Description",
                "tree_qty": "Quantité",
                "tree_price": "Prix Unitaire (€)",
                "tree_total": "Total (€)",
                "total_label": "Total : {:.2f} €",
                "generate_button": "Générer la Facture",
                "clear_button": "Tout Effacer",
                "mode_invoice": "Facture",
                "mode_estimate": "Devis",
                "lang_en": "Anglais",
                "lang_fr": "Français",
                "currency_symbol": "€",
                "generate_success": "Facture générée avec succès dans {}",
                "generate_fail": "Échec de la génération de la facture : {}",
                "no_items": "Aucun article ajouté à la facture.",
                "clear_confirm": "Tous les articles ont été effacés.",
                "error_input": "Erreur de Saisie",
                "error_desc_empty": "La description ne peut pas être vide.",
                "error_qty_invalid": "La quantité doit être un entier positif valide.",
                "error_price_invalid": "Le prix unitaire doit être un nombre valide.",
                "doc_title_label": "Titre du Document :",
                "from_address_label": "Adresse Émetteur :",
                "to_address_label": "Adresse Destinataire :",
                "no_selection": "Veuillez sélectionner un article à supprimer.",
                "item_removed": "Article supprimé avec succès.",
                "addresses_section": "Informations d'Adresse",
                "from_label_pdf": "De :",
                "to_label_pdf": "À :",
            }
        }
        self.current_lang = "en"
        self.widgets = {}

        self._create_main_layout()
        self._create_ui_for_lang("en")
        self._create_ui_for_lang("fr")
        self._switch_language() # Set initial text

    def _create_main_layout(self):
        # Logo
        if self.logo_path:
            logo_frame = ttk.Frame(self.master)
            logo_frame.pack(pady=5)
            img = Image.open(self.logo_path)
            img.thumbnail((150, 40))
            self.logo_img = ImageTk.PhotoImage(img)
            self.widgets['logo_label'] = ttk.Label(logo_frame, image=self.logo_img)
            self.widgets['logo_label'].pack()

        # Mode
        self.mode_frame = ttk.Frame(self.master)
        self.mode_frame.pack(pady=5)
        self.mode_var = tk.StringVar(value="invoice")
        self.widgets['mode_invoice_rb'] = ttk.Radiobutton(self.mode_frame, variable=self.mode_var, value="invoice")
        self.widgets['mode_invoice_rb'].pack(side="left", padx=5)
        self.widgets['mode_estimate_rb'] = ttk.Radiobutton(self.mode_frame, variable=self.mode_var, value="estimate")
        self.widgets['mode_estimate_rb'].pack(side="left", padx=5)

        # Address section
        self.address_frame = ttk.LabelFrame(self.master)
        self.address_frame.pack(padx=10, pady=5, fill="x")

        # Document Title
        self.widgets['doc_title_label'] = ttk.Label(self.address_frame)
        self.widgets['doc_title_label'].grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.doc_title_var = tk.StringVar()
        ttk.Entry(self.address_frame, textvariable=self.doc_title_var, width=60).grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=3)

        # From Address
        self.widgets['from_label'] = ttk.Label(self.address_frame)
        self.widgets['from_label'].grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.from_address_var = tk.StringVar(value=DEFAULT_FROM_ADDRESS)
        from_text = tk.Text(self.address_frame, height=3, width=40)
        from_text.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        from_text.insert("1.0", self.from_address_var.get())
        self.from_address_text = from_text

        # To Address
        self.widgets['to_label'] = ttk.Label(self.address_frame)
        self.widgets['to_label'].grid(row=1, column=2, padx=5, pady=5, sticky="nw")
        self.to_address_var = tk.StringVar(value="Customer Name\nCustomer Street 456\n67890 Othercity, Country")
        to_text = tk.Text(self.address_frame, height=3, width=40)
        to_text.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        to_text.insert("1.0", self.to_address_var.get())
        self.to_address_text = to_text

        self.address_frame.grid_columnconfigure(1, weight=1)
        self.address_frame.grid_columnconfigure(3, weight=1)

        # Tabs for languages
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(padx=10, pady=5, expand=True, fill="both")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._switch_language())

        self.en_frame = ttk.Frame(self.notebook)
        self.fr_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.en_frame, text=self.i18n["en"]["lang_en"])
        self.notebook.add(self.fr_frame, text=self.i18n["fr"]["lang_fr"])

    def _create_ui_for_lang(self, lang):
        parent = self.en_frame if lang == "en" else self.fr_frame

        # Frames
        self.widgets[f'input_frame_{lang}'] = ttk.LabelFrame(parent)
        self.widgets[f'input_frame_{lang}'].pack(padx=10, pady=5, fill="x")

        self.widgets[f'items_frame_{lang}'] = ttk.LabelFrame(parent)
        self.widgets[f'items_frame_{lang}'].pack(padx=10, pady=5, fill="both", expand=True)

        self.widgets[f'total_frame_{lang}'] = ttk.Frame(parent)
        self.widgets[f'total_frame_{lang}'].pack(padx=10, pady=5, fill="x")

        self.widgets[f'buttons_frame_{lang}'] = ttk.Frame(parent)
        self.widgets[f'buttons_frame_{lang}'].pack(padx=10, pady=5, fill="x")

        self._create_input_widgets(self.widgets[f'input_frame_{lang}'], lang)
        self._create_items_treeview(self.widgets[f'items_frame_{lang}'], lang)
        self._create_total_display(self.widgets[f'total_frame_{lang}'], lang)
        self._create_buttons(self.widgets[f'buttons_frame_{lang}'], lang)


    def _create_input_widgets(self, parent, lang):
        self.widgets[f'desc_label_{lang}'] = ttk.Label(parent)
        self.widgets[f'desc_label_{lang}'].grid(row=0, column=0, padx=5, pady=5, sticky="w")

        if not hasattr(self, 'description_vars'):
            self.description_vars = {}
        self.description_vars[lang] = tk.StringVar()
        ttk.Entry(parent, textvariable=self.description_vars[lang], width=40).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.widgets[f'qty_label_{lang}'] = ttk.Label(parent)
        self.widgets[f'qty_label_{lang}'].grid(row=0, column=2, padx=5, pady=5, sticky="w")

        if not hasattr(self, 'quantity_vars'):
            self.quantity_vars = {}
        self.quantity_vars[lang] = tk.StringVar(value="1")
        ttk.Entry(parent, textvariable=self.quantity_vars[lang], width=10).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.widgets[f'price_label_{lang}'] = ttk.Label(parent)
        self.widgets[f'price_label_{lang}'].grid(row=0, column=4, padx=5, pady=5, sticky="w")

        if not hasattr(self, 'price_vars'):
            self.price_vars = {}
        self.price_vars[lang] = tk.StringVar()
        ttk.Entry(parent, textvariable=self.price_vars[lang], width=15).grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        self.widgets[f'add_button_{lang}'] = ttk.Button(parent, command=self._add_item)
        self.widgets[f'add_button_{lang}'].grid(row=0, column=6, padx=5, pady=5)
        parent.grid_columnconfigure(1, weight=1)

    def _create_items_treeview(self, parent, lang):
        self.tree = ttk.Treeview(parent, columns=("Description", "Quantity", "Unit Price", "Total"), show="headings")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _create_total_display(self, parent, lang):
        self.widgets[f'total_label_{lang}'] = ttk.Label(parent, font=("Helvetica", 14, "bold"))
        self.widgets[f'total_label_{lang}'].pack(side="right", padx=5, pady=5)

    def _create_buttons(self, parent, lang):
        self.widgets[f'generate_button_{lang}'] = ttk.Button(parent, command=self._generate_invoice)
        self.widgets[f'generate_button_{lang}'].pack(side="left", padx=5)
        self.widgets[f'remove_button_{lang}'] = ttk.Button(parent, command=self._remove_selected_item)
        self.widgets[f'remove_button_{lang}'].pack(side="left", padx=5)
        self.widgets[f'clear_button_{lang}'] = ttk.Button(parent, command=self._clear_all)
        self.widgets[f'clear_button_{lang}'].pack(side="right", padx=5)

    def _switch_language(self):
        selected_tab = self.notebook.index(self.notebook.select())
        self.current_lang = "fr" if selected_tab == 1 else "en"

        lang_dict = self.i18n[self.current_lang]
        self.master.title(lang_dict["title"])

        self.notebook.tab(0, text=self.i18n["en"]["lang_en"])
        self.notebook.tab(1, text=self.i18n["fr"]["lang_fr"])

        for lang in ["en", "fr"]:
             parent = self.en_frame if lang == "en" else self.fr_frame
             ld = self.i18n[lang]
             self.widgets[f'input_frame_{lang}'].config(text=ld["add_item"])
             self.widgets[f'items_frame_{lang}'].config(text=ld["invoice_items"])
             self.widgets[f'desc_label_{lang}'].config(text=ld["description"])
             self.widgets[f'qty_label_{lang}'].config(text=ld["quantity"])
             self.widgets[f'price_label_{lang}'].config(text=ld["unit_price"])
             self.widgets[f'add_button_{lang}'].config(text=ld["add_button"])
             self.widgets[f'generate_button_{lang}'].config(text=ld["generate_button"])
             self.widgets[f'remove_button_{lang}'].config(text=ld["remove_button"])
             self.widgets[f'clear_button_{lang}'].config(text=ld["clear_button"])

        self.address_frame.config(text=lang_dict["addresses_section"])
        self.widgets['doc_title_label'].config(text=lang_dict["doc_title_label"])
        self.widgets['from_label'].config(text=lang_dict["from_address_label"])
        self.widgets['to_label'].config(text=lang_dict["to_address_label"])

        self.widgets['mode_invoice_rb'].config(text=lang_dict["mode_invoice"])
        self.widgets['mode_estimate_rb'].config(text=lang_dict["mode_estimate"])

        self.tree.heading("Description", text=lang_dict["tree_desc"])
        self.tree.heading("Quantity", text=lang_dict["tree_qty"])
        self.tree.heading("Unit Price", text=lang_dict["tree_price"])
        self.tree.heading("Total", text=lang_dict["tree_total"])
        self._update_total_display()
        self._redraw_items()

    def _add_item(self):
        lang_dict = self.i18n[self.current_lang]
        description = self.description_vars[self.current_lang].get().strip()
        quantity_str = self.quantity_vars[self.current_lang].get().strip()
        price_str = self.price_vars[self.current_lang].get().strip().replace(",",".") # Allow comma as decimal sep

        if not description:
            messagebox.showerror(lang_dict["error_input"], lang_dict["error_desc_empty"])
            return

        try:
            quantity = int(quantity_str)
            if quantity <= 0: raise ValueError()
        except ValueError:
            messagebox.showerror(lang_dict["error_input"], lang_dict["error_qty_invalid"])
            return

        try:
            price = float(price_str)
            if price < 0: raise ValueError()
        except ValueError:
            messagebox.showerror(lang_dict["error_input"], lang_dict["error_price_invalid"])
            return

        self.items.append({"description": description, "quantity": quantity, "price": price})
        self.total_amount += quantity * price

        self._redraw_items()
        self._update_total_display()

        self.description_vars[self.current_lang].set("")
        self.quantity_vars[self.current_lang].set("1")
        self.price_vars[self.current_lang].set("")

    def _redraw_items(self):
        lang_dict = self.i18n[self.current_lang]
        self.tree.delete(*self.tree.get_children())
        for item in self.items:
            item_total = item['quantity'] * item['price']
            price_str = f"{item['price']:.2f}".replace(".", ",") if self.current_lang == 'fr' else f"{item['price']:.2f}"
            total_str = f"{item_total:.2f}".replace(".", ",") if self.current_lang == 'fr' else f"{item_total:.2f}"
            self.tree.insert("", "end", values=(item['description'], item['quantity'], price_str, total_str))

    def _update_total_display(self):
        for lang in ["en", "fr"]:
            lang_dict = self.i18n[lang]
            total_str = lang_dict["total_label"].format(self.total_amount)
            self.widgets[f'total_label_{lang}'].config(text=total_str)


    def _generate_invoice(self):
        lang_dict = self.i18n[self.current_lang]
        if not self.items:
            messagebox.showwarning(lang_dict["generate_button"], lang_dict["no_items"])
            return

        invoice_number = datetime.now().strftime("%Y%m%d-%H%M%S")
        invoice_date = datetime.now().strftime("%Y-%m-%d")
        date_yymmdd = datetime.now().strftime("%y%m%d")
        mode = self.mode_var.get().capitalize()

        # Get addresses from text widgets
        from_address = self.from_address_text.get("1.0", "end-1c").strip()
        to_address = self.to_address_text.get("1.0", "end-1c").strip()
        doc_title = self.doc_title_var.get().strip()

        invoice_data = {
            "invoice_number": invoice_number,
            "date": invoice_date,
            "from_address": from_address,
            "to_address": to_address,
            "items": self.items,
        }

        output_dir = "invoices"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create filename: {title}_{YYMMDD}.pdf or fallback to mode_invoicenumber.pdf
        if doc_title:
            # Sanitize title for filename (remove invalid characters)
            safe_title = "".join(c for c in doc_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            file_path = os.path.join(output_dir, f"{safe_title}_{date_yymmdd}.pdf")
        else:
            file_path = os.path.join(output_dir, f"{mode.lower()}_{invoice_number}.pdf")

        headers = {
            'description': lang_dict['tree_desc'],
            'quantity': lang_dict['tree_qty'],
            'unit_price': lang_dict['tree_price'],
            'total': lang_dict['tree_total']
        }

        labels = {
            'from': lang_dict['from_label_pdf'],
            'to': lang_dict['to_label_pdf']
        }

        try:
            create_invoice(invoice_data, file_path,
                           mode=lang_dict[f"mode_{self.mode_var.get()}"],
                           currency_symbol=lang_dict["currency_symbol"],
                           logo_path=self.logo_path,
                           headers=headers,
                           labels=labels)
            messagebox.showinfo(lang_dict["generate_button"], lang_dict["generate_success"].format(file_path))
        except Exception as e:
            messagebox.showerror("Error", lang_dict["generate_fail"].format(e))

    def _remove_selected_item(self):
        lang_dict = self.i18n[self.current_lang]
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(lang_dict["remove_button"], lang_dict["no_selection"])
            return

        # Get the index of the selected item
        item_id = selected[0]
        item_index = self.tree.index(item_id)

        # Remove from items list and recalculate total
        removed_item = self.items.pop(item_index)
        self.total_amount -= removed_item['quantity'] * removed_item['price']

        # Redraw and update
        self._redraw_items()
        self._update_total_display()
        messagebox.showinfo(lang_dict["remove_button"], lang_dict["item_removed"])

    def _clear_all(self):
        lang_dict = self.i18n[self.current_lang]
        self.items = []
        self.total_amount = 0.0
        self.tree.delete(*self.tree.get_children())
        self._update_total_display()
        messagebox.showinfo(lang_dict["clear_button"], lang_dict["clear_confirm"])


if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()

