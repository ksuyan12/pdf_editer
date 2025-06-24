import argparse
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO


def merge_pdfs(output_path, inputs):
    merger = PdfMerger()
    for pdf in inputs:
        merger.append(pdf)
    with open(output_path, 'wb') as f:
        merger.write(f)


def split_pdf(input_path, output_prefix, start=None, end=None):
    reader = PdfReader(input_path)
    pages = reader.pages[start:end]
    for idx, page in enumerate(pages, start=start or 0):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = f"{output_prefix}_page_{idx + 1}.pdf"
        with open(out_path, 'wb') as f:
            writer.write(f)


def rotate_pages(input_path, output_path, angle):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)


def remove_pages(input_path, output_path, pages):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        if idx not in pages:
            writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)


def add_text(input_path, output_path, text, x, y, page_num):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(x, y, text)
    can.save()
    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    overlay_page = overlay_pdf.pages[0]

    for idx, page in enumerate(reader.pages):
        if idx == page_num:
            page.merge_page(overlay_page)
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)


def apply_edits(input_path, output_path, edits):
    """Apply multiple text edits described by a list of dictionaries.

    Each dictionary must contain ``page`` (0-index), ``text``, ``x`` and ``y``
    coordinates in PDF points.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()

    edit_map = {}
    for e in edits:
        page = int(e.get('page', 0))
        edit_map.setdefault(page, []).append(e)

    for idx, page in enumerate(reader.pages):
        if idx in edit_map:
            packet = BytesIO()
            can = canvas.Canvas(
                packet,
                pagesize=(float(page.mediabox.width), float(page.mediabox.height)),
            )
            for e in edit_map[idx]:
                can.drawString(float(e.get('x', 0)), float(e.get('y', 0)), e.get('text', ''))
            can.save()
            packet.seek(0)
            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)
        writer.add_page(page)

    with open(output_path, 'wb') as f:
        writer.write(f)


def apply_watermark(input_path, watermark_path, output_path):
    watermark = PdfReader(watermark_path).pages[0]
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)
    with open(output_path, 'wb') as f:
        writer.write(f)



def main():
    parser = argparse.ArgumentParser(description="Advanced PDF editor")
    subparsers = parser.add_subparsers(dest='command', required=True)

    merge_cmd = subparsers.add_parser('merge', help='Merge PDF files')
    merge_cmd.add_argument('output', help='Output PDF file')
    merge_cmd.add_argument('inputs', nargs='+', help='Input PDF files')

    split_cmd = subparsers.add_parser('split', help='Split PDF file')
    split_cmd.add_argument('input', help='Input PDF file')
    split_cmd.add_argument('output_prefix', help='Prefix for output files')
    split_cmd.add_argument('--start', type=int, default=None, help='Start page (0-index)')
    split_cmd.add_argument('--end', type=int, default=None, help='End page (exclusive, 0-index)')

    rotate_cmd = subparsers.add_parser('rotate', help='Rotate all pages')
    rotate_cmd.add_argument('input', help='Input PDF file')
    rotate_cmd.add_argument('output', help='Output PDF file')
    rotate_cmd.add_argument('--angle', type=int, default=90, help='Rotation angle')

    remove_cmd = subparsers.add_parser('remove', help='Remove pages by index')
    remove_cmd.add_argument('input', help='Input PDF file')
    remove_cmd.add_argument('output', help='Output PDF file')
    remove_cmd.add_argument('pages', nargs='+', type=int, help='Page indices to remove (0-index)')

    text_cmd = subparsers.add_parser('add-text', help='Add text to a page')
    text_cmd.add_argument('input', help='Input PDF file')
    text_cmd.add_argument('output', help='Output PDF file')
    text_cmd.add_argument('text', help='Text to add')
    text_cmd.add_argument('--x', type=float, default=100, help='X coordinate')
    text_cmd.add_argument('--y', type=float, default=750, help='Y coordinate')
    text_cmd.add_argument('--page', type=int, default=0, help='Page number (0-index)')

    wm_cmd = subparsers.add_parser('watermark', help='Apply watermark PDF')
    wm_cmd.add_argument('input', help='Input PDF file')
    wm_cmd.add_argument('watermark', help='Watermark PDF file (single page)')
    wm_cmd.add_argument('output', help='Output PDF file')

    args = parser.parse_args()

    if args.command == 'merge':
        merge_pdfs(args.output, args.inputs)
    elif args.command == 'split':
        split_pdf(args.input, args.output_prefix, args.start, args.end)
    elif args.command == 'rotate':
        rotate_pages(args.input, args.output, args.angle)
    elif args.command == 'remove':
        remove_pages(args.input, args.output, args.pages)
    elif args.command == 'add-text':
        add_text(args.input, args.output, args.text, args.x, args.y, args.page)
    elif args.command == 'watermark':
        apply_watermark(args.input, args.watermark, args.output)


if __name__ == "__main__":
    main()
