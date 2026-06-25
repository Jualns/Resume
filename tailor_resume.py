import os
import re
import sys
import shutil
import argparse
import unicodedata
import webbrowser
import requests
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# --- Wrappers de LLM ---

def call_gemini(api_key, resume_html, job_description, model="gemini-2.5-flash"):
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("O pacote 'google-genai' não está instalado. Instale com: pip install google-genai")

    client = genai.Client(api_key=api_key)
    prompt = get_tailor_prompt(resume_html, job_description)
    
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return clean_html_response(response.text)

def call_openai(api_key, resume_html, job_description, model="gpt-5.4"):
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("O pacote 'openai' não está instalado. Instale com: pip install openai")

    client = OpenAI(api_key=api_key)
    prompt = get_tailor_prompt(resume_html, job_description)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return clean_html_response(response.choices[0].message.content)

def call_anthropic(api_key, resume_html, job_description, model="claude-3-5-sonnet-20241022"):
    try:
        import anthropic
    except ImportError:
        raise ImportError("O pacote 'anthropic' não está instalado. Instale com: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = get_tailor_prompt(resume_html, job_description)
    
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return clean_html_response(response.content[0].text)

# --- Prompts e Helpers ---

def get_tailor_prompt(resume_html, job_description):
    return f"""
Você é um recrutador sênior e especialista em escrita de currículos.
Seu objetivo é personalizar o currículo em HTML fornecido para que ele se alinhe perfeitamente com a descrição da vaga de emprego fornecida abaixo.

Instruções cruciais:
1. NÃO ALTERE NENHUMA TAG HTML, ESTRUTURA, CLASSE, ID OU ATRIBUTO.
2. NÃO ALTERE arquivos CSS vinculados, links de fontes, ícones do FontAwesome ou scripts JS.
3. Modifique APENAS o conteúdo de texto legível (strings dentro de tags como <p>, <li>, <h3>, <span>, <a>, headers, etc.).
4. Destaque as competências, realizações, responsabilidades e tecnologias que o candidato possui e que são altamente relevantes para a vaga. Reordene ou reescreva os tópicos (bullets) das experiências passadas de forma a enfatizar as palavras-chave e requisitos da vaga.
5. NÃO invente informações falsas (como novos empregadores, novas funções de nível diferente do atual, novos diplomas de graduação, datas de emprego ou certificados inexistentes). Baseie-se estritamente nas experiências que já constam no currículo original, mas adaptando e refinando a descrição para focar nas necessidades da vaga.
6. Se a vaga pede "Power BI" ou "SQL Avançado", certifique-se de que essas competências (já presentes no currículo) ganhem o destaque apropriado nas descrições de atividades das experiências.
7. Mantenha o idioma do currículo idêntico ao idioma do currículo de entrada (se o currículo fornecido estiver em português, responda em português; se estiver em inglês, responda em inglês).
8. Retorne APENAS o código HTML completo e atualizado. Não inclua blocos de explicação markdown (como ```html ... ```), introdução, conclusão ou observações. A resposta deve ser diretamente o HTML puro.

---
VAGA DE EMPREGO (DESCRIÇÃO):
{job_description}

---
CURRÍCULO ORIGINAL (HTML):
{resume_html}
"""

def clean_html_response(text):
    clean_text = text.strip()
    if clean_text.startswith("```"):
        # Remove a linha inicial do bloco de código markdown
        clean_text = re.sub(r"^```[a-zA-Z0-9]*\n", "", clean_text)
        # Remove o bloco de fechamento do markdown
        clean_text = re.sub(r"\n```$", "", clean_text)
        clean_text = clean_text.strip()
    return clean_text

def make_safe_filename(s):
    # Remove acentos e caracteres especiais
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^a-zA-Z0-9_\- ]', '', s)
    s = s.replace(' ', '_')
    s = re.sub(r'_+', '_', s)
    return s.strip('_').lower()

