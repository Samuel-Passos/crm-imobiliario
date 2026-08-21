import os
import logging
import google.generativeai as genai
from PIL import Image
import base64
import io

log = logging.getLogger(__name__)

class CreativeEngine:
    def __init__(self, api_key: str, system_instruction: str = None):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        
        genai.configure(api_key=api_key)
        self.api_key = api_key
        self.system_instruction = system_instruction
        
        # Modelo padrão (inicial) - Usando gemini-flash-latest que é validado para esta chave
        self.default_model_name = 'gemini-flash-latest'
        self._current_model = None
        self._model_name_active = None

    def _get_model(self, model_name: str = None):
        """Inicializa ou retorna o modelo solicitado, com ferramentas (tools) nativas."""
        target_name = model_name or self.default_model_name
        
        # Tools: Definimos as funções que a IA pode chamar
        def generate_image(prompt: str):
            """Gera uma imagem realista para um post imobiliário de luxo.
            
            Args:
                prompt: Descrição visual detalhada da imagem (luz, materiais, ambiente).
            """
            # Esta é apenas a definição para a IA. A execução real ocorre no loop abaixo.
            return {"status": "requesting_image", "prompt": prompt}
        
        # Cache do modelo se for o mesmo
        if self._current_model and self._model_name_active == target_name:
            return self._current_model
        
        try:
            log.info(f"[Engine] Inicializando modelo com Tools: {target_name}")
            model = genai.GenerativeModel(
                model_name=target_name,
                system_instruction=self.system_instruction,
                tools=[generate_image]
            )
            self._current_model = model
            self._model_name_active = target_name
            return model
        except Exception as e:
            log.error(f"[Engine] Erro ao carregar modelo '{target_name}': {e}. Usando fallback Flash.")
            # Fallback para o flash estável
            fallback_model = genai.GenerativeModel(
                model_name=self.default_model_name,
                system_instruction=self.system_instruction,
                tools=[generate_image]
            )
            self._current_model = fallback_model
            self._model_name_active = self.default_model_name
            return fallback_model

    def generate_copy(self, prompt: str, history: list = None, reference_files: list = None, image_bytes: bytes = None, model_name: str = None, output_dir: str = "generated_images"):
        """Gera textos e processa chamadas de ferramentas (Function Calling)."""
        try:
            # 1. Preparar Contexto de Referência (Grounding)
            contexto_arquivos = ""
            multimodal_parts = []
            
            if reference_files:
                import fitz # PyMuPDF
                for fpath in reference_files:
                    try:
                        ext = fpath.lower()
                        if ext.endswith('.pdf'):
                            doc = fitz.open(fpath)
                            texto = chr(12).join([page.get_text() for page in doc])
                            contexto_arquivos += f"\n--- CONTEÚDO DO ARQUIVO {os.path.basename(fpath)} ---\n{texto}\n"
                        elif ext.endswith(('.txt', '.md', '.json')):
                            with open(fpath, 'r', encoding='utf-8') as f:
                                contexto_arquivos += f"\n--- CONTEÚDO DO ARQUIVO {os.path.basename(fpath)} ---\n{f.read()}\n"
                        elif ext.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            img_ref = Image.open(fpath)
                            multimodal_parts.append(f"ARQUIVO DE REFERÊNCIA VISUAL ({os.path.basename(fpath)}):")
                            multimodal_parts.append(img_ref)
                    except Exception as fe:
                        log.error(f"Erro ao ler arquivo de referência {fpath}: {fe}")

            # 2. Adicionar imagem enviada no chat (se houver)
            if image_bytes:
                chat_img = Image.open(io.BytesIO(image_bytes))
                multimodal_parts.append("IMAGEM ENVIADA PELO USUÁRIO PARA ANÁLISE ATUAL:")
                multimodal_parts.append(chat_img)

            # 3. Montar Prompt Final
            instrucao_contexto = ""
            if contexto_arquivos:
                instrucao_contexto = f"USE OS MATERIAIS DE REFERÊNCIA EM TEXTO ABAIXO:\n{contexto_arquivos}\n\n"
            
            prompt_final_texto = f"{instrucao_contexto}SOLICITAÇÃO DO USUÁRIO: {prompt}"
            
            prompt_parts = []
            if multimodal_parts:
                prompt_parts.extend(multimodal_parts)
            prompt_parts.append(prompt_final_texto)

            # 4. Chat com histórico e Tool Handling
            model = self._get_model(model_name)
            chat = model.start_chat(history=history or [])
            
            response = chat.send_message(prompt_parts)
            
            text_response = ""
            image_url = None
            
            # Processar partes da resposta (Pode vir texto e chamada de função)
            for part in response.candidates[0].content.parts:
                if part.text:
                    text_response += part.text
                if part.function_call:
                    if part.function_call.name == "generate_image":
                        # Executar a geração de imagem real no backend
                        img_prompt = part.function_call.args["prompt"]
                        log.info(f"[Engine] Executando Tool: generate_image -> {img_prompt[:50]}")
                        img_res = self.execute_real_image_gen(img_prompt, output_dir=output_dir)
                        if img_res.get("ok"):
                            image_url = img_res.get("url_local")

            return {
                "text": text_response,
                "image_url": image_url
            }

        except Exception as e:
            log.error(f"Erro no Gemini (Tool Use): {e}")
            raise e

    def analyze_image(self, prompt: str, image_bytes: bytes, reference_files: list = None, model_name: str = None):
        """Simplifica a chamada para análise de imagem mantendo o grounding."""
        return self.generate_copy(prompt, image_bytes=image_bytes, reference_files=reference_files, model_name=model_name)

    def execute_real_image_gen(self, prompt: str, output_dir: str = "generated_images"):
        """Geração via Pollinations.ai (Flux) executada internamente como uma Tool."""
        try:
            import requests
            import uuid
            import urllib.parse
            
            prompt_encoded = urllib.parse.quote(prompt)
            seed = uuid.uuid4().int >> 64
            url = f"https://pollinations.ai/p/{prompt_encoded}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
            
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return {"ok": False}
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            filename = f"gen_{uuid.uuid4().hex[:8]}.jpg"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
                
            return {
                "ok": True,
                "url_local": f"/static/generated/{filename}",
                "path_local": file_path
            }
        except Exception as e:
            log.error(f"Erro na Tool Execution: {e}")
            return {"ok": False}

# Helper para converter base64 em bytes
def base64_to_bytes(b64_string: str):
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    return base64.b64decode(b64_string)
