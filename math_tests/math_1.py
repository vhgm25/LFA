import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageOps
import re
import gradio as gr


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed").to(DEVICE)


def process_image(image):
    try:
        
        if isinstance(image, str):  
            img = Image.open(image)
        elif hasattr(image, 'name'):  
            img = Image.open(image.name)
        else:  
            img = image
            
        
        if img is None:
            return "⚠️ Não foi possível carregar a imagem!"
        
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = ImageOps.autocontrast(img)
        img = img.resize((800, 800))
        
        
        pixel_values = processor(img, return_tensors="pt").pixel_values.to(DEVICE)
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        
        if not text:
            return "⚠️ Nenhum texto reconhecido na imagem!"
        
        
        try:
            
            expr = re.sub(r'[^0-9+\-*/().,=]', '', text.replace(" ", ""))
            
            
            expr = expr.replace(',', '.')
            
            
            if '=' in expr:
                left, right = expr.split('=', 1)
                left_val = eval(left, {"__builtins__": None}, {})
                right_val = eval(right, {"__builtins__": None}, {})
                return f"Equação reconhecida: {text}\nResultado: {left} = {right} → {left_val == right_val}"
            else:
                result = eval(expr, {"__builtins__": None}, {})
                return f"Expressão reconhecida: {text}\nResultado: {expr} = {result}"
        except Exception as e:
            return f"Expressão reconhecida: {text}\n⚠ Não foi possível calcular - {str(e)}"
    
    except Exception as e:
        return f"❌ Ocorreu um erro: {str(e)}"


interface = gr.Interface(
    fn=process_image,
    inputs=gr.Image(label="Envie uma imagem com expressão matemática", type="filepath"),
    outputs=gr.Textbox(label="Resultado", lines=5),
    title="🔢math",
    description="""Escolha uma imagem abaixo e veja o resultado.""",
    examples=[
        ["math_problem.jpeg"],  
        ["math2.jpg"],
        ["math21.jpg"],
        ["certo.jpeg"],
        ["pipo.jpg"]
        
    ],
    allow_flagging="never",
    css=".gradio-container {max-width: 800px !important}"
)


def console_version():
    print("\nModo console ativado (digite 'sair' para encerrar)")
    while True:
        image_path = input("\nCaminho da imagem: ").strip()
        if image_path.lower() in ['sair', 'exit']:
            break
        
        result = process_image(image_path)
        print("\n" + result + "\n" + "="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--console', action='store_true', help='Executar versão console')
    args = parser.parse_args()
    
    if args.console:
        console_version()
    else:
        
        interface.launch(
            server_name="0.0.0.0" if torch.cuda.is_available() else None,
            server_port=7860,
            share=False
        )