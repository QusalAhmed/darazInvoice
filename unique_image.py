from random import randint
from PIL import Image, ImageDraw, ImageFont
import os
import shutil

def add_watermark(input_image_path, output_image_path, watermark_text):
    # Open the original image
    original = Image.open(input_image_path).convert("RGBA")

    # Make the image editable
    txt = Image.new("RGBA", original.size, (255, 255, 255, 0))

    # Load a font
    font = ImageFont.truetype("HARNGTON.TTF", original.height * 0.05)

    # Initialize ImageDraw
    draw = ImageDraw.Draw(txt)

    # Add text to image
    draw.text((original.width - original.height * 0.025 * len(watermark_text) -10, original.height * 0.9),
              watermark_text, fill=(0, 0, 0, 255), font=font)
    # draw.text((50, original.height - 80), watermark_text, fill=(0, 0, 0, 255), font=font)
    draw.text((10, 10), str(randint(100, 999)), fill=(255, 255, 255, 128), font=font)

    # Combine original image with watermark
    watermarked = Image.alpha_composite(original, txt)

    # Save the final image
    watermarked.convert("RGB").save(output_image_path, "PNG")

# Example usage
input_image = r"D:\Downloads\Product\help.png"
output_image = r"D:\Downloads\Product\help_watermarked.png"
directory = r'D:\Downloads\Business\Rabit Earphone'
watermark_directory = os.path.join(directory, 'watermarked')
watermark = "Tech Tornado"

# add_watermark(input_image, output_image, watermark)

# Delete and then create directory
if os.path.exists(watermark_directory):
    shutil.rmtree(watermark_directory)
os.mkdir(watermark_directory)
for filename in os.listdir(directory):
    if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jfif"):
        if len(filename) > 50:
            filename = filename[:50]
        input_image = os.path.join(directory, filename)
        output_image = os.path.join(directory, 'watermarked', filename)
        add_watermark(input_image, output_image, watermark)
        print(f"Watermark added to {filename}")
