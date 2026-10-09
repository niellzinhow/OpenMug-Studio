import os
from PIL import Image, ImageCms, ImageOps

class ImageProcessor:
    def __init__(self):
        # Resoluções Fixas (300 DPI)
        self.a4_width = 2480
        self.a4_height = 3508
        self.mug_width = 2362  # Reduzido para 20cm garantindo margens laterais seguras
        self.mug_height = 1122

    def process_and_assemble(self, images_data, icc_profile_path):
        """Monta as artes no A4 e aplica o perfil ICC se disponível. Retorna a imagem A4 final."""
        a4_image = Image.new("RGB", (self.a4_width, self.a4_height), "white")
        
        spacing = (self.a4_height - (3 * self.mug_height)) // 4
        y_offsets = [
            spacing,
            spacing + self.mug_height + spacing,
            spacing + 2 * self.mug_height + 2 * spacing
        ]
        
        x_offset = (self.a4_width - self.mug_width) // 2
        
        for i, data in enumerate(images_data):
            img_path = data["path"]
            if img_path and os.path.exists(img_path):
                with Image.open(img_path) as img:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    mode = data["mode"]
                    if mode == "Cortar":
                        # Corta pelo centro preservando a proporção
                        processed_img = ImageOps.fit(img, (self.mug_width, self.mug_height), 
                                                     method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    else:
                        # Estica para forçar o tamanho exato
                        processed_img = img.resize((self.mug_width, self.mug_height), Image.Resampling.LANCZOS)
                    
                    a4_image.paste(processed_img, (x_offset, y_offsets[i]))

        # Aplica o Perfil ICC antes da prévia
        if icc_profile_path and os.path.exists(icc_profile_path):
            srgb_profile = ImageCms.createProfile("sRGB")
            try:
                target_profile = ImageCms.getOpenProfile(icc_profile_path)
                a4_final = ImageCms.profileToProfile(
                    a4_image,
                    srgb_profile,
                    target_profile,
                    renderingIntent=0,
                    outputMode='RGB'
                )
                return a4_final
            except Exception as icc_err:
                raise Exception(f"Não foi possível aplicar o perfil ICC.\n{str(icc_err)}")
        return a4_image
