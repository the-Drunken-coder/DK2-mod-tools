from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create directory if it doesn't exist
    if not os.path.exists('resources'):
        os.makedirs('resources')

    # Create images of different sizes for the icon
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        # Create a new image with a white background
        image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a rounded rectangle for the main shape
        padding = size // 8
        draw.rounded_rectangle(
            [padding, padding, size-padding, size-padding],
            fill=(200, 137, 62),  # Orange color (#CB893E)
            radius=size//8
        )
        
        # Draw "DK2" text if size is large enough
        if size >= 32:
            try:
                # Try to use Arial, fall back to default if not available
                font_size = size // 4
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                text = "DK2"
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (size - text_width) // 2
                y = (size - text_height) // 2
                draw.text((x, y), text, fill=(255, 255, 255), font=font)
            except Exception as e:
                print(f"Could not add text to {size}x{size} icon: {e}")
        
        images.append(image)
    
    # Save as ICO file
    icon_path = os.path.join('resources', 'icon.ico')
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(size, size) for size in sizes],
        append_images=images[1:]
    )
    print(f"Icon created successfully at {icon_path}")

if __name__ == "__main__":
    create_icon() 