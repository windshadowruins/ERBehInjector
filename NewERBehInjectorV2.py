import re
import os
import shutil
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from lxml import etree
from copy import deepcopy
import traceback

def getNode(Nparent, attribName, attribValue):
    """
    Returns the first child of Nparent whose attribute `attribName`
    equals `attribValue`. Returns None if not found.
    """
    for child in Nparent:
        if child.attrib.get(attribName) == attribValue:
            return child
    return None

def process_file(directory, hkx_numbers, state_machine_parent, names):
    file_path = os.path.join(directory, "c0000.xml")
    template_path = os.path.join(directory, "template.xml")

    # Create a backup before modifying
    backup_path = file_path + ".bak"
    shutil.copy(file_path, backup_path)
    print(f"Backup created: {backup_path}")

    parser = etree.XMLParser(remove_blank_text=False, remove_comments=False)
    tree = etree.parse(file_path, parser)
    root = tree.getroot()

    # Helper: Compute next available userData value
    def get_next_user_data(root):
        user_data_elements = root.xpath("//field[@name='userData']/integer")
        max_val = 0
        for elem in user_data_elements:
            try:
                val = int(elem.attrib['value'])
                if val > max_val:
                    max_val = val
            except Exception:
                pass
        return max_val + 1
    next_user_data = get_next_user_data(root)

    # --- Update animationNames array ---
    animation_field = root.xpath("//field[@name='animationNames']/array[@elementtypeid='type7']")
    if not animation_field:
        messagebox.showerror("Error", "Could not locate animationNames array in the XML.")
        return
    animation_array = animation_field[0]
    current_count = int(animation_array.attrib['count'])
    new_count = current_count + len(hkx_numbers)
    animation_array.attrib['count'] = str(new_count)
    last_animation_entry = animation_array.xpath("string[last()]")
    for hkx_number in hkx_numbers:
        base_a_number = hkx_number.split("_")[0]
        full_hkx_path = f"..\\..\\..\\..\\Model\\chr\\c0000\\hkx\\{base_a_number}\\{hkx_number}.hkx"
        new_entry = etree.Element("string", value=full_hkx_path)
        if last_animation_entry:
            last_animation_entry[0].addnext(new_entry)
        else:
            animation_array.append(new_entry)
        new_entry.tail = "\n          "
        print(f"Added new HKX entry: {full_hkx_path}")
    animation_array.tail = "\n      "

    # --- Update eventNames array ---
    event_names_field = root.xpath("//field[@name='eventNames']/array[@elementtypeid='type7']")
    if not event_names_field:
        messagebox.showerror("Error", "Could not locate eventNames array in the XML.")
        return
    event_names_array = event_names_field[0]
    event_names_count = int(event_names_array.attrib.get('count', 0))
    event_names_array.attrib['count'] = str(event_names_count + len(names))
    last_event_entry = event_names_array.xpath("string[last()]")
    for name in names:
        new_name = name if name.startswith("W_") else f"W_{name}"
        event_name = etree.Element("string", value=new_name)
        if last_event_entry:
            last_event_entry[0].addnext(event_name)
        else:
            event_names_array.append(event_name)
        event_name.tail = "\n      "
        last_event_entry = event_name
        print(f"Added new event name: {new_name}")
    event_names_array.tail = "\n      "

    # Save original event count to use for transition info
    next_event_id = event_names_count

    # --- Ensure <hktagfile/> exists ---
    hktagfile = root.xpath("//hktagfile")
    if hktagfile:
        print("<hktagfile/> already exists. Skipping addition.")
    else:
        root.append(etree.Element("hktagfile"))
        print("Added missing <hktagfile/> at the end.")

    # ---- Process new state machine entries from template.xml ----
    # Calculate next available object ID by scanning all objects in the XML.
    existing_ids = [int(obj.attrib['id'][6:]) for obj in root if obj.tag == 'object' and obj.attrib.get('id', '').startswith("object")]
    next_obj_id = max(existing_ids) + 1 if existing_ids else 1

    new_state_ids = []  # to store new StateInfo object IDs

    for hkx_number, name in zip(hkx_numbers, names):
        # Use one event ID per new entry
        current_event_id = next_event_id
        next_event_id += 1

        print(f"Processing: {name} with HKX {hkx_number}")
        try:
            template_tree = etree.parse(template_path, parser)
            template_root = template_tree.getroot()
            new_state_info = deepcopy(template_root.xpath("//object[@typeid='type117']")[0])
            new_cmsg = deepcopy(template_root.xpath("//object[@typeid='type299']")[0])
            new_clip_gen = deepcopy(template_root.xpath("//object[@typeid='type320']")[0])
        except IndexError:
            messagebox.showerror("Error", "Template is missing required objects.")
            return

        # Set StateInfo fields
        new_state_info.attrib['id'] = f'object{next_obj_id}'
        new_state_info.xpath(".//field[@name='name']/string")[0].attrib['value'] = name
        new_state_info.xpath(".//field[@name='stateId']/integer")[0].attrib['value'] = str(next_obj_id)
        # Also update the generator pointer in StateInfo to point to new CMSG
        state_gen = new_state_info.xpath(".//field[@name='generator']/pointer")
        if state_gen:
            state_gen[0].set('id', f'object{next_obj_id + 1}')

        # Set CMSG fields
        new_cmsg.attrib['id'] = f'object{next_obj_id + 1}'
        new_cmsg.xpath(".//field[@name='name']/string")[0].attrib['value'] = f'{name}_CMSG'
        new_cmsg.xpath(".//field[@name='animId']/integer")[0].attrib['value'] = hkx_number.split("_")[1]
        new_cmsg.xpath(".//field[@name='userData']/integer")[0].attrib['value'] = str(next_obj_id + 100000)
        # In the generators array, replace the pointer element with a new pointer (to avoid immutable attribute error)
        generatorsField = new_cmsg.xpath(".//field[@name='generators']/array")
        if generatorsField and len(generatorsField[0]) > 0:
            new_pointer = etree.Element("pointer")
            new_pointer.set("id", f'object{next_obj_id + 2}')
            generatorsField[0].remove(generatorsField[0][0])
            generatorsField[0].insert(0, new_pointer)
            new_pointer.tail = "\n"  # Force newline before the closing tag of the array
            # --- ADDED SNIPPET: Remove any extra pointer with id "_OBJECTID2" ---
            for ptr in generatorsField[0].xpath("pointer[@id='_OBJECTID2']"):
                generatorsField[0].remove(ptr)
            # --- END ADDED SNIPPET ---

        # Set ClipGenerator fields
        new_clip_gen.attrib['id'] = f'object{next_obj_id + 2}'
        new_clip_name = hkx_number + "_hkx_AutoSet_00"
        new_clip_gen.xpath(".//field[@name='name']/string")[0].attrib['value'] = new_clip_name
        new_clip_gen.xpath(".//field[@name='animationName']/string")[0].attrib['value'] = hkx_number

        # Create a new TransitionInfo object from the template (assumed 4th object)
        new_transition_info = deepcopy(template_root[3])
        # Set the eventId field
        transition_event_node = getNode(new_transition_info, 'name', 'eventId')
        if transition_event_node is not None:
            transition_event_node.attrib['value'] = str(current_event_id)
        else:
            messagebox.showerror("Error", "Could not find 'eventId' field in TransitionInfo template.")
            return
        # Set the toStateId field
        transition_to_state_node = getNode(new_transition_info, 'name', 'toStateId')
        if transition_to_state_node is not None:
            transition_to_state_node.attrib['value'] = str(next_obj_id)
        else:
            messagebox.showerror("Error", "Could not find 'toStateId' field in TransitionInfo template.")
            return

        # --- ADDITION: Add a new entrance to wildcardTransitions ---
        parent_sm = root.xpath(f"//object[.//field[@name='name']/string[@value='{state_machine_parent}']]")
        if not parent_sm:
            messagebox.showerror("Error", f"Could not locate parent state machine '{state_machine_parent}' in the XML.")
            return
        parent_sm = parent_sm[0]
        wildcard_field = parent_sm.xpath(".//field[@name='wildcardTransitions']")
        if not wildcard_field:
            messagebox.showerror("Error", "Could not locate wildcardTransitions in the parent state machine.")
            return
        # In the original code, we then get the object via getObject (here we use xpath)
        wildcard_pointer_id = wildcard_field[0][0].attrib['id']
        wildcard_obj = root.xpath(f"//object[@id='{wildcard_pointer_id}']")
        if not wildcard_obj:
            messagebox.showerror("Error", "Could not locate wildcardTransitions object.")
            return
        wildcard_obj = wildcard_obj[0]
        fieldTransitions = wildcard_obj.xpath(".//field[@name='transitions']/array")
        if not fieldTransitions:
            messagebox.showerror("Error", "Could not locate transitions array in wildcardTransitions object.")
            return
        fieldTransitions[0].attrib['count'] = str(int(fieldTransitions[0].attrib['count']) + 1)
        fieldTransitions[0].append(new_transition_info)
        # --- END ADDITION ---

        # --- ADDITION: Add StateInfo to StateMachine ---
        states = parent_sm.xpath(".//field[@name='states']")
        if states:
            states[0][0].attrib['count'] = str(int(states[0][0].attrib['count']) + 1)
            states[0][0].append(etree.Element('pointer', {'id': f'object{next_obj_id}'}))
        # --- END ADDITION ---

        ###################################################
        # ADDED SNIPPET: Fix up new entry's <field name="transition"> and <field name="condition">
        # 1) For the transition field, ensure it has a nested <pointer id="object222" />
        transition_field = new_transition_info.xpath("./field[@name='transition']")
        if transition_field:
            transition_field[0].attrib.pop('pointer_id', None)
            for child in list(transition_field[0]):
                transition_field[0].remove(child)
            pointer_elem = etree.Element('pointer')
            pointer_elem.set('id', 'object222')
            pointer_elem.tail = "\n"
            transition_field[0].append(pointer_elem)
        # 2) For the condition field, ensure it has a nested <pointer id="object0" />
        condition_field = new_transition_info.xpath("./field[@name='condition']")
        if not condition_field:
            condition_field = etree.SubElement(new_transition_info, 'field')
            condition_field.set('name', 'condition')
            pointer_elem = etree.Element('pointer')
            pointer_elem.set('id', 'object0')
            pointer_elem.tail = "\n"
            condition_field.append(pointer_elem)
        else:
            condition_field[0].attrib.pop('pointer_id', None)
            for child in list(condition_field[0]):
                condition_field[0].remove(child)
            pointer_elem = etree.Element('pointer')
            pointer_elem.set('id', 'object0')
            pointer_elem.tail = "\n"
            condition_field[0].append(pointer_elem)
        # 3) Move eventId/toStateId out of <field value="X"> into a child <integer value="X">
        def fix_integer_field(field_name):
            fld = new_transition_info.xpath(f"./field[@name='{field_name}']")
            if fld:
                val = fld[0].attrib.pop('value', None)
                if val is not None:
                    int_child = fld[0].find('integer')
                    if int_child is None:
                        int_child = etree.Element('integer')
                        fld[0].append(int_child)
                    int_child.set('value', val)
        fix_integer_field("eventId")
        fix_integer_field("toStateId")
        ###################################################
        # END ADDED SNIPPET
        ###################################################

        # --- ADDITION: Append new objects StateInfo, CMSG and ClipGenerator to the root ---
        root.append(new_state_info)
        root.append(new_cmsg)
        root.append(new_clip_gen)
        print(f"Injected new objects with IDs: {next_obj_id}, {next_obj_id+1}, {next_obj_id+2}")
        next_obj_id += 3
        # --- END ADDITION ---

    # ---- Register new state entries in parent state machine (optional if needed) ----
    parent_sm = root.xpath(f"//object[.//field[@name='name']/string[@value='{state_machine_parent}']]")
    if not parent_sm:
        messagebox.showerror("Error", f"Could not locate parent state machine '{state_machine_parent}' in the XML.")
        return
    parent_sm = parent_sm[0]
    states_field = parent_sm.xpath(".//field[@name='states']/array")
    if not states_field:
        messagebox.showerror("Error", "Could not locate states array in the parent state machine.")
        return
    states_array = states_field[0]
    current_state_count = int(states_array.attrib['count'])
    new_state_count = current_state_count + len(new_state_ids)
    states_array.attrib['count'] = str(new_state_count)
    for state_id in new_state_ids:
        new_pointer = etree.Element("pointer")
        new_pointer.set("id", state_id)
        states_array.append(new_pointer)
        new_pointer.tail = "\n          "
        print(f"Registered new state pointer: {state_id}")
    states_array.tail = "\n      "

    # Convert tree to string and apply formatting fixes
    xml_string = etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")
    xml_string = xml_string.replace("<?xml version='1.0' encoding='utf-8'?>", "<?xml version=\"1.0\" encoding=\"utf-8\"?>")
    xml_string = re.sub(r'<fields count="0"\s*/>', r'<fields count="0"></fields>', xml_string)
    xml_string = xml_string.replace("/>", " />")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml_string)
        print(f"Updated file saved as: {file_path}")
        messagebox.showinfo("Success", f"Registered {len(hkx_numbers)} new animations and event names.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")

