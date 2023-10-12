from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np

class ChatboxOverlay:
    def __init__(self, device="cpu"):
        self.device = device
    _alignments = ["left", "right", "center"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "Hello"}),
                "textbox_width": ("INT", {"default": 200, "min": 1}),  # Define textbox width in pixels
                "textbox_height": ("INT", {"default": 100, "min": 1}),  # Define textbox height in pixels
                "font_size": ("INT", {"default": 16, "min": 1, "max": 256, "step": 1}),
                "font": ("STRING", {"default": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}),  # Use DejaVu Sans as the default font
                "alignment": (cls._alignments, {"default": "center"}),  # ["left", "right", "center"]
                "color": ("STRING", {"default": "#000000"}),  # Accept hex value for color
                "start_x": ("INT", {"default": 0}),  # Starting X-coordinate for the textbox
                "start_y": ("INT", {"default": 0}),  # Starting Y-coordinate for the textbox
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "draw_text_on_image"
    CATEGORY = "image/text"

    def draw_text_on_image(self, image, text, textbox_width, textbox_height, font_size, font, alignment, color, start_x, start_y):
        # Convert tensor to numpy array and then to PIL Image
        image_tensor = image
        image_np = image_tensor.cpu().numpy()  # Change from CxHxW to HxWxC for Pillow
        image = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))  # Convert float [0,1] tensor to uint8 image

        # Convert hex color to RGB tuple
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        # Load font
        loaded_font = ImageFont.truetype(font, font_size)

        # Prepare to draw on image
        draw = ImageDraw.Draw(image)

        # Calculate text dimensions
        text_width, text_height = loaded_font.getsize(text)

        # Calculate the number of lines needed for word wrapping
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            if current_line == "":
                current_line = word
            elif draw.textsize(current_line + " " + word, font=loaded_font)[0] <= textbox_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Calculate total text height for vertical centering
        total_text_height = len(lines) * text_height

        # Calculate y-coordinate for vertical centering
        y = start_y + ((textbox_height - total_text_height) // 2)

        # Draw each line of text
        for line in lines:
            # Calculate x-coordinate for horizontal centering
            x = start_x  # Start from the specified X-coordinate
            if alignment == "center":
                x += (textbox_width - draw.textsize(line, font=loaded_font)[0]) // 2
            elif alignment == "right":
                x += textbox_width - draw.textsize(line, font=loaded_font)[0]

            # Draw text on the image
            draw.text((x, y), line, fill=color_rgb, font=loaded_font)
            y += text_height

        # Convert back to Tensor if needed
        image_tensor_out = torch.tensor(np.array(image).astype(np.float32) / 255.0)  # Convert back to CxHxW
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)

        return (image_tensor_out,)

NODE_CLASS_MAPPINGS = {
    "Chatbox Overlay": ChatboxOverlay,
}
