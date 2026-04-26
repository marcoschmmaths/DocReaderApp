import os
import tempfile
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib import mathtext

class LatexRenderer:
    def __init__(self):
        plt.rcParams['mathtext.fontset'] = 'stix'
        plt.rcParams['font.family'] = 'STIXGeneral'
    
    def render_latex_to_base64(self, latex_str, fontsize=14, dpi=200):
        """
        Convierte una expresión LaTeX a una imagen base64
        """
        try:
            # Configurar el renderizador de matplotlib
            fig = plt.figure(figsize=(0.1, 0.1))
            fig.patch.set_alpha(0.0)  # Fondo transparente
            
            # Renderizar la expresión LaTeX
            buffer = BytesIO()
            plt.text(0, 0, f'${latex_str}$', fontsize=fontsize, 
                    color='black', alpha=1.0, ha='left', va='bottom')
            plt.axis('off')
            plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight', 
                       pad_inches=0.0, transparent=True)
            plt.close(fig)
            
            # Convertir a base64
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            print(f"Error renderizando LaTeX: {e}")
            return None
    
    def replace_latex_in_text(self, text, fontsize=14):
        """
        Reemplaza expresiones LaTeX entre $$ con imágenes en un texto
        """
        import re
        
        # Patrón para encontrar expresiones LaTeX entre $$
        pattern = r'\$\$(.*?)\$\$'
        parts = re.split(pattern, text)
        
        result_html = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Texto normal
                result_html += part.replace('\n', '<br>')
            else:
                # Expresión LaTeX
                img_data = self.render_latex_to_base64(part, fontsize)
                if img_data:
                    result_html += f'<img src="{img_data}" style="vertical-align: middle;">'
                else:
                    result_html += f'[Error: {part}]'
        
        return result_html