def open_ui():
    def on_submit():
        hkx_input = hkx_text_box.get("1.0", tk.END).strip()
        names_input = names_text_box.get("1.0", tk.END).strip()
        state_machine_parent = state_machine_combo.get()
        hkx_numbers = [line.strip() for line in hkx_input.split("\n") if line.strip()]
        names = [line.strip() for line in names_input.split("\n") if line.strip()]
        if not hkx_numbers:
            messagebox.showerror("Error", "No HKX numbers provided.")
            return
        if not names:
            messagebox.showerror("Error", "No Names provided.")
            return
        directory = os.getcwd()
        process_file(directory, hkx_numbers, state_machine_parent, names)

    root = tk.Tk()
    root.title("Animation Names Editor")
    tk.Label(root, text="Select State Machine Parent:", font=("Arial", 12)).pack(pady=5)
    state_machine_combo = ttk.Combobox(root, values=["GuardDamage_SM", "Attack_SM", "AttackRight_SM", "Bonfire_SM", "Throw_SM", "MagicFireRight", "Guard_SM", "Evasion_SM", "Event_SM", "SwordArts_SM", "EventGesture", "Gesture_SM", "TalkEvent_SM"], font=("Arial", 12), state="readonly")
    state_machine_combo.pack(pady=5)
    state_machine_combo.current(0)
    tk.Label(root, text="Enter HKX numbers (one per line):", font=("Arial", 12)).pack(pady=5)
    hkx_text_box = tk.scrolledtext.ScrolledText(root, width=50, height=10, font=("Courier", 10))
    hkx_text_box.pack(pady=5)
    tk.Label(root, text="Enter Names (one per line):", font=("Arial", 12)).pack(pady=5)
    names_text_box = tk.scrolledtext.ScrolledText(root, width=50, height=10, font=("Courier", 10))
    names_text_box.pack(pady=5)
    submit_button = tk.Button(root, text="Submit", command=on_submit, font=("Arial", 12), bg="green", fg="white")
    submit_button.pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    open_ui()