def get_api_key(provider):
    env_var = {
        'gemini': 'GEMINI_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'claude': 'ANTHROPIC_API_KEY'
    }[provider]
    
    key = os.environ.get(env_var)
    if not key:
        print(f"\n[Aviso] Chave de API '{env_var}' não encontrada no ambiente ou no arquivo .env.")
        key = input(f"Por favor, insira sua chave de API para o {provider.upper()}: ").strip()
        if not key:
            raise ValueError(f"A chave de API para o {provider} é obrigatória para continuar.")
        
        # Salva a chave no arquivo .env
        with open('.env', 'a', encoding='utf-8') as f:
            f.write(f"\n{env_var}={key}\n")
        os.environ[env_var] = key
        print("[Info] Chave de API salva em .env com sucesso.")
    return key

# --- Lógica de Negócio ---

def web_scrape(url):
    print(f"[Scraper] Acessando link da vaga: {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Erro ao acessar a URL {url}: {e}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove elementos irrelevantes do DOM
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
        element.decompose()
        
    text = soup.get_text(separator='\n')
    lines = [line.strip() for line in text.splitlines()]
    # Remove linhas vazias
    chunks = [line for line in lines if line]
    return '\n'.join(chunks)

def copy_static_assets(project_root, job_folder):
    os.makedirs(job_folder, exist_ok=True)
    assets = ['style.css', 'images', 'js']
    for asset in assets:
        src = os.path.join(project_root, asset)
        dst = os.path.join(job_folder, asset)
        if os.path.exists(src):
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    print(f"[Info] Ativos estáticos copiados com sucesso para: {job_folder}")

def process_single_job(project_root, resume_path, job_description, provider, api_key, model, output_dir, folder_name):
    # Carregar o currículo base
    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Currículo base não encontrado no caminho: {resume_path}")
        
    with open(resume_path, 'r', encoding='utf-8') as f:
        resume_html = f.read()

    # Chamar o provedor de LLM correspondente
    print(f"[LLM] Solicitando otimização ao {provider.upper()} (Modelo: {model or 'padrão'})...")
    if provider == 'gemini':
        tailored_html = call_gemini(api_key, resume_html, job_description, model or "gemini-2.5-flash")
    elif provider == 'openai':
        tailored_html = call_openai(api_key, resume_html, job_description, model or "gpt-4o-mini")
    elif provider == 'claude':
        tailored_html = call_anthropic(api_key, resume_html, job_description, model or "claude-3-5-sonnet-20241022")
    else:
        raise ValueError(f"Provedor {provider} não suportado.")

    # Definir os caminhos de output e copiar assets estáticos
    job_folder = os.path.join(output_dir, folder_name)
    copy_static_assets(project_root, job_folder)
    
    # Calcular o caminho relativo do currículo dentro da pasta de destino
    relative_resume_path = os.path.relpath(resume_path, project_root)
    output_html_path = os.path.join(job_folder, relative_resume_path)
    
    # Garantir que a subpasta correspondente existe (ex: se o currículo original é pt/index.html, criar output/vagas/nome_vaga/pt/)
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    
    # Salvar currículo otimizado
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(tailored_html)
        
    print(f"[Sucesso] Currículo otimizado salvo em: {output_html_path}")
    return output_html_path

# --- Execução Principal ---

def main():
    parser = argparse.ArgumentParser(description="Automação de Currículo Personalizado com IA")
    
    # Parâmetros de Entrada
    parser.add_argument('--vaga', type=str, help="Caminho para arquivo .txt/.md da vaga OU URL pública da vaga")
    parser.add_argument('--lote', type=str, help="Caminho para a planilha de vagas (CSV ou Excel)")
    
    # Configurações do Currículo
    parser.add_argument('--idioma', type=str, choices=['pt', 'en'], default='pt',
                        help="Idioma do currículo base: 'pt' para pt/index.html, 'en' para index.html (Padrão: pt)")
    
    # Configurações de IA
    parser.add_argument('--provider', type=str, choices=['gemini', 'openai', 'claude'], default='gemini',
                        help="Provedor de LLM para otimizar o currículo (Padrão: gemini)")
    parser.add_argument('--model', type=str, default=None,
                        help="Especifica um modelo customizado (ex: gpt-4o, claude-3-5-sonnet, gemini-2.5-pro)")
                        
    # Configurações de Saída
    parser.add_argument('--output-dir', type=str, default="output/vagas",
                        help="Diretório principal para salvar os resultados (Padrão: output/vagas)")
    parser.add_argument('--no-open', action='store_true',
                        help="Evita abrir automaticamente o currículo gerado no navegador")

    args = parser.parse_args()

    # Validar se foi passada vaga individual ou lote
    if not args.vaga and not args.lote:
        parser.print_help()
        print("\n[Erro] Você precisa fornecer --vaga ou --lote para processar.")
        sys.exit(1)

    project_root = os.path.abspath(os.path.dirname(__file__))
    
    # Definir currículo base com base no idioma
    if args.idioma == 'pt':
        resume_path = os.path.join(project_root, 'pt', 'index.html')
    else:
        resume_path = os.path.join(project_root, 'index.html')

    # Garantir que a chave de API correta está disponível
    try:
        api_key = get_api_key(args.provider)
    except ValueError as e:
        print(f"[Erro] {e}")
        sys.exit(1)

    # Criar pasta raiz de output
    os.makedirs(args.output_dir, exist_ok=True)

    if args.vaga:
        # Modo Vaga Única
        job_input = args.vaga.strip()
        
        # Obter descrição da vaga
        if job_input.startswith("http://") or job_input.startswith("https://"):
            try:
                job_description = web_scrape(job_input)
                # Tentar inferir empresa ou cargo pela URL para o nome da pasta
                folder_name = "vaga_" + make_safe_filename(job_input.split('/')[-1] or "link")
            except Exception as e:
                print(f"[Erro] Falha ao raspar a URL: {e}")
                sys.exit(1)
        else:
            if not os.path.exists(job_input):
                print(f"[Erro] Arquivo da vaga não encontrado: {job_input}")
                sys.exit(1)
            with open(job_input, 'r', encoding='utf-8') as f:
                job_description = f.read()
            # Nome da pasta baseado no nome do arquivo
            folder_name = make_safe_filename(os.path.splitext(os.path.basename(job_input))[0])

        print(f"\n--- Processando Vaga Individual ---")
        print(f"Currículo base: {resume_path}")
        print(f"Salvar em: {args.output_dir}/{folder_name}/")

        try:
            output_file = process_single_job(
                project_root=project_root,
                resume_path=resume_path,
                job_description=job_description,
                provider=args.provider,
                api_key=api_key,
                model=args.model,
                output_dir=args.output_dir,
                folder_name=folder_name
            )
            
            # Abrir no navegador padrão
            if not args.no_open:
                print("[Navegador] Abrindo currículo otimizado no seu navegador padrão...")
                webbrowser.open(f"file:///{os.path.abspath(output_file)}")
                print("[Info] Pressione Ctrl + P (ou Cmd + P no Mac) no navegador e escolha 'Salvar como PDF'.")
        except Exception as e:
            print(f"[Erro] Falha no processamento: {e}")
            sys.exit(1)

    elif args.lote:
        # Modo Lote (Planilha)
        spreadsheet_path = args.lote
        if not os.path.exists(spreadsheet_path):
            print(f"[Erro] Planilha de vagas não encontrada: {spreadsheet_path}")
            sys.exit(1)

        print(f"\n--- Lendo Planilha de Vagas: {spreadsheet_path} ---")
        ext = os.path.splitext(spreadsheet_path)[1].lower()
        try:
            if ext == '.csv':
                df = pd.read_csv(spreadsheet_path)
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(spreadsheet_path)
            else:
                print("[Erro] Extensão não suportada. Use CSV ou Excel (.xlsx)")
                sys.exit(1)
        except Exception as e:
            print(f"[Erro] Falha ao ler planilha: {e}")
            sys.exit(1)

        # Mapeamento dinâmico de colunas
        cols = {str(c).strip().lower(): c for c in df.columns}
        
        empresa_col = None
        cargo_col = None
        desc_col = None
        link_col = None
        
        # Tentar localizar colunas de empresa
        for term in ['empresa', 'company', 'organization', 'corporation']:
            if term in cols:
                empresa_col = cols[term]
                break
                
        # Tentar localizar colunas de cargo
        for term in ['cargo', 'vaga', 'role', 'title', 'job_title', 'posicao', 'position']:
            if term in cols:
                cargo_col = cols[term]
                break
                
        # Tentar localizar colunas de descrição
        for term in ['descricao', 'descritivo', 'description', 'texto', 'job_description', 'detalhes', 'details']:
            if term in cols:
                desc_col = cols[term]
                break
                
        # Tentar localizar colunas de link
        for term in ['link', 'url', 'site', 'website', 'vaga_link', 'job_link']:
            if term in cols:
                link_col = cols[term]
                break

        # Fallback se não encontrar mapeamento
        if not empresa_col:
            empresa_col = df.columns[0]
            print(f"[Aviso] Coluna de Empresa não mapeada automaticamente. Usando a primeira coluna: '{empresa_col}'")
        if not cargo_col:
            cargo_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            print(f"[Aviso] Coluna de Cargo não mapeada automaticamente. Usando a coluna: '{cargo_col}'")
        if not desc_col and not link_col:
            # Procurar qualquer coluna restante que pareça descrição ou link
            for col in df.columns:
                if col not in [empresa_col, cargo_col]:
                    desc_col = col
                    break
            if not desc_col:
                print("[Erro] Não foi possível encontrar nenhuma coluna contendo a descrição ou o link da vaga.")
                sys.exit(1)
            print(f"[Aviso] Usando a coluna '{desc_col}' para descrição/link de vaga.")

        print(f"[Mapeamento] Empresa: '{empresa_col}' | Cargo: '{cargo_col}' | Descrição: '{desc_col or 'Nenhum'}' | Link: '{link_col or 'Nenhum'}'")

        # Processar cada linha
        total_rows = len(df)
        print(f"Iniciando processamento de {total_rows} vagas...")
        
        sucessos = 0
        for index, row in df.iterrows():
            empresa_val = str(row[empresa_col]).strip() if pd.notna(row[empresa_col]) else "Empresa_Desconhecida"
            cargo_val = str(row[cargo_col]).strip() if pd.notna(row[cargo_col]) else "Cargo_Desconhecido"
            
            print(f"\n--- Otimizando Vaga [{index+1}/{total_rows}]: {empresa_val} - {cargo_val} ---")
            
            job_description = ""
            
            # 1. Tentar ler descrição do texto
            if desc_col and pd.notna(row[desc_col]):
                desc_val = str(row[desc_col]).strip()
                # Verificar se o campo de descrição na verdade contém uma URL
                if desc_val.startswith("http://") or desc_val.startswith("https://"):
                    try:
                        job_description = web_scrape(desc_val)
                    except Exception as e:
                        print(f"[Aviso] Erro ao raspar URL na coluna de descrição: {e}")
                else:
                    job_description = desc_val
            
            # 2. Se não conseguiu descrição, tentar link
            if not job_description and link_col and pd.notna(row[link_col]):
                link_val = str(row[link_col]).strip()
                if link_val.startswith("http://") or link_val.startswith("https://"):
                    try:
                        job_description = web_scrape(link_val)
                    except Exception as e:
                        print(f"[Aviso] Erro ao raspar URL da vaga: {e}")
            
            if not job_description:
                print(f"[Pular] Não foi possível extrair a descrição ou o link para a vaga de {cargo_val} na {empresa_val}.")
                continue
                
            folder_name = make_safe_filename(f"{empresa_val}_{cargo_val}")
            
            try:
                output_file = process_single_job(
                    project_root=project_root,
                    resume_path=resume_path,
                    job_description=job_description,
                    provider=args.provider,
                    api_key=api_key,
                    model=args.model,
                    output_dir=args.output_dir,
                    folder_name=folder_name
                )
                sucessos += 1
                
                # Abrir no navegador padrão (somente se não for lote muito grande ou sob solicitação)
                if not args.no_open and total_rows <= 3:
                    webbrowser.open(f"file:///{os.path.abspath(output_file)}")
            except Exception as e:
                print(f"[Erro] Falha ao processar linha {index+1}: {e}")
                
        print(f"\n--- Processamento em Lote Concluído ---")
        print(f"Sucesso: {sucessos}/{total_rows} vagas processadas.")
        if sucessos > 0:
            print(f"Todos os currículos estão salvos na pasta: {os.path.abspath(args.output_dir)}")
            print("Para imprimir os currículos em PDF, abra os arquivos HTML em seu navegador e use o atalho Ctrl + P.")

if __name__ == '__main__':
    main()
