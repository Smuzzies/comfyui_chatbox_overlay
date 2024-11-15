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
                "textbox_width": ("INT", {"default": 200, "min": 1}),
                "textbox_height": ("INT", {"default": 100, "min": 1}),
                "max_font_size": ("INT", {"default": 256, "min": 1, "max": 256, "step": 1}),
                "font": ("STRING", {"default": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}),
                "alignment": (cls._alignments, {"default": "center"}),
                "color": ("STRING", {"default": "#000000"}),
                "start_x": ("INT", {"default": 0}),
                "start_y": ("INT", {"default": 0}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "draw_text_on_image"
    CATEGORY = "image/text"

    def draw_text_on_image(self, image, text, textbox_width, textbox_height, max_font_size, font, alignment, color, start_x, start_y):
        image_tensor = image
        image_np = image_tensor.cpu().numpy()
        image = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        font_size = max_font_size
        while font_size >= 1:
            loaded_font = ImageFont.truetype(font, font_size)
            draw = ImageDraw.Draw(image)
            wrapped_text = self.wrap_text(text, loaded_font, textbox_width)
            bbox = draw.textbbox((0, 0), wrapped_text, font=loaded_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if text_width <= textbox_width and text_height <= textbox_height:
                lines = wrapped_text.split('\n')
                bbox = draw.textbbox((0, 0), "M", font=loaded_font)
                line_height = bbox[3] - bbox[1]
                total_text_height = len(lines) * line_height
                y = start_y + ((textbox_height - total_text_height) // 2) + line_height // 2
                x = start_x
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=loaded_font)
                    line_width = bbox[2] - bbox[0]
                    if alignment == "center":
                        x = start_x + (textbox_width - line_width) // 2
                    elif alignment == "right":
                        x = start_x + (textbox_width - line_width)
                    draw.text((x, y), line, fill=color_rgb, font=loaded_font)
                    y += line_height
                image_tensor_out = torch.tensor(np.array(image).astype(np.float32) / 255.0)
                image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
                return (image_tensor_out,)
            font_size -= 1
        image_tensor_out = torch.tensor(np.array(image).astype(np.float32) / 255.0)
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,)

    def wrap_text(self, text, font, max_width):
        lines = []
        for line in text.split('\n'):
            words = line.split()
            if not words:
                lines.append('')
                continue
            wrapped_line = words[0]
            for word in words[1:]:
                test_line = wrapped_line + ' ' + word
                test_width = font.getlength(test_line)
                if test_width <= max_width:
                    wrapped_line = test_line
                else:
                    lines.append(wrapped_line)
                    wrapped_line = word
            lines.append(wrapped_line)
        return '\n'.join(lines)

NODE_CLASS_MAPPINGS = {
    "Chatbox Overlay": ChatboxOverlay,
}
