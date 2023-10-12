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
                "max_font_size": ("INT", {"default": 256, "min": 1, "max": 256, "step": 1}),  # Maximum font size to try
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

    def draw_text_on_image(self, image, text, textbox_width, textbox_height, max_font_size, font, alignment, color, start_x, start_y):
        # Convert tensor to numpy array and then to PIL Image
        image_tensor = image
        image_np = image_tensor.cpu().numpy()  # Change from CxHxW to HxWxC for Pillow
        image = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))  # Convert float [0,1] tensor to uint8 image

        # Convert hex color to RGB tuple
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        # Start with the maximum font size
        font_size = max_font_size

        while font_size >= 1:
            # Load font
            loaded_font = ImageFont.truetype(font, font_size)

            # Prepare to draw on image
            draw = ImageDraw.Draw(image)

            # Calculate text dimensions of the wrapped text
            wrapped_text = self.wrap_text(text, loaded_font, textbox_width)
            text_width, text_height = draw.textsize(wrapped_text, font=loaded_font)

            # Check if text fits within the textbox dimensions
            if text_width <= textbox_width and text_height <= textbox_height:
                # Calculate total text height for vertical centering
                lines = wrapped_text.split('\n')
                total_text_height = len(lines) * loaded_font.getsize("M")[1]  # Use font ascent for line height

                # Calculate y-coordinate for vertical centering, considering font ascent
                y = start_y + ((textbox_height - total_text_height) // 2) + loaded_font.getsize("M")[1] // 2

                # Draw the wrapped text on the image
                x = start_x  # Start from the specified X-coordinate
                for line in lines:
                    line_width, line_height = draw.textsize(line, font=loaded_font)
                    if alignment == "center":
                        x = start_x + (textbox_width - line_width) // 2
                    elif alignment == "right":
                        x = start_x + (textbox_width - line_width)
                    draw.text((x, y), line, fill=color_rgb, font=loaded_font)
                    y += loaded_font.getsize("M")[1]  # Use font ascent for line height

                # Convert back to Tensor if needed
                image_tensor_out = torch.tensor(np.array(image).astype(np.float32) / 255.0)  # Convert back to CxHxW
                image_tensor_out = torch.unsqueeze(image_tensor_out, 0)

                return (image_tensor_out,)

            # Reduce font size and try again
            font_size -= 1

        # If the text cannot fit even at the smallest font size, return the original image
        image_tensor_out = torch.tensor(np.array(image).astype(np.float32) / 255.0)  # Convert back to CxHxW
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,)

    def wrap_text(self, text, font, max_width):
        lines = []
        for line in text.split('\n'):
            words = line.split()
            wrapped_line = words[0]
            for word in words[1:]:
                test_line = wrapped_line + ' ' + word
                test_size = font.getsize(test_line)
                if test_size[0] <= max_width:
                    wrapped_line = test_line
                else:
                    lines.append(wrapped_line)
                    wrapped_line = word
            lines.append(wrapped_line)
        return '\n'.join(lines)

NODE_CLASS_MAPPINGS = {
    "Chatbox Overlay": ChatboxOverlay,
}
