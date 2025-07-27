import fitz # PyMuPDF
import json
import os
from collections import Counter

def extract_outline(pdf_path):
    """
    Extracts the title and a hierarchical outline (H1, H2, H3) from a PDF document.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        dict: A dictionary containing the document title and its outline.
              Format: {"title": "Document Title", "outline": [{"level": "H1", "text": "Heading Text", "page": 1}]}
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return {"title": "", "outline": []}

    # --- Pass 1: Global Font Analysis ---
    # Collect all text spans with their properties to analyze font usage across the document.
    font_properties_counts = Counter()
    all_spans_with_props = []

    for page_num, page in enumerate(doc):
        # Extract text blocks in dictionary format
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for b in blocks:
            if b['type'] == 0: # Check if it's a text block
                for l in b['lines']:
                    for s in l['spans']:
                        text = s['text'].strip()
                        if text: # Only consider non-empty text
                            size = round(s['size'], 2) # Round to handle floating point variations in font sizes
                            is_bold = bool(s['flags'] & 2) # Check if the font is bold (flag 2 indicates bold)
                            font_properties_counts[(size, is_bold)] += 1
                            all_spans_with_props.append({
                                'text': text,
                                'size': size,
                                'is_bold': is_bold,
                                'page': page_num, # Changed to 0-based page number for output
                                'x0': round(s['bbox'][0], 2),
                                'y0': round(s['bbox'][1], 2),
                                'x1': round(s['bbox'][2], 2),
                                'y1': round(s['bbox'][3], 2),
                                'page_width': round(page.rect.width, 2),
                                'page_height': round(page.rect.height, 2)
                            })
    
    # Handle cases where no text is found in the document
    if not font_properties_counts:
        doc.close()
        return {"title": "", "outline": []}

    # Filter out very small fonts (likely headers, footers, page numbers, or noise)
    # A minimum font size of 8pt is a common heuristic for readable text.
    filtered_font_counts = {k: v for k, v in font_properties_counts.items() if k[0] >= 8}
    
    if not filtered_font_counts:
        doc.close()
        return {"title": "", "outline": []}

    # Determine the most common font property (size, is_bold) for body text.
    # We exclude the absolute largest font size from this consideration initially,
    # as it's likely a title or major heading, not body text.
    largest_font_size_overall = max(k[0] for k in filtered_font_counts.keys())
    
    potential_body_fonts = {
        (size, is_bold): count
        for (size, is_bold), count in filtered_font_counts.items()
        if size < largest_font_size_overall # Exclude the very largest font
    }
    
    # Fallback if all fonts are large or only one font exists
    if not potential_body_fonts:
        potential_body_fonts = filtered_font_counts

    body_text_props = max(potential_body_fonts, key=potential_body_fonts.get)
    
    # Identify candidate heading properties (larger than body text or bolded body text)
    candidate_heading_props_set = set()
    for (size, is_bold), count in filtered_font_counts.items():
        # A font is a candidate heading if:
        # 1. It's strictly larger than the body font size.
        # 2. It's the same size as body font but bold, AND the body font itself is not bold.
        # 3. It's the absolute largest font size found in the document (strong title/H1 candidate).
        if size > body_text_props[0] or \
           (size == body_text_props[0] and is_bold and not body_text_props[1]) or \
           (size == largest_font_size_overall):
            candidate_heading_props_set.add((size, is_bold))
    
    # Sort candidate heading properties: largest size first, then bold first (True comes before False)
    # This ensures a consistent hierarchy (e.g., larger bold text before smaller bold text).
    unique_heading_props = sorted(list(candidate_heading_props_set), key=lambda x: (-x[0], not x[1]))

    # Dynamic mapping of font properties to levels (H1, H2, H3)
    # The document title is explicitly set to empty as per desired output.
    props_to_level = {}
    h_levels = ["H1", "H2", "H3"]
    assigned_h_count = 0

    # Assign H1, H2, H3 to the top 3 distinct heading properties found
    for props in unique_heading_props:
        # Removed the 'pass' statement for largest_font_size_overall
        # This allows the largest font to be assigned an H-level if it's one of the top candidates.
        
        if assigned_h_count < len(h_levels):
            if props not in props_to_level: # Ensure we don't re-assign if already mapped
                props_to_level[props] = h_levels[assigned_h_count]
                assigned_h_count += 1
        else:
            break # Only need H1, H2, H3 levels

    # --- Pass 2: Extract Title and Headings ---
    document_title = "" # Explicitly set title to empty string as per desired output
    extracted_outline = []
    
    for span_props in all_spans_with_props:
        text = span_props['text']
        size = span_props['size']
        is_bold = span_props['is_bold']
        page_num = span_props['page']
        x0, y0 = span_props['x0'], span_props['y0']
        x1, y1 = span_props['x1'], span_props['y1']
        page_width, page_height = span_props['page_width'], span_props['page_height']

        current_props = (size, is_bold)

        # Heuristics to filter out non-heading text:
        # 1. Skip very short or very long lines (likely not headings).
        if len(text.strip()) < 3 or len(text.strip()) > 150:
            continue
        
        # 2. Skip lines that are too close to page top/bottom (likely headers/footers, page numbers).
        #    Top 5% and bottom 5% of the page height are typically reserved for headers/footers.
        if y0 < page_height * 0.05 or y0 > page_height * 0.95:
            continue
        
        # 3. Skip lines that look like list items or captions (simple string-based heuristic).
        #    Also, skip sentences ending with a period if they are long and not all uppercase.
        if text.strip().startswith(('1.', '2.', '3.', '4.', '5.', 'a.', 'b.', 'c.', '-', '*')) or \
           (text.strip().endswith('.') and len(text.split()) > 5 and not text.strip().isupper()):
            continue
        
        # Removed the specific title detection block to ensure document_title remains empty
        # and allows the largest text to be classified as a heading.
        
        # Heading detection based on the dynamically determined font properties
        level = props_to_level.get(current_props)
        
        if level:
            # Prevent adding duplicate headings if the same heading text appears consecutively
            # or if it's the exact same heading on the same page (e.g., from overlapping text elements).
            if not extracted_outline or \
               (extracted_outline[-1]['text'] != text.strip() or \
                extracted_outline[-1]['level'] != level or \
                extracted_outline[-1]['page'] != page_num):
                
                extracted_outline.append({"level": level, "text": text.strip(), "page": page_num})

    doc.close()
    
    return {"title": document_title, "outline": extracted_outline}

# Main execution logic for local environment
if __name__ == "__main__":
    # Changed input_dir and output_dir for local execution
    input_dir = "input"  # Use "input" for a subdirectory in the current working directory
    output_dir = "output" # Use "output" for a subdirectory in the current working directory

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process each PDF file in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            # Construct the output JSON filename (e.g., document.pdf -> document.json)
            output_filename = filename.replace(".pdf", ".json")
            output_path = os.path.join(output_dir, output_filename)

            print(f"Processing {pdf_path}...")
            try:
                # Extract the outline
                outline_data = extract_outline(pdf_path)
                # Save the extracted data to a JSON file
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(outline_data, f, indent=2, ensure_ascii=False)
                print(f"Successfully processed {filename}. Output saved to {output_path}")
            except Exception as e:
                # Log any errors during processing
                print(f"Error processing {filename}: {e}")

