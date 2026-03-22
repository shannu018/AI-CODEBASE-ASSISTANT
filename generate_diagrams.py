import base64
import urllib.request
import json
import os
import shutil

diagrams = {
    "Figure_2.1_Existing_System_Architecture.png": "flowchart TD\n    A[Developer / Engineer] -->|Uses| B(Standard IDE / Text Editor)\n    B -->|Manual Search| C[(Large Codebase Files)]\n    B -->|Regex/Grep| C\n    A -->|Reads Code Manually| C\n    C -->|Returns Raw Text| A\n    style A fill:#f9f,stroke:#333,stroke-width:2px\n    style C fill:#ccf,stroke:#333,stroke-width:2px",
    
    "Figure_3.1_Block_Diagram_Proposed_System.png": "flowchart LR\n    User[Developer] <-->|Uploads Code & Asks Questions| UI[Web Interface]\n    UI <-->|HTTP API| App[Flask Application Server]\n    subgraph AI Codebase Assistant\n        App -->|File Processing| Indexing[Indexing Engine]\n        App -->|Vector Search| RAG[RAG Pipeline]\n    end\n    Indexing -->|Extracts & Stores| DB[(ChromaDB Vector DB)]\n    RAG <-->|Retrieves Context| DB\n    Indexing -->|Calls| GeminiAPI((Google Gemini Embeddings))\n    RAG <-->|Calls| GeminiAPI\n    RAG <-->|Generates Answer| GeminiLLM((Google Gemini 1.5 Flash))",
    
    "Figure_4.1_System_Architecture_Diagram.png": "flowchart TB\n    UI[HTML/CSS/JS UI] <--> Routes[Flask API Routes]\n    Routes <--> Chunk[Parser & Chunker]\n    Routes <--> RAG[RAG Engine]\n    Chunk <--> Embed[Embedding Service]\n    RAG <--> Embed\n    Embed <--> Chroma[(ChromaDB)]\n    RAG <--> Chroma\n    Embed <--> Gemini((Google Gemini API))\n    RAG <--> Gemini",
    
    "Figure_4.2_Data_Flow_Diagram.png": "flowchart TD\n    subgraph Data Flow 1: Indexing Phase\n        U1(User Uploads Folder) --> P1[Parser Extracts Text]\n        P1 --> C1[Chunker Splits Code]\n        C1 --> E1[Gemini Embedding API]\n        E1 -->|Vectors| DB1[(ChromaDB)]\n    end\n    subgraph Data Flow 2: Query Phase\n        U2(User Submits Query) --> Q1[Embed Query via Gemini]\n        Q1 -->|Similarity Search| DB1\n        DB1 -->|Top-K Code Chunks| R1[RAG Context Builder]\n        R1 -->|Context + Query| G1[Gemini LLM]\n        G1 -->|Generated Answer| U3(Response to User)\n    end",
    
    "Figure_4.3_Use_Case_Diagram.png": "flowchart LR\n    Dev((Developer))\n    subgraph CodeBrain System\n        UC1(Upload Project Codebase)\n        UC2(Trigger Indexing)\n        UC3(Ask Natural Language Questions)\n        UC4(View Relevant Code Sources)\n        UC5(View Index Statistics)\n    end\n    Dev --> UC1\n    Dev --> UC2\n    Dev --> UC3\n    Dev --> UC4\n    Dev --> UC5",
    
    "Figure_4.4_Sequence_Diagram.png": "sequenceDiagram\n    actor User\n    participant AppJS as Frontend\n    participant Flask as Backend\n    participant RAG as RAG Service\n    participant Chroma as ChromaDB\n    participant Gemini as Google API\n    User->>AppJS: Types question & clicks Send\n    AppJS->>Flask: POST /api/chat {query}\n    Flask->>RAG: query_rag(query)\n    RAG->>Gemini: embed_query(query)\n    Gemini-->>RAG: Returns query vector\n    RAG->>Chroma: semantic_search(vector)\n    Chroma-->>RAG: Returns Top 5 code chunks\n    RAG->>RAG: Build context prompt with chunks\n    RAG->>Gemini: generate_content(prompt)\n    Gemini-->>RAG: Returns AI explantion\n    RAG-->>Flask: Dict {answer, sources}\n    Flask-->>AppJS: JSON response\n    AppJS-->>User: Displays formatted AI response",
    
    "Figure_5.1_Agile_Development_Methodology.png": "stateDiagram-v2\n    [*] --> Requirements\n    Requirements --> Design: Define Flask/RAG Architecture\n    Design --> Development: Implement API & UI\n    Development --> Testing: Validate Embeddings/Chat\n    Testing --> Deployment: Run Local Server\n    Deployment --> Review: User Feedback\n    Review --> Requirements: Next Sprint / Fixes",
    
    "Figure_5.2_RAG_Pipeline_Flow.png": "flowchart TD\n    A[Raw Query] --> B[Generate Query Embedding]\n    B --> C{Vector Database}\n    subgraph Retrieval Phase\n        C -->|Calculates Cosine Similarity| D[Fetch Top-K Contexts]\n    end\n    D --> E[Construct Prompt]\n    E -->|Combine Query + Code Context + History| F[Generative LLM]\n    subgraph Generation Phase\n        F --> G[Explain Code / Produce Output]\n    end"
}

output_dir = "C:/Users/Shannu/.gemini/antigravity/brain/932370fc-90a3-4735-89cb-1049b7e47aad/"

print("Downloading API diagrams...")
for fname, code in diagrams.items():
    url = "https://kroki.io/mermaid/png"
    data = json.dumps({"diagram_source": code}).encode('utf-8')
    headers = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        with open(os.path.join(output_dir, fname), "wb") as f:
            f.write(response.read())
        print(f"Saved {fname}")
    except Exception as e:
        print(f"Failed {fname}: {e}")

print("Copying UI screenshots...")
feedback_dir = os.path.join(output_dir, ".system_generated", "click_feedback")
if os.path.exists(feedback_dir):
    files = [f for f in os.listdir(feedback_dir) if f.endswith(".png")]
    files.sort() # get chronologically or arbitrarily
    if len(files) >= 1:
        # Just grab the last one which had full chat, or the first one which had the upload screen
        shutil.copy(os.path.join(feedback_dir, files[0]), os.path.join(output_dir, "Figure_5.3_Codebase_Upload_Interface.png"))
        print("Saved Figure_5.3_Codebase_Upload_Interface.png")
    if len(files) >= 2:
        shutil.copy(os.path.join(feedback_dir, files[-1]), os.path.join(output_dir, "Figure_5.4_Query_Response_Interface.png"))
        print("Saved Figure_5.4_Query_Response_Interface.png")
