import os
import re

def fix_po_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        # Only process msgid and msgstr lines
        if line.startswith('msgid "') or line.startswith('msgstr "'):
            # Check if this is a simple line (not multiline)
            if line.strip().endswith('"') and line.count('"') >= 2:
                # Extract prefix
                if line.startswith('msgid "'):
                    prefix = 'msgid "'
                else:
                    prefix = 'msgstr "'
                
                # Get the part after prefix
                rest = line[len(prefix):]
                
                # Get content without the closing quote
                if rest.rstrip().endswith('"'):
                    content = rest.rstrip()[:-1]
                    
                    # Only escape if there are unescaped quotes
                    if '"' in content and '\\"' not in content:
                        # Simple replacement: escape all quotes
                        content = content.replace('"', '\\"')
                    elif '"' in content:
                        # More complex: need to handle mixed escaped/unescaped
                        # First, temporarily replace already escaped quotes
                        content = content.replace('\\"', '\x00ESCAPED_QUOTE\x00')
                        # Then escape remaining quotes
                        content = content.replace('"', '\\"')
                        # Restore the originally escaped quotes
                        content = content.replace('\x00ESCAPED_QUOTE\x00', '\\"')
                    
                    # Reconstruct line with proper ending
                    line = prefix + content + '"\n'
        
        fixed_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed: {filepath}")

# Fix all ar_001.po files
scale_addons_path = r'c:\Users\ODOO\Documents\ODOO 19\odoo\scale_addons'

for root, dirs, files in os.walk(scale_addons_path):
    for file in files:
        if file == 'ar_001.po':
            filepath = os.path.join(root, file)
            try:
                fix_po_file(filepath)
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")

print("\nAll PO files fixed!")
