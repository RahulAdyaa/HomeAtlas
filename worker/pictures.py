"""One orientation/alpha convention for OCR, embeddings, crops and model input."""
from PIL import Image,ImageOps


def oriented_rgb(picture):
    image=ImageOps.exif_transpose(picture)
    if image.mode=='RGBA' or image.mode=='LA' or 'transparency' in image.info:
        rgba=image.convert('RGBA')
        background=Image.new('RGBA',rgba.size,'white')
        return Image.alpha_composite(background,rgba).convert('RGB')
    return image.convert('RGB')
